import logging
import os
import traceback

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.ai_extractor import extract_document_fields
from app.cross_document_validator import validate_cross_documents
from app.document_classifier import classify_document_pages
from app.document_extractor import extract_typed_document
# Two different validators exist; import them under distinct names so the
# second import can no longer silently replace the first.
from app.document_validator import validate_document
from app.pdf_reader import extract_pdf_text
from app.vision_ocr import recover_uncertain_pages
from app.validator import validate_document as validate_invoice_fields

log = logging.getLogger(__name__)

app = FastAPI(
    title="DocuVerify AI API",
    description="API for import/export document verification",
    version="0.2.0",
)

# Allow the local React dev server to call the API.  Extra origins can be
# supplied with CORS_ORIGINS="https://a.example,https://b.example".
_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
_origins += [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def read_uploaded_pdf(file: UploadFile) -> tuple[str, bytes]:
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

    return file.filename, pdf_bytes


def _no_text_response(filename: str, pdf_result: dict) -> dict:
    """Response for PDFs from which no text could be obtained, even by OCR."""
    ocr_attempted = any(p.get("ocr_used") for p in pdf_result["pages"])
    errors = pdf_result.get("ocr_errors") or []

    if errors:
        message = (
            "The PDF has no selectable text and OCR could not run: "
            f"{errors[0]}"
        )
    elif ocr_attempted:
        message = (
            "OCR was attempted but no readable text was recognized. "
            "The scan may be too faint, blurred or low resolution."
        )
    else:
        message = (
            "No selectable text was found. "
            "OCR support is required for this document."
        )

    return {
        "filename": filename,
        "status": "needs_ocr",
        "message": message,
        "page_count": pdf_result["page_count"],
    }


def _handle_unexpected(label: str, exc: Exception) -> HTTPException:
    print(f"\n=== {label} ERROR ===")
    traceback.print_exc()
    print(f"=== END ERROR ===\n")
    return HTTPException(
        status_code=502,
        detail=(
            f"{label.capitalize()} failed. "
            "Check the backend terminal for the underlying error."
        ),
    )


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "DocuVerify AI API",
    }


# NOTE: the endpoints below call blocking code (OCR, network calls to the AI
# provider).  It is run in a worker thread so the event loop stays free and
# /api/health keeps answering while a long analysis is running.

def _extract_text_with_vision(pdf_bytes: bytes) -> dict:
    result = extract_pdf_text(pdf_bytes)
    return recover_uncertain_pages(pdf_bytes, result)


@app.post("/api/documents/extract-text")
async def extract_document(file: UploadFile = File(...)):
    filename, pdf_bytes = await read_uploaded_pdf(file)

    try:
        result = await run_in_threadpool(_extract_text_with_vision, pdf_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "filename": filename,
        **result,
    }


def _analyze_single(filename: str, pdf_bytes: bytes) -> dict:
    pdf_result = extract_pdf_text(pdf_bytes)
    pdf_result = recover_uncertain_pages(pdf_bytes, pdf_result)

    if not pdf_result["has_text"]:
        return _no_text_response(filename, pdf_result)

    extracted_fields = extract_document_fields(pdf_result["extracted_text"])
    validation = validate_invoice_fields(extracted_fields)
    vision_pages = pdf_result.get("pages_vision_ocr_used", [])
    if vision_pages:
        validation["status"] = "needs_review"
        validation.setdefault("warnings", []).append(
            "Vision OCR was used on PDF page(s): "
            f"{', '.join(map(str, vision_pages))}. "
            "Verify extracted values against the original scan."
        )

    return {
        "filename": filename,
        "page_count": pdf_result["page_count"],
        "extracted_fields": extracted_fields,
        "validation": validation,
        "vision_ocr_pages": vision_pages,
    }


@app.post("/api/documents/analyze")
async def analyze_document(file: UploadFile = File(...)):
    filename, pdf_bytes = await read_uploaded_pdf(file)

    try:
        return await run_in_threadpool(_analyze_single, filename, pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise _handle_unexpected("document analysis", exc) from exc


def _analyze_package(filename: str, pdf_bytes: bytes) -> dict:
    # 1. Extract text from every PDF page (OCR for scanned pages).
    pdf_result = extract_pdf_text(pdf_bytes)
    pdf_result = recover_uncertain_pages(pdf_bytes, pdf_result)

    if not pdf_result["has_text"]:
        return _no_text_response(filename, pdf_result)

    pages = pdf_result["pages"]

    # OCR quality summary for the frontend.
    ocr_pages = [p["page"] for p in pages if p.get("ocr_used", False)]
    confidences = [
        p["ocr_confidence"] for p in pages
        if p.get("ocr_used") and p.get("ocr_confidence") is not None
    ]
    pages_low_confidence = pdf_result.get("pages_low_confidence", [])
    pages_needing_ocr = pdf_result.get("pages_needing_ocr", [])
    pages_vision_ocr_used = pdf_result.get("pages_vision_ocr_used", [])

    ocr_summary = {
        "ocr_used": bool(ocr_pages or pages_vision_ocr_used),
        "pages_processed": ocr_pages,
        "pages_vision_ocr_used": pages_vision_ocr_used,
        "vision_ocr_enabled": pdf_result.get("vision_ocr_enabled", False),
        "vision_ocr_model": pdf_result.get("vision_ocr_model"),
        "pages_vision_ocr_attempted": pdf_result.get("pages_vision_ocr_attempted", []),
        "pages_low_confidence": pages_low_confidence,
        "pages_needing_ocr": pages_needing_ocr,
        "average_confidence": (
            round(sum(confidences) / len(confidences), 1)
            if confidences else None
        ),
        "errors": pdf_result.get("ocr_errors", []),
        "vision_errors": {
            str(page.get("page")): page.get("vision_ocr_error")
            for page in pages if page.get("vision_ocr_error")
        },
        "review_required": bool(
            pages_low_confidence or pages_needing_ocr or pages_vision_ocr_used
        ),
    }

    # 2. Classify pages and group them into documents.
    classification = classify_document_pages(pages)

    extracted_documents = []
    document_results = []

    # 3. Extract fields and validate each detected document.
    for document in classification["documents"]:
        document_type = document["document_type"]

        # Pages the classifier could not identify are reported through
        # "unclassified_pages"; there is no schema to extract them with.
        if document_type == "unknown":
            continue

        document_pages = [
            page for page in pages
            if page["page"] in document["pages"]
        ]

        extraction = extract_typed_document(
            document_type=document_type,
            pages=document_pages,
        )

        source_text = "\n".join(
            page["text"] for page in document_pages
        )

        ocr_used = any(p.get("ocr_used") for p in document_pages)

        validation = validate_document(
            extraction,
            source_text,
            ocr_used=ocr_used,
        )

        # Identify OCR pages that need manual review for this document.
        vision_pages = [
            page["page"] for page in document_pages
            if page.get("vision_ocr_used", False)
        ]
        low_confidence_pages = [
            page["page"]
            for page in document_pages
            if page.get("ocr_used", False)
            and page.get("ocr_low_confidence", False)
        ]

        ocr_review_required = bool(low_confidence_pages or vision_pages)

        if ocr_review_required:
            validation["status"] = "needs_review"
            review_pages = sorted(set(low_confidence_pages + vision_pages))
            validation["warnings"].append(
                "OCR/vision transcription requires manual review on PDF page(s): "
                f"{', '.join(map(str, review_pages))}. "
                "Verify extracted information against the original scan."
            )

        extraction["pages"] = document["pages"]
        extracted_documents.append(extraction)

        document_results.append({
            "document_type": document_type,
            "pages": document["pages"],
            "confidence": document.get("confidence"),
            "fields": extraction["fields"],
            "validation": validation,
            "ocr_used": ocr_used,
            "ocr_review_required": ocr_review_required,
            "ocr_pages_low_confidence": low_confidence_pages,
            "vision_ocr_pages": vision_pages,
        })

    # 4. Compare information across documents.
    cross_validation = validate_cross_documents(extracted_documents)

    # 5. Summarize package-level issues.
    missing_documents = classification["missing_documents"]
    unclassified_pages = classification["unclassified_pages"]

    document_validation_issues = [
        result for result in document_results
        if result["validation"].get("status") not in ("passed", "complete")
    ]

    mismatches = cross_validation["summary"]["mismatches"]
    cross_review = cross_validation["summary"]["needs_review"]

    if (
        missing_documents
        or unclassified_pages
        or document_validation_issues
        or mismatches
        or cross_review
        or ocr_summary["review_required"]
    ):
        package_status = "needs_review"
    else:
        package_status = "passed"

    return {
        "filename": filename,
        "status": package_status,
        "page_count": pdf_result["page_count"],
        "documents_found": classification["documents_found"],
        "missing_documents": missing_documents,
        "unclassified_pages": unclassified_pages,
        "documents": document_results,
        "cross_document_validation": cross_validation,
        "ocr_summary": ocr_summary,
    }


@app.post("/api/documents/analyze-package")
async def analyze_package(file: UploadFile = File(...)):
    filename, pdf_bytes = await read_uploaded_pdf(file)

    try:
        return await run_in_threadpool(_analyze_package, filename, pdf_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise _handle_unexpected("package analysis", exc) from exc


def _classify(pdf_bytes: bytes, filename: str) -> dict:
    pdf_data = extract_pdf_text(pdf_bytes)
    pdf_data = recover_uncertain_pages(pdf_bytes, pdf_data)

    # Only give up when no page yielded any text; a few unreadable pages are
    # classified as "unknown" instead of blocking the whole file.
    if not pdf_data["has_text"]:
        response = _no_text_response(filename, pdf_data)
        response["message"] += " OCR is required before classification."
        return response

    result = classify_document_pages(pdf_data["pages"])

    return {
        "filename": filename,
        "status": (
            "needs_review"
            if result["missing_documents"] or result["unclassified_pages"]
            else "classified"
        ),
        **result,
    }


@app.post("/api/documents/classify")
async def classify_documents(file: UploadFile = File(...)):
    filename, pdf_bytes = await read_uploaded_pdf(file)

    try:
        return await run_in_threadpool(_classify, pdf_bytes, filename)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise _handle_unexpected("document classification", exc) from exc
