import pytest

from app.embeddings.models import Chunk
from app.mcp.server import mcp
from app.storage.vector_store import VectorStore


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


class _FixedEmbedder:
    def embed(self, texts):
        return [[1.0, 0.0] for _ in texts]


@pytest.mark.asyncio
async def test_mcp_search_notes_tool_returns_indexed_passage(tmp_path, monkeypatch):
    # Index temporaire et embedder factice : le test ne dépend ni de l'index local
    # (backend/data, gitignoré) ni du téléchargement du modèle d'embedding.
    from app.agents import tools as agent_tools

    store = VectorStore(tmp_path / "store.json")
    chunk = Chunk(
        id="n::0",
        document_id="n",
        index=0,
        text="Un embedding transforme un texte en vecteur.",
        metadata={"title": "note", "source_path": "note.md", "doc_type": "markdown"},
    )
    store.add(chunk, [1.0, 0.0])
    monkeypatch.setattr(agent_tools, "get_vector_store", lambda: store)
    monkeypatch.setattr(agent_tools, "_embedder", _FixedEmbedder())

    content, _ = await mcp.call_tool("search_notes", {"query": "embedding"})

    assert "embedding" in content[0].text.lower()


@pytest.mark.asyncio
async def test_mcp_search_web_tool_reports_missing_key(monkeypatch):
    from app.agents import tools as agent_tools

    monkeypatch.setattr(agent_tools.settings, "tavily_api_key", None)

    content, _ = await mcp.call_tool("search_web", {"query": "actualités IA"})

    assert "TAVILY_API_KEY" in content[0].text
