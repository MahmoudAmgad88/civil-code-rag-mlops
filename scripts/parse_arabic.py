
"""
Extract Arabic Civil Code articles from raw PDF text.

The script:
1. Detects Arabic article headers.
2. Extracts Arabic article text.
3. Preserves PDF page references.
4. Separates promulgation-law articles from Civil Code articles.
5. Saves structured records as JSONL.

Scope: Civil Code Articles 1-160.
"""

import json
import re
from pathlib import Path


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

# Locate the project root independently of the terminal.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw_pages" / "pypdf"

OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_PATH = OUTPUT_DIR / "arabic_articles_001_160.jsonl"


# --------------------------------------------------
# 2. Article header detection
# --------------------------------------------------

# Detect Arabic article headers.
# Examples:
# مادة١
# مادة ( ٥١(
# مادة٣٨( Article 83

ARABIC_HEADER = re.compile(
    r"^\s*\(?\s*مادة\s*[\(\)]*\s*"
    r"([٠-٩]+)"
    r"\s*[\(\)]*\s*"
    r"(?:Article\s+\d+)?\s*$",
    re.IGNORECASE,
)


# Detect standalone English article headers.
# English article text must not enter Arabic records.

ENGLISH_HEADER = re.compile(
    r"^(?:Article\s+\d+|\d+\s+Article)"
    r"\s*[.:]?\s*$",
    re.IGNORECASE,
)


# Detect Arabic section and chapter headings.
# These headings are not part of the preceding article.

SECTION_HEADING = re.compile(
    r"^(?:الفصل|القسم|الباب|الكتاب|الجزء)\s+",
)


# Detect standalone Arabic paragraph numbers.
# Example: (١ ( or (٢)

ARABIC_PARAGRAPH = re.compile(
    r"^[\s\(\)]*[٠-٩]+[\s\(\)]*$"
)


# --------------------------------------------------
# 3. Arabic digit conversion
# --------------------------------------------------

DIGIT_MAP = str.maketrans(
    "٠١٢٣٤٥٦٧٨٩",
    "0123456789",
)


def arabic_header_to_int(arabic_digits):
    """Convert reversed Arabic header digits into an integer."""

    # pypdf reverses article-header digits in this PDF.
    corrected_digits = arabic_digits[::-1]

    # Convert Arabic-Indic digits into Western digits.
    western_digits = corrected_digits.translate(DIGIT_MAP)

    return int(western_digits)


# --------------------------------------------------
# 4. Parse Arabic articles
# --------------------------------------------------

def parse_arabic(first_page=1, last_page=18):
    """Extract Arabic article records from the selected PDF pages."""

    records = []

    # Track the current article and its collected text.
    current_article = None
    text_lines = []

    # Track whether the current line belongs to Arabic article text.
    collecting_arabic = False

    # Stop collection after a section heading or repeal note.
    skip_until_next_article = False

    # First two Arabic article headers belong to the promulgation law.
    header_count = 0

    # Store unexpected mixed-language lines for later review.
    mixed_line_issues = []

    for page_number in range(first_page, last_page + 1):

        page_path = RAW_DIR / f"page_{page_number:03d}.txt"

        page_text = page_path.read_text(encoding="utf-8")

        for line in page_text.splitlines():

            stripped_line = line.strip()

            # ------------------------------------------
            # A. Detect a new Arabic article
            # ------------------------------------------

            match = ARABIC_HEADER.fullmatch(stripped_line)

            if match:

                article_number = arabic_header_to_int(
                    match.group(1)
                )

                # Save the previous article before starting a new one.
                if current_article is not None:

                    current_article["text_ar"] = "\n".join(
                        text_lines
                    ).strip()

                    records.append(current_article)

                # Article 161 marks the end of our subset.
                if header_count >= 2 and article_number > 160:
                    return records, mixed_line_issues

                # Distinguish promulgation-law articles from Civil Code articles.
                header_count += 1

                if header_count <= 2:
                    source = "promulgation_law"
                    article_id = f"PROM-{article_number}"

                else:
                    source = "civil_code"
                    article_id = f"CC-{article_number}"

                # Initialize the new article record.
                current_article = {
                    "article_id": article_id,
                    "source": source,
                    "number": article_number,
                    "text_ar": "",
                    "page_start": page_number,
                    "page_end": page_number,
                }

                text_lines = []

                collecting_arabic = True
                skip_until_next_article = False

                continue

            # Ignore lines before the first Arabic article.
            if current_article is None:
                continue

            # ------------------------------------------
            # B. Detect section boundaries
            # ------------------------------------------

            # Stop when a new Arabic chapter or section begins.
            if SECTION_HEADING.match(stripped_line):

                collecting_arabic = False
                skip_until_next_article = True

                continue

            # Article 54-80 repeal note follows Article 53.
            # It must not become part of Article 53.
            if stripped_line.startswith("ألغيت المواد"):

                collecting_arabic = False
                skip_until_next_article = True

                continue

            # Ignore intervening headings and repeal notes.
            if skip_until_next_article:
                continue



            # ------------------------------------------
            # Handle the repealed-articles note after CC-53
            # ------------------------------------------

            # The source note about repealed Articles 54-80
            # must not become part of Article 53's legal text.

            if (
                current_article["article_id"] == "CC-53"
                and stripped_line.startswith("المواد من")
            ):
                collecting_arabic = False
                skip_until_next_article = True
                continue


            # ------------------------------------------
            # Stop at the beginning of the Civil Code
            # ------------------------------------------

            # The promulgation-law article ends before
            # the main Civil Code's introductory headings.

            if (
                current_article["article_id"] == "PROM-2"
                and stripped_line.startswith("نصوص القانون المدنى")
            ):
                collecting_arabic = False
                skip_until_next_article = True
                continue

            # ------------------------------------------
            # C. Skip English article text
            # ------------------------------------------

            if ENGLISH_HEADER.fullmatch(stripped_line):

                collecting_arabic = False

                continue

            # ------------------------------------------
            # D. Handle the verified Article 20 case
            # ------------------------------------------

            # On page 4, Article 20 has Arabic text followed
            # by an English continuation on the same raw line.
            # Preserve the Arabic prefix and discard the English suffix.

            if (
                current_article["article_id"] == "CC-20"
                and page_number == 4
                and "contracts are concluded." in stripped_line
            ):

                arabic_text = stripped_line.split(
                    "contracts are concluded.", 1
                )[0].rstrip()

                if arabic_text:

                    text_lines.append(arabic_text)

                    current_article["page_end"] = page_number

                collecting_arabic = False

                continue



            # ------------------------------------------
            # D.1 Handle the verified Article 91 case
            # ------------------------------------------

            # Article 91 contains an Arabic sentence followed by
            # English text on the same extracted PDF line.
            # Preserve the Arabic prefix without changing its wording.

            if (
                current_article["article_id"] == "CC-91"
                and page_number == 9
                and "time that it comes to the knowledge" in stripped_line
            ):

                arabic_text = stripped_line.split(
                    "time that it comes to the knowledge", 1
                )[0].rstrip()

                if arabic_text:

                    text_lines.append(arabic_text)

                    current_article["page_end"] = page_number

                # Prevent the English continuation from entering
                # the Arabic article record.
                collecting_arabic = False

                continue

            # ------------------------------------------
            # E. Collect Arabic article text
            # ------------------------------------------

            contains_arabic = re.search(
                r"[\u0621-\u064A]",
                stripped_line,
            )

            contains_english = re.search(
                r"[A-Za-z]",
                stripped_line,
            )

            # Do not silently add other mixed-language lines.
            if contains_arabic and contains_english:

                mixed_line_issues.append(
                    {
                        "article_id": current_article["article_id"],
                        "page": page_number,
                        "text": stripped_line,
                    }
                )

                collecting_arabic = False

                continue

            # Resume collection when Arabic body text appears.
            if contains_arabic:

                collecting_arabic = True

                text_lines.append(line)

                current_article["page_end"] = page_number

                continue

            # Preserve paragraph markers within an Arabic article.
            if (
                collecting_arabic
                and ARABIC_PARAGRAPH.fullmatch(stripped_line)
            ):

                text_lines.append(line)

                current_article["page_end"] = page_number

    # Save the final article if the selected pages end
    # before the next Arabic article header.
    if current_article is not None:

        current_article["text_ar"] = "\n".join(
            text_lines
        ).strip()

        records.append(current_article)

    return records, mixed_line_issues


# --------------------------------------------------
# 5. Validate extracted records
# --------------------------------------------------

def validate_articles(records, mixed_line_issues):
    """Report missing, duplicated and empty Arabic articles."""

    # Extract Civil Code article numbers only.
    civil_numbers = [
        record["number"]
        for record in records
        if record["source"] == "civil_code"
    ]

    expected = set(range(1, 161))

    missing = sorted(expected - set(civil_numbers))

    duplicates = sorted({
        number
        for number in civil_numbers
        if civil_numbers.count(number) > 1
    })

    empty_articles = [
        record["article_id"]
        for record in records
        if not record["text_ar"]
    ]

    article_ids = [record["article_id"] for record in records]

    print("\n" + "=" * 50)
    print("ARABIC ARTICLE PARSING REPORT")
    print("=" * 50)

    print(f"Total records: {len(records)}")
    print(f"Unique article IDs: {len(set(article_ids))}")
    print(f"Missing Civil Code articles: {missing}")
    print(f"Duplicate Civil Code articles: {duplicates}")
    print(f"Empty article texts: {empty_articles}")
    print(f"Mixed-language issues: {len(mixed_line_issues)}")

    # Display unexpected mixed-language lines for review.
    for issue in mixed_line_issues:

        print(
            f"\n{issue['article_id']} | "
            f"Page {issue['page']} | "
            f"{issue['text']}"
        )


# --------------------------------------------------
# 6. Save records as JSONL
# --------------------------------------------------

def save_articles(records):
    """Save one structured Arabic article record per JSONL line."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:

        for record in records:

            json_line = json.dumps(
                record,
                ensure_ascii=False,
            )

            file.write(json_line + "\n")

    print(f"\nSaved records to: {OUTPUT_PATH}")


# --------------------------------------------------
# 7. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    articles, issues = parse_arabic()

    validate_articles(articles, issues)

    save_articles(articles)

    # Inspect Article 20 across the page boundary.
    article_20 = next(
        (
            article for article in articles
            if article["article_id"] == "CC-20"
        ),
        None,
    )

    print("\n" + "=" * 50)
    print("ARTICLE 20")
    print("=" * 50)

    if article_20 is not None:
        print(article_20)

    # Inspect the final article in the subset.
    article_160 = next(
        (
            article for article in articles
            if article["article_id"] == "CC-160"
        ),
        None,
    )

    print("\n" + "=" * 50)
    print("ARTICLE 160")
    print("=" * 50)

    if article_160 is not None:
        print(article_160)