from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ScenarioBase(BaseModel):
    name: str
    description: str | None = None


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioResponse(ScenarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
