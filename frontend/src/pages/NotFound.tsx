import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { LayoutDashboard, Briefcase, Layers, Radio, ArrowLeft } from 'lucide-react'

const quickLinks = [
  { label: 'Dashboard',  to: '/',          icon: LayoutDashboard },
  { label: 'Cases',      to: '/cases',     icon: Briefcase },
  { label: 'Scenarios',  to: '/scenarios', icon: Layers },
]

/**
 * Polished 404 page with animated glyph, brand gradient, and quick-nav links.
 */
export default function NotFound() {
  useEffect(() => {
    document.title = '404 — Page Not Found · Asterion'
  }, [])

  return (
    <div className="min-h-[80vh] flex flex-col items-center justify-center text-center px-6 py-16 animate-fade-in">
      {/* 404 glyph */}
      <div className="relative mb-8 select-none">
        {/* Background glow */}
        <div className="absolute inset-0 bg-brand-primary/10 blur-3xl rounded-full scale-150 pointer-events-none" />

        {/* Brand icon */}
        <div className="relative h-20 w-20 mx-auto rounded-3xl bg-surface-primary border border-border-primary flex items-center justify-center shadow-glow-brand mb-6">
          <Radio className="h-10 w-10 text-brand-primary" />
        </div>

        {/* Large 404 */}
        <p className="text-[8rem] font-black leading-none tracking-tighter text-content-primary opacity-10 select-none pointer-events-none">
          404
        </p>
      </div>

      {/* Copy */}
      <div className="space-y-3 max-w-sm mb-10">
        <h1 className="text-3xl font-extrabold text-content-primary tracking-tight">
          Signal Lost
        </h1>
        <p className="text-sm text-content-tertiary leading-relaxed">
          The page you're looking for doesn't exist, has been moved, or the
          coordinates are out of range.
        </p>
      </div>

      {/* Quick links */}
      <div className="flex flex-wrap items-center justify-center gap-3 mb-8">
        {quickLinks.map(({ label, to, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className="flex items-center gap-2 px-4 py-2.5 bg-surface-primary border border-border-primary rounded-xl text-sm font-semibold text-content-secondary hover:text-content-primary hover:border-border-secondary hover:bg-surface-secondary transition-all duration-200"
          >
            <Icon className="h-4 w-4 text-brand-primary" />
            {label}
          </Link>
        ))}
      </div>

      {/* Back link */}
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-sm text-content-tertiary hover:text-brand-primary transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Return to Dashboard
      </Link>
    </div>
  )
}
