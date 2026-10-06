from typing import Optional

from app.agents.loop import run_agent
from app.agents.models import Tool
from app.agents.prompts import build_system_prompt
from app.agents.subagents import SUBAGENTS

ORCHESTRATOR_MAX_TURNS = 4

ORCHESTRATOR_SYSTEM_PROMPT = build_system_prompt(
    role=(
        "Tu es l'orchestrateur de Second Brain. Tu ne réponds jamais "
        "directement aux questions de fond : tu délègues à des sous-agents "
        "spécialisés (quizzer, researcher, synthesizer)."
    ),
    instructions=[
        "Choisis le sous-agent le plus adapté à la demande de l'utilisateur.",
        "Appelle plusieurs sous-agents, dans l'ordre nécessaire, si la demande le requiert.",
        "Une fois les sous-agents appelés, rédige seulement une courte phrase de contexte.",
    ],
    constraints=[
        "Ne réalise jamais toi-même la tâche de fond (ne génère pas de quiz, de recherche ou de synthèse toi-même).",
        "Ne recopie pas le contenu des sous-agents : le système l'ajoute automatiquement à ta réponse.",
    ],
    output_format="Une seule courte phrase de contexte, en français.",
)


def _make_delegation_tool(subagent, outputs: list[str]) -> Tool:
    """Wrap a SubAgent as a Tool. The subagent's output is stored in `outputs`
    (code path) and only an acknowledgement goes back to the orchestrator LLM,
    so the content never depends on the LLM faithfully copying it."""

    def handler(task: str) -> str:
        outputs.append(subagent.run(task))
        return (
            f"Résultat du sous-agent {subagent.name} enregistré. Il sera ajouté "
            "automatiquement à la réponse : ne le recopie pas."
        )

    return Tool(
        name=f"delegate_to_{subagent.name}",
        description=subagent.description,
        parameters={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "La tâche précise à confier à ce sous-agent"}
            },
            "required": ["task"],
        },
        handler=handler,
    )


def build_delegation_tools(outputs: list[str]) -> list[Tool]:
    return [_make_delegation_tool(subagent, outputs) for subagent in SUBAGENTS.values()]


def run_orchestrator(question: str, reasoning: Optional[dict] = None) -> dict:
    outputs: list[str] = []
    result = run_agent(
        question,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=build_delegation_tools(outputs),
        max_turns=ORCHESTRATOR_MAX_TURNS,
        reasoning=reasoning,
    )
    # Le contenu des sous-agents est ajouté par le code, verbatim, après la phrase
    # de contexte du LLM : il ne dépend pas de la fidélité de sa recopie.
    parts = [part for part in [result["answer"], *outputs] if part]
    result["answer"] = "\n\n---\n\n".join(parts)
    return result
