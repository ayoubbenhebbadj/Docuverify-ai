import { createContext, useCallback, useContext, useRef, useState, ReactNode } from 'react'
import { analyzePackageFiles, ApiError } from '../services/api'
import type { AnalyzeResponse } from '../types'

// Temporary in-memory queue. Refreshing the browser clears files and results.
interface State {
  phase: 'idle' | 'running' | 'error'
  files: File[]
  result: AnalyzeResponse | null
  error: ApiError | null
}
interface Api {
  state: State
  setFiles: (files: File[]) => void
  run: (files: File[]) => Promise<boolean>
  reset: () => void
}
const Ctx = createContext<Api | null>(null)
const init: State = { phase: 'idle', files: [], result: null, error: null }

export function AnalysisProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<State>(init)
  const busy = useRef(false)

  const setFiles = useCallback((files: File[]) => {
    if (!busy.current) setState(s => ({ ...s, files, phase: 'idle', result: null, error: null }))
  }, [])

  const run = useCallback(async (files: File[]) => {
    if (busy.current || files.length === 0) return false
    busy.current = true
    setState({ phase: 'running', files, result: null, error: null })
    try {
      const result = await analyzePackageFiles(files)
      setState({ phase: 'idle', files, result, error: null })
      return true
    } catch (e) {
      setState({ phase: 'error', files, result: null, error: e instanceof ApiError ? e : new ApiError('Something unexpected went wrong.', 'format') })
      return false
    } finally {
      busy.current = false
    }
  }, [])

  const reset = useCallback(() => {
    if (!busy.current) setState(init)
  }, [])

  return <Ctx.Provider value={{ state, setFiles, run, reset }}>{children}</Ctx.Provider>
}

export function useAnalysis(): Api {
  const c = useContext(Ctx)
  if (!c) throw new Error('AnalysisProvider missing')
  return c
}
