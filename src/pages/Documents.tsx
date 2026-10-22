import { useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { UploadCloud, Search, ChevronLeft, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../services/api'
import { useAsync } from '../hooks'
import { Badge, Btn, Card, Empty, inputCls, Load, PageHeader, statusLabel, statusTone } from '../components/ui'
import type { DocStatus } from '../types'

const MAX_MB = 10, PAGE = 8
export default function Documents() {
  const [sp, setSp] = useSearchParams(); const q = sp.get('q') ?? ''
  const [status, setStatus] = useState(''); const [type, setType] = useState(''); const [page, setPage] = useState(1)
  const [drag, setDrag] = useState(false); const [busy, setBusy] = useState(false); const [err, setErr] = useState('')
  const input = useRef<HTMLInputElement>(null); const s = useAsync(() => api.listDocuments())

  async function upload(files: FileList | File[]) {
    setErr(''); const list = Array.from(files)
    const bad = list.find(f => f.type !== 'application/pdf' && !f.name.toLowerCase().endsWith('.pdf')) ? 'Only PDF files are accepted.' : list.find(f => f.size > MAX_MB * 1048576) ? `Each file must be under ${MAX_MB} MB.` : ''
    if (bad) { setErr(bad); toast.error(bad); return }
    setBusy(true)
    try { for (const f of list) await api.uploadDocument(f); toast.success(`${list.length} file(s) received. Status: Not processed (AI verification is not connected yet).`); s.reload() }
    catch (e) { toast.error((e as Error).message) } finally { setBusy(false) }
  }
  return <>
    <PageHeader title="Documents" text="Upload PDFs and track their processing status." />
    <div onDragOver={e => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)} onDrop={e => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files) }}
      className={`mb-4 rounded-lg border-2 border-dashed p-6 text-center ${drag ? 'border-blue-600 bg-blue-50' : 'border-slate-300 bg-white'}`}>
      <UploadCloud className="mx-auto h-8 w-8 text-slate-400" /><p className="mt-2 text-sm">Drag PDF files here or <button className="font-medium text-blue-600 underline" onClick={() => input.current?.click()}>browse</button></p>
      <p className="text-xs text-slate-500">PDF only, up to {MAX_MB} MB each. Files are stored as “Not processed” until the verification backend exists.</p>
      <input ref={input} type="file" accept="application/pdf,.pdf" multiple hidden onChange={e => e.target.files && upload(e.target.files)} />
      {busy && <p role="status" className="mt-2 text-sm text-slate-500">Uploading…</p>}{err && <p role="alert" className="mt-2 text-sm text-red-600">{err}</p>}</div>
    <Card><div className="flex flex-wrap gap-2 border-b border-slate-200 p-3">
      <div className="relative min-w-48 flex-1"><Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" /><input aria-label="Search" className={inputCls + ' pl-8'} placeholder="Search by name or ID" value={q} onChange={e => { setSp(e.target.value ? { q: e.target.value } : {}); setPage(1) }} /></div>
      <select aria-label="Filter by status" className={inputCls + ' w-auto'} value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}><option value="">All statuses</option>{(Object.keys(statusLabel).slice(0, 4) as DocStatus[]).map(k => <option key={k} value={k}>{statusLabel[k]}</option>)}</select>
      <select aria-label="Filter by type" className={inputCls + ' w-auto'} value={type} onChange={e => { setType(e.target.value); setPage(1) }}><option value="">All types</option>{['Commercial Invoice', 'Packing List', 'Bill of Lading', 'Customs Declaration', 'Certificate of Origin'].map(t => <option key={t}>{t}</option>)}</select></div>
      <Load s={s}>{all => {
        const rows = all.filter(d => (!q || (d.name + d.id).toLowerCase().includes(q.toLowerCase())) && (!status || d.status === status) && (!type || d.type === type))
        const pages = Math.max(1, Math.ceil(rows.length / PAGE)), cur = Math.min(page, pages)
        if (!rows.length) return <Empty title="No documents match" text="Try clearing filters or upload a new PDF." action={<Btn onClick={() => { setSp({}); setStatus(''); setType('') }}>Clear filters</Btn>} />
        return <><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-slate-500"><tr>{['Document', 'Type', 'Uploaded', 'Pages', 'Status', ''].map(h => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr></thead>
          <tbody>{rows.slice((cur - 1) * PAGE, cur * PAGE).map(d => <tr key={d.id} className="border-t border-slate-100 hover:bg-slate-50">
            <td className="px-4 py-3"><p className="font-medium">{d.name}</p><p className="text-xs text-slate-400">{d.id}</p></td><td className="px-4 py-3">{d.type}</td><td className="px-4 py-3">{d.uploaded}</td><td className="px-4 py-3">{d.pages}</td>
            <td className="px-4 py-3"><Badge tone={statusTone[d.status]}>{statusLabel[d.status]}</Badge></td>
            <td className="px-4 py-3 text-right">{d.status === 'pending' ? <span className="text-xs text-slate-400">Awaiting backend</span> : <Link className="text-blue-600 hover:underline" to={`/verification/${d.id}`}>Open</Link>}</td></tr>)}</tbody></table></div>
          <div className="flex items-center justify-between border-t border-slate-200 p-3 text-sm text-slate-500"><span>{rows.length} documents</span><div className="flex items-center gap-2">
            <Btn aria-label="Previous page" disabled={cur === 1} onClick={() => setPage(cur - 1)}><ChevronLeft className="h-4 w-4" /></Btn>Page {cur} of {pages}<Btn aria-label="Next page" disabled={cur === pages} onClick={() => setPage(cur + 1)}><ChevronRight className="h-4 w-4" /></Btn></div></div></>
      }}</Load></Card></>
}
