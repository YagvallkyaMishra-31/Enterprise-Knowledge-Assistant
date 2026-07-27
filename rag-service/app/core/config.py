"""Centralised configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings sourced from the process environment."""

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "knowledge_assistant")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "postgres")
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "default-dev-key")
    UPLOAD_ROOT_PATH: str = os.getenv("UPLOAD_ROOT_PATH", "/app/uploads")


settings = Settings()
