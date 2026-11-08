import threading
import time

from app import main


def _pdf_result(texts):
    pages = [{"page": i, "text": t, "ocr_used": False} for i, t in enumerate(texts, start=1)]
    return {"page_count": len(pages), "pages": pages, "has_text": True, "extracted_text": "\n".join(texts),
            "pages_low_confidence": [], "pages_needing_ocr": [], "pages_vision_ocr_used": [], "ocr_errors": []}


def _wire(monkeypatch, texts, types, extractor):
    monkeypatch.setattr(main, "extract_pdf_text", lambda b: _pdf_result(texts))
    monkeypatch.setattr(main, "recover_uncertain_pages", lambda b, r: r)
    monkeypatch.setattr(main, "classify_document_pages", lambda pages: {
        "documents": [{"document_type": t, "pages": [i], "confidence": 0.9} for i, t in enumerate(types, start=1)],
        "documents_found": len(types), "missing_documents": [], "unclassified_pages": []})
    monkeypatch.setattr(main, "extract_typed_document", extractor)


def _extraction(document_type, pages, ocr_used=False):
    return {"document_type": document_type, "fields": {"invoice_number": "27"}, "evidence": {}}


def test_longest_document_is_submitted_first_and_results_keep_page_order(monkeypatch):
    monkeypatch.setenv("EXTRACTION_CONCURRENCY", "1")   # sequential => call order == submit order
    order = []

    def extractor(document_type, pages, ocr_used=False):
        order.append(document_type)
        return _extraction(document_type, pages)

    _wire(monkeypatch, ["a" * 10, "b" * 5000, "c" * 300],
          ["packing_list", "commercial_invoice", "bill_of_lading"], extractor)
    result = main._analyze_package("x.pdf", b"")
    assert order == ["commercial_invoice", "bill_of_lading", "packing_list"]
    assert [d["document_type"] for d in result["documents"]] == [
        "packing_list", "commercial_invoice", "bill_of_lading"]


def test_default_concurrency_is_one_worker_per_document(monkeypatch):
    monkeypatch.delenv("EXTRACTION_CONCURRENCY", raising=False)
    state = {"active": 0, "peak": 0}
    lock = threading.Lock()

    def extractor(document_type, pages, ocr_used=False):
        with lock:
            state["active"] += 1
            state["peak"] = max(state["peak"], state["active"])
        time.sleep(0.1)
        with lock:
            state["active"] -= 1
        return _extraction(document_type, pages)

    types = ["packing_list", "commercial_invoice", "bill_of_lading", "fumigation_certificate",
             "certificate_of_quality"]
    _wire(monkeypatch, ["t"] * 5, types, extractor)
    main._analyze_package("x.pdf", b"")
    assert state["peak"] == 5


def test_one_failed_extraction_does_not_discard_the_package(monkeypatch):
    def extractor(document_type, pages, ocr_used=False):
        if document_type == "commercial_invoice":
            raise ValueError("The AI returned invalid JSON")
        return _extraction(document_type, pages)

    _wire(monkeypatch, ["a", "b"], ["packing_list", "commercial_invoice"], extractor)
    result = main._analyze_package("x.pdf", b"")
    bad = next(d for d in result["documents"] if d["document_type"] == "commercial_invoice")
    assert bad["extraction_failed"] and bad["validation"]["status"] == "needs_review"
    assert "invalid JSON" in bad["validation"]["warnings"][0]
    assert result["status"] == "needs_review"
    assert any(d["document_type"] == "packing_list" and not d.get("extraction_failed") for d in result["documents"])


def test_pages_are_joined_with_a_real_newline(monkeypatch):
    seen = {}

    def extractor(document_type, pages, ocr_used=False):
        return _extraction(document_type, pages)

    _wire(monkeypatch, ["a"], ["packing_list"], extractor)
    monkeypatch.setattr(main, "classify_document_pages", lambda pages: {
        "documents": [{"document_type": "packing_list", "pages": [1, 2], "confidence": 1}],
        "documents_found": 1, "missing_documents": [], "unclassified_pages": []})
    monkeypatch.setattr(main, "extract_pdf_text", lambda b: _pdf_result(["first", "second"]))
    orig = main.validate_document

    def spy(extraction, source_text, ocr_used=False):
        seen["text"] = source_text
        return orig(extraction, source_text, ocr_used=ocr_used)

    monkeypatch.setattr(main, "validate_document", spy)
    main._analyze_package("x.pdf", b"")
    assert "--- PDF PAGE 1 ---" in seen["text"]
    assert "--- PDF PAGE 2 ---" in seen["text"]
    assert "[TESSERACT OCR]" in seen["text"]
    assert "first" in seen["text"]
    assert "second" in seen["text"]