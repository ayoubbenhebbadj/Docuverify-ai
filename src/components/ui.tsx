import { ReactNode, ButtonHTMLAttributes, useEffect } from 'react'
import { Loader2, Inbox, AlertTriangle, X } from 'lucide-react'
import type { AsyncState } from '../hooks'

export const Card = ({ children, className = '' }: { children: ReactNode; className?: string }) =>
  <section className={`rounded-lg border border-slate-200 bg-white ${className}`}>{children}</section>
const tones = { green: 'bg-green-50 text-green-700 ring-green-600/20', amber: 'bg-amber-50 text-amber-700 ring-amber-600/20', red: 'bg-red-50 text-red-700 ring-red-600/20', blue: 'bg-blue-50 text-blue-700 ring-blue-600/20', gray: 'bg-slate-100 text-slate-600 ring-slate-500/20' }
export type Tone = keyof typeof tones
export const Badge = ({ tone = 'gray', children }: { tone?: Tone; children: ReactNode }) =>
  <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}>{children}</span>
export const statusTone = { verified: 'green', review: 'amber', incomplete: 'red', pending: 'gray', valid: 'green', uncertain: 'amber', invalid: 'red', missing: 'red' } as const
export const statusLabel = { verified: 'Verified', review: 'Needs review', incomplete: 'Incomplete', pending: 'Not processed', valid: 'Valid', uncertain: 'Uncertain', invalid: 'Invalid', missing: 'Missing' } as const

export function Btn({ variant = 'secondary', className = '', ...p }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' | 'ghost' }) {
  const v = { primary: 'bg-blue-600 text-white hover:bg-blue-700', secondary: 'border border-slate-300 bg-white hover:bg-slate-50', danger: 'border border-red-200 text-red-700 hover:bg-red-50', ghost: 'hover:bg-slate-100' }[variant]
  return <button {...p} className={`inline-flex items-center justify-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${v} ${className}`} />
}
export const inputCls = 'w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:border-blue-600'
export const Spinner = ({ label = 'Loading…' }: { label?: string }) =>
  <div role="status" className="flex items-center justify-center gap-2 p-10 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" />{label}</div>
export const Empty = ({ title, text, action }: { title: string; text?: string; action?: ReactNode }) =>
  <div className="flex flex-col items-center gap-2 p-10 text-center"><Inbox className="h-8 w-8 text-slate-300" /><p className="font-medium">{title}</p>{text && <p className="max-w-sm text-sm text-slate-500">{text}</p>}{action}</div>
export const ErrorBox = ({ msg, retry }: { msg: string; retry?: () => void }) =>
  <div role="alert" className="m-4 flex items-center gap-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800"><AlertTriangle className="h-4 w-4 shrink-0" /><span className="flex-1">{msg}</span>{retry && <Btn onClick={retry}>Try again</Btn>}</div>
export function Load<T>({ s, children }: { s: AsyncState<T>; children: (d: T) => ReactNode }) {
  if (s.loading && !s.data) return <Spinner />
  if (s.error) return <ErrorBox msg={s.error} retry={s.reload} />
  return s.data !== undefined ? <>{children(s.data)}</> : null
}
export const PageHeader = ({ title, text, actions }: { title: string; text?: string; actions?: ReactNode }) =>
  <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><h1 className="text-xl font-semibold">{title}</h1>{text && <p className="mt-1 max-w-2xl text-sm text-slate-500">{text}</p>}</div><div className="flex gap-2">{actions}</div></div>
export function Modal({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: ReactNode }) {
  useEffect(() => { if (!open) return; const h = (e: KeyboardEvent) => e.key === 'Escape' && onClose(); window.addEventListener('keydown', h); return () => window.removeEventListener('keydown', h) }, [open, onClose])
  if (!open) return null
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" onMouseDown={onClose}>
    <div role="dialog" aria-modal="true" aria-label={title} onMouseDown={e => e.stopPropagation()} className="w-full max-w-md rounded-lg bg-white p-5">
      <div className="mb-4 flex items-center justify-between"><h2 className="font-semibold">{title}</h2><button aria-label="Close" onClick={onClose} className="rounded p-1 hover:bg-slate-100"><X className="h-4 w-4" /></button></div>{children}</div></div>
}
export const Label = ({ text, error, children }: { text: string; error?: string; children: ReactNode }) =>
  <label className="block text-sm"><span className="mb-1 block font-medium">{text}</span>{children}{error && <span className="mt-1 block text-xs text-red-600">{error}</span>}</label>
export const Progress = ({ value }: { value: number }) =>
  <div className="h-1.5 w-full rounded bg-slate-100" role="progressbar" aria-valuenow={value}><div className={`h-full rounded ${value === 100 ? 'bg-green-600' : value >= 50 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${value}%` }} /></div>
