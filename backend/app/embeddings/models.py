from pydantic import BaseModel

from app.embeddings.chunking import chunk_text
from app.ingestion.models import Document


class Chunk(BaseModel):
    """A slice of a Document, small enough to be embedded meaningfully."""

    id: str
    document_id: str
    index: int
    text: str
    metadata: dict


def chunk_document(document: Document) -> list[Chunk]:
    metadata = {
        "title": document.title,
        "source_path": document.source_path,
        "doc_type": document.doc_type,
    }

    return [
        Chunk(
            id=f"{document.id}::{index}",
            document_id=document.id,
            index=index,
            text=text,
            metadata=metadata,
        )
        for index, text in enumerate(chunk_text(document.content))
    ]
