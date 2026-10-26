
def get_package_status(
    missing_documents,
    unclassified_pages,
    document_results,
    cross_validation,
):
    document_validation_issues = [
        result
        for result in document_results
        if result["validation"].get("status")
        not in ("passed", "complete")
    ]

    mismatches = cross_validation["summary"]["mismatches"]
    cross_review = cross_validation["summary"]["needs_review"]

    if (
        missing_documents
        or unclassified_pages
        or document_validation_issues
        or mismatches
        or cross_review
    ):
        return "needs_review"

    return "passed"


# Test 1: Everything is valid.
assert get_package_status(
    [],
    [],
    [{"validation": {"status": "complete"}}],
    {"summary": {"mismatches": 0, "needs_review": 0}},
) == "passed"

# Test 2: Missing required documents.
assert get_package_status(
    ["fumigation_certificate"],
    [],
    [{"validation": {"status": "complete"}}],
    {"summary": {"mismatches": 0, "needs_review": 0}},
) == "needs_review"

# Test 3: A document requires review.
assert get_package_status(
    [],
    [],
    [{"validation": {"status": "needs_review"}}],
    {"summary": {"mismatches": 0, "needs_review": 0}},
) == "needs_review"

# Test 4: Cross-document mismatch.
assert get_package_status(
    [],
    [],
    [{"validation": {"status": "complete"}}],
    {"summary": {"mismatches": 1, "needs_review": 0}},
) == "needs_review"

print("PASS: Valid package returns passed.")
print("PASS: Missing documents return needs_review.")
print("PASS: Document validation issues return needs_review.")
print("PASS: Cross-document mismatches return needs_review.")
print("\nAll package-status tests passed.")
