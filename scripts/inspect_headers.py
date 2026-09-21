
import re
from pathlib import Path


# Locate the project root and the extracted PDF pages.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw_pages" / "pypdf"


# Match lines containing the English word "Article",
# followed by optional spaces and an article number.
HEADER_PATTERN = re.compile(r"\bArticle\s+\d+\b", re.IGNORECASE)


# Inspect the first 18 PDF pages.
for page_number in range(1, 19):

    page_path = RAW_DIR / f"page_{page_number:03d}.txt"

    # Read the raw text without modifying it.
    page_text = page_path.read_text(encoding="utf-8")

    # Inspect each line independently.
    for line_number, line in enumerate(page_text.splitlines(), start=1):

        # Print lines matching the expected header format.
        if HEADER_PATTERN.search(line):

            print(
                f"Page {page_number:03d} | "
                f"Line {line_number:03d} | "
                f"{line.strip()}"
            )



# --------------------------------------------------
# Check article header coverage
# --------------------------------------------------

# Store all article numbers detected by the regex.
found_articles = []


# Search the first 18 pages again.
for page_number in range(1, 19):

    page_path = RAW_DIR / f"page_{page_number:03d}.txt"
    page_text = page_path.read_text(encoding="utf-8")

    for line in page_text.splitlines():

        # Find every article header matching the current pattern.
        matches = HEADER_PATTERN.findall(line)

        for match in matches:

            # Extract the number from "Article N".
            article_number = int(match.split()[-1])

            # Keep only articles in our initial subset.
            if 1 <= article_number <= 160:
                found_articles.append(article_number)


# Compare detected articles against the expected range.
expected_articles = set(range(1, 161))
detected_articles = set(found_articles)

missing_articles = sorted(expected_articles - detected_articles)


print("\n" + "=" * 50)
print("ENGLISH ARTICLE HEADER VALIDATION")
print("=" * 50)

print(f"Expected article numbers: {len(expected_articles)}")
print(f"Detected unique numbers: {len(detected_articles)}")
print(f"Missing article numbers: {missing_articles}")