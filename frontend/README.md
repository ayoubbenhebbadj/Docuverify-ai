# DocuVerify AI frontend

## Run locally (Windows)
Backend (from `backend`, with the existing virtual environment):

    .venv\Scripts\activate
    uvicorn app.main:app --reload --port 8000

Frontend (from the project root):

    copy .env.example .env      (skip if you already have a .env with VITE_API_BASE_URL)
    npm install
    npm run dev                 -> http://localhost:5173

Open it on `localhost:5173` or `127.0.0.1:5173`: the backend's CORS policy allows only those two origins.
Checks: `npm run typecheck`, `npm run build`.

## OCR setup
Scanned pages are read automatically by Tesseract (`backend/app/ocr_engine.py`).

1. Install Tesseract (Windows: https://github.com/UB-Mannheim/tesseract/wiki, tick the **French** language
   data if your documents are bilingual; Linux: `apt install tesseract-ocr tesseract-ocr-fra`).
2. `pip install -r backend/requirements.txt`
3. Optional environment variables (backend `.env`): `TESSERACT_CMD` (full path if it is not on PATH),
   `OCR_LANGUAGES` (e.g. `eng+fra`; French is used automatically when installed),
   `OCR_LOW_CONFIDENCE_THRESHOLD` (default 75), `OCR_THOROUGH=1` (always run every pass: slower, finds more).

## Manual test checklist
1. Success path: upload `merged files.pdf` -> results page appears with the real response.
2. Missing documents: upload a PDF that lacks some of the 8 types -> red "Missing" rows, status is never green.
3. Validation warnings: open "View fields" on a flagged document -> missing/invalid/unsupported-evidence lists show.
4. Mismatches: look for red rows in Cross-document validation with the conflicting values.
5. OCR: upload `scanned_shipment.pdf` -> results appear with an "OCR" panel and badges; pages with low confidence are flagged for review. If Tesseract is missing you get a "Needs OCR" panel explaining why.
6. Client validation: pick a .docx, an empty file, a file over 10 MB -> inline error, no request sent.
7. Connection failure: stop the backend, press Analyze -> connection message with Retry; Overview shows "Cannot reach".
8. Server errors: unplug the AI key or exhaust credit -> HTTP 502 message with guidance.
9. Print: "Print report" expands every document panel and hides navigation.

### Optional OpenRouter vision OCR fallback

DocuVerify can optionally send uncertain scanned pages to a vision-capable OpenRouter model. It reuses `OPENROUTER_API_KEY`; it does **not** require a second key. Vision is disabled unless `OPENROUTER_VISION_MODEL` is set.

Add these settings to `backend/.env` (keep the real key private):

```env
OPENROUTER_API_KEY=your_existing_key
OPENROUTER_MODEL=your_existing_text_model
OPENROUTER_VISION_MODEL=nvidia/nemotron-3.5-super-vl:free
# Optional tuning:
VISION_OCR_DPI=180
VISION_OCR_MAX_IMAGE_SIDE=2200
VISION_OCR_MAX_TOKENS=5000
```

Choose a model ID that currently supports image input on OpenRouter; free model availability and limits can change. When enabled, the fallback runs only for pages that need OCR, have no usable text, or are flagged as low-confidence by Tesseract. The vision transcription replaces the uncertain page text for downstream classification and extraction, and the response flags those pages for manual review. Provider failures do not stop processing; the original OCR result remains available. Test on non-sensitive sample documents before using real customer paperwork, and review provider data-handling terms.


## Vision OCR fallback and cross-document checks

The backend can use the same `OPENROUTER_API_KEY` for optional vision OCR. Set
`OPENROUTER_VISION_MODEL` in `backend/.env` to an OpenRouter model that accepts
image input. The fallback is attempted for pages with missing/low-confidence
OCR and pages that appear to have a broken Arabic text layer over a page image.
Package analysis reports `ocr_summary.vision_ocr_enabled`,
`ocr_summary.vision_ocr_model`, `pages_vision_ocr_attempted`,
`pages_vision_ocr_used`, and `vision_errors` so you can confirm whether it ran.
Vision-transcribed pages always require human review.

Cross-document validation now compares weights and package counts across the
packing list and supporting certificates when those fields are extracted. It
normalizes the common `(FOR EXPORT)` suffix and includes cautious Arabic/Latin
company-name comparison. Invoice arithmetic can validate the total using the
sum of extracted line-item amounts when the invoice has no printed subtotal.

Focused regression tests:

```powershell
cd backend
python -m pytest -q test_cross_document_validator.py test_cross_document_validator_improvements.py test_vision_ocr.py
```
