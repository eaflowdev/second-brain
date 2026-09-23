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
