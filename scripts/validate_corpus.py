
"""Validate the structure of the Civil Code RAG subset."""

import json
from collections import Counter
from pathlib import Path


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CORPUS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "articles.jsonl"
)


# --------------------------------------------------
# 2. Load article records
# --------------------------------------------------

def load_articles(file_path):
    """Read the corpus and return its article records."""

    with file_path.open(encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


# --------------------------------------------------
# 3. Validate article records
# --------------------------------------------------

def validate_corpus(records):
    """Check IDs, article coverage, and required metadata."""

    # Verify the expected number of records.
    assert len(records) == 162

    # Every article must have a unique identifier.
    article_ids = [
        record["article_id"]
        for record in records
    ]

    assert len(article_ids) == len(set(article_ids))

    # Expect Civil Code Articles 1-160
    # and two promulgation-law articles.
    expected_ids = {
        f"CC-{number}"
        for number in range(1, 161)
    }

    expected_ids.update({"PROM-1", "PROM-2"})

    assert set(article_ids) == expected_ids

    # Check the distribution of article types.
    alignments = Counter(
        record["alignment"]
        for record in records
    )

    assert alignments["paired"] == 133
    assert alignments["ar_only"] == 2
    assert alignments["repealed"] == 27

    # Validate the structure of every article.
    for record in records:

        # Page numbers must be valid and ordered.
        assert 1 <= record["page_start"] <= record["page_end"] <= 18

        # The current legal status is not verified.
        assert record["verified_status"] == "unverified"

        # Repealed records must carry source evidence.
        if record["alignment"] == "repealed":

            assert record["text_ar_original"] is None
            assert record["text_en_original"] is None

            assert (
                record["source_status"]
                == "repealed_per_source_note"
            )

            assert record["status_evidence"]

        else:

            # Every other article must contain
            # actual legal text in at least one language.
            assert (
                record["text_ar_original"]
                or record["text_en_original"]
            )

    # Confirm the exact repealed range.
    repealed_ids = {
        record["article_id"]
        for record in records
        if record["alignment"] == "repealed"
    }

    expected_repealed = {
        f"CC-{number}"
        for number in range(54, 81)
    }

    assert repealed_ids == expected_repealed

    print("All corpus structure checks passed.")


# --------------------------------------------------
# 4. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    articles = load_articles(CORPUS_PATH)

    validate_corpus(articles)