"""Unit tests for the initial AskService routes."""

import json
from unittest.mock import Mock

import pytest

from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.services.ask_service import (
    AmbiguousArticleRequestError,
    ArticleNotFoundError,
    ArticleTextUnavailableError,
    AskService,
    CitationValidationError,
)


@pytest.fixture
def service(tmp_path):
    corpus_path = tmp_path / "articles.jsonl"

    records = [
        {
            "article_id": "CC-91",
            "alignment": "paired",
            "text_ar_original": "النص العربي للمادة ٩١",
            "text_en_original": "English text of Article 91",
            "status_evidence": None,
            "verified_status": "unverified",
            "page_start": 8,
            "page_end": 9,
        },
        {
            "article_id": "CC-60",
            "alignment": "repealed",
            "text_ar_original": None,
            "text_en_original": None,
            "status_evidence": "Source note for Articles 54-80",
            "verified_status": "unverified",
            "page_start": 7,
            "page_end": 7,
        },
    ]

    with corpus_path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    repository = ArticleRepository(corpus_path)

    # Neither dependency should be used by out_of_scope or exact.
    return AskService(
        repository=repository,
        retriever=object(),
        generator=object(),
    )


def test_out_of_scope_question(service):
    result = service.ask(
        "ما عقوبة جريمة القتل في قانون العقوبات المصري؟"
    )

    assert result["route"] == "out_of_scope"
    assert result["language"] == "ar"
    assert result["article_id"] is None


def test_exact_article_text_without_llm(service):
    result = service.ask("ما نص المادة ٩١؟")

    assert result == {
        "route": "exact",
        "language": "ar",
        "article_id": "CC-91",
        "answer": "النص العربي للمادة ٩١",
        "source_note": None,
        "verified_status": "unverified",
        "pdf_pages": [8, 9],
    }


def test_repealed_article_returns_source_note(service):
    result = service.ask("ما نص المادة ٦٠؟")

    assert result["route"] == "exact"
    assert result["article_id"] == "CC-60"
    assert result["answer"] is None
    assert result["source_note"] == "Source note for Articles 54-80"


def test_missing_article_raises_application_error(service):
    with pytest.raises(
        ArticleNotFoundError,
        match="Article not found in the available corpus",
    ):
        service.ask("ما نص المادة ٢٠٠؟")


def test_empty_question_is_rejected(service):
    with pytest.raises(
        ValueError,
        match="Question must not be empty",
    ):
        service.ask("   ")

def test_multiple_article_request_is_rejected(service):
    with pytest.raises(
        AmbiguousArticleRequestError,
        match="Article request is ambiguous",
    ):
        service.ask("ما نص المادة ٩١ والمادة ٩٢؟")


def test_article_reference_without_clear_intent_is_rejected(service):
    with pytest.raises(
        AmbiguousArticleRequestError,
        match="Article request is ambiguous",
    ):
        service.ask("المادة ٩١")

def test_explain_uses_only_requested_article(service):
    fake_generator = Mock()
    fake_generator.generate.return_value = (
        "شرح المادة المطلوبة [CC-91]."
    )
    service.generator = fake_generator

    result = service.ask("اشرح المادة ٩١")

    assert result["route"] == "explain"
    assert result["article_id"] == "CC-91"
    assert result["cited_article_ids"] == ["CC-91"]

    fake_generator.generate.assert_called_once()

    context = fake_generator.generate.call_args.kwargs["context"]

    assert "[SOURCE: CC-91]" in context
    assert "النص العربي للمادة ٩١" in context
    assert "[SOURCE: CC-60]" not in context


def test_explain_repealed_article_does_not_call_llm(service):
    fake_generator = Mock()
    service.generator = fake_generator

    result = service.ask("اشرح المادة ٦٠")

    assert result["route"] == "explain"
    assert result["answer"] is None
    assert result["article_id"] == "CC-60"
    assert "54-80" in result["source_note"]
    assert result["cited_article_ids"] == []

    fake_generator.generate.assert_not_called()


def test_explain_missing_article_raises_error(service):
    with pytest.raises(
        ArticleNotFoundError,
        match="Article not found in the available corpus",
    ):
        service.ask("اشرح المادة ٢٠٠")


def test_explain_missing_original_text_raises_error(service):
    service.repository.articles["CC-91"]["text_en_original"] = ""

    fake_generator = Mock()
    service.generator = fake_generator

    with pytest.raises(
        ArticleTextUnavailableError,
        match="The requested article text is unavailable",
    ):
        service.ask("Explain Article 91")

    fake_generator.generate.assert_not_called()


def test_explain_rejects_unknown_citation(service):
    fake_generator = Mock()
    fake_generator.generate.return_value = (
        "Unsupported claim [CC-200]."
    )
    service.generator = fake_generator

    with pytest.raises(
        CitationValidationError,
        match="Generated answer failed citation validation",
    ):
        service.ask("اشرح المادة ٩١")

def test_out_of_scope_returns_readable_arabic(service):
    # Unicode escapes keep the test independent of editor/console encoding.
    question = (
        "\u0645\u0627 \u0639\u0642\u0648\u0628\u0629 "
        "\u0627\u0644\u0642\u062a\u0644 \u0641\u064a "
        "\u0642\u0627\u0646\u0648\u0646 "
        "\u0627\u0644\u0639\u0642\u0648\u0628\u0627\u062a\u061f"
    )

    result = service.ask(question)

    assert result["route"] == "out_of_scope"
    assert result["language"] == "ar"
    assert result["answer"].startswith(
        "\u0627\u0644\u0633\u0624\u0627\u0644"  # السؤال
    )


def test_repealed_article_returns_readable_arabic_message(service):
    # "اشرح المادة ٦٠" expressed using Unicode escapes.
    question = (
        "\u0627\u0634\u0631\u062d "
        "\u0627\u0644\u0645\u0627\u062f\u0629 "
        "\u0666\u0660"
    )

    result = service.ask(question)

    assert result["route"] == "explain"
    assert result["message"].startswith(
        "\u0627\u0644\u0646\u0635 "
        "\u0627\u0644\u0623\u0635\u0644\u064a"  # النص الأصلي
    )

def test_semantic_route_uses_retrieval_and_generation(service):
    fake_retriever = Mock()
    fake_retriever.search.return_value = [
        {
            "record": {
                "article_id": "CC-91",
                "language": "ar",
            },
            "similarity": 0.95,
        }
    ]

    fake_generator = Mock()
    fake_generator.generate.return_value = (
        "ينتج التعبير عن الإرادة أثره عند العلم به [CC-91]."
    )

    service.retriever = fake_retriever
    service.generator = fake_generator

    question = "متى ينتج التعبير عن الإرادة أثره القانوني؟"
    result = service.ask(question)

    fake_retriever.search.assert_called_once_with(
        question=question,
        language="ar",
        top_k=5,
    )
    fake_generator.generate.assert_called_once()

    context = fake_generator.generate.call_args.kwargs["context"]

    assert "[SOURCE: CC-91]" in context
    assert "النص العربي للمادة ٩١" in context

    assert result == {
        "route": "semantic",
        "intent": "semantic",
        "language": "ar",
        "answer": "ينتج التعبير عن الإرادة أثره عند العلم به [CC-91].",
        "cited_article_ids": ["CC-91"],
    }


def test_semantic_route_rejects_unknown_citation(service):
    fake_retriever = Mock()
    fake_retriever.search.return_value = [
        {
            "record": {
                "article_id": "CC-91",
                "language": "en",
            },
            "similarity": 0.95,
        }
    ]

    fake_generator = Mock()
    fake_generator.generate.return_value = (
        "Unsupported answer [CC-200]."
    )

    service.retriever = fake_retriever
    service.generator = fake_generator

    with pytest.raises(
        CitationValidationError,
        match="Generated answer failed citation validation",
    ):
        service.ask(
            "When does an expression of intent take legal effect?"
        )

    fake_retriever.search.assert_called_once()
    fake_generator.generate.assert_called_once()