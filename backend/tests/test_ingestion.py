from app.ingestion.service import scan_notes_dir
from app.core.config import settings


def test_scan_notes_dir_finds_sample_markdown():
    documents = scan_notes_dir(settings.notes_dir)

    assert any(doc.doc_type == "markdown" for doc in documents)
    assert all(doc.content for doc in documents)


def test_upload_endpoint_saves_markdown_file():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    path = settings.notes_dir / "note_upload_test.md"

    try:
        response = client.post(
            "/ingestion/upload",
            files={"file": ("note_upload_test.md", b"# Test\n\ncontenu de test", "text/markdown")},
        )

        assert response.status_code == 200
        assert path.read_text() == "# Test\n\ncontenu de test"
    finally:
        path.unlink(missing_ok=True)


def test_upload_endpoint_rejects_unsupported_format():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    response = client.post(
        "/ingestion/upload",
        files={"file": ("virus.exe", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 400
