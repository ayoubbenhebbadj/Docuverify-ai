
import io
from pathlib import Path

import pymupdf as fitz
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from pytesseract import Output

TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
pytesseract.pytesseract.tesseract_cmd = str(TESSERACT_PATH)

PDF_PATH = Path("scanned_shipment.pdf")
PAGE_NUMBER = 2  # Human-readable page number


def recognize(image, label):
    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config="--psm 6",
    )

    data = pytesseract.image_to_data(
        image,
        lang="eng",
        config="--psm 6",
        output_type=Output.DICT,
    )

    confidences = []
    for value in data["conf"]:
        try:
            value = float(value)
            if value >= 0:
                confidences.append(value)
        except (TypeError, ValueError):
            pass

    average = (
        round(sum(confidences) / len(confidences), 2)
        if confidences else None
    )

    print(f"\n--- {label} ---")
    print("Average confidence:", average)
    print(text)


with fitz.open(PDF_PATH) as pdf:
    page = pdf[PAGE_NUMBER - 1]
    pixmap = page.get_pixmap(dpi=400, alpha=False)
    image = Image.open(
        io.BytesIO(pixmap.tobytes("png"))
    ).convert("RGB")

    # Test A: Original image at higher resolution
    recognize(image, "Original 400 DPI")

    # Test B: Grayscale + contrast + sharpening
    processed = image.convert("L")
    processed = ImageEnhance.Contrast(processed).enhance(1.8)
    processed = ImageEnhance.Sharpness(processed).enhance(2.0)
    recognize(processed, "Grayscale + contrast + sharpening")

    # Test C: Thresholded black-and-white image
    thresholded = processed.point(
        lambda pixel: 255 if pixel > 170 else 0
    )
    recognize(thresholded, "Thresholded black and white")
