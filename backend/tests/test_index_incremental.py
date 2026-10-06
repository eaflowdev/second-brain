from app.api import embeddings as api
from app.core.config import settings
from app.storage.vector_store import VectorStore


class FakeEmbedder:
    def __init__(self):
        self.calls = 0

    def embed(self, texts):
        self.calls += len(texts)
        return [[1.0, 0.0] for _ in texts]


def _run_index(monkeypatch, notes_dir, store, embedder):
    monkeypatch.setattr(settings, "notes_dir", notes_dir)
    monkeypatch.setattr(api, "_store", store)
    monkeypatch.setattr(api, "_embedder", embedder)
    return api.index()


def test_index_only_reembeds_changed_documents(tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "a.md").write_text("# A\n\ncontenu de a")
    (notes / "b.md").write_text("# B\n\ncontenu de b")
    store = VectorStore(tmp_path / "store.json")
    embedder = FakeEmbedder()

    first = _run_index(monkeypatch, notes, store, embedder)
    assert first["documents_reindexed"] == 2

    embedder.calls = 0
    unchanged = _run_index(monkeypatch, notes, store, embedder)
    assert unchanged["documents_reindexed"] == 0
    assert embedder.calls == 0

    (notes / "a.md").write_text("# A\n\ncontenu modifié")
    changed = _run_index(monkeypatch, notes, store, embedder)
    assert changed["documents_reindexed"] == 1
    assert embedder.calls == 1

    (notes / "b.md").unlink()
    deleted = _run_index(monkeypatch, notes, store, embedder)
    assert deleted["documents_removed"] == 1
    assert len(store.document_hashes()) == 1


def test_documents_with_same_stem_get_distinct_ids(tmp_path, monkeypatch):
    from app.ingestion.models import Document

    md = tmp_path / "cv.md"
    pdf = tmp_path / "cv.pdf"
    md.write_text("x")
    pdf.write_text("x")

    assert Document.from_file(md, "x", "markdown").id != Document.from_file(pdf, "x", "pdf").id
