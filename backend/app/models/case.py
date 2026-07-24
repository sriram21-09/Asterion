from typing import TYPE_CHECKING, Optional

from app.models.base import BaseModel
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.confidence_result import ConfidenceResult
    from app.models.localization_result import LocalizationResult
    from app.models.measurement import Measurement
    from app.models.movement_event import MovementEvent
    from app.models.scenario import Scenario
    from app.models.tracking_result import TrackingResult


class Case(BaseModel):
    __tablename__ = "cases"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)

    scenario_id: Mapped[int | None] = mapped_column(
        ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True
    )
    scenario: Mapped[Optional["Scenario"]] = relationship(
        "Scenario", back_populates="cases"
    )
    measurements: Mapped[list["Measurement"]] = relationship(
        "Measurement", back_populates="case", cascade="all, delete-orphan"
    )
    localization_results: Mapped[list["LocalizationResult"]] = relationship(
        "LocalizationResult", back_populates="case", cascade="all, delete-orphan"
    )
    tracking_results: Mapped[list["TrackingResult"]] = relationship(
        "TrackingResult", back_populates="case", cascade="all, delete-orphan"
    )
    confidence_results: Mapped[list["ConfidenceResult"]] = relationship(
        "ConfidenceResult", back_populates="case", cascade="all, delete-orphan"
    )
    movement_events: Mapped[list["MovementEvent"]] = relationship(
        "MovementEvent", back_populates="case", cascade="all, delete-orphan"
    )
