
from pathlib import Path
import pymupdf


# --------------------------------------------------
# 1. Define Project Paths
# --------------------------------------------------

# Define project paths based on this script's location.
# This allows the script to run from any working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_PATH = PROJECT_ROOT / "Egyptian Civil Code.pdf"

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw_pages" / "pymupdf"


# --------------------------------------------------
# 2. Prepare Output Directory
# --------------------------------------------------

# Check that the source PDF exists before processing.
if not PDF_PATH.is_file():
    raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

# Create the output directory if it does not exist.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 3. Open PDF and Extract Text
# --------------------------------------------------

# Automatically close the PDF after extraction.
with pymupdf.open(PDF_PATH) as doc:

    print(f"Total PDF pages: {len(doc)}")

    # Extract text from the first three pages.
    # Avoid accessing pages beyond the document length.
    for page_index in range(min(3, len(doc))):

        # Select the current PDF page.
        page = doc[page_index]

        # Extract raw text without normalization or cleaning.
        page_text = page.get_text()

        # Preserve the original page number in the filename.
        page_number = page_index + 1
        output_path = OUTPUT_DIR / f"page_{page_number:03d}.txt"

        # Save the extracted text using UTF-8 encoding.
        output_path.write_text(page_text, encoding="utf-8")

        print(
            f"Page {page_number}: "
            f"{len(page_text)} characters -> {output_path.name}"
        )


print("PyMuPDF extraction completed.")