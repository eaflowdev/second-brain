import hashlib
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
    # Hash of the extracted text: lets re-indexing skip documents that did not change.
    content_hash: str

    @classmethod
    def from_file(cls, path: Path, content: str, doc_type: str) -> "Document":
        stat = path.stat()
        return cls(
            # Hash of the full path, not the stem: "cv.md" and "cv.pdf" must not share an id.
            id=hashlib.sha1(str(path).encode()).hexdigest()[:16],
            source_path=str(path),
            title=path.stem.replace("_", " ").replace("-", " "),
            content=content,
            doc_type=doc_type,
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
        )
