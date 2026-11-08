import logging
import os
import traceback
import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware

from app.ai_extractor import extract_document_fields
from app.cross_document_validator import validate_cross_documents
from app.document_classifier import classify_document_pages
from app.document_extractor import extract_typed_document
# Two different validators exist; import them under distinct names so the
# second import can no longer silently replace the first.
from app.evidence import build_evidence
from app.document_validator import validate_document
from app.pdf_reader import extract_pdf_text
from app.vision_ocr import recover_uncertain_pages
from app.validator import validate_document as validate_invoice_fields

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(
    title="DocuVerify AI API",
    description="API for import/export document verification",
    version="0.2.0",
)

# Allow the local React dev server to call the API.  Extra origins can be
# supplied with CORS_ORIGINS="https://a.example,https://b.example".
_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://docuverify-frontend.vercel.app",
]
_origins += [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _language_warnings() -> list[str]:
    try:
        from app.ocr_engine import missing_recommended_languages
        return missing_recommended_languages()
    except Exception:  # Tesseract missing: reported elsewhere
        return []


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


def _combined_page_source(page: dict) -> str:
    """Build a labelled, non-destructive text source for one PDF page."""

    page_number = page.get("page", "?")

    native_text = str(
        page.get("native_text")
        or page.get("native_title_text")
        or ""
    ).strip()

    ocr_text = str(page.get("ocr_text") or "").strip()
    vision_text = str(page.get("vision_text") or "").strip()

    # Compatibility with existing page dictionaries.
    if not native_text and not ocr_text and not vision_text:
        ocr_text = str(page.get("text") or "").strip()

    sections = [f"--- PDF PAGE {page_number} ---"]

    if native_text:
        sections.append(
            "[ORIGINAL PDF TEXT LAYER]\n" + native_text
        )

    if ocr_text:
        sections.append(
            "[TESSERACT OCR]\n" + ocr_text
        )

    if vision_text:
        sections.append(
            "[VISION OCR]\n" + vision_text
        )

    if len(sections) == 1:
        sections.append("[NO READABLE TEXT]")

    return "\n\n".join(sections)


def _analyze_package(filename: str, pdf_bytes: bytes) -> dict:
    package_started = time.perf_counter()
    log.info("[TIMING] ===== PACKAGE ANALYSIS START: %s =====", filename)

    # 1. Extract text from every PDF page (OCR for scanned pages).
    stage_started = time.perf_counter()
    pdf_result = extract_pdf_text(pdf_bytes)
    log.info("[TIMING] Stage PDF extraction/Tesseract: %.2f s", time.perf_counter() - stage_started)
    stage_started = time.perf_counter()
    pdf_result = recover_uncertain_pages(pdf_bytes, pdf_result)
    log.info("[TIMING] Stage Vision fallback: %.2f s", time.perf_counter() - stage_started)

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
        "pages_broken_arabic_layer": [
            p["page"] for p in pages if p.get("broken_arabic_text_layer")
        ],
        "language_warnings": _language_warnings(),
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
    stage_started = time.perf_counter()
    classification = classify_document_pages(pages)
    log.info("[TIMING] Stage classification: %.2f s | docs=%s", time.perf_counter() - stage_started, len(classification.get("documents", [])))

    extracted_documents = []
    document_results = []

    # 3. Extract fields concurrently. These requests are independent after
    # classification. Keep result ordering aligned with classification output.
    extraction_jobs = []
    for document in classification["documents"]:
        document_type = document["document_type"]

        # Unknown pages have no typed schema to extract.
        if document_type == "unknown":
            continue

        document_pages = [
            page for page in pages
            if page["page"] in document["pages"]
        ]
        extraction_jobs.append({
            "document": document,
            "document_type": document_type,
            "document_pages": document_pages,
            # Rich, labelled source for typed extraction and evidence lookup.
            "source_text": "\n\n".join(
                _combined_page_source(page)
                for page in document_pages
            ),
            # Plain text for the legacy validator: do not inject page headers
            # or OCR source labels into the text it receives.
            "validation_text": "\n".join(
                str(page.get("text") or "").strip()
                for page in document_pages
                if str(page.get("text") or "").strip()
            ),
            "ocr_used": any(page.get("ocr_used") for page in document_pages),
        })

    # Submit larger documents first so the longest independent request starts early,
    # while keeping extraction_jobs in classifier order for the final response.
    submission_jobs = sorted(
        extraction_jobs, key=lambda job: len(job["source_text"]), reverse=True
    )

    # By default, allow one worker per document; cap explicitly in .env if needed.
    from concurrent.futures import ThreadPoolExecutor, as_completed

    try:
        configured_workers = int(os.getenv("EXTRACTION_CONCURRENCY", str(len(extraction_jobs) or 1)))
    except (TypeError, ValueError):
        configured_workers = len(extraction_jobs) or 1
    max_workers = max(1, configured_workers)
    extraction_started = time.perf_counter()
    futures = {}

    def _run_typed_extraction(job):
        started = time.perf_counter()
        result = extract_typed_document(
            document_type=job["document_type"],
            pages=job["document_pages"],
        )
        return result, time.perf_counter() - started

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for job in submission_jobs:
            futures[executor.submit(_run_typed_extraction, job)] = job

        # Log each extraction as soon as it finishes.
        for future in as_completed(futures):
            job = futures[future]
            try:
                extraction, elapsed = future.result()
            except Exception as exc:
                log.exception("Typed extraction failed for %s; preserving the rest of the package.", job["document_type"])
                extraction = {
                    "document_type": job["document_type"],
                    "fields": {},
                    "evidence": {},
                    "unsupported_fields": [],
                    "extraction_error": str(exc),
                }
                elapsed = 0.0
            log.info(
                "[TIMING] Stage typed extraction %s pages=%s: %.2f s | concurrent_workers=%s",
                job["document_type"],
                job["document"]["pages"],
                elapsed,
                max_workers,
            )
            job["extraction"] = extraction

    log.info(
        "[TIMING] Stage typed extraction concurrent total: %.2f s | documents=%s | workers=%s",
        time.perf_counter() - extraction_started,
        len(extraction_jobs),
        max_workers,
    )

    # Validate and assemble in the original classifier order.
    for job in extraction_jobs:
        document = job["document"]
        document_type = job["document_type"]
        document_pages = job["document_pages"]
        extraction = job["extraction"]
        source_text = job["source_text"]
        validation_text = job["validation_text"]
        ocr_used = job["ocr_used"]

        # Find each value in the source text in code.  The model's own quotes often
        # stitch table cells together in reading order, which never appears verbatim
        # in OCR text (columns interleave), so they are only a fallback.
        try:
            located = build_evidence(extraction["fields"], source_text, fuzzy=ocr_used)
            extraction.setdefault("evidence", {})
            for field_name, quote in located.items():
                if quote:
                    extraction["evidence"][field_name] = quote
        except Exception:
            log.exception("Evidence location failed for %s; using model quotes", document_type)

        validation_started = time.perf_counter()
        validation = validate_document(
            extraction,
            source_text,
            ocr_used=ocr_used,
        )

        # A failed AI extraction must remain visible in the document result,
        # even though the rest of the package continues through validation.
        extraction_failed = bool(extraction.get("extraction_error"))
        if extraction_failed:
            validation["status"] = "needs_review"
            warnings = validation.setdefault("warnings", [])
            error_message = str(extraction.get("extraction_error") or "Unknown extraction error")
            warnings.insert(
                0,
                f"AI extraction failed: {error_message}. "
                "Review the original PDF and retry extraction."
            )

        log.info(
            "[TIMING] Stage document validation %s: %.2f s",
            document_type,
            time.perf_counter() - validation_started,
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
            "extraction_failed": extraction_failed,
            "ocr_used": ocr_used,
            "ocr_review_required": ocr_review_required,
            "ocr_pages_low_confidence": low_confidence_pages,
            "vision_ocr_pages": vision_pages,
        })

    # 4. Compare information across documents.
    cross_started = time.perf_counter()
    cross_validation = validate_cross_documents(extracted_documents)
    log.info("[TIMING] Stage cross-document validation: %.2f s", time.perf_counter() - cross_started)

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

    total_elapsed = time.perf_counter() - package_started
    log.info("[TIMING] ===== PACKAGE ANALYSIS TOTAL: %.2f s (%.2f min) | %s =====", total_elapsed, total_elapsed / 60, filename)

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