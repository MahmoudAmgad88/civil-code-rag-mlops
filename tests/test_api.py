"""API contract tests using injected dependencies and no external services."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from civil_code_rag.api.dependencies import get_ask_service
from civil_code_rag.api.main import app
from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.services.ask_service import AskService

CORPUS_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "articles.jsonl"


@pytest.fixture
def api():
    retriever = Mock()
    generator = Mock()
    service = AskService(ArticleRepository(CORPUS_PATH), retriever, generator)
    app.dependency_overrides[get_ask_service] = lambda: service
    with TestClient(app) as client:
        yield client, service
    app.dependency_overrides.clear()


def test_health_does_not_resolve_ask_service():
    def fail_if_resolved():
        raise AssertionError("Health must not initialize application resources.")

    app.dependency_overrides[get_ask_service] = fail_if_resolved
    try:
        response = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("question", "language", "text_fragment"),
    [
        ("ما نص المادة ٩١؟", "ar", "الإرادة"),
        ("What does Article 91 say?", "en", "declaration of intention"),
    ],
)
def test_exact_lookup_in_both_languages(api, question, language, text_fragment):
    client, service = api
    response = client.post("/ask", json={"question": question})
    assert response.status_code == 200
    data = response.json()
    assert data["route"] == "exact"
    assert data["language"] == language
    assert data["article_id"] == "CC-91"
    assert text_fragment in data["answer"]
    assert data["source_note"] is None
    service.retriever.search.assert_not_called()
    service.generator.generate.assert_not_called()


def test_repealed_article_returns_source_note_without_llm(api):
    client, service = api
    response = client.post("/ask", json={"question": "ما نص المادة ٦٠؟"})
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] is None
    assert "54-80" in data["source_note"]
    assert data["verified_status"] == "unverified"
    service.generator.generate.assert_not_called()


def test_out_of_scope_question(api):
    client, service = api
    response = client.post(
        "/ask", json={"question": "What does the Egyptian Penal Code say?"}
    )
    assert response.status_code == 200
    assert response.json()["route"] == "out_of_scope"
    service.retriever.search.assert_not_called()


def test_explain_specific_article_without_semantic_retrieval(api):
    client, service = api
    service.generator.generate.return_value = "Article explanation [CC-91]."
    response = client.post("/ask", json={"question": "Explain Article 91"})
    assert response.status_code == 200
    data = response.json()
    assert data["cited_article_ids"] == ["CC-91"]
    assert "source_note" not in data
    assert "verified_status" not in data
    service.retriever.search.assert_not_called()


def test_semantic_route_with_controlled_dependencies(api):
    client, service = api
    service.retriever.search.return_value = [
        {"record": {"article_id": "CC-91", "language": "en"}, "similarity": 0.9}
    ]
    service.generator.generate.return_value = "The rule applies on notice [CC-91]."
    response = client.post(
        "/ask", json={"question": "When does an expression of intent take effect?"}
    )
    assert response.status_code == 200
    assert response.json()["route"] == "semantic"
    assert response.json()["cited_article_ids"] == ["CC-91"]


@pytest.mark.parametrize(
    ("question", "status", "detail"),
    [
        ("What does Article 200 say?", 404, "Article not found in the available corpus."),
        (
            "Article 91",
            422,
            "Article request is ambiguous. Ask for the article text or its explanation.",
        ),
        ("   ", 422, "Question must not be empty."),
    ],
)
def test_application_error_contracts(api, question, status, detail):
    client, _ = api
    response = client.post("/ask", json={"question": question})
    assert response.status_code == status
    assert response.json() == {"detail": detail}


def test_empty_question_is_rejected_by_pydantic(api):
    client, _ = api
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_invalid_citation_returns_502(api):
    client, service = api
    service.generator.generate.return_value = "Unsupported claim [CC-200]."
    response = client.post("/ask", json={"question": "Explain Article 91"})
    assert response.status_code == 502
    assert response.json() == {
        "detail": "Generated answer failed citation validation."
    }
