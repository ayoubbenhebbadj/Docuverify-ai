
from pathlib import Path

from app.pdf_reader import extract_pdf_text
from app.document_validator import validate_document

pdf_path = Path(__file__).parent / "merged files.pdf"
pdf_result = extract_pdf_text(pdf_path.read_bytes())
pages = pdf_result["pages"]

# Bill of lading: pages 3 and 4.
source_text = "\n".join(
    page["text"]
    for page in pages
    if page["page"] in [3, 4]
)

extraction = {
    "document_type": "bill_of_lading",
    "fields": {
        "bill_of_lading_number": "BOL-9938210-DE",
        "shipper_name": "Nexus Industrial GmbH",
        "consignee_name": "Apex Systems Europe B.V.",
        "carrier_name": "Ocean Carrier Lines",
        "total_gross_weight": "465.00 KG",
    },
    "evidence": {
        "bill_of_lading_number": "BOL-9938210-DE",
        "shipper_name": "Nexus Industrial GmbH",
        "consignee_name": "Apex Systems Europe B.V.",
        "carrier_name": "Ocean Carrier Lines",
        "total_gross_weight": "465.00 KG",
    },
}

result = validate_document(extraction, source_text)

print("Validation status:", result["status"])
print("Missing fields:", result["missing_fields"])
print("Invalid fields:", result["invalid_fields"])
print("Unsupported evidence:", result["unsupported_evidence"])
print("Warnings:", result["warnings"])

assert "total_gross_weight" not in result["unsupported_evidence"], (
    "Gross-weight evidence is still unsupported."
)

print("\nPASS: Gross-weight evidence is supported.")
