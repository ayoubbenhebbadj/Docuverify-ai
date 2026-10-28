
import re
from difflib import SequenceMatcher
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

    # Ignore descriptive exporter suffixes that are not part of the legal name.
    text = re.sub(r"\s*\(\s*for\s+export\s*\)\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfor\s+export\b", " ", text, flags=re.IGNORECASE)

    # Normalize whitespace and punctuation.
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .,:;-").lower()

    # Normalize common OCR spacing variations in legal suffixes.
    text = re.sub(r"(?<=[a-z])(?=(?:gmbh|ltd|limited|llc|inc|corp|sarl)\b)", " ", text)
    # Legal forms are not the core name and are frequently omitted in Arabic.
    text = re.sub(r"\b(?:sarl|gmbh|ltd|limited|llc|inc|corp|corporation)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text

def normalize_identifier(value):
    """Normalise a document number, tolerating common OCR confusions."""
    if value is None:
        return ""
    text = re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()
    return text.translate(str.maketrans("OIL", "011"))


def _arabic_to_latin_name(value: str) -> str:
    """Lightweight name transliteration for common Arabic spellings.

    This is deliberately limited to company-name comparison; it is not a
    general-purpose Arabic transliterator. Arabic ب can represent Latin b/p,
    and common vowel letters are mapped to approximate Latin vowels.
    """
    mapping = str.maketrans({
        "ا": "a", "أ": "a", "إ": "i", "آ": "a", "ى": "a",
        "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "h",
        "خ": "kh", "د": "d", "ذ": "th", "ر": "r", "ز": "z",
        "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t",
        "ظ": "z", "ع": "a", "غ": "gh", "ف": "f", "ق": "q",
        "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h",
        "ة": "a", "و": "o", "ي": "i", "ئ": "i", "ؤ": "o",
        "ء": "", "پ": "p",
    })
    return value.translate(mapping)


def names_match(a: str, b: str, threshold: float = 0.88) -> bool:
    """Compare normalized company names, including simple Arabic transliteration."""
    squash = lambda v: re.sub(r"[^a-z0-9]", "", v.casefold())
    a_norm = normalize_company_name(a)
    b_norm = normalize_company_name(b)
    a_has_arabic = bool(re.search(r"[\u0600-\u06ff]", a_norm))
    b_has_arabic = bool(re.search(r"[\u0600-\u06ff]", b_norm))

    candidates_a = {squash(a_norm)}
    candidates_b = {squash(b_norm)}
    if a_has_arabic:
        candidates_a.add(squash(_arabic_to_latin_name(a_norm)))
    if b_has_arabic:
        candidates_b.add(squash(_arabic_to_latin_name(b_norm)))

    # The exporter country is sometimes appended to the name by OCR/extraction
    # even though the document has a separate country field.
    country_suffixes = ("egypt", "algeria", "algerie", "tunisia", "morocco", "china", "india")
    for candidate_set in (candidates_a, candidates_b):
        candidate_set.update(
            candidate[:-len(country)]
            for candidate in list(candidate_set)
            for country in country_suffixes
            if candidate.endswith(country) and len(candidate) > len(country) + 3
        )

    # In Arabic company names, ب commonly stands in for Latin p. If either
    # side is Arabic, compare a b/p-neutral variant as well.
    if a_has_arabic or b_has_arabic:
        candidates_a |= {v.replace("p", "b") for v in list(candidates_a)}
        candidates_a |= {v.replace("b", "p") for v in list(candidates_a)}
        candidates_b |= {v.replace("p", "b") for v in list(candidates_b)}
        candidates_b |= {v.replace("b", "p") for v in list(candidates_b)}

    candidates_a.discard("")
    candidates_b.discard("")
    if not candidates_a or not candidates_b:
        return False
    if candidates_a.intersection(candidates_b):
        return True
    return max(
        SequenceMatcher(None, left, right).ratio()
        for left in candidates_a for right in candidates_b
    ) >= threshold


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
    """Extract a weight and convert it to kilograms."""
    if value is None:
        return None

    text = str(value).strip().lower()
    # "1,234.50" -> "1234.50" (thousands separators)
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)

    match = re.search(
        r"(-?\d+(?:[.,]\d+)?)\s*"
        r"(kgs?|kilograms?|kilos?|grams?|g|lbs?|pounds?|tonnes?|tons?|mt|t)"
        r"(?![a-z])",
        text,
    )

    if not match:
        # The compared fields are explicitly weight fields; many extractors
        # return the numeric value but omit the unit despite the source saying KG.
        numeric = re.fullmatch(r"\s*-?\d+(?:[.,]\d+)?\s*", text)
        if not numeric:
            return None
        return Decimal(text.strip().replace(",", "."))

    amount = Decimal(match.group(1).replace(",", "."))
    unit = match.group(2)

    if unit in {"g", "gram", "grams"}:
        return amount / Decimal("1000")
    if unit in {"lb", "lbs", "pound", "pounds"}:
        return amount * Decimal("0.45359237")
    if unit in {"t", "mt", "tonne", "tonnes", "ton", "tons"}:
        return amount * Decimal("1000")
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
        doc.get("document_type"): (doc.get("fields") or {})
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

        raw = list(values.values())

        if name in ("Exporter / shipper", "Consignee"):
            names = [normalize_company_name(v) for v in raw]
            same = all(names_match(names[0], n) for n in names[1:])
        elif name == "Invoice number":
            ids = {normalize_identifier(v) for v in raw}
            same = len(ids) == 1
        else:
            same = len({normalize(v) for v in raw}) == 1

        if same:
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
            ("certificate_of_conformity", "invoice_number"),
            ("fumigation_certificate", "invoice_number"),
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
            ("phytosanitary_certificate", "exporter_name"),
            ("fumigation_certificate", "exporter_name"),
        ],
    )

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
            ("phytosanitary_certificate", "consignee_name"),
            ("fumigation_certificate", "consignee_name"),
        ],
    )

    # 4. Gross weight
    weight_sources = [
        ("commercial_invoice", "total_gross_weight"),
        ("packing_list", "total_gross_weight"),
        ("bill_of_lading", "total_gross_weight"),
        ("certificate_of_quality", "total_gross_weight"),
        ("phytosanitary_certificate", "total_gross_weight"),
        ("fumigation_certificate", "total_gross_weight"),
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
    for doc_type in (
        "commercial_invoice", "packing_list", "certificate_of_quality",
        "phytosanitary_certificate", "fumigation_certificate",
    ):
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
        ("certificate_of_quality", "package_count"),
        ("phytosanitary_certificate", "package_count"),
        ("fumigation_certificate", "package_count"),
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
    line_amounts = invoice.get("line_item_amounts")
    parsed_line_amounts = [parse_number(v) for v in line_amounts] if isinstance(line_amounts, list) else []
    parsed_line_amounts = [v for v in parsed_line_amounts if v is not None]

    # Many invoices do not print a subtotal field, but do print each line amount
    # and a separate freight charge. Sum the visible line amounts instead.
    arithmetic_base = subtotal
    base_label = "subtotal"
    if arithmetic_base is None and parsed_line_amounts:
        arithmetic_base = sum(parsed_line_amounts, Decimal("0"))
        base_label = "sum_of_line_item_amounts"

    if arithmetic_base is None or total is None:
        add_check(
            "Invoice arithmetic", {}, "needs_review",
            "A readable subtotal (or line-item amounts) and declared total are required."
        )
    else:
        calculated_total = (
            arithmetic_base
            + (freight if freight is not None else Decimal("0"))
            + (insurance if insurance is not None else Decimal("0"))
            + (tax if tax is not None else Decimal("0"))
        )

        values = {
            base_label: str(arithmetic_base),
            "line_item_amounts": [str(v) for v in parsed_line_amounts] if parsed_line_amounts else None,
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
