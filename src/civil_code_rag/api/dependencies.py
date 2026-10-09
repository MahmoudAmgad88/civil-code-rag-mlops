"""Construct and cache application resources at their appropriate lifecycle."""

from functools import lru_cache

from civil_code_rag.config import get_settings
from civil_code_rag.generation.answer_generator import AnswerGenerator
from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.retrieval.retriever import Retriever
from civil_code_rag.services.ask_service import AskService


@lru_cache
def get_repository() -> ArticleRepository:
    """Load the small article corpus once per process."""

    return ArticleRepository(get_settings().corpus_path)


@lru_cache
def get_retriever() -> Retriever:
    """Lazily load and reuse the embedding model and local index."""

    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    model = SentenceTransformer(settings.embedding_model)
    return Retriever(index_dir=settings.index_dir, model=model)


@lru_cache
def get_generator() -> AnswerGenerator:
    """Lazily create and reuse the OpenAI client."""

    from openai import OpenAI

    settings = get_settings()
    return AnswerGenerator(client=OpenAI(), model_name=settings.llm_model)


class LazyRetriever:
    """Defer embedding dependencies until semantic search is requested."""

    def search(self, *args, **kwargs):
        return get_retriever().search(*args, **kwargs)


class LazyGenerator:
    """Defer OpenAI client construction until generation is requested."""

    def generate(self, *args, **kwargs):
        return get_generator().generate(*args, **kwargs)


@lru_cache
def get_ask_service() -> AskService:
    """Return the shared application service used by HTTP requests."""

    return AskService(
        repository=get_repository(),
        retriever=LazyRetriever(),
        generator=LazyGenerator(),
    )
