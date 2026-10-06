from fastapi import APIRouter, Depends

from app.core.config import settings
from app.core.rate_limit import costly_endpoint_limit
from app.embeddings.embedder import Embedder
from app.embeddings.models import chunk_document
from app.ingestion.service import scan_notes_dir
from app.storage.vector_store import get_vector_store

router = APIRouter(prefix="/embeddings", tags=["embeddings"])

_embedder = Embedder()
_store = get_vector_store()


@router.post("/index", dependencies=[Depends(costly_endpoint_limit)])
def index() -> dict:
    """Re-scan notes_dir and embed only what changed: new or modified documents are
    (re)embedded, unchanged ones are kept, and deleted ones are dropped from the store."""
    documents = scan_notes_dir(settings.notes_dir)
    indexed_hashes = _store.document_hashes()
    current_ids = {document.id for document in documents}

    removed = [doc_id for doc_id in indexed_hashes if doc_id not in current_ids]
    for doc_id in removed:
        _store.remove_document(doc_id)

    total_chunks = 0
    reindexed = 0
    for document in documents:
        if indexed_hashes.get(document.id) == document.content_hash:
            continue

        _store.remove_document(document.id)
        chunks = chunk_document(document)
        reindexed += 1
        if not chunks:
            continue

        vectors = _embedder.embed([chunk.text for chunk in chunks])
        for chunk, vector in zip(chunks, vectors):
            _store.add(chunk, vector)
        total_chunks += len(chunks)

    _store.save()
    return {
        "documents_indexed": len(documents),
        "chunks_indexed": total_chunks,
        "documents_reindexed": reindexed,
        "documents_removed": len(removed),
    }


@router.get("/search")
def search(q: str, top_k: int = 5) -> dict:
    query_vector = _embedder.embed([q])[0]
    results = _store.search(query_vector, top_k=top_k, query_text=q)
    return {
        "query": q,
        "results": [
            {"score": r["score"], "text": r["text"], "metadata": r["metadata"]}
            for r in results
        ],
    }
