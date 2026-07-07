from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text
from app.models.base import BaseModel

class Case(BaseModel):
    __tablename__ = "cases"
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
