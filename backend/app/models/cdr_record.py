from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from app.models.base import BaseModel
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.import_job import ImportJob


class CDRRecord(BaseModel):
    __tablename__ = "cdr_records"

    import_job_id: Mapped[int] = mapped_column(
        ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[int | None] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True
    )

    operator: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    b_party_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    call_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    service_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    duration: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    first_cgi: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    first_bts_location: Mapped[str | None] = mapped_column(Text, nullable=True)

    last_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_cgi: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    last_bts_location: Mapped[str | None] = mapped_column(Text, nullable=True)

    imei: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    imsi: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    smsc_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    roaming_network: Mapped[str | None] = mapped_column(String(100), nullable=True)

    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    import_job: Mapped["ImportJob"] = relationship(
        "ImportJob", back_populates="cdr_records"
    )
    case: Mapped[Optional["Case"]] = relationship("Case", backref="cdr_records")

    __table_args__ = (
        Index("ix_cdr_records_case_timestamp", "case_id", "timestamp"),
        Index("ix_cdr_records_case_cgi", "case_id", "first_cgi"),
        Index("ix_cdr_records_case_imei", "case_id", "imei"),
        Index("ix_cdr_records_case_target", "case_id", "target_number"),
    )
