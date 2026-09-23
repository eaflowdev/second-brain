from pathlib import Path

from pypdf import PdfReader

from app.ingestion.models import Document


def load_markdown(path: Path) -> Document:
    content = path.read_text(encoding="utf-8")
    return Document.from_file(path, content, doc_type="markdown")


def load_pdf(path: Path) -> Document:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    content = "\n\n".join(pages).strip()
    return Document.from_file(path, content, doc_type="pdf")


LOADERS = {
    ".md": load_markdown,
    ".markdown": load_markdown,
    ".pdf": load_pdf,
}
