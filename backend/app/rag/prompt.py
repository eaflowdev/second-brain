SYSTEM_PROMPT = (
    "Tu es l'assistant de révision de Second Brain. Réponds UNIQUEMENT à partir "
    "du contexte ci-dessous, extrait des notes personnelles de l'utilisateur. "
    "Si le contexte ne permet pas de répondre, dis-le clairement plutôt que "
    "d'inventer. Cite le titre de la note source quand c'est pertinent."
)


def build_user_message(question: str, chunks: list[dict]) -> str:
    context = "\n\n---\n\n".join(
        f"[Source: {chunk['metadata']['title']}]\n{chunk['text']}" for chunk in chunks
    )
    return f"Contexte (extrait de mes notes) :\n\n{context}\n\nQuestion : {question}"
