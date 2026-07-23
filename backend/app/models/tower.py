from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class Tower(BaseModel):
    __tablename__ = "towers"

    tower_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cgi: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    mcc: Mapped[str | None] = mapped_column(String(10), index=True, nullable=True)
    mnc: Mapped[str | None] = mapped_column(String(10), index=True, nullable=True)
    lac: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    ci: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    operator: Mapped[str | None] = mapped_column(String(50), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    confidence_category: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Known"
    )
    resolution_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
