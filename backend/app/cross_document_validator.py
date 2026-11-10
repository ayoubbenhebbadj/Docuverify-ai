"""Enhanced cross-document validation with multilingual normalization and confidence scoring.

Replaces naive string comparison with field-specific normalization and structured outcomes:
- MATCH: High-confidence equivalence
- POSSIBLE_MATCH: Probable equivalence but needs review
- MISMATCH: Clear contradiction
- INSUFFICIENT_EVIDENCE: Missing or unreliable data
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Optional, Tuple, List
from datetime import date

from app.localization import _, get_language, t, cross_doc_check_label, cross_doc_message
from app.normalization import (
    normalize_company_name, normalize_identifier, parse_weight_kg,
    parse_number, normalize_date, normalize_amount, normalize_currency,
    normalize_weight, normalize_quantity, normalize_country,
    parse_date_flexible, consonant_skeleton, names_match
)


# =============================================================================
# COMPARISON OUTCOMES
# =============================================================================

class ComparisonOutcome:
    # New enriched outcomes
    MATCH = "match"
    POSSIBLE_MATCH = "possible_match"
    MISMATCH = "mismatch"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

    # Legacy mappings for backward compatibility
    PASSED = "passed"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"


def _label(doc_type: str) -> str:
    return str(doc_type).replace("_", " ").capitalize()


# =============================================================================
# FIELD-SPECIFIC COMPARISON FUNCTIONS
# =============================================================================

def compare_identifiers(value_a: str, value_b: str) -> Tuple[str, float, str]:
    """Compare document identifiers (invoice numbers, B/L numbers, etc.)."""
    norm_a = normalize_identifier(value_a)
    norm_b = normalize_identifier(value_b)

    if not norm_a or not norm_b:
        return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, "One or both identifiers are empty"

    if norm_a == norm_b:
        return ComparisonOutcome.MATCH, 1.0, f"Identifiers match exactly: {norm_a}"

    # Check if they're close (e.g., OCR errors)
    similarity = SequenceMatcher(None, norm_a, norm_b).ratio()
    if similarity >= 0.9:
        return ComparisonOutcome.POSSIBLE_MATCH, similarity, f"Identifiers very similar: {norm_a} vs {norm_b}"

    return ComparisonOutcome.MISMATCH, 0.0, f"Identifiers differ: {norm_a} vs {norm_b}"


def compare_companies(value_a: str, value_b: str) -> Tuple[str, float, str]:
    """Compare company names with multilingual normalization."""
    # Use the existing sophisticated names_match but also get a confidence score
    match = names_match(value_a, value_b, threshold=0.88)

    # Get normalized versions for explanation
    norm_a = normalize_company_name(value_a)
    norm_b = normalize_company_name(value_b)

    # Compute similarity for confidence
    similarity = SequenceMatcher(None, norm_a, norm_b).ratio()

    # Also check consonant skeleton
    sk_a = consonant_skeleton(norm_a)
    sk_b = consonant_skeleton(norm_b)
    sk_match = sk_a == sk_b if sk_a and sk_b else False

    if not norm_a or not norm_b:
        return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, "One or both company names are empty"

    if match:
        if similarity >= 0.95 or sk_match:
            return ComparisonOutcome.MATCH, 0.95, f"Company names match: {value_a} ≈ {value_b}"
        else:
            return ComparisonOutcome.POSSIBLE_MATCH, similarity, f"Company names likely match (similarity: {similarity:.2f}): {value_a} ≈ {value_b}"

    return ComparisonOutcome.MISMATCH, similarity, f"Company names differ: {value_a} vs {value_b}"


def compare_dates(value_a: str, value_b: str) -> Tuple[str, float, str]:
    """Compare dates with flexible parsing."""
    date_a = parse_date_flexible(value_a)
    date_b = parse_date_flexible(value_b)

    if not date_a or not date_b:
        return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, f"Could not parse one or both dates: {value_a} vs {value_b}"

    if date_a == date_b:
        return ComparisonOutcome.MATCH, 1.0, f"Dates match: {date_a.isoformat()}"

    # Check if they're close (within a few days - possible OCR error)
    diff = abs((date_a - date_b).days)
    if diff <= 2:
        return ComparisonOutcome.POSSIBLE_MATCH, max(0.7, 1.0 - diff * 0.1), f"Dates very close ({diff} days apart): {date_a} vs {date_b}"

    return ComparisonOutcome.MISMATCH, 0.0, f"Dates differ: {date_a} vs {date_b}"


def compare_amounts(value_a: str, value_b: str) -> Tuple[str, float, str]:
    """Compare monetary amounts."""
    amount_a = parse_amount(value_a)
    amount_b = parse_amount(value_b)

    if amount_a is None or amount_b is None:
        return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, f"Could not parse one or both amounts: {value_a} vs {value_b}"

    if amount_a == amount_b:
        return ComparisonOutcome.MATCH, 1.0, f"Amounts match exactly: {amount_a}"

    # Small difference might be rounding
    diff = abs(amount_a - amount_b)
    if diff <= Decimal("0.01"):
        return ComparisonOutcome.POSSIBLE_MATCH, 0.9, f"Amounts differ by {diff} (possible rounding): {amount_a} vs {amount_b}"

    # Check if relative difference is small
    if amount_a != 0:
        rel_diff = diff / abs(amount_a)
        if rel_diff <= Decimal("0.001"):  # 0.1%
            return ComparisonOutcome.POSSIBLE_MATCH, float(1.0 - float(rel_diff)), f"Amounts very close (rel diff: {rel_diff:.4f}): {amount_a} vs {amount_b}"

    return ComparisonOutcome.MISMATCH, 0.0, f"Amounts differ: {amount_a} vs {amount_b}"


def compare_currencies(value_a: str, value_b: str) -> Tuple[str, float, str]:
    """Compare currency codes."""
    curr_a, _ = normalize_currency(value_a)
    curr_b, _ = normalize_currency(value_b)

    if not curr_a or not curr_b:
        return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, f"Could not determine currency codes: {value_a} vs {value_b}"

    if curr_a == curr_b:
        return ComparisonOutcome.MATCH, 1.0, f"Currencies match: {curr_a}"

    return ComparisonOutcome.MISMATCH, 0.0, f"Currencies differ: {curr_a} vs {curr_b}"


def compare_weights(value_a: str, value_b: str) -> Tuple[str, float, str]:
    """Compare weights in kilograms."""
    kg_a = parse_weight_kg(value_a)
    kg_b = parse_weight_kg(value_b)

    if kg_a is None or kg_b is None:
        return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, f"Could not parse one or both weights: {value_a} vs {value_b}"

    if kg_a == kg_b:
        return ComparisonOutcome.MATCH, 1.0, f"Weights match: {kg_a} kg"

    diff = abs(kg_a - kg_b)
    if diff <= Decimal("0.01"):
        return ComparisonOutcome.MATCH, 1.0, f"Weights match within tolerance: {kg_a} kg vs {kg_b} kg"

    if diff <= Decimal("0.1"):
        return ComparisonOutcome.POSSIBLE_MATCH, 0.8, f"Weights very close ({diff} kg diff): {kg_a} kg vs {kg_b} kg"

    return ComparisonOutcome.MISMATCH, 0.0, f"Weights differ: {kg_a} kg vs {kg_b} kg"


def compare_quantities(value_a: str, value_b: str) -> Tuple[str, float, str]:
    """Compare package counts / quantities."""
    qty_a = parse_quantity(value_a)
    qty_b = parse_quantity(value_b)

    if qty_a is None or qty_b is None:
        return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, f"Could not parse quantities: {value_a} vs {value_b}"

    if qty_a == qty_b:
        return ComparisonOutcome.MATCH, 1.0, f"Quantities match: {qty_a}"

    return ComparisonOutcome.MISMATCH, 0.0, f"Quantities differ: {qty_a} vs {qty_b}"


def compare_countries(value_a: str, value_b: str) -> Tuple[str, float, str]:
    """Compare country names."""
    country_a, _ = normalize_country(value_a)
    country_b, _ = normalize_country(value_b)

    if not country_a or not country_b:
        return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, f"Could not determine country codes: {value_a} vs {value_b}"

    if country_a == country_b:
        return ComparisonOutcome.MATCH, 1.0, f"Countries match: {country_a}"

    return ComparisonOutcome.MISMATCH, 0.0, f"Countries differ: {country_a} vs {country_b}"


# =============================================================================
# FIELD-TO-COMPARER MAPPING
# =============================================================================

COMPARISON_DISPATCH = {
    # Identifiers
    "invoice_number": compare_identifiers,
    "packing_list_number": compare_identifiers,
    "bill_of_lading_number": compare_identifiers,
    "certificate_number": compare_identifiers,
    "booking_number": compare_identifiers,
    "container_numbers": compare_identifiers,
    "seal_numbers": compare_identifiers,
    "customs_declaration_number": compare_identifiers,

    # Company names
    "exporter_name": compare_companies,
    "consignee_name": compare_companies,
    "shipper_name": compare_companies,
    "notify_party": compare_companies,
    "issuer_name": compare_companies,
    "producer_name": compare_companies,
    "issuing_authority": compare_companies,
    "carrier_name": compare_companies,
    "buyer_name": compare_companies,
    "supplier_name": compare_companies,
    "company_name": compare_companies,

    # Dates
    "invoice_date": compare_dates,
    "issue_date": compare_dates,
    "on_board_date": compare_dates,
    "inspection_date": compare_dates,
    "treatment_date": compare_dates,

    # Amounts
    "amount": compare_amounts,
    "total_amount": compare_amounts,
    "subtotal": compare_amounts,
    "freight_and_handling": compare_amounts,
    "insurance_fee": compare_amounts,
    "tax_amount": compare_amounts,
    "line_item_amounts": compare_amounts,
    "calculated_total": compare_amounts,
    "declared_total": compare_amounts,

    # Currency
    "currency": compare_currencies,

    # Weights
    "total_gross_weight": compare_weights,
    "total_net_weight": compare_weights,
    "line_item_gross_weights": compare_weights,
    "line_item_net_weights": compare_weights,
    "package_weight": compare_weights,

    # Quantities
    "total_quantity": compare_quantities,
    "quantity": compare_quantities,
    "package_count": compare_quantities,
    "line_item_package_counts": compare_quantities,

    # Countries
    "country_of_origin": compare_countries,
    "destination_country": compare_countries,
}


# =============================================================================
# MAIN VALIDATION FUNCTION
# =============================================================================

from difflib import SequenceMatcher


def validate_cross_documents(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare extracted fields across documents with enhanced normalization.

    Returns structured comparison results with outcomes, confidence, and explanations.
    """
    by_type = {
        doc.get("document_type"): (doc.get("fields") or {})
        for doc in documents
    }
    unsupported_by_type = {
        doc.get("document_type"): set(doc.get("unsupported_fields") or [])
        for doc in documents
    }

    checks = []

    def add_check(name: str, field_name: str, values: Dict[str, Any],
                  outcome: str, confidence: float, message: str,
                  comparison_method: str = "", ignored: List[str] = None) -> None:
        """Add a comparison check with full metadata."""
        item = {
            "check": name,
            "field": field_name,
            "status": outcome,
            "confidence": round(confidence, 3),
            "values": values,
            "message": message,
            "comparison_method": comparison_method,
        }
        if ignored:
            item["ignored"] = ignored
        checks.append(item)

    def compare_field_values(name: str, field_name: str,
                             field_sources: List[Tuple[str, str]]) -> None:
        """Compare values for a specific field across documents."""
        values = {}

        for doc_type, field_key in field_sources:
            if field_key in unsupported_by_type.get(doc_type, set()):
                continue
            fields = by_type.get(doc_type, {})
            value = fields.get(field_key)
            if value is not None and str(value).strip():
                values[doc_type] = value

        if len(values) < 2:
            add_check(
                name, field_name, values,
                ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0,
                t("Not enough documents contain this field to compare.", "cross_doc_messages"),
                comparison_method="insufficient_data"
            )
            return

        # Use field-specific comparer if available
        comparer = COMPARISON_DISPATCH.get(field_name)
        if comparer:
            # For company names, we need special handling with multiple values
            if field_name in ("exporter_name", "consignee_name", "shipper_name"):
                outcome, confidence, message = compare_companies_multi(values)
                add_check(name, field_name, values, outcome, confidence, message,
                         comparison_method="multilingual_company_matching")
            else:
                # Pairwise comparison for other fields
                doc_types = list(values.keys())
                if len(doc_types) == 2:
                    dt1, dt2 = doc_types[0], doc_types[1]
                    outcome, confidence, message = comparer(values[dt1], values[dt2])
                    add_check(name, field_name, values, outcome, confidence, message,
                             comparison_method=comparer.__name__)
                else:
                    # Multiple documents - compare all pairs
                    outcomes = []
                    for i, dt1 in enumerate(doc_types):
                        for dt2 in doc_types[i+1:]:
                            o, c, m = comparer(values[dt1], values[dt2])
                            outcomes.append((o, c, m, dt1, dt2))

                    # Aggregate: if any MISMATCH -> MISMATCH, if all MATCH -> MATCH, etc.
                    if any(o == ComparisonOutcome.MISMATCH for o, _, _, _, _ in outcomes):
                        outcome = ComparisonOutcome.MISMATCH
                    elif all(o == ComparisonOutcome.MATCH for o, _, _, _, _ in outcomes):
                        outcome = ComparisonOutcome.MATCH
                    elif any(o == ComparisonOutcome.POSSIBLE_MATCH for o, _, _, _, _ in outcomes):
                        outcome = ComparisonOutcome.POSSIBLE_MATCH
                    else:
                        outcome = ComparisonOutcome.INSUFFICIENT_EVIDENCE

                    confidence = sum(c for _, c, _, _, _ in outcomes) / len(outcomes) if outcomes else 0.0
                    message = "; ".join(f"{_label(dt1)} vs {_label(dt2)}: {m}" for _, _, m, dt1, dt2 in outcomes)
                    add_check(name, field_name, values, outcome, confidence, message,
                             comparison_method=comparer.__name__)
        else:
            # Default: simple string normalization comparison
            norm_values = {dt: normalize_text(v) for dt, v in values.items()}
            unique = set(norm_values.values())

            if len(unique) == 1:
                add_check(name, field_name, values,
                         ComparisonOutcome.MATCH, 1.0,
                         t("Values match.", "cross_doc_messages"),
                         comparison_method="normalized_string")
            else:
                add_check(name, field_name, values,
                         ComparisonOutcome.MISMATCH, 0.0,
                         t("Documents disagree: ", "cross_doc_messages") +
                         " vs ".join(f"{_label(d)} ({v})" for d, v in values.items()) + ".",
                         comparison_method="normalized_string")


    def compare_companies_multi(values: Dict[str, str]) -> Tuple[str, float, str]:
        """Compare company names across multiple documents."""
        # Group by identity using names_match
        address_docs = {d: v for d, v in values.items() if looks_like_address(strip_address_suffix(v))}
        usable = {d: v for d, v in values.items() if d not in address_docs}

        if not usable or len(usable) < 2:
            return ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0, "Not enough usable company names"

        # Build identity groups
        groups = []
        for doc_type, value in usable.items():
            cleaned = normalize_company_name(value)
            matched = False
            for group in groups:
                if names_match(normalize_company_name(usable[group[0]]), cleaned):
                    group.append(doc_type)
                    matched = True
                    break
            if not matched:
                groups.append([doc_type])

        if len(groups) == 1:
            if address_docs:
                address_note = f"{', '.join(_label(d) for d in address_docs)}: address not company name. "
                # Address fragment is an extraction problem, not a company mismatch
                return ComparisonOutcome.NEEDS_REVIEW, 0.5, address_note + "All company names match"
            else:
                address_note = ""
                # Return legacy status for backward compatibility
                return ComparisonOutcome.PASSED, 0.95, address_note + "All company names match"

        # Multiple groups - find majority
        groups.sort(key=len, reverse=True)
        if len(groups[0]) > len(groups[1]):
            odd = [d for g in groups[1:] for d in g]
            detail = "; ".join(f"{_label(d)} ({usable[d]})" for d in odd)
            return ComparisonOutcome.FAILED, 0.0, f"Majority disagrees with: {detail}"
        else:
            message = "Documents disagree: " + " vs ".join(
                ", ".join(_label(d) for d in g) for g in groups) + "."
            return ComparisonOutcome.FAILED, 0.0, message

    # =========================================================================
    # COMPARISON CHECKS
    # =========================================================================

    # 1. Invoice number
    compare_field_values(
        "Invoice number", "invoice_number",
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
    compare_field_values(
        "Exporter / shipper", "exporter_name",
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
    compare_field_values(
        "Consignee", "consignee_name",
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
    ignored_gross = []
    for doc_type, field_name in weight_sources:
        if field_name in unsupported_by_type.get(doc_type, set()):
            ignored_gross.append(doc_type)
            continue
        value = by_type.get(doc_type, {}).get(field_name)
        if value is not None:
            parsed = parse_weight_kg(value)
            if parsed is not None:
                weights[doc_type] = parsed

    if ignored_gross:
        ignored_labels = ", ".join(_label(d) for d in ignored_gross)
        add_check(
            t("Gross weight", "cross_doc_checks"), "total_gross_weight",
            weights, ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0,
            f"{ignored_labels}: {t('gross weight was not found in the document and was excluded from comparison.', 'cross_doc_messages')}",
            comparison_method="weight_kg", ignored=ignored_gross
        )
    elif len(weights) < 2:
        add_check(
            t("Gross weight", "cross_doc_checks"), "total_gross_weight",
            weights, ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0,
            t("Not enough readable gross weights to compare.", "cross_doc_messages"),
            comparison_method="weight_kg"
        )
    else:
        # Use the field comparer
        compare_field_values(t("Gross weight", "cross_doc_checks"), "total_gross_weight",
                           [(dt, "total_gross_weight") for dt in weights.keys()])

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

    if len(net_weights) >= 2:
        compare_field_values(t("Net weight", "cross_doc_checks"), "total_net_weight",
                           [(dt, "total_net_weight") for dt in net_weights.keys()])
    else:
        add_check(
            t("Net weight", "cross_doc_checks"), "total_net_weight",
            net_weights, ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0,
            t("Not enough readable net weights to compare.", "cross_doc_messages"),
            comparison_method="weight_kg"
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
        if value is not None:
            match = re.search(r"\d+", str(value))
            if match:
                package_values[doc_type] = int(match.group())

    if len(package_values) >= 2:
        compare_field_values(t("Package count", "cross_doc_checks"), "package_count",
                           [(dt, "package_count") for dt in package_values.keys()])
    else:
        add_check(
            t("Package count", "cross_doc_checks"), "package_count",
            package_values, ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0,
            t("Not enough package counts to compare.", "cross_doc_messages"),
            comparison_method="quantity"
        )

    # 7. Invoice arithmetic (special case - internal consistency)
    invoice = by_type.get("commercial_invoice", {})

    subtotal = parse_number(invoice.get("subtotal"))
    freight = parse_number(invoice.get("freight_and_handling"))
    insurance = parse_number(invoice.get("insurance_fee"))
    tax = parse_number(invoice.get("tax_amount"))
    total = parse_number(invoice.get("total_amount"))
    line_amounts = invoice.get("line_item_amounts")
    parsed_line_amounts = [parse_number(v) for v in line_amounts] if isinstance(line_amounts, list) else []
    parsed_line_amounts = [v for v in parsed_line_amounts if v is not None]

    arithmetic_base = subtotal
    base_label = "subtotal"
    if arithmetic_base is None and parsed_line_amounts:
        arithmetic_base = sum(parsed_line_amounts, Decimal("0"))
        base_label = "sum_of_line_item_amounts"

    if arithmetic_base is None or total is None:
        add_check(
            t("Invoice arithmetic", "cross_doc_checks"), "invoice_arithmetic",
            {}, ComparisonOutcome.INSUFFICIENT_EVIDENCE, 0.0,
            t("A readable subtotal (or line-item amounts) and declared total are required.", "cross_doc_messages"),
            comparison_method="arithmetic"
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
                t("Invoice arithmetic", "cross_doc_checks"), "invoice_arithmetic",
                values, ComparisonOutcome.MATCH, 1.0,
                t("The calculated total matches the declared total.", "cross_doc_messages"),
                comparison_method="arithmetic"
            )
        else:
            diff = abs(calculated_total - total)
            if diff <= Decimal("0.01"):
                outcome = ComparisonOutcome.POSSIBLE_MATCH
                confidence = 0.9
            else:
                outcome = ComparisonOutcome.MISMATCH
                confidence = 0.0
            add_check(
                t("Invoice arithmetic", "cross_doc_checks"), "invoice_arithmetic",
                values, outcome, confidence,
                t("The calculated total does not match the declared total.", "cross_doc_messages"),
                comparison_method="arithmetic"
            )

    # Summary with new outcome types
    summary = {
        "total_checks": len(checks),
        "match": sum(c["status"] in (ComparisonOutcome.MATCH, ComparisonOutcome.PASSED) for c in checks),
        "possible_match": sum(c["status"] == ComparisonOutcome.POSSIBLE_MATCH for c in checks),
        "mismatch": sum(c["status"] in (ComparisonOutcome.MISMATCH, ComparisonOutcome.FAILED) for c in checks),
        "insufficient_evidence": sum(c["status"] == ComparisonOutcome.INSUFFICIENT_EVIDENCE for c in checks),
        # Legacy fields for backward compatibility
        "passed": sum(c["status"] in (ComparisonOutcome.MATCH, ComparisonOutcome.PASSED) for c in checks),
        "mismatches": sum(c["status"] in (ComparisonOutcome.MISMATCH, ComparisonOutcome.FAILED) for c in checks),
        "needs_review": sum(c["status"] in (ComparisonOutcome.POSSIBLE_MATCH, ComparisonOutcome.INSUFFICIENT_EVIDENCE) for c in checks),
    }

    return {
        "summary": summary,
        "checks": checks,
    }


# =============================================================================
# HELPER FUNCTIONS (duplicated from normalization for backward compatibility)
# =============================================================================

def normalize_text(value):
    """Normalize text for reliable comparisons."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[.,;:]+$", "", text)
    return text


def looks_like_address(value) -> bool:
    """True when the value is an address fragment rather than a company name."""
    if value is None:
        return False
    tokens = [t.casefold() for t in re.split(r"[\s.,،;:/\-]+", str(value)) if t]
    # Use the same address words from normalization
    from app.normalization import _ADDRESS_INDICATORS
    hits = sum(1 for t in tokens if t in _ADDRESS_INDICATORS)
    rest = [
        t for t in tokens
        if t not in _ADDRESS_INDICATORS and not any(c.isdigit() for c in t)
        and not (len(t) == 1 and re.search(r"[؀-ۿ]", t))
    ]
    return hits >= 2 and (not rest or hits >= 3)


def strip_address_suffix(value):
    """Strip address suffix from company name."""
    if not value:
        return value
    tokens = str(value).split()

    from app.normalization import _ADDRESS_INDICATORS, _LEGAL_SUFFIXES

    def is_addr(tok):
        t = tok.casefold().strip(".,;:()")
        return t in _ADDRESS_INDICATORS or t.startswith("nif") or any(c.isdigit() for c in t)

    # Everything after a trailing legal form ("... CO.,LTD TIANJIN FREE TRADE ZONE ...") is address.
    for i, tok in enumerate(tokens[:-1]):
        flat = re.sub(r"[^a-z0-9]", "", tok.casefold())
        if i >= 1 and flat in _LEGAL_SUFFIXES:
            return " ".join(tokens[: i + 1])

    for i in range(1, len(tokens)):
        t = tokens[i].casefold().strip(".,;:()")
        if (t in _ADDRESS_INDICATORS or t.startswith("nif")) and \
                sum(is_addr(x) for x in tokens[i:]) >= 2:
            return " ".join(tokens[:i])
    return value