import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../services/api'
import { useAsync } from '../hooks'
import { Badge, Btn, Card, Empty, inputCls, Label, Load, Modal, PageHeader } from '../components/ui'
import type { Rule } from '../types'

const DOC_TYPES = ['Commercial Invoice', 'Packing List', 'Bill of Lading', 'Customs Declaration', 'Certificate of Origin'] as const
const schema = z.object({ docType: z.enum(DOC_TYPES), field: z.string().min(2, 'Enter the field name'), kind: z.enum(['required', 'format', 'range', 'crossCheck']), description: z.string().min(5, 'Describe the rule in at least 5 characters'), enabled: z.boolean() })
type Form = z.infer<typeof schema>
const kinds = { required: 'Required', format: 'Format', range: 'Value range', crossCheck: 'Cross-check' }

export default function Rules() {
  const s = useAsync(() => api.listRules()); const [edit, setEdit] = useState<Rule | 'new' | null>(null); const [filter, setFilter] = useState('')
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<Form>({ resolver: zodResolver(schema) })
  function openForm(r: Rule | 'new') { reset(r === 'new' ? { docType: 'Commercial Invoice', field: '', kind: 'required', description: '', enabled: true } : r); setEdit(r) }
  const save = handleSubmit(async v => { await api.saveRule({ ...v, id: edit !== 'new' && edit ? edit.id : undefined }); toast.success(edit === 'new' ? 'Rule added' : 'Rule updated'); setEdit(null); s.reload() })
  return <><PageHeader title="Validation Rules" text="Choose which fields are required and how values are checked for each document type. Disabled rules are kept but not applied." actions={<Btn variant="primary" onClick={() => openForm('new')}><Plus className="h-4 w-4" />Add rule</Btn>} />
    <select aria-label="Filter by document type" className={inputCls + ' mb-4 max-w-xs'} value={filter} onChange={e => setFilter(e.target.value)}><option value="">All document types</option>{DOC_TYPES.map(t => <option key={t}>{t}</option>)}</select>
    <Load s={s}>{all => { const rows = all.filter(r => !filter || r.docType === filter)
      return rows.length === 0 ? <Card><Empty title="No rules for this document type" action={<Btn onClick={() => openForm('new')}>Add a rule</Btn>} /></Card> :
        <div className="space-y-4">{DOC_TYPES.filter(t => rows.some(r => r.docType === t)).map(t => <Card key={t}><h2 className="border-b border-slate-100 p-3 text-sm font-semibold">{t}</h2><ul className="divide-y divide-slate-100">{rows.filter(r => r.docType === t).map(r =>
          <li key={r.id} className="flex flex-wrap items-center gap-3 p-3"><div className={`min-w-48 flex-1 ${r.enabled ? '' : 'opacity-50'}`}><p className="text-sm font-medium">{r.field} <Badge tone="blue">{kinds[r.kind]}</Badge></p><p className="text-sm text-slate-500">{r.description}</p></div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={r.enabled} onChange={async () => { await api.saveRule({ ...r, enabled: !r.enabled }); toast.success(r.enabled ? 'Rule disabled' : 'Rule enabled'); s.reload() }} />Enabled</label>
            <Btn aria-label={`Edit ${r.field}`} onClick={() => openForm(r)}><Pencil className="h-4 w-4" /></Btn>
            <Btn variant="danger" aria-label={`Delete ${r.field}`} onClick={async () => { if (confirm(`Delete the rule for “${r.field}”?`)) { await api.deleteRule(r.id); toast.success('Rule deleted'); s.reload() } }}><Trash2 className="h-4 w-4" /></Btn></li>)}</ul></Card>)}</div> }}</Load>
    <Modal open={edit !== null} title={edit === 'new' ? 'Add rule' : 'Edit rule'} onClose={() => setEdit(null)}><form onSubmit={save} className="space-y-3">
      <Label text="Document type"><select className={inputCls} {...register('docType')}>{DOC_TYPES.map(t => <option key={t}>{t}</option>)}</select></Label>
      <Label text="Field" error={errors.field?.message}><input className={inputCls} {...register('field')} placeholder="e.g. Invoice number" /></Label>
      <Label text="Rule type"><select className={inputCls} {...register('kind')}>{Object.entries(kinds).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></Label>
      <Label text="Description" error={errors.description?.message}><textarea rows={3} className={inputCls} {...register('description')} /></Label>
      <label className="flex items-center gap-2 text-sm"><input type="checkbox" {...register('enabled')} />Enabled</label>
      <div className="flex justify-end gap-2 pt-2"><Btn type="button" onClick={() => setEdit(null)}>Cancel</Btn><Btn variant="primary" type="submit" disabled={isSubmitting}>Save rule</Btn></div></form></Modal></>
}
