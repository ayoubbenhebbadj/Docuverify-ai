export const REQUIRED_DOCS = [
  { id: 'commercial_invoice', label: 'Commercial invoice' }, { id: 'packing_list', label: 'Packing list' },
  { id: 'bill_of_lading', label: 'Bill of lading' }, { id: 'certificate_of_origin', label: 'Certificate of origin' },
  { id: 'certificate_of_quality', label: 'Certificate of quality' }, { id: 'certificate_of_conformity', label: 'Certificate of conformity' },
  { id: 'phytosanitary_certificate', label: 'Phytosanitary certificate' }, { id: 'fumigation_certificate', label: 'Fumigation certificate' },
] as const
export const MAX_BYTES = 10 * 1024 * 1024 // matches MAX_FILE_SIZE in backend/app/main.py
export const titleCase = (s: string) => { const t = s.replace(/_/g, ' '); return t.charAt(0).toUpperCase() + t.slice(1) }
export const docLabel = (id: string) => REQUIRED_DOCS.find(d => d.id === id)?.label ?? (id === 'unknown' ? 'Unrecognized pages' : titleCase(id))
export const fmtSize = (b: number) => b < 1048576 ? `${Math.max(1, Math.round(b / 1024))} KB` : `${(b / 1048576).toFixed(1)} MB`
export function pageRange(pages: number[]): string {
  const p = [...pages].sort((a, b) => a - b), out: string[] = []
  for (let i = 0; i < p.length; i++) { let j = i; while (p[j + 1] === p[j] + 1) j++; out.push(j > i ? `${p[i]}–${p[j]}` : `${p[i]}`); i = j }
  return out.join(', ') || '—'
}
