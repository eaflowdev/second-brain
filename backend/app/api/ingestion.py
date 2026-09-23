from fastapi import APIRouter

from app.core.config import settings
from app.ingestion.service import scan_notes_dir

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.get("/scan")
def scan() -> dict:
    documents = scan_notes_dir(settings.notes_dir)
    return {
        "count": len(documents),
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "doc_type": doc.doc_type,
                "source_path": doc.source_path,
                "content_preview": doc.content[:200],
            }
            for doc in documents
        ],
    }
