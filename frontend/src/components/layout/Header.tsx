import { useLocation } from 'react-router-dom'
import { Menu, Sun, Moon, User } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useNavigationStore } from '@/stores/useNavigationStore'
import { useThemeStore } from '@/stores/useThemeStore'

/** Map route paths to human-readable breadcrumb labels */
const routeLabels: Record<string, string> = {
  '/': 'Dashboard',
  '/cases': 'Cases',
  '/scenarios': 'Scenarios',
  '/reports': 'Reports',
  '/settings': 'Settings',
}

export default function Header() {
  const location = useLocation()
  const { toggleSidebar } = useNavigationStore()
  const { theme, toggleTheme } = useThemeStore()

  const currentLabel = routeLabels[location.pathname] ?? 'Page'
  const isDark = theme === 'dark'

  return (
    <header
      id="app-header"
      className="h-16 bg-surface-primary border-b border-border-primary flex items-center justify-between px-4 md:px-8 z-10 shrink-0"
    >
      {/* Left: Mobile hamburger + Breadcrumb */}
      <div className="flex items-center space-x-4">
        {/* Mobile hamburger */}
        <button
          id="sidebar-toggle"
          onClick={toggleSidebar}
          className="md:hidden p-2 -ml-1 text-content-tertiary hover:text-content-primary hover:bg-surface-secondary rounded-lg transition-colors"
          aria-label="Toggle sidebar"
          aria-expanded={false}
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Breadcrumb */}
        <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-sm">
          <span className="text-content-tertiary hidden sm:inline">Asterion</span>
          <span className="text-content-tertiary hidden sm:inline">/</span>
          <span className="text-content-primary font-semibold">{currentLabel}</span>
        </nav>
      </div>

      {/* Right: Theme toggle + Status + Profile */}
      <div className="flex items-center space-x-3 md:space-x-4">
        {/* Theme Toggle — icon rotates smoothly on switch */}
        <button
          id="theme-toggle"
          onClick={toggleTheme}
          className={cn(
            'relative h-9 w-9 rounded-xl flex items-center justify-center',
            'bg-surface-secondary border border-border-secondary',
            'hover:border-brand-primary/50 hover:text-brand-primary',
            'text-content-tertiary transition-all duration-200',
          )}
          aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
          title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
        >
          <span
            className={cn(
              'absolute inset-0 flex items-center justify-center transition-all duration-300',
              isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 rotate-90 scale-75',
            )}
          >
            <Sun className="h-4 w-4" />
          </span>
          <span
            className={cn(
              'absolute inset-0 flex items-center justify-center transition-all duration-300',
              !isDark ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 -rotate-90 scale-75',
            )}
          >
            <Moon className="h-4 w-4" />
          </span>
        </button>

        {/* System Status */}
        <div className="hidden md:flex items-center space-x-2">
          <div className="h-2 w-2 rounded-full bg-success animate-pulse" />
          <span className="text-xs text-content-tertiary font-semibold tracking-wider uppercase">
            Online
          </span>
        </div>

        {/* Divider */}
        <div className="hidden md:block h-6 w-px bg-border-primary" />

        {/* User Avatar */}
        <button
          id="user-profile-btn"
          className={cn(
            'h-9 w-9 rounded-full flex items-center justify-center transition-all duration-200',
            'bg-brand-primary/10 border border-brand-primary/20',
            'hover:border-brand-primary/50 hover:shadow-md hover:shadow-brand-primary/10',
          )}
          aria-label="User profile"
        >
          <User className="h-4 w-4 text-brand-primary" />
        </button>
      </div>
    </header>
  )
}
