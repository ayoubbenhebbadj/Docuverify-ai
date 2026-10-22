/**
 * Typed API layer. Today every method resolves from in-memory mock data.
 * To connect FastAPI: set VITE_API_URL and replace each body with `http<T>(path, init)`.
 * The frontend never talks to an LLM provider or holds API keys; the backend does.
 */
import type { Dashboard, DocumentRecord, ExtractedField, Operation, Rule } from '../types'
import { documents, operations, fieldsFor, fieldStore, rules } from './mock'

export const API_URL: string = import.meta.env.VITE_API_URL ?? ''
export async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_URL}${path}`, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!r.ok) throw new Error(`API ${r.status}: ${await r.text()}`)
  return r.json() as Promise<T>
}
const wait = <T,>(v: T, ms = 400): Promise<T> => new Promise(res => setTimeout(() => res(structuredClone(v)), ms))
const fail = (m: string) => new Promise<never>((_, rej) => setTimeout(() => rej(new Error(m)), 300))

export const api = {
  getDashboard(): Promise<Dashboard> {
    const c = (s: string) => documents.filter(d => d.status === s).length
    const trend = [['Sep 7', 14, 3], ['Sep 14', 21, 5], ['Sep 21', 18, 6], ['Sep 28', 26, 4], ['Oct 5', 31, 7], ['Oct 12', 29, 5]]
    return wait({
      kpis: { total: documents.length, review: c('review'), incomplete: c('incomplete'), verified: c('verified') },
      trend: trend.map(([w, p, f]) => ({ week: w as string, processed: p as number, flagged: f as number })),
      status: [{ name: 'Verified', value: c('verified'), color: '#16a34a' }, { name: 'Needs review', value: c('review'), color: '#d97706' }, { name: 'Incomplete', value: c('incomplete'), color: '#dc2626' }, { name: 'Not processed', value: c('pending'), color: '#94a3b8' }],
      issues: [{ issue: 'Missing customs no.', count: 14 }, { issue: 'Currency mismatch', count: 11 }, { issue: 'Invalid invoice date', count: 9 }, { issue: 'Weight inconsistency', count: 7 }, { issue: 'Origin not stated', count: 5 }],
      activity: [{ id: 'a1', text: 'Customs Declaration for IMP-2026-0149 flagged: invoice date invalid', time: '12 min ago' }, { id: 'a2', text: 'Y. Benali resolved 2 issues on D-1006', time: '1 h ago' }, { id: 'a3', text: 'Rule "Currency" updated for Commercial Invoice', time: 'Yesterday' }, { id: 'a4', text: 'EXP-2026-0163 reached 100% completeness', time: 'Yesterday' }]
    })
  },
  listDocuments: () => wait(documents),
  getDocument: (id: string) => { const d = documents.find(x => x.id === id); return d ? wait(d) : fail('Document not found') },
  async uploadDocument(file: File): Promise<DocumentRecord> {
    const d: DocumentRecord = { id: `D-${1001 + documents.length}`, name: file.name, type: 'Commercial Invoice', uploaded: new Date().toISOString().slice(0, 10), status: 'pending', pages: 1 }
    documents.unshift(d); return wait(d, 700) // 'pending' = received, NOT analysed. No AI runs in mock mode.
  },
  getFields: (id: string) => { const d = documents.find(x => x.id === id); return d ? wait(fieldsFor(d)) : fail('Document not found') },
  saveFields(id: string, f: ExtractedField[]) {
    fieldStore[id] = f; const d = documents.find(x => x.id === id)
    if (d && d.status !== 'pending') d.status = f.every(x => x.state === 'valid' || x.resolved) ? 'verified' : f.some(x => x.state === 'missing' && !x.resolved) ? 'incomplete' : 'review'
    return wait(f, 500)
  },
  listOperations: () => wait(operations),
  createOperation(o: Omit<Operation, 'id' | 'requiredTypes' | 'eta'>) {
    const n: Operation = { ...o, id: `OP-${operations.length + 1}`, eta: new Date(Date.now() + 14 * 864e5).toISOString().slice(0, 10), requiredTypes: ['Commercial Invoice', 'Packing List', 'Bill of Lading', 'Customs Declaration'] }
    operations.unshift(n); return wait(n)
  },
  attachDocument(docId: string, opId: string) { const d = documents.find(x => x.id === docId); if (d) d.operationId = opId; return wait(true, 250) },
  listRules: () => wait(rules),
  saveRule(r: Omit<Rule, 'id'> & { id?: string }) {
    const i = rules.findIndex(x => x.id === r.id)
    if (i >= 0) rules[i] = { ...rules[i], ...r } as Rule; else rules.push({ ...r, id: `R${rules.length + 1}` } as Rule)
    return wait(true, 300)
  },
  deleteRule(id: string) { const i = rules.findIndex(x => x.id === id); if (i >= 0) rules.splice(i, 1); return wait(true, 250) }
}
