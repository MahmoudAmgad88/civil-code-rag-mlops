"""API-key auth, request-ID propagation, audit records and /metrics contracts."""

import json
import logging
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from civil_code_rag.api.dependencies import get_ask_service
from civil_code_rag.api.main import app
from civil_code_rag.api.observability import (
    Metrics,
    index_version,
    resolve_request_id,
)
from civil_code_rag.api.security import match_client
from civil_code_rag.config import Settings, get_settings
from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.services.ask_service import AskService

CORPUS_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "processed" / "articles.jsonl"
)
KEY = "test-key-for-client-a"
AUTH = {"X-API-Key": KEY}


class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[dict] = []

    def emit(self, record):
        self.records.append(json.loads(record.getMessage()))


def make_settings(**overrides) -> Settings:
    values = {"api_keys": {"client-a": KEY, "client-b": "other-key"}}
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def audit_records():
    handler = ListHandler()
    logger = logging.getLogger("civil_code_rag.audit")
    logger.addHandler(handler)
    yield handler.records
    logger.removeHandler(handler)


@pytest.fixture
def client_factory():
    service = AskService(ArticleRepository(CORPUS_PATH), Mock(), Mock())

    def build(**settings_overrides):
        settings = make_settings(**settings_overrides)
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_ask_service] = lambda: service
        return TestClient(app), service

    yield build
    app.dependency_overrides.clear()


def test_ask_without_key_is_rejected_before_the_service_runs(client_factory):
    client, service = client_factory()
    service.ask = Mock()
    response = client.post("/ask", json={"question": "What does Article 91 say?"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid API key."}
    assert response.headers["WWW-Authenticate"] == "ApiKey"
    service.ask.assert_not_called()


def test_ask_with_wrong_key_is_rejected(client_factory):
    client, _ = client_factory()
    response = client.post(
        "/ask",
        json={"question": "What does Article 91 say?"},
        headers={"X-API-Key": "wrong"},
    )
    assert response.status_code == 401


def test_ask_with_valid_key_succeeds(client_factory):
    client, _ = client_factory()
    response = client.post(
        "/ask", json={"question": "What does Article 91 say?"}, headers=AUTH
    )
    assert response.status_code == 200
    assert response.json()["article_id"] == "CC-91"


def test_auth_fails_closed_when_no_keys_are_configured(client_factory):
    client, _ = client_factory(api_keys={})
    response = client.post(
        "/ask", json={"question": "What does Article 91 say?"}, headers=AUTH
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "API authentication is not configured."}


def test_auth_can_be_disabled_explicitly_for_local_development(client_factory):
    client, _ = client_factory(api_keys={}, auth_disabled=True)
    response = client.post("/ask", json={"question": "What does Article 91 say?"})
    assert response.status_code == 200


def test_health_stays_open_for_container_probes(client_factory):
    client, _ = client_factory()
    assert client.get("/health").status_code == 200


def test_match_client_maps_key_to_client_id():
    settings = make_settings()
    assert match_client(KEY, settings.api_keys) == "client-a"
    assert match_client("other-key", settings.api_keys) == "client-b"
    assert match_client("", settings.api_keys) is None
    assert match_client(None, settings.api_keys) is None


def test_api_keys_are_hidden_in_settings_repr():
    assert KEY not in repr(make_settings())


def test_request_id_is_generated_and_returned(client_factory):
    client, _ = client_factory()
    response = client.get("/health")
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 32 and request_id.isalnum()


def test_well_formed_caller_request_id_is_echoed(client_factory):
    client, _ = client_factory()
    response = client.get("/health", headers={"X-Request-ID": "trace-abc_123.4"})
    assert response.headers["X-Request-ID"] == "trace-abc_123.4"


@pytest.mark.parametrize("incoming", ["", "has space", "x" * 65, "bad\nnewline"])
def test_malformed_request_id_is_replaced(incoming):
    assert resolve_request_id(incoming) != incoming


def test_audit_record_for_answered_question(client_factory, audit_records):
    client, _ = client_factory()
    question = "What does Article 91 say?"
    response = client.post(
        "/ask",
        json={"question": question},
        headers={**AUTH, "X-Request-ID": "req-1"},
    )
    assert response.status_code == 200
    record = audit_records[-1]
    assert record["event"] == "api_audit"
    assert record["request_id"] == "req-1"
    assert record["client_id"] == "client-a"
    assert record["path"] == "/ask"
    assert record["status_code"] == 200
    assert record["outcome"] == "answered"
    assert record["route"] == "exact"
    assert record["language"] == "en"
    assert record["cited_article_ids"] == ["CC-91"]
    assert record["question_chars"] == len(question)
    assert len(record["question_sha256"]) == 64
    assert record["llm_model"] is None
    assert record["index_archive_sha256"] == index_version()
    assert record["latency_ms"] >= 0


def test_audit_record_never_contains_the_question_text(client_factory, audit_records):
    client, _ = client_factory()
    question = "What does Article 91 say?"
    client.post("/ask", json={"question": question}, headers=AUTH)
    assert question not in json.dumps(audit_records[-1])


def test_audit_record_for_generated_answer_names_the_llm(
    client_factory, audit_records
):
    client, service = client_factory()
    service.generator.generate.return_value = "Article explanation [CC-91]."
    response = client.post(
        "/ask", json={"question": "Explain Article 91"}, headers=AUTH
    )
    assert response.status_code == 200
    record = audit_records[-1]
    assert record["route"] == "explain"
    assert record["llm_model"] == get_settings().llm_model


def test_audit_record_for_rejected_key(client_factory, audit_records):
    client, _ = client_factory()
    client.post("/ask", json={"question": "Article 91"}, headers={"X-API-Key": "no"})
    record = audit_records[-1]
    assert record["status_code"] == 401
    assert record["outcome"] == "unauthorized"
    assert record["client_id"] is None


def test_audit_record_for_citation_failure(client_factory, audit_records):
    client, service = client_factory()
    service.generator.generate.return_value = "Unsupported claim [CC-200]."
    response = client.post(
        "/ask", json={"question": "Explain Article 91"}, headers=AUTH
    )
    assert response.status_code == 502
    assert audit_records[-1]["outcome"] == "citation_validation_failed"


def test_health_is_not_audited(client_factory, audit_records):
    client, _ = client_factory()
    client.get("/health")
    assert audit_records == []


def test_metrics_requires_a_key(client_factory):
    client, _ = client_factory()
    assert client.get("/metrics").status_code == 401


def test_metrics_reports_requests_latency_and_outcomes(client_factory):
    client, _ = client_factory()
    client.post("/ask", json={"question": "What does Article 91 say?"}, headers=AUTH)
    client.post(
        "/ask",
        json={"question": "What does the Egyptian Penal Code say?"},
        headers=AUTH,
    )
    response = client.get("/metrics", headers=AUTH)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain; version=0.0.4")
    body = response.text
    assert (
        'civil_code_rag_http_requests_total{method="POST",path="/ask",status="200"}'
        in body
    )
    assert 'civil_code_rag_http_request_duration_seconds_count{path="/ask"}' in body
    assert 'civil_code_rag_ask_total{outcome="answered",route="exact"}' in body
    assert 'civil_code_rag_ask_total{outcome="out_of_scope",route="out_of_scope"}' in (
        body
    )


def test_metrics_histogram_is_cumulative():
    metrics = Metrics()
    metrics.observe_request("POST", "/ask", 200, 0.07)
    metrics.observe_request("POST", "/ask", 200, 3.0)
    body = metrics.render()
    name = "civil_code_rag_http_request_duration_seconds"
    assert f'{name}_bucket{{path="/ask",le="0.05"}} 0' in body
    assert f'{name}_bucket{{path="/ask",le="0.1"}} 1' in body
    assert f'{name}_bucket{{path="/ask",le="5.0"}} 2' in body
    assert f'{name}_bucket{{path="/ask",le="+Inf"}} 2' in body
    assert f'{name}_count{{path="/ask"}} 2' in body


def test_unknown_paths_are_collapsed_in_metrics(client_factory):
    client, _ = client_factory()
    client.get("/does-not-exist-123")
    body = client.get("/metrics", headers=AUTH).text
    assert "does-not-exist-123" not in body
    assert 'path="other",status="404"' in body
