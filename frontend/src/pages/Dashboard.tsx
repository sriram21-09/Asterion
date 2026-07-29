import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Briefcase, Layers, Eye, Activity } from 'lucide-react'
import { useCases } from '@/hooks/useCases'
import { useScenarios } from '@/hooks/useScenarios'
import { useHealthCheck } from '@/hooks/useHealthCheck'

export default function Dashboard() {
  const { data: cases } = useCases()
  const { data: scenarios } = useScenarios()
  const { isSuccess: isOnline } = useHealthCheck()

  useEffect(() => {
    document.title = 'Dashboard — Asterion'
  }, [])

  const quickStats = [
    { 
      label: 'Active Cases', 
      value: cases ? cases.filter(c => c.status !== 'closed' && c.status !== 'archived').length.toString() : '0', 
      icon: Briefcase, 
      color: 'text-brand-secondary' 
    },
    { 
      label: 'Scenarios', 
      value: scenarios ? scenarios.length.toString() : '0', 
      icon: Layers, 
      color: 'text-emerald-400' 
    },
    { label: 'System', value: isOnline ? 'Online' : 'Offline', icon: Activity, color: isOnline ? 'text-emerald-400' : 'text-red-500' },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero section */}
      <div className="bg-gradient-to-r from-surface-primary via-brand-muted to-surface-primary border border-border-primary rounded-3xl p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-brand-primary/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl space-y-4">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-content-primary leading-tight">
            Asterion Localization & Investigation Platform
          </h1>
          <p className="text-lg text-content-tertiary">
            An engineering and research workspace for simulating, evaluating,
            and visualizing RF-based device localization. Configure scenarios,
            test solvers, and investigate coordinates.
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {quickStats.map((stat) => {
          const Icon = stat.icon
          return (
            <div
              key={stat.label}
              className="bg-surface-primary border border-border-primary rounded-2xl p-5 flex items-center space-x-4 transition-all duration-200 hover:border-border-secondary hover:shadow-glow-brand"
            >
              <div className="h-10 w-10 rounded-xl bg-surface-secondary border border-border-secondary flex items-center justify-center shrink-0">
                <Icon className={`h-5 w-5 ${stat.color}`} />
              </div>
              <div>
                <p className="text-xs text-content-tertiary font-medium uppercase tracking-wide">
                  {stat.label}
                </p>
                <p className="text-xl font-bold text-content-primary mt-0.5">
                  {stat.value}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Active Investigations */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-content-primary tracking-wide">
              Active Investigations
            </h2>
            <p className="text-sm text-content-tertiary mt-1">
              Quick access to current tracking cases
            </p>
          </div>
          <Link
            to="/cases"
            className="text-sm font-semibold text-brand-primary hover:text-brand-secondary transition-colors"
          >
            View All Cases →
          </Link>
        </div>

        {cases && cases.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {cases.slice(0, 3).map((c) => (
              <div
                key={c.id}
                className="bg-surface-primary border border-border-primary rounded-2xl p-5 hover:border-brand-primary/50 transition-all shadow-sm flex flex-col justify-between"
              >
                <div>
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-xs font-semibold text-content-tertiary uppercase tracking-wider">
                      {c.referenceNumber || `CASE-${String(c.id).padStart(3, '0')}`}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold border bg-green-500/10 text-green-500 border-green-500/20 uppercase tracking-widest">
                      {c.status}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-content-primary line-clamp-1 mb-1">
                    {c.title}
                  </h3>
                  <p className="text-xs text-content-secondary line-clamp-2 mb-4">
                    {c.description || 'No description provided.'}
                  </p>
                </div>
                <div className="pt-3 border-t border-border-secondary flex items-center justify-between">
                  <span className="text-[10px] text-content-tertiary">
                    {new Date(c.created_at).toLocaleDateString()}
                  </span>
                  <Link
                    to={`/cases/${c.id}`}
                    className="inline-flex items-center text-xs font-semibold text-brand-primary hover:text-brand-secondary"
                  >
                    <Eye className="w-3.5 h-3.5 mr-1" />
                    <span>View Dashboard</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="bg-surface-primary border border-border-primary border-dashed rounded-2xl p-8 text-center text-content-tertiary">
            No active investigations found. Go to Cases page to create one.
          </div>
        )}
      </div>
    </div>
  )
}
