import { Outlet } from 'react-router-dom'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'

/**
 * Root layout shell for the Asterion dashboard.
 * Composes the Sidebar, Header, and Content Area into a
 * responsive flex layout with nested route rendering via <Outlet />.
 */
export default function DashboardLayout() {
  return (
    <div className="min-h-screen bg-surface-base text-content-primary flex flex-col md:flex-row font-sans">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Column */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Header Bar */}
        <Header />

        {/* Page Content */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto bg-surface-base">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
