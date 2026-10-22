import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus, ChevronDown } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../services/api'
import { useAsync } from '../hooks'
import { Badge, Btn, Card, Empty, inputCls, Label, Load, Modal, PageHeader, Progress, statusLabel, statusTone } from '../components/ui'
import type { DocumentRecord, Operation } from '../types'

const completeness = (o: Operation, docs: DocumentRecord[]) => Math.round(o.requiredTypes.filter(t => docs.some(d => d.type === t && d.status === 'verified')).length / o.requiredTypes.length * 100)
export default function Operations() {
  const ops = useAsync(() => api.listOperations()); const docs = useAsync(() => api.listDocuments())
  const [open, setOpen] = useState<string>(''); const [modal, setModal] = useState(false); const [f, setF] = useState({ ref: '', partner: '', country: '', kind: 'Import' as Operation['kind'] })
  const reload = () => { ops.reload(); docs.reload() }
  async function create() {
    if (!f.ref.trim() || !f.partner.trim()) return toast.error('Reference and partner are required.')
    await api.createOperation(f); toast.success(`Operation ${f.ref} created`); setModal(false); setF({ ref: '', partner: '', country: '', kind: 'Import' }); reload()
  }
  return <>
    <PageHeader title="Import/Export Files" text="Each operation groups the documents required for one shipment. Completeness counts required document types that are fully verified." actions={<Btn variant="primary" onClick={() => setModal(true)}><Plus className="h-4 w-4" />New operation</Btn>} />
    <Load s={ops}>{o => <Load s={docs}>{all => o.length === 0 ? <Card><Empty title="No operations yet" text="Create an operation, then attach its documents." /></Card> :
      <div className="space-y-3">{o.map(op => { const mine = all.filter(d => d.operationId === op.id), pct = completeness(op, all.filter(d => d.operationId === op.id)), missing = op.requiredTypes.filter(t => !mine.some(d => d.type === t)), spare = all.filter(d => !d.operationId)
        return <Card key={op.id}><button className="flex w-full flex-wrap items-center gap-4 p-4 text-left" aria-expanded={open === op.id} onClick={() => setOpen(open === op.id ? '' : op.id)}>
          <div className="min-w-48 flex-1"><p className="font-medium">{op.ref} <Badge tone="blue">{op.kind}</Badge></p><p className="text-sm text-slate-500">{op.partner}, {op.country}. ETA {op.eta}</p></div>
          <div className="w-48"><div className="mb-1 flex justify-between text-xs"><span>Completeness</span><span>{pct}%</span></div><Progress value={pct} /></div><ChevronDown className={`h-4 w-4 transition-transform ${open === op.id ? 'rotate-180' : ''}`} /></button>
          {open === op.id && <div className="border-t border-slate-100 p-4 text-sm">
            {mine.length ? <ul className="divide-y divide-slate-100">{mine.map(d => <li key={d.id} className="flex items-center justify-between py-2"><span>{d.type} <span className="text-slate-400">{d.name}</span></span><span className="flex items-center gap-3"><Badge tone={statusTone[d.status]}>{statusLabel[d.status]}</Badge>{d.status !== 'pending' && <Link className="text-blue-600" to={`/verification/${d.id}`}>Open</Link>}</span></li>)}</ul> : <p className="text-slate-500">No documents attached.</p>}
            {missing.length > 0 && <p className="mt-3 rounded-md bg-red-50 p-2 text-red-700">Missing document types: {missing.join(', ')}</p>}
            {spare.length > 0 && <div className="mt-3 flex gap-2"><select aria-label="Attach document" className={inputCls + ' max-w-xs'} defaultValue="" onChange={async e => { if (e.target.value) { await api.attachDocument(e.target.value, op.id); toast.success('Document attached'); reload() } }}><option value="">Attach an unassigned document…</option>{spare.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}</select></div>}</div>}</Card> })}</div>}</Load>}</Load>
    <Modal open={modal} title="New operation" onClose={() => setModal(false)}><div className="space-y-3">
      <Label text="Reference"><input className={inputCls} value={f.ref} onChange={e => setF({ ...f, ref: e.target.value })} placeholder="IMP-2026-0200" /></Label>
      <Label text="Type"><select className={inputCls} value={f.kind} onChange={e => setF({ ...f, kind: e.target.value as Operation['kind'] })}><option>Import</option><option>Export</option></select></Label>
      <Label text="Supplier or customer"><input className={inputCls} value={f.partner} onChange={e => setF({ ...f, partner: e.target.value })} /></Label>
      <Label text="Country"><input className={inputCls} value={f.country} onChange={e => setF({ ...f, country: e.target.value })} /></Label>
      <div className="flex justify-end gap-2 pt-2"><Btn onClick={() => setModal(false)}>Cancel</Btn><Btn variant="primary" onClick={create}>Create operation</Btn></div></div></Modal></>
}
