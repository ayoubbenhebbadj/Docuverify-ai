
from pathlib import Path
from app.pdf_reader import extract_pdf_text
import re

PDF_PATH = Path("merged files.pdf")

if not PDF_PATH.exists():
    raise FileNotFoundError(
        f"PDF not found: {PDF_PATH.resolve()}\n"
        "Update PDF_PATH to your sample PDF location."
    )

pdf_result = extract_pdf_text(PDF_PATH.read_bytes())
pages = pdf_result["pages"]

identifier_pattern = re.compile(
    r"\b(?:INV-\d{4}-[\w-]+|PKL-\d{4}-[\w-]+|BOL-[\w-]+|COO-[\w-]+)\b",
    re.IGNORECASE,
)

print("Page count:", len(pages))

for index, page in enumerate(pages):
    text = page.get("text", "").strip()
    identifiers = sorted({
        value.upper()
        for value in identifier_pattern.findall(text)
    })

    print(f"\nPage {page['page']}")
    print("Characters:", len(text))
    print("Identifiers:", identifiers)
    print("Text preview:", repr(text[:180]))

    if index > 0:
        previous_text = pages[index - 1].get("text", "")
        previous_ids = {
            value.upper()
            for value in identifier_pattern.findall(previous_text)
        }

        print(
            "Shares identifier with previous page:",
            bool(set(identifiers) & previous_ids),
        )
