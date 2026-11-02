import type { AnalyzeResponse } from '../types'

export const API_BASE_URL: string = ((import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://127.0.0.1:8000').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message: string, public kind: 'network' | 'http' | 'format', public status?: number, public hint?: string) { super(message) }
}

/** FastAPI errors are {"detail": "text"} or {"detail": [{"msg": ...}]} (422 validation). */
function detailOf(body: unknown): string | undefined {
  const d = (body as { detail?: unknown } | null)?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map(x => (x as { msg?: string }).msg).filter(Boolean).join('; ') || undefined
  return undefined
}
function hintFor(status: number, detail: string): string | undefined {
  const d = detail.toLowerCase()
  if (status === 413) return 'Reduce the file size (the backend limit is 10 MB) and try again.'
  if (d.includes('password')) return 'Remove the password protection from the PDF and upload it again.'
  if (d.includes('not appear to be a valid pdf') || d.includes('not a valid or readable') || d.includes('no pages') || d.includes('empty')) return 'Check that the file opens normally in a PDF viewer, then upload it again.'
  if (d.includes('unsupported document type')) return 'The backend could not process a group of pages it could not identify. Check the merged PDF for unrelated or unreadable pages.'
  if (d.includes('ai returned')) return 'The AI service returned an unusable answer. Try again; if it keeps happening, tell your administrator.'
  if (status === 502) return 'This can be a temporary AI provider outage or an exhausted provider credit balance. The backend hides the cause from the browser, so ask your administrator to check the backend terminal.'
  if (status === 429 || status === 503) return 'The service is busy or temporarily unavailable. Wait a moment and retry.'
  return undefined
}

export async function analyzePackage(file: File, signal?: AbortSignal): Promise<AnalyzeResponse> {
  const body = new FormData()
  body.append('file', file) // field name required by the backend; no Content-Type header so the browser sets the boundary
  let res: Response
  try { res = await fetch(`${API_BASE_URL}/api/documents/analyze-package`, { method: 'POST', body, signal }) }
  catch (e) {
    if ((e as Error).name === 'AbortError') throw e
    throw new ApiError('Could not reach the DocuVerify backend.', 'network', undefined, `Check that the backend is running at ${API_BASE_URL} and that this page is served from http://localhost:5173 (the only origin its CORS policy allows).`)
  }
  let json: unknown = null
  try { json = await res.json() } catch { /* non-JSON body */ }
  if (!res.ok) {
    const detail = detailOf(json) ?? `The server returned an error (HTTP ${res.status}).`
    throw new ApiError(detail, 'http', res.status, hintFor(res.status, detail))
  }
  const r = json as { status?: unknown; filename?: unknown } | null
  if (!r || typeof r.status !== 'string' || typeof r.filename !== 'string') throw new ApiError('The backend returned a response in an unexpected format.', 'format')
  return json as AnalyzeResponse
}

export async function checkHealth(): Promise<boolean> {
  try { return (await fetch(`${API_BASE_URL}/api/health`)).ok } catch { return false }
}
