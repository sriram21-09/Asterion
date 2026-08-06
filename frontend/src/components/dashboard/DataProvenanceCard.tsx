import { useState } from 'react'
import { createPortal } from 'react-dom'
import { Database, ShieldCheck, X } from 'lucide-react'
import { cn } from '@/lib/cn'

export interface ProvenanceData {
  status?: string
  augmentation_enabled?: boolean
  counts?: {
    REAL?: number
    AUGMENTED_RSSI?: number
    AUGMENTED_TA?: number
    SIMULATED?: number
  }
  percentages?: {
    imported_pct?: number
    generated_pct?: number
  }
  total_measurements?: number
  has_generated_data?: boolean
  has_augmentation?: boolean
  has_simulation?: boolean
  scientific_integrity_statement?: string
}

interface DataProvenanceCardProps {
  provenance?: ProvenanceData | null
  className?: string
}

export function DataProvenanceCard({ provenance, className }: DataProvenanceCardProps) {
  const [showModal, setShowModal] = useState(false)

  const counts = provenance?.counts || { REAL: 0, AUGMENTED_RSSI: 0, AUGMENTED_TA: 0, SIMULATED: 0 }
  const realCount = counts.REAL || 0
  const rssiCount = counts.AUGMENTED_RSSI || 0
  const taCount = counts.AUGMENTED_TA || 0
  const simCount = counts.SIMULATED || 0

  const importedPct = provenance?.percentages?.imported_pct ?? 100
  const generatedPct = provenance?.percentages?.generated_pct ?? 0
  const statusStr = provenance?.status || (generatedPct > 0 ? 'Measurement Augmentation Active' : 'Imported Dataset Only')

  return (
    <>
      <div
        onClick={() => setShowModal(true)}
        className={cn(
          'p-5 rounded-2xl border border-border-secondary bg-surface-secondary/40 backdrop-blur-sm shadow-sm cursor-pointer hover:border-brand-primary/40 hover:bg-surface-secondary/60 transition-all duration-200 group flex flex-col justify-between',
          className
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-xl bg-blue-500/10 text-blue-500 border border-blue-500/20">
              <Database className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-content-primary group-hover:text-brand-primary transition-colors">
                Measurement Provenance
              </h3>
              <p className="text-[11px] text-content-tertiary">Signal Provenance Breakdown</p>
            </div>
          </div>
          <span
            className={cn(
              'text-[10px] font-bold px-2.5 py-1 rounded-full border',
              generatedPct > 0
                ? 'bg-amber-500/10 text-amber-500 border-amber-500/20'
                : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20'
            )}
          >
            {statusStr}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-[11px] font-mono mb-1.5 font-semibold text-content-secondary">
            <span>{importedPct}% Imported</span>
            <span>{generatedPct}% Generated</span>
          </div>
          <div className="w-full h-2 rounded-full bg-surface-primary overflow-hidden flex border border-border-secondary">
            <div
              className="h-full bg-emerald-500 transition-all duration-500"
              style={{ width: `${importedPct}%` }}
            />
            <div
              className="h-full bg-amber-500 transition-all duration-500"
              style={{ width: `${generatedPct}%` }}
            />
          </div>
        </div>

        {/* Breakdown Items */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
          <div className="p-2 rounded-lg bg-surface-primary/60 border border-border-primary flex items-center justify-between">
            <span className="text-[11px] text-emerald-500 font-semibold flex items-center gap-1">
              🟢 REAL
            </span>
            <span className="font-bold text-content-primary">{realCount}</span>
          </div>
          <div className="p-2 rounded-lg bg-surface-primary/60 border border-border-primary flex items-center justify-between">
            <span className="text-[11px] text-amber-500 font-semibold flex items-center gap-1">
              🟠 AUG RSSI
            </span>
            <span className="font-bold text-content-primary">{rssiCount}</span>
          </div>
          <div className="p-2 rounded-lg bg-surface-primary/60 border border-border-primary flex items-center justify-between">
            <span className="text-[11px] text-blue-400 font-semibold flex items-center gap-1">
              🔵 AUG TA
            </span>
            <span className="font-bold text-content-primary">{taCount}</span>
          </div>
          <div className="p-2 rounded-lg bg-surface-primary/60 border border-border-primary flex items-center justify-between">
            <span className="text-[11px] text-purple-400 font-semibold flex items-center gap-1">
              🟣 SIMULATED
            </span>
            <span className="font-bold text-content-primary">{simCount}</span>
          </div>
        </div>
      </div>

      {/* Detailed Provenance Modal */}
      {showModal &&
        createPortal(
          <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in">
            <div className="w-full max-w-lg rounded-2xl bg-surface-primary border border-border-secondary p-6 shadow-2xl space-y-5">
              <div className="flex items-center justify-between border-b border-border-primary pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 rounded-xl bg-brand-primary/10 text-brand-primary border border-brand-primary/20">
                    <Database className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-content-primary">Measurement Provenance Audit</h3>
                    <p className="text-xs text-content-tertiary">Scientific Evidence Classification Ledger</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-1.5 rounded-lg text-content-tertiary hover:text-content-primary hover:bg-surface-secondary transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="space-y-4 text-xs">
                <div className="p-3.5 rounded-xl bg-surface-secondary/50 border border-border-secondary space-y-2">
                  <div className="flex justify-between items-center text-content-secondary font-semibold">
                    <span>Provenance Status:</span>
                    <span className="font-bold text-brand-primary">{statusStr}</span>
                  </div>
                  <div className="flex justify-between items-center text-content-secondary">
                    <span>Composition Ratio:</span>
                    <span className="font-mono font-bold">{importedPct}% Real / {generatedPct}% Derived</span>
                  </div>
                </div>

                {/* Provenance Legend */}
                <div className="space-y-2">
                  <h4 className="font-bold text-content-secondary uppercase tracking-wider text-[10px]">
                    Measurement Sources Legend
                  </h4>
                  <div className="grid grid-cols-1 gap-2">
                    <div className="p-2.5 rounded-xl border border-emerald-500/30 bg-emerald-500/5 flex items-start gap-2.5">
                      <span className="text-sm">📡</span>
                      <div>
                        <span className="font-bold text-emerald-400">REAL ({realCount})</span>
                        <p className="text-content-tertiary text-[11px]">Imported directly from raw telecom CDR datasets without modification.</p>
                      </div>
                    </div>
                    <div className="p-2.5 rounded-xl border border-amber-500/30 bg-amber-500/5 flex items-start gap-2.5">
                      <span className="text-sm">🧮</span>
                      <div>
                        <span className="font-bold text-amber-400">AUGMENTED RSSI ({rssiCount})</span>
                        <p className="text-content-tertiary text-[11px]">Derived using the Log-Distance Path Loss propagation model because RSSI was omitted.</p>
                      </div>
                    </div>
                    <div className="p-2.5 rounded-xl border border-blue-500/30 bg-blue-500/5 flex items-start gap-2.5">
                      <span className="text-sm">🧮</span>
                      <div>
                        <span className="font-bold text-blue-400">AUGMENTED TA ({taCount})</span>
                        <p className="text-content-tertiary text-[11px]">Derived using Timing Advance distance estimation to support localization.</p>
                      </div>
                    </div>
                    <div className="p-2.5 rounded-xl border border-purple-500/30 bg-purple-500/5 flex items-start gap-2.5">
                      <span className="text-sm">🧪</span>
                      <div>
                        <span className="font-bold text-purple-400">SIMULATED ({simCount})</span>
                        <p className="text-content-tertiary text-[11px]">Generated by the Scenario Simulation Engine for synthetic scenario testing.</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Scientific Integrity Statement */}
                <div className="p-3.5 rounded-xl bg-blue-50 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800/50 text-blue-950 dark:text-blue-200 space-y-1 text-[11px] leading-relaxed">
                  <div className="font-bold text-blue-900 dark:text-blue-300 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                    <span>Scientific Integrity Statement</span>
                  </div>
                  <p className="text-blue-950 dark:text-blue-200/90 font-medium">
                    Imported telecom records are <b className="font-bold text-blue-950 dark:text-white">never modified</b>. Generated measurements supplement only missing signal parameters required by localization and remain explicitly marked and fully traceable throughout the platform.
                  </p>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl bg-brand-primary text-white font-semibold text-xs hover:bg-brand-primary/90 transition-colors cursor-pointer"
                >
                  Close Audit View
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </>
  )
}
