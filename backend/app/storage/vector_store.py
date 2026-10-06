import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Optional

import numpy as np

from app.core.config import settings
from app.embeddings.models import Chunk

# Reciprocal Rank Fusion constant (standard value from the RRF paper)
RRF_K = 60
BM25_K1 = 1.5
BM25_B = 0.75


def _tokenize(text: str) -> list[str]:
    """Lowercase, strip accents, keep alphanumeric tokens of 2+ chars ("CV", "RAG", "IA")."""
    normalized = unicodedata.normalize("NFKD", text.lower())
    without_accents = "".join(c for c in normalized if not unicodedata.combining(c))
    return [t for t in re.findall(r"[a-z0-9]+", without_accents) if len(t) >= 2]


def _bm25_scores(query: str, texts: list[str]) -> list[float]:
    """Okapi BM25 score of each text against the query (exact term matching)."""
    query_terms = set(_tokenize(query))
    docs = [Counter(_tokenize(t)) for t in texts]
    lengths = [sum(d.values()) for d in docs]
    avg_len = (sum(lengths) / len(lengths)) if lengths else 0.0
    n = len(docs)

    scores = []
    for doc, length in zip(docs, lengths):
        score = 0.0
        for term in query_terms:
            tf = doc.get(term, 0)
            if tf == 0:
                continue
            df = sum(1 for d in docs if term in d)
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            norm = tf + BM25_K1 * (1 - BM25_B + BM25_B * length / (avg_len or 1.0))
            score += idf * tf * (BM25_K1 + 1) / norm
        scores.append(score)
    return scores


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

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        query_text: Optional[str] = None,
    ) -> list[dict]:
        """Semantic search; when `query_text` is given, fuse it with BM25 keyword search (hybrid)."""
        if not self._records:
            return []

        vectors = np.array([record["vector"] for record in self._records])
        query = np.array(query_vector)

        # cosine similarity: dot product of the vectors, normalized by their magnitudes
        norms = np.linalg.norm(vectors, axis=1) * np.linalg.norm(query)
        semantic = (vectors @ query) / np.where(norms == 0, 1e-10, norms)

        if query_text is None:
            top_indices = np.argsort(-semantic)[:top_k]
            return [
                {**self._records[i], "score": float(semantic[i])} for i in top_indices
            ]

        lexical = _bm25_scores(query_text, [record["text"] for record in self._records])
        fused = _reciprocal_rank_fusion(semantic.tolist(), lexical)

        top_indices = sorted(range(len(fused)), key=lambda i: -fused[i])[:top_k]
        return [
            {**self._records[i], "score": float(fused[i])} for i in top_indices
        ]


def _reciprocal_rank_fusion(semantic: list[float], lexical: list[float]) -> list[float]:
    """Sum 1/(RRF_K + rank) over both rankings; robust to the two score scales differing."""
    fused = [0.0] * len(semantic)
    for rank, i in enumerate(sorted(range(len(semantic)), key=lambda i: -semantic[i]), start=1):
        fused[i] += 1.0 / (RRF_K + rank)
    # a zero BM25 score means no query term matched: don't reward it with a rank
    matched = [i for i in range(len(lexical)) if lexical[i] > 0]
    for rank, i in enumerate(sorted(matched, key=lambda i: -lexical[i]), start=1):
        fused[i] += 1.0 / (RRF_K + rank)
    return fused


_shared_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Process-wide singleton so every route sees the same in-memory index."""
    global _shared_store
    if _shared_store is None:
        _shared_store = VectorStore(settings.data_dir / "vector_store.json")
    return _shared_store
