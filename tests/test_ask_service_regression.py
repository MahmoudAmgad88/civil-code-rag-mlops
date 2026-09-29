"""Real-corpus regression coverage for the migrated AskService."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.services.ask_service import (
    AmbiguousArticleRequestError,
    ArticleNotFoundError,
    AskService,
    CitationValidationError,
)

CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "articles.jsonl"


def create_service() -> AskService:
    return AskService(ArticleRepository(CORPUS_PATH), Mock(), Mock())


def test_exact_lookup_preserves_complete_response_contract():
    result = create_service().ask("What does Article 91 say?")
    assert set(result) == {
        "route", "language", "article_id", "answer", "source_note",
        "verified_status", "pdf_pages",
    }
    assert result["article_id"] == "CC-91"


def test_explain_uses_only_requested_article():
    service = create_service()
    service.generator.generate.return_value = "Explanation [CC-91]."
    result = service.ask("Explain Article 91")
    assert result["route"] == "explain"
    service.retriever.search.assert_not_called()
    context = service.generator.generate.call_args.kwargs["context"]
    assert "[SOURCE: CC-91]" in context
    assert "[SOURCE: CC-60]" not in context


def test_semantic_route_keeps_language_isolation():
    service = create_service()
    service.retriever.search.return_value = [
        {"record": {"article_id": "CC-91", "language": "en"}, "similarity": 0.95}
    ]
    service.generator.generate.return_value = "Grounded answer [CC-91]."
    result = service.ask("When does an expression of intent take effect?")
    assert result["route"] == "semantic"
    service.retriever.search.assert_called_once_with(
        question="When does an expression of intent take effect?", language="en", top_k=5
    )


@pytest.mark.parametrize(
    ("question", "exception"),
    [
        ("What does Article 200 say?", ArticleNotFoundError),
        ("Article 91", AmbiguousArticleRequestError),
        ("   ", ValueError),
    ],
)
def test_application_errors(question, exception):
    with pytest.raises(exception):
        create_service().ask(question)


def test_invalid_generated_citation_is_rejected():
    service = create_service()
    service.generator.generate.return_value = "Unsupported claim [CC-200]."
    with pytest.raises(CitationValidationError):
        service.ask("Explain Article 91")
