import { api } from '@/lib/api'

export interface ReportPreviewData {
  metadata?: {
    report_id?: string
    case_id: string
    case_title?: string
    generated_at: string
    report_type: string
    status: string
    crs?: string
    primary_operator?: string
  }
  data_quality?: {
    dataset_completeness: string
    measurement_completeness: string
    tower_coverage: string
    localization_confidence: string
    scientific_integrity: string
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
    evidence_hash?: string
    augmentation_status?: string
  }
  recommendations?: string[]
  evidence_declaration?: string
}

class ReportService {
  /**
   * Generates a report and returns preview data for the sections
   */
  async generateReport(caseId: number, reportType: string = 'full'): Promise<ReportPreviewData> {
    const response = await api.post(`/reports/${caseId}/generate`, null, {
      params: { report_type: reportType }
    })
    const resData = response.data
    return resData?.preview || resData || {}
  }

  /**
   * Fetches preview metrics for a case without generating PDF
   */
  async getReportPreview(caseId: number, reportType: string = 'full'): Promise<ReportPreviewData> {
    const response = await api.get(`/reports/${caseId}/preview`, {
      params: { report_type: reportType }
    })
    return response.data || {}
  }

  /**
   * Downloads raw CSV export for a case (or all cases if omitted)
   */
  async exportCsv(caseId?: number): Promise<Blob> {
    const url = caseId ? `/reports/${caseId}/export-csv` : `/reports/export-csv`
    const response = await api.get(url, {
      responseType: 'blob'
    })
    return response.data
  }

  /**
   * Downloads the generated PDF report
   */
  async downloadReport(caseId: number): Promise<Blob> {
    const response = await api.get(`/reports/${caseId}/download`, {
      responseType: 'blob'
    })
    return response.data
  }
}

export const reportService = new ReportService()
