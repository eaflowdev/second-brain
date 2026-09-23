from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm import LLMError
from app.rag.service import answer_question

router = APIRouter(prefix="/rag", tags=["rag"])


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


@router.post("/ask")
def ask(request: AskRequest) -> dict:
    try:
        return answer_question(request.question, top_k=request.top_k)
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
