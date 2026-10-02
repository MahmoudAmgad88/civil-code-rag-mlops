"""Evaluate semantic retrieval on the development questions."""

import json
import subprocess
import time
from pathlib import Path

from sentence_transformers import SentenceTransformer

from pipelines.search_articles import (
    MODEL_NAME,
    load_index,
    search_articles,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_PATH = PROJECT_ROOT / "eval" / "dev_questions.jsonl"

def get_git_metadata():
    """Return the current Git commit and whether the working tree is dirty."""

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()

    status = subprocess.check_output(
        ["git", "status", "--porcelain"],
        text=True,
    ).strip()

    return commit, bool(status)

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


def evaluate(
    questions,
    model,
    embeddings,
    records,
    top_k=5,
):
    """Evaluate retrieval and print the ranking for each question."""

    recalls_by_language = {"ar": [], "en": []}
    rr_by_language = {"ar": [], "en": []}
    latencies_by_language = {"ar": [], "en": []}

    for question in questions:
        start = time.perf_counter()
        results = search_articles(
            question=question["question"],
            language=question["language"],
            model=model,
            embeddings=embeddings,
            records=records,
            top_k=top_k,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        retrieved_ids = [
            result["record"]["article_id"]
            for result in results
        ]

        expected_ids = set(question["expected_article_ids"])

        if not expected_ids:
            raise ValueError(
                f"{question['id']} has no expected article IDs."
            )

        found_ids = expected_ids.intersection(retrieved_ids)
        recall_at_k = len(found_ids) / len(expected_ids)

        # Find the first expected article's position in the results.
        ranks = [
            rank
            for rank, article_id in enumerate(retrieved_ids, start=1)
            if article_id in expected_ids
        ]

        first_rank = min(ranks) if ranks else None
        reciprocal_rank = 1 / first_rank if first_rank else 0.0

        language = question["language"]

        recalls_by_language[language].append(recall_at_k)
        rr_by_language[language].append(reciprocal_rank)
        latencies_by_language[language].append(latency_ms)

        print("\n" + "=" * 50)
        print(f"Question ID: {question['id']}")
        print(f"Question: {question['question']}")
        print(f"Expected: {sorted(expected_ids)}")
        print(f"Retrieved: {retrieved_ids}")
        print(f"First expected rank: {first_rank}")
        print(f"Recall@{top_k}: {recall_at_k:.2f}")
        print(f"Reciprocal Rank: {reciprocal_rank:.2f}")
        print(f"Latency: {latency_ms:.2f} ms")

    print("\n" + "=" * 50)
    print("SEMANTIC RETRIEVAL EVALUATION")
    print("=" * 50)

    summary = {}

    for language in ("ar", "en"):
        recalls = recalls_by_language[language]
        reciprocal_ranks = rr_by_language[language]
        latencies = latencies_by_language[language]

        if not recalls:
            continue

        mean_recall = sum(recalls) / len(recalls)
        mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
        mean_latency_ms = sum(latencies) / len(latencies)

        summary[language] = {
            "question_count": len(recalls),
            "mean_recall": mean_recall,
            "mrr": mrr,
            "mean_latency_ms": mean_latency_ms,
        }
        print(
            f"{language}: "
            f"{len(recalls)} questions | "
            f"Mean Recall@{top_k}: {mean_recall:.2f} | "
            f"MRR: {mrr:.2f} | "
            f"Mean Latency: {mean_latency_ms:.2f} ms"
        )

    return summary

if __name__ == "__main__":
    import mlflow

    TOP_K = 3

    questions = load_semantic_questions(QUESTIONS_PATH)

    embeddings, records = load_index()
    model = SentenceTransformer(MODEL_NAME)

    summary = evaluate(
        questions,
        model,
        embeddings,
        records,
        top_k=TOP_K,
    )

    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    mlflow.set_experiment("civil-code-rag-retrieval")

    git_commit, git_dirty = get_git_metadata()
    import json
    with mlflow.start_run(run_name=f"retrieval-eval-topk{TOP_K}"):

        mlflow.set_tag("project", "civil-code-rag")
        mlflow.set_tag("pipeline", "retrieval-evaluation")
        mlflow.set_tag("git_commit", git_commit)
        mlflow.set_tag("git_dirty", str(git_dirty).lower())

        mlflow.log_param("top_k", TOP_K)
        mlflow.log_param("embedding_model", MODEL_NAME)
        mlflow.log_param(
            "evaluation_dataset",
            "eval/dev_questions.jsonl",
        )
        mlflow.log_param("question_count", len(questions))



        for language, metrics in summary.items():
            mlflow.log_metric(
                f"{language}_mean_recall_at_k",
                metrics["mean_recall"],
            )
            mlflow.log_metric(
                f"{language}_mrr",
                metrics["mrr"],
            )
            mlflow.log_metric(
                f"{language}_mean_latency_ms",
                metrics["mean_latency_ms"],
            )

        mlflow.log_dict(
            summary,
            "evaluation_summary.json",
        )