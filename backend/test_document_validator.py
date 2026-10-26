
from app.pdf_reader import extract_pdf_text
from app.document_classifier import classify_document_pages
from app.document_extractor import extract_typed_document
from app.document_validator import validate_document


PDF_PATH = r"merged files.pdf"


with open(PDF_PATH, "rb") as pdf_file:
    pdf_bytes = pdf_file.read()

pdf_data = extract_pdf_text(pdf_bytes)
classification = classify_document_pages(pdf_data["pages"])

for document in classification["documents"]:
    document_type = document["document_type"]

    if document_type == "unknown":
        print(f"\nSkipping unknown pages: {document['pages']}")
        continue

    document_pages = [
        page for page in pdf_data["pages"]
        if page["page"] in document["pages"]
    ]

    source_text = "\n\n".join(
        page.get("text", "") for page in document_pages
    )

    print(f"\nValidating {document_type}...")

    extraction = extract_typed_document(
        document_type=document_type,
        pages=document_pages,
    )

    validation = validate_document(extraction, source_text)

for field in validation["unsupported_evidence"]:
    print(f"\n--- {document_type}: {field} ---")
    print("Extracted value:")
    print(repr(extraction["fields"].get(field)))
    print("Evidence quotation:")
    print(repr(extraction["evidence"].get(field)))
    print("Source text:")
    print(repr(source_text))
