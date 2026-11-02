"""Document totals computed in code from line items.

Many invoices and packing lists print a weight (and a package count) on every
line but never a grand total.  If the model is asked for "the total" it adds the
numbers up itself, and language models add badly and differently on every run:
the same invoice produced a gross weight of 24667 kg in one run, 24652 kg in
the next, and 27667 kg is correct.  That false disagreement then made four
correct documents look wrong.

So the model only transcribes the per-line values, and this module sums them
exactly.  A total that the document really prints is kept as printed (and
cross-checked against the sum of its lines).
"""
from __future__ import annotations

import re
from decimal import Decimal

from app.cross_document_validator import parse_weight_kg

# (total field, per-line field, kind)
DERIVATIONS = [
    ("total_gross_weight", "line_item_gross_weights", "weight"),
    ("total_net_weight", "line_item_net_weights", "weight"),
    ("package_count", "line_item_package_counts", "count"),
]

FIELD_LABELS = {
    "total_gross_weight": "gross weight",
    "total_net_weight": "net weight",
    "package_count": "package count",
}


def _parse(kind: str, value) -> Decimal | None:
    if kind == "weight":
        return parse_weight_kg(value)
    match = re.search(r"\d+", str(value))
    return Decimal(match.group()) if match else None


def _fmt(kind: str, amount: Decimal) -> str:
    text = format(amount.normalize(), "f")
    return f"{text} KG" if kind == "weight" else text


def _is_grounded(evidence: dict, field: str, fields: dict) -> bool:
    return fields.get(field) is not None and bool(evidence.get(field))


def derive_totals(fields: dict, evidence: dict) -> dict:
    """Fill / verify total fields from their per-line lists.

    Returns ``{"fields", "evidence", "derived_fields", "warnings"}``; the inputs
    are not modified.
    """
    fields, evidence = dict(fields), dict(evidence)
    derived: list[str] = []
    warnings: list[str] = []

    for total_field, line_field, kind in DERIVATIONS:
        lines = fields.get(line_field)
        if not isinstance(lines, list) or not lines:
            continue
        # Never sum lines the document does not actually contain.
        if not evidence.get(line_field):
            continue

        parsed = [_parse(kind, v) for v in lines]
        if any(p is None for p in parsed):
            continue  # a line we cannot read: do not guess a total

        total = sum(parsed, Decimal("0"))
        printed_ok = _is_grounded(evidence, total_field, fields)

        if printed_ok:
            printed = _parse(kind, fields[total_field])
            if printed is not None and abs(printed - total) > Decimal("0.01"):
                warnings.append(
                    f"The printed total {FIELD_LABELS[total_field]} ({fields[total_field]}) differs from the "
                    f"sum of its {len(parsed)} line items ({_fmt(kind, total)})."
                )
            continue

        # No printed total in the document (or the model's number is not in the
        # text, i.e. it added the lines itself): use the exact sum.
        fields[total_field] = _fmt(kind, total)
        quotes = evidence[line_field]
        evidence[total_field] = quotes if isinstance(quotes, list) else [quotes]
        derived.append(total_field)

    return {"fields": fields, "evidence": evidence, "derived_fields": derived, "warnings": warnings}
