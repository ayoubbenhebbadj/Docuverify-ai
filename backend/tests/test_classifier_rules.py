import json
from types import SimpleNamespace

from app import document_classifier as dc


def _llm(pages):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason="stop", message=SimpleNamespace(
        content=json.dumps({"pages": pages})))])


def page(n, text):
    return {"page": n, "text": text}


def test_all_titles_matched_means_no_ai_call(monkeypatch):
    def boom(**kw):
        raise AssertionError("the AI must not be called")
    monkeypatch.setattr(dc, "create_with_retry", boom)
    result = dc.classify_document_pages([
        page(1, "COMMERCIAL INVOICE ..."), page(2, "PACKING LIST ..."), page(3, "Phytosanitary Certificate ..."),
    ])
    assert [d["document_type"] for d in result["documents"]] == [
        "commercial_invoice", "packing_list", "phytosanitary_certificate"]


def test_only_undecided_pages_are_sent_with_context(monkeypatch):
    sent = {}

    def fake(**kw):
        sent.update(kw)
        return _llm([{"page": 2, "document_type": "commercial_invoice", "starts_new_document": True,
                      "confidence": 0.9, "evidence": "Invoice No"}])

    monkeypatch.setattr(dc, "create_with_retry", fake)
    result = dc.classify_document_pages([
        page(1, "BILL OF LADING shipper ..."),
        page(2, "Invoice No : 27 Price CFR 1350 USD " * 5),
        page(3, "شهادة مطابقة"),
    ])
    user = sent["messages"][1]["content"]
    assert "Invoice No : 27" in user
    assert "already identified by title as: bill_of_lading" in user
    assert "BILL OF LADING shipper" not in user                 # text of decided pages is not sent
    assert [d["document_type"] for d in result["documents"]] == [
        "bill_of_lading", "commercial_invoice", "certificate_of_conformity"]


def test_empty_pages_are_unknown_without_ai(monkeypatch):
    monkeypatch.setattr(dc, "create_with_retry", lambda **kw: (_ for _ in ()).throw(AssertionError("no AI")))
    result = dc.classify_document_pages([page(1, "Packing List"), page(2, "")])
    assert result["documents"][1]["document_type"] == "unknown"
    assert result["unclassified_pages"] == []                   # empty page is not "unidentified text"


def test_model_may_continue_a_ruled_document(monkeypatch):
    monkeypatch.setattr(dc, "create_with_retry", lambda **kw: _llm([
        {"page": 2, "document_type": "bill_of_lading", "starts_new_document": False,
         "confidence": 0.8, "evidence": "tariff continues B/L"}]))
    result = dc.classify_document_pages([
        page(1, "BILL OF LADING (COPY)"), page(2, "ALGERIA DETENTION TARIFF: BASIC FREE TIME")])
    assert result["documents"][0]["pages"] == [1, 2]
