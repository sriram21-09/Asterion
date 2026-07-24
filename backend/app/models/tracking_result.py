from typing import TYPE_CHECKING, Optional

from app.models.base import BaseModel
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.localization_result import LocalizationResult


class TrackingResult(BaseModel):
    """Stores a single step in a Kalman-smoothed tracking path for a Case."""

    __tablename__ = "tracking_results"

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    localization_result_id: Mapped[int | None] = mapped_column(
        ForeignKey("localization_results.id", ondelete="SET NULL"), nullable=True
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    smoothed_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    smoothed_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    velocity_lat: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    velocity_lon: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    velocity_mps: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    computation_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    algorithm: Mapped[str] = mapped_column(String(50), nullable=False, default="kalman")
    timestamp: Mapped[str | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    case: Mapped["Case"] = relationship("Case", back_populates="tracking_results")
    localization_result: Mapped[Optional["LocalizationResult"]] = relationship(
        "LocalizationResult"
    )
