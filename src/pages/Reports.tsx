import { useState } from 'react'
import { Download, Printer } from 'lucide-react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts'
import toast from 'react-hot-toast'
import { api } from '../services/api'
import { useAsync } from '../hooks'
import { Btn, Card, Empty, inputCls, Load, PageHeader, statusLabel } from '../components/ui'
import type { DocStatus } from '../types'

export default function Reports() {
  const [from, setFrom] = useState('2026-10-01'); const [to, setTo] = useState('2026-10-31')
  const docs = useAsync(() => api.listDocuments()); const dash = useAsync(() => api.getDashboard())
  return <><PageHeader title="Reports" text="Verification summaries for a date range, based on upload date." actions={<>
    <Btn onClick={() => window.print()}><Printer className="h-4 w-4" />Print / PDF</Btn></>} />
    <Card className="mb-4 flex flex-wrap items-end gap-3 p-3"><label className="text-sm">From<input type="date" className={inputCls} value={from} onChange={e => setFrom(e.target.value)} /></label><label className="text-sm">To<input type="date" className={inputCls} value={to} onChange={e => setTo(e.target.value)} /></label>
      {from > to && <p role="alert" className="text-sm text-red-600">Start date must be before end date.</p>}</Card>
    <Load s={docs}>{all => { const r = from > to ? [] : all.filter(d => d.uploaded >= from && d.uploaded <= to)
      if (!r.length) return <Card><Empty title="No documents in this range" text="Widen the date range to see results." /></Card>
      const st = (['verified', 'review', 'incomplete', 'pending'] as DocStatus[]).map(k => ({ k, n: r.filter(d => d.status === k).length }))
      const types = [...new Set(r.map(d => d.type))].map(t => ({ type: t, Verified: r.filter(d => d.type === t && d.status === 'verified').length, 'Needs attention': r.filter(d => d.type === t && (d.status === 'review' || d.status === 'incomplete')).length }))
      const csv = () => { const rows = [['id', 'name', 'type', 'uploaded', 'status'], ...r.map(d => [d.id, d.name, d.type, d.uploaded, d.status])]; const a = document.createElement('a')
        a.href = URL.createObjectURL(new Blob([rows.map(x => x.join(',')).join('\n')], { type: 'text/csv' })); a.download = `docuverify-report-${from}_${to}.csv`; a.click(); toast.success('CSV exported') }
      return <div className="space-y-4"><div className="flex justify-end"><Btn onClick={csv}><Download className="h-4 w-4" />Export CSV</Btn></div>
        <div className="grid gap-4 sm:grid-cols-4">{st.map(x => <Card key={x.k} className="p-4"><p className="text-sm text-slate-500">{statusLabel[x.k]}</p><p className="text-2xl font-semibold">{x.n}</p><p className="text-xs text-slate-400">{Math.round(x.n / r.length * 100)}% of {r.length}</p></Card>)}</div>
        <div className="grid gap-4 lg:grid-cols-2">
          <Card className="p-4"><h2 className="mb-3 text-sm font-semibold">Status by document type</h2><div className="h-64"><ResponsiveContainer><BarChart data={types}><CartesianGrid stroke="#e2e8f0" vertical={false} /><XAxis dataKey="type" fontSize={11} /><YAxis allowDecimals={false} fontSize={12} /><Tooltip /><Legend /><Bar dataKey="Verified" stackId="a" fill="#16a34a" /><Bar dataKey="Needs attention" stackId="a" fill="#d97706" /></BarChart></ResponsiveContainer></div></Card>
          <Card className="p-4"><h2 className="mb-3 text-sm font-semibold">Common errors (sample data)</h2><Load s={dash}>{d => <table className="w-full text-sm"><tbody>{d.issues.map(i => <tr key={i.issue} className="border-t border-slate-100 first:border-0"><td className="py-2">{i.issue}</td><td className="py-2 text-right font-medium">{i.count}</td></tr>)}</tbody></table>}</Load></Card></div></div> }}</Load></>
}
