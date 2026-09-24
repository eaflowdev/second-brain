from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.loop import run_agent
from app.core.llm import LLMError

router = APIRouter(prefix="/agent", tags=["agent"])


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask(request: AskRequest) -> dict:
    try:
        return run_agent(request.question)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
