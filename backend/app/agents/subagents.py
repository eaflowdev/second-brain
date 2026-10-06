from dataclasses import dataclass
from typing import List

from app.agents.loop import run_agent
from app.agents.models import Tool
from app.agents.skill_loader import get_skill
from app.agents.tools import search_notes_tool, search_web_tool

SUBAGENT_MAX_TURNS = 4

# Tools a skill can request in its frontmatter (`tools:`), by name.
_TOOLS_BY_NAME = {tool.name: tool for tool in [search_notes_tool, search_web_tool]}


@dataclass
class SubAgent:
    """A narrowly-scoped agent: its own system prompt, its own toolset, and its
    own isolated conversation. Only .run()'s return value crosses back out —
    the caller never sees this subagent's internal reasoning or tool calls."""

    name: str
    description: str
    system_prompt: str
    tools: List[Tool]

    def run(self, task: str) -> str:
        result = run_agent(
            task,
            system_prompt=self.system_prompt,
            tools=self.tools,
            max_turns=SUBAGENT_MAX_TURNS,
        )
        return result["answer"]


def subagent_from_skill(skill_name: str) -> SubAgent:
    """Build a sub-agent from its skill file: the .md is the only place its prompt,
    description and toolset are defined."""
    skill = get_skill(skill_name)
    return SubAgent(
        name=skill.name,
        description=skill.description,
        system_prompt=f"<role>\n{skill.role}\n</role>\n\n{skill.body}",
        tools=[_TOOLS_BY_NAME[tool_name] for tool_name in skill.tools],
    )


QUIZZER = subagent_from_skill("quizzer")
RESEARCHER = subagent_from_skill("researcher")
SYNTHESIZER = subagent_from_skill("synthesizer")

SUBAGENTS = {agent.name: agent for agent in [QUIZZER, RESEARCHER, SYNTHESIZER]}
