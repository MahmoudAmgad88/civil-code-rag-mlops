
from pathlib import Path


# Locate the project root independently of the terminal directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw_pages"


# Define the extraction methods we want to compare.
METHODS = ["pymupdf", "pypdf"]


# Read the first page extracted by each library.
for method in METHODS:

    file_path = RAW_DIR / method / "page_001.txt"

    # Read the original extracted text without modifying it.
    text = file_path.read_text(encoding="utf-8")

    print("\n" + "=" * 60)
    print(f"Extraction method: {method}")
    print(f"Total characters: {len(text)}")
    print("=" * 60)

    # Display the first 1200 characters for manual inspection.
    print(text[:1200])