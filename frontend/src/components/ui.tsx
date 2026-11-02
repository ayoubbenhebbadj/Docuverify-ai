import { ReactNode, ButtonHTMLAttributes } from 'react'
import { Loader2 } from 'lucide-react'
import { useLanguage } from '../state/LanguageContext'

export const Card = ({ children, className = '' }: { children: ReactNode; className?: string }) => (
  <section className={`rounded-xl border border-slate-200 bg-white ${className}`}>{children}</section>
)

const tones = {
  green: 'bg-emerald-50 text-emerald-800 ring-emerald-600/20',
  amber: 'bg-amber-50 text-amber-800 ring-amber-600/30',
  red: 'bg-red-50 text-red-800 ring-red-600/20',
  blue: 'bg-blue-50 text-blue-800 ring-blue-600/20',
  gray: 'bg-slate-100 text-slate-700 ring-slate-500/20',
}

export type Tone = keyof typeof tones

export const Badge = ({ tone = 'gray', children }: { tone?: Tone; children: ReactNode }) => (
  <span
    className={`inline-flex items-center whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ring-inset ${tones[tone]}`}
  >
    {children}
  </span>
)

export function StatusBadge({ status }: { status: string }) {
  const { statusLabel } = useLanguage()

  const toneMap: Record<string, Tone> = {
    passed: 'green',
    complete: 'green',
    detected: 'green',
    needs_review: 'amber',
    needs_ocr: 'amber',
    mismatch: 'red',
    missing: 'red',
  }

  const tone = toneMap[status] ?? 'gray'
  const label = statusLabel(status)

  return <Badge tone={tone}>{label}</Badge>
}

export function Btn({
  variant = 'secondary',
  className = '',
  ...p
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' }) {
  const v =
    variant === 'primary'
      ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-2xs'
      : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50'

  return (
    <button
      {...p}
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${v} ${className}`}
    />
  )
}

export const Spinner = ({ className = 'h-5 w-5' }: { className?: string }) => (
  <Loader2 aria-hidden className={`animate-spin ${className}`} />
)

export const PageHeader = ({
  title,
  text,
  actions,
}: {
  title: string
  text?: string
  actions?: ReactNode
}) => (
  <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
    <div>
      <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
      {text && <p className="mt-1 max-w-2xl text-sm text-slate-600">{text}</p>}
    </div>
    <div className="flex gap-2 print:hidden">{actions}</div>
  </div>
)

/** Renders any backend field value; null/empty shows localized "Not found" rather than the word null. */
export function Value({ v }: { v: unknown }): JSX.Element {
  const { t } = useLanguage()

  if (v === null || v === undefined || v === '' || (Array.isArray(v) && v.length === 0)) {
    return <em className="text-slate-400 font-normal">{t.common.notFound}</em>
  }
  if (Array.isArray(v)) {
    return (
      <ul className="list-disc space-y-0.5 pl-4 text-slate-800">
        {v.map((x, i) => (
          <li key={i}>
            <Value v={x} />
          </li>
        ))}
      </ul>
    )
  }
  if (typeof v === 'boolean') {
    return <>{v ? t.common.yes : t.common.no}</>
  }
  if (typeof v === 'object') {
    return <code className="text-xs font-mono">{JSON.stringify(v)}</code>
  }
  return <>{String(v)}</>
}
