import { useLanguage } from '../state/LanguageContext'
import { Globe } from 'lucide-react'

export default function LanguageToggle({ className = '' }: { className?: string }) {
  const { language, setLanguage, t } = useLanguage()

  return (
    <div
      className={`inline-flex items-center rounded-lg border border-slate-200 bg-slate-50/80 p-0.5 text-xs font-medium shadow-xs transition-colors ${className}`}
      role="group"
      aria-label={t.nav.switchLanguage}
    >
      <span className="flex items-center pl-2 pr-1 text-slate-400" aria-hidden="true">
        <Globe className="h-3.5 w-3.5" />
      </span>
      <button
        type="button"
        onClick={() => setLanguage('en')}
        className={`flex items-center gap-1 rounded-md px-2 py-1 transition-all ${
          language === 'en'
            ? 'bg-white font-semibold text-blue-700 shadow-xs'
            : 'text-slate-600 hover:text-slate-900'
        }`}
        aria-pressed={language === 'en'}
      >
        <span aria-hidden="true">🇬🇧</span>
        <span>EN</span>
      </button>
      <button
        type="button"
        onClick={() => setLanguage('fr')}
        className={`flex items-center gap-1 rounded-md px-2 py-1 transition-all ${
          language === 'fr'
            ? 'bg-white font-semibold text-blue-700 shadow-xs'
            : 'text-slate-600 hover:text-slate-900'
        }`}
        aria-pressed={language === 'fr'}
      >
        <span aria-hidden="true">🇫🇷</span>
        <span>FR</span>
      </button>
    </div>
  )
}
