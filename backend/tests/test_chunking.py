from app.embeddings.chunking import chunk_text


def test_chunk_text_splits_long_content_into_multiple_chunks():
    paragraphs = [f"Paragraphe numero {i} avec un peu de contenu." for i in range(20)]
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text, chunk_size=200, overlap=50)

    assert len(chunks) > 1
    assert all(len(chunk) > 0 for chunk in chunks)


def test_chunk_text_keeps_short_text_as_single_chunk():
    text = "Une seule courte note."

    chunks = chunk_text(text, chunk_size=800, overlap=150)

    assert chunks == [text]


def test_chunk_text_overlap_carries_context_across_boundary():
    paragraphs = [f"Paragraphe {i} " + "x" * 40 for i in range(10)]
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text, chunk_size=150, overlap=30)

    assert len(chunks) > 1
    # the tail of a chunk should reappear at the start of the next one
    assert chunks[0][-30:] in chunks[1]
