"""Portable application settings and repository data locations."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings configurable through ``CIVIL_CODE_RAG_*`` variables."""

    model_config = SettingsConfigDict(
        env_prefix="CIVIL_CODE_RAG_",
        extra="ignore",
    )

    corpus_path: Path = PROJECT_ROOT / "data" / "processed" / "articles.jsonl"
    index_dir: Path = PROJECT_ROOT / "data" / "index"
    embedding_model: str = "intfloat/multilingual-e5-small"
    llm_model: str = "gpt-4.1-mini"


@lru_cache
def get_settings() -> Settings:
    """Return one settings object for the process."""

    return Settings()
