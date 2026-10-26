
from app.pdf_reader import extract_pdf_text
from app.document_classifier import classify_document_pages

PDF_PATH = r"scanned_bill_of_lading.pdf"
with open(PDF_PATH, "rb") as pdf_file:
    pdf_bytes = pdf_file.read()

pdf_data = extract_pdf_text(pdf_bytes)

result = classify_document_pages(pdf_data["pages"])

print("Pages:", result["page_count"])
print("Documents found:", result["documents_found"])
print("Missing documents:", result["missing_documents"])
print("Unclassified pages:", result["unclassified_pages"])

for document in result["documents"]:
    print(
        document["document_type"],
        "Pages:", document["pages"],
        "Confidence:", document["confidence"],
    )
