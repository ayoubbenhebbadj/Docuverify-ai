
from datetime import date
from decimal import Decimal, InvalidOperation

import re


def normalize_document_type(value: str | None) -> str | None:
    if not value:
        return None

    normalized = re.sub(
        r"[^a-z0-9]+",
        "_",
        value.strip().lower()
    ).strip("_")

    aliases = {
        "commercial_invoice": "commercial_invoice",
        "invoice": "commercial_invoice",
    }

    return aliases.get(normalized, normalized)
# Initial demonstration rules for commercial invoices.
# We will later make these configurable per document type.
REQUIRED_FIELDS = {
    "commercial_invoice": [
        "company_name",
        "supplier_name",
        "invoice_number",
        "invoice_date",
        "amount",
        "currency",
    ]
}


def validate_document(data: dict) -> dict:
    document_type = normalize_document_type(
    data.get("document_type")
    )
    if document_type not in REQUIRED_FIELDS:
        return {
            "status": "needs_review",
            "missing_fields": [],
            "invalid_fields": [],
            "message": (
                "Document type is unknown or unsupported. "
                "Confirm the type and applicable rules."
            ),
        }

    required_fields = REQUIRED_FIELDS[document_type]
    missing_fields = []
    invalid_fields = []

    for field in required_fields:
        value = data.get(field)

        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            missing_fields.append(field)

    # Validate the date only if it was extracted.
    invoice_date = data.get("invoice_date")

    if invoice_date:
        try:
            date.fromisoformat(invoice_date)
        except (TypeError, ValueError):
            invalid_fields.append({
                "field": "invoice_date",
                "reason": "Expected a valid date in YYYY-MM-DD format.",
            })

    # Validate amount without accepting booleans as numbers.
    amount = data.get("amount")

    if amount is not None:
        try:
            if isinstance(amount, bool):
                raise InvalidOperation()

            numeric_amount = Decimal(str(amount))

            if not numeric_amount.is_finite() or numeric_amount <= 0:
                raise InvalidOperation()

        except (InvalidOperation, ValueError, TypeError):
            invalid_fields.append({
                "field": "amount",
                "reason": "Expected a positive numeric amount.",
            })

    if invalid_fields:
        status = "needs_review"
    elif missing_fields:
        status = "incomplete"
    else:
        status = "complete"

    return {
        "status": status,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "message": {
            "complete": "All configured required fields were extracted.",
            "incomplete": "One or more required fields are missing.",
            "needs_review": "One or more fields require review.",
        }[status],
    }
