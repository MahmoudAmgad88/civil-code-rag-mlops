"""Unit tests for the source context builder."""

import pytest

from civil_code_rag.retrieval.context_builder import build_context


@pytest.fixture
def article_lookup():
    return {
        "CC-91": {
            "article_id": "CC-91",
            "page_start": 8,
            "page_end": 9,
            "text_ar_original": "النص العربي الأصلي",
            "text_en_original": "Original English article text",
        },
    }


def test_build_arabic_context(article_lookup):
    results = [
        {
            "record": {
                "article_id": "CC-91",
                "language": "ar",
            }
        }
    ]

    context = build_context(results, article_lookup, language="ar")

    assert context == (
        "[SOURCE: CC-91]\n"
        "PDF pages: 8-9\n"
        "Article text:\n"
        "النص العربي الأصلي"
    )


def test_build_english_context(article_lookup):
    results = [
        {
            "record": {
                "article_id": "CC-91",
                "language": "en",
            }
        }
    ]

    context = build_context(results, article_lookup, language="en")

    assert "Original English article text" in context
    assert "النص العربي الأصلي" not in context
    assert "[SOURCE: CC-91]" in context


def test_reject_language_mismatch(article_lookup):
    results = [
        {
            "record": {
                "article_id": "CC-91",
                "language": "en",
            }
        }
    ]

    with pytest.raises(
        ValueError,
        match="Retrieved record language mismatch",
    ):
        build_context(results, article_lookup, language="ar")


def test_reject_missing_original_text(article_lookup):
    article_lookup["CC-91"]["text_en_original"] = ""

    results = [
        {
            "record": {
                "article_id": "CC-91",
                "language": "en",
            }
        }
    ]

    with pytest.raises(
        ValueError,
        match="No en source text for CC-91",
    ):
        build_context(results, article_lookup, language="en")