"""Uses the real Tesseract (skipped if not installed)."""
import shutil

import cv2
import numpy as np
import pytest

from app import ocr_engine

pytestmark = pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract not installed")


def _page(lines: int) -> np.ndarray:
    img = np.full((2339, 1654, 3), 255, np.uint8)  # A4 @ 200 dpi
    for i in range(lines):
        cv2.putText(img, f"INVOICE LINE {i} NET WEIGHT 1000 KG TOTAL 5000 USD", (80, 120 + i * 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 2)
    return img


def test_logo_like_page_is_sparse_and_single_pass():
    img = np.full((2339, 1654, 3), 255, np.uint8)
    cv2.putText(img, "Acme Herbs", (500, 1100), cv2.FONT_HERSHEY_SIMPLEX, 2, (30, 120, 30), 3)
    result = ocr_engine.ocr_image(img, 200)
    assert result["ocr_sparse"] is True
    assert result["ocr_details"]["passes"] == ["psm3/gray"]
    assert result["ocr_low_confidence"] is False        # nothing worth a manual review


def test_empty_page_is_blank():
    result = ocr_engine.ocr_image(np.full((2339, 1654, 3), 255, np.uint8), 200)
    assert result["ocr_sparse"] and result["ocr_blank"] and result["text"].strip() == ""


def test_dense_page_is_not_sparse():
    result = ocr_engine.ocr_image(_page(30), 200)
    assert result["ocr_sparse"] is False
    assert "INVOICE" in result["text"].upper()


def test_thorough_mode_disables_the_shortcut(monkeypatch):
    monkeypatch.setenv("OCR_THOROUGH", "1")
    img = np.full((2339, 1654, 3), 255, np.uint8)
    cv2.putText(img, "Acme Herbs", (500, 1100), cv2.FONT_HERSHEY_SIMPLEX, 2, (30, 120, 30), 3)
    result = ocr_engine.ocr_image(img, 200)
    assert result["ocr_sparse"] is False and len(result["ocr_details"]["passes"]) >= 3


def test_arabic_is_used_when_installed_and_reported_when_not(monkeypatch):
    monkeypatch.delenv("OCR_LANGUAGES", raising=False)
    monkeypatch.setattr(ocr_engine, "_installed_languages", lambda: frozenset({"eng", "fra", "ara"}))
    assert ocr_engine.resolve_languages() == "eng+fra+ara"
    assert ocr_engine.missing_recommended_languages() == []
    monkeypatch.setattr(ocr_engine, "_installed_languages", lambda: frozenset({"eng"}))
    assert ocr_engine.resolve_languages() == "eng"
    assert "Arabic" in ocr_engine.missing_recommended_languages()[0]
    monkeypatch.setenv("OCR_LANGUAGES", "eng")
    assert ocr_engine.missing_recommended_languages() == []     # explicit choice: no nagging
