import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8222/api/v1'

export interface ReportPreviewData {
  metadata?: {
    case_id: string
    case_title?: string
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
    const resData = response.data?.data
    return resData?.preview || resData || {}
  }

  /**
   * Fetches preview metrics for a case without generating PDF
   */
  async getReportPreview(caseId: number, reportType: string = 'full'): Promise<ReportPreviewData> {
    const response = await axios.get(`${API_URL}/reports/${caseId}/preview`, {
      params: { report_type: reportType }
    })
    return response.data?.data || {}
  }

  /**
   * Downloads raw CSV export for a case (or all cases if omitted)
   */
  async exportCsv(caseId?: number): Promise<Blob> {
    const url = caseId ? `${API_URL}/reports/${caseId}/export-csv` : `${API_URL}/reports/export-csv`
    const response = await axios.get(url, {
      responseType: 'blob'
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

