from app.ai_extractor import extract_document_fields
from app.validator import validate_document

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.pdf_reader import extract_pdf_text

app = FastAPI(
    title="DocuVerify AI API",
    description="API for import/export document verification",
    version="0.1.0",
)

# Allow the local React development server to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@app.get("/api/health")

def health_check():
    return {
        "status": "ok",
        "service": "DocuVerify AI API",
    }


@app.post("/api/documents/extract-text")
async def extract_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file.",
        )

    pdf_bytes = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The PDF exceeds the 10 MB upload limit.",
        )

    # Check the PDF signature instead of trusting the filename alone.
    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The file does not appear to be a valid PDF.",
        )

    try:
        result = extract_pdf_text(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "filename": file.filename,
        **result,
    }
#analyse happens here
@app.post("/api/documents/analyze")
async def analyze_document(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF file.",
        )

    pdf_bytes = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not pdf_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The PDF exceeds the 10 MB upload limit.",
        )

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="The file does not appear to be a valid PDF.",
        )

    try:
        pdf_result = extract_pdf_text(pdf_bytes)

        if not pdf_result["has_text"]:
            return {
                "filename": file.filename,
                "status": "needs_ocr",
                "message": (
                    "No selectable text was found. "
                    "OCR support is required for this document."
                ),
                "page_count": pdf_result["page_count"],
            }

        extracted_fields = extract_document_fields(
            pdf_result["extracted_text"]
        )

        validation = validate_document(extracted_fields)

        return {
            "filename": file.filename,
            "page_count": pdf_result["page_count"],
            "extracted_fields": extracted_fields,
            "validation": validation,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception:
        # Avoid exposing API keys, provider responses, or internal
        # exception details to the client.
        raise HTTPException(
            status_code=502,
            detail=(
                "Document analysis failed. "
                "Check the backend terminal for the underlying error."
            ),
        )
