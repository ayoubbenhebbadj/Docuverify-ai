import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { LayoutDashboard, FilePlus2, ClipboardCheck, Menu, X, ShieldCheck } from 'lucide-react'
import { useLanguage } from '../state/LanguageContext'
import LanguageToggle from './LanguageToggle'

export default function Layout() {
  const [open, setOpen] = useState(false)
  const { pathname } = useLocation()
  const { t } = useLanguage()

  const nav = [
    { to: '/', label: t.nav.overview, desc: t.nav.overviewDesc, Icon: LayoutDashboard },
    { to: '/analysis', label: t.nav.newAnalysis, desc: t.nav.newAnalysisDesc, Icon: FilePlus2 },
    { to: '/results', label: t.nav.results, desc: t.nav.resultsDesc, Icon: ClipboardCheck },
  ] as const

  const cur = nav.find((item) => item.to === pathname) ?? nav[0]

  return (
    <div className="flex min-h-screen bg-slate-50">
      {open && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden print:hidden"
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform lg:static lg:translate-x-0 print:hidden ${
          open ? '' : '-translate-x-full'
        }`}
      >
        {/* Brand header */}
        <div className="flex h-16 items-center justify-between border-b border-slate-200 px-4">
          <span className="flex items-center gap-2.5 font-bold tracking-tight text-slate-900">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs">
              <ShieldCheck className="h-5 w-5" />
            </span>
            <span>{t.nav.brand}</span>
          </span>
          <button
            aria-label={t.nav.closeMenu}
            className="rounded-md p-1 text-slate-500 hover:bg-slate-100 lg:hidden"
            onClick={() => setOpen(false)}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation links */}
        <nav aria-label="Main" className="flex-1 space-y-1.5 p-3">
          {nav.map(({ to, label, Icon }) => (
            <NavLink
              key={to}
              to={to}
              end
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-50 text-blue-700 shadow-2xs'
                    : 'text-slate-700 hover:bg-slate-100'
                }`
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Sidebar Footer with Language Switcher */}
        <div className="border-t border-slate-200 p-4">
          <p className="mb-2 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            {t.nav.switchLanguage}
          </p>
          <LanguageToggle className="w-full justify-between" />
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="min-w-0 flex-1">
        {/* Mobile Header */}
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 lg:hidden print:hidden">
          <div className="flex items-center gap-3">
            <button
              aria-label={t.nav.openMenu}
              className="rounded-md p-1.5 text-slate-600 hover:bg-slate-100"
              onClick={() => setOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="font-semibold text-slate-900">{cur.label}</span>
          </div>
          <LanguageToggle />
        </header>

        <main className="mx-auto max-w-6xl p-4 lg:p-6">
          <Outlet context={cur.desc} />
        </main>
      </div>
    </div>
  )
}
