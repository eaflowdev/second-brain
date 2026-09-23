import pytest

from app.core import llm
from app.embeddings.models import Chunk
from app.rag import prompt, service
from app.storage.vector_store import VectorStore


def test_build_user_message_includes_source_and_question():
    chunks = [{"text": "Un embedding transforme un texte en vecteur.", "metadata": {"title": "exemple"}}]

    message = prompt.build_user_message("c'est quoi un embedding ?", chunks)

    assert "exemple" in message
    assert "c'est quoi un embedding ?" in message


def test_answer_question_returns_message_when_no_chunks(monkeypatch, tmp_path):
    empty_store = VectorStore(tmp_path / "empty.json")
    monkeypatch.setattr(service, "get_vector_store", lambda: empty_store)

    result = service.answer_question("question sans note")

    assert result["sources"] == []
    assert "trouv" in result["answer"]


def test_answer_question_calls_llm_with_retrieved_context(monkeypatch, tmp_path):
    store = VectorStore(tmp_path / "store.json")
    chunk = Chunk(
        id="doc::0",
        document_id="doc",
        index=0,
        text="Un embedding transforme un texte en vecteur.",
        metadata={"title": "exemple", "source_path": "x", "doc_type": "markdown"},
    )
    store.add(chunk, [1.0, 0.0])
    monkeypatch.setattr(service, "get_vector_store", lambda: store)
    monkeypatch.setattr(service._embedder, "embed", lambda texts: [[1.0, 0.0]])

    captured = {}

    def fake_generate(system, user_message, max_tokens=1024):
        captured["user_message"] = user_message
        return "réponse test"

    monkeypatch.setattr(service, "generate", fake_generate)

    result = service.answer_question("c'est quoi un embedding ?")

    assert result["answer"] == "réponse test"
    assert result["sources"][0]["title"] == "exemple"
    assert "embedding" in captured["user_message"].lower()


def test_generate_raises_without_api_key(monkeypatch):
    monkeypatch.setattr(llm.settings, "openrouter_api_key", None)

    with pytest.raises(llm.LLMError):
        llm.generate("system", "user")
