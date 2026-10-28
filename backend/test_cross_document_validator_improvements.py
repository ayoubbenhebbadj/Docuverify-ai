from app.cross_document_validator import names_match, validate_cross_documents


def test_exporter_suffix_and_country_noise_are_normalized():
    assert names_match("Zohoor Albarryea Herbs", "Zohoor Albarryea Herbs ( FOR EXPORT)")
    assert names_match("Zohoor Albarryea Herbs", "ZOHOOR ALBARREYA HERBS EGYPT")


def test_arabic_consignee_spelling_matches_latin_name():
    assert names_match("BIOPPAM SARL", "بيوببام")


def test_package_fields_can_be_compared_across_supporting_certificates():
    documents = [
        {"document_type": "packing_list", "fields": {
            "exporter_name": "Zohoor Albarryea Herbs ( FOR EXPORT)",
            "consignee_name": "بيوببام", "total_gross_weight": "27667",
            "total_net_weight": "27500", "package_count": "1255",
        }},
        {"document_type": "certificate_of_quality", "fields": {
            "exporter_name": "Zohoor Albarryea Herbs ( FOR EXPORT)",
            "consignee_name": "BIOPPAM SARL", "total_gross_weight": "27667 KGS",
            "total_net_weight": "27500 KGS", "package_count": "1255",
        }},
        {"document_type": "phytosanitary_certificate", "fields": {
            "exporter_name": "ZOHOOR ALBARREYA HERBS EGYPT", "consignee_name": "BIOPPAM SARL",
            "total_gross_weight": "27667 KGS", "total_net_weight": "27500 KGS", "package_count": "1255",
        }},
    ]
    result = validate_cross_documents(documents)
    by_name = {item["check"]: item for item in result["checks"]}
    assert by_name["Exporter / shipper"]["status"] == "passed"
    assert by_name["Consignee"]["status"] == "passed"
    assert by_name["Gross weight"]["status"] == "passed"
    assert by_name["Net weight"]["status"] == "passed"
    assert by_name["Package count"]["status"] == "passed"


def test_invoice_arithmetic_uses_line_amounts_when_subtotal_is_not_printed():
    documents = [{"document_type": "commercial_invoice", "fields": {
        "invoice_number": "27", "total_amount": 87185,
        "freight_and_handling": 2600,
        "line_item_amounts": ["11475 USD", "6600 USD", "12300 USD", "5820 USD", "5040 USD", "37950 USD", "5400 USD"],
    }}]
    result = validate_cross_documents(documents)
    check = next(item for item in result["checks"] if item["check"] == "Invoice arithmetic")
    assert check["status"] == "passed"
    assert check["values"]["calculated_total"] == "87185"
