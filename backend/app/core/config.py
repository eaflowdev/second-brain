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
    # Tool calling natif : tous les modèles :free ne le supportent pas (vérifier
    # "tools" dans supported_parameters via GET /api/v1/models avant de changer).
    agent_model: str = "nvidia/nemotron-3-super-120b-a12b:free"

    # Tavily: recherche web pensée pour les agents LLM. Clé gratuite sur https://tavily.com
    tavily_api_key: Optional[str] = None

    class Config:
        # Chemin absolu : un serveur MCP est lancé par Claude Desktop avec un cwd
        # imprévisible, un chemin relatif ".env" ne serait pas trouvé de manière fiable.
        env_file = Path(__file__).resolve().parents[2] / ".env"


settings = Settings()
settings.data_dir.mkdir(exist_ok=True)
