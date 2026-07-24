from typing import TYPE_CHECKING, Optional

from app.models.base import BaseModel
from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.localization_result import LocalizationResult


class ConfidenceResult(BaseModel):
    """Stores the output of a confidence analysis run for a Case."""

    __tablename__ = "confidence_results"

    case_id: Mapped[int] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
    )
    localization_result_id: Mapped[int | None] = mapped_column(
        ForeignKey("localization_results.id", ondelete="SET NULL"), nullable=True
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="low"
    )
    error_ellipse_semi_major_m: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    error_ellipse_semi_minor_m: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    error_ellipse_orientation_deg: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )
    gdop: Mapped[float | None] = mapped_column(Float, nullable=True)
    method: Mapped[str] = mapped_column(String(50), nullable=False, default="gdop")

    case: Mapped["Case"] = relationship("Case", back_populates="confidence_results")
    localization_result: Mapped[Optional["LocalizationResult"]] = relationship(
        "LocalizationResult"
    )
