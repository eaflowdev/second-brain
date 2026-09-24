import json
from typing import Optional

from app.agents.prompts import build_system_prompt
from app.agents.skill_loader import list_skills
from app.agents.tools import TOOLS
from app.core.config import settings
from app.core.llm import LLMError, chat

MAX_TURNS = 5
CHAT_RETRY_ATTEMPTS = 2


def _skills_index() -> str:
    """Lightweight index (name + one-line description) always in context — the
    full instructions of a skill are only loaded on demand via `load_skill`."""
    return "\n".join(f"- {skill.name}: {skill.description}" for skill in list_skills())


SYSTEM_PROMPT = build_system_prompt(
    role=(
        "Tu es l'assistant de révision de Second Brain, un agent qui aide "
        "l'utilisateur à retrouver et comprendre le contenu de ses propres "
        "notes personnelles."
    ),
    instructions=[
        "Utilise `search_notes` pour chercher dans les notes personnelles de l'utilisateur.",
        "Utilise `search_web` uniquement si les notes ne suffisent pas à répondre.",
        "Utilise `load_skill` dès que la tâche correspond à l'une des compétences ci-dessous, puis suis ses instructions.",
        "Ne réponds qu'une fois avoir rassemblé assez d'informations pour une réponse fiable.",
    ],
    constraints=[
        "Ne réponds jamais en inventant une information absente des notes et des résultats web.",
        "Si aucune source ne permet de répondre, dis-le clairement plutôt que de deviner.",
    ],
    output_format=(
        "Réponds en français, dans un ton clair et direct. Cite la note ou la "
        "source utilisée quand c'est pertinent."
    ),
) + f"\n\n<skills>\n{_skills_index()}\n</skills>"

PLANNING_PROMPT_TEMPLATE = (
    "Question : {question}\n\nOutils disponibles :\n{tool_list}\n\n"
    "Propose un plan court (2 à 4 étapes maximum) pour répondre à cette "
    "question à l'aide de ces outils. Ne réponds pas à la question, donne "
    "uniquement le plan."
)


def _chat_with_retry(messages, tools=None, model=None, reasoning: Optional[dict] = None, attempts=CHAT_RETRY_ATTEMPTS):
    """The free-tier model pool occasionally returns a transient error
    (rate-limit, malformed body). Retrying once is enough in practice."""
    last_error = None
    for _ in range(attempts):
        try:
            return chat(messages, tools=tools, model=model, reasoning=reasoning)
        except LLMError as exc:
            last_error = exc
    raise last_error


def _plan(question: str, tools) -> str:
    tool_list = "\n".join(f"- {tool.name}: {tool.description}" for tool in tools)
    prompt = PLANNING_PROMPT_TEMPLATE.format(question=question, tool_list=tool_list)
    message = _chat_with_retry([{"role": "user", "content": prompt}], model=settings.agent_model)
    return message.get("content") or ""


def _build_system_message(content: str, cache: bool) -> dict:
    """Plain string content by default. When `cache=True`, wrap the content as
    a content-block with a `cache_control` breakpoint — the format Anthropic,
    Gemini and Alibaba Qwen use on OpenRouter to mark a prefix as reusable.
    Providers that ignore/ don't support this block format are unaffected: it's
    additive metadata, not a different prompt."""
    if not cache:
        return {"role": "system", "content": content}
    return {
        "role": "system",
        "content": [{"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}],
    }


def run_agent(
    question: str,
    system_prompt: str = SYSTEM_PROMPT,
    tools=None,
    max_turns: int = MAX_TURNS,
    reasoning: Optional[dict] = None,
    cache_system_prompt: bool = False,
) -> dict:
    """Plan, then ReAct loop: the model decides to call a tool (action), we run
    it and feed back the result (observation), until it answers directly, gets
    stuck repeating itself, or max_turns is hit.

    system_prompt/tools default to the general assistant, but can be overridden
    to turn this same engine into a narrowly-scoped subagent with its own,
    isolated conversation (a fresh `messages` list every call - nothing is
    shared with the caller's context).

    `reasoning` (e.g. {"effort": "low"|"medium"|"high"}) controls how much the
    model is allowed to "think" before answering, on models that support it.
    Any reasoning trace returned by the model is collected in `thinking`,
    exposed to the caller instead of being silently discarded.

    `cache_system_prompt` marks the (large, stable) system prompt as a cacheable
    block via `cache_control` — it never changes within a run, and across a
    multi-turn loop the same prefix is resent at every single turn, making it
    the prime candidate for prompt caching."""
    active_tools = list(TOOLS.values()) if tools is None else tools
    tools_by_name = {tool.name: tool for tool in active_tools}
    tool_schemas = [tool.to_schema() for tool in active_tools]

    plan = _plan(question, active_tools)

    system_message = _build_system_message(system_prompt, cache=cache_system_prompt)
    messages = [
        system_message,
        {"role": "user", "content": question},
        {"role": "assistant", "content": f"Plan envisagé :\n{plan}"},
    ]
    steps = []
    thinking = []
    usage_log = []
    seen_calls = set()

    for _ in range(max_turns):
        message = _chat_with_retry(
            messages, tools=tool_schemas, model=settings.agent_model, reasoning=reasoning
        )
        if message.get("reasoning"):
            thinking.append(message["reasoning"])
        usage_log.append(message.get("usage", {}))
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            return {
                "plan": plan,
                "answer": message["content"],
                "steps": steps,
                "thinking": thinking,
                "usage": usage_log,
            }

        messages.append(message)
        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"] or "{}")
            tool = tools_by_name.get(name)
            call_signature = (name, json.dumps(args, sort_keys=True))

            if call_signature in seen_calls:
                observation = (
                    "Tu as déjà appelé cet outil avec exactement les mêmes "
                    "arguments : le résultat sera identique. Essaie une "
                    "requête différente, ou réponds avec les informations "
                    "déjà récoltées."
                )
            else:
                seen_calls.add(call_signature)
                try:
                    observation = tool.handler(**args) if tool else f"Outil inconnu : {name}"
                except Exception as exc:  # noqa: BLE001 - un outil qui plante ne doit pas casser la boucle
                    observation = f"L'outil a échoué : {exc}"

            steps.append({"tool": name, "input": args, "output": observation})
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": observation}
            )

    # Plafond atteint : on force une synthèse avec ce qui a été récolté plutôt
    # que d'abandonner sèchement.
    messages.append(
        {
            "role": "user",
            "content": (
                "Tu as atteint la limite d'itérations autorisées. Réponds du "
                "mieux possible avec les informations déjà récoltées ci-dessus."
            ),
        }
    )
    final_message = _chat_with_retry(messages, model=settings.agent_model, reasoning=reasoning)
    if final_message.get("reasoning"):
        thinking.append(final_message["reasoning"])
    usage_log.append(final_message.get("usage", {}))
    return {
        "plan": plan,
        "answer": final_message.get("content") or "Je n'ai pas réussi à conclure.",
        "steps": steps,
        "thinking": thinking,
        "usage": usage_log,
    }
    return {
        "plan": plan,
        "answer": final_message.get("content") or "Je n'ai pas réussi à conclure.",
        "steps": steps,
        "thinking": thinking,
    }
