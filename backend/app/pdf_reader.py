import logging
import re

import pymupdf as fitz

from app.ocr_engine import ocr_page

log = logging.getLogger(__name__)


def _image_coverage(page: fitz.Page) -> float:
    """Largest fraction of the page area covered by a single image."""
    page_area = max(page.rect.width * page.rect.height, 1)
    best = 0.0

    for image in page.get_images(full=True):
        try:
            rects = page.get_image_rects(image[0])
        except Exception:
            continue
        for rect in rects:
            best = max(best, (rect.width * rect.height) / page_area)

    return best


def page_needs_ocr(page: fitz.Page, text: str) -> bool:
    """Identify pages likely to need OCR, including partial-text scans."""

    stripped = text.strip()

    if not stripped:
        # Truly blank pages (no text, images or drawings) do not need OCR.
        try:
            if not page.get_images() and not page.get_drawings():
                return False
        except Exception:
            pass
        return True

    coverage = _image_coverage(page)

    # A little selectable text (page number, footer, Bates stamp) on top of a
    # page-sized image is a scan with a stray text layer.
    if len(stripped) < 80 and coverage >= 0.25:
        return True
    if len(stripped) < 400 and coverage >= 0.6:
        return True

    return False


def _merge_native_text(native: str, ocr_text: str) -> str:
    """Keep native text lines that OCR did not reproduce (e.g. a footer)."""

    def norm(value: str) -> str:
        return re.sub(r"[\W_]+", "", value).casefold()

    ocr_norm = norm(ocr_text)
    extra = [
        line.strip()
        for line in native.splitlines()
        if len(norm(line)) >= 4 and norm(line) not in ocr_norm
    ]

    if not extra:
        return ocr_text
    return "\n".join([ocr_text, *extra]).strip()


def extract_pdf_text(pdf_bytes: bytes) -> dict:
    """Extract native PDF text and OCR pages without selectable text."""

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            # needs_pass is only True when a password is really required;
            # is_encrypted is also True for harmless permission-only PDFs.
            if document.needs_pass:
                raise ValueError("This PDF is password-protected.")

            if len(document) == 0:
                raise ValueError("The PDF contains no pages.")

            pages = []
            ocr_errors = []

            for page_number, page in enumerate(document, start=1):
                native_text = page.get_text("text").strip()

                needs_ocr = page_needs_ocr(page, native_text)
                page_result = {
                    "page": page_number,
                    "text": native_text,
                    "ocr_used": False,
                    "ocr_confidence": None,
                    "ocr_word_count": 0,
                    "ocr_low_confidence": False,
                    "needs_ocr": needs_ocr,
                    "image_coverage": round(_image_coverage(page), 3),
                    "native_text_length": len(native_text),
                }

                if needs_ocr:
                    try:
                        ocr_result = ocr_page(page)
                    except Exception as exc:  # keep processing other pages
                        log.exception("OCR failed on page %s", page_number)
                        ocr_errors.append(f"page {page_number}: {exc}")
                        page_result["ocr_error"] = str(exc)
                    else:
                        text = ocr_result["text"]
                        if native_text:
                            text = _merge_native_text(native_text, text)

                        page_result.update(ocr_result)
                        page_result["page"] = page_number
                        page_result["text"] = text
                        page_result["needs_ocr"] = not bool(text.strip())

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
                "has_text": bool(full_text.strip()),
                "needs_ocr": bool(pages_needing_ocr),
                "pages_needing_ocr": pages_needing_ocr,
                "pages_low_confidence": pages_low_confidence,
                "ocr_errors": ocr_errors,
            }

    except fitz.FileDataError as exc:
        raise ValueError(
            "The uploaded file is not a valid or readable PDF."
        ) from exc
