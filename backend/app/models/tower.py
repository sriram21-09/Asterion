from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import BaseModel


class Tower(BaseModel):
    __tablename__ = "towers"

    tower_name: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
