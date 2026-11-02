import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { Language, translations, TranslationDictionary } from '../i18n/translations'

interface LanguageContextValue {
  language: Language
  setLanguage: (lang: Language) => void
  toggleLanguage: () => void
  t: TranslationDictionary
  docLabel: (id: string) => string
  statusLabel: (status: string) => string
}

const LanguageContext = createContext<LanguageContextValue | null>(null)

const STORAGE_KEY = 'docuverify_lang'

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved === 'fr' || saved === 'en') return saved
      if (typeof navigator !== 'undefined' && navigator.language?.toLowerCase().startsWith('fr')) {
        return 'fr'
      }
    } catch {
      // fallback
    }
    return 'en'
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, language)
      document.documentElement.lang = language
    } catch {
      // storage unavailable
    }
  }, [language])

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang)
  }, [])

  const toggleLanguage = useCallback(() => {
    setLanguageState((prev) => (prev === 'en' ? 'fr' : 'en'))
  }, [])

  const t = translations[language]

  const docLabel = useCallback(
    (id: string): string => {
      const dict = translations[language].docTypes
      if (id in dict) return dict[id]
      if (id === 'unknown') return dict.unknown
      const cleaned = id.replace(/_/g, ' ')
      return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
    },
    [language]
  )

  const statusLabel = useCallback(
    (status: string): string => {
      const dict = translations[language].statuses
      if (status in dict) return dict[status]
      const cleaned = status.replace(/_/g, ' ')
      return cleaned.charAt(0).toUpperCase() + cleaned.slice(1)
    },
    [language]
  )

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        toggleLanguage,
        t,
        docLabel,
        statusLabel,
      }}
    >
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage(): LanguageContextValue {
  const ctx = useContext(LanguageContext)
  if (!ctx) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return ctx
}
