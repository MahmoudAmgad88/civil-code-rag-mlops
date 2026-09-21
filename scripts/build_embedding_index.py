
"""Build and save embeddings for all Civil Code search records."""

import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SEARCH_RECORDS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "search_records.jsonl"
)

INDEX_DIR = PROJECT_ROOT / "data" / "index"

EMBEDDINGS_PATH = INDEX_DIR / "embeddings.npy"
INDEX_RECORDS_PATH = INDEX_DIR / "index_records.jsonl"

MODEL_NAME = "intfloat/multilingual-e5-small"


# --------------------------------------------------
# 2. Load search records
# --------------------------------------------------

def load_search_records(file_path):
    """Read search records while preserving their file order."""

    records = []

    with file_path.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records


# --------------------------------------------------
# 3. Prepare passages
# --------------------------------------------------

def prepare_passages(records, model):
    """Add the E5 passage prefix and reject oversized inputs."""

    passages = []

    for record in records:

        passage = "passage: " + record["text_search"]

        # Avoid silently truncating legal article text.
        token_count = len(
            model.tokenizer(
                passage,
                add_special_tokens=True,
                truncation=False,
            )["input_ids"]
        )

        if token_count > model.max_seq_length:
            raise ValueError(
                f"{record['record_id']} has {token_count} tokens; "
                f"model limit is {model.max_seq_length}."
            )

        passages.append(passage)

    return passages


# --------------------------------------------------
# 4. Generate embeddings
# --------------------------------------------------

def generate_embeddings(passages, model):
    """Generate one normalized embedding per search record."""

    embeddings = model.encode(
        passages,
        batch_size=16,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=True,
    )

    return embeddings


# --------------------------------------------------
# 5. Save the index
# --------------------------------------------------

def save_index(records, embeddings):
    """Save vectors and their matching records in the same order."""

    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Save numerical vectors in NumPy's binary format.
    np.save(EMBEDDINGS_PATH, embeddings)

    # Save the metadata and text associated with each vector.
    with INDEX_RECORDS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                ) + "\n"
            )


# --------------------------------------------------
# 6. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    records = load_search_records(SEARCH_RECORDS_PATH)

    # Avoid duplicate or missing vector-to-record mappings.
    record_ids = [record["record_id"] for record in records]

    if len(record_ids) != len(set(record_ids)):
        raise ValueError("Duplicate search record IDs found.")

    if not records:
        raise ValueError("No search records found.")

    print(f"Loaded search records: {len(records)}")

    model = SentenceTransformer(MODEL_NAME)

    passages = prepare_passages(records, model)

    print(f"Prepared passages: {len(passages)}")

    embeddings = generate_embeddings(passages, model)

    # Each record must have exactly one embedding.
    if embeddings.shape[0] != len(records):
        raise ValueError("Embedding count does not match record count.")

    # Reject invalid numerical values before saving.
    if not np.isfinite(embeddings).all():
        raise ValueError("Embeddings contain NaN or infinite values.")

    save_index(records, embeddings)

    print("\n" + "=" * 50)
    print("EMBEDDING INDEX REPORT")
    print("=" * 50)

    print(f"Model: {MODEL_NAME}")
    print(f"Search records: {len(records)}")
    print(f"Embeddings shape: {embeddings.shape}")
    print(f"Embeddings dtype: {embeddings.dtype}")
    print(f"First record ID: {records[0]['record_id']}")

    print(f"\nSaved embeddings to: {EMBEDDINGS_PATH}")
    print(f"Saved index records to: {INDEX_RECORDS_PATH}")