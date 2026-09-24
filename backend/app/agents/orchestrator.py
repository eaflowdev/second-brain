from app.agents.loop import run_agent
from app.agents.models import Tool
from app.agents.subagents import SUBAGENTS

ORCHESTRATOR_MAX_TURNS = 4

ORCHESTRATOR_SYSTEM_PROMPT = (
    "Tu es l'orchestrateur de Second Brain. Tu ne réponds jamais directement "
    "aux questions de fond : tu délègues à des sous-agents spécialisés "
    "(quizzer, researcher, synthesizer) selon la demande, puis tu présentes "
    "leurs résultats à l'utilisateur. Choisis le sous-agent le plus adapté ; "
    "tu peux en appeler plusieurs si la demande le nécessite."
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
