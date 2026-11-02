import { ReactNode, ButtonHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'
import { titleCase } from '../constants'

export const Card = ({ children, className = '' }: { children: ReactNode; className?: string }) => <section className={`rounded-lg border border-slate-200 bg-white ${className}`}>{children}</section>
const tones = { green: 'bg-green-50 text-green-800 ring-green-600/20', amber: 'bg-amber-50 text-amber-800 ring-amber-600/30', red: 'bg-red-50 text-red-800 ring-red-600/20', blue: 'bg-blue-50 text-blue-800 ring-blue-600/20', gray: 'bg-slate-100 text-slate-700 ring-slate-500/20' }
export type Tone = keyof typeof tones
export const Badge = ({ tone = 'gray', children }: { tone?: Tone; children: ReactNode }) => <span className={`inline-flex items-center whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}>{children}</span>
export function StatusBadge({ status }: { status: string }) {
  const m: Record<string, [Tone, string]> = { passed: ['green', 'Passed'], complete: ['green', 'Complete'], needs_review: ['amber', 'Needs review'], mismatch: ['red', 'Mismatch'], needs_ocr: ['amber', 'Needs OCR'], missing: ['red', 'Missing'], detected: ['green', 'Detected'] }
  const [t, l] = m[status] ?? ['gray', titleCase(status)]
  return <Badge tone={t}>{l}</Badge>
}
export function Btn({ variant = 'secondary', className = '', ...p }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' }) {
  const v = variant === 'primary' ? 'bg-blue-600 text-white hover:bg-blue-700' : 'border border-slate-300 bg-white hover:bg-slate-50'
  return <button {...p} className={`inline-flex items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${v} ${className}`} />
}
export const Spinner = ({ className = 'h-5 w-5' }: { className?: string }) => <Loader2 aria-hidden className={`animate-spin ${className}`} />
export const PageHeader = ({ title, text, actions }: { title: string; text?: string; actions?: ReactNode }) =>
  <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><h1 className="text-xl font-semibold">{title}</h1>{text && <p className="mt-1 max-w-2xl text-sm text-slate-600">{text}</p>}</div><div className="flex gap-2 print:hidden">{actions}</div></div>
/** Renders any backend field value; null/empty shows "Not found" rather than the word null. */
export function Value({ v }: { v: unknown }): JSX.Element {
  if (v === null || v === undefined || v === '' || (Array.isArray(v) && v.length === 0)) return <em className="text-slate-500">Not found</em>
  if (Array.isArray(v)) return <ul className="list-disc space-y-0.5 pl-4">{v.map((x, i) => <li key={i}><Value v={x} /></li>)}</ul>
  if (typeof v === 'boolean') return <>{v ? 'Yes' : 'No'}</>
  if (typeof v === 'object') return <code className="text-xs">{JSON.stringify(v)}</code>
  return <>{String(v)}</>
}
