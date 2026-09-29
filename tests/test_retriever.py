"""Unit tests for loading the Retriever index."""

import json

import numpy as np
import pytest

from civil_code_rag.retrieval.retriever import Retriever


def save_test_index(index_dir, embeddings, records):
    """Create a small index inside a temporary directory."""

    index_dir.mkdir()

    np.save(index_dir / "embeddings.npy", embeddings)

    with (index_dir / "index_records.jsonl").open(
        "w",
        encoding="utf-8",
    ) as file:
        for record in records:
            file.write(json.dumps(record) + "\n")


def test_load_valid_index(tmp_path):
    embeddings = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
        ]
    )

    records = [
        {"record_id": "CC-91-AR", "language": "ar"},
        {"record_id": "CC-160-EN", "language": "en"},
    ]

    index_dir = tmp_path / "index"

    save_test_index(index_dir, embeddings, records)

    fake_model = object()

    retriever = Retriever(
        index_dir=index_dir,
        model=fake_model,
    )

    assert retriever.embeddings.shape == (2, 2)
    assert retriever.records == records
    assert retriever.model is fake_model


def test_reject_mismatched_record_count(tmp_path):
    embeddings = np.array(
        [
            [1.0, 0.0],
            [0.0, 1.0],
        ]
    )

    records = [
        {"record_id": "CC-91-AR", "language": "ar"},
    ]

    index_dir = tmp_path / "index"

    save_test_index(index_dir, embeddings, records)

    with pytest.raises(
        ValueError,
        match="Embedding and record counts do not match",
    ):
        Retriever(index_dir=index_dir, model=object())


def test_reject_invalid_vectors(tmp_path):
    embeddings = np.array(
        [
            [1.0, 0.0],
            [np.nan, 1.0],
        ]
    )

    records = [
        {"record_id": "CC-91-AR", "language": "ar"},
        {"record_id": "CC-160-EN", "language": "en"},
    ]

    index_dir = tmp_path / "index"

    save_test_index(index_dir, embeddings, records)

    with pytest.raises(
        ValueError,
        match="Index contains invalid vectors",
    ):
        Retriever(index_dir=index_dir, model=object())

class FakeEmbeddingModel:
    """Return a known question vector without loading a real model."""

    def encode(
        self,
        text,
        normalize_embeddings,
        convert_to_numpy,
    ):
        assert text == "query: contract"
        assert normalize_embeddings is True
        assert convert_to_numpy is True

        return np.array([1.0, 0.0])


def test_search_ranks_only_records_in_requested_language(tmp_path):
    index_dir = tmp_path / "index"

    # Each row corresponds to the record at the same list position.
    embeddings = np.array(
        [
            [1.0, 0.0],  # Arabic: CC-91
            [0.0, 1.0],  # Arabic: CC-160
            [0.0, 1.0],  # English: CC-91
            [1.0, 0.0],  # English: CC-160
        ]
    )

    records = [
        {"article_id": "CC-91", "language": "ar"},
        {"article_id": "CC-160", "language": "ar"},
        {"article_id": "CC-91", "language": "en"},
        {"article_id": "CC-160", "language": "en"},
    ]

    save_test_index(index_dir, embeddings, records)

    retriever = Retriever(
        index_dir=index_dir,
        model=FakeEmbeddingModel(),
    )

    arabic_results = retriever.search(
        question="contract",
        language="ar",
        top_k=1,
    )

    english_results = retriever.search(
        question="contract",
        language="en",
        top_k=1,
    )

    assert len(arabic_results) == 1
    assert arabic_results[0]["record"]["article_id"] == "CC-91"
    assert arabic_results[0]["record"]["language"] == "ar"
    assert arabic_results[0]["similarity"] == pytest.approx(1.0)

    assert len(english_results) == 1
    assert english_results[0]["record"]["article_id"] == "CC-160"
    assert english_results[0]["record"]["language"] == "en"
    assert english_results[0]["similarity"] == pytest.approx(1.0)

@pytest.mark.parametrize(
    ("question", "language", "expected_message"),
    [
        ("contract", "fr", "Language must be 'ar' or 'en'"),
        ("   ", "en", "Question must not be empty"),
    ],
)
def test_reject_invalid_search_inputs(
    tmp_path,
    question,
    language,
    expected_message,
):
    index_dir = tmp_path / "index"

    save_test_index(
        index_dir,
        embeddings=np.array([[1.0, 0.0]]),
        records=[{"article_id": "CC-91", "language": "en"}],
    )

    retriever = Retriever(
        index_dir=index_dir,
        model=FakeEmbeddingModel(),
    )

    with pytest.raises(ValueError, match=expected_message):
        retriever.search(question=question, language=language)


def test_reject_query_embedding_dimension_mismatch(tmp_path):
    index_dir = tmp_path / "index"

    # The saved document vectors have 3 dimensions.
    save_test_index(
        index_dir,
        embeddings=np.array([[1.0, 0.0, 0.0]]),
        records=[{"article_id": "CC-91", "language": "en"}],
    )

    # FakeEmbeddingModel returns a 2-dimensional query vector.
    retriever = Retriever(
        index_dir=index_dir,
        model=FakeEmbeddingModel(),
    )

    with pytest.raises(
        ValueError,
        match="Query and document embedding dimensions do not match",
    ):
        retriever.search(question="contract", language="en")