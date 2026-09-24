from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.loop import run_agent
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
