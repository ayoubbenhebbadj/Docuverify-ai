
from pathlib import Path
import re

from app.pdf_reader import extract_pdf_text


PDF_PATH = Path("merged files.pdf")

EXPECTED_TYPES = [
    "certificate_of_origin",
    "bill_of_lading",
    "packing_list",
    "commercial_invoice",
]

if not PDF_PATH.exists():
    raise FileNotFoundError(f"PDF not found: {PDF_PATH.resolve()}")

pages = extract_pdf_text(PDF_PATH.read_bytes())["pages"]

# Simulate the page classifications so no AI request is needed.
normalized_pages = [
    {
        "page": 1,
        "document_type": "certificate_of_origin",
        "starts_new_document": True,
        "confidence": 0.99,
        "evidence": "CERTIFICATE OF ORIGIN",
    },
    {
        "page": 2,
        "document_type": "certificate_of_origin",
        "starts_new_document": True,
        "confidence": 0.99,
        "evidence": "Certificate of Origin",
    },
    {
        "page": 3,
        "document_type": "bill_of_lading",
        "starts_new_document": True,
        "confidence": 0.99,
        "evidence": "BILL OF LADING",
    },
    {
        "page": 4,
        "document_type": "bill_of_lading",
        "starts_new_document": True,
        "confidence": 0.99,
        "evidence": "Bill of Lading",
    },
    {
        "page": 5,
        "document_type": "packing_list",
        "starts_new_document": True,
        "confidence": 0.99,
        "evidence": "PACKING LIST",
    },
    {
        "page": 6,
        "document_type": "packing_list",
        "starts_new_document": True,
        "confidence": 0.99,
        "evidence": "Packing List",
    },
    {
        "page": 7,
        "document_type": "commercial_invoice",
        "starts_new_document": True,
        "confidence": 0.99,
        "evidence": "COMMERCIAL INVOICE",
    },
    {
        "page": 8,
        "document_type": "commercial_invoice",
        "starts_new_document": True,
        "confidence": 0.99,
        "evidence": "Commercial Invoice",
    },
]

page_text_by_number = {
    page["page"]: page.get("text", "")
    for page in pages
}

identifier_pattern = re.compile(
    r"\b(?:"
    r"INV-\d{4}-[\w-]+|"
    r"PKL-\d{4}-[\w-]+|"
    r"BOL-[\w-]+|"
    r"COO-[\w-]+"
    r")\b",
    re.IGNORECASE,
)

# Recover short footer pages using matching identifiers.
for index in range(1, len(normalized_pages)):
    item = normalized_pages[index]
    previous = normalized_pages[index - 1]

    current_text = page_text_by_number[item["page"]]
    previous_text = page_text_by_number[previous["page"]]

    if not current_text.strip() or len(current_text.strip()) > 500:
        continue

    current_ids = {
        match.upper()
        for match in identifier_pattern.findall(current_text)
    }
    previous_ids = {
        match.upper()
        for match in identifier_pattern.findall(previous_text)
    }

    if (
        current_ids
        and current_ids.intersection(previous_ids)
        and previous["document_type"] != "unknown"
    ):
        item["document_type"] = previous["document_type"]
        item["starts_new_document"] = False
        item["confidence"] = min(previous["confidence"], 0.80)
        item["evidence"] = "Matched preceding document identifier."

# Group consecutive pages.
documents = []

for item in normalized_pages:
    starts_new = (
        not documents
        or item["starts_new_document"]
        or documents[-1]["document_type"] != item["document_type"]
    )

    if starts_new:
        documents.append({
            "document_type": item["document_type"],
            "pages": [item["page"]],
            "confidence": item["confidence"],
        })
    else:
        documents[-1]["pages"].append(item["page"])
        documents[-1]["confidence"] = min(
            documents[-1]["confidence"],
            item["confidence"],
        )

print("Documents found:", len(documents))

for document in documents:
    print(
        f"{document['document_type']} "
        f"-> pages {document['pages']}"
    )

assert len(documents) == 4, "Expected four documents."
assert [d["document_type"] for d in documents] == EXPECTED_TYPES
assert [d["pages"] for d in documents] == [
    [1, 2], [3, 4], [5, 6], [7, 8]
]

print("\nPASSED: real PDF text grouped into four documents.")
