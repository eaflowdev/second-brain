from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Second Brain"
    notes_dir: Path = Path(__file__).resolve().parents[3] / "notes_sample"
    data_dir: Path = Path(__file__).resolve().parents[2] / "data"

    class Config:
        env_file = ".env"


settings = Settings()
settings.data_dir.mkdir(exist_ok=True)
