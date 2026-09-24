import pytest

from app.mcp.server import mcp


@pytest.mark.asyncio
async def test_mcp_server_registers_all_expected_tools():
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}

    assert names == {
        "search_notes",
        "search_web",
        "generate_quiz",
        "research_topic",
        "synthesize_notes",
    }


@pytest.mark.asyncio
async def test_mcp_search_notes_tool_returns_real_results():
    content, _ = await mcp.call_tool("search_notes", {"query": "embedding"})

    assert "embedding" in content[0].text.lower()


@pytest.mark.asyncio
async def test_mcp_search_web_tool_reports_missing_key(monkeypatch):
    from app.agents import tools as agent_tools

    monkeypatch.setattr(agent_tools.settings, "tavily_api_key", None)

    content, _ = await mcp.call_tool("search_web", {"query": "actualités IA"})

    assert "TAVILY_API_KEY" in content[0].text
