
import fitz  # PyMuPDF


def extract_pdf_text(pdf_bytes: bytes) -> dict:
    """Extract selectable text from a PDF document."""

    try:
        with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
            if document.is_encrypted:
                raise ValueError(
                    "This PDF is password-protected."
                )

            if len(document) == 0:
                raise ValueError("The PDF contains no pages.")

            pages = []
            for page_number, page in enumerate(document, start=1):
                text = page.get_text("text").strip()

                pages.append({
                    "page": page_number,
                    "text": text,
                })

            full_text = "\n\n".join(
                page["text"]
                for page in pages
                if page["text"]
            )

            return {
                "page_count": len(document),
                "extracted_text": full_text,
                "has_text": bool(full_text.strip()),
                "needs_ocr": not bool(full_text.strip()),
            }

    except fitz.FileDataError as exc:
        raise ValueError(
            "The uploaded file is not a valid or readable PDF."
        ) from exc
