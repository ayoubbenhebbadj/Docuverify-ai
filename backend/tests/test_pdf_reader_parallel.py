import threading
import time

import cv2
import numpy as np
import pymupdf as fitz
import pytest

from app import pdf_reader


def _scan_png(label: int) -> bytes:
    img = np.full((1100, 800, 3), 255, np.uint8)
    cv2.putText(img, f"SCAN {label}", (80, 200), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 0), 6)
    ok, buf = cv2.imencode(".png", img)
    return buf.tobytes()


def build_pdf(kinds: str) -> bytes:
    """'t' = text page, 's' = scanned (image-only) page."""
    doc = fitz.open()
    for i, kind in enumerate(kinds, start=1):
        page = doc.new_page(width=595, height=842)
        if kind == "t":
            page.insert_text((72, 100), f"NATIVE TEXT PAGE {i} " + "word " * 30)
        else:
            page.insert_image(page.rect, stream=_scan_png(i))
    return doc.tobytes()


class FakeOcr:
    def __init__(self, delay=0.15, fail_on=None):
        self.delay, self.fail_on = delay, fail_on
        self.active = self.peak = 0
        self.lock = threading.Lock()
        self.calls = 0

    def __call__(self, image, dpi, language=None):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.calls += 1
            n = self.calls
        try:
            time.sleep(self.delay)
            if self.fail_on == n:
                raise RuntimeError("tesseract crashed")
            return {"text": f"ocr text {int(image.sum()) % 997}", "ocr_used": True, "ocr_confidence": 90.0,
                    "ocr_word_count": 3, "ocr_low_confidence": False, "ocr_details": {"passes": ["psm3/gray"]}}
        finally:
            with self.lock:
                self.active -= 1


def test_pages_keep_their_order_and_run_sequentially(monkeypatch):
    fake = FakeOcr()
    monkeypatch.setattr(pdf_reader, "ocr_image", fake)
    monkeypatch.setenv("OCR_WORKERS", "3")
    pdf = build_pdf("ssstss")
    started = time.perf_counter()
    result = pdf_reader.extract_pdf_text(pdf)
    elapsed = time.perf_counter() - started

    assert [p["page"] for p in result["pages"]] == [1, 2, 3, 4, 5, 6]
    assert [p["ocr_used"] for p in result["pages"]] == [True, True, True, False, True, True]
    assert result["pages"][3]["text"].startswith("NATIVE TEXT PAGE 4")
    assert fake.peak == 1                       # one full-resolution page at a time
    assert elapsed >= 5 * 0.15                  # OCR is deliberately sequential
    assert result["has_text"] and result["pages_needing_ocr"] == []


def test_each_page_gets_its_own_pixels(monkeypatch):
    seen = {}

    def fake(image, dpi, language=None):
        return {"text": f"page-{int(image.sum())}", "ocr_used": True, "ocr_confidence": 95.0,
                "ocr_word_count": 1, "ocr_low_confidence": False, "ocr_details": {}}

    monkeypatch.setattr(pdf_reader, "ocr_image", fake)
    monkeypatch.setenv("OCR_WORKERS", "3")
    seq = pdf_reader.extract_pdf_text(build_pdf("ssss"))
    monkeypatch.setenv("OCR_WORKERS", "1")
    one = pdf_reader.extract_pdf_text(build_pdf("ssss"))
    assert [p["text"] for p in seq["pages"]] == [p["text"] for p in one["pages"]]
    assert len({p["text"] for p in seq["pages"]}) == 4  # pages were not mixed up


def test_one_failing_page_does_not_stop_the_others(monkeypatch):
    monkeypatch.setattr(pdf_reader, "ocr_image", FakeOcr(delay=0.02, fail_on=2))
    monkeypatch.setenv("OCR_WORKERS", "2")
    result = pdf_reader.extract_pdf_text(build_pdf("sss"))
    assert len(result["ocr_errors"]) == 1 and "tesseract crashed" in result["ocr_errors"][0]
    assert sum(p["ocr_used"] for p in result["pages"]) == 2
    assert len(result["pages_needing_ocr"]) == 1


def test_sequential_mode_when_one_worker(monkeypatch):
    fake = FakeOcr(delay=0.01)
    monkeypatch.setattr(pdf_reader, "ocr_image", fake)
    monkeypatch.setenv("OCR_WORKERS", "1")
    pdf_reader.extract_pdf_text(build_pdf("sss"))
    assert fake.peak == 1


def test_blank_scan_is_not_reported_as_unreadable(monkeypatch):
    monkeypatch.setattr(pdf_reader, "ocr_image", lambda *a, **k: {
        "text": "", "ocr_used": True, "ocr_confidence": None, "ocr_word_count": 0,
        "ocr_low_confidence": False, "ocr_sparse": True, "ocr_blank": True, "ocr_details": {}})
    monkeypatch.setenv("OCR_WORKERS", "1")
    result = pdf_reader.extract_pdf_text(build_pdf("ts"))
    assert result["pages_needing_ocr"] == []
    assert result["pages_sparse"] == [2]


def test_invalid_worker_setting_falls_back(monkeypatch):
    monkeypatch.setenv("OCR_WORKERS", "many")
    assert pdf_reader._ocr_workers() >= 1
