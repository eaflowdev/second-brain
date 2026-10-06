from app.embeddings.models import Chunk
from app.storage.vector_store import VectorStore


def _chunk(id_: str, text: str) -> Chunk:
    return Chunk(id=id_, document_id="doc", index=0, text=text, metadata={})


def test_search_ranks_closest_vector_first(tmp_path):
    store = VectorStore(tmp_path / "store.json")
    store.add(_chunk("a", "vecteur proche"), [1.0, 0.0])
    store.add(_chunk("b", "vecteur oppose"), [-1.0, 0.0])
    store.add(_chunk("c", "vecteur orthogonal"), [0.0, 1.0])

    results = store.search([1.0, 0.0], top_k=2)

    assert [r["id"] for r in results] == ["a", "c"]
    assert results[0]["score"] > results[1]["score"]


def test_save_and_reload_persists_records(tmp_path):
    path = tmp_path / "store.json"
    store = VectorStore(path)
    store.add(_chunk("a", "hello"), [0.1, 0.2])
    store.save()

    reloaded = VectorStore(path)

    assert len(reloaded.search([0.1, 0.2], top_k=1)) == 1


def test_hybrid_search_finds_exact_acronym_that_embedding_misses(tmp_path):
    store = VectorStore(tmp_path / "store.json")
    # the embedding alone prefers "a" (closest vector), but only "b" contains the term "CV"
    store.add(_chunk("a", "notes sur la cuisine italienne"), [1.0, 0.0])
    store.add(_chunk("b", "mon CV et mon parcours"), [0.0, 1.0])

    results = store.search([1.0, 0.0], top_k=2, query_text="CV")

    assert results[0]["id"] == "b"


def test_hybrid_search_without_query_text_stays_semantic(tmp_path):
    store = VectorStore(tmp_path / "store.json")
    store.add(_chunk("a", "notes sur la cuisine"), [1.0, 0.0])
    store.add(_chunk("b", "mon CV"), [0.0, 1.0])

    results = store.search([1.0, 0.0], top_k=1)

    assert results[0]["id"] == "a"


def test_pdf_loader_strips_private_use_icon_glyphs():
    from app.ingestion.loaders import _PUA_GLYPHS

    assert _PUA_GLYPHS.sub("", "Expérience  Projets ") == "Expérience  Projets "


def test_document_hashes_and_remove_document(tmp_path):
    store = VectorStore(tmp_path / "store.json")
    chunk_a = Chunk(id="a::0", document_id="a", index=0, text="x", metadata={"content_hash": "h1"})
    chunk_b = Chunk(id="b::0", document_id="b", index=0, text="y", metadata={"content_hash": "h2"})
    store.add(chunk_a, [1.0, 0.0])
    store.add(chunk_b, [0.0, 1.0])

    assert store.document_hashes() == {"a": "h1", "b": "h2"}

    store.remove_document("a")

    assert store.document_hashes() == {"b": "h2"}
