import { useState } from 'react'
import { Microscope, X, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/cn'

interface ScientificTransparencyBannerProps {
  provenance?: {
    status?: string
    has_generated_data?: boolean
    counts?: {
      REAL?: number
      AUGMENTED_RSSI?: number
      AUGMENTED_TA?: number
      SIMULATED?: number
    }
  } | null
  onViewDetails?: () => void
  className?: string
}

export function ScientificTransparencyBanner({
  provenance,
  onViewDetails,
  className,
}: ScientificTransparencyBannerProps) {
  const [dismissed, setDismissed] = useState(false)

  if (!provenance?.has_generated_data || dismissed) {
    return null
  }

  return (
    <div
      className={cn(
        'w-full bg-amber-50 dark:bg-amber-950/60 border-y border-amber-300 dark:border-amber-700/50 text-amber-950 dark:text-amber-100 px-4 py-2.5 transition-all duration-300 flex items-center justify-between gap-4 text-xs font-medium shadow-sm',
        className
      )}
    >
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <div className="w-7 h-7 rounded-lg bg-amber-200/80 dark:bg-amber-800/50 flex items-center justify-center shrink-0 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-700">
          <Microscope className="w-4 h-4" />
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3 min-w-0">
          <span className="font-bold tracking-wide text-amber-900 dark:text-amber-200 flex items-center gap-1.5 shrink-0">
            🔬 Scientific Transparency Notice:
          </span>
          <p className="truncate text-amber-950 dark:text-amber-100/90 text-xs font-medium">
            This investigation uses Measurement Augmentation because the imported dataset did not contain all required signal parameters. Imported evidence has NOT been modified.
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {onViewDetails && (
          <button
            onClick={onViewDetails}
            className="inline-flex items-center gap-1 px-3 py-1 rounded-lg bg-amber-200/80 hover:bg-amber-300/80 text-amber-950 dark:bg-amber-800/60 dark:hover:bg-amber-700/60 dark:text-amber-100 font-bold text-xs transition-colors border border-amber-400/60 dark:border-amber-600/60 shadow-xs cursor-pointer"
          >
            <span>View Details</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
        <button
          onClick={() => setDismissed(true)}
          className="p-1 rounded-lg text-amber-800 hover:text-amber-950 dark:text-amber-300 dark:hover:text-amber-100 hover:bg-amber-200/60 dark:hover:bg-amber-800/60 transition-colors cursor-pointer"
          title="Dismiss notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
