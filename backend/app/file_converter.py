"""Convert supported uploads to PDF bytes for the existing DocuVerify pipeline.

Supported inputs: PDF, DOCX, DOC, JPG/JPEG and PNG.
DOC/DOCX conversion requires LibreOffice (soffice) on PATH.
"""
from __future__ import annotations

import io
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pymupdf as fitz
from PIL import Image

MAX_FILE_SIZE = 10 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".jpg", ".jpeg", ".png"}
_OLE_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_JPEG_SIGNATURES = (b"\xff\xd8\xff",)


def _validate_docx(data: bytes, filename: str) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if "[Content_Types].xml" not in archive.namelist() or "word/document.xml" not in archive.namelist():
                raise ValueError
    except Exception as exc:
        raise ValueError(f"{filename}: This is not a valid DOCX document.") from exc


def _image_to_pdf(data: bytes, filename: str) -> bytes:
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            if image.width < 1 or image.height < 1:
                raise ValueError("empty image")
            # Normalize color mode; Pillow can then encode all supported inputs safely.
            image = image.convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            png_bytes = buffer.getvalue()
        doc = fitz.open()
        try:
            page = doc.new_page(width=595, height=842)
            rect = fitz.Rect(0, 0, 595, 842)
            page.insert_image(rect, stream=png_bytes, keep_proportion=True, overlay=True)
            return doc.tobytes(garbage=3, deflate=True)
        finally:
            doc.close()
    except Exception as exc:
        raise ValueError(f"{filename}: The image is damaged or cannot be decoded.") from exc


def _word_to_pdf(data: bytes, filename: str, extension: str) -> bytes:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise RuntimeError(
            "Word conversion is unavailable: install LibreOffice on the backend host "
            "and make sure 'soffice' is on PATH."
        )

    if extension == ".docx":
        _validate_docx(data, filename)
    elif not data.startswith(_OLE_SIGNATURE):
        raise ValueError(f"{filename}: This does not look like a valid legacy DOC file.")

    with tempfile.TemporaryDirectory(prefix="docuverify_word_") as tmp:
        work = Path(tmp)
        source = work / f"input{extension}"
        source.write_bytes(data)
        out_dir = work / "out"
        out_dir.mkdir()
        profile = work / "lo_profile"
        command = [
            soffice,
            f"-env:UserInstallation={profile.as_uri()}",
            "--headless",
            "--convert-to", "pdf",
            "--outdir", str(out_dir),
            str(source),
        ]
        try:
            completed = subprocess.run(
                command, capture_output=True, text=True, timeout=90, check=False
            )
        except subprocess.TimeoutExpired as exc:
            raise ValueError(f"{filename}: Word-to-PDF conversion timed out.") from exc
        output = out_dir / "input.pdf"
        if completed.returncode != 0 or not output.exists():
            detail = (completed.stderr or completed.stdout or "LibreOffice conversion failed").strip()
            raise ValueError(f"{filename}: Could not convert Word document to PDF: {detail[:500]}")
        pdf_bytes = output.read_bytes()
        if not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError(f"{filename}: Word conversion did not produce a valid PDF.")
        return pdf_bytes


def convert_upload_to_pdf(filename: str, data: bytes) -> bytes:
    """Validate and convert one upload to PDF bytes without writing user files permanently."""
    if not filename:
        raise ValueError("An uploaded file has no filename.")
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"{filename}: Unsupported format. Upload PDF, DOCX, DOC, JPG, JPEG or PNG."
        )
    if not data:
        raise ValueError(f"{filename}: The uploaded file is empty.")
    if len(data) > MAX_FILE_SIZE:
        raise ValueError(f"{filename}: File exceeds the 10 MB per-file limit.")

    if extension == ".pdf":
        if not data.startswith(b"%PDF-"):
            raise ValueError(f"{filename}: This does not appear to be a valid PDF.")
        try:
            with fitz.open(stream=data, filetype="pdf") as pdf:
                if pdf.needs_pass:
                    raise ValueError(f"{filename}: This PDF is password-protected.")
                if len(pdf) == 0:
                    raise ValueError(f"{filename}: This PDF contains no pages.")
        except fitz.FileDataError as exc:
            raise ValueError(f"{filename}: This PDF is damaged or unreadable.") from exc
        return data

    if extension in {".jpg", ".jpeg"}:
        if not any(data.startswith(sig) for sig in _JPEG_SIGNATURES):
            raise ValueError(f"{filename}: Invalid JPEG file signature.")
        return _image_to_pdf(data, filename)

    if extension == ".png":
        if not data.startswith(_PNG_SIGNATURE):
            raise ValueError(f"{filename}: Invalid PNG file signature.")
        return _image_to_pdf(data, filename)

    return _word_to_pdf(data, filename, extension)
