import { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate, Link } from 'react-router-dom'
import { LayoutDashboard, FileText, Ship, ScanSearch, BarChart3, ListChecks, Settings, Bell, Search, Upload, Menu, PanelLeftClose, PanelLeftOpen, ShieldCheck, User } from 'lucide-react'
import toast from 'react-hot-toast'
import { Btn } from './ui'

const nav = [['/', 'Overview', LayoutDashboard], ['/documents', 'Documents', FileText], ['/operations', 'Import/Export Files', Ship], ['/verification', 'Verification Center', ScanSearch],
  ['/reports', 'Reports', BarChart3], ['/rules', 'Validation Rules', ListChecks], ['/settings', 'Settings', Settings]] as const
const notes = ['3 documents need review in IMP-2026-0149', 'Rule change saved: Currency (Commercial Invoice)', 'EXP-2026-0163 is fully verified']

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false); const [drawer, setDrawer] = useState(false)
  const [menu, setMenu] = useState<'' | 'bell' | 'user'>(''); const [q, setQ] = useState('')
  const { pathname } = useLocation(); const go = useNavigate()
  const title = nav.find(([to]) => (to === '/' ? pathname === '/' : pathname.startsWith(to)))?.[1] ?? ''
  return <div className="flex min-h-screen">
    {drawer && <div className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden" onClick={() => setDrawer(false)} />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex flex-col border-r border-slate-200 bg-white transition-all lg:static ${drawer ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'} ${collapsed ? 'lg:w-16' : 'lg:w-60'} w-60`}>
      <div className="flex h-14 items-center gap-2 border-b border-slate-200 px-4"><ShieldCheck className="h-6 w-6 shrink-0 text-blue-600" /><span className={`font-semibold ${collapsed ? 'lg:hidden' : ''}`}>DocuVerify AI</span></div>
      <nav className="flex-1 space-y-1 p-2" aria-label="Main">{nav.map(([to, label, Icon]) =>
        <NavLink key={to} to={to} end={to === '/'} onClick={() => setDrawer(false)} title={label}
          className={({ isActive }) => `flex items-center gap-3 rounded-md px-3 py-2 text-sm ${isActive ? 'bg-blue-50 font-medium text-blue-700' : 'text-slate-600 hover:bg-slate-100'}`}>
          <Icon className="h-4 w-4 shrink-0" /><span className={collapsed ? 'lg:hidden' : ''}>{label}</span></NavLink>)}</nav>
      <button onClick={() => setCollapsed(c => !c)} className="m-2 hidden items-center gap-3 rounded-md px-3 py-2 text-sm text-slate-500 hover:bg-slate-100 lg:flex" aria-label="Collapse sidebar">
        {collapsed ? <PanelLeftOpen className="h-4 w-4" /> : <><PanelLeftClose className="h-4 w-4" />Collapse</>}</button>
    </aside>
    <div className="flex min-w-0 flex-1 flex-col">
      <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-slate-200 bg-white px-4">
        <button className="rounded p-1 hover:bg-slate-100 lg:hidden" aria-label="Open menu" onClick={() => setDrawer(true)}><Menu className="h-5 w-5" /></button>
        <div className="hidden text-sm sm:block"><span className="text-slate-400">DocuVerify / </span><span className="font-medium">{title}</span></div>
        <form className="relative ml-auto max-w-xs flex-1" onSubmit={e => { e.preventDefault(); go(`/documents?q=${encodeURIComponent(q)}`) }}>
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" /><input aria-label="Search documents" value={q} onChange={e => setQ(e.target.value)} placeholder="Search documents…" className="w-full rounded-md border border-slate-300 py-2 pl-8 pr-3 text-sm" /></form>
        <Btn variant="primary" onClick={() => go('/documents?upload=1')}><Upload className="h-4 w-4" /><span className="hidden sm:inline">Upload Documents</span></Btn>
        <div className="relative"><button aria-label="Notifications" onClick={() => setMenu(m => m === 'bell' ? '' : 'bell')} className="relative rounded p-2 hover:bg-slate-100"><Bell className="h-5 w-5" /><span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500" /></button>
          {menu === 'bell' && <div className="absolute right-0 mt-1 w-72 rounded-md border border-slate-200 bg-white p-2 shadow-md">{notes.map(n => <p key={n} className="rounded p-2 text-sm hover:bg-slate-50">{n}</p>)}
            <Link to="/verification" onClick={() => setMenu('')} className="block p-2 text-sm text-blue-600">Open Verification Center</Link></div>}</div>
        <div className="relative"><button aria-label="Profile menu" onClick={() => setMenu(m => m === 'user' ? '' : 'user')} className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-xs font-medium text-white">YB</button>
          {menu === 'user' && <div className="absolute right-0 mt-1 w-48 rounded-md border border-slate-200 bg-white p-1 shadow-md">
            <Link to="/settings" onClick={() => setMenu('')} className="flex items-center gap-2 rounded p-2 text-sm hover:bg-slate-50"><User className="h-4 w-4" />Profile & settings</Link>
            <button onClick={() => { setMenu(''); toast('Sign-in is not connected yet (backend pending).') }} className="w-full rounded p-2 text-left text-sm hover:bg-slate-50">Sign out</button></div>}</div>
      </header>
      <main className="flex-1 p-4 lg:p-6" onClick={() => menu && setMenu('')}><Outlet /></main>
    </div></div>
}
