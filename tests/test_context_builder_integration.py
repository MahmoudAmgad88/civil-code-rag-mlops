"""Exercise context construction against the frozen real corpus."""

from pathlib import Path

import pytest

from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.retrieval.context_builder import build_context

ARTICLES_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "articles.jsonl"


@pytest.mark.parametrize(
    ("language", "article_ids"),
    [
        ("ar", ["CC-91", "CC-160"]),
        ("en", ["CC-160", "CC-91"]),
    ],
)
def test_context_on_real_corpus(
    language: str,
    article_ids: list[str],
) -> None:
    # Both implementations receive identical retrieval results.
    results = [
        {
            "record": {
                "article_id": article_id,
                "language": language,
            }
        }
        for article_id in article_ids
    ]

    article_lookup = ArticleRepository(ARTICLES_PATH).articles
    context = build_context(
        results=results,
        article_lookup=article_lookup,
        language=language,
    )

    # Verify that both article references are present and in order.
    first_source = f"[SOURCE: {article_ids[0]}]"
    second_source = f"[SOURCE: {article_ids[1]}]"

    assert context.index(first_source) < context.index(
        second_source
    )
