"""Release checks exercise corruption, clean restoration and no-key routes."""

import json
import shutil
from unittest.mock import Mock

import httpx
import pytest
from fastapi.testclient import TestClient
from openai import APIConnectionError

from civil_code_rag.api import dependencies, main
from civil_code_rag.api.security import require_client
from civil_code_rag.config import PROJECT_ROOT, Settings
from civil_code_rag.release_artifact import restore


def test_restore_into_empty_directory_preserves_release_bytes(tmp_path):
    output = tmp_path / "empty"
    assert restore(output)["indexed_document_count"] == 268
    manifest = json.loads((PROJECT_ROOT / "artifacts/retrieval-index.json").read_text())
    from civil_code_rag.release_artifact import sha256

    for name, digest in manifest["files"].items():
        assert sha256((output / name).read_bytes()) == digest
    assert restore(output)["corpus_record_count"] == 162


def test_restore_rejects_corrupt_archive_before_writing(tmp_path):
    shutil.copytree(PROJECT_ROOT / "artifacts", tmp_path / "artifacts")
    (tmp_path / "artifacts/retrieval-index.zip").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="archive checksum"):
        restore(tmp_path / "index", root=tmp_path)
    assert not (tmp_path / "index").exists()


def test_restore_preserves_different_existing_index(tmp_path):
    (tmp_path / "embeddings.npy").write_bytes(b"user artifact")
    with pytest.raises(ValueError, match="Existing index differs"):
        restore(tmp_path)
    assert (tmp_path / "embeddings.npy").read_bytes() == b"user artifact"


def test_health_reports_unavailable_index(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "get_settings", lambda: Settings(index_dir=tmp_path))
    response = TestClient(main.app).get("/health")
    assert response.status_code == 503
    assert str(tmp_path) not in response.text


@pytest.mark.parametrize(
    "question", ["Explain Article 91", "When does an expression of intent take effect?"]
)
def test_no_key_generated_routes_fail_before_network(question, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setitem(
        main.app.dependency_overrides, require_client, lambda: "test-client"
    )
    retriever = Mock(side_effect=AssertionError("Must not load model"))
    monkeypatch.setattr(dependencies, "get_retriever", retriever)
    dependencies.get_ask_service.cache_clear()
    response = TestClient(main.app).post("/ask", json={"question": question})
    assert response.status_code == 503
    assert response.json() == {
        "detail": "OPENAI_API_KEY is required for generated answers."
    }
    retriever.assert_not_called()


def test_key_is_read_using_standard_environment_name(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    assert dependencies.require_api_key() == "test-placeholder"


def test_openai_errors_are_sanitized(monkeypatch):
    generator = Mock()
    generator.generate.side_effect = APIConnectionError(
        request=httpx.Request("POST", "https://example.invalid"),
        message="private detail",
    )
    monkeypatch.setattr(dependencies, "get_generator", lambda: generator)
    with pytest.raises(dependencies.ServiceUnavailableError) as exc:
        dependencies.LazyGenerator().generate("question", "context")
    assert str(exc.value) == "Answer generation is temporarily unavailable."
