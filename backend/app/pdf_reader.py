
import pymupdf as fitz

from app.ocr_engine import ocr_page

def page_needs_ocr(page: fitz.Page, text: str) -> bool:
    """Identify pages likely to need OCR, including partial-text scans."""

    if not text.strip():
        return True

    # A small amount of selectable text may just be a page number/footer.
    if len(text.strip()) < 80:
        page_area = max(page.rect.width * page.rect.height, 1)

        for image in page.get_images(full=True):
            xref = image[0]

            for rect in page.get_image_rects(xref):
                image_area = rect.width * rect.height

                if image_area / page_area >= 0.25:
                    return True

    return False

def extract_pdf_text(pdf_bytes: bytes) -> dict:
    """Extract native PDF text and OCR pages without selectable text."""

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            if document.is_encrypted:
                raise ValueError("This PDF is password-protected.")

            if len(document) == 0:
                raise ValueError("The PDF contains no pages.")

            pages = []

            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()

                page_result = {
                    "page": page_number,
                    "text": text,
                    "ocr_used": False,
                    "ocr_confidence": None,
                    "ocr_word_count": 0,
                    "ocr_low_confidence": False,
                    "needs_ocr": not bool(text),
                }

                if page_needs_ocr(page, text):
                    ocr_result = ocr_page(page, language="eng")
                    text = ocr_result["text"]

                    page_result.update(ocr_result)
                    page_result["page"] = page_number
                    page_result["text"] = text
                    page_result["needs_ocr"] = not bool(text)

                pages.append(page_result)

            full_text = "\n\n".join(
                page["text"]
                for page in pages
                if page["text"]
            )

            pages_needing_ocr = [
                page["page"]
                for page in pages
                if page["needs_ocr"]
            ]

            pages_low_confidence = [
                page["page"]
                for page in pages
                if page["ocr_used"] and page["ocr_low_confidence"]
            ]

            return {
                "page_count": len(document),
                "pages": pages,
                "extracted_text": full_text,
                "has_text": bool(full_text),
                "needs_ocr": bool(pages_needing_ocr),
                "pages_needing_ocr": pages_needing_ocr,
                "pages_low_confidence": pages_low_confidence,
            }

    except fitz.FileDataError as exc:
        raise ValueError(
            "The uploaded file is not a valid or readable PDF."
        ) from exc

