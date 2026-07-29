import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await api.get('/health')
      return response.data
    },
    refetchInterval: 10000, // Poll every 10 seconds
    retry: false,
  })
}
