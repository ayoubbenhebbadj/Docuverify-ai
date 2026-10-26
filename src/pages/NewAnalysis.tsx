import { useRef, useState, DragEvent, KeyboardEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, FileText, X, AlertTriangle, RefreshCw } from 'lucide-react'
import { useAnalysis } from '../state/AnalysisContext'
import { MAX_BYTES, fmtSize } from '../constants'
import { Btn, Card, PageHeader, Spinner } from '../components/ui'

function validate(f: File): string {
  if (!f.name.toLowerCase().endsWith('.pdf')) return 'This is not a PDF. Choose a file ending in .pdf.'
  if (f.size === 0) return 'This file is empty.'
  if (f.size > MAX_BYTES) return `This file is ${fmtSize(f.size)}. The upload limit is 10 MB.`
  return ''
}
export default function NewAnalysis() {
  const { state, setFile, run } = useAnalysis(); const nav = useNavigate(); const pick = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false); const [localErr, setLocalErr] = useState('')
  const running = state.phase === 'running'; const file = state.file
  const choose = (f?: File) => { if (!f || running) return; const e = validate(f); setLocalErr(e); if (!e) setFile(f) }
  const open = () => !running && pick.current?.click()
  const onKey = (e: KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open() } }
  const onDrop = (e: DragEvent) => { e.preventDefault(); setDrag(false); choose(e.dataTransfer.files[0]) }
  const analyze = async () => { if (file && (await run(file))) nav('/results') }
  return <>
    <PageHeader title="New analysis" text="Upload one PDF that contains all of the shipment's documents." />
    <Card className="p-5">
      <p className="mb-4 rounded-md bg-blue-50 p-3 text-sm text-blue-900">Merge the exporter’s documents into a single PDF before uploading. The PDF needs selectable text (scanned images are reported as needing OCR). Maximum size 10 MB.</p>
      <div role="button" tabIndex={0} aria-disabled={running} aria-label="Choose a PDF file, or drag one here" onClick={open} onKeyDown={onKey} onDragOver={e => { e.preventDefault(); if (!running) setDrag(true) }} onDragLeave={() => setDrag(false)} onDrop={onDrop}
        className={`flex cursor-pointer flex-col items-center gap-2 rounded-lg border-2 border-dashed p-8 text-center ${drag ? 'border-blue-600 bg-blue-50' : 'border-slate-300'} ${running ? 'cursor-not-allowed opacity-60' : 'hover:border-slate-400'}`}>
        <UploadCloud className="h-8 w-8 text-slate-400" /><p className="text-sm"><span className="font-medium text-blue-700">Choose a PDF</span> or drag it here</p><p className="text-xs text-slate-600">PDF only</p></div>
      <input ref={pick} type="file" accept="application/pdf,.pdf" hidden disabled={running} onChange={e => { choose(e.target.files?.[0]); e.target.value = '' }} />
      {localErr && <p role="alert" className="mt-3 text-sm text-red-700">{localErr}</p>}
      {file && <div className="mt-4 flex items-center gap-3 rounded-md border border-slate-200 p-3"><FileText className="h-5 w-5 shrink-0 text-slate-500" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{file.name}</p><p className="text-xs text-slate-600">{fmtSize(file.size)}</p></div>
        <Btn onClick={open} disabled={running}>Replace</Btn><Btn aria-label="Remove file" onClick={() => setFile(null)} disabled={running}><X className="h-4 w-4" /></Btn></div>}
      {state.phase === 'error' && state.error && <div role="alert" className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-900"><p className="flex items-start gap-2 font-medium"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />{state.error.message}</p>{state.error.hint && <p className="mt-1 pl-6">{state.error.hint}</p>}</div>}
      {running && <div role="status" className="mt-4 flex items-center gap-3 rounded-md bg-slate-50 p-3 text-sm"><Spinner /><span>Processing your PDF. This can take a while for longer packages. Keep this page open.</span></div>}
      <div className="mt-5 flex flex-wrap gap-2"><Btn variant="primary" disabled={!file || running} onClick={analyze}>{running ? 'Analyzing…' : state.phase === 'error' ? <><RefreshCw className="h-4 w-4" />Retry analysis</> : 'Analyze package'}</Btn>
        {!file && <span className="self-center text-sm text-slate-600">Select a PDF to enable analysis.</span>}</div>
    </Card></>
}
