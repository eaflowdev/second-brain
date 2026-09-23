import re

DEFAULT_CHUNK_SIZE = 800
DEFAULT_OVERLAP = 150


def split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    """Group paragraphs into ~chunk_size chars, carrying the tail of the previous
    chunk forward so a chunk boundary never fully severs the context."""
    chunks: list[str] = []
    current = ""

    for paragraph in split_paragraphs(text):
        if current and len(current) + len(paragraph) + 2 > chunk_size:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{paragraph}".strip() if tail else paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip() if current else paragraph

    if current:
        chunks.append(current)

    return chunks
