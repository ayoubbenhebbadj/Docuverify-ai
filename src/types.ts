// Mirrors backend/app/main.py -> POST /api/documents/analyze-package (verified against the source).
export type FieldValue = string | number | boolean | null | FieldValue[]
export interface InvalidField { field: string; reason: string }
export interface DocumentValidation {
  status: 'complete' | 'needs_review' | string   // document_validator.py returns "complete" or "needs_review"
  missing_fields: string[]
  invalid_fields: InvalidField[]
  unsupported_evidence: string[]
  warnings: string[]
}
export interface DocumentResult {
  document_type: string            // one of the 8 required ids, or "unknown"
  pages: number[]
  confidence: number | null        // 0..1, lowest page confidence in the group
  fields: Record<string, FieldValue>
  validation: DocumentValidation
  ocr_used?: boolean
  ocr_review_required?: boolean
  ocr_pages_low_confidence?: number[]
}
export type CheckStatus = 'passed' | 'mismatch' | 'needs_review'
export interface CrossCheck { check: string; status: CheckStatus | string; values: Record<string, unknown>; message: string }
export interface CrossValidation { summary: { total_checks: number; passed: number; mismatches: number; needs_review: number }; checks: CrossCheck[] }
export interface OcrSummary {
  ocr_used: boolean
  pages_processed: number[]
  pages_low_confidence: number[]
  pages_needing_ocr: number[]
  average_confidence?: number | null
  errors?: string[]
  review_required: boolean
}
export interface PackageResult {
  filename: string
  status: 'passed' | 'needs_review' | string
  page_count: number
  documents_found: number
  missing_documents: string[]
  unclassified_pages: number[]
  documents: DocumentResult[]
  cross_document_validation: CrossValidation
  ocr_summary?: OcrSummary
}
export interface OcrResult { filename: string; status: 'needs_ocr'; message: string; page_count: number }
export type AnalyzeResponse = PackageResult | OcrResult
export const isOcr = (r: AnalyzeResponse): r is OcrResult => r.status === 'needs_ocr'
