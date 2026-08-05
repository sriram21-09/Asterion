"""
CDR Import Service
==================
"""

from typing import Any

from app.models.cdr_record import CDRRecord
from app.models.import_job import ImportJob
from app.services.parsers import (
    AirtelCDRParser,
    BaseCDRParser,
    BSNLCDRParser,
    JioCDRParser,
    ViCDRParser,
    GenericJSONParser,
    GenericXMLParser,
)
from app.models.case import Case
from app.models.measurement import Measurement
from app.models.movement_event import MovementEvent
from datetime import datetime, timezone
from sqlalchemy.orm import Session


class CDRImportService:
    """Service to orchestrate CDR file uploads, parsing, and database storage."""

    PARSERS: list[BaseCDRParser] = [
        AirtelCDRParser(),
        JioCDRParser(),
        ViCDRParser(),
        BSNLCDRParser(),
        GenericJSONParser(),
        GenericXMLParser(),
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
                elif isinstance(parser, GenericJSONParser):
                    return "generic_json"
                elif isinstance(parser, GenericXMLParser):
                    return "generic_xml"
        return "unknown"

    @classmethod
    def get_parser(cls, operator: str) -> BaseCDRParser | None:
        op_lower = operator.lower()
        if op_lower == "airtel":
            return AirtelCDRParser()
        elif op_lower == "bsnl":
            return BSNLCDRParser()
        elif op_lower == "jio":
            return JioCDRParser()
        elif op_lower in ("vi", "vodafone", "idea", "vodafone idea"):
            return ViCDRParser()
        elif op_lower in ("generic_json", "json"):
            return GenericJSONParser()
        elif op_lower in ("generic_xml", "xml"):
            return GenericXMLParser()
        return None

    def process_upload(
        self,
        file_name: str,
        file_bytes: bytes,
        case_id: int | None = None,
        operator: str | None = None,
        db: Session = None,  # type: ignore[assignment]
    ) -> dict[str, Any]:
        content = file_bytes.decode("utf-8", errors="replace")

        detected_op = operator
        if not detected_op or detected_op.lower() == "auto":
            detected_op = self.detect_operator(content)

        parser = self.get_parser(detected_op)

        if case_id is not None:
            existing_job = (
                db.query(ImportJob)
                .filter(
                    ImportJob.case_id == case_id,
                    ImportJob.filename == file_name,
                    ImportJob.status == "completed",
                )
                .first()
            )
            if existing_job:
                return {
                    "job": existing_job,
                    "summary": {
                        "total_records": existing_job.total_records,
                        "parsed_records": existing_job.parsed_records,
                        "failed_records": existing_job.failed_records,
                        "status": "duplicate",
                        "error": "This file has already been imported into this case.",
                    },
                }

        if case_id is None:
            new_case = Case(
                title=f"Import - {file_name}",
                description="Automatically created from file upload.",
                status="review",
            )
            db.add(new_case)
            db.commit()
            db.refresh(new_case)
            case_id = new_case.id

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

            # Pre-resolve tower coordinates for CGIs without explicit lat/lon
            from app.models.tower import Tower

            cgi_coords_map: dict[str, tuple[float | None, float | None]] = {}
            new_towers: list[Tower] = []

            for data in records_data:
                lat = data.get("latitude")
                lon = data.get("longitude")
                cgi = data.get("first_cgi") or data.get("last_cgi")

                if (lat is None or lon is None) and cgi:
                    if cgi not in cgi_coords_map:
                        cgi_coords_map[cgi] = (None, None)
                        new_towers.append(
                            Tower(
                                cgi=cgi,
                                tower_name=f"Cell {cgi}",
                                latitude=None,
                                longitude=None,
                                operator=detected_op or "Unknown",
                                confidence=0.1,
                                confidence_category="Unknown",
                                resolution_method="unresolved",
                            )
                        )
                    resolved_lat, resolved_lon = cgi_coords_map[cgi]
                    data["latitude"] = resolved_lat
                    data["longitude"] = resolved_lon

            if new_towers:
                db.bulk_save_objects(new_towers)

            db_records = [
                CDRRecord(
                    import_job_id=job.id,
                    case_id=case_id,
                    **data,
                )
                for data in records_data
            ]

            db.bulk_save_objects(db_records)

            measurements = []
            movement_events = []
            now = datetime.now(timezone.utc)

            for i, data in enumerate(records_data):
                lat = data.get("latitude")
                lon = data.get("longitude")
                ts = data.get("timestamp") or now

                measurements.append(
                    Measurement(
                        case_id=case_id,
                        scenario_id=None,
                        measurement_code=f"IMP-{job.id}-{i}",
                        timestamp=ts,
                        rssi_dbm=None,
                        latitude=lat,
                        longitude=lon,
                        uncertainty_m=None,
                    )
                )

                movement_events.append(
                    MovementEvent(
                        case_id=case_id,
                        timestamp=ts,
                        latitude=lat,
                        longitude=lon,
                        event_type="movement",
                        sequence_number=i,
                        speed_kmh=None,
                        confidence=None,
                    )
                )

            if measurements:
                db.bulk_save_objects(measurements)
            if movement_events:
                db.bulk_save_objects(movement_events)

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
    "AirtelCDRParser",
    "BSNLCDRParser",
    "BaseCDRParser",
    "CDRImportService",
    "JioCDRParser",
    "ViCDRParser",
    "GenericJSONParser",
    "GenericXMLParser",
]
