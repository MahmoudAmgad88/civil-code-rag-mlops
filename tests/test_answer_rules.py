"""Tests for language detection and citation validation."""

import pytest

from civil_code_rag.core.answer_rules import (
    detect_language,
    validate_citations,
)
from scripts.ask import (
    detect_language as legacy_detect_language,
    validate_citations as legacy_validate_citations,
)


@pytest.mark.parametrize(
    ("question", "expected_language"),
    [
        ("اشرح المادة ٩١", "ar"),
        ("Explain Article 91", "en"),
    ],
)
def test_detect_language(question, expected_language):
    assert detect_language(question) == expected_language


def test_accept_citation_present_in_context():
    context = "[SOURCE: CC-91]\nArticle text:\nExample text."
    answer = "Example answer [CC-91]."

    assert validate_citations(answer, context) == {"CC-91"}


def test_reject_citation_absent_from_context():
    context = "[SOURCE: CC-91]\nArticle text:\nExample text."
    answer = "Example answer [CC-200]."

    with pytest.raises(
        ValueError,
        match="Answer cites sources that were not retrieved",
    ):
        validate_citations(answer, context)


def test_legacy_imports_use_the_same_functions():
    assert legacy_detect_language is detect_language
    assert legacy_validate_citations is validate_citations