
import io
from pathlib import Path
from statistics import mean

import pymupdf as fitz
import pytesseract
from PIL import Image
from pytesseract import Output


TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)

# Tune this threshold after testing more scanned documents.
LOW_CONFIDENCE_THRESHOLD = 75.0


def ocr_page(page: fitz.Page, language: str = "eng") -> dict:
    """OCR one PDF page and report word-level confidence."""

    if not TESSERACT_PATH.exists():
        raise RuntimeError(
            f"Tesseract executable not found: {TESSERACT_PATH}"
        )

    # Render at 300 DPI for recognition.
    pixmap = page.get_pixmap(dpi=400, alpha=False)
    image_bytes = pixmap.tobytes("png")

    with Image.open(io.BytesIO(image_bytes)) as image:
        # Collect recognized text and confidence values.
        data = pytesseract.image_to_data(
            image,
            lang=language,
            config="--psm 3",
            output_type=Output.DICT,
        )

    recognized_words = []
    word_confidences = []

    for word, raw_confidence in zip(
        data["text"], data["conf"]
    ):
        word = word.strip()

        try:
            confidence = float(raw_confidence)
        except (TypeError, ValueError):
            continue

        # Tesseract uses negative confidence for non-word entries.
        if word and confidence >= 0:
            recognized_words.append(word)
            word_confidences.append(confidence)

    text = " ".join(recognized_words)

    average_confidence = (
        round(mean(word_confidences), 2)
        if word_confidences
        else None
    )

    low_confidence = (
        average_confidence is None
        or average_confidence < LOW_CONFIDENCE_THRESHOLD
    )

    return {
        "text": text,
        "ocr_used": True,
        "ocr_confidence": average_confidence,
        "ocr_word_count": len(recognized_words),
        "ocr_low_confidence": low_confidence,
    }
