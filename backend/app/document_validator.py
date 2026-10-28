
import re
from difflib import SequenceMatcher
from datetime import date
from decimal import Decimal, InvalidOperation
import unicodedata

# Initial required-field rules.
# We can refine these as we establish your company's requirements.
REQUIRED_FIELDS = {
    
    "certificate_of_quality": [
        "certificate_number",
        "issuer_name",
        "goods_description",
    ],

    "certificate_of_conformity": [
        "certificate_number",
        "issuer_name",
        "goods_description",
        "conformity_status",
    ],

    "phytosanitary_certificate": [
        "certificate_number",
        "exporter_name",
        "consignee_name",
        "country_of_origin",
        "goods_description",
    ],

    "fumigation_certificate": [
        "certificate_number",
        "goods_description",
        "fumigant",
        "treatment_date",
    ],
    "commercial_invoice": [
        "exporter_name",
        "consignee_name",
        "invoice_number",
        "invoice_date",
        "currency",
        "total_amount",
    ],
    "packing_list": [
        "exporter_name",
        "consignee_name",
        "packing_list_number",
        "package_count",
        "total_gross_weight",
    ],
    "bill_of_lading": [
        "bill_of_lading_number",
        "shipper_name",
        "consignee_name",
        "carrier_name",
    ],
    "certificate_of_origin": [
        "certificate_number",
        "exporter_name",
        "country_of_origin",
        "goods_description",
    ],
}

DATE_FIELDS = {
    "invoice_date",
    "issue_date",
    "on_board_date",
    "inspection_date",
    "treatment_date",

}

MONEY_FIELDS = {
    "subtotal",
    "freight_and_handling",
    "insurance_fee",
    "tax_amount",
    "total_amount",
}

WEIGHT_FIELDS = {
    "total_net_weight",
    "total_gross_weight",
}

IDENTIFIER_FIELDS = {
    "invoice_number",
    "packing_list_number",
    "bill_of_lading_number",
    "certificate_number",
    "booking_number",
}


def normalize_text(value: str) -> str:
    """Normalize Unicode, whitespace, and common punctuation differences."""
    value = unicodedata.normalize("NFKC", value).casefold()

    # Normalize common typographic punctuation.
    value = (
        value.replace("–", "-")
        .replace("—", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    # Treat line breaks and repeated spaces consistently.
    value = re.sub(r"\s+", " ", value)

    # Ignore whitespace around punctuation.
    value = re.sub(r"\s*([,.;:/()\-])\s*", r"\1", value)

    return value.strip()





def fuzzy_contains(quote: str, source: str, threshold: float) -> bool:
    """True if `quote` appears in `source` allowing OCR-style character errors.

    Both strings must already be normalised.  A sliding window of about the
    quote's length is compared with difflib; short quotes are never matched
    fuzzily because a few wrong characters would change their meaning.
    """
    size = len(quote)
    if size < 8 or not source:
        return False

    # Numbers are what the validator exists to protect: every number in the
    # quote must appear exactly in the source (treating O/0 and I/l/1 as the
    # same glyph, the classic OCR confusion).  Only words may differ fuzzily.
    glyphs = str.maketrans("oOlI", "0011")
    folded_source = source.translate(glyphs)
    for number in re.findall(r"\d+", quote.translate(glyphs)):
        if number not in folded_source:
            return False

    matcher = SequenceMatcher(None, autojunk=False)
    matcher.set_seq2(quote)
    step = max(1, size // 16)

    for width in {size, max(1, int(size * 0.9)), int(size * 1.1) + 1}:
        for start in range(0, max(len(source) - width, 0) + 1, step):
            matcher.set_seq1(source[start:start + width])
            if (
                matcher.real_quick_ratio() >= threshold
                and matcher.quick_ratio() >= threshold
                and matcher.ratio() >= threshold
            ):
                return True

    return False


def evidence_matches(
    evidence_value,
    source_text: str,
    fuzzy_threshold: float | None = None,
) -> bool:
    """Check whether evidence quotations are supported by the source text.

    Pass `fuzzy_threshold` (e.g. 0.85) for OCR text so that small recognition
    errors do not make a correct quotation look unsupported.
    """
    if not isinstance(source_text, str) or not source_text.strip():
        return False

    if isinstance(evidence_value, str):
        quotations = [evidence_value]
    elif isinstance(evidence_value, list):
        quotations = evidence_value
    else:
        return False

    normalized_source = normalize_text(source_text)

    for quotation in quotations:
        if not isinstance(quotation, str) or not quotation.strip():
            continue

        normalized_quote = normalize_text(quotation)

        # 1. Exact match after Unicode, whitespace, and punctuation normalization.
        if normalized_quote and normalized_quote in normalized_source:
            return True

        # 2. Check meaningful lines from multiline evidence.
        lines = [
            normalize_text(line)
            for line in quotation.splitlines()
            if line.strip()
        ]

        meaningful_lines = [
            line for line in lines
            if len(line) >= 12
        ]

        if meaningful_lines and all(
            line in normalized_source for line in meaningful_lines
        ):
            return True

        # 3. Check separate product descriptions joined with semicolons.
        parts = [
            normalize_text(part)
            for part in quotation.split(";")
            if part.strip()
        ]

        if len(parts) > 1 and all(
            part in normalized_source for part in parts
        ):
            return True

        # 4. Support shortened quotations containing an ellipsis.
        # Every non-empty segment must occur in the source.
        if "..." in quotation or "…" in quotation:
            segments = re.split(r"\.{3,}|…", quotation)
            segments = [
                normalize_text(segment)
                for segment in segments
                if len(normalize_text(segment)) >= 8
            ]

            if len(segments) >= 2 and all(
                segment in normalized_source for segment in segments
            ):
                return True

        # 5. OCR text: tolerate a few misread characters.
        if fuzzy_threshold and fuzzy_contains(
            normalized_quote, normalized_source, fuzzy_threshold
        ):
            return True

    return False




def parse_decimal(value):
    """Parse a numeric value without silently accepting arbitrary text."""
    if isinstance(value, bool) or value is None:
        return None

    try:
        if isinstance(value, (int, float, Decimal)):
            result = Decimal(str(value))
        elif isinstance(value, str):
            cleaned = value.strip().replace(",", "")
            result = Decimal(cleaned)
        else:
            return None

        if not result.is_finite():
            return None

        return result

    except (InvalidOperation, ValueError):
        return None


def validate_document(
    extraction: dict,
    source_text: str,
    ocr_used: bool = False,
) -> dict:
    document_type = extraction.get("document_type")
    fields = extraction.get("fields")
    evidence = extraction.get("evidence")

    if document_type not in REQUIRED_FIELDS:
        return {
            "status": "needs_review",
            "missing_fields": [],
            "invalid_fields": [],
            "unsupported_evidence": [],
            "warnings": [
                f"Unsupported document type: {document_type}"
            ],
        }

    if not isinstance(fields, dict):
        return {
            "status": "needs_review",
            "missing_fields": REQUIRED_FIELDS[document_type],
            "invalid_fields": [],
            "unsupported_evidence": [],
            "warnings": ["The extracted fields object is missing or invalid."],
        }

    if not isinstance(evidence, dict):
        evidence = {}

    missing_fields = []
    invalid_fields = []
    unsupported_evidence = []
    warnings = []

    # OCR output may contain small recognition errors.
    fuzzy_threshold = 0.85 if ocr_used else None

    # 1. Required fields must be present and non-empty.
    for field in REQUIRED_FIELDS[document_type]:
        value = fields.get(field)

        if value is None or (
            isinstance(value, str) and not value.strip()
        ) or value == []:
            missing_fields.append(field)

    # 2. Validate field formats.
    for field, value in fields.items():
        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            invalid_fields.append({
                "field": field,
                "reason": "Value is an empty string.",
            })
            continue

        if field in DATE_FIELDS:
            if not isinstance(value, str):
                invalid_fields.append({
                    "field": field,
                    "reason": "Date must be a YYYY-MM-DD string.",
                })
            else:
                try:
                    parsed_date = date.fromisoformat(value)
                    if parsed_date.isoformat() != value:
                        raise ValueError("Date is not canonical ISO format.")
                except ValueError:
                    invalid_fields.append({
                        "field": field,
                        "reason": "Invalid date; expected YYYY-MM-DD.",
                    })

        elif field in MONEY_FIELDS:
            number = parse_decimal(value)

            if number is None or number < 0:
                invalid_fields.append({
                    "field": field,
                    "reason": "Expected a non-negative numeric amount.",
                })

        elif field == "currency":
            if not isinstance(value, str) or not re.fullmatch(
                r"[A-Za-z]{3}", value.strip()
            ):
                invalid_fields.append({
                    "field": field,
                    "reason": "Expected a three-letter currency code.",
                })

        elif field in WEIGHT_FIELDS:
            if not isinstance(value, str) or not re.search(
                r"(?<![A-Za-z])(?:kgs?|kilograms?|g|grams?|lbs?|pounds?|"
                r"tonnes?|tons?|mt|t)(?![A-Za-z])",
                value,
                re.IGNORECASE,
            ):
                invalid_fields.append({
                    "field": field,
                    "reason": "Weight must include a recognizable unit.",
                })

        elif field == "package_count":
            # Package counts may be represented as a number or text
            # such as "3 PALLETS". Do not confuse pieces with packages.
            if isinstance(value, bool) or not isinstance(
                value, (str, int, float)
            ):
                invalid_fields.append({
                    "field": field,
                    "reason": "Expected a package count or package description.",
                })
            elif isinstance(value, (int, float)) and (
                value <= 0 or int(value) != value
            ):
                invalid_fields.append({
                    "field": field,
                    "reason": "Numeric package count must be a positive integer.",
                })
            elif isinstance(value, str) and not value.strip():
                invalid_fields.append({
                    "field": field,
                    "reason": "Package description is empty.",
                })

        elif field in IDENTIFIER_FIELDS:
            if not isinstance(value, str) or not value.strip():
                invalid_fields.append({
                    "field": field,
                    "reason": "Expected a non-empty identifier string.",
                })

    # 3. Check that non-null extracted fields have source evidence.
    for field, value in fields.items():
        if value is None:
            continue

        quotation = evidence.get(field)

        if evidence_matches(quotation, source_text, fuzzy_threshold):
            continue

        # PDF table extraction may separate a numeric value from its
        # column header. Accept this only when both are independently
        # present in the source text.
        if field in {"total_gross_weight", "total_net_weight"}:
            value_text = str(value)

            numeric_match = re.search(
                r"-?\d+(?:[.,]\d+)?",
                value_text,
            )

            if numeric_match:
                numeric_value = numeric_match.group()

                has_value = evidence_matches(
                    numeric_value,
                    source_text,
                )

                if field == "total_gross_weight":
                    header_pattern = r"\b(?:GROSS\s+WT|GROSS\s+WEIGHT)\b"
                else:
                    header_pattern = r"\b(?:NET\s+WT|NET\s+WEIGHT)\b"

                has_header = bool(
                    re.search(
                        header_pattern,
                        source_text,
                        re.IGNORECASE,
                    )
                )

                if has_value and has_header:
                    continue

        unsupported_evidence.append(field)



    if unsupported_evidence:
        warnings.append(
            "Some extracted values could not be matched to their "
            "provided evidence quotations in the source text."
        )

    if missing_fields:
        warnings.append("One or more required fields are missing.")

    if invalid_fields:
        warnings.append("One or more fields failed format validation.")

    # Evidence problems are review flags, not proof that the value is false.
    status = (
        "needs_review"
        if missing_fields
        or invalid_fields
        or unsupported_evidence
        else "complete"
    )

    return {
        "status": status,
        "missing_fields": missing_fields,
        "invalid_fields": invalid_fields,
        "unsupported_evidence": unsupported_evidence,
        "warnings": warnings,
    }
