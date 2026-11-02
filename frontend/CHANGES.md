# Changes in this update

Backend
- `main.py`: longest-first extraction scheduling, one worker per document (max 6, `EXTRACTION_CONCURRENCY`),
  per-document failure isolation (`extraction_failed`), fixed pages being joined with a literal `\n`,
  OCR summary now has `pages_sparse` and `warnings`.
- `pdf_reader.py`: bounded parallel OCR (`OCR_WORKERS`), blank scans are not "unreadable".
- `ocr_engine.py`: `prepare_page_image` / thread-safe `ocr_image`; sparse-page fast path; Arabic data used when
  installed; `missing_recommended_languages()`; fixed `IndexError` on pages where Tesseract finds no words.
- `ai_extractor.py`: `AI_REASONING` control with automatic fallback; logs completion and reasoning tokens.
- `document_extractor.py`: values-only prompt + code-side evidence (`EXTRACTION_EVIDENCE`); one retry on empty / invalid JSON.
- `evidence.py` (new): locates values in source text (numbers with any separator, Arabic-Indic digits, dates in
  other layouts, units, lists, OCR-fuzzy); whole-token matching.
- `document_classifier.py`: rule-first classification; the AI sees only undecided pages.
- `tests/` (new, 44 tests, mocked LLM) + `pytest.ini`.

Cross-document name matching (false "Mismatch" on exporter / consignee)
- `cross_document_validator.py`: Arabic and Latin names are compared by consonant skeleton
  (`زهور البرية هبربس للتصدير` ~ `Zohoor Albarryea Herbs`); Arabic legal forms (ش.ذ.م.م, شركة) and
  "for export" (للتصدير) are ignored; Arabic spelling variants are unified.
- Names are compared against the majority group instead of only the first document, and the message now
  names the documents that differ.
- A "name" that is really an address fragment (e.g. `مجموعة ملكية`, "Zone industrielle ... Sect 02") is reported as
  `needs_review` (probable extraction error) instead of a company mismatch.
- `document_extractor.py`: prompts now say party names are the company name only, never the address.

Unstable / false weight mismatches (same file, different results on each run)
- Cause: the invoice prints weights per line but no total; the model was asked for "the total" and added the
  lines itself (24667, then 24652; the true sum is 27667).
- `derive.py` (new): the model only transcribes `line_item_gross_weights`, `line_item_net_weights` and
  `line_item_package_counts`; totals are summed in code (exact, identical on every run). A printed total is kept and
  checked against its own lines. Totals computed this way are marked `derived_fields`.
- `cross_document_validator.py`: a value that cannot be found in its own document's text is no longer compared as a
  fact; it is listed under `ignored` and the check becomes `needs_review` with an explanation.
- Scrambled Arabic names (`ش. قسم م. م بيوييام ملكية`): address words, legal-form fragments and numbers are removed, and the
  ب/ي/ن/ت OCR confusion is tolerated when comparing with the Latin spelling.

Frontend
- `types.ts`, `Results.tsx`: show OCR warnings, an "Extraction failed" badge, ignored (not compared) values and
  "computed from the line items" labels.

Not changed (still open from the review): cross-document `by_type` overwrite for duplicate document types,
`parse_weight_kg` European thousands separators, hard-coded footer identifier regex, line-item checks,
required-documents profiles, `.env` provider handling at import time.
