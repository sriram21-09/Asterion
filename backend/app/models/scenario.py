from typing import TYPE_CHECKING

from app.models.base import BaseModel
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.measurement import Measurement


class Scenario(BaseModel):
    __tablename__ = "scenarios"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    cases: Mapped[list["Case"]] = relationship("Case", back_populates="scenario")
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement", back_populates="scenario", cascade="all, delete-orphan"
    )
