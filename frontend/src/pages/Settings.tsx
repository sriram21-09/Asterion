import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Save, Monitor, Map, Link2, Moon, Sun } from 'lucide-react'
import { useAppSettingsStore } from '@/stores/useAppSettingsStore'
import { useThemeStore } from '@/stores/useThemeStore'
import { toast } from 'sonner'
import { Button } from '@/components/ui'
import { cn } from '@/lib/cn'

export default function Settings() {
  const {
    apiBaseUrl,
    mapTileProvider,
    defaultMapCenter,
    defaultMapZoom,
    setApiBaseUrl,
    setMapTileProvider,
    setDefaultMapCenter,
    setDefaultMapZoom,
  } = useAppSettingsStore()

  const { theme, setTheme } = useThemeStore()

  // Local state for form edits before saving
  const [formApiUrl, setFormApiUrl] = useState(apiBaseUrl)
  const [formLat, setFormLat] = useState(defaultMapCenter[0].toString())
  const [formLng, setFormLng] = useState(defaultMapCenter[1].toString())
  const [formZoom, setFormZoom] = useState(defaultMapZoom.toString())
  const [formTileProvider, setFormTileProvider] = useState(mapTileProvider)

  useEffect(() => {
    document.title = 'Settings — Asterion'
  }, [])

  const handleSaveMapSettings = () => {
    const lat = parseFloat(formLat)
    const lng = parseFloat(formLng)
    const zoom = parseInt(formZoom, 10)

    if (isNaN(lat) || isNaN(lng)) {
      toast.error('Invalid latitude or longitude.')
      return
    }
    if (isNaN(zoom) || zoom < 1 || zoom > 19) {
      toast.error('Zoom must be between 1 and 19.')
      return
    }

    setDefaultMapCenter([lat, lng])
    setDefaultMapZoom(zoom)
    setMapTileProvider(formTileProvider as any)
    toast.success('Map settings saved.')
  }

  const handleSaveSystemSettings = () => {
    if (!formApiUrl) {
      toast.error('API URL cannot be empty.')
      return
    }
    setApiBaseUrl(formApiUrl)
    toast.success('System settings saved.')
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      <div className="border-b border-border-primary pb-5">
        <h1 className="text-3xl font-extrabold text-content-primary tracking-tight flex items-center space-x-3">
          <SettingsIcon className="h-8 w-8 text-brand-secondary" />
          <span>System Settings</span>
        </h1>
        <p className="text-sm text-content-tertiary mt-2">
          Configure workspace defaults, API endpoints, and map styling preferences.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Appearance Settings */}
        <section className="bg-surface-primary border border-border-primary rounded-2xl p-6 md:p-8 space-y-6">
          <div className="flex items-center space-x-3 border-b border-border-primary pb-4">
            <div className="p-2 bg-brand-primary/10 rounded-xl">
              <Monitor className="h-5 w-5 text-brand-primary" />
            </div>
            <h2 className="text-xl font-bold text-content-primary">Appearance</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-content-secondary mb-3">
                Workspace Theme
              </label>
              <div className="flex gap-4">
                <button
                  onClick={() => setTheme('dark')}
                  className={cn(
                    'flex-1 flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all',
                    theme === 'dark' 
                      ? 'border-brand-primary bg-brand-primary/5 text-brand-primary' 
                      : 'border-border-secondary bg-surface-secondary text-content-tertiary hover:border-border-primary'
                  )}
                >
                  <Moon className="h-6 w-6 mb-2" />
                  <span className="font-semibold text-sm">Dark Mode</span>
                </button>
                <button
                  onClick={() => setTheme('light')}
                  className={cn(
                    'flex-1 flex flex-col items-center justify-center p-4 rounded-xl border-2 transition-all',
                    theme === 'light' 
                      ? 'border-brand-primary bg-brand-primary/5 text-brand-primary' 
                      : 'border-border-secondary bg-surface-secondary text-content-tertiary hover:border-border-primary'
                  )}
                >
                  <Sun className="h-6 w-6 mb-2" />
                  <span className="font-semibold text-sm">Light Mode</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* System Settings */}
        <section className="bg-surface-primary border border-border-primary rounded-2xl p-6 md:p-8 space-y-6">
          <div className="flex items-center space-x-3 border-b border-border-primary pb-4">
            <div className="p-2 bg-indigo-500/10 rounded-xl">
              <Link2 className="h-5 w-5 text-indigo-500" />
            </div>
            <h2 className="text-xl font-bold text-content-primary">API Connectivity</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-content-secondary mb-1">
                Backend API Base URL
              </label>
              <p className="text-xs text-content-tertiary mb-3">
                The fully qualified URL to the FastAPI backend.
              </p>
              <input
                type="text"
                value={formApiUrl}
                onChange={(e) => setFormApiUrl(e.target.value)}
                className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-2.5 text-sm text-content-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-shadow"
                placeholder="http://localhost:8000"
              />
            </div>
            <div className="pt-2">
              <Button onClick={handleSaveSystemSettings}>
                <Save className="w-4 h-4 mr-2 inline" />
                Save Connection Settings
              </Button>
            </div>
          </div>
        </section>

        {/* Map Preferences */}
        <section className="bg-surface-primary border border-border-primary rounded-2xl p-6 md:p-8 space-y-6 lg:col-span-2">
          <div className="flex items-center space-x-3 border-b border-border-primary pb-4">
            <div className="p-2 bg-emerald-500/10 rounded-xl">
              <Map className="h-5 w-5 text-emerald-500" />
            </div>
            <h2 className="text-xl font-bold text-content-primary">Map Defaults</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-content-secondary mb-3">
                Tile Provider
              </label>
              <select
                value={formTileProvider}
                onChange={(e) => setFormTileProvider(e.target.value as any)}
                className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-2.5 text-sm text-content-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-shadow"
              >
                <option value="carto-dark">CARTO Dark Matter (Best for Dark Mode)</option>
                <option value="carto-light">CARTO Positron (Best for Light Mode)</option>
                <option value="osm">OpenStreetMap Standard</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-content-secondary mb-3">
                Default Zoom Level
              </label>
              <input
                type="number"
                min="1"
                max="19"
                value={formZoom}
                onChange={(e) => setFormZoom(e.target.value)}
                className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-2.5 text-sm text-content-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-shadow"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-content-secondary mb-3">
                Default Latitude
              </label>
              <input
                type="number"
                step="any"
                value={formLat}
                onChange={(e) => setFormLat(e.target.value)}
                className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-2.5 text-sm text-content-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-shadow"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-content-secondary mb-3">
                Default Longitude
              </label>
              <input
                type="number"
                step="any"
                value={formLng}
                onChange={(e) => setFormLng(e.target.value)}
                className="w-full bg-surface-secondary border border-border-primary rounded-xl px-4 py-2.5 text-sm text-content-primary focus:outline-none focus:ring-2 focus:ring-brand-primary/50 transition-shadow"
              />
            </div>
          </div>
          
          <div className="pt-4 border-t border-border-primary">
            <Button onClick={handleSaveMapSettings}>
              <Save className="w-4 h-4 mr-2 inline" />
              Save Map Preferences
            </Button>
          </div>
        </section>
      </div>
    </div>
  )
}
