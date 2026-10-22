// MOCK DATA ONLY. Sample values below are NOT AI output.
import type { DocType, DocumentRecord, ExtractedField, Operation, Rule, FieldState } from '../types'

const T: DocType[] = ['Commercial Invoice', 'Packing List', 'Bill of Lading', 'Customs Declaration', 'Certificate of Origin']
const P = [['Shenzhen Hengtong Electronics Co.', 'China', 'Import'], ['Hamburg Maschinenbau GmbH', 'Germany', 'Import'], ['Istanbul Tekstil A.S.', 'Turkey', 'Import'],
  ['Valencia Citrus S.L.', 'Spain', 'Export'], ['Busan Marine Parts Ltd.', 'South Korea', 'Import'], ['Mumbai Spice Traders Pvt.', 'India', 'Export']] as const

export const operations: Operation[] = P.map((p, i) => ({
  id: `OP-${i + 1}`, ref: `${p[2] === 'Import' ? 'IMP' : 'EXP'}-2026-${String(142 + i * 7).padStart(4, '0')}`, kind: p[2], partner: p[0], country: p[1],
  requiredTypes: i % 2 ? T.slice(0, 4) : T, eta: `2026-11-${String(3 + i * 4).padStart(2, '0')}`
}))
const S = ['verified', 'verified', 'review', 'incomplete', 'verified', 'review'] as const
export const documents: DocumentRecord[] = operations.flatMap((op, o) => op.requiredTypes.slice(0, op.requiredTypes.length - (o === 5 ? 2 : 0)).map((t, k) => {
  const i = o * 5 + k
  return { id: `D-${1001 + i}`, name: `${t.split(' ').map(w => w[0]).join('')}_${op.ref}.pdf`, type: t, operationId: op.id, pages: 1 + (i % 4),
    uploaded: `2026-10-${String(1 + ((i * 3) % 20)).padStart(2, '0')}`, status: (i === 27 ? 'pending' : S[(i + o) % 6]) } as DocumentRecord
}))

const tpl: [string, string, string, string][] = [
  ['company', 'Company name', 'Atlas Trading International SARL', 'Header'], ['supplier', 'Supplier name', 'Shenzhen Hengtong Electronics Co.', 'Seller block'],
  ['importer', 'Importer / customer', 'Atlas Trading International SARL', 'Consignee block'], ['invoiceNo', 'Invoice number', 'INV-2026-08812', 'Top right'],
  ['invoiceDate', 'Invoice date', '2026-09-24', 'Top right'], ['amount', 'Total amount', '48,250.00', 'Totals table'], ['currency', 'Currency', 'USD', 'Totals table'],
  ['origin', 'Country of origin', 'China', 'Line items'], ['customsNo', 'Customs declaration no.', 'DZ-2026-0457712', 'Reference box'],
  ['quantity', 'Quantity', '1,200 units', 'Line items'], ['weight', 'Gross weight', '2,340 kg', 'Footer']]
const note: Record<FieldState, string> = { valid: '', missing: 'No matching text found in document', invalid: 'Value fails format or consistency check', uncertain: 'Low-contrast scan, please confirm' }
export const fieldStore: Record<string, ExtractedField[]> = {}
export function fieldsFor(d: DocumentRecord): ExtractedField[] {
  if (fieldStore[d.id]) return fieldStore[d.id]
  const n = Number(d.id.slice(2))
  return (fieldStore[d.id] = tpl.map(([key, label, value, ev], i) => {
    let state: FieldState = 'valid'
    if (d.status === 'incomplete' && (n + i) % 4 === 0) state = 'missing'
    else if (d.status === 'incomplete' && (n + i) % 7 === 0) state = 'invalid'
    else if (d.status === 'review' && (n + i) % 4 === 0) state = 'uncertain'
    else if (d.status === 'review' && (n + i) % 9 === 0) state = 'invalid'
    const v = state === 'missing' ? '' : state === 'invalid' ? (key === 'invoiceDate' ? '2026-13-40' : value + ' ??') : value
    const pg = 1 + (i % d.pages)
    return { key, label, value: v, state, confidence: state === 'valid' ? 0.93 + (i % 5) / 100 : state === 'uncertain' ? 0.58 : state === 'missing' ? 0 : 0.41,
      page: state === 'missing' ? undefined : pg, evidence: state === 'valid' ? `${ev}, p.${pg}` : note[state], resolved: false }
  }))
}
export const rules: Rule[] = [
  { id: 'R1', docType: 'Commercial Invoice', field: 'Invoice number', kind: 'required', description: 'Must be present on every commercial invoice.', enabled: true },
  { id: 'R2', docType: 'Commercial Invoice', field: 'Currency', kind: 'format', description: 'Must be a valid ISO 4217 code (USD, EUR, DZD...).', enabled: true },
  { id: 'R3', docType: 'Commercial Invoice', field: 'Total amount', kind: 'crossCheck', description: 'Must equal the sum of line items.', enabled: true },
  { id: 'R4', docType: 'Packing List', field: 'Gross weight', kind: 'range', description: 'Gross weight must be greater than net weight.', enabled: true },
  { id: 'R5', docType: 'Bill of Lading', field: 'Importer / customer', kind: 'required', description: 'Consignee must match the importer on the invoice.', enabled: true },
  { id: 'R6', docType: 'Customs Declaration', field: 'Customs declaration no.', kind: 'format', description: 'Format DZ-YYYY-NNNNNNN.', enabled: true },
  { id: 'R7', docType: 'Certificate of Origin', field: 'Country of origin', kind: 'required', description: 'Required for preferential tariff claims.', enabled: false }]
