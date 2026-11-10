"""The Egyptian invoice prints weights per line but no total.  Run 1 of the real
pipeline reported gross 24667, run 2 reported 24652; the correct sum is 27667."""
import json
from types import SimpleNamespace

from app import document_extractor as de
from app.cross_document_validator import validate_cross_documents
from app.derive import derive_totals

INVOICE_TEXT = """Invoice No : 27
THYME ((ORIGANO) LOT NO : Z26
Packed in ( 340 )Bags Of ( 25 ) kg Net Weight
G.W :8534 KG
N.W : 8500 KG
HIBISCUS LOT NO :Z31
G.W :2008 KG
N.W : 2000 KG
SAGE LOT NO : Z27
G.W :5050 KG
N.W : 5000 KG
DRIED LEMON LOT NO :Z28
G.W :3030 KG
N.W : 3000 KG
GELERY LOT N0 : Z29
G. W : 3015
N,W : 3000
GUM ARABIC (RESIN) LOT NO : Z30
G.W :3015 KG
N.W : 3000 KG
WHEAT GRAIN ( MAHALEB) LOT NO Z32
G.W :3015 KG
N.W : 3000 KG
Grand Total 87185 USD
"""
GROSS = ["8534 KG", "2008 KG", "5050 KG", "3030 KG", "3015 KG", "3015 KG", "3015 KG"]
NET = ["8500 KG", "2000 KG", "5000 KG", "3000 KG", "3000 KG", "3000 KG", "3000 KG"]
PACKS = ["340", "80", "250", "300", "150", "60", "75"]


def _reply(payload):
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=json.dumps(payload)))],
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1))


def test_model_arithmetic_is_replaced_by_the_exact_sum(monkeypatch):
    # Package count lines are not all present in this text on purpose (80, 250...): only weights here.
    monkeypatch.setattr(de, "create_with_retry", lambda **kw: _reply({"fields": {
        "invoice_number": "27",
        "total_gross_weight": "24667 KG",          # the model added the lines wrongly
        "total_net_weight": "24500 KG",
        "line_item_gross_weights": GROSS,
        "line_item_net_weights": NET,
    }}))
    out = de.extract_typed_document("commercial_invoice", [{"page": 8, "text": INVOICE_TEXT}])
    assert out["fields"]["total_gross_weight"] == "27667 KG"
    assert out["fields"]["total_net_weight"] == "27500 KG"
    assert set(out["derived_fields"]) == {"total_gross_weight", "total_net_weight"}
    assert out["evidence"]["total_gross_weight"]            # grounded in the line quotes


def test_result_is_identical_whatever_the_model_guesses(monkeypatch):
    totals = set()
    for wrong in ("24667 KG", "24652 KG", "30000 KG", None):
        monkeypatch.setattr(de, "create_with_retry", lambda wrong=wrong, **kw: _reply({"fields": {
            "total_gross_weight": wrong, "line_item_gross_weights": GROSS}}))
        out = de.extract_typed_document("commercial_invoice", [{"page": 8, "text": INVOICE_TEXT}])
        totals.add(out["fields"]["total_gross_weight"])
    assert totals == {"27667 KG"}


def test_a_printed_total_is_kept_and_checked_against_its_lines():
    fields = {"total_gross_weight": "27667 KG", "line_item_gross_weights": GROSS}
    ev = {"total_gross_weight": "TOTAL G.W : 27667 KG", "line_item_gross_weights": ["g"] * 7}
    out = derive_totals(fields, ev)
    assert out["derived_fields"] == [] and out["warnings"] == []

    fields["total_gross_weight"] = "27000 KG"
    out = derive_totals(fields, ev)
    assert out["fields"]["total_gross_weight"] == "27000 KG"       # not overwritten
    assert "differs from the sum" in out["warnings"][0] and "27667" in out["warnings"][0]


def test_package_counts_are_summed_too():
    out = derive_totals({"package_count": "1250", "line_item_package_counts": PACKS},
                        {"package_count": None, "line_item_package_counts": ["x"] * 7})
    assert out["fields"]["package_count"] == "1255"


def test_no_total_is_invented_from_lines_that_are_not_in_the_document():
    out = derive_totals({"total_gross_weight": None, "line_item_gross_weights": GROSS},
                        {"line_item_gross_weights": None})        # lines not found in the text
    assert out["fields"]["total_gross_weight"] is None


def test_an_unreadable_line_blocks_the_total():
    out = derive_totals({"total_gross_weight": None, "line_item_gross_weights": ["8534 KG", "heavy"]},
                        {"line_item_gross_weights": ["x", "y"]})
    assert out["fields"]["total_gross_weight"] is None


def test_mixed_units_are_converted():
    out = derive_totals({"line_item_net_weights": ["1.5 tons", "500 kg"], "total_net_weight": None},
                        {"line_item_net_weights": ["x"]})
    assert out["fields"]["total_net_weight"] == "2000 KG"


# ---- cross-check ---------------------------------------------------------

def _docs(invoice_gross, unsupported=()):
    return [
        {"document_type": "commercial_invoice", "fields": {"total_gross_weight": invoice_gross},
         "unsupported_fields": list(unsupported)},
        {"document_type": "packing_list", "fields": {"total_gross_weight": "27667 KG"}},
        {"document_type": "certificate_of_quality", "fields": {"total_gross_weight": "27667"}},
        {"document_type": "fumigation_certificate", "fields": {"total_gross_weight": "27667 KG"}},
    ]


def _check(docs, name="Gross weight"):
    return next(c for c in validate_cross_documents(docs)["checks"] if c["check"] == name)


def test_value_not_found_in_its_document_is_not_compared_as_a_fact():
    check = _check(_docs("24667 KG", unsupported=["total_gross_weight"]))
    assert check["status"] == "insufficient_evidence"                       # not a false "mismatch"
    assert "commercial_invoice" in check["ignored"]
    assert "Commercial invoice" in check["message"] and "not found" in check["message"]


def test_a_real_discrepancy_is_still_a_mismatch():
    assert _check(_docs("24667 KG"))["status"] == "mismatch"      # printed and found: a true difference


def test_agreeing_documents_pass_cleanly():
    check = _check(_docs("27667 KG"))
    assert check["status"] == "match" and "ignored" not in check
