import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { CheckCircle2, AlertTriangle, XCircle, Printer, RotateCcw } from 'lucide-react'
import { useAnalysis } from '../state/AnalysisContext'
import { useLanguage } from '../state/LanguageContext'
import { isOcr, type DocumentResult } from '../types'
import { REQUIRED_DOCS, pageRange, titleCase } from '../constants'
import { Badge, Btn, Card, PageHeader, StatusBadge, Value } from '../components/ui'

const Stat = ({
  label,
  children,
  sub,
}: {
  label: string
  children: React.ReactNode
  sub?: string
}) => (
  <Card className="p-4 shadow-2xs">
    <p className="text-xs font-medium text-slate-500">{label}</p>
    <div className="mt-1 text-2xl font-bold tracking-tight text-slate-900">{children}</div>
    {sub && <p className="mt-0.5 text-xs text-slate-500">{sub}</p>}
  </Card>
)

export default function Results() {
  const { state, reset } = useAnalysis()
  const { t, docLabel } = useLanguage()
  const nav = useNavigate()
  const r = state.result
  const [openKey, setOpenKey] = useState('')
  const [printing, setPrinting] = useState(false)

  useEffect(() => {
    const b = () => setPrinting(true)
    const a = () => setPrinting(false)
    window.addEventListener('beforeprint', b)
    window.addEventListener('afterprint', a)
    return () => {
      window.removeEventListener('beforeprint', b)
      window.removeEventListener('afterprint', a)
    }
  }, [])

  const again = () => {
    reset()
    nav('/analysis')
  }

  if (!r) {
    return (
      <>
        <PageHeader title={t.results.title} />
        <Card className="p-10 text-center">
          <p className="text-base font-bold text-slate-800">{t.results.noResultsTitle}</p>
          <p className="mt-1.5 text-sm text-slate-600">{t.results.noResultsText}</p>
          <Link
            to="/analysis"
            className="mt-4 inline-block font-semibold text-blue-700 underline decoration-blue-300 hover:text-blue-900"
          >
            {t.results.startNewLink} →
          </Link>
        </Card>
      </>
    )
  }

  if (isOcr(r)) {
    return (
      <>
        <PageHeader
          title={r.filename}
          actions={
            <Btn variant="primary" onClick={again}>
              <RotateCcw className="h-4 w-4" />
              <span>{t.results.analyzeAnother}</span>
            </Btn>
          }
        />
        <Card className="p-6">
          <div className="mb-3">
            <StatusBadge status="needs_ocr" />
          </div>
          <p className="font-semibold text-slate-900">{t.results.ocrNeedsTitle(r.page_count)}</p>
          <p className="mt-1.5 text-sm leading-relaxed text-slate-700">
            {t.results.ocrNeedsBody(r.message)}
          </p>
        </Card>
      </>
    )
  }

  const ocr = r.ocr_summary
  const docs = r.documents ?? []
  const missing = r.missing_documents ?? []
  const unclassified = r.unclassified_pages ?? []
  const cv = r.cross_document_validation
  const checks = cv?.checks ?? []
  const sum = cv?.summary
  const review = docs.filter((d) => d.validation?.status !== 'complete')
  const knownOk = r.status === 'passed' || r.status === 'needs_review'
  const shown =
    r.status === 'passed' && (missing.length > 0 || unclassified.length > 0)
      ? 'needs_review'
      : r.status // never show success while documents are missing

  const keyOf = (d: DocumentResult, i: number) => `doc-${i}-${d.document_type}`
  const jump = (k: string) => {
    setOpenKey(k)
    setTimeout(() => {
      document.getElementById(k)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 50)
  }

  const banner =
    shown === 'passed'
      ? (['border-emerald-200 bg-emerald-50 text-emerald-950', CheckCircle2, t.results.bannerPassed] as const)
      : ([
          'border-amber-200 bg-amber-50 text-amber-950',
          AlertTriangle,
          knownOk ? t.results.bannerReview : t.results.bannerUnknown(r.status),
        ] as const)

  const BannerIcon = banner[1]

  const steps = [
    ...(missing.length
      ? [t.results.stepsGeneration.missingDocs(missing.map(docLabel).join(', '))]
      : []),
    ...(unclassified.length
      ? [t.results.stepsGeneration.unclassified(pageRange(unclassified))]
      : []),
    ...review.map((d) =>
      t.results.stepsGeneration.reviewDoc(docLabel(d.document_type), pageRange(d.pages ?? []))
    ),
    ...checks
      .filter((c) => c.status === 'mismatch')
      .map((c) => t.results.stepsGeneration.mismatchCheck(c.check)),
    ...checks
      .filter((c) => c.status === 'needs_review')
      .map((c) => t.results.stepsGeneration.reviewCheck(c.check, c.message)),
  ]

  return (
    <>
      <PageHeader
        title={r.filename}
        text={t.results.subtitle(r.page_count)}
        actions={
          <>
            <Btn onClick={() => window.print()}>
              <Printer className="h-4 w-4" />
              <span>{t.results.printReport}</span>
            </Btn>
            <Btn variant="primary" onClick={again}>
              <RotateCcw className="h-4 w-4" />
              <span>{t.results.analyzeAnother}</span>
            </Btn>
          </>
        }
      />

      {/* Main Status Banner */}
      <div
        role="status"
        className={`mb-5 flex items-start gap-3.5 rounded-xl border p-4 text-sm shadow-xs ${banner[0]}`}
      >
        <BannerIcon className="mt-0.5 h-5 w-5 shrink-0" />
        <div>
          <div className="flex items-center gap-2 font-bold">
            <span>{t.results.overallStatus}:</span>
            <StatusBadge status={shown} />
          </div>
          <p className="mt-1 leading-relaxed">{banner[2]}</p>
        </div>
      </div>

      {/* OCR Notice */}
      {ocr?.ocr_used && (
        <div
          role="note"
          className={`mb-5 rounded-xl border p-4 text-sm shadow-2xs ${
            ocr.review_required
              ? 'border-amber-200 bg-amber-50 text-amber-950'
              : 'border-slate-200 bg-white text-slate-700'
          }`}
        >
          <p className="font-bold">{t.results.ocrUsedHeader}</p>
          <p className="mt-1 leading-relaxed">
            {t.results.ocrPagesInfo(pageRange(ocr.pages_processed), ocr.average_confidence ?? undefined)}{' '}
            {ocr.review_required
              ? t.results.ocrCheckScans(
                  pageRange([...ocr.pages_low_confidence, ...ocr.pages_needing_ocr])
                )
              : t.results.ocrConfidenceGood}
          </p>
          {(ocr.errors?.length ?? 0) > 0 && (
            <p className="mt-1 text-xs text-red-700 font-medium">
              {t.results.ocrProblems}: {ocr.errors!.join('; ')}
            </p>
          )}
        </div>
      )}

      {/* Stats Summary Grid */}
      <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Stat label={t.results.stats.pagesProcessed}>{r.page_count}</Stat>
        <Stat label={t.results.stats.docsDetected}>{r.documents_found}</Stat>
        <Stat
          label={t.results.stats.requiredMissing}
          sub={t.results.stats.ofRequired(REQUIRED_DOCS.length)}
        >
          <span className={missing.length ? 'text-red-700 font-bold' : 'text-emerald-700 font-bold'}>
            {missing.length}
          </span>
        </Stat>
        <Stat
          label={t.results.stats.crossPassed}
          sub={sum ? t.results.stats.ofTotal(sum.total_checks) : undefined}
        >
          {sum?.passed ?? '—'}
        </Stat>
        <Stat label={t.results.stats.mismatchesReview} sub={t.results.stats.crossDoc}>
          <span className={sum?.mismatches ? 'text-red-700 font-bold' : ''}>
            {sum?.mismatches ?? '—'}
          </span>{' '}
          /{' '}
          <span className={sum?.needs_review ? 'text-amber-700 font-bold' : ''}>
            {sum?.needs_review ?? '—'}
          </span>
        </Stat>
      </div>

      {/* Required Documents Checklist */}
      <Card className="mb-6 shadow-2xs">
        <h2 className="border-b border-slate-100 p-4 font-bold text-slate-900">
          {t.results.requiredDocs.title}
        </h2>
        <ul className="divide-y divide-slate-100">
          {REQUIRED_DOCS.map((req) => {
            const hits = docs
              .map((d, i) => ({ d, i }))
              .filter((x) => x.d.document_type === req.id)
            const found = hits.length > 0
            return (
              <li key={req.id} className="flex flex-wrap items-center gap-3 p-3.5 text-sm">
                {found ? (
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" aria-hidden />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600 shrink-0" aria-hidden />
                )}
                <span className="min-w-40 flex-1 font-semibold text-slate-900">
                  {docLabel(req.id)}
                </span>
                <StatusBadge status={found ? 'detected' : 'missing'} />
                <span className="text-xs text-slate-500 font-mono">
                  {found
                    ? `Pages ${hits.map((h) => pageRange(h.d.pages ?? [])).join('; ')}`
                    : t.results.requiredDocs.notFound}
                </span>
                {found && (
                  <button
                    className="text-xs font-semibold text-blue-700 underline hover:text-blue-900 print:hidden"
                    onClick={() => jump(keyOf(hits[0].d, hits[0].i))}
                  >
                    {t.results.requiredDocs.viewFields}
                  </button>
                )}
              </li>
            )
          })}
        </ul>
        {unclassified.length > 0 && (
          <p className="border-t border-slate-100 p-3.5 text-xs font-medium text-amber-800 bg-amber-50/50">
            {t.results.requiredDocs.unidentifiedPages}: {pageRange(unclassified)}
          </p>
        )}
      </Card>

      {/* Extracted Documents Detail */}
      <h2 className="mb-3 text-base font-bold text-slate-900">{t.results.extractedDocs.title}</h2>
      {docs.length === 0 ? (
        <Card className="mb-6 p-4 text-sm text-slate-600">
          {t.results.extractedDocs.empty}
        </Card>
      ) : (
        <div className="mb-6 space-y-2.5">
          {docs.map((d, i) => {
            const k = keyOf(d, i)
            const v = d.validation
            return (
              <details
                key={k}
                id={k}
                open={printing || openKey === k}
                onToggle={(e) => {
                  if (!printing) {
                    setOpenKey(
                      (e.currentTarget as HTMLDetailsElement).open
                        ? k
                        : openKey === k
                        ? ''
                        : openKey
                    )
                  }
                }}
                className="rounded-xl border border-slate-200 bg-white shadow-2xs"
              >
                <summary className="flex cursor-pointer flex-wrap items-center gap-3 p-3.5 text-sm hover:bg-slate-50/50 transition-colors">
                  <span className="min-w-40 flex-1 font-bold text-slate-900">
                    {docLabel(d.document_type)}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">
                    {t.results.extractedDocs.pages} {pageRange(d.pages ?? [])}
                  </span>
                  {d.ocr_used && <Badge tone={d.ocr_review_required ? 'amber' : 'blue'}>OCR</Badge>}
                  {typeof d.confidence === 'number' && (
                    <Badge tone="gray">
                      {t.results.extractedDocs.classifiedWith(d.confidence)}
                    </Badge>
                  )}
                  <StatusBadge status={v?.status ?? 'needs_review'} />
                </summary>

                <div className="space-y-4 border-t border-slate-100 p-4 text-sm">
                  {(v?.missing_fields?.length ?? 0) > 0 && (
                    <div>
                      <p className="font-bold text-red-800">
                        {t.results.extractedDocs.missingFields}
                      </p>
                      <p className="text-xs text-slate-700">{v!.missing_fields.map(titleCase).join(', ')}</p>
                    </div>
                  )}

                  {(v?.invalid_fields?.length ?? 0) > 0 && (
                    <div>
                      <p className="font-bold text-red-800">
                        {t.results.extractedDocs.invalidFields}
                      </p>
                      <ul className="list-disc pl-5 text-xs text-slate-700">
                        {v!.invalid_fields.map((f) => (
                          <li key={f.field}>
                            <b>{titleCase(f.field)}</b>: {f.reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {(v?.unsupported_evidence?.length ?? 0) > 0 && (
                    <div>
                      <p className="font-bold text-amber-800">
                        {t.results.extractedDocs.unsupportedEvidence}
                      </p>
                      <p className="text-xs text-slate-700">{v!.unsupported_evidence.map(titleCase).join(', ')}</p>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {t.results.extractedDocs.unsupportedNote}
                      </p>
                    </div>
                  )}

                  {(v?.warnings?.length ?? 0) > 0 && (
                    <div>
                      <p className="font-bold text-amber-800">
                        {t.results.extractedDocs.warnings}
                      </p>
                      <ul className="list-disc pl-5 text-xs text-slate-700">
                        {v!.warnings.map((w) => (
                          <li key={w}>{w}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <dl className="grid gap-x-6 gap-y-2.5 sm:grid-cols-2 pt-2 border-t border-slate-100">
                    {Object.entries(d.fields ?? {}).map(([f, val]) => (
                      <div key={f} className="border-b border-slate-50 pb-2">
                        <dt className="text-xs font-medium text-slate-500">{titleCase(f)}</dt>
                        <dd className="break-words text-sm font-semibold text-slate-900">
                          <Value v={val} />
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              </details>
            )
          })}
        </div>
      )}

      {/* Cross-Document Validation Table */}
      <Card className="mb-6 shadow-2xs">
        <h2 className="border-b border-slate-100 p-4 font-bold text-slate-900">
          {t.results.crossDoc.title}
        </h2>
        {checks.length === 0 ? (
          <p className="p-4 text-sm text-slate-600">{t.results.crossDoc.empty}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-600 uppercase">
                <tr>
                  <th className="px-4 py-3">{t.results.crossDoc.colCheck}</th>
                  <th className="px-4 py-3">{t.results.crossDoc.colStatus}</th>
                  <th className="px-4 py-3">{t.results.crossDoc.colValues}</th>
                  <th className="px-4 py-3">{t.results.crossDoc.colMessage}</th>
                </tr>
              </thead>
              <tbody>
                {checks.map((c, i) => (
                  <tr
                    key={`${c.check}-${i}`}
                    className={`border-t border-slate-100 align-top ${
                      c.status === 'mismatch' ? 'bg-red-50/50' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-semibold text-slate-900">{c.check}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="px-4 py-3">
                      {Object.keys(c.values ?? {}).length === 0 ? (
                        <em className="text-slate-400">{t.results.crossDoc.none}</em>
                      ) : (
                        <dl className="space-y-1">
                          {Object.entries(c.values).map(([k, val]) => (
                            <div key={k}>
                              <dt className="text-[11px] font-medium text-slate-500">{docLabel(k)}</dt>
                              <dd className="text-xs font-semibold text-slate-900">
                                <Value v={val} />
                              </dd>
                            </div>
                          ))}
                        </dl>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs leading-relaxed text-slate-700">{c.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Package Summary Report */}
      <Card className="p-5 shadow-2xs">
        <h2 className="mb-4 text-base font-bold text-slate-900">{t.results.report.title}</h2>
        <div className="space-y-2.5 text-sm text-slate-800">
          <p className="flex items-center gap-2">
            <b>{t.results.report.overall}</b>
            <StatusBadge status={shown} />
          </p>
          <p>
            <b>{t.results.report.missing}</b>{' '}
            {missing.length ? missing.map(docLabel).join(', ') : t.results.report.none}
          </p>
          <p>
            <b>{t.results.report.requiringReview}</b>{' '}
            {review.length
              ? review.map((d) => docLabel(d.document_type)).join(', ')
              : t.results.report.none}
          </p>
          <p>
            <b>{t.results.report.mismatches}</b>{' '}
            {checks.filter((c) => c.status === 'mismatch').map((c) => c.check).join(', ') ||
              t.results.report.none}
          </p>
          <div className="pt-1">
            <b>{t.results.report.nextSteps}</b>
            {steps.length ? (
              <ul className="mt-1.5 list-disc pl-5 space-y-1 text-xs text-slate-700">
                {steps.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-600 mt-0.5">{t.results.report.noAction}</p>
            )}
          </div>
          <p className="border-t border-slate-100 pt-3 text-[11px] text-slate-400 leading-relaxed">
            {t.results.report.legalDisclaimer}
          </p>
        </div>
      </Card>
    </>
  )
}
