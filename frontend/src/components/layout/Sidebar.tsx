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
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden transition-opacity duration-300"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar Panel */}
      <aside
        id="sidebar-nav"
        className={cn(
          'fixed inset-y-0 left-0 w-64 bg-surface-primary border-r border-border-primary flex flex-col z-40',
          'transform transition-transform duration-300 ease-in-out',
          'md:relative md:translate-x-0 md:z-auto',
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
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
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
                  'flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 group',
                  active
                    ? 'bg-brand-primary text-white shadow-lg shadow-brand-primary/20'
                    : 'text-content-tertiary hover:bg-surface-secondary hover:text-content-primary',
                )}
              >
                <Icon
                  className={cn(
                    'h-5 w-5 transition-transform duration-200 group-hover:scale-110',
                    active
                      ? 'text-white'
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
          className="absolute top-4 right-4 md:hidden text-content-tertiary hover:text-content-primary transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* User Profile Footer */}
        <div className="p-4 border-t border-border-primary bg-surface-tertiary shrink-0">
          <div className="flex items-center space-x-3 px-4 py-3">
            <div className="h-9 w-9 rounded-full bg-surface-secondary flex items-center justify-center border border-border-secondary">
              <User className="h-5 w-5 text-content-tertiary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-content-secondary truncate">
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
