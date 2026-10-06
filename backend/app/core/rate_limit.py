import time
from collections import defaultdict, deque
from threading import Lock
from typing import Callable

from fastapi import HTTPException, Request

from app.core.config import settings


class RateLimiter:
    """Sliding-window limit per client IP, used as a FastAPI dependency.

    In-memory, so it covers a single process. Behind a reverse proxy, every request
    shares the proxy's IP and the limit becomes global: read the real client IP
    from the proxy headers in that case (uvicorn --proxy-headers)."""

    def __init__(self, max_calls: int, window_seconds: float = 60.0, clock: Callable[[], float] = time.monotonic):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def __call__(self, request: Request) -> None:
        key = request.client.host if request.client else "unknown"
        now = self.clock()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] >= self.window_seconds:
                hits.popleft()
            if len(hits) >= self.max_calls:
                raise HTTPException(
                    status_code=429,
                    detail="Trop de requêtes : réessaie dans une minute.",
                )
            hits.append(now)


# Un seul budget partagé par tous les endpoints coûteux (appels LLM, RAG, réindexation).
costly_endpoint_limit = RateLimiter(settings.rate_limit_per_minute)
