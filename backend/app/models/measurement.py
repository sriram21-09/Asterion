from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.models.base import BaseModel
from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.scenario import Scenario


class Measurement(BaseModel):
    __tablename__ = "measurements"

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=True
    )
    measurement_code: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rssi_dbm: Mapped[float] = mapped_column(Float, nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    timing_advance: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="measurements")
    scenario: Mapped[Optional["Scenario"]] = relationship(
        "Scenario", back_populates="measurements"
    )
