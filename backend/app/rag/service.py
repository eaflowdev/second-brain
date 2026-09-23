from app.core.llm import generate
from app.embeddings.embedder import Embedder
from app.rag.prompt import SYSTEM_PROMPT, build_user_message
from app.storage.vector_store import get_vector_store

_embedder = Embedder()


def answer_question(question: str, top_k: int = 5) -> dict:
    store = get_vector_store()
    query_vector = _embedder.embed([question])[0]
    chunks = store.search(query_vector, top_k=top_k)

    if not chunks:
        return {"answer": "Je n'ai trouvé aucune note pertinente pour répondre.", "sources": []}

    user_message = build_user_message(question, chunks)
    answer = generate(SYSTEM_PROMPT, user_message)

    sources = [
        {
            "title": chunk["metadata"]["title"],
            "source_path": chunk["metadata"]["source_path"],
            "score": chunk["score"],
        }
        for chunk in chunks
    ]
    return {"answer": answer, "sources": sources}
