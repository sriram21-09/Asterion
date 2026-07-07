import { useEffect } from 'react'
import { Briefcase, Layers, Radio, Eye, TrendingUp, Activity, MapPin } from 'lucide-react'

const incomingFeatures = [
  {
    title: 'Case Management',
    description:
      'Create, edit, and organize telecom localization investigations. Link scenarios together to build structural evidence chains.',
    icon: Briefcase,
    timeline: 'Day 3 Release',
  },
  {
    title: 'Scenario Configurator',
    description:
      'Define mock transmitter layouts, set up sector bounds, configure signal parameters, and define device movement paths.',
    icon: Layers,
    timeline: 'Day 4 Release',
  },
  {
    title: 'Scientific Simulation Engine',
    description:
      'Generate synthetic RSSI measurement samples with adjustable noise values (Gaussian/multi-path fade) for tracking tests.',
    icon: Radio,
    timeline: 'Week 2 Core',
  },
  {
    title: 'Explainable Localization (NLLS)',
    description:
      'Execute multilateration algorithms (Non-Linear Least Squares) and track devices using Kalman filters with full mathematical overlays.',
    icon: Eye,
    timeline: 'Week 2 Core',
  },
]

const quickStats = [
  { label: 'Active Cases', value: '0', icon: Briefcase, color: 'text-brand-secondary' },
  { label: 'Scenarios', value: '0', icon: Layers, color: 'text-emerald-400' },
  { label: 'Localizations', value: '—', icon: MapPin, color: 'text-amber-400' },
  { label: 'System', value: 'Online', icon: Activity, color: 'text-emerald-400' },
]

export default function Dashboard() {
  useEffect(() => {
    document.title = 'Dashboard — Asterion'
  }, [])

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero section */}
      <div className="bg-gradient-to-r from-surface-primary via-brand-muted to-surface-primary border border-border-primary rounded-3xl p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-brand-primary/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-2xl space-y-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-brand-muted text-brand-secondary border border-brand-primary/20">
            v0.1.0 Foundation Release
          </span>
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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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

      {/* Feature Cards Grid */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-bold text-content-primary tracking-wide flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-brand-secondary" />
            <span>Platform Status & Capabilities</span>
          </h2>
          <p className="text-sm text-content-tertiary mt-1">
            Overview of components scheduled for the Week 1 sprint phases
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {incomingFeatures.map((feature, idx) => {
            const Icon = feature.icon
            return (
              <div
                key={idx}
                className="bg-surface-primary border border-border-primary rounded-2xl p-6 transition-all duration-300 hover:border-brand-primary/30 hover:shadow-xl hover:shadow-brand-primary/5 group"
              >
                <div className="flex items-start justify-between">
                  <div className="h-12 w-12 rounded-xl bg-surface-secondary border border-border-secondary flex items-center justify-center group-hover:border-brand-primary/20 group-hover:bg-brand-muted transition-colors">
                    <Icon className="h-6 w-6 text-brand-secondary group-hover:text-brand-primary" />
                  </div>
                  <span className="text-xs font-medium px-2.5 py-1 rounded-lg bg-surface-secondary border border-border-secondary text-content-tertiary">
                    {feature.timeline}
                  </span>
                </div>
                <div className="mt-5 space-y-2">
                  <h3 className="text-lg font-bold text-content-secondary group-hover:text-content-primary transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-content-tertiary leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
