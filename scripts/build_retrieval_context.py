"""Build source-linked context for a future grounded LLM answer."""

import json
from pathlib import Path

from civil_code_rag.retrieval.context_builder import build_context

# 1. Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

ARTICLES_PATH = (
    PROJECT_ROOT / "data" / "processed" / "articles.jsonl"
)


# 2. Load original articles
def load_article_lookup(file_path):
    """Create a dictionary for looking up an article by its ID."""

    lookup = {}

    with file_path.open(encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            article = json.loads(line)
            article_id = article["article_id"]

            if article_id in lookup:
                raise ValueError(f"Duplicate article ID: {article_id}")

            lookup[article_id] = article

    return lookup

# 4. Run one end-to-end context-building example
if __name__ == "__main__":

    from sentence_transformers import SentenceTransformer

    from scripts.search_articles import (
        MODEL_NAME,
        load_index,
        search_articles,
    )

    question = "What happens to the parties when a contract is rescinded?"
    language = "en"

    embeddings, search_records = load_index()

    model = SentenceTransformer(MODEL_NAME)

    results = search_articles(
        question=question,
        language=language,
        model=model,
        embeddings=embeddings,
        records=search_records,
        top_k=5,
    )

    article_lookup = load_article_lookup(ARTICLES_PATH)

    context = build_context(
        results=results,
        article_lookup=article_lookup,
        language=language,
    )

    print("=" * 50)
    print("QUESTION")
    print("=" * 50)
    print(question)

    print("\n" + "=" * 50)
    print("RETRIEVED EVIDENCE CONTEXT")
    print("=" * 50)
    print(context)