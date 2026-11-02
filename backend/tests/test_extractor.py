import json
from types import SimpleNamespace

import pytest

from app import document_extractor as de

PAGE = {"page": 8, "text": "Invoice No : 27\nDate : 30/ 06/2026\nTotal 87185 USD\nTo : BIOPPAM SARL"}


def _reply(payload, finish="stop"):
    content = payload if isinstance(payload, str) else json.dumps(payload)
    return SimpleNamespace(
        choices=[SimpleNamespace(finish_reason=finish, message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
    )


def test_code_mode_prompt_has_no_evidence_and_values_are_grounded(monkeypatch):
    captured = {}

    def fake(**kw):
        captured.update(kw)
        return _reply({"document_type": "commercial_invoice", "fields": {
            "invoice_number": "27", "invoice_date": "2026-06-30", "total_amount": 87185,
            "currency": "USD", "consignee_name": "BIOPPAM SARL", "buyer_name": "Invented Ltd",
        }})

    monkeypatch.setattr(de, "create_with_retry", fake)
    out = de.extract_typed_document("commercial_invoice", [PAGE])
    system = captured["messages"][0]["content"]
    assert '"evidence"' not in system and "Never translate" in system
    assert "extra_body" not in captured                      # handled centrally now
    assert out["evidence"]["invoice_date"] == "Date : 30/ 06/2026"
    assert out["evidence"]["total_amount"] == "Total 87185 USD"
    assert out["evidence"]["buyer_name"] is None             # not in the text -> flagged later
    assert out["fields"]["buyer_name"] == "Invented Ltd"


def test_model_mode_keeps_model_quotes(monkeypatch):
    monkeypatch.setenv("EXTRACTION_EVIDENCE", "model")
    monkeypatch.setattr(de, "create_with_retry", lambda **kw: _reply({
        "document_type": "commercial_invoice",
        "fields": {"invoice_number": "27"}, "evidence": {"invoice_number": "Invoice No : 27"},
    }))
    out = de.extract_typed_document("commercial_invoice", [PAGE])
    assert out["evidence"]["invoice_number"] == "Invoice No : 27"


def test_bad_json_is_retried_once(monkeypatch):
    answers = iter([_reply("not json at all"), _reply({"fields": {"invoice_number": "27"}})])
    monkeypatch.setattr(de, "create_with_retry", lambda **kw: next(answers))
    out = de.extract_typed_document("commercial_invoice", [PAGE])
    assert out["fields"]["invoice_number"] == "27"


def test_two_bad_answers_raise(monkeypatch):
    monkeypatch.setattr(de, "create_with_retry", lambda **kw: _reply("nope"))
    with pytest.raises(ValueError):
        de.extract_typed_document("commercial_invoice", [PAGE])


def test_truncation_is_not_retried(monkeypatch):
    calls = []
    monkeypatch.setattr(de, "create_with_retry", lambda **kw: calls.append(1) or _reply("{}", "length"))
    with pytest.raises(ValueError, match="truncated"):
        de.extract_typed_document("commercial_invoice", [PAGE])
    assert len(calls) == 1
