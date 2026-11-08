import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pymupdf as fitz

from app.ocr_engine import _page_image, ocr_image

log = logging.getLogger(__name__)


def _ocr_workers() -> int:
    """Return a safe OCR worker count from OCR_WORKERS."""
    try:
        return max(1, int(os.getenv("OCR_WORKERS", "4")))
    except (TypeError, ValueError):
        return 1


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


_ARABIC_GAP_RE = re.compile(r"[\u0600-\u06ff]\s+[\u0600-\u06ff]")
_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")


def has_broken_arabic_layer(text: str) -> bool:
    """True when the embedded text layer holds mangled Arabic.

    Word/PDF exports with a bad Unicode map give Arabic letters separated by
    spaces, dropped letters and reversed fragments.  The text looks present but
    is unusable, so the page must be OCR'd from its picture instead.
    """
    arabic = len(_ARABIC_RE.findall(text))
    if arabic < 20:
        return False
    gaps = len(_ARABIC_GAP_RE.findall(text))
    # Arabic words average ~4-5 letters; a healthy layer has far fewer
    # letter-gap-letter hits than letters.  Also flag very short Arabic "words".
    words = [w for w in re.split(r"\s+", text) if _ARABIC_RE.search(w)]
    short = sum(1 for w in words if len(w) <= 2)
    return gaps >= 8 or (words and short / len(words) > 0.45)


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

    if has_broken_arabic_layer(stripped):
        return True

    coverage = _image_coverage(page)

    # A little selectable text (page number, footer, Bates stamp) on top of a
    # page-sized image is a scan with a stray text layer.
    if len(stripped) < 80 and coverage >= 0.25:
        return True
    if len(stripped) < 400 and coverage >= 0.6:
        return True

    return False


def _merge_native_text(native: str, ocr_text: str, latin_only: bool = False) -> str:
    """Keep native text lines that OCR did not reproduce (e.g. a footer)."""

    def norm(value: str) -> str:
        return re.sub(r"[\W_]+", "", value).casefold()

    ocr_norm = norm(ocr_text)
    extra = [
        line.strip()
        for line in native.splitlines()
        if len(norm(line)) >= 4 and norm(line) not in ocr_norm
        and not (latin_only and _ARABIC_RE.search(line))
    ]

    if not extra:
        return ocr_text
    return "\n".join([ocr_text, *extra]).strip()


def extract_pdf_text(pdf_bytes: bytes) -> dict:
    """Extract native PDF text and OCR pages without selectable text."""

    extraction_started = time.perf_counter()
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

            # Render page pixels before launching workers: PyMuPDF page objects
            # stay on this thread, while independent Tesseract jobs run in parallel.
            ocr_inputs = {}
            for page_number, page in enumerate(document, start=1):
                native = page.get_text("text").strip()
                if page_needs_ocr(page, native):
                    try:
                        ocr_inputs[page_number] = _page_image(page)
                    except Exception as exc:
                        ocr_errors.append(f"page {page_number}: {exc}")

            ocr_results = {}
            if ocr_inputs:
                with ThreadPoolExecutor(max_workers=min(_ocr_workers(), len(ocr_inputs))) as pool:
                    futures = {
                        pool.submit(ocr_image, image, dpi): page_number
                        for page_number, (image, dpi) in ocr_inputs.items()
                    }
                    for future in as_completed(futures):
                        page_number = futures[future]
                        try:
                            ocr_results[page_number] = future.result()
                        except Exception as exc:
                            ocr_results[page_number] = exc

            for page_number, page in enumerate(document, start=1):
                native_text = page.get_text("text").strip()

                needs_ocr = page_needs_ocr(page, native_text)
                
                page_result = {
                    "page": page_number,

                    # Keep the original PDF text unchanged.
                    "native_text": native_text,

                    # Keep OCR and vision results as separate sources.
                    "ocr_text": "",
                    "vision_text": "",

                    # Existing primary text field for compatibility.
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
                    page_ocr_started = time.perf_counter()
                    try:
                        precomputed = ocr_results.get(page_number)
                        if isinstance(precomputed, Exception):
                            raise precomputed
                        ocr_result = precomputed or {
                            "text": "", "ocr_used": True, "ocr_confidence": None,
                            "ocr_word_count": 0, "ocr_low_confidence": False,
                            "ocr_sparse": True, "ocr_blank": True, "ocr_details": {},
                        }
                    except Exception as exc:  # keep processing other pages
                        log.exception("OCR failed on page %s", page_number)
                        log.info("[TIMING] Tesseract page %s FAILED after %.2f s", page_number, time.perf_counter() - page_ocr_started)
                        ocr_errors.append(f"page {page_number}: {exc}")
                        page_result["ocr_error"] = str(exc)
                    else:
                        # Preserve the original Tesseract result before merging anything.
                        ocr_text = ocr_result.get("text", "")

                        page_result["ocr_text"] = ocr_text

                        broken_layer = has_broken_arabic_layer(native_text)
                        page_result["broken_arabic_text_layer"] = broken_layer

                        text = ocr_text
                        # Arabic in a broken layer is garbage, but its Latin lines
                        # (company names, e-mails, numbers) are exact: keep only those.
                        if native_text:
                            text = _merge_native_text(native_text, text, latin_only=broken_layer)

                        # Keep the PDF's own first lines: a clean title there helps classification.
                        page_result.update(ocr_result)

                        # Restore source-specific values after update(), because OCR results
                        # also contain a "text" field.
                        page_result["page"] = page_number
                        page_result["native_text"] = native_text
                        page_result["native_title_text"] = native_text[:2000]
                        page_result["ocr_text"] = ocr_text
                        page_result["text"] = text
                        # A truly blank page is not an OCR failure and should
                        # not be sent for another OCR attempt.
                        page_result["needs_ocr"] = (
                            not bool(text.strip())
                            and not bool(ocr_result.get("ocr_blank", False))
                        )
                        log.info(
                            "[TIMING] Tesseract page %s: %.2f s | confidence=%s | words=%s | passes=%s",
                            page_number, time.perf_counter() - page_ocr_started,
                            page_result.get("ocr_confidence"), page_result.get("ocr_word_count"),
                            ",".join((page_result.get("ocr_details") or {}).get("passes", [])),
                        )

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

            pages_sparse = [
                page["page"]
                for page in pages
                if page.get("ocr_sparse", False)
            ]

            log.info("[TIMING] PDF text extraction + Tesseract total: %.2f s | pages=%s | OCR pages=%s", time.perf_counter() - extraction_started, len(document), sum(bool(p.get("ocr_used")) for p in pages))
            return {
                "page_count": len(document),
                "pages": pages,
                "extracted_text": full_text,
                "has_text": bool(full_text.strip()),
                "needs_ocr": bool(pages_needing_ocr),
                "pages_needing_ocr": pages_needing_ocr,
                "pages_low_confidence": pages_low_confidence,
                "pages_sparse": pages_sparse,
                "ocr_errors": ocr_errors,
            }

    except fitz.FileDataError as exc:
        raise ValueError(
            "The uploaded file is not a valid or readable PDF."
        ) from exc
