from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any, Dict
from sqlalchemy import ForeignKey, String, Text, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.import_job import ImportJob
    from app.models.case import Case


class CDRRecord(BaseModel):
    __tablename__ = "cdr_records"

    import_job_id: Mapped[int] = mapped_column(
        ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True
    )

    operator: Mapped[str] = mapped_column(String(50), nullable=False)
    target_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    b_party_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    call_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    service_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    first_cgi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    first_bts_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    last_latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_cgi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_bts_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    imei: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    imsi: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    smsc_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    roaming_network: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    raw_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    import_job: Mapped["ImportJob"] = relationship("ImportJob", back_populates="cdr_records")
    case: Mapped[Optional["Case"]] = relationship("Case", backref="cdr_records")
