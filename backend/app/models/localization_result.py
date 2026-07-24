from typing import TYPE_CHECKING, Optional

from app.models.base import BaseModel
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.scenario import Scenario


class LocalizationResult(BaseModel):
    """Stores the output of a localization algorithm run against a Case."""

    __tablename__ = "localization_results"

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True
    )
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False)
    estimated_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    error_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    computation_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    signals_used: Mapped[int] = mapped_column(Integer, nullable=False)

    case: Mapped["Case"] = relationship("Case", back_populates="localization_results")
    scenario: Mapped[Optional["Scenario"]] = relationship("Scenario")
