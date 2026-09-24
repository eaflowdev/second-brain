import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.loop import run_agent, run_agent_stream
from app.agents.orchestrator import run_orchestrator
from app.core.llm import LLMError

router = APIRouter(prefix="/agent", tags=["agent"])


class AskRequest(BaseModel):
    question: str
    # "low" | "medium" | "high" (voir OpenRouter reasoning.effort) - None = comportement par défaut du modèle
    reasoning_effort: Optional[str] = None
    # Marque le system prompt comme cacheable (cache_control) - utile sur les modèles qui le supportent
    cache_system_prompt: bool = False


@router.post("/ask")
def ask(request: AskRequest) -> dict:
    reasoning = {"effort": request.reasoning_effort} if request.reasoning_effort else None
    try:
        return run_agent(
            request.question, reasoning=reasoning, cache_system_prompt=request.cache_system_prompt
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
def ask_stream(question: str, reasoning_effort: Optional[str] = None) -> StreamingResponse:
    reasoning = {"effort": reasoning_effort} if reasoning_effort else None

    def event_generator():
        try:
            for event in run_agent_stream(question, reasoning=reasoning):
                yield _sse_format(event)
        except LLMError as exc:
            yield _sse_format({"type": "error", "message": str(exc)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")
