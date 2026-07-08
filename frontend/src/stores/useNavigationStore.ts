import { create } from 'zustand'

interface NavigationState {
  sidebarOpen: boolean
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
}

/**
 * Navigation store for global sidebar state.
 * Replaces local useState in DashboardLayout so that both the
 * header hamburger button and the sidebar overlay can control
 * the same open/close state.
 */
export const useNavigationStore = create<NavigationState>()((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
}))
