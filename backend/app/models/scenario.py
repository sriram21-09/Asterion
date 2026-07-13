from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.case import Case


class Scenario(BaseModel):
    __tablename__ = "scenarios"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    cases: Mapped[list["Case"]] = relationship("Case", back_populates="scenario")
