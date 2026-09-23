import json
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.config import settings
from app.embeddings.models import Chunk


class VectorStore:
    """Minimal cosine-similarity vector store, persisted as a flat JSON file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._records: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return []

    def save(self) -> None:
        self.path.write_text(json.dumps(self._records))

    def clear(self) -> None:
        self._records = []

    def add(self, chunk: Chunk, vector: list[float]) -> None:
        self._records.append(
            {
                "id": chunk.id,
                "document_id": chunk.document_id,
                "text": chunk.text,
                "metadata": chunk.metadata,
                "vector": vector,
            }
        )

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        if not self._records:
            return []

        vectors = np.array([record["vector"] for record in self._records])
        query = np.array(query_vector)

        # cosine similarity: dot product of the vectors, normalized by their magnitudes
        norms = np.linalg.norm(vectors, axis=1) * np.linalg.norm(query)
        scores = (vectors @ query) / np.where(norms == 0, 1e-10, norms)

        top_indices = np.argsort(-scores)[:top_k]
        return [
            {**self._records[i], "score": float(scores[i])} for i in top_indices
        ]


_shared_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Process-wide singleton so every route sees the same in-memory index."""
    global _shared_store
    if _shared_store is None:
        _shared_store = VectorStore(settings.data_dir / "vector_store.json")
    return _shared_store
