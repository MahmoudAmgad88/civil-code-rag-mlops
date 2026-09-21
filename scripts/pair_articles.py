
"""Pair Arabic and English Civil Code articles by their identifiers."""

import json
from pathlib import Path


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data" / "processed"

ARABIC_PATH = DATA_DIR / "arabic_articles_001_160.jsonl"
ENGLISH_PATH = DATA_DIR / "english_articles_001_160.jsonl"

# Intermediate output: repealed records will be added later.
OUTPUT_PATH = DATA_DIR / "paired_articles_001_160.jsonl"


# --------------------------------------------------
# 2. Load JSONL records
# --------------------------------------------------

def load_jsonl(file_path):
    """Load JSONL records into a list of dictionaries."""

    records = []

    with file_path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records


# --------------------------------------------------
# 3. Pair Arabic and English articles
# --------------------------------------------------

def pair_articles(arabic_records, english_records):
    """Combine records for the same Civil Code article."""

    paired_records = []

    # Build a dictionary for fast English article lookup.
    # Article 54 contains a repeal note, not a normal article.
    english_lookup = {}

    for record in english_records:

        number = record["number"]

        if number == 54:
            continue

        if number in english_lookup:
            raise ValueError(
                f"Duplicate English article: {number}"
            )

        english_lookup[number] = record

    # Track IDs to prevent accidental duplicate pairing.
    seen_ids = set()

    for arabic_record in arabic_records:

        article_id = arabic_record["article_id"]
        number = arabic_record["number"]
        source = arabic_record["source"]

        if article_id in seen_ids:
            raise ValueError(
                f"Duplicate Arabic article: {article_id}"
            )

        seen_ids.add(article_id)

        # English records are numbered as Civil Code articles.
        # Do not pair them with promulgation-law articles.
        english_record = None

        if source == "civil_code":
            english_record = english_lookup.get(number)

        # Preserve the English text when available.
        english_text = (
            english_record["text_en"]
            if english_record is not None
            else None
        )

        # Use page references from both sources when available.
        page_start = arabic_record["page_start"]
        page_end = arabic_record["page_end"]

        if english_record is not None:
            page_start = min(
                page_start,
                english_record["page_start"],
            )

            page_end = max(
                page_end,
                english_record["page_end"],
            )

        # Record extraction and alignment issues.
        issues = []

        if english_record is None:
            issues.append("missing_en")

        if article_id == "PROM-2":
            issues.append("date_extraction_needs_review")

        # Create one bilingual article record.
        paired_record = {
            "article_id": article_id,
            "source": source,
            "article_number": number,
            "text_ar_original": arabic_record["text_ar"],
            "text_en_original": english_text,
            "page_start": page_start,
            "page_end": page_end,
            "source_status": "no_source_annotation",
            "status_evidence": None,
            "verified_status": "unverified",
            "alignment": (
                "paired"
                if english_record is not None
                else "ar_only"
            ),
            "issues": issues,
        }

        paired_records.append(paired_record)

    # Ensure no English-only Civil Code article was silently lost.
    paired_cc_numbers = {
        record["article_number"]
        for record in paired_records
        if record["source"] == "civil_code"
    }

    unpaired_english = (
        set(english_lookup) - paired_cc_numbers
    )

    if unpaired_english:
        raise ValueError(
            f"Unpaired English articles: "
            f"{sorted(unpaired_english)}"
        )

    return paired_records


# --------------------------------------------------
# 4. Add repealed article records
# --------------------------------------------------

def add_repealed_articles(paired_records, english_records):
    """Add records for Articles 54-80 using the PDF repeal note."""

    # Locate the English repeal note extracted from Article 54.
    repeal_record = next(
        (
            record
            for record in english_records
            if record["number"] == 54
        ),
        None,
    )

    if repeal_record is None:
        raise ValueError("Repeal note for Articles 54-80 not found.")

    # Preserve the actual note extracted from the PDF.
    repeal_note = repeal_record["text_en"].strip()

    # Verify that the expected source note was found.
    if not (
        "54-80" in repeal_note
        and "repealed" in repeal_note.lower()
    ):
        raise ValueError("Unexpected repeal note content.")

    # Work on a new list without modifying the input records.
    final_records = list(paired_records)

    # Collect existing IDs to prevent duplicates.
    existing_ids = {
        record["article_id"]
        for record in final_records
    }

    # Create one record for each repealed article.
    for number in range(54, 81):

        article_id = f"CC-{number}"

        if article_id in existing_ids:
            raise ValueError(
                f"Duplicate article ID: {article_id}"
            )

        repealed_record = {
            "article_id": article_id,
            "source": "civil_code",
            "article_number": number,

            # No individual article body exists in our source.
            "text_ar_original": None,
            "text_en_original": None,

            # These pages locate the repeal note, not
            # the original text of each repealed article.
            "page_start": repeal_record["page_start"],
            "page_end": repeal_record["page_end"],

            # This status describes only what the PDF states.
            "source_status": "repealed_per_source_note",
            "status_evidence": repeal_note,

            # Current legal status has not been verified.
            "verified_status": "unverified",

            "alignment": "repealed",
            "issues": [],
        }

        final_records.append(repealed_record)
        existing_ids.add(article_id)

    # Sort promulgation articles first, then Civil Code articles.
    final_records.sort(
        key=lambda record: (
            0 if record["source"] == "promulgation_law" else 1,
            record["article_number"],
        )
    )

    return final_records

# --------------------------------------------------
# 4. Save paired records
# --------------------------------------------------

def save_jsonl(records, output_path):
    """Save paired article records in JSONL format."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open("w", encoding="utf-8") as file:

        for record in records:

            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                ) + "\n"
            )


# --------------------------------------------------
# 5. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    arabic_records = load_jsonl(ARABIC_PATH)
    english_records = load_jsonl(ENGLISH_PATH)

    paired_records = pair_articles(
        arabic_records,
        english_records,
    )


    # Save the intermediate paired dataset.
    save_jsonl(paired_records, OUTPUT_PATH)

    # Add the 27 repealed articles to the existing records.
    final_records = add_repealed_articles(
        paired_records,
        english_records,
    )

    # Validate article coverage before saving.
    article_ids = [
        record["article_id"]
        for record in final_records
    ]

    expected_ids = {
        "PROM-1",
        "PROM-2",
    } | {
        f"CC-{number}"
        for number in range(1, 161)
    }

    if len(article_ids) != len(set(article_ids)):
        raise ValueError("Duplicate article IDs found.")

    if set(article_ids) != expected_ids:
        raise ValueError("Missing or unexpected article IDs.")

    # Save the final corpus.
    final_path = DATA_DIR / "articles.jsonl"

    save_jsonl(final_records, final_path)

    print("\n" + "=" * 50)
    print("FINAL CORPUS REPORT")
    print("=" * 50)

    print(f"Total article records: {len(final_records)}")

    print(
        "Paired articles:",
        sum(
            record["alignment"] == "paired"
            for record in final_records
        ),
    )

    print(
        "Arabic-only articles:",
        sum(
            record["alignment"] == "ar_only"
            for record in final_records
        ),
    )

    print(
        "Repealed articles:",
        sum(
            record["alignment"] == "repealed"
            for record in final_records
        ),
    )

    print(f"Unique article IDs: {len(set(article_ids))}")

    print(f"\nFinal corpus saved to: {final_path}")

    print("=" * 50)
    print("ARTICLE PAIRING REPORT")
    print("=" * 50)

    print(f"Arabic records: {len(arabic_records)}")
    print(f"English records: {len(english_records)}")
    print(f"Total output records: {len(paired_records)}")

    print(f"\nSaved records to: {OUTPUT_PATH}")

    # Inspect a representative bilingual article.
    article_20 = next(
        record
        for record in paired_records
        if record["article_id"] == "CC-20"
    )

    print("\nARTICLE 20:")
    print(
        json.dumps(
            article_20,
            ensure_ascii=False,
            indent=2,
        )
    )