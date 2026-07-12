import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type Theme = 'dark' | 'light'

interface ThemeState {
  theme: Theme
  toggleTheme: () => void
  setTheme: (theme: Theme) => void
}

/**
 * Theme store with localStorage persistence.
 * Applies the theme class to <html> so Tailwind dark-mode and
 * CSS custom properties respond globally.
 */
function applyThemeToDOM(theme: Theme) {
  const root = document.documentElement
  root.classList.remove('dark', 'light')
  root.classList.add(theme)
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'dark',
      toggleTheme: () =>
        set((state) => {
          const next: Theme = state.theme === 'dark' ? 'light' : 'dark'
          applyThemeToDOM(next)
          return { theme: next }
        }),
      setTheme: (theme: Theme) => {
        applyThemeToDOM(theme)
        set({ theme })
      },
    }),
    {
      name: 'asterion-theme',
      onRehydrateStorage: () => (state) => {
        if (state) {
          applyThemeToDOM(state.theme)
        }
      },
    },
  ),
)
