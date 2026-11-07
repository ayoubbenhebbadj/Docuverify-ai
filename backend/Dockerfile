# Backend image for Render (FastAPI + Tesseract OCR).
FROM python:3.11-slim

# Tesseract binary + libs needed by OpenCV. Language data (Arabic/French/English)
# comes from backend/tessdata, so no language packs are installed from apt.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tessdata ./tessdata

ENV PYTHONUNBUFFERED=1
# Render injects $PORT (default 10000).
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
