from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CaseBase(BaseModel):
    title: str
    description: str | None = None
    status: str = "active"

class CaseCreate(CaseBase):
    pass

class CaseResponse(CaseBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
