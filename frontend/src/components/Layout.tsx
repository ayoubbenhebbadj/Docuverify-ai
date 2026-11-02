import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { LayoutDashboard, FilePlus2, ClipboardCheck, Menu, X, ShieldCheck } from 'lucide-react'

const nav = [['/', 'Overview', 'How verification works and backend status.', LayoutDashboard], ['/analysis', 'New Analysis', 'Upload one merged shipment PDF for verification.', FilePlus2], ['/results', 'Analysis Results', 'Review the report for the most recent analysis.', ClipboardCheck]] as const
export default function Layout() {
  const [open, setOpen] = useState(false); const { pathname } = useLocation()
  const cur = nav.find(([to]) => to === pathname) ?? nav[0]
  return <div className="flex min-h-screen">
    {open && <div className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden print:hidden" onClick={() => setOpen(false)} />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-slate-200 bg-white transition-transform lg:static lg:translate-x-0 print:hidden ${open ? '' : '-translate-x-full'}`}>
      <div className="flex h-14 items-center justify-between border-b border-slate-200 px-4"><span className="flex items-center gap-2 font-semibold"><ShieldCheck className="h-6 w-6 text-blue-600" />DocuVerify AI</span><button aria-label="Close menu" className="lg:hidden" onClick={() => setOpen(false)}><X className="h-5 w-5" /></button></div>
      <nav aria-label="Main" className="space-y-1 p-2">{nav.map(([to, label, , Icon]) => <NavLink key={to} to={to} end onClick={() => setOpen(false)} className={({ isActive }) => `flex items-center gap-3 rounded-md px-3 py-2 text-sm ${isActive ? 'bg-blue-50 font-medium text-blue-700' : 'text-slate-700 hover:bg-slate-100'}`}><Icon className="h-4 w-4" />{label}</NavLink>)}</nav>
    </aside>
    <div className="min-w-0 flex-1">
      <header className="flex h-14 items-center gap-3 border-b border-slate-200 bg-white px-4 lg:hidden print:hidden"><button aria-label="Open menu" onClick={() => setOpen(true)}><Menu className="h-5 w-5" /></button><span className="font-medium">{cur[1]}</span></header>
      <main className="mx-auto max-w-6xl p-4 lg:p-6"><Outlet context={cur[2]} /></main>
    </div></div>
}
