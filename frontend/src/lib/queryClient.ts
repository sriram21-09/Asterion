import { QueryClient } from '@tanstack/react-query'
import axios from 'axios'

/**
 * Determines if a query error is a network/server error (5xx) worth retrying,
 * or a client error (4xx) that should fail immediately.
 */
function shouldRetry(failureCount: number, error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status
    // Don't retry client errors (4xx) — they won't resolve on their own
    if (status && status >= 400 && status < 500) return false
    // Retry server/network errors up to 2 times
    return failureCount < 2
  }
  return failureCount < 1
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: shouldRetry,
      // Stale after 30 seconds — keeps dashboard data fresh
      staleTime: 30_000,
    },
    mutations: {
      retry: false,
    },
  },
})
