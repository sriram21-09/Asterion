import { useEffect, useRef } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import { useThemeStore } from '@/stores/useThemeStore'

/**
 * Root layout shell for the Asterion dashboard.
 * Applies theme-transition class briefly on mount so switching feels smooth,
 * then removes it to avoid paying the transition cost on every render.
 */
export default function DashboardLayout() {
  const { theme } = useThemeStore()
  const rootRef = useRef<HTMLDivElement>(null)

  // Temporarily enable transitions only when theme actually changes
  useEffect(() => {
    const el = rootRef.current
    if (!el) return
    el.classList.add('theme-transition')
    const id = setTimeout(() => el.classList.remove('theme-transition'), 400)
    return () => clearTimeout(id)
  }, [theme])

  return (
    <div
      ref={rootRef}
      className="min-h-screen bg-surface-base text-content-primary flex flex-col md:flex-row font-sans"
    >
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Column */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Header Bar */}
        <Header />

        {/* Page Content */}
        <main
          id="main-content"
          className="flex-1 p-6 md:p-8 overflow-y-auto bg-surface-base"
        >
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
