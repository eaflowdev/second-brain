import json

from app.agents.tools import TOOLS
from app.core.config import settings
from app.core.llm import chat

MAX_TURNS = 5

SYSTEM_PROMPT = (
    "Tu es l'assistant de révision de Second Brain. Tu as accès à des outils : "
    "utilise `search_notes` pour chercher dans les notes personnelles de "
    "l'utilisateur, et `search_web` seulement si les notes ne suffisent pas. "
    "Ne réponds qu'une fois avoir rassemblé assez d'informations. Si tu ne "
    "trouves rien de pertinent, dis-le clairement plutôt que d'inventer."
)


def run_agent(question: str, max_turns: int = MAX_TURNS) -> dict:
    """ReAct loop: the model decides to call a tool (action), we run it and feed
    back the result (observation), until it answers directly or max_turns is hit."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tool_schemas = [tool.to_schema() for tool in TOOLS.values()]
    steps = []

    for _ in range(max_turns):
        message = chat(messages, tools=tool_schemas, model=settings.agent_model)
        tool_calls = message.get("tool_calls")

        if not tool_calls:
            return {"answer": message["content"], "steps": steps}

        messages.append(message)
        for call in tool_calls:
            name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"] or "{}")
            tool = TOOLS.get(name)

            observation = tool.handler(**args) if tool else f"Outil inconnu : {name}"

            steps.append({"tool": name, "input": args, "output": observation})
            messages.append(
                {"role": "tool", "tool_call_id": call["id"], "content": observation}
            )

    return {
        "answer": "Je n'ai pas réussi à conclure dans le nombre de tours autorisé.",
        "steps": steps,
    }
