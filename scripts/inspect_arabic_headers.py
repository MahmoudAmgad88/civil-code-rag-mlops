
"""Inspect Arabic article headers before building the Arabic parser."""

import re
from pathlib import Path


# 1. Define the project paths.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw_pages" / "pypdf"


# 2. Detect lines containing the Arabic article keyword.
# This is an inspection pattern, not the final article parser.
ARABIC_HEADER_CANDIDATE = re.compile(r"مادة")


def inspect_headers(first_page=1, last_page=18):
    """Print possible Arabic headers with their page and line numbers."""

    # Process pages in their original order.
    for page_number in range(first_page, last_page + 1):

        page_path = RAW_DIR / f"page_{page_number:03d}.txt"

        page_text = page_path.read_text(encoding="utf-8")

        # Inspect every extracted line.
        for line_number, line in enumerate(
            page_text.splitlines(),
            start=1,
        ):

            if ARABIC_HEADER_CANDIDATE.search(line):

                print(
                    f"Page {page_number:03d} | "
                    f"Line {line_number:03d} | "
                    f"{line.strip()}"
                )


if __name__ == "__main__":
    inspect_headers()