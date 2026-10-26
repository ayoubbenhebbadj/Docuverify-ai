
from app.document_extractor import DOCUMENT_SCHEMAS
from app.document_validator import REQUIRED_FIELDS, DATE_FIELDS


EXPECTED_SCHEMAS = {
    "certificate_of_quality": [
        "certificate_number",
        "issuer_name",
        "exporter_name",
        "consignee_name",
        "product_name",
        "goods_description",
        "inspection_results",
        "issue_date",
    ],
    "certificate_of_conformity": [
        "certificate_number",
        "issuer_name",
        "exporter_name",
        "consignee_name",
        "product_name",
        "goods_description",
        "applicable_standards",
        "conformity_status",
        "issue_date",
    ],
    "phytosanitary_certificate": [
        "certificate_number",
        "exporter_name",
        "consignee_name",
        "country_of_origin",
        "destination_country",
        "botanical_name",
        "goods_description",
        "quantity",
        "inspection_date",
        "issue_date",
    ],
    "fumigation_certificate": [
        "certificate_number",
        "issuer_name",
        "exporter_name",
        "consignee_name",
        "goods_description",
        "fumigant",
        "treatment_date",
        "duration",
        "temperature",
        "issue_date",
    ],
}

EXPECTED_REQUIRED_FIELDS = {
    "certificate_of_quality": [
        "certificate_number",
        "issuer_name",
        "goods_description",
    ],
    "certificate_of_conformity": [
        "certificate_number",
        "issuer_name",
        "goods_description",
        "conformity_status",
    ],
    "phytosanitary_certificate": [
        "certificate_number",
        "exporter_name",
        "consignee_name",
        "country_of_origin",
        "goods_description",
    ],
    "fumigation_certificate": [
        "certificate_number",
        "goods_description",
        "fumigant",
        "treatment_date",
    ],
}

errors = []

print("=== DOCUMENT SCHEMA CONFIGURATION TEST ===")

for document_type, expected_fields in EXPECTED_SCHEMAS.items():
    actual_fields = DOCUMENT_SCHEMAS.get(document_type)

    if actual_fields is None:
        errors.append(f"{document_type}: schema is missing")
    elif actual_fields != expected_fields:
        errors.append(
            f"{document_type}: schema fields do not match expected fields"
        )

    required_fields = REQUIRED_FIELDS.get(document_type)

    if required_fields is None:
        errors.append(f"{document_type}: required-field rules are missing")
    elif required_fields != EXPECTED_REQUIRED_FIELDS[document_type]:
        errors.append(
            f"{document_type}: required-field rules do not match"
        )

    print(
        f"{document_type}: "
        f"{'OK' if actual_fields == expected_fields else 'CHECK SCHEMA'}"
    )

# Check date-field coverage.
for field in ("inspection_date", "treatment_date"):
    if field not in DATE_FIELDS:
        errors.append(f"{field}: missing from DATE_FIELDS")

print("\n=== RESULT ===")

if errors:
    print(f"FAILED: {len(errors)} issue(s)")
    for error in errors:
        print("-", error)
else:
    print("PASSED: all four schemas and required-field rules are configured.")
