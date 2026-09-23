from app.ingestion.service import scan_notes_dir
from app.core.config import settings


def test_scan_notes_dir_finds_sample_markdown():
    documents = scan_notes_dir(settings.notes_dir)

    assert any(doc.doc_type == "markdown" for doc in documents)
    assert all(doc.content for doc in documents)
