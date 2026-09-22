"""Generate metadata for the Civil Code RAG corpus."""

import hashlib
import json
from pathlib import Path


# 1. Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

PDF_PATH = DATA_DIR / "Egyptian Civil Code.pdf"

ARTICLES_PATH = DATA_DIR / "processed" / "articles.jsonl"

SEARCH_RECORDS_PATH = DATA_DIR / "processed" / "search_records.jsonl"

MANIFEST_PATH = DATA_DIR / "processed" / "corpus_manifest.json"

# 2. Load JSONL records
def load_jsonl(path: Path) -> list[dict]:
    """Load JSON records from a JSONL file."""

    with path.open(encoding="utf-8") as file:
        return [
            json.loads(line)
            for line in file
            if line.strip()
        ]


# 3. Calculate file hash
def calculate_sha256(path: Path) -> str:
    """Calculate the SHA-256 hash of a file."""

    hasher = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(block)

    return hasher.hexdigest()

def build_manifest() -> dict:
    """Build metadata describing the current RAG corpus."""

    from collections import Counter
    from pypdf import PdfReader

    articles = load_jsonl(ARTICLES_PATH)
    search_records = load_jsonl(SEARCH_RECORDS_PATH)

    # Separate Civil Code articles from PROM records.
    civil_articles = [
        article
        for article in articles
        if article["article_id"].startswith("CC-")
    ]

    article_numbers = sorted(
        article["article_number"]
        for article in civil_articles
    )

    repealed_numbers = sorted(
        article["article_number"]
        for article in civil_articles
        if article["alignment"] == "repealed"
    )

    language_counts = Counter(
        record["language"]
        for record in search_records
    )

    # Validate the frozen MVP scope.
    if article_numbers != list(range(1, 161)):
        raise ValueError("Unexpected Civil Code article range.")

    if repealed_numbers != list(range(54, 81)):
        raise ValueError("Unexpected repealed article range.")

    manifest = {
        "schema_version": "1.0",
        "parser_version": "v1-current-mvp",
        "source_pdf_sha256": calculate_sha256(PDF_PATH),
        "source_pdf_pages": len(PdfReader(PDF_PATH).pages),
        "corpus_sha256": calculate_sha256(ARTICLES_PATH),
        "record_count": len(articles),
        "article_range": [
            min(article_numbers),
            max(article_numbers),
        ],
        "covered_pages": [
            min(article["page_start"] for article in articles),
            max(article["page_end"] for article in articles),
        ],
        "repealed_ranges": [
            [min(repealed_numbers), max(repealed_numbers)]
        ],
        "languages": sorted(language_counts),
        "search_record_count": len(search_records),
        "coverage_statement_ar": (
            "هذه نسخة تجريبية تغطي المواد من 1 إلى 160 فقط "
            "من الصفحات 1 إلى 18 من ملف القانون المدني المصري. "
            "لا تمثل تغطية كاملة للقانون أو تحققًا من حالته القانونية الحالية."
        ),
        "coverage_statement_en": (
            "This experimental corpus covers Articles 1–160 "
            "from PDF pages 1–18 only. It does not cover the "
            "entire Egyptian Civil Code or verify current legal status."
        ),
    }

    return manifest

# 4. Verify the source files
if __name__ == "__main__":

    manifest = build_manifest()

    MANIFEST_PATH.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"Manifest saved to: {MANIFEST_PATH}")