"""Unit tests for ArticleRepository."""

import json

import pytest

from civil_code_rag.repositories.article_repository import (
    ArticleRepository,
)


def write_jsonl(path, records):
    """Create a small test corpus."""

    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def test_get_existing_article(tmp_path):
    corpus_path = tmp_path / "articles.jsonl"

    write_jsonl(
        corpus_path,
        [
            {
                "article_id": "CC-91",
                "text_ar_original": "نص المادة ٩١",
            }
        ],
    )

    repo = ArticleRepository(corpus_path)

    article = repo.get("CC-91")

    assert article is not None
    assert article["text_ar_original"] == "نص المادة ٩١"


def test_missing_article_returns_none(tmp_path):
    corpus_path = tmp_path / "articles.jsonl"

    write_jsonl(
        corpus_path,
        [{"article_id": "CC-91"}],
    )

    repo = ArticleRepository(corpus_path)

    assert repo.get("CC-200") is None


def test_duplicate_article_ids_are_rejected(tmp_path):
    corpus_path = tmp_path / "articles.jsonl"

    write_jsonl(
        corpus_path,
        [
            {"article_id": "CC-91"},
            {"article_id": "CC-91"},
        ],
    )

    with pytest.raises(
        ValueError,
        match="Duplicate article ID: CC-91",
    ):
        ArticleRepository(corpus_path)


def test_corpus_is_loaded_once(tmp_path):
    corpus_path = tmp_path / "articles.jsonl"

    write_jsonl(
        corpus_path,
        [{"article_id": "CC-91"}],
    )

    repo = ArticleRepository(corpus_path)

    # Change the file after creating the repository.
    write_jsonl(
        corpus_path,
        [{"article_id": "CC-92"}],
    )

    # The existing object keeps its original loaded data.
    assert repo.get("CC-91") is not None
    assert repo.get("CC-92") is None