
from pathlib import Path
from pypdf import PdfReader


# --------------------------------------------------
# 1. Project configuration
# --------------------------------------------------

# Find the project root using the script location.
# This avoids depending on the current terminal directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

PDF_PATH = PROJECT_ROOT / "Egyptian Civil Code.pdf"

OUTPUT_DIR = PROJECT_ROOT / "data" / "raw_pages" / "pypdf"


# Create the output directory if it does not exist.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Extract PDF pages
# --------------------------------------------------

def extract_pages(pdf_path):

    # Open the PDF and create a reader object.
    reader = PdfReader(pdf_path)

    # Store extracted text from all pages.
    pages = []

    # Loop through every page in the document.
    for page in reader.pages:

        # Extract the original text without cleaning.
        # Use an empty string if no text is extracted.
        page_text = page.extract_text() or ""

        pages.append(page_text)

    return pages


# --------------------------------------------------
# 3. Save extracted pages
# --------------------------------------------------

def save_pages(pages, output_dir):

    # Save each PDF page as a separate UTF-8 file.
    for page_number, page_text in enumerate(pages, start=1):

        # Preserve PDF page numbers for future citations.
        filename = f"page_{page_number:03d}.txt"

        output_path = output_dir / filename

        # Save the raw text without changing its content.
        output_path.write_text(page_text, encoding="utf-8")

        # Show extraction progress.
        print(
            f"Page {page_number:03d}: "
            f"{len(page_text)} characters"
        )


# --------------------------------------------------
# 4. Run the extraction pipeline
# --------------------------------------------------

if __name__ == "__main__":

    # Extract all pages from the PDF.
    pages = extract_pages(PDF_PATH)

    print(f"Total PDF pages: {len(pages)}")

    # Save all pages to individual text files.
    save_pages(pages, OUTPUT_DIR)

    print("\nFull PDF extraction completed.")