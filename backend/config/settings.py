"""Environment-backed application settings."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    api_title: str = "Healthcare Conversational AI Assistant"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    frontend_origins: str = "http://localhost:8501"
    credentials_file: Path = PROJECT_ROOT / "backend" / "config" / "credentials.json"
    document_storage_dir: Path = PROJECT_ROOT / "backend" / "storage" / "documents"
    image_storage_dir: Path = PROJECT_ROOT / "backend" / "storage" / "images"
    vector_storage_dir: Path = PROJECT_ROOT / "backend" / "storage" / "vector_db"
    metadata_database: Path = PROJECT_ROOT / "backend" / "storage" / "metadata.sqlite3"
    max_upload_size_mb: int = 50
    chunk_size: int = 1000
    chunk_overlap: int = 150
    retrieval_top_k: int = 5
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 30.0
    auth_token_ttl_hours: int = 12


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
