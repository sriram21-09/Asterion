import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8222/api/v1'

export interface ReportPreviewData {
  metadata?: {
    case_id: string
    generated_at: string
    report_type: string
    status: string
  }
  validation_summary?: {
    total_measurements: number
    rejected: number
    pass_rate: number
  }
  tower_report?: {
    towers_involved: number
    sector_coverage: number
  }
  movement?: {
    estimated_distance_km: number
    points_tracked: number
  }
  evidence?: {
    confidence_score: number
    algorithms_used: string[]
  }
}

class ReportService {
  /**
   * Generates a report and returns preview data for the sections
   */
  async generateReport(caseId: number, reportType: string = 'full'): Promise<ReportPreviewData> {
    const response = await axios.post(`${API_URL}/reports/${caseId}/generate`, null, {
      params: { report_type: reportType }
    })
    return response.data
  }

  /**
   * Downloads the generated PDF report
   */
  async downloadReport(caseId: number): Promise<Blob> {
    const response = await axios.get(`${API_URL}/reports/${caseId}/download`, {
      responseType: 'blob'
    })
    return response.data
  }
}

export const reportService = new ReportService()
