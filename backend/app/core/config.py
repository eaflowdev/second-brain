from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Second Brain"
    notes_dir: Path = Path(__file__).resolve().parents[3] / "notes_sample"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"

    # OpenRouter: passerelle gratuite vers de nombreux modèles (dont certains :free).
    # Modèles gratuits à jour sur https://openrouter.ai/models?max_price=0
    openrouter_api_key: Optional[str] = None
    generation_model: str = "z-ai/glm-5.2:free"

    class Config:
        env_file = ".env"


settings = Settings()
settings.data_dir.mkdir(exist_ok=True)
