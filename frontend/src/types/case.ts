export type CaseStatus = 'open' | 'in_progress' | 'closed' | 'archived';

/**
 * Matches the backend CaseResponse Pydantic schema exactly.
 * Backend fields: id (int), title, description, status, scenario_id,
 * created_at, updated_at (snake_case datetimes).
 */
export interface Case {
  id: number;
  title: string;
  description?: string | null;
  status: string;
  scenario_id?: number | null;
  created_at: string;
  updated_at: string;
}

export interface CreateCaseDTO {
  title: string;
  description?: string;
  status?: CaseStatus;
  scenario_id?: number | null;
}

export interface UpdateCaseDTO extends Partial<CreateCaseDTO> {}
