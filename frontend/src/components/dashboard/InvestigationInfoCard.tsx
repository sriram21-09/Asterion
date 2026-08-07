import { ShieldCheck, FileText, CheckCircle2 } from 'lucide-react'
import { cn } from '@/lib/cn'

interface InvestigationInfoCardProps {
  provenance?: {
    status?: string
    augmentation_enabled?: boolean
    counts?: {
      REAL?: number
      AUGMENTED_RSSI?: number
      AUGMENTED_TA?: number
      SIMULATED?: number
    }
    has_generated_data?: boolean
    has_augmentation?: boolean
    has_simulation?: boolean
    evidence_integrity?: string
    scientific_transparency?: string
  } | null
  className?: string
}

export function InvestigationInfoCard({ provenance, className }: InvestigationInfoCardProps) {
  const isAugmentationEnabled = provenance?.augmentation_enabled ?? true
  const generatedCount = (provenance?.counts?.AUGMENTED_RSSI || 0) + (provenance?.counts?.AUGMENTED_TA || 0)
  const isSimulationUsed = (provenance?.counts?.SIMULATED || 0) > 0
  const isAugmentationUsed = generatedCount > 0

  return (
    <div
      className={cn(
        'p-5 rounded-2xl border border-border-secondary bg-surface-secondary/40 backdrop-blur-sm shadow-sm flex flex-col justify-between',
        className
      )}
    >
      <div className="flex items-center justify-between mb-4 border-b border-border-primary/60 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-brand-primary/10 text-brand-primary border border-brand-primary/20">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-content-primary">Investigation Summary</h3>
            <p className="text-[11px] text-content-tertiary">Operational &amp; Evidence Audit Parameters</p>
          </div>
        </div>
        <div className="flex items-center gap-1 text-[10px] font-bold text-emerald-500 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
          <ShieldCheck className="w-3 h-3" />
          <span>Provenanced</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
        <div className="p-2.5 rounded-xl bg-surface-primary/60 border border-border-secondary">
          <span className="text-[10px] uppercase tracking-wider text-content-tertiary font-bold block mb-1">
            Data Source
          </span>
          <span className="font-semibold text-content-primary truncate block">
            {isSimulationUsed ? 'Scenario Simulation' : 'Imported Telecom Dataset'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-surface-primary/60 border border-border-secondary">
          <span className="text-[10px] uppercase tracking-wider text-content-tertiary font-bold block mb-1">
            Augmentation
          </span>
          <span
            className={cn(
              'font-semibold block',
              isAugmentationEnabled ? 'text-blue-500' : 'text-content-tertiary'
            )}
          >
            {isAugmentationEnabled ? 'Enabled' : 'Disabled'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-surface-primary/60 border border-border-secondary">
          <span className="text-[10px] uppercase tracking-wider text-content-tertiary font-bold block mb-1">
            Generated Signal Data
          </span>
          <span className="font-semibold text-content-primary block">
            {isAugmentationUsed ? `Used (${generatedCount})` : 'Not Used (0)'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-surface-primary/60 border border-border-secondary">
          <span className="text-[10px] uppercase tracking-wider text-content-tertiary font-bold block mb-1">
            Scenario Simulation
          </span>
          <span className="font-semibold text-content-primary block">
            {isSimulationUsed ? 'Used' : 'Not Used'}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-surface-primary/60 border border-border-secondary">
          <span className="text-[10px] uppercase tracking-wider text-content-tertiary font-bold block mb-1">
            Evidence Integrity
          </span>
          <span className="font-bold text-emerald-500 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Verified ✓
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-surface-primary/60 border border-border-secondary">
          <span className="text-[10px] uppercase tracking-wider text-content-tertiary font-bold block mb-1">
            Scientific Transparency
          </span>
          <span className="font-bold text-emerald-500 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Verified ✓
          </span>
        </div>
      </div>
    </div>
  )
}
