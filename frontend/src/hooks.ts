import { useEffect, useState } from 'react'
export interface AsyncState<T> { data?: T; loading: boolean; error?: string; reload: () => void }
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []): AsyncState<T> {
  const [data, setData] = useState<T>(); const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>(); const [n, setN] = useState(0)
  useEffect(() => {
    let live = true; setLoading(true); setError(undefined)
    fn().then(d => live && setData(d)).catch(e => live && setError(e?.message ?? 'Request failed')).finally(() => live && setLoading(false))
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, n])
  return { data, loading, error, reload: () => setN(x => x + 1) }
}
