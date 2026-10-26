
from pathlib import Path
import re
from app.pdf_reader import extract_pdf_text
from app.document_validator import evidence_matches

pdf_path = Path(__file__).parent / "merged files.pdf"

if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found: {pdf_path}")

pdf_result = extract_pdf_text(pdf_path.read_bytes())
pages = pdf_result["pages"]

print("PDF pages:", len(pages))
print("Has text:", pdf_result["has_text"])

# Evidence examples based on the fields returned by your previous analysis.
tests = [
    {
        "name": "Carrier name",
        "pages": [3, 4],
        "evidence": "Ocean Carrier Lines",
    },
    {
        "name": "Goods description",
        "pages": [3, 4],
        "evidence": "Industrial Valves, Power Converters, Sensor Arrays",
    },
    {
        "name": "Package count",
        "pages": [3, 4],
        "evidence": "3 PALLETS (187 PCS)",
    },
    {
        "name": "Gross weight",
        "pages": [3, 4],
        "evidence": "465.00",
    },
    {
        "name": "Container number",
        "pages": [3, 4],
        "evidence": "MSCU-482910-4",
    },
    {
        "name": "Packing list package type",
        "pages": [5, 6],
        "evidence": "Euro Pallet (Wood)",
    },
]

for test in tests:
    source_text = "\n".join(
        page["text"]
        for page in pages
        if page["page"] in test["pages"]
    )

    matched = evidence_matches(test["evidence"], source_text)

    print(
        f"{'PASS' if matched else 'REVIEW'}: "
        f"{test['name']} -> {matched}"
    )
print("\n--- Gross-weight source text (pages 3–4) ---")

for page in pages:
    if page["page"] in [3, 4]:
        for line in page["text"].splitlines():
            if "weight" in line.lower() or "465" in line:
                print(repr(line))

print("\n--- Full page 3 text ---")
print(pages[2]["text"])

print("\n--- Full page 4 text ---")
print(pages[3]["text"])

page3_text = pages[2]["text"]

has_gross_weight_header = bool(
    re.search(
        r"GROSS\s+WT\s*\(KG\)",
        page3_text,
        re.IGNORECASE,
    )
)

print(
    "PASS: Gross-weight unit supported by header"
    if has_gross_weight_header
    else "REVIEW: Gross-weight unit not confirmed"
)