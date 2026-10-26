
from pathlib import Path

import pymupdf as fitz

from app.ocr_engine import ocr_page


pdf_path = Path("scanned_shipment.pdf")

with fitz.open(pdf_path) as document:
    print("Pages:", len(document))

    for page_number, page in enumerate(document, start=1):
        result = ocr_page(page, language="eng")

        print(f"\n--- Page {page_number} ---")
        print("Words recognized:", result["ocr_word_count"])
        print("Average confidence:", result["ocr_confidence"])
        print("Low confidence:", result["ocr_low_confidence"])
        print("Text preview:", result["text"][:500])

        assert result["ocr_used"] is True

print("\nPASS: OCR confidence scoring completed.")
