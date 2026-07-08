import { useEffect } from 'react'
import { Settings as SettingsIcon } from 'lucide-react'

export default function Settings() {
  useEffect(() => {
    document.title = 'Settings — Asterion'
  }, [])

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="border-b border-border-primary pb-5">
        <h1 className="text-3xl font-extrabold text-content-primary tracking-tight">
          System Settings
        </h1>
        <p className="text-sm text-content-tertiary mt-1">
          Configure workspace defaults, API endpoints, and map styling
          preferences.
        </p>
      </div>

      <div className="bg-surface-primary border border-border-primary rounded-2xl p-12 text-center max-w-2xl mx-auto my-12 space-y-4">
        <div className="h-16 w-16 bg-surface-secondary border border-border-secondary rounded-2xl flex items-center justify-center mx-auto">
          <SettingsIcon className="h-8 w-8 text-brand-secondary" />
        </div>
        <div className="space-y-2">
          <h3 className="text-xl font-bold text-content-secondary">
            Settings panel
          </h3>
          <p className="text-sm text-content-tertiary max-w-sm mx-auto leading-relaxed">
            Configure system configurations, map layouts, API URLs, and UI theme
            options here in future updates.
          </p>
        </div>
      </div>
    </div>
  )
}
