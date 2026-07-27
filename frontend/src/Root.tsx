import { useThemeStore } from '@/stores/useThemeStore'
import { Toaster } from 'sonner'
import App from './App.tsx'

export function Root() {
  // Subscribe to theme so Sonner toasts match the active theme
  const { theme } = useThemeStore()

  return (
    <>
      <App />
      <Toaster
        position="top-right"
        richColors
        theme={theme}
        closeButton
        duration={4000}
        toastOptions={{
          classNames: {
            toast: 'font-sans text-sm',
          },
        }}
      />
    </>
  )
}
