import type { AnalyzeResponse } from '../types'

export const DEFAULT_DEV_API_URL = 'http://127.0.0.1:8000'
export const DEFAULT_PROD_API_URL = 'https://docuverify-backend-l6g7.onrender.com'

/**
 * Normalizes an API base URL:
 * - Trims whitespace
 * - Strips trailing slashes
 * - Strips a trailing '/api' so endpoint paths (e.g. '/api/health') never produce '/api/api'
 */
export function normalizeApiUrl(raw?: string | null): string {
  if (!raw) return ''
  let url = raw.trim().replace(/\/+$/, '')
  if (url.endsWith('/api')) {
    url = url.slice(0, -4).replace(/\/+$/, '')
  }
  return url
}

/**
 * Resolves the API base URL based on environment variables and execution mode.
 * - Prioritizes import.meta.env.VITE_API_URL
 * - Falls back to import.meta.env.VITE_API_BASE_URL (for backward compatibility)
 * - If neither is provided:
 *     - In local development (isDev = true): falls back to DEFAULT_DEV_API_URL ("http://127.0.0.1:8000")
 *     - In production builds (isDev = false): falls back to DEFAULT_PROD_API_URL ("https://docuverify-backend-l6g7.onrender.com")
 *       ensuring production requests never accidentally use localhost.
 */
export function resolveApiBaseUrl(
  envUrl?: string | null,
  envBaseUrl?: string | null,
  isDev: boolean = false
): string {
  const chosen = (envUrl && envUrl.trim()) || (envBaseUrl && envBaseUrl.trim())
  if (chosen) {
    const normalized = normalizeApiUrl(chosen)
    if (normalized) return normalized
  }
  return isDev ? DEFAULT_DEV_API_URL : DEFAULT_PROD_API_URL
}

const env =
  typeof import.meta !== 'undefined' && (import.meta as unknown as { env?: Record<string, string | boolean> }).env
    ? (import.meta as unknown as { env: Record<string, string | boolean> }).env
    : {}

export const API_BASE_URL: string = resolveApiBaseUrl(
  env.VITE_API_URL as string | undefined,
  env.VITE_API_BASE_URL as string | undefined,
  Boolean(env.DEV)
)

export class ApiError extends Error {
  kind: 'network' | 'http' | 'format'
  status?: number
  hint?: string

  constructor(
    message: string,
    kind: 'network' | 'http' | 'format',
    status?: number,
    hint?: string
  ) {
    super(message)
    this.kind = kind
    this.status = status
    this.hint = hint
  }
}

/** FastAPI errors are {"detail": "text"} or {"detail": [{"msg": ...}]} (422 validation). */
function detailOf(body: unknown): string | undefined {
  const d = (body as { detail?: unknown } | null)?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) {
    return d.map((x) => (x as { msg?: string }).msg).filter(Boolean).join('; ') || undefined
  }
  return undefined
}

function hintFor(status: number, detail: string): string | undefined {
  const d = detail.toLowerCase()
  if (status === 413) return 'Reduce the file size (the backend limit is 10 MB) and try again.'
  if (d.includes('password')) return 'Remove the password protection from the PDF and upload it again.'
  if (
    d.includes('not appear to be a valid pdf') ||
    d.includes('not a valid or readable') ||
    d.includes('no pages') ||
    d.includes('empty')
  ) {
    return 'Check that the file opens normally in a PDF viewer, then upload it again.'
  }
  if (d.includes('unsupported document type')) {
    return 'The backend could not process a group of pages it could not identify. Check the merged PDF for unrelated or unreadable pages.'
  }
  if (d.includes('ai returned')) {
    return 'The AI service returned an unusable answer. Try again; if it keeps happening, tell your administrator.'
  }
  if (status === 502) {
    return 'This can be a temporary AI provider outage or an exhausted provider credit balance. The backend hides the cause from the browser, so ask your administrator to check the backend terminal.'
  }
  if (status === 429 || status === 503) {
    return 'The service is busy or temporarily unavailable. Wait a moment and retry.'
  }
  return undefined
}

function networkErrorHint(baseUrl: string): string {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'your frontend origin'
  if (import.meta.env.DEV) {
    return `Check that the backend is running at ${baseUrl} and that its CORS policy allows requests from ${origin}.`
  }
  return `Could not connect to the backend at ${baseUrl}. Ensure the backend service is up and allows requests from ${origin}.`
}

/**
 * Generic helper for multipart file uploads to backend endpoints.
 * Crucial: Do NOT manually set Content-Type header so the browser automatically sets
 * multipart/form-data with the correct boundary parameter.
 */
async function postFile<T = unknown>(
  endpointPath: string,
  file: File,
  signal?: AbortSignal
): Promise<T> {
  const body = new FormData()
  body.append('file', file) // Field name required by FastAPI backend

  const cleanEndpoint = endpointPath.startsWith('/') ? endpointPath : `/${endpointPath}`
  const targetUrl = `${API_BASE_URL}${cleanEndpoint}`
  let res: Response

  try {
    res = await fetch(targetUrl, {
      method: 'POST',
      body,
      signal,
    })
  } catch (e) {
    if ((e as Error).name === 'AbortError') throw e
    throw new ApiError(
      'Could not reach the DocuVerify backend.',
      'network',
      undefined,
      networkErrorHint(API_BASE_URL)
    )
  }

  let json: unknown = null
  try {
    json = await res.json()
  } catch {
    /* non-JSON body */
  }

  if (!res.ok) {
    const detail = detailOf(json) ?? `The server returned an error (HTTP ${res.status}).`
    throw new ApiError(detail, 'http', res.status, hintFor(res.status, detail))
  }

  return json as T
}

/**
 * Uploads a merged shipment package PDF to verify consistency across all documents.
 * Endpoint: POST /api/documents/analyze-package
 */
export async function analyzePackage(file: File, signal?: AbortSignal): Promise<AnalyzeResponse> {
  const json = await postFile<unknown>('/api/documents/analyze-package', file, signal)
  const r = json as { status?: unknown; filename?: unknown } | null
  if (!r || typeof r.status !== 'string' || typeof r.filename !== 'string') {
    throw new ApiError('The backend returned a response in an unexpected format.', 'format')
  }
  return json as AnalyzeResponse
}

/**
 * Analyzes a single document PDF (e.g. standalone commercial invoice).
 * Endpoint: POST /api/documents/analyze
 */
export async function analyzeDocument(file: File, signal?: AbortSignal): Promise<unknown> {
  return postFile('/api/documents/analyze', file, signal)
}

/**
 * Classifies pages in a document without full field extraction.
 * Endpoint: POST /api/documents/classify
 */
export async function classifyDocuments(file: File, signal?: AbortSignal): Promise<unknown> {
  return postFile('/api/documents/classify', file, signal)
}

/**
 * Extracts raw and OCR text from a PDF.
 * Endpoint: POST /api/documents/extract-text
 */
export async function extractDocumentText(file: File, signal?: AbortSignal): Promise<unknown> {
  return postFile('/api/documents/extract-text', file, signal)
}

/**
 * Checks connectivity to the backend health endpoint.
 * Endpoint: GET /api/health
 */
export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`, { signal })
    return res.ok
  } catch {
    return false
  }
}
