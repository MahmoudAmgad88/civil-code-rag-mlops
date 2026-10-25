"""Construct and cache application resources at their appropriate lifecycle."""

import os
from functools import lru_cache

from civil_code_rag.config import get_settings
from civil_code_rag.generation.answer_generator import AnswerGenerator
from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.retrieval.retriever import Retriever
from civil_code_rag.services.ask_service import AskService


class ServiceUnavailableError(Exception):
    """A runtime resource required for this route is unavailable."""


def require_api_key() -> str:
    """Read the standard key without exposing it in errors or logs."""
    from dotenv import dotenv_values

    key = os.environ.get("OPENAI_API_KEY", dotenv_values(".env").get("OPENAI_API_KEY"))
    if not key or not key.strip():
        raise ServiceUnavailableError(
            "OPENAI_API_KEY is required for generated answers."
        )
    return key


@lru_cache
def get_repository() -> ArticleRepository:
    """Load the small article corpus once per process."""

    try:
        return ArticleRepository(get_settings().corpus_path)
    except (OSError, ValueError, KeyError):
        from fastapi import HTTPException

        raise HTTPException(503, "Corpus is unavailable or invalid.") from None


@lru_cache
def get_retriever() -> Retriever:
    """Lazily load and reuse the embedding model and local index."""

    settings = get_settings()
    from civil_code_rag.release_artifact import MODEL_NAME, MODEL_REVISION

    try:
        from sentence_transformers import SentenceTransformer

        if settings.embedding_model != MODEL_NAME:
            raise ServiceUnavailableError(
                "The release index requires intfloat/multilingual-e5-small."
            )
        revision = MODEL_REVISION
        model = SentenceTransformer(
            settings.embedding_model, revision=revision, device="cpu"
        )
        return Retriever(index_dir=settings.index_dir, model=model)
    except (ImportError, OSError, ValueError):
        raise ServiceUnavailableError(
            "Embedding model or retrieval index is unavailable."
        ) from None


@lru_cache
def get_generator() -> AnswerGenerator:
    """Lazily create and reuse the OpenAI client."""

    from openai import OpenAI

    settings = get_settings()
    return AnswerGenerator(
        client=OpenAI(api_key=require_api_key(), timeout=60.0, max_retries=1),
        model_name=settings.llm_model,
    )


class LazyRetriever:
    """Defer embedding dependencies until semantic search is requested."""

    def search(self, *args, **kwargs):
        require_api_key()
        return get_retriever().search(*args, **kwargs)


class LazyGenerator:
    """Defer OpenAI client construction until generation is requested."""

    def generate(self, *args, **kwargs):
        from openai import OpenAIError

        try:
            return get_generator().generate(*args, **kwargs)
        except OpenAIError:
            raise ServiceUnavailableError(
                "Answer generation is temporarily unavailable."
            ) from None


@lru_cache
def get_ask_service() -> AskService:
    """Return the shared application service used by HTTP requests."""

    return AskService(
        repository=get_repository(),
        retriever=LazyRetriever(),
        generator=LazyGenerator(),
    )
