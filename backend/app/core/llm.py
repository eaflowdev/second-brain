import httpx

from typing import Optional

from app.core.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(RuntimeError):
    """Raised when the LLM cannot be called (missing config, API failure, ...)."""


def chat(
    messages: list[dict],
    tools: Optional[list[dict]] = None,
    max_tokens: int = 1024,
    model: Optional[str] = None,
    reasoning: Optional[dict] = None,
) -> dict:
    """Low-level call: returns the raw assistant message (may contain tool_calls
    and, for reasoning-capable models, a "reasoning" field with the model's
    chain of thought). `reasoning` follows OpenRouter's unified format, e.g.
    {"effort": "low" | "medium" | "high"} or {"max_tokens": 2000}."""
    if not settings.openrouter_api_key:
        raise LLMError(
            "OPENROUTER_API_KEY manquante : ajoute-la dans backend/.env pour activer la génération."
        )

    payload = {
        "model": model or settings.generation_model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
    if reasoning:
        payload["reasoning"] = reasoning

    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMError(f"Appel OpenRouter échoué : {exc}") from exc

    body = response.json()
    choices = body.get("choices")
    if not choices:
        # Le pool de modèles :free renvoie parfois un 200 avec un corps d'erreur
        # (rate-limit upstream, provider indisponible...) plutôt qu'un code HTTP.
        raise LLMError(f"Réponse OpenRouter inattendue (pas de 'choices') : {body}")

    message = choices[0]["message"]
    message["usage"] = body.get("usage", {})
    return message


def generate(system: str, user_message: str, max_tokens: int = 1024) -> str:
    message = chat(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        max_tokens=max_tokens,
    )
    return message["content"]

