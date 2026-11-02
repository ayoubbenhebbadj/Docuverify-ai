"""Locate extracted values in the source text (replaces model-written quotes).

Asking the LLM to also write a quotation for every field makes the answer much
longer (slow, and more tokens to pay for), and a quote proves nothing about
whether the *value* is right.  Here the model returns values only and this
module finds, in code, the source line each value came from.  A value that
cannot be found in the source gets no evidence, which the document validator
reports as "unsupported evidence" (a flag to check it, not proof it is wrong).

Handles: Arabic-Indic digits, thousands separators (1,234.50 / 1.234,50 /
1 234), dates written in other layouts than YYYY-MM-DD (12/10/2026, 12 Jun.,
2026, JUN.24,2026), values with units ("27500 KG" vs "27,500 KGS"), lists, and
OCR noise (fuzzy match when ``fuzzy`` is true).
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal, InvalidOperation

from app.document_validator import fuzzy_contains, normalize_text

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_MONTHS = [
    ("jan", "january"), ("feb", "february"), ("mar", "march"), ("apr", "april"),
    ("may", "may"), ("jun", "june"), ("jul", "july"), ("aug", "august"),
    ("sep", "september"), ("oct", "october"), ("nov", "november"), ("dec", "december"),
]
# Digit groups ("27 500", "27,500.00", "27.500", "1.234,56") or a plain number.
# Whitespace only joins digits when exactly three follow ("220 11000 11440" is
# three numbers, not one), and a group may not run into further digits.
_NUMBER_TOKEN = re.compile(r"\d{1,3}(?:[ ,.]\d{3})+(?!\d)(?:[.,]\d+)?|\d+(?:[.,]\d+)?")
_MAX_QUOTE = 240


def fold_digits(text: str) -> str:
    return text.translate(_ARABIC_DIGITS)


def _number_variants(token: str) -> set[Decimal]:
    """Every sensible reading of a numeric token (separator conventions differ)."""
    token = re.sub(r"\s+", "", token)
    variants: set[str] = set()
    if "," in token and "." in token:
        # The right-most separator is the decimal point.
        if token.rfind(",") > token.rfind("."):
            variants.add(token.replace(".", "").replace(",", "."))
        else:
            variants.add(token.replace(",", ""))
    elif "," in token:
        variants.add(token.replace(",", ""))        # 27,500 -> 27500
        variants.add(token.replace(",", "."))       # 27,5   -> 27.5
    elif "." in token:
        variants.add(token)                         # 27.5
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", token):
            variants.add(token.replace(".", ""))    # 27.500 -> 27500 (European)
    else:
        variants.add(token)
    out = set()
    for v in variants:
        try:
            out.add(Decimal(v).normalize())
        except InvalidOperation:
            continue
    return out


def _to_decimal(value) -> Decimal | None:
    if isinstance(value, bool):
        return None
    try:
        return Decimal(str(value)).normalize()
    except InvalidOperation:
        return None


def _clip(line: str) -> str:
    line = re.sub(r"\s+", " ", line).strip()
    return line if len(line) <= _MAX_QUOTE else line[:_MAX_QUOTE].rstrip()


def _line_containing(text: str, start: int, end: int) -> str:
    left = text.rfind("\n", 0, start) + 1
    right = text.find("\n", end)
    return _clip(text[left: right if right != -1 else len(text)])


def _find_number(target: Decimal, text: str) -> str | None:
    for match in _NUMBER_TOKEN.finditer(text):
        if target in _number_variants(match.group()):
            return _line_containing(text, match.start(), match.end())
    return None


def _date_patterns(d: date) -> list[re.Pattern]:
    day, month, year = d.day, d.month, d.year
    dd = rf"0?{day}" if day < 10 else str(day)
    mm = rf"0?{month}" if month < 10 else str(month)
    yyyy, yy = str(year), f"{year % 100:02d}"
    sep = r"[\s./,\-]*"
    abbr, full = _MONTHS[month - 1]
    mon = rf"(?:{full}|{abbr})"
    forms = [
        rf"(?<!\d){dd}{sep}{mm}{sep}(?:{yyyy}|{yy})(?!\d)",     # 12/10/2026, 12.10.26
        rf"(?<!\d){yyyy}{sep}{mm}{sep}{dd}(?!\d)",              # 2026/10/12
        rf"(?<!\d){dd}{sep}{mon}{sep}(?:{yyyy}|{yy})(?!\d)",    # 12 Jun., 2026
        rf"{mon}{sep}{dd}{sep}{yyyy}(?!\d)",                    # JUN.24,2026
        rf"(?<!\d){mm}{sep}{dd}{sep}{yyyy}(?!\d)",              # 10/12/2026 (US)
    ]
    return [re.compile(f, re.IGNORECASE) for f in forms]


def _find_date(iso: str, text: str) -> str | None:
    try:
        d = date.fromisoformat(iso)
    except ValueError:
        return None
    for pattern in _date_patterns(d):
        match = pattern.search(text)
        if match:
            return _line_containing(text, match.start(), match.end())
    return None


def _contains_token(needle: str, haystack: str) -> bool:
    """Substring match that may not start or end inside a longer word/number
    ("27" must not match inside "1148562277")."""
    return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", haystack) is not None


def _find_string(value: str, text: str, fuzzy: bool) -> str | None:
    norm_value = normalize_text(value)
    if not norm_value:
        return None
    norm_text = normalize_text(text)

    # 1. Verbatim (after Unicode / whitespace / punctuation normalisation).
    if _contains_token(norm_value, norm_text):
        for line in text.splitlines():
            if _contains_token(norm_value, normalize_text(line)):
                return _clip(line)
        return _clip(value)  # spans several lines

    # 2. Values with numbers/units ("27500 KG"): every number must exist in the
    #    source, and so must every word of three or more letters.
    numbers = _NUMBER_TOKEN.findall(norm_value)
    if numbers:
        words = [w for w in re.findall(r"[^\W\d_]{3,}", norm_value)]
        first_line = None
        numbers_found = True
        for token in numbers:
            variants = _number_variants(token)
            hit = next(
                (m for m in _NUMBER_TOKEN.finditer(text) if variants & _number_variants(m.group())),
                None,
            )
            if hit is None:
                numbers_found = False
                break
            if first_line is None:
                first_line = _line_containing(text, hit.start(), hit.end())
        if numbers_found and all(_contains_token(w, norm_text) or w in norm_text for w in words):
            return first_line
        # Numbers must always match exactly; only wording may be fuzzy (OCR).
        # fuzzy_contains enforces the exact-number rule itself.

    # 3. OCR noise.
    if fuzzy and fuzzy_contains(norm_value, norm_text, 0.85):
        return _clip(value)
    return None


def locate_value(value, source_text: str, *, fuzzy: bool = False):
    """Return the quotation supporting ``value`` (str, or list of str), or None."""
    if value is None or not isinstance(source_text, str) or not source_text.strip():
        return None
    text = fold_digits(source_text)

    if isinstance(value, list):
        quotes = []
        for item in value:
            quote = locate_value(item, source_text, fuzzy=fuzzy)
            if quote is None:
                return None  # one ungrounded element makes the field unsupported
            quotes.extend(quote if isinstance(quote, list) else [quote])
        return quotes or None

    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        target = _to_decimal(value)
        return _find_number(target, text) if target is not None else None

    if isinstance(value, str):
        stripped = fold_digits(value).strip()
        if not stripped:
            return None
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", stripped):
            return _find_date(stripped, text)
        return _find_string(stripped, text, fuzzy)
    return None


def build_evidence(fields: dict, source_text: str, *, fuzzy: bool = False) -> dict:
    """Evidence for every field: a source quotation, or None if not found."""
    return {
        name: locate_value(value, source_text, fuzzy=fuzzy)
        for name, value in fields.items()
    }
