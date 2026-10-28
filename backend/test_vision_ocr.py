"""Unit tests for the optional vision OCR fallback (no network calls)."""
import os

# ai_extractor requires these settings at import time; dummy values are enough
# because the tests replace the network-facing transcription function.
os.environ.setdefault("OPENROUTER_API_KEY", "test-key-not-real")
os.environ.setdefault("OPENROUTER_MODEL", "test/text-model")

from app import vision_ocr


def test_disabled_vision_fallback_leaves_result_unchanged(monkeypatch):
    monkeypatch.setattr(vision_ocr, "VISION_MODEL", "")
    result = {
        "pages": [{"page": 1, "text": "already readable", "needs_ocr": False}],
        "extracted_text": "already readable",
        "has_text": True,
    }
    assert vision_ocr.recover_uncertain_pages(b"pdf", result) is result
    assert result["pages"][0]["text"] == "already readable"


def test_uncertain_page_uses_vision_and_marks_review(monkeypatch):
    monkeypatch.setattr(vision_ocr, "VISION_MODEL", "test/vision-model")
    monkeypatch.setattr(
        vision_ocr,
        "vision_transcribe_page",
        lambda _pdf, page: f"Recovered page {page}: TOTAL USD 12850.00",
    )
    result = {
        "page_count": 2,
        "pages": [
            {"page": 1, "text": "good native text", "needs_ocr": False},
            {
                "page": 2,
                "text": "T0TAL USD 12B50.00",
                "needs_ocr": False,
                "ocr_used": True,
                "ocr_low_confidence": True,
            },
        ],
        "extracted_text": "good native text\n\nT0TAL USD 12B50.00",
        "has_text": True,
    }

    vision_ocr.recover_uncertain_pages(b"pdf", result)

    assert result["pages"][0].get("vision_ocr_used") is None
    assert result["pages"][1]["text"] == "Recovered page 2: TOTAL USD 12850.00"
    assert result["pages"][1]["vision_ocr_used"] is True
    assert result["pages"][1]["vision_ocr_review_required"] is True
    assert result["pages_vision_ocr_used"] == [2]
    assert "Recovered page 2" in result["extracted_text"]
