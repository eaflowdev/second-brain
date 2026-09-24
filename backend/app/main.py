from fastapi import FastAPI

from app.api import agent, embeddings, ingestion, rag
from app.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(ingestion.router)
app.include_router(embeddings.router)
app.include_router(rag.router)
app.include_router(agent.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
