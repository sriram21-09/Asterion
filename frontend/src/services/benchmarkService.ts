import { api } from '@/lib/api'

export interface BenchmarkMetric {
  metric_name: string
  value: number
  threshold: number
  passed: boolean
}

export interface BenchmarkResponse {
  case_passed: boolean
  metrics: BenchmarkMetric[]
}

class BenchmarkService {
  async getBenchmark(caseId: number): Promise<BenchmarkResponse> {
    const response = await api.get(`/validation/benchmark/${caseId}`)
    return response.data
  }
}

export const benchmarkService = new BenchmarkService()
