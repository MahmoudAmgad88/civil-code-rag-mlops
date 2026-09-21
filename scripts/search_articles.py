
"""Retrieve the most relevant Civil Code articles by semantic similarity."""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INDEX_DIR = PROJECT_ROOT / "data" / "index"

EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
INDEX_RECORDS_PATH = INDEX_DIR / "index_records.jsonl"

MODEL_NAME = "intfloat/multilingual-e5-small"


# --------------------------------------------------
# 2. Load the saved index
# --------------------------------------------------

def load_index():
    """Load vectors and their associated records."""

    embeddings = np.load(
        EMBEDDINGS_PATH,
        allow_pickle=False,
    )

    with INDEX_RECORDS_PATH.open(
        encoding="utf-8",
    ) as file:

        records = [
            json.loads(line)
            for line in file
            if line.strip()
        ]

    # Row i in embeddings must correspond to record i.
    if len(embeddings) != len(records):
        raise ValueError(
            "Embedding and record counts do not match."
        )

    if embeddings.ndim != 2:
        raise ValueError("Expected a 2D embedding matrix.")

    if not np.isfinite(embeddings).all():
        raise ValueError("Index contains invalid vectors.")

    return embeddings, records


# --------------------------------------------------
# 3. Search articles
# --------------------------------------------------

def search_articles(
    question,
    language,
    model,
    embeddings,
    records,
    top_k=5,
):
    """Find the most similar articles in the requested language."""

    if language not in {"ar", "en"}:
        raise ValueError("Language must be 'ar' or 'en'.")

    if not question.strip():
        raise ValueError("Question must not be empty.")

    # Keep Arabic and English retrieval separate.
    matching_indices = [
        index
        for index, record in enumerate(records)
        if record["language"] == language
    ]

    if not matching_indices:
        return []

    # E5 uses 'query:' for questions, unlike document passages.
    query_text = "query: " + question.strip()

    query_embedding = model.encode(
        query_text,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    # Check that query and document vectors have matching dimensions.
    if query_embedding.shape[0] != embeddings.shape[1]:
        raise ValueError(
            "Query and document embedding dimensions do not match."
        )

    # Select only the vectors matching the question's language.
    language_embeddings = embeddings[matching_indices]

    # One similarity score per candidate article.
    similarity_scores = language_embeddings @ query_embedding

    # Highest similarity scores first.
    ranked_positions = np.argsort(similarity_scores)[::-1][:top_k]

    results = []

    for position in ranked_positions:

        # Convert the language-specific position back to
        # the corresponding position in the full index.
        original_index = matching_indices[int(position)]

        results.append(
            {
                "record": records[original_index],
                "similarity": float(similarity_scores[position]),
            }
        )

    return results


# --------------------------------------------------
# 4. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    embeddings, records = load_index()

    print(f"Loaded records: {len(records)}")
    print(f"Loaded embeddings: {embeddings.shape}")

    model = SentenceTransformer(MODEL_NAME)

    # Two questions from our development evaluation dataset.
    test_questions = [
        {
            "language": "ar",
            "question": "متى ينتج التعبير عن الإرادة أثره القانوني؟",
            "expected_article_id": "CC-91",
        },
        {
            "language": "en",
            "question": "What happens to the parties when a contract is rescinded?",
            "expected_article_id": "CC-160",
        },
    ]

    for test in test_questions:

        results = search_articles(
            question=test["question"],
            language=test["language"],
            model=model,
            embeddings=embeddings,
            records=records,
            top_k=5,
        )

        print("\n" + "=" * 50)
        print(f"Language: {test['language']}")
        print(f"Question: {test['question']}")
        print(f"Expected article: {test['expected_article_id']}")
        print("=" * 50)

        for rank, result in enumerate(results, start=1):

            record = result["record"]

            print(
                f"\nRank {rank} | "
                f"{record['record_id']} | "
                f"Similarity: {result['similarity']:.4f}"
            )

            # Display a short preview of the retrieved article.
            preview = " ".join(
                record["text_display"].split()
            )[:180]

            print(f"Text: {preview}...")

        # This checks retrieval, not answer correctness.
        retrieved_article_ids = {
            result["record"]["article_id"]
            for result in results
        }

        found = (
            test["expected_article_id"]
            in retrieved_article_ids
        )

        print(f"\nExpected article found in Top 5: {found}")