from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CaseBase(BaseModel):
    title: str
    description: str | None = None
    status: str = "open"
    scenario_id: int | None = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    scenario_id: int | None = None
    status: str | None = None


class CaseResponse(CaseBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
