import { useState, useEffect, useMemo } from 'react'
import {
  FileText,
  Scan,
  Terminal,
  Lightbulb,
  CheckCircle2,
  Clock,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  Layers,
  Activity,
  Zap,
} from 'lucide-react'
import { useLanguage } from '../state/LanguageContext'
import { Spinner } from './ui'

interface ProcessingMotionProps {
  fileName?: string
  fileSize?: string
}

interface LogEntry {
  id: string
  time: string
  text: string
  tone: 'info' | 'success' | 'process'
}

export default function ProcessingMotion({ fileName, fileSize }: ProcessingMotionProps) {
  const { t, language } = useLanguage()

  // Elapsed time in seconds
  const [seconds, setSeconds] = useState(0)
  // Interactive Toggles
  const [showRadar, setShowRadar] = useState(true)
  const [showLogs, setShowLogs] = useState(true)
  const [showTips, setShowTips] = useState(true)
  const [tipIndex, setTipIndex] = useState(0)

  // Stage definitions mapped to t.processing.stages
  const stages = useMemo(() => {
    return [
      { key: 'reading', ...t.processing.stages.reading, threshold: 0 },
      { key: 'ocr', ...t.processing.stages.ocr, threshold: 18 },
      { key: 'classification', ...t.processing.stages.classification, threshold: 38 },
      { key: 'extraction', ...t.processing.stages.extraction, threshold: 58 },
      { key: 'validation', ...t.processing.stages.validation, threshold: 78 },
      { key: 'results', ...t.processing.stages.results, threshold: 92 },
    ]
  }, [t])

  // Progress percentage (0 - 98% simulated smoothly)
  const [progress, setProgress] = useState(6)

  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((s) => s + 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    // Non-linear realistic progress increment
    const progressTimer = setInterval(() => {
      setProgress((p) => {
        if (p < 25) return p + 3
        if (p < 55) return p + 2
        if (p < 80) return p + 1.2
        if (p < 95) return p + 0.5
        return Math.min(97.5, p + 0.1)
      })
    }, 400)
    return () => clearInterval(progressTimer)
  }, [])

  // Determine current active stage index
  const activeStageIndex = useMemo(() => {
    for (let i = stages.length - 1; i >= 0; i--) {
      if (progress >= stages[i].threshold) return i
    }
    return 0
  }, [progress, stages])

  // Live diagnostic logs generated as stages advance
  const logEntries = useMemo<LogEntry[]>(() => {
    const list: LogEntry[] = [
      {
        id: '1',
        time: '+0.4s',
        text: t.processing.logs.init,
        tone: 'info',
      },
    ]

    if (progress >= 15) {
      list.push({
        id: '2',
        time: '+1.8s',
        text: t.processing.logs.reading,
        tone: 'process',
      })
    }
    if (progress >= 35) {
      list.push({
        id: '3',
        time: '+3.5s',
        text: t.processing.logs.ocrDetect,
        tone: 'process',
      })
    }
    if (progress >= 55) {
      list.push({
        id: '4',
        time: '+6.2s',
        text: t.processing.logs.classifying,
        tone: 'success',
      })
    }
    if (progress >= 75) {
      list.push({
        id: '5',
        time: '+8.9s',
        text: t.processing.logs.extractingFields,
        tone: 'process',
      })
    }
    if (progress >= 88) {
      list.push({
        id: '6',
        time: '+11.4s',
        text: t.processing.logs.crossValidating,
        tone: 'process',
      })
    }
    if (progress >= 94) {
      list.push({
        id: '7',
        time: '+13.8s',
        text: t.processing.logs.finalizing,
        tone: 'success',
      })
    }

    return list
  }, [progress, t])

  const formattedTime = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(
    seconds % 60
  ).padStart(2, '0')}`

  const currentStage = stages[activeStageIndex]

  // Dynamic animated badge label (extracting ... ... ... results)
  const motionPill = useMemo(() => {
    if (activeStageIndex <= 1) return language === 'fr' ? 'Extraction en cours…' : 'Extracting…'
    if (activeStageIndex === 2) return language === 'fr' ? 'Classification…' : 'Classifying…'
    if (activeStageIndex === 3) return language === 'fr' ? 'Extraction des données…' : 'Extracting fields…'
    if (activeStageIndex === 4) return language === 'fr' ? 'Validation croisée…' : 'Validating…'
    return language === 'fr' ? 'Préparation des résultats…' : 'Compiling results…'
  }, [activeStageIndex, language])

  const tips = t.processing.tipsList
  const currentTip = tips[tipIndex % tips.length]

  return (
    <div className="mt-6 space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-blue-200 bg-linear-to-r from-blue-50 via-indigo-50/40 to-white p-5 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/20">
              <Activity className="h-6 w-6 animate-pulse" />
              <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex h-3.5 w-3.5 rounded-full bg-blue-500" />
              </span>
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">{t.processing.mainTitle}</h3>
              <p className="text-xs text-slate-600">{t.processing.subTitle}</p>
            </div>
          </div>

          {/* Time & File Pill */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-2xs">
              <Clock className="h-3.5 w-3.5 text-blue-600" />
              <span>{t.processing.elapsed}:</span>
              <span className="font-mono font-semibold text-slate-900">{formattedTime}</span>
            </div>
            {fileName && (
              <div className="hidden max-w-xs truncate rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs text-slate-600 sm:block">
                <span className="font-medium text-slate-900">{fileName}</span>
                {fileSize && <span className="ml-1 text-slate-400">({fileSize})</span>}
              </div>
            )}
          </div>
        </div>

        {/* Dynamic Progress Bar */}
        <div className="mt-5 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="flex items-center gap-2 font-semibold text-blue-800">
              <Zap className="h-3.5 w-3.5 text-blue-600" />
              {currentStage.title}
            </span>
            <span className="font-mono font-bold text-blue-700">{Math.round(progress)}%</span>
          </div>
          <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full rounded-full animate-shimmer-bar transition-all duration-300"
              style={{ width: `${Math.min(100, progress)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Interactive Toggles Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-slate-50/70 p-3 text-xs">
        <span className="font-semibold text-slate-600 uppercase tracking-wider">
          {t.processing.activeMotionBadge}
        </span>
        <div className="flex flex-wrap items-center gap-2">
          {/* Toggle 1: Radar Visualizer */}
          <button
            type="button"
            onClick={() => setShowRadar((v) => !v)}
            className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 font-medium transition-colors ${
              showRadar
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-100'
            }`}
          >
            <Scan className="h-3.5 w-3.5" />
            <span>{t.processing.toggles.radar}</span>
          </button>

          {/* Toggle 2: Diagnostic Logs */}
          <button
            type="button"
            onClick={() => setShowLogs((v) => !v)}
            className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 font-medium transition-colors ${
              showLogs
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-100'
            }`}
          >
            <Terminal className="h-3.5 w-3.5" />
            <span>{t.processing.toggles.liveLogs}</span>
          </button>

          {/* Toggle 3: Customs Tips */}
          <button
            type="button"
            onClick={() => setShowTips((v) => !v)}
            className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 font-medium transition-colors ${
              showTips
                ? 'bg-blue-600 text-white shadow-2xs'
                : 'border border-slate-300 bg-white text-slate-700 hover:bg-slate-100'
            }`}
          >
            <Lightbulb className="h-3.5 w-3.5" />
            <span>{t.processing.toggles.tips}</span>
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        {/* Left Column: Visual Radar / Laser Scanner & Stage Timeline (7 cols) */}
        <div className="space-y-6 lg:col-span-7">
          {/* Visual Scanner Card (Interactive Toggleable) */}
          {showRadar && (
            <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-linear-to-b from-slate-950 via-slate-900 to-slate-950 p-6 text-white shadow-lg">
              {/* Subtle background grid pattern */}
              <div
                className="pointer-events-none absolute inset-0 opacity-15"
                style={{
                  backgroundImage:
                    'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.4) 1px, transparent 0)',
                  backgroundSize: '24px 24px',
                }}
              />

              {/* Status Header */}
              <div className="relative z-10 flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center gap-2">
                  <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-400 animate-ping" />
                  <span className="text-xs font-mono font-medium tracking-wide text-emerald-400 uppercase">
                    {t.processing.fastScanLabel}
                  </span>
                </div>
                <div className="inline-flex items-center gap-1.5 rounded-full bg-blue-500/20 px-3 py-0.5 text-xs font-medium text-blue-300 ring-1 ring-blue-400/30">
                  <Sparkles className="h-3 w-3 animate-spin" />
                  <span>{motionPill}</span>
                </div>
              </div>

              {/* Scanner Screen Area */}
              <div className="relative my-6 flex h-48 items-center justify-center rounded-lg border border-slate-800/80 bg-slate-900/60 p-4">
                {/* Moving Laser Beam */}
                <div className="pointer-events-none absolute left-0 right-0 h-1 bg-linear-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_12px_#38bdf8] animate-scanline" />

                {/* Simulated Document Card */}
                <div className="relative flex w-64 flex-col gap-2 rounded-lg border border-slate-700/80 bg-slate-800/90 p-4 shadow-xl">
                  <div className="flex items-center justify-between border-b border-slate-700/60 pb-2">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-cyan-400" />
                      <span className="font-mono text-xs text-slate-300">
                        {fileName ? fileName.slice(0, 18) : 'shipment_doc.pdf'}
                      </span>
                    </div>
                    <span className="font-mono text-[10px] text-slate-400">P. 1–{activeStageIndex + 1}</span>
                  </div>

                  {/* Simulated text lines */}
                  <div className="space-y-1.5 py-1">
                    <div className="h-2 w-3/4 rounded-sm bg-slate-600/70" />
                    <div className="h-2 w-full rounded-sm bg-slate-600/50" />
                    <div className="h-2 w-5/6 rounded-sm bg-cyan-500/40" />
                    <div className="h-2 w-2/3 rounded-sm bg-slate-600/50" />
                  </div>

                  <div className="mt-1 flex items-center justify-between pt-1 text-[10px] text-slate-400">
                    <span className="font-mono">OCR: 300 DPI</span>
                    <span className="flex items-center gap-1 font-mono text-cyan-300">
                      <Layers className="h-3 w-3" />
                      {activeStageIndex + 1}/6
                    </span>
                  </div>
                </div>

                {/* Radar Waves Behind Document */}
                <div className="pointer-events-none absolute flex items-center justify-center">
                  <div className="h-36 w-36 rounded-full border border-cyan-500/20 animate-pulse-radar" />
                  <div
                    className="h-24 w-24 rounded-full border border-blue-500/30 animate-pulse-radar"
                    style={{ animationDelay: '0.8s' }}
                  />
                </div>
              </div>

              {/* Bottom detail pill */}
              <div className="relative z-10 flex items-center justify-between rounded-lg bg-slate-950/70 px-3 py-2 text-xs text-slate-300">
                <span className="truncate text-slate-400">{currentStage.desc}</span>
                <span className="ml-2 font-mono text-cyan-400">{formattedTime}</span>
              </div>
            </div>
          )}

          {/* Stepper Progression Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
            <h4 className="mb-4 text-sm font-bold text-slate-900">{t.processing.currentPhase}</h4>
            <div className="space-y-3">
              {stages.map((stage, idx) => {
                const isDone = idx < activeStageIndex
                const isActive = idx === activeStageIndex
                return (
                  <div
                    key={stage.key}
                    className={`flex items-start gap-3 rounded-lg border p-3 transition-all ${
                      isActive
                        ? 'border-blue-300 bg-blue-50/70 shadow-xs'
                        : isDone
                        ? 'border-slate-100 bg-slate-50/60 opacity-80'
                        : 'border-transparent text-slate-400 opacity-50'
                    }`}
                  >
                    <div className="mt-0.5 shrink-0">
                      {isDone ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                      ) : isActive ? (
                        <Spinner className="h-5 w-5 text-blue-600" />
                      ) : (
                        <div className="flex h-5 w-5 items-center justify-center rounded-full border border-slate-300 text-xs font-semibold text-slate-500">
                          {idx + 1}
                        </div>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p
                          className={`text-sm font-semibold ${
                            isActive ? 'text-blue-900' : isDone ? 'text-slate-800' : 'text-slate-500'
                          }`}
                        >
                          {stage.title}
                        </p>
                        {isActive && (
                          <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">
                            IN PROGRESS
                          </span>
                        )}
                        {isDone && (
                          <span className="text-[10px] font-semibold text-emerald-700">DONE</span>
                        )}
                      </div>
                      <p
                        className={`mt-0.5 text-xs ${
                          isActive ? 'text-blue-800' : 'text-slate-500'
                        }`}
                      >
                        {stage.desc}
                      </p>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Right Column: Live Logs & Tips Carousel (5 cols) */}
        <div className="space-y-6 lg:col-span-5">
          {/* Live Diagnostic Logs (Interactive Toggleable) */}
          {showLogs && (
            <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-white shadow-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                <div className="flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-emerald-400" />
                  <span className="font-mono text-xs font-bold text-slate-200">
                    {t.processing.toggles.liveLogs}
                  </span>
                </div>
                <span className="flex items-center gap-1.5 rounded-full bg-emerald-950 px-2 py-0.5 font-mono text-[10px] text-emerald-400 ring-1 ring-emerald-500/30">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  STREAM
                </span>
              </div>

              <div className="mt-3 max-h-56 space-y-2 overflow-y-auto pr-1 font-mono text-[11px] leading-relaxed">
                {logEntries.map((log) => (
                  <div key={log.id} className="flex items-start gap-2 border-l-2 border-slate-800 pl-2">
                    <span className="shrink-0 text-slate-500">{log.time}</span>
                    <span
                      className={
                        log.tone === 'success'
                          ? 'text-emerald-300'
                          : log.tone === 'process'
                          ? 'text-cyan-300'
                          : 'text-slate-300'
                      }
                    >
                      {log.text}
                    </span>
                  </div>
                ))}
              </div>

              <div className="mt-3 flex items-center justify-between border-t border-slate-800/80 pt-2 text-[10px] text-slate-400">
                <span>{logEntries.length} events logged</span>
                <span className="text-emerald-400">● Live engine</span>
              </div>
            </div>
          )}

          {/* Interactive Customs Tips Carousel (Toggleable) */}
          {showTips && (
            <div className="rounded-xl border border-amber-200/80 bg-amber-50/60 p-4 text-slate-800 shadow-2xs">
              <div className="flex items-center justify-between border-b border-amber-200/60 pb-2">
                <div className="flex items-center gap-2 text-amber-900">
                  <Lightbulb className="h-4 w-4 text-amber-600" />
                  <span className="text-xs font-bold">{t.processing.toggles.tips}</span>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setTipIndex((i) => (i - 1 + tips.length) % tips.length)}
                    aria-label={t.processing.prevTip}
                    className="flex h-6 w-6 items-center justify-center rounded-md border border-amber-300 bg-white text-slate-700 hover:bg-amber-100"
                  >
                    <ChevronLeft className="h-3.5 w-3.5" />
                  </button>
                  <span className="px-1 text-[10px] font-semibold text-amber-900">
                    {tipIndex + 1}/{tips.length}
                  </span>
                  <button
                    type="button"
                    onClick={() => setTipIndex((i) => (i + 1) % tips.length)}
                    aria-label={t.processing.nextTip}
                    className="flex h-6 w-6 items-center justify-center rounded-md border border-amber-300 bg-white text-slate-700 hover:bg-amber-100"
                  >
                    <ChevronRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              <div className="mt-3">
                <h5 className="text-xs font-bold text-amber-950">{currentTip.title}</h5>
                <p className="mt-1 text-xs leading-relaxed text-amber-900">{currentTip.text}</p>
              </div>

              <div className="mt-3 flex justify-end">
                <button
                  type="button"
                  onClick={() => setTipIndex((i) => (i + 1) % tips.length)}
                  className="inline-flex items-center gap-1 text-[11px] font-semibold text-amber-800 hover:text-amber-950 hover:underline"
                >
                  <span>{t.processing.nextTip}</span>
                  <ChevronRight className="h-3 w-3" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
