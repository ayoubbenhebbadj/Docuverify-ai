"""Company-name comparison across documents (values taken from a real result)."""
import pytest

from app.cross_document_validator import (
    consonant_skeleton, looks_like_address, names_match, normalize_company_name,
    validate_cross_documents,
)

EXPORTER = {
    "commercial_invoice": "Zohoor Albarryea Herbs",
    "packing_list": "Zohoor Albarryea Herbs (FOR EXPORT)",
    "certificate_of_origin": "زهور البرية هبربس للتصدير",
    "certificate_of_quality": "Zohoor Albarryea Herbs ( FOR EXPORT)",
    "certificate_of_conformity": "Zohoor Albarryea Herbs (FOR EXPORT)",
    "phytosanitary_certificate": "ZOHOOR ALBARRYEA HERBS",
    "fumigation_certificate": "Zohoor Albarryea Herbs For Export",
}
CONSIGNEE_OK = {
    "commercial_invoice": "BIOPPAM SARL",
    "packing_list": "بيوببام",
    "certificate_of_quality": "BIOPPAM SARL",
    "phytosanitary_certificate": "BIOPPAM SARL",
    "fumigation_certificate": "BIOPPAM SARL",
}


def run(exporter, consignee):
    docs = {}
    for t, v in exporter.items():
        docs.setdefault(t, {})["exporter_name"] = v
    for t, v in consignee.items():
        docs.setdefault(t, {})["consignee_name"] = v
    result = validate_cross_documents([{"document_type": t, "fields": f} for t, f in docs.items()])
    return {c["check"]: c for c in result["checks"]}


def test_exporter_in_arabic_matches_the_latin_spellings():
    assert run(EXPORTER, CONSIGNEE_OK)["Exporter / shipper"]["status"] == "passed"


def test_consignee_in_arabic_matches():
    assert run(EXPORTER, CONSIGNEE_OK)["Consignee"]["status"] == "passed"


def test_address_fragment_is_an_extraction_problem_not_a_mismatch():
    bad = dict(CONSIGNEE_OK, certificate_of_origin="مجموعة ملكية")
    check = run(EXPORTER, bad)["Consignee"]
    assert check["status"] == "needs_review"
    assert "Certificate of origin" in check["message"] and "address" in check["message"]


def test_a_really_different_company_is_still_a_mismatch_and_named():
    other = dict(CONSIGNEE_OK, certificate_of_quality="NOVA PHARMA SARL")
    check = run(EXPORTER, other)["Consignee"]
    assert check["status"] == "mismatch"
    assert "Certificate of quality" in check["message"]
    assert "Commercial invoice" not in check["message"]       # the majority is not blamed


def test_a_really_different_arabic_company_is_still_a_mismatch():
    other = dict(CONSIGNEE_OK, certificate_of_origin="ش.ذ.م.م نوفا فارما")
    assert run(EXPORTER, other)["Consignee"]["status"] == "mismatch"


def test_first_document_being_odd_does_not_fail_everyone():
    odd_first = {"commercial_invoice": "Wrong Co", **{k: v for k, v in CONSIGNEE_OK.items() if k != "commercial_invoice"}}
    check = run(EXPORTER, odd_first)["Consignee"]
    assert check["status"] == "mismatch" and "Commercial invoice" in check["message"]


@pytest.mark.parametrize("a,b", [
    ("زهور البرية هبربس للتصدير", "Zohoor Albarryea Herbs"),
    ("ش.ذ.م.م بيوببام", "BIOPPAM SARL"),
    ("Zohoor Al Barryea Herbs", "ZOHOOR ALBARRYEA HERBS (FOR EXPORT)"),
    ("TIANJIN LIESI INTERNATIONAL TRADING CO.,LTD", "Tianjin Liesi International"),
])
def test_same_company(a, b):
    assert names_match(normalize_company_name(a), normalize_company_name(b))


@pytest.mark.parametrize("a,b", [
    ("زهور البرية هبربس للتصدير", "BIOPPAM SARL"),
    ("بيوببام", "Zohoor Albarryea Herbs"),
    ("Alpha Foods", "Omega Chemicals"),
    ("شركة النور", "Zohoor Albarryea Herbs"),
])
def test_different_company(a, b):
    assert not names_match(normalize_company_name(a), normalize_company_name(b))


def test_address_detection():
    assert looks_like_address("مجموعة ملكية")
    assert looks_like_address("المنطقة الصناعية قسم 02")
    assert looks_like_address("Zone industrielle Ouled Moussa Sect 02 Gp 235 Loc 3")
    assert not looks_like_address("BIOPPAM SARL")
    assert not looks_like_address("بيوببام")
    assert not looks_like_address("Zone Pharma SARL")        # one address-like word is not enough


def test_skeleton_folds_cross_script_sounds():
    assert consonant_skeleton("BIOPPAM") == consonant_skeleton("بيوببام")


def test_scrambled_arabic_consignee_from_a_real_scan():
    """Certificate of origin: legal-form letters and address words mixed into the name,
    and OCR read ب as ي (بيوببام -> بيوييام)."""
    garbled = dict(CONSIGNEE_OK, certificate_of_origin="ش. قسم م. م بيوييام ملكية")
    check = run(EXPORTER, garbled)["Consignee"]
    assert check["status"] == "passed", check["message"]


def test_cleaning_keeps_the_name_and_drops_the_noise():
    assert normalize_company_name("ش. قسم م. م بيوييام ملكية") == "بيوييام"
    assert normalize_company_name("ش.ذ.م.م بيوببام") == "بيوببام"


def test_ocr_confusion_does_not_make_different_companies_match():
    assert not names_match(normalize_company_name("بيوييام"), normalize_company_name("NOVA PHARMA"))
    assert not names_match(normalize_company_name("بيوييام"), normalize_company_name("Zohoor Albarryea Herbs"))


def test_ocr_stray_h_and_address_suffix_do_not_cause_mismatch():
    from app.cross_document_validator import strip_address_suffix, names_match, normalize_company_name as n
    assert strip_address_suffix(
        "BIOPPAM SARL ZONE INDUSTRIELLE SECT 02 GP 235 LOC 3 OULED MOUSSA 16000 ALGERIA NIF:002035072889131"
    ) == "BIOPPAM SARL"
    assert strip_address_suffix("Pharma Zone SARL") == "Pharma Zone SARL"
    assert names_match(n("ش. ذ. م. م بيوبيهام"), n("BIOPPAM SARL"))
    assert not names_match(n("ش.ذ.م.م نوفا فارما"), n("BIOPPAM SARL"))


def test_ocr_noise_and_address_after_legal_suffix():
    from app.cross_document_validator import names_match, normalize_company_name as n
    clean = n("TIANJIN LIESI INTERNATIONAL TRADING CO.,LTD")
    noisy = n("TIANJIN LIESI INTERNATIONAL TRADING ATE LTD TIANJIN FREE TRADE ZONE CENTRAL BUSINESS DISTRICT VISTA ESTATE 90-1-430 ROOM, CHINA")
    assert names_match(clean, noisy)
    assert not names_match(n("Acme Pharma Ltd"), n("Beta Foods Ltd"))


def test_invoice_number_mismatch_names_the_odd_document():
    from app.cross_document_validator import validate_cross_documents as v
    docs = [
        {"document_type": "commercial_invoice", "fields": {"invoice_number": "TL2026061101"}},
        {"document_type": "packing_list", "fields": {"invoice_number": "TL2026051301"}},
        {"document_type": "certificate_of_origin", "fields": {"invoice_number": "TL2026051301"}},
    ]
    check = [c for c in v(docs)["checks"] if c["check"] == "Invoice number"][0]
    assert check["status"] == "mismatch" and "Commercial invoice" in check["message"]
