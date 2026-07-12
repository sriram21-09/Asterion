import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { Toaster } from 'sonner'
import { useThemeStore } from '@/stores/useThemeStore'
import App from './App.tsx'
import './index.css'

function Root() {
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

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <Root />
    </QueryClientProvider>
  </StrictMode>,
)
