export type ScenarioStatus = 'draft' | 'active' | 'archived';

export interface Scenario {
  id: string;
  title: string;
  description?: string;
  environmentType: string;
  status: ScenarioStatus;
  createdAt: string;
  updatedAt: string;
}

export interface CreateScenarioDTO {
  title: string;
  description?: string;
  environmentType?: string;
  status?: ScenarioStatus;
}

export interface UpdateScenarioDTO extends Partial<CreateScenarioDTO> {}
