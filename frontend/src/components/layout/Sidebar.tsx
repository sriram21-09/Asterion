import { Link, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Briefcase,
  Settings,
  FileText,
  Layers,
  Radio,
  User,
  X,
} from 'lucide-react'
import { cn } from '@/lib/cn'
import { useNavigationStore } from '@/stores/useNavigationStore'

interface NavItem {
  name: string
  path: string
  icon: React.ComponentType<{ className?: string }>
}

const navigation: NavItem[] = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Cases', path: '/cases', icon: Briefcase },
  { name: 'Scenarios', path: '/scenarios', icon: Layers },
  { name: 'Reports', path: '/reports', icon: FileText },
  { name: 'Settings', path: '/settings', icon: Settings },
]

export default function Sidebar() {
  const location = useLocation()
  const { sidebarOpen, setSidebarOpen } = useNavigationStore()

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/'
    return location.pathname.startsWith(path)
  }

  return (
    <>
      {/* Mobile Overlay — fades in/out */}
      <div
        className={cn(
          'fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden',
          'transition-opacity duration-300',
          sidebarOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none',
        )}
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar Panel */}
      <aside
        id="sidebar-nav"
        aria-label="Primary navigation"
        className={cn(
          // Layout
          'fixed inset-y-0 left-0 w-64 flex flex-col z-40',
          // Appearance
          'bg-surface-primary border-r border-border-primary',
          // GPU-accelerated slide — uses will-change for smooth animation
          'will-change-transform transform transition-transform duration-300 ease-in-out',
          // Desktop: always visible, no translate
          'md:relative md:translate-x-0 md:z-auto md:will-change-auto',
          // Mobile: slide in/out
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Branding */}
        <div className="h-16 flex items-center px-6 border-b border-border-primary space-x-3 shrink-0">
          <Radio className="h-7 w-7 text-brand-primary animate-pulse" />
          <span className="text-2xl font-black tracking-wider text-content-primary">
            ASTERION
          </span>
        </div>

        {/* Navigation Links */}
        <nav className="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const active = isActive(item.path)
            const Icon = item.icon
            return (
              <Link
                key={item.name}
                to={item.path}
                id={`nav-${item.name.toLowerCase()}`}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  'relative flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium',
                  'transition-all duration-200 group overflow-hidden',
                  active
                    ? 'bg-brand-primary/15 text-brand-primary'
                    : 'text-content-tertiary hover:bg-surface-secondary hover:text-content-primary',
                )}
              >
                {/* Active left accent bar */}
                {active && (
                  <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-r-full bg-brand-primary" />
                )}

                <Icon
                  className={cn(
                    'h-5 w-5 shrink-0 transition-transform duration-200 group-hover:scale-110',
                    active
                      ? 'text-brand-primary'
                      : 'text-content-tertiary group-hover:text-brand-secondary',
                  )}
                />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>

        {/* Mobile Close Button */}
        <button
          onClick={() => setSidebarOpen(false)}
          className="absolute top-4 right-4 md:hidden p-1.5 text-content-tertiary hover:text-content-primary hover:bg-surface-secondary rounded-lg transition-colors"
          aria-label="Close sidebar"
        >
          <X className="h-4 w-4" />
        </button>

        {/* User Profile Footer */}
        <div className="p-3 border-t border-border-primary shrink-0">
          <div className="flex items-center space-x-3 px-3 py-2.5 rounded-xl hover:bg-surface-secondary transition-colors cursor-pointer group">
            <div className="h-9 w-9 rounded-full bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center shrink-0">
              <User className="h-4 w-4 text-brand-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-content-secondary truncate group-hover:text-content-primary transition-colors">
                Researcher Mode
              </p>
              <p className="text-xs text-content-tertiary truncate">
                Asterion Platform
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
