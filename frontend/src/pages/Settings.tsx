import { useEffect, useState } from 'react'
import { Settings as SettingsIcon, Save, Monitor, Map, Link2, Moon, Sun, Database, Trash2, Sparkles, AlertTriangle, Loader2 } from 'lucide-react'
import { useAppSettingsStore } from '@/stores/useAppSettingsStore'
import { useThemeStore } from '@/stores/useThemeStore'
import { systemService } from '@/services/systemService'
import { toast } from 'sonner'
import { Button, ConfirmDialog } from '@/components/ui'
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

  // Database Management states
  const [isResetConfirmOpen, setIsResetConfirmOpen] = useState(false)
  const [isResetting, setIsResetting] = useState(false)
  const [isSeeding, setIsSeeding] = useState(false)

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

  const handleResetDatabase = async () => {
    try {
      setIsResetting(true)
      setIsResetConfirmOpen(false)
      const res = await systemService.resetDatabase()
      toast.success(res.message || 'Database cleanly purged.')
    } catch (err: any) {
      toast.error(err?.message || 'Failed to reset database.')
    } finally {
      setIsResetting(false)
    }
  }

  const handleSeedDatabase = async () => {
    try {
      setIsSeeding(true)
      const res = await systemService.seedDatabase()
      toast.success(res.message || 'Demonstration data seeded successfully!')
    } catch (err: any) {
      toast.error(err?.message || 'Failed to seed database.')
    } finally {
      setIsSeeding(false)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12">
      <div className="border-b border-border-primary pb-5">
        <h1 className="text-3xl font-extrabold text-content-primary tracking-tight flex items-center space-x-3">
          <SettingsIcon className="h-8 w-8 text-brand-secondary" />
          <span>System Settings</span>
        </h1>
        <p className="text-sm text-content-tertiary mt-2">
          Configure workspace defaults, API endpoints, map styling preferences, and database maintenance operations.
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
                placeholder="http://localhost:8222"
              />
            </div>
            <div className="pt-2">
              <Button onClick={handleSaveSystemSettings} leftIcon={<Save className="w-4 h-4" />}>
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
            <Button onClick={handleSaveMapSettings} leftIcon={<Save className="w-4 h-4" />}>
              Save Map Preferences
            </Button>
          </div>
        </section>

        {/* Database Management & Maintenance (Danger Zone / Admin Operations) */}
        <section className="bg-surface-primary border border-border-primary rounded-2xl p-6 md:p-8 space-y-6 lg:col-span-2">
          <div className="flex items-center space-x-3 border-b border-border-primary pb-4">
            <div className="p-2 bg-purple-500/10 rounded-xl">
              <Database className="h-5 w-5 text-purple-500" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-content-primary">Database Operations & Maintenance</h2>
              <p className="text-xs text-content-tertiary mt-0.5">
                Purge workspace state or seed default demonstration scenarios.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Feature 1: Clean Complete Database */}
            <div className="bg-red-500/5 border border-red-500/20 rounded-xl p-5 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center space-x-2 text-red-500 font-bold text-base mb-2">
                  <AlertTriangle className="w-5 h-5" />
                  <span>Clean Complete Database</span>
                </div>
                <p className="text-xs text-content-secondary leading-relaxed">
                  Permanently deletes all case records, imported CDR files, simulation measurements, NLLS localizations, and evidence logs.
                </p>
                <p className="text-[11px] text-content-tertiary mt-2 font-mono">
                  * Keeps all database tables, columns, indexes, and constraints 100% intact.
                </p>
              </div>

              <div>
                <button
                  onClick={() => setIsResetConfirmOpen(true)}
                  disabled={isResetting || isSeeding}
                  className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-red-600/20 disabled:opacity-50 cursor-pointer"
                >
                  {isResetting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4" />
                  )}
                  <span>{isResetting ? 'Purging Database...' : 'Clean Complete Database'}</span>
                </button>
              </div>
            </div>

            {/* Feature 2: Seed Demonstration Data */}
            <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-5 flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center space-x-2 text-indigo-500 font-bold text-base mb-2">
                  <Sparkles className="w-5 h-5" />
                  <span>Seed Demonstration Data</span>
                </div>
                <p className="text-xs text-content-secondary leading-relaxed">
                  Populates 2 default scenarios and 4 rich demonstration cases (`MG Road Search`, `Koramangala Tracking`, `VIP Escort`, `PhantomNet`) with full measurements, localization, and timeline tracks.
                </p>
                <p className="text-[11px] text-content-tertiary mt-2 font-mono">
                  * Perfect for demonstrating all Asterion features to stakeholders.
                </p>
              </div>

              <div>
                <button
                  onClick={handleSeedDatabase}
                  disabled={isResetting || isSeeding}
                  className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-indigo-600/20 disabled:opacity-50 cursor-pointer"
                >
                  {isSeeding ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Database className="w-4 h-4" />
                  )}
                  <span>{isSeeding ? 'Seeding Demo Data...' : 'Seed Demonstration Data'}</span>
                </button>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Safety Confirmation Dialog for Purging Database */}
      {isResetConfirmOpen && (
        <ConfirmDialog
          title="Clean Complete Database?"
          message="This action will permanently delete ALL cases, imported CDR records, localizations, and evidence trails in the system. Tables and database structure will remain intact. Are you sure you want to proceed?"
          confirmLabel="Yes, Purge Database"
          cancelLabel="Cancel"
          isDangerous={true}
          isLoading={isResetting}
          onConfirm={handleResetDatabase}
          onCancel={() => setIsResetConfirmOpen(false)}
        />
      )}
    </div>
  )
}
