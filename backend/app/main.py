from fastapi import FastAPI

from app.api import ingestion
from app.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(ingestion.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
