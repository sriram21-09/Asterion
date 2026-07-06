import { Layers, Plus } from 'lucide-react'

export default function Scenarios() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Scenarios Configurator</h1>
          <p className="text-sm text-slate-400 mt-1">Configure layout, transmitters, bounds, and signal paths.</p>
        </div>
        <button 
          disabled
          className="inline-flex items-center space-x-2 px-4 py-2.5 bg-indigo-600/50 text-indigo-300 border border-indigo-500/20 rounded-xl text-sm font-semibold cursor-not-allowed"
        >
          <Plus className="h-4 w-4" />
          <span>Add Scenario</span>
        </button>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 space-y-4">
        <div className="h-16 w-16 bg-slate-800/80 border border-slate-700 rounded-2xl flex items-center justify-center mx-auto">
          <Layers className="h-8 w-8 text-indigo-400" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-slate-200">No scenarios configured</h3>
          <p className="text-sm text-slate-400 max-w-sm mx-auto leading-relaxed">
            Scenario creation forms, validation configurations, and mapping models are scheduled to be implemented during Day 4 of the Foundation Sprint.
          </p>
        </div>
      </div>
    </div>
  )
}
