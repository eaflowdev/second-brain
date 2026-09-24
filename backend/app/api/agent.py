import json
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.loop import run_agent, run_agent_stream
from app.agents.orchestrator import run_orchestrator
from app.core.llm import LLMError

router = APIRouter(prefix="/agent", tags=["agent"])


class Turn(BaseModel):
    # Uniquement user/assistant : un "system" venu du client serait une injection de prompt.
    role: Literal["user", "assistant"]
    content: str


def _parse_history(raw: Optional[str]) -> Optional[list[dict]]:
    if not raw:
        return None
    try:
        return [Turn(**turn).model_dump() for turn in json.loads(raw)]
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=f"history invalide : {exc}") from exc


class AskRequest(BaseModel):
    question: str
    # "low" | "medium" | "high" (voir OpenRouter reasoning.effort) - None = comportement par défaut du modèle
    reasoning_effort: Optional[str] = None
    # Marque le system prompt comme cacheable (cache_control) - utile sur les modèles qui le supportent
    cache_system_prompt: bool = False
    # Tours précédents de la conversation ([{role, content}, ...], question+réponse finale uniquement)
    history: Optional[list[Turn]] = None
    # Résume les anciens tours au lieu de les tronquer (1 appel LLM en plus)
    summarize_history: bool = False


@router.post("/ask")
def ask(request: AskRequest) -> dict:
    reasoning = {"effort": request.reasoning_effort} if request.reasoning_effort else None
    try:
        return run_agent(
            request.question,
            reasoning=reasoning,
            cache_system_prompt=request.cache_system_prompt,
            history=[t.model_dump() for t in request.history] if request.history else None,
            summarize_history=request.summarize_history,
        )
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/orchestrate")
def orchestrate(request: AskRequest) -> dict:
    reasoning = {"effort": request.reasoning_effort} if request.reasoning_effort else None
    try:
        return run_orchestrator(request.question, reasoning=reasoning)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _sse_format(event: dict) -> str:
    """One Server-Sent Event: a `data:` line with a JSON payload, blank line
    to terminate it — the exact format `EventSource` on the browser expects."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.get("/ask/stream")
def ask_stream(
    question: str, reasoning_effort: Optional[str] = None, history: Optional[str] = None,
    summarize_history: bool = False,
) -> StreamingResponse:
    reasoning = {"effort": reasoning_effort} if reasoning_effort else None
    # EventSource ne supporte que GET (pas de corps JSON) : l'historique voyage
    # en query param, sérialisé en JSON par le frontend.
    parsed_history = _parse_history(history)

    def event_generator():
        try:
            for event in run_agent_stream(question, reasoning=reasoning,
                history=parsed_history,
                summarize_history=summarize_history,
            ):
                yield _sse_format(event)
        except LLMError as exc:
            yield _sse_format({"type": "error", "message": str(exc)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
