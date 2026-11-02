import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FilePlus2, CheckCircle2, XCircle } from 'lucide-react'
import { checkHealth, API_BASE_URL } from '../services/api'
import { useAnalysis } from '../state/AnalysisContext'
import { isOcr } from '../types'
import { Card, PageHeader, Spinner, StatusBadge } from '../components/ui'

const steps = ['Extracts the text of every PDF page', 'Classifies each page by document type', 'Groups pages that belong to the same document', 'Extracts structured fields from each document', 'Checks required fields and whether quoted evidence appears in the source text', 'Cross-checks values between documents', 'Reports missing documents, unsupported evidence, warnings and mismatches']
export default function Overview() {
  const [up, setUp] = useState<boolean | null>(null); const { state } = useAnalysis(); const r = state.result
  useEffect(() => { checkHealth().then(setUp) }, [])
  return <>
    <PageHeader title="Shipment document verification" text="Merge the exporter's documents into one PDF, upload it, and review what the system found, what is missing, and what does not match." actions={<Link to="/analysis" className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"><FilePlus2 className="h-4 w-4" />New analysis</Link>} />
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="p-4 lg:col-span-2"><h2 className="mb-3 font-semibold">What happens to your PDF</h2><ol className="space-y-2 text-sm text-slate-700">{steps.map((s, i) => <li key={s} className="flex gap-3"><span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-medium">{i + 1}</span>{s}</li>)}</ol>
        <p className="mt-4 rounded-md bg-slate-50 p-3 text-sm text-slate-700">“Needs review” means the package needs a person’s attention. It does not mean fraud has been found.</p></Card>
      <div className="space-y-4">
        <Card className="p-4"><h2 className="mb-2 font-semibold">Backend connection</h2>
          {up === null ? <p className="flex items-center gap-2 text-sm text-slate-600"><Spinner className="h-4 w-4" />Checking…</p> : up ? <p className="flex items-center gap-2 text-sm text-green-800"><CheckCircle2 className="h-4 w-4" />Connected to {API_BASE_URL}</p> : <p role="alert" className="flex items-start gap-2 text-sm text-red-800"><XCircle className="mt-0.5 h-4 w-4 shrink-0" />Cannot reach {API_BASE_URL}. Start the backend, then reload this page.</p>}</Card>
        <Card className="p-4"><h2 className="mb-2 font-semibold">Latest analysis</h2>
          {!r ? <p className="text-sm text-slate-600">No analysis yet in this session.</p> : <div className="space-y-2 text-sm"><p className="break-all font-medium">{r.filename}</p><StatusBadge status={r.status} />{!isOcr(r) && <p className="text-slate-600">{r.documents_found} documents found, {r.missing_documents?.length ?? 0} missing.</p>}<Link className="block text-blue-700 underline" to="/results">Open results</Link></div>}</Card>
      </div></div></>
}
