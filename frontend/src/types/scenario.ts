/**
 * Matches the backend ScenarioResponse Pydantic schema exactly.
 * Backend fields: id (int), name, description,
 * created_at, updated_at (snake_case datetimes).
 *
 * Note: Backend uses 'name' — frontend components should use scenario.name.
 */
export interface Scenario {
  id: number;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateScenarioDTO {
  name: string;
  description?: string;
}

export interface UpdateScenarioDTO extends Partial<CreateScenarioDTO> {}
