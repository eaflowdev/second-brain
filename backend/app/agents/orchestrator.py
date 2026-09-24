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
        "Présente le(s) résultat(s) des sous-agents à l'utilisateur une fois obtenus.",
    ],
    constraints=[
        "Ne réalise jamais toi-même la tâche de fond (ne génère pas de quiz, de recherche ou de synthèse toi-même).",
        "Ne modifie pas le contenu factuel renvoyé par un sous-agent, présente-le fidèlement.",
    ],
    output_format=(
        "Une réponse claire à l'utilisateur, éventuellement introduite par une "
        "courte phrase de contexte, suivie du contenu produit par le(s) sous-agent(s)."
    ),
)


def _make_delegation_tool(subagent) -> Tool:
    """Wrap a SubAgent as a Tool: from the orchestrator's point of view,
    delegating IS just another tool call — same mechanism, no special-casing."""
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
        handler=lambda task: subagent.run(task),
    )


DELEGATION_TOOLS = [_make_delegation_tool(subagent) for subagent in SUBAGENTS.values()]


def run_orchestrator(question: str) -> dict:
    return run_agent(
        question,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=DELEGATION_TOOLS,
        max_turns=ORCHESTRATOR_MAX_TURNS,
    )
