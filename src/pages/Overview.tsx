import { Link } from 'react-router-dom'
import { FileText, Clock, AlertCircle, CheckCircle2, Upload, ScanSearch, BarChart3 } from 'lucide-react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts'
import { api } from '../services/api'
import { useAsync } from '../hooks'
import { Card, Load, PageHeader } from '../components/ui'

export default function Overview() {
  const s = useAsync(() => api.getDashboard())
  const today = new Date().toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
  return <>
    <PageHeader title="Welcome back, Yasmine" text={`${today}. DocuVerify AI checks import/export paperwork for missing, invalid and inconsistent information so your team can focus on exceptions.`}
      actions={<Link to="/documents?upload=1" className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"><Upload className="h-4 w-4" />Upload Documents</Link>} />
    <p className="mb-4 rounded-md border border-blue-100 bg-blue-50 p-3 text-sm text-blue-800">Prototype mode: figures below are sample data. No documents are being analysed until the backend is connected.</p>
    <Load s={s}>{d => <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{([['Total documents processed', d.kpis.total, FileText, 'text-blue-600'], ['Awaiting review', d.kpis.review, Clock, 'text-amber-600'], ['Incomplete documents', d.kpis.incomplete, AlertCircle, 'text-red-600'], ['Verified documents', d.kpis.verified, CheckCircle2, 'text-green-600']] as const).map(([l, v, Icon, c]) =>
        <Card key={l} className="flex items-center justify-between p-4"><div><p className="text-sm text-slate-500">{l}</p><p className="mt-1 text-2xl font-semibold">{v}</p></div><Icon className={`h-6 w-6 ${c}`} /></Card>)}</div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="p-4 lg:col-span-2"><h2 className="mb-3 text-sm font-semibold">Documents processed per week</h2><div className="h-64"><ResponsiveContainer><LineChart data={d.trend}><CartesianGrid stroke="#e2e8f0" vertical={false} /><XAxis dataKey="week" fontSize={12} /><YAxis fontSize={12} allowDecimals={false} /><Tooltip /><Legend />
          <Line name="Processed" dataKey="processed" stroke="#2563eb" strokeWidth={2} /><Line name="Flagged" dataKey="flagged" stroke="#d97706" strokeWidth={2} /></LineChart></ResponsiveContainer></div></Card>
        <Card className="p-4"><h2 className="mb-3 text-sm font-semibold">Verification status</h2><div className="h-64"><ResponsiveContainer><PieChart><Pie data={d.status} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80}>{d.status.map(x => <Cell key={x.name} fill={x.color} />)}</Pie><Tooltip /><Legend /></PieChart></ResponsiveContainer></div></Card>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="p-4"><h2 className="mb-3 text-sm font-semibold">Most common validation issues</h2><div className="h-56"><ResponsiveContainer><BarChart data={d.issues} layout="vertical" margin={{ left: 20 }}><XAxis type="number" fontSize={12} /><YAxis type="category" dataKey="issue" width={130} fontSize={12} /><Tooltip /><Bar dataKey="count" name="Occurrences" fill="#2563eb" /></BarChart></ResponsiveContainer></div></Card>
        <Card className="p-4"><h2 className="mb-3 text-sm font-semibold">Recent activity</h2><ul className="space-y-3">{d.activity.map(a => <li key={a.id} className="text-sm">{a.text}<span className="block text-xs text-slate-400">{a.time}</span></li>)}</ul></Card>
        <Card className="p-4"><h2 className="mb-3 text-sm font-semibold">Quick actions</h2><div className="space-y-2">{([['/documents?upload=1', 'Upload documents', Upload], ['/verification', 'Review flagged documents', ScanSearch], ['/reports', 'Open reports', BarChart3]] as const).map(([to, l, Icon]) =>
          <Link key={to} to={to} className="flex items-center gap-2 rounded-md border border-slate-200 p-3 text-sm hover:bg-slate-50"><Icon className="h-4 w-4 text-blue-600" />{l}</Link>)}</div></Card>
      </div></div>}</Load></>
}
