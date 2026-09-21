"""Run a small embedding smoke test on Arabic and English articles."""

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

# Use a small sample before embedding the full corpus.
SAMPLE_IDS = {
    "CC-20:ar",
    "CC-20:en",
    "CC-91:ar",
    "CC-91:en",
}


# --------------------------------------------------
# 2. Load sample records
# --------------------------------------------------

def load_sample_records(file_path):
    """Load only the search records selected for this smoke test."""

    selected_records = []

    with file_path.open(encoding="utf-8") as file:

        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if record["record_id"] in SAMPLE_IDS:
                selected_records.append(record)

    # Check that all four expected records were found.
    found_ids = {
        record["record_id"]
        for record in selected_records
    }

    if found_ids != SAMPLE_IDS:
        raise ValueError(
            f"Missing sample records: {sorted(SAMPLE_IDS - found_ids)}"
        )

    return selected_records


# --------------------------------------------------
# 3. Generate embeddings
# --------------------------------------------------

def generate_embeddings(records, model):
    """Convert the selected article texts into numerical vectors."""

    # E5 expects the 'passage:' prefix for document texts.
    passages = [
        "passage: " + record["text_search"]
        for record in records
    ]

    # Check input lengths before embedding.
    # Long inputs may be truncated by the model.
    for record, passage in zip(records, passages):

        token_ids = model.tokenizer(
            passage,
            add_special_tokens=True,
            truncation=False,
        )["input_ids"]

        token_count = len(token_ids)

        print(
            f"{record['record_id']}: "
            f"{token_count} tokens"
        )

        if token_count > model.max_seq_length:
            raise ValueError(
                f"{record['record_id']} exceeds the model's "
                f"{model.max_seq_length}-token limit."
            )

    # Return one normalized vector per passage.
    embeddings = model.encode(
        passages,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )

    return embeddings


# --------------------------------------------------
# 4. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    records = load_sample_records(SEARCH_RECORDS_PATH)

    print(f"Loaded sample records: {len(records)}")

    # Load the pretrained model.
    model = SentenceTransformer(MODEL_NAME)

    print(f"Model: {MODEL_NAME}")
    print(f"Max sequence length: {model.max_seq_length}")

    embeddings = generate_embeddings(records, model)

    print("\n" + "=" * 50)
    print("EMBEDDING SMOKE TEST")
    print("=" * 50)

    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Data type: {embeddings.dtype}")
    print(f"First record ID: {records[0]['record_id']}")
    print(f"First five vector values: {embeddings[0][:5]}")