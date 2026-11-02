import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FilePlus2, CheckCircle2, XCircle } from 'lucide-react'
import { checkHealth, API_BASE_URL } from '../services/api'
import { useAnalysis } from '../state/AnalysisContext'
import { useLanguage } from '../state/LanguageContext'
import { isOcr } from '../types'
import { Card, PageHeader, Spinner, StatusBadge } from '../components/ui'

export default function Overview() {
  const [up, setUp] = useState<boolean | null>(null)
  const { state } = useAnalysis()
  const { t } = useLanguage()
  const r = state.result

  useEffect(() => {
    checkHealth().then(setUp)
  }, [])

  return (
    <>
      <PageHeader
        title={t.overview.title}
        text={t.overview.subtitle}
        actions={
          <Link
            to="/analysis"
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition-colors"
          >
            <FilePlus2 className="h-4 w-4" />
            <span>{t.overview.newAnalysisBtn}</span>
          </Link>
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        {/* Left Column: What happens to your PDF */}
        <Card className="p-5 lg:col-span-2">
          <h2 className="mb-4 text-base font-bold text-slate-900">{t.overview.processHeader}</h2>
          <ol className="space-y-3 text-sm text-slate-700">
            {t.overview.steps.map((s, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                  {i + 1}
                </span>
                <span className="leading-relaxed">{s}</span>
              </li>
            ))}
          </ol>
          <p className="mt-5 rounded-lg border border-slate-200 bg-slate-50 p-3.5 text-xs leading-relaxed text-slate-700">
            {t.overview.needsReviewNote}
          </p>
        </Card>

        {/* Right Column: Connection and Latest Status */}
        <div className="space-y-4">
          <Card className="p-4">
            <h2 className="mb-2.5 text-sm font-bold text-slate-900">{t.overview.backendConnection}</h2>
            {up === null ? (
              <p className="flex items-center gap-2 text-xs text-slate-600">
                <Spinner className="h-3.5 w-3.5 text-blue-600" />
                <span>{t.overview.checking}</span>
              </p>
            ) : up ? (
              <p className="flex items-center gap-2 text-xs font-medium text-emerald-800">
                <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                <span>
                  {t.overview.connectedTo} <code className="font-mono text-[11px]">{API_BASE_URL}</code>
                </span>
              </p>
            ) : (
              <p role="alert" className="flex items-start gap-2 text-xs text-red-800">
                <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
                <span>
                  {t.overview.cannotReach} {API_BASE_URL}. Start the backend, then reload this page.
                </span>
              </p>
            )}
          </Card>

          <Card className="p-4">
            <h2 className="mb-2.5 text-sm font-bold text-slate-900">{t.overview.latestAnalysis}</h2>
            {!r ? (
              <p className="text-xs text-slate-500">{t.overview.noAnalysisYet}</p>
            ) : (
              <div className="space-y-2.5 text-xs">
                <p className="break-all font-semibold text-slate-900">{r.filename}</p>
                <div>
                  <StatusBadge status={r.status} />
                </div>
                {!isOcr(r) && (
                  <p className="text-slate-600">
                    {t.overview.docsSummary(r.documents_found, r.missing_documents?.length ?? 0)}
                  </p>
                )}
                <Link
                  className="inline-block font-semibold text-blue-700 underline decoration-blue-300 hover:text-blue-900"
                  to="/results"
                >
                  {t.overview.openResults} →
                </Link>
              </div>
            )}
          </Card>
        </div>
      </div>
    </>
  )
}
