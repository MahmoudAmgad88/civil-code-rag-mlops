"""Compare the new context builder with the legacy implementation."""

import pytest

from civil_code_rag.repositories.article_repository import ArticleRepository
from civil_code_rag.retrieval.context_builder import build_context
from scripts.build_retrieval_context import (
    ARTICLES_PATH,
    build_context as legacy_build_context,
    load_article_lookup,
)


@pytest.mark.parametrize(
    ("language", "article_ids"),
    [
        ("ar", ["CC-91", "CC-160"]),
        ("en", ["CC-160", "CC-91"]),
    ],
)
def test_context_matches_legacy_on_real_corpus(
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

    new_lookup = ArticleRepository(ARTICLES_PATH).articles
    legacy_lookup = load_article_lookup(ARTICLES_PATH)

    new_context = build_context(
        results=results,
        article_lookup=new_lookup,
        language=language,
    )

    legacy_context = legacy_build_context(
        results=results,
        article_lookup=legacy_lookup,
        language=language,
    )

    assert new_context == legacy_context

    # Verify that both article references are present and in order.
    first_source = f"[SOURCE: {article_ids[0]}]"
    second_source = f"[SOURCE: {article_ids[1]}]"

    assert new_context.index(first_source) < new_context.index(
        second_source
    )