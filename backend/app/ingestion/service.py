import logging
from pathlib import Path

from app.ingestion.loaders import LOADERS
from app.ingestion.models import Document

logger = logging.getLogger(__name__)


def scan_notes_dir(notes_dir: Path) -> list[Document]:
    """Walk notes_dir, load every supported file into a Document, skip the rest."""
    documents: list[Document] = []

    for path in sorted(notes_dir.rglob("*")):
        if not path.is_file():
            continue

        loader = LOADERS.get(path.suffix.lower())
        if loader is None:
            continue

        try:
            documents.append(loader(path))
        except Exception:
            logger.exception("Failed to ingest %s", path)

    return documents
