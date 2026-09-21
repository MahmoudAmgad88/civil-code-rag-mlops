
"""Detect and validate Arabic article numbers from raw PDF pages."""

import re
from pathlib import Path


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw_pages" / "pypdf"


# --------------------------------------------------
# 2. Arabic article header detection
# --------------------------------------------------

# Match complete Arabic article headers.
# Allow parentheses, spaces, and an optional English
# header on the same line, as in Article 83.

ARABIC_HEADER = re.compile(
    r"^\s*مادة\s*[\(\)]*\s*"
    r"([٠-٩]+)"
    r"\s*[\(\)]*\s*"
    r"(?:Article\s+\d+)?\s*$",
    re.IGNORECASE,
)


# --------------------------------------------------
# 3. Arabic digit conversion
# --------------------------------------------------

def arabic_header_to_int(arabic_digits):
    """Convert reversed Arabic header digits to an article number."""

    # Reverse the digit order found in this PDF extraction.
    corrected_digits = arabic_digits[::-1]

    # Convert Arabic-Indic digits into Western digits.
    digit_map = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩",
        "0123456789",
    )

    western_digits = corrected_digits.translate(digit_map)

    return int(western_digits)


# --------------------------------------------------
# 4. Inspect article numbers
# --------------------------------------------------

def check_headers(first_page=1, last_page=18):
    """Print article numbers detected in the selected PDF pages."""

    detected_numbers = []

    for page_number in range(first_page, last_page + 1):

        page_path = RAW_DIR / f"page_{page_number:03d}.txt"

        page_text = page_path.read_text(encoding="utf-8")

        for line in page_text.splitlines():

            # Match only complete Arabic article headers.
            match = ARABIC_HEADER.fullmatch(line.strip())

            if not match:
                continue

            # Extract and convert the article number.
            article_number = arabic_header_to_int(
                match.group(1)
            )

            detected_numbers.append(article_number)

            print(
                f"Page {page_number:03d} | "
                f"Article {article_number}"
            )

    return detected_numbers


# --------------------------------------------------
# 5. Main execution
# --------------------------------------------------

if __name__ == "__main__":

    numbers = check_headers()

    print("\nTotal detected headers:", len(numbers))

    print("First 10 article numbers:", numbers[:10])

    print("Last 10 article numbers:", numbers[-10:])