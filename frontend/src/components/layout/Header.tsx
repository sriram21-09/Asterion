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
          className="md:hidden text-content-tertiary hover:text-content-primary transition-colors"
          aria-label="Toggle sidebar"
        >
          <Menu className="h-6 w-6" />
        </button>

        {/* Breadcrumb */}
        <div className="flex items-center space-x-2 text-sm">
          <span className="text-content-tertiary hidden sm:inline">
            Asterion
          </span>
          <span className="text-content-tertiary hidden sm:inline">/</span>
          <span className="text-content-primary font-semibold">
            {currentLabel}
          </span>
        </div>
      </div>

      {/* Right: Theme toggle + Status + Profile */}
      <div className="flex items-center space-x-3 md:space-x-5">
        {/* Theme Toggle */}
        <button
          id="theme-toggle"
          onClick={toggleTheme}
          className={cn(
            'relative h-9 w-9 rounded-xl flex items-center justify-center transition-all duration-200',
            'bg-surface-secondary border border-border-secondary',
            'hover:border-brand-secondary hover:text-brand-secondary',
            'text-content-tertiary',
          )}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </button>

        {/* System Status */}
        <div className="hidden md:flex items-center space-x-2">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-content-tertiary font-semibold tracking-wider uppercase">
            Connected
          </span>
        </div>

        {/* Divider */}
        <div className="hidden md:block h-6 w-px bg-border-primary" />

        {/* User Avatar */}
        <button
          id="user-profile-btn"
          className={cn(
            'h-9 w-9 rounded-full flex items-center justify-center transition-all duration-200',
            'bg-surface-secondary border border-border-secondary',
            'hover:border-brand-secondary hover:shadow-md hover:shadow-brand-primary/10',
          )}
          aria-label="User profile"
        >
          <User className="h-4 w-4 text-content-tertiary" />
        </button>
      </div>
    </header>
  )
}
