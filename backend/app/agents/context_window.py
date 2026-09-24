from app.core.llm import chat

# Heuristique simple (pas de vrai tokenizer) : ~4 caractères par token en
# moyenne pour du texte français/anglais courant. Assez précis pour prendre une
# décision de troncature, pas assez pour un comptage facturable exact.
CHARS_PER_TOKEN = 4

SUMMARY_PROMPT_TEMPLATE = (
    "Résume en 3-5 phrases les échanges suivants entre un utilisateur et son "
    "assistant de révision, en conservant les faits et décisions importants, "
    "pas la forme de la conversation :\n\n{conversation}"
)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def count_history_tokens(history: list[dict]) -> int:
    return sum(estimate_tokens(turn["content"]) for turn in history)


def compact_history(history: list[dict], max_tokens: int) -> list[dict]:
    """Sliding window: keep the most recent turns that fit the budget, drop the
    oldest first. Cheap and dependency-free — no LLM call needed, so it never
    fails/costs anything, unlike summarize_history() below. This is the default
    strategy; summarization is an opt-in upgrade when preserving older context
    matters more than the extra LLM call."""
    kept: list[dict] = []
    budget = max_tokens

    for turn in reversed(history):
        cost = estimate_tokens(turn["content"])
        if kept and cost > budget:
            break
        kept.append(turn)
        budget -= cost

    return list(reversed(kept))


def summarize_history(history: list[dict]) -> str:
    """Condense the whole history into a short summary via one LLM call —
    preserves meaning better than truncation, at the cost of an extra request
    (and its latency/price) every time it's triggered."""
    conversation = "\n".join(f"{turn['role']}: {turn['content']}" for turn in history)
    prompt = SUMMARY_PROMPT_TEMPLATE.format(conversation=conversation)
    message = chat([{"role": "user", "content": prompt}])
    return message.get("content") or ""


def build_context(history: list[dict], max_tokens: int, summarize: bool = False) -> list[dict]:
    """Bound the history to `max_tokens`. Default = sliding window. With
    `summarize`, the turns that don't fit are condensed into one summary message
    (falls back to plain truncation if the LLM call fails or returns nothing)."""
    kept = compact_history(history, max_tokens)
    dropped = history[: len(history) - len(kept)]
    if not summarize or not dropped:
        return kept

    try:
        summary = summarize_history(dropped)
    except Exception:
        return kept
    if not summary:
        return kept
    return [{"role": "system", "content": f"Résumé des échanges précédents : {summary}"}, *kept]
