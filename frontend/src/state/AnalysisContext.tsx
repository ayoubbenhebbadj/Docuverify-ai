import { createContext, useCallback, useContext, useRef, useState, ReactNode } from 'react'
import { analyzePackage, ApiError } from '../services/api'
import type { AnalyzeResponse } from '../types'

// In memory only: the PDF and results are never written to localStorage or any other storage.
interface State { phase: 'idle' | 'running' | 'error'; file: File | null; result: AnalyzeResponse | null; error: ApiError | null }
interface Api { state: State; setFile: (f: File | null) => void; run: (f: File) => Promise<boolean>; reset: () => void }
const Ctx = createContext<Api | null>(null)
const init: State = { phase: 'idle', file: null, result: null, error: null }

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>(init); const busy = useRef(false)
  const setFile = useCallback((file: File | null) => { if (!busy.current) setState(s => ({ ...s, file, phase: 'idle', error: null })) }, [])
  const run = useCallback(async (file: File) => {
    if (busy.current) return false // blocks duplicate submissions
    busy.current = true; setState({ phase: 'running', file, result: null, error: null })
    try { const result = await analyzePackage(file); setState({ phase: 'idle', file, result, error: null }); return true }
    catch (e) { setState({ phase: 'error', file, result: null, error: e instanceof ApiError ? e : new ApiError('Something unexpected went wrong.', 'format') }); return false }
    finally { busy.current = false }
  }, [])
  const reset = useCallback(() => { if (!busy.current) setState(init) }, [])
  return <Ctx.Provider value={{ state, setFile, run, reset }}>{children}</Ctx.Provider>
}
export function useAnalysis(): Api { const c = useContext(Ctx); if (!c) throw new Error('AnalysisProvider missing'); return c }
