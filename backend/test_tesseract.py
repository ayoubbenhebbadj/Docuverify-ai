import pymupdf as fitz
import pytesseract
from PIL import Image
from pytesseract import Output
from pathlib import Path
import time
import io

# Folder containing scanned PDFs
PDF_PATH = Path(
    r"C:\Users\QUBIX TECH\Desktop\docuverify-repo\backend\Commercial Invoice (Scanned).pdf"
)

# OCR languages installed on your machine
LANGUAGES = "eng"

# Rendering resolution
DPI = 250

def test_pdf(pdf_path):
    print("\n" + "=" * 70)
    print(f"FILE: {pdf_path.name}")
    print("=" * 70)

    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc):
        start = time.time()

        # Render PDF page as an image
        pix = page.get_pixmap(
            dpi=DPI,
            colorspace=fitz.csRGB,
            alpha=False
        )

        image = Image.open(
            io.BytesIO(pix.tobytes("png"))
        )

        # Run Tesseract
        data = pytesseract.image_to_data(
            image,
            lang=LANGUAGES,
            config="--oem 3 --psm 4",
            output_type=Output.DICT
        )

        # Extract recognized words
        words = []
        confidences = []

        for word, confidence in zip(
            data["text"], data["conf"]
        ):
            word = word.strip()

            try:
                confidence = float(confidence)
            except ValueError:
                continue

            if word and confidence >= 0:
                words.append(word)
                confidences.append(confidence)

        elapsed = time.time() - start

        average_confidence = (
            sum(confidences) / len(confidences)
            if confidences else 0
        )

        extracted_text = " ".join(words)

        print(f"\nPAGE {page_index + 1}")
        print(f"Words recognized: {len(words)}")
        print(f"Average confidence: {average_confidence:.2f}%")
        print(f"Processing time: {elapsed:.2f} seconds")

        print("\nEXTRACTED TEXT:")
        print(extracted_text[:3000])

        # Save OCR output
        output_file = pdf_path.with_name(
            f"{pdf_path.stem}_page_{page_index + 1}.txt"
        )

        output_file.write_text(
            extracted_text,
            encoding="utf-8"
        )

    doc.close()


def main():
    if not PDF_PATH.exists():
        print(f"PDF not found: {PDF_PATH}")
        return

    print(f"Testing: {PDF_PATH.name}")
    print(f"OCR languages: {LANGUAGES}")
    print(f"Rendering DPI: {DPI}")

    test_pdf(PDF_PATH)


if __name__ == "__main__":
    main()