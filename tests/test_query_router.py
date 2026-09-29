"""Unit tests for query routing and legacy compatibility."""

import pytest

from civil_code_rag.core.query_router import route_question
from scripts.query_router import route_question as legacy_route_question


@pytest.mark.parametrize(
    ("question", "expected_route", "expected_article_id"),
    [
        ("ما نص المادة ٩١؟", "exact", "CC-91"),
        ("What does Article 91 say?", "exact", "CC-91"),
        ("اشرحلي المادة ٩١ ببساطة.", "explain", "CC-91"),
        ("Explain Article 91", "explain", "CC-91"),
        (
            "متى ينتج التعبير عن الإرادة أثره القانوني؟",
            "semantic",
            None,
        ),
        ("ما نص المادة ٩١ والمادة ٩٢؟", "unsupported", None),
    ],
)
def test_question_routing(
    question: str,
    expected_route: str,
    expected_article_id: str | None,
) -> None:
    decision = route_question(question)

    assert decision["route"] == expected_route
    assert decision["article_id"] == expected_article_id


def test_empty_question_is_rejected() -> None:
    with pytest.raises(ValueError, match="Question must not be empty"):
        route_question("   ")


def test_legacy_import_uses_same_function() -> None:
    assert legacy_route_question is route_question