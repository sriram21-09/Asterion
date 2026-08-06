import { useState } from 'react'
import { createPortal } from 'react-dom'
import { Flame, Info, X, ShieldCheck } from 'lucide-react'
import { cn } from '@/lib/cn'

interface HeatmapTransparencyBadgeProps {
  hasGeneratedData?: boolean
  onViewDetails?: () => void
  className?: string
}

export function HeatmapTransparencyBadge({
  hasGeneratedData = false,
  onViewDetails,
  className,
}: HeatmapTransparencyBadgeProps) {
  const [showModal, setShowModal] = useState(false)

  if (!hasGeneratedData) {
    return null
  }

  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className={cn(
          'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-surface-primary/95 border border-amber-500/40 text-amber-500 hover:text-amber-400 hover:bg-surface-primary shadow-lg backdrop-blur-md text-xs font-bold transition-all duration-200 cursor-pointer group select-none',
          className
        )}
      >
        <Flame className="w-3.5 h-3.5 text-amber-500 animate-pulse" />
        <span>Generated Measurements Used</span>
        <Info className="w-3 h-3 text-amber-500/70 group-hover:text-amber-400" />
      </button>

      {/* Heatmap Transparency Modal */}
      {showModal &&
        createPortal(
          <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-in fade-in">
            <div className="w-full max-w-md rounded-2xl bg-surface-primary border border-border-secondary p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-border-primary pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="p-2 rounded-xl bg-amber-500/10 text-amber-500 border border-amber-500/20">
                    <Flame className="w-4 h-4" />
                  </div>
                  <h3 className="text-sm font-bold text-content-primary">Heatmap Transparency</h3>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-1 rounded-lg text-content-tertiary hover:text-content-primary hover:bg-surface-secondary transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3 text-xs leading-relaxed text-content-secondary">
                <p>
                  This heatmap includes <b>generated measurements</b> because the imported dataset did not contain every signal measurement (e.g. RSSI or Timing Advance) required by the scientific localization pipeline.
                </p>
                <div className="p-3 rounded-xl bg-surface-secondary/60 border border-border-secondary space-y-1 text-[11px]">
                  <div className="font-bold text-content-primary flex items-center gap-1.5">
                    <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                    <span>Evidence Integrity</span>
                  </div>
                  <p className="text-content-tertiary">
                    Only missing signal values supplement spatial density. Raw imported telecom records remain completely unchanged.
                  </p>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                {onViewDetails && (
                  <button
                    onClick={() => {
                      setShowModal(false)
                      onViewDetails()
                    }}
                    className="px-3 py-1.5 rounded-xl bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 font-semibold text-xs border border-amber-500/30 transition-colors cursor-pointer"
                  >
                    View Provenance Details
                  </button>
                )}
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-1.5 rounded-xl bg-brand-primary text-white font-semibold text-xs hover:bg-brand-primary/90 transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>,
          document.body
        )}
    </>
  )
}
