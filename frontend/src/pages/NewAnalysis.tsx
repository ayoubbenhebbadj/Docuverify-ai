import { useRef, useState, DragEvent, KeyboardEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, FileText, X, AlertTriangle, RefreshCw, ArrowRight } from 'lucide-react'
import { useAnalysis } from '../state/AnalysisContext'
import { useLanguage } from '../state/LanguageContext'
import { MAX_BYTES, MAX_PACKAGE_BYTES, fmtSize } from '../constants'
import { Btn, Card, PageHeader } from '../components/ui'
import ProcessingMotion from '../components/ProcessingMotion'

export default function NewAnalysis() {
  const { state, setFiles, run } = useAnalysis()
  const { t } = useLanguage()
  const nav = useNavigate()
  const pick = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)
  const [localErr, setLocalErr] = useState('')

  const running = state.phase === 'running'
  const files = state.files
  const totalSize = files.reduce((sum, file) => sum + file.size, 0)

  function validate(file: File): string {
    const extension = file.name.split('.').pop()?.toLowerCase() ?? ''
    const supported = ['pdf', 'docx', 'doc', 'jpg', 'jpeg', 'png']
    if (!supported.includes(extension)) {
      return 'Unsupported format. Use PDF, DOCX, DOC, JPG, JPEG or PNG.'
    }
    if (file.size === 0) return t.newAnalysis.validation.empty
    if (file.size > MAX_BYTES) return t.newAnalysis.validation.tooLarge(fmtSize(file.size))
    return ''
  }

  const addFiles = (incoming: FileList | File[]) => {
    if (running) return
    const candidates = Array.from(incoming)
    const errors: string[] = []
    const accepted: File[] = []
    for (const file of candidates) {
      const error = validate(file)
      if (error) { errors.push(`${file.name}: ${error}`); continue }
      const duplicate = [...files, ...accepted].some(
        existing => existing.name === file.name && existing.size === file.size && existing.lastModified === file.lastModified
      )
      if (!duplicate) accepted.push(file)
    }
    const next = [...files, ...accepted]
    const nextSize = next.reduce((sum, file) => sum + file.size, 0)
    if (nextSize > MAX_PACKAGE_BYTES) {
      setLocalErr(t.newAnalysis.validation.packageTooLarge(fmtSize(nextSize)))
      return
    }
    setFiles(next)
    setLocalErr(errors.join(' '))
  }

  const open = () => !running && pick.current?.click()
  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open() }
  }
  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDrag(false)
    addFiles(e.dataTransfer.files)
  }
  const analyze = async () => {
    if (files.length && await run(files)) nav('/results')
  }
  const removeFile = (index: number) => setFiles(files.filter((_, i) => i !== index))

  return (
    <>
      <PageHeader title={t.newAnalysis.title} text={t.newAnalysis.subtitle} />
      <Card className="p-5 sm:p-6">
        <p className="mb-4 rounded-lg bg-blue-50/80 p-3.5 text-sm text-blue-900 border border-blue-100">
          {t.newAnalysis.tip}
        </p>
        <div
          role="button" tabIndex={0} aria-disabled={running} aria-label={t.newAnalysis.dropTitle}
          onClick={open} onKeyDown={onKey}
          onDragOver={(e) => { e.preventDefault(); if (!running) setDrag(true) }}
          onDragLeave={() => setDrag(false)} onDrop={onDrop}
          className={`flex cursor-pointer flex-col items-center gap-2.5 rounded-xl border-2 border-dashed p-8 text-center transition-all ${
            drag ? 'border-blue-600 bg-blue-50/70 shadow-sm' : 'border-slate-300'
          } ${running ? 'cursor-not-allowed opacity-50' : 'hover:border-blue-400 hover:bg-slate-50/50'}`}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="text-sm font-medium text-slate-800">
            <span className="text-blue-700 underline decoration-blue-300 underline-offset-2">{t.newAnalysis.dropTitle}</span>{' '}
            {t.newAnalysis.dropSub}
          </p>
          <p className="text-xs text-slate-500 font-mono">PDF · DOCX · DOC · JPG · JPEG · PNG (max 20 MB each)</p>
        </div>
        <input
          ref={pick} type="file" accept=".pdf,.docx,.doc,.jpg,.jpeg,.png,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/msword,image/jpeg,image/png" multiple hidden disabled={running}
          onChange={(e) => { if (e.target.files) addFiles(e.target.files); e.target.value = '' }}
        />
        {localErr && (
          <p role="alert" className="mt-3 text-sm font-medium text-red-600 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />{localErr}
          </p>
        )}
        {files.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-semibold text-slate-800">{t.newAnalysis.selectedFiles(files.length)}</p>
              <p className="text-xs text-slate-500 font-mono">{fmtSize(totalSize)}</p>
            </div>
            {files.map((file, index) => (
              <div key={`${file.name}-${file.size}-${file.lastModified}`} className="flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50/60 p-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold text-slate-900">{file.name}</p>
                  <p className="text-xs text-slate-500 font-mono">{fmtSize(file.size)}</p>
                </div>
                <Btn aria-label={`${t.newAnalysis.remove}: ${file.name}`} onClick={() => removeFile(index)} disabled={running}>
                  <X className="h-4 w-4" />
                </Btn>
              </div>
            ))}
            <div className="flex flex-wrap gap-2">
              <Btn onClick={open} disabled={running}>{t.newAnalysis.addMore}</Btn>
              <Btn onClick={() => setFiles([])} disabled={running}>{t.newAnalysis.clearAll}</Btn>
            </div>
          </div>
        )}
        {state.phase === 'error' && state.error && (
          <div role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900">
            <p className="flex items-start gap-2 font-semibold">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />{state.error.message}
            </p>
            {state.error.hint && <p className="mt-1 pl-6 text-xs text-red-700">{state.error.hint}</p>}
          </div>
        )}
        {!running && (
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Btn variant="primary" disabled={!files.length} onClick={analyze}>
              {state.phase === 'error' ? <><RefreshCw className="h-4 w-4" />{t.newAnalysis.retryBtn}</> : <><span>{t.newAnalysis.analyzeBtn}</span><ArrowRight className="h-4 w-4" /></>}
            </Btn>
            {!files.length && <span className="text-xs text-slate-500">{t.newAnalysis.selectPdfHint}</span>}
          </div>
        )}
        {running && (
          <ProcessingMotion
            fileName={files.length === 1 ? files[0].name : `${files.length} files`}
            fileSize={fmtSize(totalSize)}
          />
        )}
      </Card>
    </>
  )
}
