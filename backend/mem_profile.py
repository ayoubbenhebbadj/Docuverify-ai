"""Measure peak RSS during DocuVerify pipeline stages (AI calls mocked).

Usage:
    python mem_profile.py [pdf_path]
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault("AI_PROVIDER", "openrouter")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
os.environ.setdefault("OPENROUTER_MODEL", "test-model")

import app.ai_extractor as ai_extractor  # noqa: E402
import app.document_classifier as dc_mod  # noqa: E402
import app.document_extractor as de_mod  # noqa: E402
from app import main  # noqa: E402
from app.pdf_reader import extract_pdf_text  # noqa: E402
from app.vision_ocr import recover_uncertain_pages  # noqa: E402
from app.document_classifier import classify_document_pages  # noqa: E402
from app.document_extractor import extract_typed_document  # noqa: E402
from app.document_validator import validate_document  # noqa: E402
from app.cross_document_validator import validate_cross_documents  # noqa: E402
from app.evidence import build_evidence  # noqa: E402


def _fake_response(payload: dict):
    class _Msg:
        def __init__(self, content):
            self.content = content
            self.role = "assistant"

    class _Choice:
        def __init__(self, content):
            self.message = _Msg(content)
            self.finish_reason = "stop"

    class _Resp:
        def __init__(self, content):
            self.choices = [_Choice(content)]
            self.model = "mock"

    import json
    return _Resp(json.dumps(payload))


def _install_mocks() -> None:
    def fake_create(**kwargs):
        # Classification expects {"pages": [{"page": N, "document_type": ...}]}
        msgs = kwargs.get("messages", [])
        content = msgs[0].get("content", "") if msgs else ""
        if "Classify" in content:
            return _fake_response({"pages": []})
        return _fake_response({"document_type": "commercial_invoice", "fields": {}})

    ai_extractor.create_with_retry = fake_create
    dc_mod.create_with_retry = fake_create
    de_mod.create_with_retry = fake_create


def rss_mb() -> float:
    try:
        with open("/proc/self/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024.0
    except OSError:
        pass
    try:
        import psutil  # type: ignore
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def peak_mb() -> float:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        return 0.0


def stage(name: str, fn):
    before = rss_mb()
    started = time.perf_counter()
    result = fn()
    elapsed = time.perf_counter() - started
    current = rss_mb()
    print(
        f"[{name:28s}] rss {before:7.1f} -> {current:7.1f} MB "
        f"(+{current - before:6.1f}) | {elapsed:6.2f}s"
    )
    return result


def main_run(pdf_path: str) -> None:
    _install_mocks()
    data = Path(pdf_path).read_bytes()
    print(f"File: {pdf_path} ({len(data)/1e6:.1f} MB)")

    pdf_result = stage("PDF read + OCR", lambda: extract_pdf_text(data))
    pdf_result = stage("Vision fallback", lambda: recover_uncertain_pages(data, pdf_result))

    pages = pdf_result["pages"]
    classification = stage("Classification", lambda: classify_document_pages(pages))

    extracted = []
    for document in classification["documents"]:
        if document["document_type"] == "unknown":
            continue
        doc_pages = [p for p in pages if p["page"] in document["pages"]]
        source_text = "\n\n".join(
            "--- PDF PAGE %s ---\n%s" % (p["page"], p.get("text") or "")
            for p in doc_pages
        )
        extraction = stage(
            f"Extract {document['document_type']}",
            lambda sp=source_text, dp=doc_pages: extract_typed_document(
                document["document_type"], dp
            ),
        )
        build_evidence(extraction["fields"], source_text)
        validate_document(extraction, source_text)
        extracted.append(extraction)

    stage("Cross-doc validation", lambda: validate_cross_documents(extracted))
    print(f"\nPeak RSS (ru_maxrss): {peak_mb():.1f} MB")


if __name__ == "__main__":
    main_run(sys.argv[1] if len(sys.argv) > 1 else "ilovepdf_merged (1).pdf")