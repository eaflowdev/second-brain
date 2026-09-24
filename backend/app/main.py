from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent, embeddings, ingestion, rag
from app.core.config import settings

app = FastAPI(title=settings.app_name)

# Le frontend (Vite, port 5173 par défaut) tourne sur une origine différente
# du backend (uvicorn, port 8000) : sans CORS, le navigateur bloquerait les
# requêtes fetch/EventSource entre les deux.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router)
app.include_router(embeddings.router)
app.include_router(rag.router)
app.include_router(agent.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
