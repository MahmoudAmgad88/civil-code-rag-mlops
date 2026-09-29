"""Load the embedding index for semantic article retrieval."""

import json
from pathlib import Path

import numpy as np


class Retriever:
    """Hold the embedding model and its matching search index."""

    def __init__(self, index_dir: Path, model) -> None:
        self.index_dir = index_dir
        self.model = model

        self.embeddings, self.records = self._load_index()

    def _load_index(self) -> tuple[np.ndarray, list[dict]]:
        """Load vectors and their records, then validate their alignment."""

        embeddings_path = self.index_dir / "embeddings.npy"
        records_path = self.index_dir / "index_records.jsonl"

        embeddings = np.load(
            embeddings_path,
            allow_pickle=False,
        )

        with records_path.open(encoding="utf-8") as file:
            records = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        if embeddings.ndim != 2:
            raise ValueError("Expected a 2D embedding matrix.")

        if len(embeddings) != len(records):
            raise ValueError(
                "Embedding and record counts do not match."
            )

        if not np.isfinite(embeddings).all():
            raise ValueError("Index contains invalid vectors.")

        return embeddings, records

    def search(
        self,
        question: str,
        language: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Return the most similar records in the requested language."""

        if language not in {"ar", "en"}:
            raise ValueError("Language must be 'ar' or 'en'.")

        if not question.strip():
            raise ValueError("Question must not be empty.")

        # 1. Select records belonging to the requested language.
        matching_indices = [
            index
            for index, record in enumerate(self.records)
            if record["language"] == language
        ]

        if not matching_indices:
            return []

        # 2. Generate the question embedding.
        query_text = "query: " + question.strip()

        query_embedding = self.model.encode(
            query_text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        if query_embedding.shape[0] != self.embeddings.shape[1]:
            raise ValueError(
                "Query and document embedding dimensions do not match."
            )

        # 3. Compare the question only with records in its language.
        language_embeddings = self.embeddings[matching_indices]

        similarity_scores = language_embeddings @ query_embedding

        # 4. Rank by similarity, highest first.
        ranked_positions = np.argsort(similarity_scores)[::-1][:top_k]

        results = []

        for position in ranked_positions:
            original_index = matching_indices[int(position)]

            results.append(
                {
                    "record": self.records[original_index],
                    "similarity": float(similarity_scores[position]),
                }
            )

        return results
