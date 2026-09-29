"""Regression tests comparing AskService with the legacy API."""

from pathlib import Path

from fastapi.testclient import TestClient

import scripts.api as legacy_api

from civil_code_rag.repositories.article_repository import (
    ArticleRepository,
)
from civil_code_rag.services.ask_service import AskService
from unittest.mock import Mock

from civil_code_rag.retrieval.context_builder import build_context

import pytest

from civil_code_rag.services.ask_service import (
    AmbiguousArticleRequestError,
    ArticleNotFoundError,
    CitationValidationError,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CORPUS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "articles.jsonl"
)


def create_service() -> AskService:
    """Create AskService for routes that do not need retrieval or LLM."""

    repository = ArticleRepository(CORPUS_PATH)

    return AskService(
        repository=repository,
        retriever=object(),
        generator=object(),
    )


legacy_client = TestClient(legacy_api.app)


def test_out_of_scope_matches_legacy_api():
    question = (
        "ما عقوبة جريمة القتل العمد "
        "في قانون العقوبات المصري؟"
    )

    service_result = create_service().ask(question)

    legacy_response = legacy_client.post(
        "/ask",
        json={"question": question},
    )

    assert legacy_response.status_code == 200

    assert service_result == legacy_response.json()


def test_exact_article_matches_legacy_api():
    question = "ما نص المادة ٩١؟"

    service_result = create_service().ask(question)

    legacy_response = legacy_client.post(
        "/ask",
        json={"question": question},
    )

    assert legacy_response.status_code == 200

    assert service_result == legacy_response.json()


def test_repealed_article_matches_legacy_api():
    question = "ما نص المادة ٦٠؟"

    service_result = create_service().ask(question)

    legacy_response = legacy_client.post(
        "/ask",
        json={"question": question},
    )

    assert legacy_response.status_code == 200

    assert service_result == legacy_response.json()
def test_explain_matches_legacy_api(monkeypatch):
    """Both implementations must explain the same requested article."""

    question = "اشرح المادة ٩١"

    fake_answer = "شرح تجريبي للمادة القانونية [CC-91]."

    # New implementation
    service = create_service()

    fake_generator = Mock()
    fake_generator.generate.return_value = fake_answer

    fake_retriever = Mock()
    fake_retriever.search.side_effect = AssertionError(
        "Explain must not perform semantic retrieval."
    )

    service.generator = fake_generator
    service.retriever = fake_retriever

    # Legacy implementation: replace only its OpenAI call.
    monkeypatch.setattr(
        legacy_api,
        "generate_answer",
        lambda question, context: fake_answer,
    )

    new_result = service.ask(question)

    legacy_response = legacy_client.post(
        "/ask",
        json={"question": question},
    )

    assert legacy_response.status_code == 200
    assert new_result == legacy_response.json()

    # The new service must use only the requested article.
    fake_retriever.search.assert_not_called()
    fake_generator.generate.assert_called_once()

    context = fake_generator.generate.call_args.kwargs["context"]

    assert "[SOURCE: CC-91]" in context
    assert "[SOURCE: CC-60]" not in context

def test_semantic_matches_legacy_api(monkeypatch):
    """Both implementations must return the same semantic API response."""

    question = "متى ينتج التعبير عن الإرادة أثره القانوني؟"

    fake_answer = (
        "ينتج التعبير عن الإرادة أثره عند العلم به [CC-91]."
    )

    service = create_service()

    # Controlled retrieval result: no embedding model required.
    fake_results = [
        {
            "record": {
                "article_id": "CC-91",
                "language": "ar",
            },
            "similarity": 0.95,
        }
    ]

    fake_retriever = Mock()
    fake_retriever.search.return_value = fake_results

    fake_generator = Mock()
    fake_generator.generate.return_value = fake_answer

    service.retriever = fake_retriever
    service.generator = fake_generator

    # Build the evidence from the same real corpus.
    context = build_context(
        results=fake_results,
        article_lookup=service.repository.articles,
        language="ar",
    )

    # Replace the legacy external dependencies.
    monkeypatch.setattr(
        legacy_api,
        "retrieve_evidence",
        lambda question, language: context,
    )

    monkeypatch.setattr(
        legacy_api,
        "generate_answer",
        lambda question, context: fake_answer,
    )

    new_result = service.ask(question)

    legacy_response = legacy_client.post(
        "/ask",
        json={"question": question},
    )

    assert legacy_response.status_code == 200
    assert new_result == legacy_response.json()

    fake_retriever.search.assert_called_once_with(
        question=question,
        language="ar",
        top_k=5,
    )

    fake_generator.generate.assert_called_once_with(
        question=question,
        context=context,
    )

@pytest.mark.parametrize(
    ("question", "expected_exception", "expected_status"),
    [
        ("ما نص المادة ٢٠٠؟", ArticleNotFoundError, 404),
        ("المادة ٩١", AmbiguousArticleRequestError, 422),
        ("   ", ValueError, 422),
    ],
)
def test_application_errors_match_legacy_api(
    question,
    expected_exception,
    expected_status,
):
    service = create_service()

    # The current HTTP behavior is our regression baseline.
    legacy_response = legacy_client.post(
        "/ask",
        json={"question": question},
    )

    # The new service is independent of HTTP.
    with pytest.raises(expected_exception) as exc:
        service.ask(question)

    assert legacy_response.status_code == expected_status

    assert str(exc.value) == legacy_response.json()["detail"]


def test_citation_error_matches_legacy_api(monkeypatch):
    question = "اشرح المادة ٩١"

    service = create_service()

    fake_generator = Mock()
    fake_generator.generate.return_value = (
        "Unsupported legal claim [CC-200]."
    )

    service.generator = fake_generator

    monkeypatch.setattr(
        legacy_api,
        "generate_answer",
        lambda question, context: (
            "Unsupported legal claim [CC-200]."
        ),
    )

    legacy_response = legacy_client.post(
        "/ask",
        json={"question": question},
    )

    with pytest.raises(CitationValidationError) as exc:
        service.ask(question)

    assert legacy_response.status_code == 502
    assert str(exc.value) == legacy_response.json()["detail"]