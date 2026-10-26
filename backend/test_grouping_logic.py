
from app.document_classifier import DOCUMENT_TYPES
import re


# Simulate the eight pages in your sample PDF.
pages = [
    {"page": 1, "text": "Certificate of Origin COO-DE-2026-9912"},
    {"page": 2, "text": "Certificate of Origin • COO-DE-2026-9912 Page 1 of 1"},
    {"page": 3, "text": "Bill of Lading BOL-9938210-DE"},
    {"page": 4, "text": "Bill of Lading • BOL-9938210-DE Page 1 of 1"},
    {"page": 5, "text": "Packing List PKL-2026-88421"},
    {"page": 6, "text": "Packing List • PKL-2026-88421 Page 1 of 1"},
    {"page": 7, "text": "Commercial Invoice INV-2026-88421"},
    {"page": 8, "text": "Commercial Invoice • INV-2026-88421 Page 1 of 1"},
]

# Simulate the AI classifications returned for the pages.
normalized_pages = [
    {"page": 1, "document_type": "certificate_of_origin", "starts_new_document": True, "confidence": 0.99, "evidence": "Certificate of Origin"},
    {"page": 2, "document_type": "certificate_of_origin", "starts_new_document": True, "confidence": 0.99, "evidence": "Certificate of Origin"},
    {"page": 3, "document_type": "bill_of_lading", "starts_new_document": True, "confidence": 0.99, "evidence": "Bill of Lading"},
    {"page": 4, "document_type": "bill_of_lading", "starts_new_document": True, "confidence": 0.99, "evidence": "Bill of Lading"},
    {"page": 5, "document_type": "packing_list", "starts_new_document": True, "confidence": 0.99, "evidence": "Packing List"},
    {"page": 6, "document_type": "packing_list", "starts_new_document": True, "confidence": 0.99, "evidence": "Packing List"},
    {"page": 7, "document_type": "commercial_invoice", "starts_new_document": True, "confidence": 0.99, "evidence": "Commercial Invoice"},
    {"page": 8, "document_type": "commercial_invoice", "starts_new_document": True, "confidence": 0.99, "evidence": "Commercial Invoice"},
]

page_text_by_number = {p["page"]: p["text"] for p in pages}

identifier_pattern = re.compile(
    r"\b(?:INV-\d{4}-[\w-]+|PKL-\d{4}-[\w-]+|BOL-[\w-]+|COO-[\w-]+)\b",
    re.IGNORECASE,
)

# Apply the same footer recovery logic.
for index in range(1, len(normalized_pages)):
    item = normalized_pages[index]
    previous = normalized_pages[index - 1]
    current_text = page_text_by_number[item["page"]]
    previous_text = page_text_by_number[previous["page"]]

    if not current_text.strip() or len(current_text.strip()) > 500:
        continue

    current_ids = {m.upper() for m in identifier_pattern.findall(current_text)}
    previous_ids = {m.upper() for m in identifier_pattern.findall(previous_text)}

    if (
        current_ids
        and current_ids.intersection(previous_ids)
        and previous["document_type"] != "unknown"
    ):
        item["document_type"] = previous["document_type"]
        item["starts_new_document"] = False
        item["confidence"] = min(previous["confidence"], 0.80)
        item["evidence"] = "Matched preceding document identifier."

# Apply the grouping logic.
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
            "evidence": [item["evidence"]] if item["evidence"] else [],
        })
    else:
        current = documents[-1]
        current["pages"].append(item["page"])
        current["confidence"] = min(current["confidence"], item["confidence"])

        if item["evidence"]:
            current["evidence"].append(item["evidence"])

print("Documents found:", len(documents))

for document in documents:
    print(document["document_type"], "-> pages", document["pages"])

assert len(documents) == 4, "Expected exactly four grouped documents."
assert [d["pages"] for d in documents] == [[1, 2], [3, 4], [5, 6], [7, 8]]

print("\nPASSED: footer pages are grouped with their preceding documents.")
