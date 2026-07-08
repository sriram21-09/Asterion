export type CaseStatus = 'open' | 'in_progress' | 'closed' | 'archived';

export interface Case {
  id: string;
  referenceNumber: string;
  title: string;
  description?: string;
  status: CaseStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CreateCaseDTO {
  title: string;
  referenceNumber?: string;
  description?: string;
  status?: CaseStatus;
}

export interface UpdateCaseDTO extends Partial<CreateCaseDTO> {}
