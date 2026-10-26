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

## Manual test checklist
1. Success path: upload `merged files.pdf` -> results page appears with the real response.
2. Missing documents: upload a PDF that lacks some of the 8 types -> red "Missing" rows, status is never green.
3. Validation warnings: open "View fields" on a flagged document -> missing/invalid/unsupported-evidence lists show.
4. Mismatches: look for red rows in Cross-document validation with the conflicting values.
5. OCR: upload `scanned_bill_of_lading.pdf` -> "Needs OCR" panel, no checklist.
6. Client validation: pick a .docx, an empty file, a file over 10 MB -> inline error, no request sent.
7. Connection failure: stop the backend, press Analyze -> connection message with Retry; Overview shows "Cannot reach".
8. Server errors: unplug the AI key or exhaust credit -> HTTP 502 message with guidance.
9. Print: "Print report" expands every document panel and hides navigation.
