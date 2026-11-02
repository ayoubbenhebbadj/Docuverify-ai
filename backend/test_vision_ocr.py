from dotenv import load_dotenv
load_dotenv()  # <--- This must run first!

import json
import logging
from pathlib import Path

from app.vision_ocr import vision_transcribe_page

logging.basicConfig(level=logging.INFO)

pdf_path = Path(r"ilovepdf_merged.pdf")
pdf_bytes = pdf_path.read_bytes()

text = vision_transcribe_page(pdf_bytes, 2)

print("\n===== VISION OCR OUTPUT =====\n")
print(text)