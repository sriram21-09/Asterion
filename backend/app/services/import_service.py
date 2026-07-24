"""
CDR Import Service
==================
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.cdr_record import CDRRecord
from app.models.import_job import ImportJob
from app.services.parsers import (
    AirtelCDRParser,
    BaseCDRParser,
    BSNLCDRParser,
    JioCDRParser,
    ViCDRParser,
)


class CDRImportService:
    """Service to orchestrate CDR file uploads, parsing, and database storage."""

    PARSERS: List[BaseCDRParser] = [
        AirtelCDRParser(),
        JioCDRParser(),
        ViCDRParser(),
        BSNLCDRParser(),
    ]

    @classmethod
    def detect_operator(cls, content: str) -> str:
        sample = content[:4096]
        for parser in cls.PARSERS:
            if parser.detect(sample):
                if isinstance(parser, AirtelCDRParser):
                    return "airtel"
                elif isinstance(parser, BSNLCDRParser):
                    return "bsnl"
                elif isinstance(parser, JioCDRParser):
                    return "jio"
                elif isinstance(parser, ViCDRParser):
                    return "vi"
        return "unknown"

    @classmethod
    def get_parser(cls, operator: str) -> Optional[BaseCDRParser]:
        op_lower = operator.lower()
        if op_lower == "airtel":
            return AirtelCDRParser()
        elif op_lower == "bsnl":
            return BSNLCDRParser()
        elif op_lower == "jio":
            return JioCDRParser()
        elif op_lower in ("vi", "vodafone", "idea", "vodafone idea"):
            return ViCDRParser()
        return None

    def process_upload(
        self,
        file_name: str,
        file_bytes: bytes,
        case_id: Optional[int] = None,
        operator: Optional[str] = None,
        db: Session = None,  # type: ignore[assignment]
    ) -> Dict[str, Any]:
        content = file_bytes.decode("utf-8", errors="replace")

        detected_op = operator
        if not detected_op or detected_op.lower() == "auto":
            detected_op = self.detect_operator(content)

        parser = self.get_parser(detected_op)

        job = ImportJob(
            filename=file_name,
            operator=detected_op,
            status="processing",
            case_id=case_id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        if not parser:
            job.status = "failed"
            job.error_message = f"Unsupported or unknown operator format: {detected_op}"
            db.commit()
            return {
                "job": job,
                "summary": {
                    "total_records": 0,
                    "parsed_records": 0,
                    "failed_records": 0,
                    "status": "failed",
                    "error": job.error_message,
                },
            }

        try:
            records_data, failed_count = parser.parse(content)
            total_count = len(records_data) + failed_count

            db_records = [
                CDRRecord(
                    import_job_id=job.id,
                    case_id=case_id,
                    **data,
                )
                for data in records_data
            ]

            db.bulk_save_objects(db_records)

            job.total_records = total_count
            job.parsed_records = len(records_data)
            job.failed_records = failed_count
            job.status = "completed"
            db.commit()
            db.refresh(job)

            return {
                "job": job,
                "summary": {
                    "total_records": total_count,
                    "parsed_records": len(records_data),
                    "failed_records": failed_count,
                    "status": "completed",
                },
            }
        except Exception as e:
            db.rollback()
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            return {
                "job": job,
                "summary": {
                    "total_records": 0,
                    "parsed_records": 0,
                    "failed_records": 0,
                    "status": "failed",
                    "error": str(e),
                },
            }


__all__ = [
    "BaseCDRParser",
    "AirtelCDRParser",
    "BSNLCDRParser",
    "JioCDRParser",
    "ViCDRParser",
    "CDRImportService",
]
