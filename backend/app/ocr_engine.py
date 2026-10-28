"""OCR engine for scanned PDF pages.

What changed compared with the first version (measured on the sample scans):
  * The original scan pixels are used instead of re-rendering the page.  The
    samples are ~150 DPI images; rendering them at 400 DPI only blurred them.
  * Background normalisation + cubic up-scaling to ~400 DPI (Tesseract works
    best with ~30 px tall characters).  This alone roughly doubles the number
    of recognised words on the sample packing lists.
  * Skew correction and (only when needed) 90/180/270 degree orientation fix.
  * Several recognition passes (different layout modes / colour handling) whose
    results are merged, so words missed by one pass are recovered by another.
  * Tesseract is located automatically (env TESSERACT_CMD, PATH, common
    Windows folders) and French is used automatically when it is installed.

Environment variables (all optional):
  TESSERACT_CMD                  full path to tesseract(.exe)
  OCR_LANGUAGES                  e.g. "eng+fra" (default: eng, plus fra if installed)
  OCR_LOW_CONFIDENCE_THRESHOLD   default 75
  OCR_THOROUGH                   "1" = always run every pass (slower, max recall)
"""

from __future__ import annotations

import logging
import os
import re
import shutil
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import mean

import cv2
import numpy as np
import pymupdf as fitz
import pytesseract
from pytesseract import Output

log = logging.getLogger(__name__)

LOW_CONFIDENCE_THRESHOLD = float(
    os.getenv("OCR_LOW_CONFIDENCE_THRESHOLD", "75")
)
TARGET_DPI = 400          # effective resolution we feed to Tesseract
MAX_SCALE = 4.5
MAX_LONG_SIDE = 5600      # px, keeps memory/time bounded
FALLBACK_RENDER_DPI = 300
GOOD_ENOUGH_CONFIDENCE = 90.0   # skip extra passes when the first one is this good
GOOD_ENOUGH_WORDS = 25
TESSERACT_TIMEOUT = 180   # seconds per recognition call

_WINDOWS_CANDIDATES = (
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Tesseract-OCR" / "tesseract.exe",
)


# --------------------------------------------------------------------------
# Tesseract discovery
# --------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _configure_tesseract() -> str:
    candidates = [os.getenv("TESSERACT_CMD") or ""]
    candidates.append(shutil.which("tesseract") or "")
    candidates.extend(str(p) for p in _WINDOWS_CANDIDATES)

    for candidate in candidates:
        if candidate and Path(candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = candidate
            return candidate

    raise RuntimeError(
        "Tesseract OCR was not found. Install it (Windows installer from "
        "https://github.com/UB-Mannheim/tesseract/wiki, or `apt install "
        "tesseract-ocr`) or set the TESSERACT_CMD environment variable to "
        "the full path of tesseract."
    )


@lru_cache(maxsize=1)
def _installed_languages() -> frozenset[str]:
    _configure_tesseract()
    try:
        return frozenset(pytesseract.get_languages(config=""))
    except Exception:  # pragma: no cover - defensive
        return frozenset({"eng"})


def resolve_languages(requested: str | None = None) -> str:
    """Return a Tesseract language string using only installed languages."""
    installed = _installed_languages()

    if requested is None:
        requested = os.getenv("OCR_LANGUAGES")

    if requested is None:
        # Import/export paperwork is often bilingual: add French if present.
        wanted = ["eng"] + (["fra"] if "fra" in installed else [])
    else:
        wanted = [l for l in requested.split("+") if l]

    usable = [l for l in wanted if l in installed]
    if not usable:
        usable = ["eng"] if "eng" in installed else sorted(installed - {"osd"})[:1]
    if not usable:
        raise RuntimeError("No Tesseract language data is installed.")
    return "+".join(usable)


# --------------------------------------------------------------------------
# Page image acquisition
# --------------------------------------------------------------------------

def _dominant_image(page: fitz.Page) -> np.ndarray | None:
    """Original pixels of the image that covers most of the page, if any."""
    if page.rotation != 0:
        return None

    page_area = max(page.rect.width * page.rect.height, 1.0)
    best_xref, best_cover = None, 0.0

    for info in page.get_images(full=True):
        xref = info[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            continue
        cover = max((r.width * r.height for r in rects), default=0.0) / page_area
        if cover > best_cover:
            best_xref, best_cover = xref, cover

    if best_xref is None or best_cover < 0.6:
        return None

    try:
        pix = fitz.Pixmap(page.parent, best_xref)
        if pix.alpha:
            pix = fitz.Pixmap(pix, 0)
        if pix.colorspace is None or pix.colorspace.n != 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        return np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, 3).copy()
    except Exception as exc:
        log.debug("Could not read embedded image, rendering instead: %s", exc)
        return None


def _page_image(page: fitz.Page) -> tuple[np.ndarray, float]:
    """Return (RGB array, effective DPI)."""
    page_width_in = max(page.rect.width / 72.0, 0.1)

    array = _dominant_image(page)
    if array is not None:
        return array, array.shape[1] / page_width_in

    pix = page.get_pixmap(dpi=FALLBACK_RENDER_DPI, alpha=False)
    array = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)
    if pix.n == 1:
        array = np.repeat(array, 3, axis=2)
    return array[:, :, :3].copy(), float(FALLBACK_RENDER_DPI)


# --------------------------------------------------------------------------
# Pre-processing
# --------------------------------------------------------------------------

def _odd(n: float) -> int:
    n = int(round(n))
    return n if n % 2 else n + 1


def _normalise_background(gray: np.ndarray, dpi: float) -> np.ndarray:
    """Flatten uneven lighting / tinted boxes so text has uniform contrast."""
    k = min(_odd(max(21, dpi / 5)), 101)
    background = cv2.medianBlur(gray, k)
    return cv2.divide(gray, background, scale=255)


def _estimate_skew(gray: np.ndarray) -> float:
    """Skew angle in degrees (projection-profile search, +/-6 degrees)."""
    h, w = gray.shape
    factor = 700.0 / max(w, 1)
    small = cv2.resize(gray, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA) \
        if factor < 1 else gray
    binary = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    if cv2.countNonZero(binary) < 200:
        return 0.0

    sh, sw = binary.shape
    centre = (sw / 2, sh / 2)

    def score(angle: float) -> float:
        m = cv2.getRotationMatrix2D(centre, angle, 1.0)
        rotated = cv2.warpAffine(binary, m, (sw, sh), flags=cv2.INTER_NEAREST)
        return float(np.var(rotated.sum(axis=1, dtype=np.float64)))

    coarse = max(np.arange(-6.0, 6.01, 1.0), key=score)
    fine = max(np.arange(coarse - 0.9, coarse + 0.91, 0.1), key=score)

    # Only trust a clear improvement over "no rotation".
    if score(fine) < score(0.0) * 1.03:
        return 0.0
    return float(fine)


def _rotate_small(gray: np.ndarray, angle: float) -> np.ndarray:
    h, w = gray.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(
        gray, m, (w, h), flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT, borderValue=255,
    )


def _upscale(gray: np.ndarray, dpi: float) -> tuple[np.ndarray, float]:
    scale = min(max(TARGET_DPI / max(dpi, 1.0), 1.0), MAX_SCALE)
    long_side = max(gray.shape) * scale
    if long_side > MAX_LONG_SIDE:
        scale = MAX_LONG_SIDE / max(gray.shape)

    if abs(scale - 1.0) < 0.05:
        return gray, 1.0
    interpolation = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    return cv2.resize(gray, None, fx=scale, fy=scale, interpolation=interpolation), scale


def _pad(gray: np.ndarray) -> np.ndarray:
    # Tesseract struggles with text touching the image border.
    return cv2.copyMakeBorder(gray, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)


# --------------------------------------------------------------------------
# Recognition
# --------------------------------------------------------------------------

@dataclass
class Word:
    text: str
    conf: float
    left: int
    top: int
    width: int
    height: int
    order: int = 0

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def cy(self) -> float:
        return self.top + self.height / 2


def _is_noise(text: str, conf: float) -> bool:
    if conf < 20:
        return True
    # Stray rules / box borders recognised as punctuation.
    return not any(c.isalnum() for c in text) and conf < 50


def _recognise(image: np.ndarray, psm: int, lang: str) -> list[Word]:
    data = pytesseract.image_to_data(
        image,
        lang=lang,
        config=f"--oem 1 --psm {psm} -c preserve_interword_spaces=1",
        output_type=Output.DICT,
        timeout=TESSERACT_TIMEOUT,
    )
    words: list[Word] = []
    for i, raw in enumerate(data["text"]):
        text = (raw or "").strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            continue
        if not text or conf < 0 or _is_noise(text, conf):
            continue
        words.append(Word(
            text, conf,
            int(data["left"][i]), int(data["top"][i]),
            int(data["width"][i]), int(data["height"][i]),
            order=len(words),
        ))
    return words


def _score(words: list[Word]) -> float:
    """Approximate number of correctly read words."""
    return sum(w.conf / 100.0 for w in words if w.conf >= 50)


def _mean_conf(words: list[Word]) -> float | None:
    return round(mean(w.conf for w in words), 2) if words else None


def _osd_hint(image: np.ndarray) -> int:
    """Orientation suggested by Tesseract's OSD (any confidence), else 0."""
    try:
        osd = pytesseract.image_to_osd(image, config="--psm 0", timeout=60)
    except Exception:
        return 0
    match = re.search(r"Rotate:\s*(\d+)", osd)
    return int(match.group(1)) % 360 if match else 0


def _best_rotation(
    image: np.ndarray, lang: str, baseline: float,
    candidates: tuple[int, ...] = (90, 180, 270),
    margin: float = 1.3,
) -> int:
    """Degrees (0/90/180/270, clockwise) after which the page reads best.

    Tesseract's own orientation detector reports low confidence on sparse
    forms, so instead each rotation is tried on a down-scaled copy and the one
    that yields the most confidently-read words wins.  A rotation must beat
    the current orientation clearly before it is applied.
    """
    factor = min(1.0, 2200.0 / max(image.shape))
    small = cv2.resize(image, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA) \
        if factor < 1 else image

    # Score the current orientation on the same down-scaled copy so that the
    # comparison with the rotated candidates is like for like.
    try:
        baseline = _score(_recognise(small, 3, lang))
    except Exception:
        pass
    best_degrees, best_score = 0, baseline
    for degrees in candidates:
        try:
            candidate = _score(_recognise(_rotate_clockwise(small, degrees), 3, lang))
        except Exception:
            continue
        if candidate >= 8 and candidate > best_score * margin:
            best_degrees, best_score = degrees, candidate
    return best_degrees


def _enhance(gray: np.ndarray) -> np.ndarray:
    """Denoise and sharpen: helps noisy, blurred or low-resolution scans."""
    denoised = cv2.fastNlMeansDenoising(gray, None, h=12, templateWindowSize=7, searchWindowSize=21)
    blurred = cv2.GaussianBlur(denoised, (0, 0), 3)
    return cv2.addWeighted(denoised, 1.8, blurred, -0.8, 0)


def _rotate_clockwise(image: np.ndarray, degrees: int) -> np.ndarray:
    return np.rot90(image, k=-(degrees // 90) % 4).copy()


# --------------------------------------------------------------------------
# Merging passes
# --------------------------------------------------------------------------

def _overlap(a: Word, b: Word) -> float:
    ix = min(a.right, b.right) - max(a.left, b.left)
    iy = min(a.bottom, b.bottom) - max(a.top, b.top)
    if ix <= 0 or iy <= 0:
        return 0.0
    return (ix * iy) / max(min(a.width * a.height, b.width * b.height), 1)


def _group_lines(words: list[Word]) -> list[list[Word]]:
    """Group words into text lines keeping the order Tesseract produced."""
    lines: list[list[Word]] = []
    for w in words:
        if lines:
            last = lines[-1]
            ref = last[-1]
            same_line = (
                abs(w.cy - ref.cy) < 0.6 * max(w.height, ref.height)
                and w.left >= ref.left - 5
            )
            if same_line:
                last.append(w)
                continue
        lines.append([w])
    return lines


def _merge(passes: list[list[Word]]) -> list[list[Word]]:
    """Merge several recognition passes into one set of text lines.

    The best-scoring pass provides the reading order.  Words from the other
    passes are added where the best pass found nothing, and replace words the
    best pass read with clearly lower confidence.
    """
    passes = sorted(passes, key=_score, reverse=True)
    lines = _group_lines(passes[0])

    for extra in passes[1:]:
        for w in sorted(extra, key=lambda x: (x.top, x.left)):
            if w.conf < 60 or not any(c.isalnum() for c in w.text):
                continue

            clash = None
            for line in lines:
                for existing in line:
                    if _overlap(w, existing) > 0.3:
                        clash = existing
                        break
                if clash:
                    break

            if clash is not None:
                if w.conf >= clash.conf + 25 and w.text != clash.text:
                    clash.text, clash.conf = w.text, w.conf
                continue

            # Place into a line at the same height, otherwise create a line.
            target = None
            for line in lines:
                ref_h = max(x.height for x in line)
                if abs(w.cy - sum(x.cy for x in line) / len(line)) < 0.5 * max(ref_h, w.height):
                    left = min(x.left for x in line)
                    right = max(x.right for x in line)
                    gap = max(left - w.right, w.left - right, 0)
                    if gap <= 4 * w.height:
                        target = line
                        break

            if target is not None:
                target.append(w)
            else:
                position = len(lines)
                for idx, line in enumerate(lines):
                    if min(x.top for x in line) > w.bottom and (
                        min(x.right for x in line) > w.left
                        and max(x.left for x in line) < w.right
                    ):
                        position = idx
                        break
                lines.insert(position, [w])

    return lines


def _lines_to_text(lines: list[list[Word]]) -> str:
    out = []
    for line in lines:
        ordered = sorted(line, key=lambda w: w.left)
        parts: list[str] = []
        for i, w in enumerate(ordered):
            if i:
                gap = w.left - ordered[i - 1].right
                parts.append("  " if gap > 2.5 * w.height else " ")
            parts.append(w.text)
        out.append("".join(parts))
    return "\n".join(out)


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------

def ocr_page(page: fitz.Page, language: str | None = None) -> dict:
    """OCR one PDF page and report word-level confidence."""
    _configure_tesseract()
    lang = resolve_languages(language)

    rgb, dpi = _page_image(page)
    thorough = os.getenv("OCR_THOROUGH") == "1"

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    # min(R,G,B) keeps coloured (e.g. blue stamp) text dark.
    min_rgb = rgb.min(axis=2)

    gray_n = _normalise_background(gray, dpi)
    min_n = _normalise_background(min_rgb, dpi)

    skew = _estimate_skew(gray_n)
    if abs(skew) >= 0.3:
        gray_n = _rotate_small(gray_n, skew)
        min_n = _rotate_small(min_n, skew)
    else:
        skew = 0.0

    gray_img, scale = _upscale(gray_n, dpi)
    gray_img = _pad(gray_img)

    rotation = 0
    words_a = _recognise(gray_img, 3, lang)

    good_enough = (
        (_mean_conf(words_a) or 0) >= GOOD_ENOUGH_CONFIDENCE
        and len(words_a) >= GOOD_ENOUGH_WORDS
    )

    # A page that reads badly may simply be sideways / upside down.  Tesseract
    # can half-cope with some rotations, so also follow its orientation hint
    # whenever the page is not an obviously clean read.
    if len(words_a) < 15 or (_mean_conf(words_a) or 0) < 60:
        rotation = _best_rotation(gray_img, lang, _score(words_a))
    elif not good_enough:
        hint = _osd_hint(gray_img)
        if hint:
            # OSD's sign convention differs between versions: try both
            # directions for a quarter turn and let the read-out decide.
            options = (180,) if hint == 180 else (90, 270)
            rotation = _best_rotation(
                gray_img, lang, _score(words_a), options, margin=0.92
            )

    if rotation:
        gray_img = _rotate_clockwise(gray_img, rotation)
        min_n = _rotate_clockwise(min_n, rotation)
        words_a = _recognise(gray_img, 3, lang)

    passes = [words_a]
    pass_names = ["psm3/gray"]

    good_enough = (
        (_mean_conf(words_a) or 0) >= GOOD_ENOUGH_CONFIDENCE
        and len(words_a) >= GOOD_ENOUGH_WORDS
    )

    if thorough or not good_enough:
        passes.append(_recognise(gray_img, 6, lang))
        pass_names.append("psm6/gray")

        min_img, _ = _upscale(min_n, dpi)
        min_img = _pad(min_img)
        passes.append(_recognise(min_img, 11, lang))
        pass_names.append("psm11/min-rgb")

    # Still poor after all passes: try a denoised + sharpened version too.
    if (_mean_conf(max(passes, key=_score)) or 0) < 80:
        enhanced = _pad(_upscale(_enhance(gray_n if rotation == 0 else _rotate_clockwise(gray_n, rotation)), dpi)[0])
        passes.append(_recognise(enhanced, 6, lang))
        pass_names.append("psm6/enhanced")

    lines = _merge([p for p in passes if p])
    final_words = [w for line in lines for w in line]

    text = _lines_to_text(lines)
    average_confidence = _mean_conf(final_words)
    low_confidence = (
        average_confidence is None
        or average_confidence < LOW_CONFIDENCE_THRESHOLD
    )

    return {
        "text": text,
        "ocr_used": True,
        "ocr_confidence": average_confidence,
        "ocr_word_count": len(final_words),
        "ocr_low_confidence": low_confidence,
        "ocr_details": {
            "source_dpi": round(dpi),
            "scale": round(scale, 2),
            "skew_degrees": round(skew, 1),
            "rotation": rotation,
            "languages": lang,
            "passes": pass_names,
        },
    }
