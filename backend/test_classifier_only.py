
from pathlib import Path
from app.pdf_reader import extract_pdf_text
from app.document_classifier import classify_document_pages

PDF_PATH = Path("merged files.pdf")

if not PDF_PATH.exists():
    raise FileNotFoundError(f"PDF not found: {PDF_PATH.resolve()}")

pdf_result = extract_pdf_text(PDF_PATH.read_bytes())

if not pdf_result["has_text"]:
    raise ValueError("The PDF has no selectable text.")

result = classify_document_pages(pdf_result["pages"])

print("Documents found:", result["documents_found"])
print("Missing documents:", result["missing_documents"])
print("Unclassified pages:", result["unclassified_pages"])

for document in result["documents"]:
    print(
        f"{document['document_type']} "
        f"-> pages {document['pages']}"
    )
