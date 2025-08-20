from pydantic import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DATABASE_URL: str

    class Config:
        # Go up two levels from core/config.py → project root
        env_file = str(Path(__file__).resolve().parents[2] / ".env")

settings = Settings()
