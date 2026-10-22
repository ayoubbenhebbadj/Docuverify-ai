import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Check, Save, FileText } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../services/api'
import { useAsync } from '../hooks'
import { Badge, Btn, Card, Empty, inputCls, Load, PageHeader, statusLabel, statusTone } from '../components/ui'
import type { ExtractedField } from '../types'

function Queue() {
  const s = useAsync(() => api.listDocuments())
  return <><PageHeader title="Verification Center" text="Documents that need a person to confirm, correct or complete information." />
    <Load s={s}>{all => { const q = all.filter(d => d.status === 'review' || d.status === 'incomplete')
      return <Card>{q.length === 0 ? <Empty title="Nothing to review" text="Every processed document is verified." /> : <ul className="divide-y divide-slate-100">{q.map(d =>
        <li key={d.id}><Link to={`/verification/${d.id}`} className="flex items-center justify-between gap-3 p-4 hover:bg-slate-50"><span><span className="font-medium">{d.name}</span><span className="block text-xs text-slate-500">{d.type}. Uploaded {d.uploaded}</span></span><Badge tone={statusTone[d.status]}>{statusLabel[d.status]}</Badge></Link></li>)}</ul>}</Card> }}</Load></>
}

function Workspace({ id }: { id: string }) {
  const doc = useAsync(() => api.getDocument(id), [id]); const fs = useAsync(() => api.getFields(id), [id])
  const [f, setF] = useState<ExtractedField[]>([]); const [active, setActive] = useState(''); const [saving, setSaving] = useState(false)
  useEffect(() => { if (fs.data) setF(fs.data) }, [fs.data])
  const set = (k: string, p: Partial<ExtractedField>) => setF(x => x.map(a => a.key === k ? { ...a, ...p } : a))
  const open = f.filter(a => a.state !== 'valid' && !a.resolved).length
  async function save() { setSaving(true); try { await api.saveFields(id, f); toast.success('Changes saved'); doc.reload() } catch (e) { toast.error((e as Error).message) } finally { setSaving(false) } }
  return <>
    <Link to="/verification" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-ink"><ArrowLeft className="h-4 w-4" />Back to queue</Link>
    <Load s={doc}>{d => <PageHeader title={d.name} text={`${d.type}. ${d.pages} page(s). ${open} item(s) still open.`} actions={<><Badge tone={statusTone[d.status]}>{statusLabel[d.status]}</Badge><Btn variant="primary" disabled={saving} onClick={save}><Save className="h-4 w-4" />{saving ? 'Saving…' : 'Save changes'}</Btn></>} />}</Load>
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="p-4"><div className="mb-2 flex items-center gap-2 text-sm font-semibold"><FileText className="h-4 w-4" />Document preview</div>
        <p className="mb-3 rounded-md bg-slate-100 p-2 text-xs text-slate-600">Placeholder. The real PDF viewer (for example pdf.js) will render the uploaded file once the backend serves it. Highlighted lines show the evidence reference for the selected field.</p>
        <div className="aspect-[3/4] overflow-auto rounded border border-slate-200 bg-white p-6 text-xs text-slate-500">{f.map(a => <p key={a.key} className={`mb-2 rounded px-1 py-1 ${active === a.key ? 'bg-yellow-100 text-ink' : ''}`}>{a.label}: <span className="font-medium">{a.value || '(not found)'}</span>{a.page ? <span className="text-slate-400"> [p.{a.page}]</span> : ''}</p>)}</div></Card>
      <Card><Load s={fs}>{() => <ul className="divide-y divide-slate-100">{f.map(a => <li key={a.key} className={`p-4 ${active === a.key ? 'bg-slate-50' : ''}`} onClick={() => setActive(a.key)}>
        <div className="mb-1 flex items-center justify-between gap-2"><label htmlFor={a.key} className="text-sm font-medium">{a.label}</label>{a.resolved ? <Badge tone="green">Resolved</Badge> : <Badge tone={statusTone[a.state]}>{statusLabel[a.state]}</Badge>}</div>
        <input id={a.key} className={`${inputCls} ${a.state === 'valid' || a.resolved ? '' : a.state === 'uncertain' ? 'border-amber-400' : 'border-red-400'}`} value={a.value} placeholder="Enter value" onFocus={() => setActive(a.key)} onChange={e => set(a.key, { value: e.target.value })} />
        <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-slate-500">
          <span className="flex items-center gap-1.5" title="Model confidence (sample value)"><span className="h-1.5 w-16 rounded bg-slate-100"><span className={`block h-full rounded ${a.confidence > 0.85 ? 'bg-green-600' : a.confidence > 0.5 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${a.confidence * 100}%` }} /></span>{Math.round(a.confidence * 100)}%</span>
          <span className="flex-1">{a.evidence}</span>
          {a.state !== 'valid' && <Btn className="!px-2 !py-1 text-xs" onClick={() => set(a.key, { resolved: !a.resolved })}><Check className="h-3 w-3" />{a.resolved ? 'Reopen' : 'Mark resolved'}</Btn>}</div></li>)}</ul>}</Load></Card></div></>
}
export default function Verification() { const { id } = useParams(); return id ? <Workspace id={id} /> : <Queue /> }
