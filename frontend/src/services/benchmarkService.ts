import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8222/api/v1'

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
    const response = await axios.get(`${API_URL}/validation/benchmark/${caseId}`)
    return response.data
  }
}

export const benchmarkService = new BenchmarkService()
