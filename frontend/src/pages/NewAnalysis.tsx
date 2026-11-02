import { useRef, useState, DragEvent, KeyboardEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, FileText, X, AlertTriangle, RefreshCw, ArrowRight } from 'lucide-react'
import { useAnalysis } from '../state/AnalysisContext'
import { useLanguage } from '../state/LanguageContext'
import { MAX_BYTES, fmtSize } from '../constants'
import { Btn, Card, PageHeader } from '../components/ui'
import ProcessingMotion from '../components/ProcessingMotion'

export default function NewAnalysis() {
  const { state, setFile, run } = useAnalysis()
  const { t } = useLanguage()
  const nav = useNavigate()
  const pick = useRef<HTMLInputElement>(null)

  const [drag, setDrag] = useState(false)
  const [localErr, setLocalErr] = useState('')

  const running = state.phase === 'running'
  const file = state.file

  function validate(f: File): string {
    if (!f.name.toLowerCase().endsWith('.pdf')) {
      return t.newAnalysis.validation.notPdf
    }
    if (f.size === 0) {
      return t.newAnalysis.validation.empty
    }
    if (f.size > MAX_BYTES) {
      return t.newAnalysis.validation.tooLarge(fmtSize(f.size))
    }
    return ''
  }

  const choose = (f?: File) => {
    if (!f || running) return
    const e = validate(f)
    setLocalErr(e)
    if (!e) setFile(f)
  }

  const open = () => !running && pick.current?.click()

  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      open()
    }
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDrag(false)
    choose(e.dataTransfer.files[0])
  }

  const analyze = async () => {
    if (file && (await run(file))) {
      nav('/results')
    }
  }

  return (
    <>
      <PageHeader title={t.newAnalysis.title} text={t.newAnalysis.subtitle} />

      <Card className="p-5 sm:p-6">
        <p className="mb-4 rounded-lg bg-blue-50/80 p-3.5 text-sm text-blue-900 border border-blue-100">
          {t.newAnalysis.tip}
        </p>

        {/* Upload Drop Zone */}
        <div
          role="button"
          tabIndex={0}
          aria-disabled={running}
          aria-label={t.newAnalysis.dropTitle}
          onClick={open}
          onKeyDown={onKey}
          onDragOver={(e) => {
            e.preventDefault()
            if (!running) setDrag(true)
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={onDrop}
          className={`flex cursor-pointer flex-col items-center gap-2.5 rounded-xl border-2 border-dashed p-8 text-center transition-all ${
            drag ? 'border-blue-600 bg-blue-50/70 shadow-sm' : 'border-slate-300'
          } ${running ? 'cursor-not-allowed opacity-50' : 'hover:border-blue-400 hover:bg-slate-50/50'}`}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-50 text-blue-600">
            <UploadCloud className="h-6 w-6" />
          </div>
          <p className="text-sm font-medium text-slate-800">
            <span className="text-blue-700 underline decoration-blue-300 underline-offset-2">
              {t.newAnalysis.dropTitle}
            </span>{' '}
            {t.newAnalysis.dropSub}
          </p>
          <p className="text-xs text-slate-500 font-mono">{t.newAnalysis.pdfOnly}</p>
        </div>

        <input
          ref={pick}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          disabled={running}
          onChange={(e) => {
            choose(e.target.files?.[0])
            e.target.value = ''
          }}
        />

        {localErr && (
          <p role="alert" className="mt-3 text-sm font-medium text-red-600 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            {localErr}
          </p>
        )}

        {/* Selected File Card */}
        {file && (
          <div className="mt-4 flex items-center gap-3 rounded-lg border border-slate-200 bg-slate-50/60 p-3.5">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
              <FileText className="h-5 w-5" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-900">{file.name}</p>
              <p className="text-xs text-slate-500 font-mono">{fmtSize(file.size)}</p>
            </div>
            <Btn onClick={open} disabled={running}>
              {t.newAnalysis.replace}
            </Btn>
            <Btn
              aria-label={t.newAnalysis.remove}
              onClick={() => setFile(null)}
              disabled={running}
            >
              <X className="h-4 w-4" />
            </Btn>
          </div>
        )}

        {/* Error Alert */}
        {state.phase === 'error' && state.error && (
          <div
            role="alert"
            className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900"
          >
            <p className="flex items-start gap-2 font-semibold">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
              {state.error.message}
            </p>
            {state.error.hint && <p className="mt-1 pl-6 text-xs text-red-700">{state.error.hint}</p>}
          </div>
        )}

        {/* Action Buttons */}
        {!running && (
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Btn variant="primary" disabled={!file || running} onClick={analyze}>
              {state.phase === 'error' ? (
                <>
                  <RefreshCw className="h-4 w-4" />
                  {t.newAnalysis.retryBtn}
                </>
              ) : (
                <>
                  <span>{t.newAnalysis.analyzeBtn}</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Btn>
            {!file && (
              <span className="text-xs text-slate-500">{t.newAnalysis.selectPdfHint}</span>
            )}
          </div>
        )}

        {/* Rich Interactive Motions & Toggles while Running */}
        {running && (
          <ProcessingMotion
            fileName={file?.name}
            fileSize={file ? fmtSize(file.size) : undefined}
          />
        )}
      </Card>
    </>
  )
}
