import httpx

from app.core.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(RuntimeError):
    """Raised when the LLM cannot be called (missing config, API failure, ...)."""


def generate(system: str, user_message: str, max_tokens: int = 1024) -> str:
    if not settings.openrouter_api_key:
        raise LLMError(
            "OPENROUTER_API_KEY manquante : ajoute-la dans backend/.env pour activer la génération."
        )

    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
            json={
                "model": settings.generation_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LLMError(f"Appel OpenRouter échoué : {exc}") from exc

    return response.json()["choices"][0]["message"]["content"]
