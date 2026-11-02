"""Evidence is located in code; text below is taken from the real sample scans."""
from app.evidence import build_evidence, locate_value

INVOICE = """Invoice No : 27
Date : 30/ 06/2026
THYME ((ORIGANO) LOT NO : Z26
G.W :8534 KG
N.W : 8500 KG
1350 USD
PER TON 0 11475 USD
GUM ARABIC (RESIN) LOT NO : Z30
12650 USD 0 37950 USD
Grand Total ( Only EIGHTY SEVEN THAOUSAND ... ( CFR ALGERIA PORT ) 87185 USD
FROM : Zohoor Albarryea Herbs
"""

CHINA = """Date of Issue 12 Jun.,2026
Date : 2026.06.24
Certificate dated SEP.17,2026
Total Gross 21,540.000 KGS 65.0000 CBM
٢٧٥٠٠ كجم
"""


def test_plain_string_returns_its_source_line():
    quote = locate_value("Zohoor Albarryea Herbs", INVOICE)
    assert quote == "FROM : Zohoor Albarryea Herbs"


def test_numbers_match_regardless_of_separators_and_type():
    assert "87185" in locate_value(87185, INVOICE)
    assert "11475" in locate_value(11475.0, INVOICE)
    assert locate_value("21540 KG", CHINA) is not None          # 21,540.000 KGS
    assert locate_value(27500, CHINA) is not None               # Arabic-Indic digits


def test_european_thousands_separator():
    assert locate_value(27500, "Net weight 27.500 KGS") is not None
    assert locate_value(27500, "Net weight 27,500 KGS") is not None
    assert locate_value(27500, "Net weight 27 500 KGS") is not None


def test_a_wrong_number_is_not_found():
    assert locate_value(87186, INVOICE) is None
    assert locate_value("27501 KG", CHINA) is None


def test_dates_in_other_layouts():
    assert locate_value("2026-06-30", INVOICE) is not None      # 30/ 06/2026
    assert locate_value("2026-06-12", CHINA) is not None        # 12 Jun.,2026
    assert locate_value("2026-06-24", CHINA) is not None        # 2026.06.24
    assert locate_value("2026-09-17", CHINA) is not None        # SEP.17,2026
    assert locate_value("2026-07-30", INVOICE) is None


def test_list_requires_every_element():
    assert locate_value([11475, 37950], INVOICE) is not None
    assert locate_value([11475, 99999], INVOICE) is None


def test_value_not_in_document_gets_no_evidence():
    assert locate_value("Some Other Company", INVOICE) is None
    assert build_evidence({"a": "Some Other Company", "b": 87185}, INVOICE)["a"] is None


def test_unit_word_must_also_exist():
    # number exists, but the text never mentions tonnes
    assert locate_value("8534 tonnes", INVOICE) is None


def test_ocr_noise_needs_fuzzy_mode():
    noisy = "ZONE INDUSTRIELLE SECT 02 GP 235 LOC 3 OULEDMOUSSA BOUMERDES"
    value = "ZONE INDUSTRIELLE SECT 02 GP 235 LOC 3 OULEDMOUSSA BOUMERDFS"
    assert locate_value(value, noisy) is None
    assert locate_value(value, noisy, fuzzy=True) is not None


def test_short_value_must_not_match_inside_a_longer_number():
    text = "TEL : (+20) 1148562277\nInvoice No : 27"
    assert locate_value("27", text) == "Invoice No : 27"
    assert locate_value("27", "TEL : (+20) 1148562277") is None


def test_adjacent_table_numbers_stay_separate():
    row = "COSTUS 220 11000 11440"
    assert locate_value(220, row) == row
    assert locate_value(11000, row) == row
    assert locate_value(11440, row) == row
    assert locate_value(220110, row) is None            # not a merged number
    assert locate_value(22011000, row) is None


def test_grouped_numbers_still_parse():
    assert locate_value(21540, "G.W. 21,540.000 KGS") is not None
    assert locate_value(1234.56, "total 1.234,56 EUR") is not None
    assert locate_value(27500, "N.W. 27 500 KG") is not None
