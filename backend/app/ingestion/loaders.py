import re
from pathlib import Path

from pypdf import PdfReader

from app.ingestion.models import Document

# Private Use Area: icon glyphs embedded by PDF templates (e.g. ), not real text
_PUA_GLYPHS = re.compile(r"[-]")


def load_markdown(path: Path) -> Document:
    content = path.read_text(encoding="utf-8")
    return Document.from_file(path, content, doc_type="markdown")


def load_pdf(path: Path) -> Document:
    reader = PdfReader(str(path))
    pages = [_PUA_GLYPHS.sub("", page.extract_text() or "") for page in reader.pages]
    content = "\n\n".join(pages).strip()
    return Document.from_file(path, content, doc_type="pdf")


LOADERS = {
    ".md": load_markdown,
    ".markdown": load_markdown,
    ".pdf": load_pdf,
}
