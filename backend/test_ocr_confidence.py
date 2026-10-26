
from pathlib import Path

import pymupdf as fitz

from app.ocr_engine import ocr_page, LOW_CONFIDENCE_THRESHOLD


pdf_path = Path("scanned_shipment.pdf")

with fitz.open(pdf_path) as document:
    for page_number, page in enumerate(document, start=1):
        result = ocr_page(page, language="eng")

        confidence = result["ocr_confidence"]
        expected_low = (
            confidence is None
            or confidence < LOW_CONFIDENCE_THRESHOLD
        )

        print(
            f"Page {page_number}: "
            f"confidence={confidence}, "
            f"low_confidence={result['ocr_low_confidence']}, "
            f"expected_low={expected_low}"
        )

        assert result["ocr_low_confidence"] == expected_low

print("\nPASS: Confidence flags match the configured threshold.")
