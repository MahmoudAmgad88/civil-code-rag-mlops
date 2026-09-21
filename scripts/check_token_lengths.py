"""Check whether search records fit within the embedding model's token limit."""

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. Configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SEARCH_RECORDS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "search_records.jsonl"
)

MODEL_NAME = "intfloat/multilingual-e5-small"


# --------------------------------------------------
# 2. Load search records
# --------------------------------------------------

def load_search_records(file_path):
    """Read all language-specific search records."""

    with file_path.open(encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


# --------------------------------------------------
# 3. Count tokens
# --------------------------------------------------

def check_token_lengths(records, model):
    """Count document tokens without truncating any text."""

    results = []

    for record in records:

        # E5 requires the passage prefix for document embeddings.
        passage = "passage: " + record["text_search"]

        # Use the same tokenizer as the embedding model.
        # truncation=False is essential: we want to DETECT long
        # inputs, not silently shorten them.
        token_ids = model.tokenizer(
            passage,
            add_special_tokens=True,
            truncation=False,
        )["input_ids"]

        results.append(
            {
                "record_id": record["record_id"],
                "language": record["language"],
                "token_count": len(token_ids),
            }
        )

    return results


# --------------------------------------------------
# 4. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    records = load_search_records(SEARCH_RECORDS_PATH)

    model = SentenceTransformer(MODEL_NAME)

    max_length = model.max_seq_length

    results = check_token_lengths(records, model)

    # Sort longest articles first.
    results.sort(
        key=lambda item: item["token_count"],
        reverse=True,
    )

    # Identify records that exceed the model's limit.
    oversized = [
        item
        for item in results
        if item["token_count"] > max_length
    ]

    print("=" * 50)
    print("TOKEN LENGTH REPORT")
    print("=" * 50)

    print(f"Total search records: {len(records)}")
    print(f"Model token limit: {max_length}")

    print("\nLongest 10 records:")

    for item in results[:10]:
        print(
            f"{item['record_id']} | "
            f"{item['language']} | "
            f"{item['token_count']} tokens"
        )

    print(f"\nRecords exceeding token limit: {len(oversized)}")

    for item in oversized:
        print(
            f"OVERSIZED: {item['record_id']} | "
            f"{item['token_count']} tokens"
        )

    print("\n" + "=" * 50)

    if oversized:
        print("RESULT: Some records need chunking before embedding.")
    else:
        print("RESULT: All records fit within the model's token limit.")