"""Automated tests for the local Civil Code RAG API."""

from fastapi.testclient import TestClient

import scripts.api as api


client = TestClient(api.app)


def test_health():
    """The API responds to a health check."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_exact_lookup_repealed_article():
    """Exact lookup returns the source note, not invented article text."""

    response = client.post(
        "/ask",
        json={"question": "ما نص المادة ٦٠؟"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route"] == "exact"
    assert data["language"] == "ar"
    assert data["article_id"] == "CC-60"
    assert data["answer"] is None
    assert "54-80" in data["source_note"]
    assert data["verified_status"] == "unverified"


def test_explicitly_out_of_scope_question():
    """A clearly unsupported domain is rejected before retrieval."""

    response = client.post(
        "/ask",
        json={
            "question": (
                "ما عقوبة جريمة القتل العمد "
                "في قانون العقوبات المصري؟"
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["route"] == "out_of_scope"


def test_semantic_route_without_real_llm(monkeypatch):
    """Test semantic routing with controlled retrieval and LLM outputs."""

    fake_context = """
[SOURCE: CC-91]
PDF pages: 8-9
Article text:
ينتج التعبير عن الإرادة أثره في الوقت الذي يتصل فيه بعلم من وجه إليه.
"""

    fake_answer = (
        "ينتج التعبير عن الإرادة أثره عند علم من وجه إليه [CC-91]."
    )

    # Replace the real functions only during this test.
    def fake_retrieve_evidence(question, language):
        assert question == "متى ينتج التعبير عن الإرادة أثره القانوني؟"
        assert language == "ar"
        return fake_context

    def fake_generate_answer(question, context):
        assert context == fake_context
        return fake_answer

    monkeypatch.setattr(
        api,
        "retrieve_evidence",
        fake_retrieve_evidence,
    )

    monkeypatch.setattr(
        api,
        "generate_answer",
        fake_generate_answer,
    )

    response = client.post(
        "/ask",
        json={
            "question": "متى ينتج التعبير عن الإرادة أثره القانوني؟"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route"] == "semantic"
    assert data["language"] == "ar"
    assert data["answer"] == fake_answer
    assert data["cited_article_ids"] == ["CC-91"]

def test_show_article_text_without_llm(monkeypatch):
    """A show_text request must not call the LLM."""

    def fail_if_llm_called(question, context):
        raise AssertionError(
            "LLM must not be called for show_text."
        )

    monkeypatch.setattr(
        api,
        "generate_answer",
        fail_if_llm_called,
    )

    response = client.post(
        "/ask",
        json={"question": "ما نص المادة ٩١؟"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route"] == "exact"
    assert data["article_id"] == "CC-91"
    assert "ينتج التعبير عن الإرادة" in data["answer"]

def test_explain_specific_article_without_real_llm(monkeypatch):
    """An explain request must use the specified article as evidence."""

    question = "اشرحلي المادة ٩١ ببساطة."

    fake_answer = (
        "المادة بتوضح إمتى التعبير عن الإرادة "
        "يبدأ ينتج أثره [CC-91]."
    )

    def fail_if_semantic_retrieval_called(question, language):
        raise AssertionError(
            "Semantic retrieval must not run "
            "when the article is explicitly specified."
        )

    def fake_generate_answer(question, context):
        assert question == "اشرحلي المادة ٩١ ببساطة."
        assert "[SOURCE: CC-91]" in context
        assert "ينتج التعبير عن الإرادة" in context

        return fake_answer

    monkeypatch.setattr(
        api,
        "retrieve_evidence",
        fail_if_semantic_retrieval_called,
    )

    monkeypatch.setattr(
        api,
        "generate_answer",
        fake_generate_answer,
    )

    response = client.post(
        "/ask",
        json={"question": question},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route"] == "explain"
    assert data["intent"] == "explain"
    assert data["article_id"] == "CC-91"
    assert data["answer"] == fake_answer
    assert data["cited_article_ids"] == ["CC-91"]

def test_explain_article_with_source_note_without_llm(monkeypatch):
    """A source-note-only article must not be explained by the LLM."""

    def fail_if_llm_called(question, context):
        raise AssertionError(
            "LLM must not be called when article text is unavailable."
        )

    monkeypatch.setattr(
        api,
        "generate_answer",
        fail_if_llm_called,
    )

    response = client.post(
        "/ask",
        json={"question": "اشرحلي المادة ٦٠ ببساطة."},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["route"] == "explain"
    assert data["article_id"] == "CC-60"
    assert data["answer"] is None

    assert "غير متاح" in data["message"]
    assert "54-80" in data["source_note"]
    assert data["verified_status"] == "unverified"
    assert data["cited_article_ids"] == []

def test_missing_article_returns_404():
    """An article absent from our corpus returns 404."""

    response = client.post(
        "/ask",
        json={"question": "ما نص المادة ٢٠٠؟"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Article not found in the available corpus."
    }


def test_empty_question_returns_422():
    """Pydantic rejects an empty question."""

    response = client.post(
        "/ask",
        json={"question": ""},
    )

    assert response.status_code == 422


def test_whitespace_question_returns_422():
    """The endpoint rejects a question containing spaces only."""

    response = client.post(
        "/ask",
        json={"question": "   "},
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Question must not be empty."
    }