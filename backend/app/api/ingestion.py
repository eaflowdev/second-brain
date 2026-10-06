from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.core.config import settings
from app.ingestion.loaders import LOADERS
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


@router.post("/upload")
async def upload(file: UploadFile) -> dict:
    # path().name strips any directory components a malicious filename could carry.
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    if suffix not in LOADERS:
        raise HTTPException(status_code=400, detail=f"Format non supporté : {suffix or '(aucun)'}")

    # Lit au plus max+1 octets : suffit à détecter un dépassement sans charger un fichier géant en mémoire.
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (maximum {settings.max_upload_bytes // (1024 * 1024)} Mo)",
        )

    destination = settings.notes_dir / filename
    destination.write_bytes(content)

    return {"filename": filename, "saved_to": str(destination)}

