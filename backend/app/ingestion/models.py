from datetime import datetime
from pathlib import Path

from pydantic import BaseModel


class Document(BaseModel):
    """Unified representation of an ingested source file, before chunking/embeddings."""

    id: str
    source_path: str
    title: str
    content: str
    doc_type: str  # "markdown" | "pdf"
    modified_at: datetime

    @classmethod
    def from_file(cls, path: Path, content: str, doc_type: str) -> "Document":
        stat = path.stat()
        return cls(
            id=path.stem,
            source_path=str(path),
            title=path.stem.replace("_", " ").replace("-", " "),
            content=content,
            doc_type=doc_type,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
        )
