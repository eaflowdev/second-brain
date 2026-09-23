from fastapi import APIRouter

from app.core.config import settings
from app.embeddings.embedder import Embedder
from app.embeddings.models import chunk_document
from app.ingestion.service import scan_notes_dir
from app.storage.vector_store import get_vector_store

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

_embedder = Embedder()
_store = get_vector_store()


@router.post("/index")
def index() -> dict:
    """Re-scan notes_dir, chunk + embed everything, replace the vector store."""
    documents = scan_notes_dir(settings.notes_dir)
    _store.clear()

    total_chunks = 0
    for document in documents:
        chunks = chunk_document(document)
        if not chunks:
            continue

        vectors = _embedder.embed([chunk.text for chunk in chunks])
        for chunk, vector in zip(chunks, vectors):
            _store.add(chunk, vector)
        total_chunks += len(chunks)

    _store.save()
    return {"documents_indexed": len(documents), "chunks_indexed": total_chunks}


@router.get("/search")
def search(q: str, top_k: int = 5) -> dict:
    query_vector = _embedder.embed([q])[0]
    results = _store.search(query_vector, top_k=top_k)
    return {
        "query": q,
        "results": [
            {"score": r["score"], "text": r["text"], "metadata": r["metadata"]}
            for r in results
        ],
    }
