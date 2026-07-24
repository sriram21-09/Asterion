from typing import TYPE_CHECKING, Optional

from app.models.base import BaseModel
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.cdr_record import CDRRecord


class ImportJob(BaseModel):
    __tablename__ = "import_jobs"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    operator: Mapped[str] = mapped_column(String(50), default="unknown", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    parsed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    case_id: Mapped[int | None] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=True
    )
    case: Mapped[Optional["Case"]] = relationship("Case", backref="import_jobs")

    cdr_records: Mapped[list["CDRRecord"]] = relationship(
        "CDRRecord", back_populates="import_job", cascade="all, delete-orphan"
    )
