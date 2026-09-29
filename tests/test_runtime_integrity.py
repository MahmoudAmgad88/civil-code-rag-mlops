"""Runtime lifecycle and frozen-artifact integrity checks."""

import json
from pathlib import Path
from unittest.mock import Mock

import numpy as np
from fastapi.testclient import TestClient

from civil_code_rag.api.dependencies import get_ask_service
from civil_code_rag.api.main import app
from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.services.ask_service import AskService

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


def test_frozen_corpus_and_index_counts_match_manifest():
    manifest = json.loads((PROCESSED / "corpus_manifest.json").read_text("utf-8"))
    article_count = sum(1 for line in (PROCESSED / "articles.jsonl").open("r", encoding="utf-8") if line.strip())
    index_record_count = sum(
        1
        for line in (ROOT / "data" / "index" / "index_records.jsonl").open("r", encoding="utf-8")
        if line.strip()
    )
    embeddings = np.load(ROOT / "data" / "index" / "embeddings.npy", allow_pickle=False)

    assert manifest["record_count"] == article_count == 162
    assert manifest["search_record_count"] == index_record_count == 268
    assert embeddings.shape == (268, 384)


def test_explain_source_note_article_never_calls_generator():
    service = AskService(
        ArticleRepository(PROCESSED / "articles.jsonl"), Mock(), Mock()
    )

    result = service.ask("Explain Article 60")

    assert result["answer"] is None
    assert result["verified_status"] == "unverified"
    service.generator.generate.assert_not_called()


def test_health_does_not_require_corpus_or_optional_dependencies():
    def fail_if_service_is_built():
        raise AssertionError("The service must not be built for health checks.")

    app.dependency_overrides[get_ask_service] = fail_if_service_is_built
    try:
        response = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.json() == {"status": "ok"}
