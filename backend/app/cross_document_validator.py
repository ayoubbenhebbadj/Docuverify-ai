
from openai.types import image_gen_partial_image_event
from openai.types import image_gen_partial_image_event
from openai.types import image_gen_partial_image_event
import re
from decimal import Decimal, InvalidOperation


def normalize(value):
    """Normalize text for reliable comparisons."""
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[.,;:]+$", "", text)

    return text

def normalize_company_name(value):
    """Normalize a company name for cross-document comparison."""
    if value is None:
        return ""

    text = str(value).strip()

    # Remove registration and tax details when they follow a separator.
    text = re.split(
        r"[,;]|\b(?:EORI|VAT(?:\s+ID)?|Tax\s+ID|Registration\s+No\.?)\s*:",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]

    # Normalize whitespace and punctuation.
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .,:;-").lower()

    # Normalize common OCR spacing variations in legal suffixes.
    text = re.sub(r"(?<=[a-z])(?=(?:gmbh|ltd|limited|llc|inc|corp|sarl)\b)", " ", text)

    return text

def parse_number(value):
    """Convert a numeric value or simple formatted number to Decimal."""
    if value is None:
        return None

    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    text = str(value).strip()
    text = text.replace(",", "").replace("€", "").replace("$", "")
    text = re.sub(r"\s+", "", text)

    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None

    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


def parse_weight_kg(value):
    """Extract a weight and convert grams or kilograms to kilograms."""
    if value is None:
        return None

    text = str(value).strip().lower().replace(",", "")

    match = re.search(
        r"(-?\d+(?:\.\d+)?)\s*(kg|kgs|kilograms?|g|grams?)\b",
        text,
    )

    if not match:
        return None

    amount = Decimal(match.group(1))
    unit = match.group(2)

    if unit in {"g", "gram", "grams"}:
        amount /= Decimal("1000")

    return amount


def validate_cross_documents(documents):
    """
    Compare extracted fields across documents.

    Expected input:
    [
        {
            "document_type": "commercial_invoice",
            "fields": {...}
        },
        ...
    ]
    """
    by_type = {
        doc.get("document_type"): doc.get("fields", {})
        for doc in documents
    }

    checks = []

    def add_check(name, values, status, message):
        checks.append({
            "check": name,
            "status": status,
            "values": values,
            "message": message,
        })

    def compare_text(name, field_sources):
        values = {}

        for doc_type, field_name in field_sources:
            fields = by_type.get(doc_type, {})
            value = fields.get(field_name)

            if value is not None and str(value).strip():
                values[doc_type] = value

        if len(values) < 2:
            add_check(
                name, values, "needs_review",
                "Not enough documents contain this field to compare."
            )
            return

        if name in ("Exporter / shipper", "Consignee"):
            normalized = {
                normalize_company_name(value)
                for value in values.values()
            }
        else:
            normalized = {
                  normalize(value)
                for value in values.values()
            }

        if len(normalized) == 1:
            add_check(name, values, "passed", "Values match.")
        else:
            add_check(name, values, "mismatch", "Values differ between documents.")

    # 1. Invoice number
    compare_text(
        "Invoice number",
        [
            ("commercial_invoice", "invoice_number"),
            ("packing_list", "invoice_number"),
            ("bill_of_lading", "invoice_number"),
            ("certificate_of_origin", "invoice_number"),
        ],
    )

    # 2. Exporter / shipper
    compare_text(
        "Exporter / shipper",
        [
            ("commercial_invoice", "exporter_name"),
            ("packing_list", "exporter_name"),
            ("bill_of_lading", "shipper_name"),
            ("certificate_of_origin", "exporter_name"),
            ("certificate_of_quality", "exporter_name"),
            ("certificate_of_conformity", "exporter_name"),
        ],
    )

    # 3. Consignee
        # 3. Consignee
    compare_text(
        "Consignee",
        [
            ("commercial_invoice", "consignee_name"),
            ("packing_list", "consignee_name"),
            ("bill_of_lading", "consignee_name"),
            ("certificate_of_origin", "consignee_name"),
            ("certificate_of_quality", "consignee_name"),
            ("certificate_of_conformity", "consignee_name"),
        ],
    )

    # 4. Gross weight
    weight_sources = [
        ("commercial_invoice", "total_gross_weight"),
        ("packing_list", "total_gross_weight"),
        ("bill_of_lading", "total_gross_weight"),
    ]

    weights = {}
    for doc_type, field_name in weight_sources:
        value = by_type.get(doc_type, {}).get(field_name)
        if value is not None:
            parsed = parse_weight_kg(value)
            if parsed is not None:
                weights[doc_type] = parsed

    if len(weights) < 2:
        add_check(
            "Gross weight", weights, "needs_review",
            "Not enough readable gross weights to compare."
        )
    elif max(weights.values()) - min(weights.values()) <= Decimal("0.01"):
        add_check(
            "Gross weight", weights, "passed",
            "Gross weights agree within 0.01 kg."
        )
    else:
        add_check(
            "Gross weight", weights, "mismatch",
            "Gross weights differ between documents."
        )

    # 5. Net weight
    net_weights = {}
    for doc_type in ("commercial_invoice", "packing_list"):
        value = by_type.get(doc_type, {}).get("total_net_weight")
        parsed = parse_weight_kg(value)

        if parsed is not None:
            net_weights[doc_type] = parsed

    if len(net_weights) < 2:
        add_check(
            "Net weight", net_weights, "needs_review",
            "Not enough readable net weights to compare."
        )
    elif max(net_weights.values()) - min(net_weights.values()) <= Decimal("0.01"):
        add_check(
            "Net weight", net_weights, "passed",
            "Net weights agree within 0.01 kg."
        )
    else:
        add_check(
            "Net weight", net_weights, "mismatch",
            "Net weights differ between documents."
        )

    # 6. Package count
    package_sources = [
        ("commercial_invoice", "package_count"),
        ("packing_list", "package_count"),
        ("bill_of_lading", "package_count"),
    ]

    package_values = {}
    for doc_type, field_name in package_sources:
        value = by_type.get(doc_type, {}).get(field_name)

        if value is None:
            continue

        # Compare the number of packages, not the number of individual items.
        match = re.search(r"\d+", str(value))
        if match:
            package_values[doc_type] = int(match.group())

    if len(package_values) < 2:
        add_check(
            "Package count", package_values, "needs_review",
            "Not enough package counts to compare."
        )
    elif len(set(package_values.values())) == 1:
        add_check(
            "Package count", package_values, "passed",
            "Package counts agree."
        )
    else:
        add_check(
            "Package count", package_values, "mismatch",
            "Package counts differ between documents."
        )

    # 7. Invoice arithmetic
    invoice = by_type.get("commercial_invoice", {})

    subtotal = parse_number(invoice.get("subtotal"))
    freight = parse_number(invoice.get("freight_and_handling"))
    insurance = parse_number(invoice.get("insurance_fee"))
    tax = parse_number(invoice.get("tax_amount"))
    total = parse_number(invoice.get("total_amount"))

    if subtotal is None or total is None:
        add_check(
            "Invoice arithmetic", {}, "needs_review",
            "Subtotal or total amount is missing or unreadable."
        )
    else:
        calculated_total = (
            subtotal
            + (freight if freight is not None else Decimal("0"))
            + (insurance if insurance is not None else Decimal("0"))
            + (tax if tax is not None else Decimal("0"))
        )

        values = {
            "subtotal": str(subtotal),
            "freight_and_handling": str(freight) if freight is not None else None,
            "insurance_fee": str(insurance) if insurance is not None else None,
            "tax_amount": str(tax) if tax is not None else None,
            "calculated_total": str(calculated_total),
            "declared_total": str(total),
        }

        if calculated_total == total:
            add_check(
                "Invoice arithmetic", values, "passed",
                "The calculated total matches the declared total."
            )
        else:
            add_check(
                "Invoice arithmetic", values, "mismatch",
                "The calculated total does not match the declared total."
            )

    summary = {
        "total_checks": len(checks),
        "passed": sum(c["status"] == "passed" for c in checks),
        "mismatches": sum(c["status"] == "mismatch" for c in checks),
        "needs_review": sum(c["status"] == "needs_review" for c in checks),
    }

    return {
        "summary": summary,
        "checks": checks,
    }
