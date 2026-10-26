
from app.document_validator import evidence_matches

source = """
CARRIER: Ocean Carrier Lines
DESCRIPTION OF GOODS:
Industrial Valves, Power Converters, Sensor Arrays & Fastener Sets
3 PALLETS (187 PCS)
TOTAL GROSS WEIGHT: 465.00 KG
CONTAINER NO: MSCU-482910-4

PACKING DETAILS:
Euro Pallet (Wood)
Euro Pallet (Wood)
Euro Pallet (Custom)
"""

tests = [
    (
        "Carrier name",
        "Ocean Carrier Lines",
        True,
    ),
    (
        "Goods description",
        "Industrial Valves...Sensor Arrays & Fastener Sets",
        True,
    ),
    (
        "Package count",
        "3 PALLETS (187 PCS)",
        True,
    ),
    (
        "Gross weight",
        "TOTAL GROSS WEIGHT: 465.00 KG",
        True,
    ),
    (
        "Container number",
        "MSCU-482910-4",
        True,
    ),
    (
        "Package type",
        "Euro Pallet (Wood)",
        True,
    ),
    (
        "Unsupported evidence",
        "UNRELATED COMPANY XYZ",
        False,
    ),
]

for name, evidence, expected in tests:
    actual = evidence_matches(evidence, source)
    result = "PASS" if actual == expected else "FAIL"
    print(f"{result}: {name} (expected={expected}, actual={actual})")
