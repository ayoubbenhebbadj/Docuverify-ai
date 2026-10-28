import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { CheckCircle2, AlertTriangle, XCircle, Printer, RotateCcw } from 'lucide-react'
import { useAnalysis } from '../state/AnalysisContext'
import { isOcr, type DocumentResult } from '../types'
import { REQUIRED_DOCS, docLabel, pageRange, titleCase } from '../constants'
import { Badge, Btn, Card, PageHeader, StatusBadge, Value } from '../components/ui'

const Stat = ({ label, children, sub }: { label: string; children: React.ReactNode; sub?: string }) => <Card className="p-4"><p className="text-sm text-slate-600">{label}</p><div className="mt-1 text-2xl font-semibold">{children}</div>{sub && <p className="text-xs text-slate-600">{sub}</p>}</Card>

export default function Results() {
  const { state, reset } = useAnalysis(); const nav = useNavigate(); const r = state.result
  const [openKey, setOpenKey] = useState(''); const [printing, setPrinting] = useState(false)
  useEffect(() => { const b = () => setPrinting(true), a = () => setPrinting(false); window.addEventListener('beforeprint', b); window.addEventListener('afterprint', a); return () => { window.removeEventListener('beforeprint', b); window.removeEventListener('afterprint', a) } }, [])
  const again = () => { reset(); nav('/analysis') }

  if (!r) return <><PageHeader title="Analysis results" /><Card className="p-8 text-center"><p className="font-medium">No results yet</p><p className="mt-1 text-sm text-slate-600">Upload a merged shipment PDF to see its report here.</p><Link to="/analysis" className="mt-3 inline-block text-blue-700 underline">Start a new analysis</Link></Card></>
  if (isOcr(r)) return <><PageHeader title={r.filename} actions={<Btn variant="primary" onClick={again}><RotateCcw className="h-4 w-4" />Analyze another PDF</Btn>} />
    <Card className="p-5"><StatusBadge status="needs_ocr" /><p className="mt-3 font-medium">No selectable text was found in this PDF ({r.page_count} page{r.page_count === 1 ? '' : 's'}).</p><p className="mt-1 text-sm text-slate-700">{r.message} No documents were classified or checked. Try a clearer or higher-resolution scan, or ask the exporter for a text-based PDF.</p></Card></>

  const ocr = r.ocr_summary
  const docs = r.documents ?? [], missing = r.missing_documents ?? [], unclassified = r.unclassified_pages ?? []
  const cv = r.cross_document_validation, checks = cv?.checks ?? [], sum = cv?.summary
  const review = docs.filter(d => d.validation?.status !== 'complete')
  const knownOk = r.status === 'passed' || r.status === 'needs_review'
  const shown = r.status === 'passed' && (missing.length > 0 || unclassified.length > 0) ? 'needs_review' : r.status // never show success while documents are missing
  const keyOf = (d: DocumentResult, i: number) => `doc-${i}-${d.document_type}`
  const jump = (k: string) => { setOpenKey(k); setTimeout(() => document.getElementById(k)?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50) }
  const banner = shown === 'passed' ? ['border-green-200 bg-green-50 text-green-900', CheckCircle2, 'All eight documents were found and no issues were reported.'] as const
    : ['border-amber-200 bg-amber-50 text-amber-900', AlertTriangle, knownOk ? 'This package needs review. That means a person should look at the items below. It does not mean fraud has been found.' : `The backend reported an unrecognized status (“${r.status}”). Treat this package as needing review.`] as const
  const Banner = banner[1]
  const steps = [
    ...(missing.length ? [`Request the missing documents from the exporter: ${missing.map(docLabel).join(', ')}.`] : []),
    ...(unclassified.length ? [`Check pages ${pageRange(unclassified)}: the system could not identify them.`] : []),
    ...review.map(d => `Check the flagged fields in the ${docLabel(d.document_type).toLowerCase()} (pages ${pageRange(d.pages ?? [])}).`),
    ...checks.filter(c => c.status === 'mismatch').map(c => `Resolve the “${c.check}” mismatch between documents.`),
    ...checks.filter(c => c.status === 'needs_review').map(c => `Review “${c.check}”: ${c.message}`)]

  return <>
    <PageHeader title={r.filename} text={`${r.page_count} pages analyzed`} actions={<><Btn onClick={() => window.print()}><Printer className="h-4 w-4" />Print report</Btn><Btn variant="primary" onClick={again}><RotateCcw className="h-4 w-4" />Analyze another PDF</Btn></>} />
    <div role="status" className={`mb-4 flex items-start gap-3 rounded-lg border p-4 text-sm ${banner[0]}`}><Banner className="mt-0.5 h-5 w-5 shrink-0" /><div><p className="font-semibold">Overall status: <StatusBadge status={shown} /></p><p className="mt-1">{banner[2]}</p></div></div>

    {ocr?.ocr_used && <div role="note" className={`mb-4 rounded-lg border p-4 text-sm ${ocr.review_required ? 'border-amber-200 bg-amber-50 text-amber-900' : 'border-slate-200 bg-white text-slate-700'}`}><p className="font-semibold">Scanned pages were read with OCR</p>
      <p className="mt-1">Pages {pageRange(ocr.pages_processed)}{typeof ocr.average_confidence === 'number' ? ` · average confidence ${Math.round(ocr.average_confidence)}%` : ''}. {ocr.review_required ? `Check these against the original scan: ${pageRange([...ocr.pages_low_confidence, ...ocr.pages_needing_ocr])}.` : 'OCR confidence was good on every page.'}</p>
      {(ocr.errors?.length ?? 0) > 0 && <p className="mt-1">OCR problems: {ocr.errors!.join('; ')}</p>}</div>}

    <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
      <Stat label="Pages processed">{r.page_count}</Stat><Stat label="Documents detected">{r.documents_found}</Stat>
      <Stat label="Required missing" sub={`of ${REQUIRED_DOCS.length} required`}><span className={missing.length ? 'text-red-700' : 'text-green-700'}>{missing.length}</span></Stat>
      <Stat label="Cross-checks passed" sub={sum ? `of ${sum.total_checks}` : undefined}>{sum?.passed ?? '—'}</Stat>
      <Stat label="Mismatches / review" sub="cross-document"><span className={sum?.mismatches ? 'text-red-700' : ''}>{sum?.mismatches ?? '—'}</span> / <span className={sum?.needs_review ? 'text-amber-700' : ''}>{sum?.needs_review ?? '—'}</span></Stat></div>

    <Card className="mb-6"><h2 className="border-b border-slate-100 p-4 font-semibold">Required documents</h2><ul className="divide-y divide-slate-100">{REQUIRED_DOCS.map(req => {
      const hits = docs.map((d, i) => ({ d, i })).filter(x => x.d.document_type === req.id), found = hits.length > 0
      return <li key={req.id} className="flex flex-wrap items-center gap-3 p-3 text-sm">{found ? <CheckCircle2 className="h-5 w-5 text-green-600" aria-hidden /> : <XCircle className="h-5 w-5 text-red-600" aria-hidden />}
        <span className="min-w-40 flex-1 font-medium">{req.label}</span><StatusBadge status={found ? 'detected' : 'missing'} />
        <span className="text-slate-600">{found ? `Pages ${hits.map(h => pageRange(h.d.pages ?? [])).join('; ')}` : 'Not found in this PDF'}</span>
        {found && <button className="text-blue-700 underline print:hidden" onClick={() => jump(keyOf(hits[0].d, hits[0].i))}>View fields</button>}</li> })}</ul>
      {unclassified.length > 0 && <p className="border-t border-slate-100 p-3 text-sm text-amber-800">Unidentified pages: {pageRange(unclassified)}</p>}</Card>

    <h2 className="mb-2 font-semibold">Extracted documents</h2>
    {docs.length === 0 ? <Card className="mb-6 p-4 text-sm text-slate-600">No documents were detected.</Card> : <div className="mb-6 space-y-2">{docs.map((d, i) => { const k = keyOf(d, i), v = d.validation
      return <details key={k} id={k} open={printing || openKey === k} onToggle={e => { if (!printing) setOpenKey((e.currentTarget as HTMLDetailsElement).open ? k : openKey === k ? '' : openKey) }} className="rounded-lg border border-slate-200 bg-white">
        <summary className="flex cursor-pointer flex-wrap items-center gap-3 p-3 text-sm"><span className="min-w-40 flex-1 font-medium">{docLabel(d.document_type)}</span><span className="text-slate-600">Pages {pageRange(d.pages ?? [])}</span>
          {d.ocr_used && <Badge tone={d.ocr_review_required ? 'amber' : 'blue'}>OCR</Badge>}{typeof d.confidence === 'number' && <Badge tone="gray">Classified with {Math.round(d.confidence * 100)}% confidence</Badge>}<StatusBadge status={v?.status ?? 'needs_review'} /></summary>
        <div className="space-y-4 border-t border-slate-100 p-4 text-sm">
          {(v?.missing_fields?.length ?? 0) > 0 && <div><p className="font-medium text-red-800">Missing required fields</p><p>{v.missing_fields.map(titleCase).join(', ')}</p></div>}
          {(v?.invalid_fields?.length ?? 0) > 0 && <div><p className="font-medium text-red-800">Invalid fields</p><ul className="list-disc pl-5">{v.invalid_fields.map(f => <li key={f.field}><b>{titleCase(f.field)}</b>: {f.reason}</li>)}</ul></div>}
          {(v?.unsupported_evidence?.length ?? 0) > 0 && <div><p className="font-medium text-amber-800">Unsupported evidence</p><p>{v.unsupported_evidence.map(titleCase).join(', ')}</p><p className="text-slate-600">The AI’s quoted proof for these values was not found in the PDF text. This is a flag to check them, not proof they are wrong.</p></div>}
          {(v?.warnings?.length ?? 0) > 0 && <div><p className="font-medium text-amber-800">Warnings</p><ul className="list-disc pl-5">{v.warnings.map(w => <li key={w}>{w}</li>)}</ul></div>}
          <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">{Object.entries(d.fields ?? {}).map(([f, val]) => <div key={f} className="border-b border-slate-100 pb-2"><dt className="text-xs text-slate-600">{titleCase(f)}</dt><dd className="break-words font-medium"><Value v={val} /></dd></div>)}</dl></div></details> })}</div>}

    <Card className="mb-6"><h2 className="border-b border-slate-100 p-4 font-semibold">Cross-document validation</h2>
      {checks.length === 0 ? <p className="p-4 text-sm text-slate-600">The backend returned no cross-document checks.</p> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-600"><tr><th className="px-4 py-2 font-medium">Check</th><th className="px-4 py-2 font-medium">Status</th><th className="px-4 py-2 font-medium">Values compared</th><th className="px-4 py-2 font-medium">Message</th></tr></thead>
        <tbody>{checks.map((c, i) => <tr key={`${c.check}-${i}`} className={`border-t border-slate-100 align-top ${c.status === 'mismatch' ? 'bg-red-50/50' : ''}`}><td className="px-4 py-3 font-medium">{c.check}</td><td className="px-4 py-3"><StatusBadge status={c.status} /></td>
          <td className="px-4 py-3">{Object.keys(c.values ?? {}).length === 0 ? <em className="text-slate-500">None</em> : <dl className="space-y-1">{Object.entries(c.values).map(([k, val]) => <div key={k}><dt className="text-xs text-slate-600">{docLabel(k)}</dt><dd><Value v={val} /></dd></div>)}</dl>}</td><td className="px-4 py-3">{c.message}</td></tr>)}</tbody></table></div>}</Card>

    <Card className="p-4"><h2 className="mb-3 font-semibold">Package report</h2><div className="space-y-2 text-sm">
      <p><b>Overall status:</b> <StatusBadge status={shown} /></p><p><b>Missing documents:</b> {missing.length ? missing.map(docLabel).join(', ') : 'None'}</p>
      <p><b>Documents requiring review:</b> {review.length ? review.map(d => docLabel(d.document_type)).join(', ') : 'None'}</p>
      <p><b>Cross-document mismatches:</b> {checks.filter(c => c.status === 'mismatch').map(c => c.check).join(', ') || 'None'}</p>
      <div><b>Recommended next steps</b>{steps.length ? <ul className="mt-1 list-disc pl-5">{steps.map((s, i) => <li key={i}>{s}</li>)}</ul> : <p>No action needed based on the returned data.</p>}</div>
      <p className="border-t border-slate-100 pt-3 text-xs text-slate-600">This report is generated by an automated system for internal review. It is not digitally signed, legally certified, or proof that the documents are authentic.</p></div></Card></>
}
