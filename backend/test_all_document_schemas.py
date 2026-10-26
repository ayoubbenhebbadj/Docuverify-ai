
from app.document_extractor import DOCUMENT_SCHEMAS

required_types = {
    "commercial_invoice",
    "packing_list",
    "bill_of_lading",
    "certificate_of_origin",
    "certificate_of_quality",
    "certificate_of_conformity",
    "phytosanitary_certificate",
    "fumigation_certificate",
}

assert set(DOCUMENT_SCHEMAS) == required_types

for document_type, schema in DOCUMENT_SCHEMAS.items():
    assert isinstance(schema, dict), (
        f"{document_type}: schema must be a dictionary"
    )
    assert isinstance(schema.get("description"), str), (
        f"{document_type}: missing description"
    )
    assert isinstance(schema.get("fields"), dict), (
        f"{document_type}: fields must be a dictionary"
    )
    assert schema["fields"], (
        f"{document_type}: fields cannot be empty"
    )

    print(f"PASS: {document_type} ({len(schema['fields'])} fields)")

print("\nAll eight document schemas are valid.")
