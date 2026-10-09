"""Load and retrieve Civil Code articles by their IDs."""

import json
from pathlib import Path


class ArticleRepository:
    """Provide access to articles stored in a JSONL corpus."""

    def __init__(self, corpus_path: Path) -> None:
        self.corpus_path = corpus_path
        self.articles = self._load_articles()

    def _load_articles(self) -> dict[str, dict]:
        """Load articles once and reject duplicate article IDs."""

        lookup = {}

        with self.corpus_path.open(encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue

                article = json.loads(line)
                article_id = article["article_id"]

                if article_id in lookup:
                    raise ValueError(
                        f"Duplicate article ID: {article_id}"
                    )

                lookup[article_id] = article

        return lookup

    def get(self, article_id: str) -> dict | None:
        """Return an article or None when its ID is not present."""

        return self.articles.get(article_id)