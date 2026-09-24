"""MCP server: exposes Second Brain's capabilities as raw tools for an external
MCP client (e.g. Claude Desktop) to reason over and call directly.

Design choice: expose the underlying capabilities (search, and the specialized
subagents), NOT our own ReAct loop. When called from Claude Desktop, Claude's
own model does the planning/tool-selection — our OpenRouter-based agent loop
(app/agents/loop.py) is a separate, independent way to use the same building
blocks, for standalone/API use without Claude Desktop.
"""

from mcp.server.fastmcp import FastMCP

from app.agents.subagents import QUIZZER, RESEARCHER, SYNTHESIZER
from app.agents.tools import _search_notes, _search_web

mcp = FastMCP("second-brain")


@mcp.tool()
def search_notes(query: str) -> str:
    """Recherche par similarité sémantique dans les notes personnelles de l'utilisateur."""
    return _search_notes(query)


@mcp.tool()
def search_web(query: str) -> str:
    """Recherche des informations à jour sur le web (via Tavily)."""
    return _search_web(query)


@mcp.tool()
def generate_quiz(topic: str) -> str:
    """Génère un quiz de révision (questions + réponses) sur un sujet, à partir des notes personnelles."""
    return QUIZZER.run(topic)


@mcp.tool()
def research_topic(topic: str) -> str:
    """Fait une recherche approfondie sur un sujet, en combinant notes personnelles et web, sources citées."""
    return RESEARCHER.run(topic)


@mcp.tool()
def synthesize_notes(topic: str) -> str:
    """Produit une synthèse structurée d'un sujet à partir des notes personnelles."""
    return SYNTHESIZER.run(topic)


if __name__ == "__main__":
    mcp.run()
