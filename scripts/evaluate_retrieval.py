"""Evaluate semantic retrieval on the development questions."""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from scripts.search_articles import (
    MODEL_NAME,
    load_index,
    search_articles,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = PROJECT_ROOT / "eval" / "dev_questions.jsonl"


def load_semantic_questions(file_path):
    """Load only questions intended for semantic retrieval testing."""

    questions = []

    with file_path.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            question = json.loads(line)

            if question["category"] == "semantic":
                questions.append(question)

    return questions


def evaluate(questions, model, embeddings, records):
    """Evaluate retrieval and print the ranking for each question."""

    hits_by_language = {"ar": [], "en": []}

    for question in questions:
        results = search_articles(
            question=question["question"],
            language=question["language"],
            model=model,
            embeddings=embeddings,
            records=records,
            top_k=5,
        )

        retrieved_ids = [
            result["record"]["article_id"]
            for result in results
        ]

        expected_ids = set(question["expected_article_ids"])

        if not expected_ids:
            raise ValueError(
                f"{question['id']} has no expected article IDs."
            )

        # Recall@5 = relevant retrieved articles / expected articles.
        found_ids = expected_ids.intersection(retrieved_ids)
        recall_at_5 = len(found_ids) / len(expected_ids)

        # Find the first expected article's position in the results.
        ranks = [
            rank
            for rank, article_id in enumerate(retrieved_ids, start=1)
            if article_id in expected_ids
        ]

        first_rank = min(ranks) if ranks else None

        hits_by_language[question["language"]].append(recall_at_5)

        print("\n" + "=" * 50)
        print(f"Question ID: {question['id']}")
        print(f"Question: {question['question']}")
        print(f"Expected: {sorted(expected_ids)}")
        print(f"Retrieved: {retrieved_ids}")
        print(f"First expected rank: {first_rank}")
        print(f"Recall@5: {recall_at_5:.2f}")

    print("\n" + "=" * 50)
    print("SEMANTIC RETRIEVAL EVALUATION")
    print("=" * 50)

    for language, scores in hits_by_language.items():
        if scores:
            average_recall = sum(scores) / len(scores)

            print(
                f"{language}: "
                f"{len(scores)} questions | "
                f"Mean Recall@5: {average_recall:.2f}"
            )


if __name__ == "__main__":
    questions = load_semantic_questions(QUESTIONS_PATH)

    embeddings, records = load_index()
    model = SentenceTransformer(MODEL_NAME)

    evaluate(questions, model, embeddings, records)