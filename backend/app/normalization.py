"""Multilingual normalization layer for Arabic/English document processing.

Handles:
- Arabic and English text normalization
- Arabic diacritics and character variants
- Arabic and Western numerals
- Whitespace and punctuation differences
- Company name variations and legal suffixes
- Dates, amounts, currencies, quantities, units
- Country names and aliases

Preserves original values. Never overwrites source with normalized representation.
Normalization is field-specific.
"""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher
from typing import Optional, Tuple, Dict, Any, List
from datetime import date

# =============================================================================
# CHARACTER NORMALIZATION
# =============================================================================

# Arabic-Indic and Extended Arabic-Indic digits to Western
_ARABIC_DIGITS_MAP = {
    '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
    '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
}
_ARABIC_DIGITS_TRANS = str.maketrans(_ARABIC_DIGITS_MAP)

# Arabic character normalization (remove diacritics, normalize variants)
_ARABIC_DIACRITICS = re.compile(r'[ً-ٰٟۖ-ۜ۟-۪ۨ-ۭ]')

# Arabic letter variants normalization
_ARABIC_LETTER_MAP = {
    # Alef variants
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ا': 'ا', 'ى': 'ا',
    # Teh marbuta
    'ة': 'ه',
    # Yeh variants
    'ي': 'ي', 'ى': 'ي',
    # Kaf variants
    'ك': 'ك', 'ک': 'ك',
    # Lam alef variants handled by NFKC
}
_ARABIC_LETTER_TRANS = str.maketrans(_ARABIC_LETTER_MAP)


def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text: remove diacritics, normalize letter variants."""
    if not text:
        return ""
    # NFKC handles ligatures like lam-alef
    text = unicodedata.normalize('NFKC', text)
    # Remove diacritics
    text = _ARABIC_DIACRITICS.sub('', text)
    # Normalize letter variants
    text = text.translate(_ARABIC_LETTER_TRANS)
    return text


def fold_digits(text: str) -> str:
    """Convert Arabic-Indic and Extended Arabic-Indic digits to Western."""
    if not text:
        return ""
    return text.translate(_ARABIC_DIGITS_TRANS)


# =============================================================================
# COMPANY NAME NORMALIZATION
# =============================================================================

# Legal suffixes in various languages
_LEGAL_SUFFIXES = {
    # English
    'ltd', 'limited', 'llc', 'inc', 'corp', 'corporation', 'plc', 'co', 'company',
    # French
    'sarl', 'sas', 'sa', 'ei', 'eurl', 'snnc', 'scop', 'scic',
    # German
    'gmbh', 'kg', 'ag', 'ohg', 'ug',
    # Arabic
    'شركة', 'شركه', 'مؤسسة', 'مؤسسه', 'مجموعة', 'مجموعه',
    # Spanish
    'sl', 'sa', 'sc',
    # Italian
    'srl', 'spa', 'snc', 'sas',
    # Dutch
    'bv', 'nv', 'cv',
    # Generic
    'co', 'ltd', 'inc',
}

# Address indicators
_ADDRESS_INDICATORS = {
    'zone', 'industrial', 'industrielle', 'sect', 'sector', 'secteur',
    'gp', 'groupe', 'loc', 'lot', 'rue', 'street', 'road', 'avenue', 'boulevard',
    'bp', 'lotissement', 'cite', 'bloc', 'wilaya', 'commune', 'alger', 'algeria', 'algerie',
    'zone', 'industrielle', 'industriel',
    # Arabic address words
    'المنطقة', 'المنطقه', 'منطقة', 'منطقه', 'الصناعية', 'الصناعيه', 'صناعية', 'صناعيه',
    'شارع', 'حي', 'ولاية', 'ولايه', 'الجزائر',
    'مجموعة', 'ملكية', 'مجموعة ملكية',
    'قسم', 'صناعية', 'صناعيه',
}


def normalize_company_name(value: str) -> str:
    """Normalize a company name for cross-document comparison."""
    if not value:
        return ""

    text = str(value).strip()

    # Remove registration and tax details
    text = re.split(
        r"[,;]|\b(?:EORI|VAT(?:\s+ID)?|Tax\s+ID|Registration\s+No\.?)\s*:",
        text, maxsplit=1, flags=re.IGNORECASE
    )[0]

    # Ignore descriptive exporter suffixes
    text = re.sub(r"\s*\(\s*for\s+export\s*\)\s*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bfor\s+export\b", " ", text, flags=re.IGNORECASE)

    # Normalize whitespace and punctuation
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .,:;-")

    # Normalize Arabic text
    if re.search(r'[؀-ۿ]', text):
        text = normalize_arabic_text(text)
        # Remove noise words
        tokens = [t for t in re.split(r'[\s.،]+', text) if t]
        kept = []
        for tok in tokens:
            is_arabic = bool(re.search(r'[؀-ۿ]', tok))
            if is_arabic and len(tok) == 1:
                continue  # single Arabic letters from legal forms
            if tok in {'للتصدير', 'لتصدير', 'التصدير', 'شركة', 'شركه', 'مؤسسة', 'مؤسسه',
                       'قسم', 'ملكيه', 'مجموعه', 'المنطقة', 'المنطقه',
                       'منطقة', 'منطقه', 'الصناعية', 'الصناعيه', 'صناعية', 'صناعيه',
                       'شارع', 'حي', 'ولاية', 'ولايه', 'الجزائر'}:
                continue
            kept.append(tok)
        text = " ".join(kept)
    else:
        text = text.lower()
        # Normalize legal suffixes spacing
        text = re.sub(r"(?<=[a-z])(?=(?:gmbh|ltd|limited|llc|inc|corp|sarl)\b)", " ", text)
        # Remove legal forms
        text = re.sub(r"\b(?:sarl|gmbh|ltd|limited|llc|inc|corp|corporation)\b", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+co\.?$", "", text)
        # Strip address suffix
        text = strip_address_suffix(text)

    return text


def strip_address_suffix(value: str) -> str:
    """Cut at the first address word (after at least one name word)."""
    if not value:
        return value
    tokens = str(value).split()

    def is_addr(tok: str) -> bool:
        t = tok.casefold().strip(".,;:()")
        return t in _ADDRESS_INDICATORS or t.startswith("nif") or any(c.isdigit() for c in t)

    # Everything after a trailing legal form is address
    for i, tok in enumerate(tokens[:-1]):
        flat = re.sub(r"[^a-z0-9]", "", tok.casefold())
        if i >= 1 and flat in _LEGAL_SUFFIXES:
            return " ".join(tokens[:i + 1])

    for i in range(1, len(tokens)):
        t = tokens[i].casefold().strip(".,;:()")
        if (t in _ADDRESS_INDICATORS or t.startswith("nif")) and \
                sum(is_addr(x) for x in tokens[i:]) >= 2:
            return " ".join(tokens[:i])
    return value


def _company_identity(value: str) -> str:
    """
    Extract the likely company identity from a company name that may
    have an address appended to it.

    This is intentionally conservative: only known address markers
    are treated as the beginning of an appended address.
    """
    text = normalize_company_name(value)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    address_markers = (
        r"\bzone industrielle\b",
        r"\bindustrial zone\b",
        r"\bloc(?:ation)?\s+\d+\b",
        r"\bouledmoussa\b",
        r"\bboumerdes\b",
        r"\balger\b",
        r"\balgeria\b",
        r"\balgerie\b",
    )

    for marker in address_markers:
        match = re.search(marker, text, flags=re.IGNORECASE)
        if match and match.start() > 0:
            text = text[:match.start()].strip()
            break

    return re.sub(r"\s+", " ", text).strip()


def looks_like_address(value: Optional[str]) -> bool:
    """Check if a value looks like an address fragment rather than a company name."""
    if not value:
        return False
    tokens = [t.casefold() for t in re.split(r"[\s.,،;:/\-]+", str(value)) if t]
    hits = sum(1 for t in tokens if t in _ADDRESS_INDICATORS)
    rest = [
        t for t in tokens
        if t not in _ADDRESS_INDICATORS and not any(c.isdigit() for c in t)
        and not (len(t) == 1 and re.search(r"[؀-ۿ]", t))
    ]
    return hits >= 2 and (not rest or hits >= 3)


# =============================================================================
# CONSONANT SKELETON (CROSS-SCRIPT MATCHING)
# =============================================================================

_AR_SKELETON = {
    "ب": "b", "پ": "b", "ت": "t", "ث": "t", "ط": "t", "ج": "j",
    "ح": "h", "ه": "h", "خ": "k", "ك": "k", "ق": "k", "د": "d", "ض": "d",
    "ذ": "z", "ز": "z", "ظ": "z", "ر": "r", "س": "s", "ص": "s", "ش": "s",
    "غ": "g", "ف": "f", "ل": "l", "م": "m", "ن": "n",
}
_LATIN_DIGRAPHS = (("sh", "s"), ("ch", "s"), ("kh", "k"), ("th", "t"),
                   ("ph", "f"), ("gh", "g"), ("dh", "z"))
_LATIN_SKELETON = {"p": "b", "v": "f", "c": "k", "q": "k", "x": "ks"}


def consonant_skeleton(value: str) -> str:
    """Script-independent consonant skeleton for cross-script matching."""
    if not value:
        return ""
    text = str(value).casefold()
    text = re.sub(r"[ً-ْـ]", "", text)  # diacritics, tatweel
    out = []
    for word in re.split(r"[^a-z؀-ۿ0-9]+", text):
        if not word:
            continue
        if re.search(r"[؀-ۿ]", word):
            word = re.sub(r"[هة]$", "", word)  # final ه/ة is a vowel
            letters = [_AR_SKELETON.get(ch, "") for ch in word]
        else:
            for src, dst in _LATIN_DIGRAPHS:
                word = word.replace(src, dst)
            letters = [_LATIN_SKELETON.get(ch, ch) for ch in word if ch not in "aeiouyw"]
        out.extend(letters)
    skeleton = "".join(out)
    return re.sub(r"(.)\1+", r"\1", skeleton)


# =============================================================================
# IDENTIFIER NORMALIZATION
# =============================================================================

def normalize_identifier(value: Optional[str]) -> str:
    """Normalize document numbers, tolerating common OCR confusions."""
    if not value:
        return ""
    text = re.sub(r"[^A-Za-z0-9]", "", str(value)).upper()
    return text.translate(str.maketrans("OIL", "011"))


# =============================================================================
# ARABIC TO LATIN TRANSLITERATION (for names)
# =============================================================================

_ARABIC_TO_LATIN = str.maketrans({
    "ا": "a", "أ": "a", "إ": "i", "آ": "a", "ى": "a",
    "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "h",
    "خ": "kh", "د": "d", "ذ": "th", "ر": "r", "ز": "z",
    "س": "s", "ش": "sh", "ص": "s", "ض": "d", "ط": "t",
    "ظ": "z", "ع": "a", "غ": "gh", "ف": "f", "ق": "q",
    "ك": "k", "ل": "l", "م": "m", "ن": "n", "ه": "h",
    "ة": "a", "و": "o", "ي": "i", "ئ": "i", "ؤ": "o",
    "ء": "", "پ": "p",
})


def arabic_to_latin_name(value: str) -> str:
    """Lightweight name transliteration for common Arabic spellings."""
    if not value:
        return ""
    return value.translate(_ARABIC_TO_LATIN)


# =============================================================================
# DATE NORMALIZATION
# =============================================================================

_MONTH_NAMES = {
    # English
    'jan': 1, 'january': 1, 'feb': 2, 'february': 2, 'mar': 3, 'march': 3,
    'apr': 4, 'april': 4, 'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
    'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
    'oct': 10, 'october': 10, 'nov': 11, 'november': 11, 'dec': 12, 'december': 12,
    # French
    'janv': 1, 'janvier': 1, 'févr': 2, 'fevr': 2, 'février': 2, 'mars': 3,
    'avr': 4, 'avril': 4, 'mai': 5, 'juin': 6, 'juil': 7, 'juillet': 7,
    'août': 8, 'aout': 8, 'sept': 9, 'septembre': 9,
    'oct': 10, 'octobre': 10, 'nov': 11, 'novembre': 11, 'déc': 12, 'dec': 12, 'décembre': 12,
    # Arabic (transliterated)
    'janvier': 1, 'fevrier': 2, 'mars': 3, 'avril': 4, 'mai': 5, 'juin': 6,
    'juillet': 7, 'aout': 8, 'septembre': 9, 'octobre': 10, 'novembre': 11, 'decembre': 12,
    # Arabic month names (common)
    'يناير': 1, 'فبراير': 2, 'مارس': 3, 'ابريل': 4, 'مايو': 5, 'يونيو': 6,
    'يوليو': 7, 'اغسطس': 8, 'سبتمبر': 9, 'اكتوبر': 10, 'نوفمبر': 11, 'ديسمبر': 12,
    'كانون الثاني': 1, 'شباط': 2, 'اذار': 3, 'نيسان': 4, 'ايار': 5, 'حزيران': 6,
    'تموز': 7, 'اب': 8, 'ايلول': 9, 'تشرين الاول': 10, 'تشرين الثاني': 11, 'كانون الاول': 12,
}


def _parse_arabic_date(text: str) -> Optional[date]:
    """Try to parse dates written in Arabic numerals or Arabic month names."""
    # Convert Arabic digits first
    text = fold_digits(text)
    # Try standard patterns
    return None  # Handled by general parser


_DATE_PATTERNS = [
    # YYYY-MM-DD (ISO)
    (re.compile(r'(?<!\d)(\d{4})[-/](\d{1,2})[-/](\d{1,2})(?!\d)'), 'ymd'),
    # DD/MM/YYYY or DD-MM-YYYY
    (re.compile(r'(?<!\d)(\d{1,2})[-/](\d{1,2})[-/](\d{4})(?!\d)'), 'dmy'),
    # MM/DD/YYYY (US)
    (re.compile(r'(?<!\d)(\d{1,2})[-/](\d{1,2})[-/](\d{4})(?!\d)'), 'mdy'),
    # DD Mon YYYY
    (re.compile(r'(?<!\d)(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})(?!\d)', re.IGNORECASE), 'dmy_named'),
    # Mon DD, YYYY
    (re.compile(r'([A-Za-z]{3,9})\s+(\d{1,2})[.,]?\s+(\d{4})', re.IGNORECASE), 'mdy_named'),
    # YYYY Mon DD
    (re.compile(r'(\d{4})\s+([A-Za-z]{3,9})\s+(\d{1,2})', re.IGNORECASE), 'ymd_named'),
]


def parse_date_flexible(text: str) -> Optional[date]:
    """Parse date from various formats, return ISO date object."""
    if not text:
        return None

    text = fold_digits(text).strip()

    # Try ISO format first
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass

    for pattern, fmt in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue

        try:
            if fmt == 'ymd':
                y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif fmt == 'dmy':
                d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif fmt == 'mdy':
                m, d, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif fmt == 'dmy_named':
                d = int(match.group(1))
                mon = match.group(2).lower()[:3]
                y = int(match.group(3))
                m = _MONTH_NAMES.get(mon)
                if not m:
                    continue
            elif fmt == 'mdy_named':
                mon = match.group(1).lower()[:3]
                d = int(match.group(2))
                y = int(match.group(3))
                m = _MONTH_NAMES.get(mon)
                if not m:
                    continue
            elif fmt == 'ymd_named':
                y = int(match.group(1))
                mon = match.group(2).lower()[:3]
                d = int(match.group(3))
                m = _MONTH_NAMES.get(mon)
                if not m:
                    continue
            else:
                continue

            return date(y, m, d)
        except (ValueError, IndexError):
            continue

    return None


def normalize_date(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Normalize date to ISO format. Returns (iso_string, original_string)."""
    if not value:
        return (None, value)
    parsed = parse_date_flexible(value)
    if parsed:
        return (parsed.isoformat(), value)
    return (None, value)


# =============================================================================
# NUMBER/AMOUNT NORMALIZATION
# =============================================================================

_NUMBER_TOKEN = re.compile(r"\d{1,3}(?:[ ,.]\d{3})+(?!\d)(?:[.,]\d+)?|\d+(?:[.,]\d+)?")


def _number_variants(token: str) -> set[Decimal]:
    """All sensible readings of a numeric token."""
    token = re.sub(r"\s+", "", token)
    variants: set[str] = set()
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            variants.add(token.replace(".", "").replace(",", "."))
        else:
            variants.add(token.replace(",", ""))
    elif "," in token:
        variants.add(token.replace(",", ""))
        variants.add(token.replace(",", "."))
    elif "." in token:
        variants.add(token)
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", token):
            variants.add(token.replace(".", ""))
    else:
        variants.add(token)
    out = set()
    for v in variants:
        try:
            out.add(Decimal(v).normalize())
        except InvalidOperation:
            continue
    return out


def parse_amount(text: str) -> Optional[Decimal]:
    """Parse monetary amount from text."""
    if not text:
        return None
    text = fold_digits(text)
    text = text.replace(",", "").replace("€", "").replace("$", "").replace("£", "")
    text = re.sub(r"\s+", "", text)
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


def parse_number(text: str) -> Optional[Decimal]:
    """Parse a numeric value or simple formatted number to Decimal."""
    if not text:
        return None
    text = fold_digits(text)
    text = text.replace(",", "").replace("€", "").replace("$", "").replace("£", "")
    text = re.sub(r"\s+", "", text)
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


def normalize_amount(value: str) -> Tuple[Optional[Decimal], Optional[str]]:
    """Normalize amount to Decimal. Returns (decimal_value, original_string)."""
    if not value:
        return (None, value)
    parsed = parse_amount(value)
    return (parsed, value)


# =============================================================================
# CURRENCY NORMALIZATION
# =============================================================================

_CURRENCY_ALIASES = {
    'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR', '€': 'EUR',
    'usd': 'USD', 'dollar': 'USD', 'dollars': 'USD', '$': 'USD',
    'gbp': 'GBP', 'pound': 'GBP', 'pounds': 'GBP', '£': 'GBP',
    'jpy': 'JPY', 'yen': 'JPY', '¥': 'JPY',
    'cny': 'CNY', 'rmb': 'CNY', 'yuan': 'CNY', '¥': 'JPY',  # Note: same symbol
    'mad': 'MAD', 'dhs': 'MAD', 'dh': 'MAD',
    'dzd': 'DZD', 'da': 'DZD',
    'tnd': 'TND', 'dt': 'TND',
    'egp': 'EGP', 'le': 'EGP', '£e': 'EGP',
    'sar': 'SAR', 'sr': 'SAR',
    'aed': 'AED', 'dh': 'AED',
}


def normalize_currency(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Normalize currency to ISO 4217 code. Returns (iso_code, original_string)."""
    if not value:
        return (None, value)
    text = str(value).strip().lower()
    # Check 3-letter code first
    if re.fullmatch(r'[a-z]{3}', text):
        return (text.upper(), value)
    # Check aliases
    for alias, iso in _CURRENCY_ALIASES.items():
        if alias in text:
            return (iso, value)
    return (None, value)


# =============================================================================
# WEIGHT/QUANTITY NORMALIZATION
# =============================================================================

_UNIT_CONVERSIONS = {
    # Weight to kg
    'kg': Decimal('1'), 'kgs': Decimal('1'), 'kilogram': Decimal('1'), 'kilograms': Decimal('1'),
    'g': Decimal('0.001'), 'gram': Decimal('0.001'), 'grams': Decimal('0.001'),
    'lb': Decimal('0.45359237'), 'lbs': Decimal('0.45359237'), 'pound': Decimal('0.45359237'), 'pounds': Decimal('0.45359237'),
    't': Decimal('1000'), 'ton': Decimal('1000'), 'tons': Decimal('1000'), 'tonne': Decimal('1000'), 'tonnes': Decimal('1000'), 'mt': Decimal('1000'),
    # Arabic weight units
    'كجم': Decimal('1'), 'كغ': Decimal('1'), 'كيلوجرام': Decimal('1'), 'كيلوغرام': Decimal('1'),
    'جرام': Decimal('0.001'), 'جرامات': Decimal('0.001'),
    # Volume (not converted to weight)
    'l': None, 'liter': None, 'liters': None, 'litre': None, 'litres': None,
    'm3': None, 'cbm': None,
    # Count
    'pcs': Decimal('1'), 'pieces': Decimal('1'), 'pc': Decimal('1'),
    'pkg': Decimal('1'), 'packages': Decimal('1'), 'pallets': Decimal('1'), 'pallet': Decimal('1'),
    'cartons': Decimal('1'), 'carton': Decimal('1'), 'boxes': Decimal('1'), 'box': Decimal('1'),
    'أعداد': Decimal('1'), 'عدد': Decimal('1'),
}


_WEIGHT_PATTERN = re.compile(
    r"(-?\d+(?:[.,]\d+)?)\s*"
    r"(kgs?|kilograms?|kilos?|grams?|g|lbs?|pounds?|tonnes?|tons?|mt|t|"
    r"كجم|كغ|كيلوجرام(?:ات)?|جرام(?:ات)?)"
    r"(?![a-z])",
    re.IGNORECASE
)


def parse_weight_kg(text: str) -> Optional[Decimal]:
    """Extract weight and convert to kilograms."""
    if not text:
        return None

    text = fold_digits(str(text)).strip().lower()
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)

    match = _WEIGHT_PATTERN.search(text)
    if not match:
        # Try numeric only (assume kg for weight fields)
        numeric = re.fullmatch(r"\s*-?\d+(?:[.,]\d+)?\s*", text)
        if not numeric:
            return None
        return Decimal(text.strip().replace(",", "."))

    amount = Decimal(match.group(1).replace(",", "."))
    unit = match.group(2).lower()

    # Arabic unit mapping
    if unit in ('كجم', 'كغ', 'كيلوجرام', 'كيلوغرام', 'كيلوجرامات', 'كيلوغرامات'):
        unit = 'kg'
    elif unit in ('جرام', 'جرامات'):
        unit = 'g'

    factor = _UNIT_CONVERSIONS.get(unit)
    if factor is None:
        return None  # Unknown or non-weight unit
    return amount * factor


def normalize_weight(value: str) -> Tuple[Optional[Decimal], Optional[str]]:
    """Normalize weight to kg. Returns (kg_value, original_string)."""
    if not value:
        return (None, value)
    parsed = parse_weight_kg(value)
    return (parsed, value)


def parse_quantity(text: str) -> Optional[Decimal]:
    """Parse quantity (count) from text."""
    if not text:
        return None
    text = fold_digits(text)
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)
    match = re.search(r"\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return Decimal(match.group())
    except InvalidOperation:
        return None


def normalize_quantity(value: str) -> Tuple[Optional[Decimal], Optional[str]]:
    """Normalize quantity. Returns (decimal_value, original_string)."""
    if not value:
        return (None, value)
    parsed = parse_quantity(value)
    return (parsed, value)


# =============================================================================
# COUNTRY NORMALIZATION
# =============================================================================

_COUNTRY_ALIASES = {
    # English
    'algeria': 'DZ', 'algerie': 'DZ', 'algérie': 'DZ',
    'france': 'FR', 'fr': 'FR',
    'china': 'CN', 'cn': 'CN',
    'india': 'IN', 'in': 'IN',
    'united states': 'US', 'usa': 'US', 'us': 'US',
    'germany': 'DE', 'de': 'DE',
    'italy': 'IT', 'it': 'IT',
    'spain': 'ES', 'es': 'ES',
    'turkey': 'TR', 'tr': 'TR',
    'united arab emirates': 'AE', 'uae': 'AE', 'ae': 'AE',
    'saudi arabia': 'SA', 'sa': 'SA',
    'morocco': 'MA', 'ma': 'MA',
    'tunisia': 'TN', 'tn': 'TN',
    'egypt': 'EG', 'eg': 'EG',
    # French
    'algérie': 'DZ', 'france': 'FR', 'chine': 'CN', 'inde': 'IN',
    'etats-unis': 'US', 'allemagne': 'DE', 'italie': 'IT', 'espagne': 'ES',
    'turquie': 'TR', 'emirats arabes unis': 'AE', 'arabie saoudite': 'SA',
    'maroc': 'MA', 'tunisie': 'TN', 'egypte': 'EG',
    # Arabic
    'الجزائر': 'DZ', 'فرنسا': 'FR', 'الصين': 'CN', 'الهند': 'IN',
    'الولايات المتحدة': 'US', 'المانيا': 'DE', 'ايطاليا': 'IT', 'اسبانيا': 'ES',
    'تركيا': 'TR', 'الامارات': 'AE', 'السعودية': 'SA', 'المغرب': 'MA',
    'تونس': 'TN', 'مصر': 'EG',
}


def normalize_country(value: str) -> Tuple[Optional[str], Optional[str]]:
    """Normalize country to ISO 3166-1 alpha-2 code. Returns (iso_code, original_string)."""
    if not value:
        return (None, value)
    text = str(value).strip().lower()
    # Check if already a 2-letter code
    if re.fullmatch(r'[a-z]{2}', text):
        return (text.upper(), value)
    # Check aliases
    for alias, iso in _COUNTRY_ALIASES.items():
        if alias in text:
            return (iso, value)
    return (None, value)


# =============================================================================
# FIELD-SPECIFIC NORMALIZATION ENTRY POINT
# =============================================================================

# Map field names to normalization functions
FIELD_NORMALIZERS = {
    # Company names
    'exporter_name': ('company_name', normalize_company_name),
    'consignee_name': ('company_name', normalize_company_name),
    'shipper_name': ('company_name', normalize_company_name),
    'notify_party': ('company_name', normalize_company_name),
    'issuer_name': ('company_name', normalize_company_name),
    'producer_name': ('company_name', normalize_company_name),
    'issuing_authority': ('company_name', normalize_company_name),
    'carrier_name': ('company_name', normalize_company_name),
    'buyer_name': ('company_name', normalize_company_name),
    'supplier_name': ('company_name', normalize_company_name),
    'company_name': ('company_name', normalize_company_name),

    # Identifiers
    'invoice_number': ('identifier', normalize_identifier),
    'packing_list_number': ('identifier', normalize_identifier),
    'bill_of_lading_number': ('identifier', normalize_identifier),
    'certificate_number': ('identifier', normalize_identifier),
    'booking_number': ('identifier', normalize_identifier),
    'container_numbers': ('identifier', normalize_identifier),
    'seal_numbers': ('identifier', normalize_identifier),
    'customs_declaration_number': ('identifier', normalize_identifier),

    # Dates
    'invoice_date': ('date', normalize_date),
    'issue_date': ('date', normalize_date),
    'on_board_date': ('date', normalize_date),
    'inspection_date': ('date', normalize_date),
    'treatment_date': ('date', normalize_date),

    # Amounts
    'amount': ('amount', normalize_amount),
    'total_amount': ('amount', normalize_amount),
    'subtotal': ('amount', normalize_amount),
    'freight_and_handling': ('amount', normalize_amount),
    'insurance_fee': ('amount', normalize_amount),
    'tax_amount': ('amount', normalize_amount),
    'line_item_amounts': ('amount', normalize_amount),
    'calculated_total': ('amount', normalize_amount),
    'declared_total': ('amount', normalize_amount),

    # Currency
    'currency': ('currency', normalize_currency),

    # Weights
    'total_gross_weight': ('weight', normalize_weight),
    'total_net_weight': ('weight', normalize_weight),
    'line_item_gross_weights': ('weight', normalize_weight),
    'line_item_net_weights': ('weight', normalize_weight),
    'package_weight': ('weight', normalize_weight),

    # Quantities
    'total_quantity': ('quantity', normalize_quantity),
    'quantity': ('quantity', normalize_quantity),
    'package_count': ('quantity', normalize_quantity),
    'line_item_package_counts': ('quantity', normalize_quantity),
    'package_count': ('quantity', normalize_quantity),

    # Countries
    'country_of_origin': ('country', normalize_country),
    'destination_country': ('country', normalize_country),
}


def normalize_field(field_name: str, value: str) -> Tuple[Any, str]:
    """
    Normalize a field value according to its type.
    Returns (normalized_value, original_value).
    """
    if field_name in FIELD_NORMALIZERS:
        _, normalizer = FIELD_NORMALIZERS[field_name]
        return normalizer(value)
    # Default: return as-is
    return (value, value)


def normalize_field_pair(field_name: str, value_a: str, value_b: str) -> Tuple[Any, Any, str, str]:
    """
    Normalize two values for the same field for comparison.
    Returns (norm_a, norm_b, orig_a, orig_b).
    """
    norm_a, orig_a = normalize_field(field_name, value_a)
    norm_b, orig_b = normalize_field(field_name, value_b)
    return (norm_a, norm_b, orig_a, orig_b)


# =============================================================================
# COMPANY NAME MATCHING (re-exported from cross_document_validator for convenience)
# =============================================================================

# =============================================================================
# COMPANY NAME MATCHING
# =============================================================================

def names_match(a: str, b: str, threshold: float = 0.88) -> bool:
    """Compare normalized company names, including simple Arabic transliteration.

    Uses consonant skeletons, transliteration, and fuzzy matching to determine
    if two company names refer to the same entity across different scripts/languages.
    """
    squash = lambda v: re.sub(r"[^a-z0-9]", "", v.casefold())
    a_norm = normalize_company_name(a)
    b_norm = normalize_company_name(b)

    # Compare the core company identity when address details are appended.
    a_identity = _company_identity(a)
    b_identity = _company_identity(b)
    if a_identity and b_identity and a_identity == b_identity:
        return True

    a_has_arabic = bool(re.search(r"[؀-ۿ]", a_norm))
    b_has_arabic = bool(re.search(r"[؀-ۿ]", b_norm))

    # Cross-script comparison on consonant skeletons (handles Arabic vs Latin spellings
    # and common OCR letter confusions such as ب read as ي).
    if a_has_arabic or b_has_arabic:
        sk_a, sk_b = consonant_skeleton(a_norm), consonant_skeleton(b_norm)
        if sk_a and sk_b:
            if sk_a == sk_b:
                return True
            # OCR often inserts a stray ه ("بيوبيهام" for "بيوببام"); retry without h.
            nh_a, nh_b = sk_a.replace("h", ""), sk_b.replace("h", "")
            if min(len(nh_a), len(nh_b)) >= 2 and nh_a == nh_b:
                return True
            if min(len(sk_a), len(sk_b)) >= 5 and \
                    SequenceMatcher(None, sk_a, sk_b).ratio() >= 0.85:
                return True

    candidates_a = {squash(a_norm)}
    candidates_b = {squash(b_norm)}
    if a_has_arabic:
        candidates_a.add(squash(arabic_to_latin_name(a_norm)))
    if b_has_arabic:
        candidates_b.add(squash(arabic_to_latin_name(b_norm)))

    # The exporter country is sometimes appended to the name by OCR/extraction
    # even though the document has a separate country field.
    country_suffixes = ("egypt", "algeria", "algerie", "tunisia", "morocco", "china", "india")
    for candidate_set in (candidates_a, candidates_b):
        candidate_set.update(
            candidate[:-len(country)]
            for candidate in list(candidate_set)
            for country in country_suffixes
            if candidate.endswith(country) and len(candidate) > len(country) + 3
        )

    # In Arabic company names, ب commonly stands in for Latin p. If either
    # side is Arabic, compare a b/p-neutral variant as well.
    if a_has_arabic or b_has_arabic:
        candidates_a |= {v.replace("p", "b") for v in list(candidates_a)}
        candidates_a |= {v.replace("b", "p") for v in list(candidates_a)}
        candidates_b |= {v.replace("p", "b") for v in list(candidates_b)}
        candidates_b |= {v.replace("b", "p") for v in list(candidates_b)}

    candidates_a.discard("")
    candidates_b.discard("")
    if not candidates_a or not candidates_b:
        return False
    if candidates_a.intersection(candidates_b):
        return True
    # One side may omit trailing descriptors ("... International Trading Co").
    for left in candidates_a:
        for right in candidates_b:
            short, long_ = sorted((left, right), key=len)
            if len(short) >= 8 and long_.startswith(short):
                return True
    return max(
        SequenceMatcher(None, left, right).ratio()
        for left in candidates_a for right in candidates_b
    ) >= threshold


# Export consonant_skeleton for backward compatibility
def consonant_skeleton(value: str) -> str:
    """Script-independent consonant skeleton (re-exported for tests)."""
    if not value:
        return ""
    text = str(value).casefold()
    text = re.sub(r"[ً-ْـ]", "", text)  # diacritics, tatweel
    out = []
    for word in re.split(r"[^a-z؀-ۿ0-9]+", text):
        if not word:
            continue
        if re.search(r"[؀-ۿ]", word):
            word = re.sub(r"[هة]$", "", word)  # final ه/ة is a vowel (-a)
            letters = [_AR_SKELETON.get(ch, "") for ch in word]
        else:
            for src, dst in _LATIN_DIGRAPHS:
                word = word.replace(src, dst)
            letters = [_LATIN_SKELETON.get(ch, ch) for ch in word if ch not in "aeiouyw"]
        out.extend(letters)
    skeleton = "".join(out)
    return re.sub(r"(.)\1+", r"\1", skeleton)


def parse_date_flexible(text: str) -> Optional[date]:
    """Parse date from various formats, return ISO date object."""
    if not text:
        return None

    text = fold_digits(text).strip()

    # Try ISO format first
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass

    for pattern, fmt in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue

        try:
            if fmt == 'ymd':
                y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif fmt == 'dmy':
                d, m, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif fmt == 'mdy':
                m, d, y = int(match.group(1)), int(match.group(2)), int(match.group(3))
            elif fmt == 'dmy_named':
                d = int(match.group(1))
                mon = match.group(2).lower()[:3]
                y = int(match.group(3))
                m = _MONTH_NAMES.get(mon)
                if not m:
                    continue
            elif fmt == 'mdy_named':
                mon = match.group(1).lower()[:3]
                d = int(match.group(2))
                y = int(match.group(3))
                m = _MONTH_NAMES.get(mon)
                if not m:
                    continue
            elif fmt == 'ymd_named':
                y = int(match.group(1))
                mon = match.group(2).lower()[:3]
                d = int(match.group(3))
                m = _MONTH_NAMES.get(mon)
                if not m:
                    continue
            else:
                continue

            return date(y, m, d)
        except (ValueError, IndexError):
            continue

    return None