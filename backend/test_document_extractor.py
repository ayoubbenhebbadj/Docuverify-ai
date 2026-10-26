
import json

from app.pdf_reader import extract_pdf_text
from app.document_classifier import classify_document_pages
from app.document_extractor import extract_typed_document


PDF_PATH = r"merged files.pdf"


with open(PDF_PATH, "rb") as pdf_file:
    pdf_bytes = pdf_file.read()

pdf_data = extract_pdf_text(pdf_bytes)

# First classify the pages.
classification = classify_document_pages(pdf_data["pages"])

print("Detected documents:", classification["documents_found"])

all_results = []

# Then extract fields from each detected document.
for document in classification["documents"]:
    document_type = document["document_type"]

    if document_type == "unknown":
        print("Skipping unknown document:", document["pages"])
        continue

    document_pages = [
        page
        for page in pdf_data["pages"]
        if page["page"] in document["pages"]
    ]

    print(
        f"\nExtracting {document_type} "
        f"from pages {document['pages']}..."
    )

    result = extract_typed_document(
        document_type=document_type,
        pages=document_pages,
    )

    result["pages"] = document["pages"]
    all_results.append(result)

print("\n=== EXTRACTION RESULTS ===")
print(json.dumps(all_results, indent=2, ensure_ascii=False))
