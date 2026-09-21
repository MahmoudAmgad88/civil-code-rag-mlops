"""Extract English Civil Code articles 1–160 from page-by-page PDF text.

Input:  data/raw_pages/pypdf/page_001.txt through page_018.txt.
Output: data/processed/english_articles_001_160.jsonl.

This is an intermediate English-only parser, not the final validated bilingual corpus.
"""

import json
import re
from collections import Counter
from pathlib import Path


# --------------------------------------------------
# 1. Project paths and subset settings
# --------------------------------------------------

# Resolve paths from the script's location, not the terminal's location.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw_pages" / "pypdf"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "english_articles_001_160.jsonl"

FIRST_PAGE = 1
LAST_PAGE = 18
LAST_ARTICLE = 160


# --------------------------------------------------
# 2. Patterns for article and section boundaries
# --------------------------------------------------

# Match a complete English article header, including reversed and mixed
# Arabic/English header layouts. A full match avoids ordinary references.
ENGLISH_HEADER = re.compile(
    r"^(?:مادة\s*[0-9٠-٩]+\s*[\(\)]*\s*)?"
    r"(?:Article\s+(\d{1,4})|(\d{1,4})\s+Article)"
    r"\s*[.:]?\s*$",
    re.IGNORECASE,
)

# Detect Arabic article headers so their body text is not collected as English.
# This pattern is for a boundary check, not for parsing Arabic articles.
ARABIC_HEADER = re.compile(
    r"^\s*\(?\s*(?:"
    r"مادة\s*\(?\s*[0-9٠-٩]+"
    r"|"
    r"[0-9٠-٩]+\s*\)?\s*مادة"
    r")(?:\s|\)|\(|$)"
)

# Once one of these English headings appears, ignore the intervening section
# titles until the next English article header. Compile this pattern once.
SECTION_HEADING = re.compile(
    r"^(?:"
    r"SECTION\s+[IVXLC\d]+"
    r"|(?:FIRST|SECOND|THIRD)\s+PART"
    r"|BOOK\s+[IVXLC\d]+"
    r"|CHAPTER\s+[IVXLC\d]+"
    r")\b",
    re.IGNORECASE,
)

# Look for actual Arabic letters; Arabic-Indic digits alone do not count.
ARABIC_LETTERS = re.compile(r"[\u0621-\u064A]")
ENGLISH_LETTERS = re.compile(r"[A-Za-z]")


# --------------------------------------------------
# 3. Extract article records from the raw page files
# --------------------------------------------------

def parse_english(first_page=FIRST_PAGE, last_page=LAST_PAGE):
    """Collect English article text with its first and last PDF page numbers."""
    records = []
    current_article = None  # The article whose text is being collected.
    text_lines = []        # Original English lines for that article.
    collecting_english = False
    skip_until_next_article = False

    # Keep page order so that articles spanning multiple pages stay together.
    for page_number in range(first_page, last_page + 1):
        page_path = RAW_DIR / f"page_{page_number:03d}.txt"
        page_text = page_path.read_text(encoding="utf-8")

        for line in page_text.splitlines():
            stripped_line = line.strip()  # For checks only; keep `line` for output.

            # A new English header closes the previous article and starts one.
            # Check this BEFORE skip_until_next_article so collection can resume.
            match = ENGLISH_HEADER.fullmatch(stripped_line)
            if match:
                article_number = int(match.group(1) or match.group(2))

                if current_article is not None:
                    current_article["text_en"] = "\n".join(text_lines).strip()
                    records.append(current_article)

                # Do not include articles outside the selected 1–160 subset.
                if article_number > LAST_ARTICLE:
                    return records

                current_article = {
                    "number": article_number,
                    "text_en": "",
                    "page_start": page_number,
                    "page_end": page_number,
                }
                text_lines = []
                collecting_english = True
                skip_until_next_article = False
                continue

            # Nothing belongs to an article until its first header is found.
            if current_article is None:
                continue

            # Section headings and the titles that follow are not article text.
            if SECTION_HEADING.match(stripped_line):
                skip_until_next_article = True
                collecting_english = False
                continue

            # In the source PDF, Article 54 holds the repeal note for 54–80.
            # Stop at the next Arabic chapter heading to avoid attaching its
            # English title to the repeal note. This is NOT status verification.
            if current_article["number"] == 54 and stripped_line.startswith("الفصل"):
                skip_until_next_article = True
                collecting_english = False
                continue

            # Do not resume on any line between the heading and next article.
            if skip_until_next_article:
                continue

            # An Arabic article header is a boundary for English text.
            if ARABIC_HEADER.match(stripped_line):
                collecting_english = False
                continue

            # The bilingual extraction may place Arabic body text before the
            # remaining English text. Resume when an English line is found.
            # NOTE: Mixed Arabic/English lines are skipped, not reconstructed.
            if not collecting_english:
                if not ENGLISH_LETTERS.search(stripped_line):
                    continue
                collecting_english = True

            if not stripped_line:
                continue

            # Never copy a mixed-language line into the English-only record.
            # This can lose English words (e.g., Article 20): review separately.
            if ARABIC_LETTERS.search(stripped_line):

                if current_article["number"] == 20 and page_number == 4:

                    # Find the beginning of the verified English continuation.
                    english_start = stripped_line.find(
                        "contracts are concluded."
                    )

                    if english_start != -1:

                        # Preserve the English text from the raw PDF extraction.
                        english_text = stripped_line[english_start:]

                        text_lines.append(english_text)

                        current_article["page_end"] = page_number

                        continue

                    # --------------------------------------------------
                    # Restore the verified English continuation of CC-91.
                    # --------------------------------------------------

                    # On PDF page 9, the first English continuation line
                    # appears after Arabic text in the same extracted line.
                    # Keep only the English part, without altering its wording.

                if current_article["number"] == 91 and page_number == 9:

                    english_marker = "time that it comes to the knowledge"

                    english_start = stripped_line.find(english_marker)

                    if english_start != -1:

                        english_text = stripped_line[english_start:]

                        text_lines.append(english_text)

                        current_article["page_end"] = page_number

                        collecting_english = True

                        continue
                collecting_english = False
                continue

            # Keep the source line; only its final surrounding blank lines are
            # removed when the article is saved.
            text_lines.append(line)
            current_article["page_end"] = page_number

    # The last article might not be followed by another header in this subset.
    if current_article is not None:
        current_article["text_en"] = "\n".join(text_lines).strip()
        records.append(current_article)

    return records


# --------------------------------------------------
# 4. Validate extracted article IDs and obvious text issues
# --------------------------------------------------

def validate_articles(records):
    """Print article counts and flag obvious extraction issues for review."""
    numbers = [record["number"] for record in records]
    counts = Counter(numbers)
    expected = set(range(1, LAST_ARTICLE + 1))

    missing = sorted(expected - counts.keys())
    duplicates = sorted(number for number, count in counts.items() if count > 1)
    empty_articles = [r["number"] for r in records if not r["text_en"]]
    arabic_text_issues = [
        r["number"] for r in records if ARABIC_LETTERS.search(r["text_en"])
    ]
    heading_issues = [
        r["number"]
        for r in records
        if any(SECTION_HEADING.match(line.strip()) for line in r["text_en"].splitlines())
    ]

    print("\n" + "=" * 50)
    print("ENGLISH ARTICLE PARSING REPORT")
    print("=" * 50)
    print(f"Total records: {len(records)}")
    print(f"Unique article numbers: {len(counts)}")
    print(f"Missing articles: {missing}")
    print(f"Duplicate articles: {duplicates}")
    print(f"Empty article texts: {empty_articles}")
    print(f"Records containing Arabic text: {arabic_text_issues}")
    print(f"Records containing section headings: {heading_issues}")

    # Article 54 is a repeal-note record, not ordinary substantive article text.
    article_54 = next((r for r in records if r["number"] == 54), None)
    if article_54 is not None:
        print("\nArticle 54: review the repeal note separately.")
        print(article_54["text_en"])

    # Counts and regex checks do not prove the article bodies are complete.
    print("\nManual check still needed: mixed-language Article 20 and source fidelity.")


# --------------------------------------------------
# 5. Write one JSON object per line
# --------------------------------------------------

def save_articles(records):
    """Write English article records as UTF-8 JSONL without escaping Unicode."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\nSaved records to: {OUTPUT_PATH}")


# --------------------------------------------------
# 6. Run the extraction and show two records for manual checks
# --------------------------------------------------

def main():
    """Run parsing, print its validation report, and save the JSONL file."""
    records = parse_english()
    validate_articles(records)
    save_articles(records)

    # Article 83 spans pages 7–8; Article 160 is our subset's last article.
    for article_number in (83, 160):
        article = next((r for r in records if r["number"] == article_number), None)
        print(f"\n{'=' * 50}\nARTICLE {article_number}\n{'=' * 50}")
        print(article if article is not None else f"Article {article_number} not found.")


if __name__ == "__main__":
    main()
