import pytest
from fastapi import HTTPException

from app.core.config import settings
from app.core.rate_limit import RateLimiter


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def _request(host="1.2.3.4"):
    from starlette.requests import Request

    scope = {"type": "http", "client": (host, 1234), "headers": []}
    return Request(scope)


def test_rate_limiter_blocks_after_max_calls_then_recovers():
    clock = FakeClock()
    limiter = RateLimiter(max_calls=2, window_seconds=60, clock=clock)

    limiter(_request())
    limiter(_request())
    with pytest.raises(HTTPException) as exc:
        limiter(_request())
    assert exc.value.status_code == 429

    clock.now = 61  # la fenêtre glissante est passée
    limiter(_request())


def test_rate_limiter_counts_each_ip_separately():
    limiter = RateLimiter(max_calls=1, window_seconds=60, clock=FakeClock())

    limiter(_request("1.1.1.1"))
    limiter(_request("2.2.2.2"))  # une autre IP n'est pas bloquée


def test_upload_rejects_file_over_size_limit(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr(settings, "max_upload_bytes", 10)
    monkeypatch.setattr(settings, "notes_dir", tmp_path)

    response = TestClient(app).post(
        "/ingestion/upload",
        files={"file": ("big.md", b"x" * 11, "text/markdown")},
    )

    assert response.status_code == 413
    assert not (tmp_path / "big.md").exists()
