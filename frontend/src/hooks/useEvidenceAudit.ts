import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface EvidenceAuditResponse {
  case_code: string
  reproducibility_hash: string
  solver_version: string
  input_record_ids: string[]
  parameter_strings: string
  summary: any
  towers: any[]
  rejections: any[]
  confidence: any
  audit_status: string
  generated_at: string
}

export function useEvidenceAudit(caseId: number | string | undefined) {
  return useQuery({
    queryKey: ['evidence-audit', caseId],
    queryFn: async () => {
      if (!caseId) return null
      const response = await api.get<{ success: boolean; data: EvidenceAuditResponse }>(`/evidence/${caseId}/audit`)
      return response.data as unknown as EvidenceAuditResponse;
    },
    enabled: !!caseId,
    retry: false,
  })
}
