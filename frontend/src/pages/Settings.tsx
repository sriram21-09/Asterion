import { Settings as SettingsIcon } from 'lucide-react'

export default function Settings() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="border-b border-slate-800 pb-5">
        <h1 className="text-3xl font-extrabold text-white tracking-tight">System Settings</h1>
        <p className="text-sm text-slate-400 mt-1">Configure workspace defaults, API endpoints, and map styling preferences.</p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 space-y-4">
        <div className="h-16 w-16 bg-slate-800/80 border border-slate-700 rounded-2xl flex items-center justify-center mx-auto">
          <SettingsIcon className="h-8 w-8 text-indigo-400" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-slate-200">Settings panel</h3>
          <p className="text-sm text-slate-400 max-w-sm mx-auto leading-relaxed">
            Configure system configurations, map layouts, API URLs, and UI theme options here in future updates.
          </p>
        </div>
      </div>
    </div>
  )
}
