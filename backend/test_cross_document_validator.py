
from app.cross_document_validator import validate_cross_documents

documents = [
    {
        "document_type": "packing_list",
        "fields": {
            "exporter_name": "GLOBAL TECH LOGISTICSGMBH",
            "consignee_name": "ALGERIA APPLIANCE CORP SARL",
            "total_gross_weight": "445.00 KG",
            "total_net_weight": "410.00 KG",
            "package_count": "2",
        },
    },
    {
        "document_type": "certificate_of_quality",
        "fields": {
            "exporter_name": "GLOBAL TECH LOGISTICSGMBH",
            "consignee_name": "ALGERIA APPLIANCE CORP SARL",
        },
    },
    {
        "document_type": "certificate_of_conformity",
        "fields": {
            "exporter_name": "GLOBAL TECH LOGISTICS GMBH",
            "consignee_name": "ALGERIA APPLIANCE CORP SARL",
        },
    },
]

result = validate_cross_documents(documents)

for check in result["checks"]:
    if check["check"] in ("Exporter / shipper", "Consignee"):
        print(check)

print("\nSummary:", result["summary"])
