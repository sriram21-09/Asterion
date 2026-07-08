import { useEffect } from 'react'
import { Layers, Plus } from 'lucide-react'

export default function Scenarios() {
  useEffect(() => {
    document.title = 'Scenarios — Asterion'
  }, [])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border-primary pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-content-primary tracking-tight">
            Scenarios Configurator
          </h1>
          <p className="text-sm text-content-tertiary mt-1">
            Configure layout, transmitters, bounds, and signal paths.
          </p>
        </div>
        <button
          disabled
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-brand-primary/50 text-brand-secondary border border-brand-primary/20 rounded-xl text-sm font-semibold cursor-not-allowed"
        >
          <Plus className="h-4 w-4" />
          <span>Add Scenario</span>
        </button>
      </div>

      <div className="bg-surface-primary border border-border-primary rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 space-y-4">
        <div className="h-16 w-16 bg-surface-secondary border border-border-secondary rounded-2xl flex items-center justify-center mx-auto">
          <Layers className="h-8 w-8 text-brand-secondary" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-content-secondary">
            No scenarios configured
          </h3>
          <p className="text-sm text-content-tertiary max-w-sm mx-auto leading-relaxed">
            Scenario creation forms, validation configurations, and mapping
            models are scheduled to be implemented during Day 4 of the
            Foundation Sprint.
          </p>
        </div>
      </div>
    </div>
  )
}
