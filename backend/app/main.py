import traceback

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from app.document_classifier import classify_document_pages
from app.ai_extractor import extract_document_fields
from app.pdf_reader import extract_pdf_text
from app.validator import validate_document
from app.document_classifier import classify_document_pages
from app.document_extractor import extract_typed_document
from app.document_validator import validate_document
from app.cross_document_validator import validate_cross_documents


app = FastAPI(
    title="DocuVerify AI API",
    description="API for import/export document verification",
    version="0.1.0",
)

# Allow the local React dev server to call the API from the common local ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "DocuVerify AI API",
    }


@app.post("/api/documents/extract-text")
async def extract_document(file: UploadFile = File(...)):
    filename, pdf_bytes = await read_uploaded_pdf(file)

    try:
        result = extract_pdf_text(pdf_bytes)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "filename": filename,
        **result,
    }


@app.post("/api/documents/analyze")
async def analyze_document(file: UploadFile = File(...)):
    filename, pdf_bytes = await read_uploaded_pdf(file)

    try:
        pdf_result = extract_pdf_text(pdf_bytes)

        if not pdf_result["has_text"]:
            return {
                "filename": filename,
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
            "filename": filename,
            "page_count": pdf_result["page_count"],
            "extracted_fields": extracted_fields,
            "validation": validation,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        print("\n=== DOCUMENT ANALYSIS ERROR ===")
        traceback.print_exc()
        print("=== END ERROR ===\n")

        raise HTTPException(
            status_code=502,
            detail=(
                "Document analysis failed. "
                "Check the backend terminal for the underlying error."
            ),
        ) from exc

@app.post("/api/documents/analyze-package")
async def analyze_package(file: UploadFile = File(...)):
    filename, pdf_bytes = await read_uploaded_pdf(file)

    try:
        # 1. Extract text from every PDF page.
        pdf_result = extract_pdf_text(pdf_bytes)

        if not pdf_result["has_text"]:
            return {
                "filename": filename,
                "status": "needs_ocr",
                "message": (
                    "No selectable text was found. "
                    "OCR support is required for this document."
                ),
                "page_count": pdf_result["page_count"],
            }

        pages = pdf_result["pages"]
        
        # OCR quality summary for the frontend.
        ocr_pages = [
            page["page"]
            for page in pages
            if page.get("ocr_used", False)
        ]

        pages_low_confidence = pdf_result.get(
            "pages_low_confidence", []
        )

        pages_needing_ocr = pdf_result.get(
            "pages_needing_ocr", []
        )

        ocr_summary = {
            "ocr_used": bool(ocr_pages),
            "pages_processed": ocr_pages,
            "pages_low_confidence": pages_low_confidence,
            "pages_needing_ocr": pages_needing_ocr,
            "review_required": bool(
                pages_low_confidence or pages_needing_ocr
            ),
        }


        # 2. Classify pages and group them into documents.
        classification = classify_document_pages(pages)

        extracted_documents = []
        document_results = []

        # 3. Extract fields and validate each detected document.
        for document in classification["documents"]:
            document_type = document["document_type"]
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

            validation = validate_document(
                extraction,
                source_text,
            )
            
            # Identify OCR pages that need manual review for this document.
            low_confidence_pages = [
                page["page"]
                for page in document_pages
                if page.get("ocr_used", False)
                and page.get("ocr_low_confidence", False)
            ]

            ocr_review_required = bool(low_confidence_pages)

            if ocr_review_required:
                validation["status"] = "needs_review"

                validation["warnings"].append(
                    "OCR confidence is low on PDF page(s): "
                    f"{', '.join(map(str, low_confidence_pages))}. "
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
                "ocr_review_required": ocr_review_required,
                "ocr_pages_low_confidence": low_confidence_pages,
            })

        # 4. Compare information across documents.
        cross_validation = validate_cross_documents(
            extracted_documents
        )

        # 5. Summarize package-level issues.
        missing_documents = classification["missing_documents"]
        unclassified_pages = classification["unclassified_pages"]

        document_validation_issues = [
        result
        for result in document_results
        if result["validation"].get("status")
        not in ("passed", "complete")
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

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        print("\n=== PACKAGE ANALYSIS ERROR ===")
        traceback.print_exc()
        print("=== END ERROR ===\n")

        raise HTTPException(
            status_code=502,
            detail=(
                "Package analysis failed. "
                "Check the backend terminal for the underlying error."
            ),
        ) from exc

@app.post("/api/documents/classify")
async def classify_documents(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=422,
            detail="Please upload a PDF file.",
        )

    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="The PDF exceeds the 10 MB upload limit.",
        )

    if not pdf_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=422,
            detail="The uploaded file is not a valid PDF.",
        )

    try:
        pdf_data = extract_pdf_text(pdf_bytes)

        if pdf_data["needs_ocr"]:
            return {
                "filename": file.filename,
                "status": "needs_ocr",
                "message": (
                    "No readable text was found. "
                    "OCR is required before classification."
                ),
            }

        result = classify_document_pages(pdf_data["pages"])

        return {
            "filename": file.filename,
            "status": (
                "needs_review"
                if result["missing_documents"]
                or result["unclassified_pages"]
                else "classified"
            ),
            **result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        import traceback
        traceback.print_exc()

        raise HTTPException(
            status_code=502,
            detail="Document classification failed. Check the backend terminal.",
        ) from exc

    finally:
        await file.close()
