import { Briefcase, Layers, Radio, Eye } from 'lucide-react'

export default function Dashboard() {
  const incomingFeatures = [
    {
      title: 'Case Management',
      description: 'Create, edit, and organize telecom localization investigations. Link scenarios together to build structural evidence chains.',
      icon: Briefcase,
      timeline: 'Day 3 Release',
    },
    {
      title: 'Scenario Configurator',
      description: 'Define mock transmitter layouts, set up sector bounds, configure signal parameters, and define device movement paths.',
      icon: Layers,
      timeline: 'Day 4 Release',
    },
    {
      title: 'Scientific Simulation Engine',
      description: 'Generate synthetic RSSI measurement samples with adjustable noise values (Gaussian/multi-path fade) for tracking tests.',
      icon: Radio,
      timeline: 'Week 2 Core',
    },
    {
      title: 'Explainable Localization (NLLS)',
      description: 'Execute multilateration algorithms (Non-Linear Least Squares) and track devices using Kalman filters with full mathematical overlays.',
      icon: Eye,
      timeline: 'Week 2 Core',
    },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Hero section */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-3xl p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        
        <div className="relative z-10 max-w-2xl space-y-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            v0.1.0 Foundation Release
          </span>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Asterion Localization & Investigation Platform
          </h1>
          <p className="text-lg text-slate-400">
            An engineering and research workspace for simulating, evaluating, and visualizing RF-based device localization. Configure scenarios, test solvers, and investigate coordinates.
          </p>
        </div>
      </div>

      {/* Main Grid */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white tracking-wide">Platform Status & Capabilities</h2>
          <p className="text-sm text-slate-400 mt-1">Overview of components scheduled for the Week 1 sprint phases</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {incomingFeatures.map((feature, idx) => {
            const Icon = feature.icon
            return (
              <div 
                key={idx} 
                className="bg-slate-900 border border-slate-800 rounded-2xl p-6 transition-all duration-300 hover:border-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/5 group"
              >
                <div className="flex items-start justify-between">
                  <div className="h-12 w-12 rounded-xl bg-slate-800/80 border border-slate-700 flex items-center justify-center group-hover:border-indigo-500/20 group-hover:bg-indigo-950/20 transition-colors">
                    <Icon className="h-6 w-6 text-indigo-400 group-hover:text-indigo-300" />
                  </div>
                  <span className="text-xs font-medium px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700/50 text-slate-400">
                    {feature.timeline}
                  </span>
                </div>
                <div className="mt-5 space-y-2">
                  <h3 className="text-lg font-bold text-slate-200 group-hover:text-white transition-colors">{feature.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{feature.description}</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
