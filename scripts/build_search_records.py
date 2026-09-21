
"""Create language-specific search records from the article corpus."""

import json
import re
from pathlib import Path


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_PATH = DATA_DIR / "articles.jsonl"

OUTPUT_PATH = DATA_DIR / "search_records.jsonl"


# --------------------------------------------------
# 2. Text normalization
# --------------------------------------------------

def normalize_search_text(text, language):
    """Prepare text for search without changing the original text."""

    # Replace repeated whitespace and line breaks with one space.
    normalized = " ".join(text.split())

    if language == "en":
        # Standardize English capitalization for search.
        return normalized.lower()

    if language == "ar":
        # Remove Arabic diacritics.
        normalized = re.sub(
            r"[\u064B-\u065F\u0670]",
            "",
            normalized,
        )

        # Remove tatweel (Arabic elongation character).
        normalized = normalized.replace("\u0640", "")

    return normalized


# --------------------------------------------------
# 3. Load the article corpus
# --------------------------------------------------

def load_articles(file_path):
    """Read article records from a JSONL file."""

    records = []

    with file_path.open("r", encoding="utf-8") as file:

        for line in file:

            if line.strip():
                records.append(json.loads(line))

    return records


# --------------------------------------------------
# 4. Create search records
# --------------------------------------------------

def build_search_records(articles):
    """Create one search record per available article language."""

    search_records = []

    for article in articles:

        # Repealed articles have no individual legal text.
        # Their status notes will be handled by exact lookup.
        if article["alignment"] == "repealed":
            continue

        article_id = article["article_id"]

        # Process Arabic and English separately.
        for language, text_field in [
            ("ar", "text_ar_original"),
            ("en", "text_en_original"),
        ]:

            original_text = article[text_field]

            # Skip languages that have no available text.
            if not original_text or not original_text.strip():
                continue

            search_record = {
                "record_id": f"{article_id}:{language}",
                "article_id": article_id,
                "language": language,

                # Preserve the original extracted article text.
                "text_display": original_text,

                # Store normalized text separately for search.
                "text_search": normalize_search_text(
                    original_text,
                    language,
                ),
            }

            search_records.append(search_record)

    return search_records


# --------------------------------------------------
# 5. Save search records
# --------------------------------------------------

def save_jsonl(records, output_path):
    """Save search records as JSONL using UTF-8 encoding."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:

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

    articles = load_articles(INPUT_PATH)

    search_records = build_search_records(articles)

    # Every search record must have a unique identifier.
    record_ids = [
        record["record_id"]
        for record in search_records
    ]

    assert len(record_ids) == len(set(record_ids))

    # Verify that every search record refers to an article.
    article_ids = {
        article["article_id"]
        for article in articles
    }

    assert all(
        record["article_id"] in article_ids
        for record in search_records
    )

    save_jsonl(search_records, OUTPUT_PATH)

    # Report the number of records per language.
    arabic_count = sum(
        record["language"] == "ar"
        for record in search_records
    )

    english_count = sum(
        record["language"] == "en"
        for record in search_records
    )

    print("=" * 50)
    print("SEARCH RECORDS REPORT")
    print("=" * 50)

    print(f"Original article records: {len(articles)}")
    print(f"Arabic search records: {arabic_count}")
    print(f"English search records: {english_count}")
    print(f"Total search records: {len(search_records)}")
    print(f"Unique record IDs: {len(set(record_ids))}")

    print(f"\nSaved records to: {OUTPUT_PATH}")

    # Inspect Article 20 in both languages.
    print("\nARTICLE 20 SEARCH RECORDS")

    for record in search_records:

        if record["article_id"] == "CC-20":
            print(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    indent=2,
                )
            )