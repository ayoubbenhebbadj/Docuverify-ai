export type DocStatus = 'verified' | 'review' | 'incomplete' | 'pending'
export type FieldState = 'valid' | 'missing' | 'invalid' | 'uncertain'
export type DocType = 'Commercial Invoice' | 'Packing List' | 'Bill of Lading' | 'Customs Declaration' | 'Certificate of Origin'
export interface DocumentRecord { id: string; name: string; type: DocType; uploaded: string; status: DocStatus; operationId?: string; pages: number }
export interface ExtractedField { key: string; label: string; value: string; state: FieldState; confidence: number; page?: number; evidence?: string; resolved: boolean }
export interface Operation { id: string; ref: string; kind: 'Import' | 'Export'; partner: string; country: string; requiredTypes: DocType[]; eta: string }
export interface Rule { id: string; docType: DocType; field: string; kind: 'required' | 'format' | 'range' | 'crossCheck'; description: string; enabled: boolean }
export interface Dashboard {
  kpis: { total: number; review: number; incomplete: number; verified: number }
  trend: { week: string; processed: number; flagged: number }[]
  status: { name: string; value: number; color: string }[]
  issues: { issue: string; count: number }[]
  activity: { id: string; text: string; time: string }[]
}
