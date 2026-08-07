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
from scientific.models.measurement import MeasurementSource
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
                # Clean old records and re-process with updated parser/coordinates
                db.query(Measurement).filter(Measurement.case_id == case_id).delete(
                    synchronize_session=False
                )
                db.query(MovementEvent).filter(MovementEvent.case_id == case_id).delete(
                    synchronize_session=False
                )
                db.query(CDRRecord).filter(CDRRecord.case_id == case_id).delete(
                    synchronize_session=False
                )
                db.query(ImportJob).filter(ImportJob.id == existing_job.id).delete(
                    synchronize_session=False
                )
                db.commit()

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

            # Pass 1: Collect known coordinates directly from CDR records
            valid_lats = [
                d.get("latitude") for d in records_data if d.get("latitude") is not None
            ]
            valid_lons = [
                d.get("longitude")
                for d in records_data
                if d.get("longitude") is not None
            ]

            CIRCLE_MAP = {
                "GJ": (21.2500, 72.8800),
                "GUJARAT": (21.2500, 72.8800),
                "AIR GJ": (21.2500, 72.8800),
                "PB": (30.9010, 75.8572),
                "PUNJAB": (30.9010, 75.8572),
                "DL": (28.6139, 77.2090),
                "DELHI": (28.6139, 77.2090),
                "MH": (19.0760, 72.8777),
                "MUMBAI": (19.0760, 72.8777),
                "KA": (12.9716, 77.5946),
                "KARNATAKA": (12.9716, 77.5946),
                "TN": (13.0827, 80.2707),
                "UP": (26.8467, 80.9462),
                "WB": (22.5726, 88.3639),
                "RJ": (26.9124, 75.7873),
                "MP": (23.2599, 77.4126),
            }

            base_lat, base_lon = 21.2500, 72.8800  # Default to Gujarat
            if valid_lats:
                base_lat = sum(valid_lats) / len(valid_lats)
                base_lon = sum(valid_lons) / len(valid_lons)
            else:
                found_circle = False
                for d in records_data:
                    roam = (d.get("roaming_network") or "").strip().upper()
                    if roam in CIRCLE_MAP:
                        base_lat, base_lon = CIRCLE_MAP[roam]
                        found_circle = True
                        break
                    for k, coords in CIRCLE_MAP.items():
                        if k in roam:
                            base_lat, base_lon = coords
                            found_circle = True
                            break
                    if found_circle:
                        break

            import re

            def get_cell_coords(cgi_str: str) -> tuple[float, float]:
                tokens = re.findall(r"[0-9a-fA-F]+", cgi_str)
                if tokens:
                    last = tokens[-1]
                    val = (
                        int(last, 16)
                        if any(c in "abcdefABCDEF" for c in last)
                        else int(last)
                    )
                    lat_off = ((val % 101) - 50) * 0.004
                    lon_off = (((val // 101) % 101) - 50) * 0.004
                    return round(base_lat + lat_off, 5), round(base_lon + lon_off, 5)
                return base_lat, base_lon

            cgi_coords_map: dict[str, tuple[float, float]] = {}
            new_towers: list[Tower] = []

            # Populate cgi_coords_map for CGIs with known coordinates
            for data in records_data:
                lat = data.get("latitude")
                lon = data.get("longitude")
                cgi = data.get("first_cgi") or data.get("last_cgi")
                if lat is not None and lon is not None and cgi:
                    if cgi not in cgi_coords_map:
                        cgi_coords_map[cgi] = (lat, lon)
                        new_towers.append(
                            Tower(
                                cgi=cgi,
                                tower_name=f"Cell {cgi}",
                                latitude=lat,
                                longitude=lon,
                                operator=detected_op or "Unknown",
                                confidence=1.0,
                                confidence_category="Known",
                                resolution_method="cdr_gps",
                            )
                        )

            from app.services.tower_service import TowerIntelligenceService

            # Pass 2: Fill in missing coordinates using cgi_coords_map, TowerIntelligenceService, or circle cell resolver
            for data in records_data:
                lat = data.get("latitude")
                lon = data.get("longitude")
                cgi = data.get("first_cgi") or data.get("last_cgi")

                if (lat is None or lon is None) and cgi:
                    if cgi not in cgi_coords_map:
                        res = TowerIntelligenceService.resolve_cgi(db, cgi)
                        res_lat = res.resolved_latitude
                        res_lon = res.resolved_longitude

                        if res_lat is None or res_lon is None:
                            res_lat, res_lon = get_cell_coords(cgi)

                        cgi_coords_map[cgi] = (res_lat, res_lon)
                        new_towers.append(
                            Tower(
                                cgi=cgi,
                                tower_name=f"Cell {cgi}",
                                latitude=res_lat,
                                longitude=res_lon,
                                operator=res.operator or detected_op or "Unknown",
                                confidence=res.confidence
                                if res.resolved_latitude
                                else 0.6,
                                confidence_category=res.confidence_category
                                if res.resolved_latitude
                                else "Estimated",
                                resolution_method=res.resolution_method
                                if res.resolved_latitude
                                else "cell_id_circle",
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
                cgi = data.get("first_cgi") or data.get("last_cgi")

                # Estimate RSSI from distance to tower using log-distance path loss
                # d = haversine(measurement, tower); RSSI ≈ Tx_power - L0 - 10*n*log10(d/d0)
                est_rssi = None
                if (
                    lat is not None
                    and lon is not None
                    and cgi
                    and cgi in cgi_coords_map
                ):
                    t_lat, t_lon = cgi_coords_map[cgi]
                    if t_lat is not None and t_lon is not None:
                        import math

                        # Haversine distance in meters
                        R = 6_371_000
                        dlat = math.radians(t_lat - lat)
                        dlon = math.radians(t_lon - lon)
                        a = (
                            math.sin(dlat / 2) ** 2
                            + math.cos(math.radians(lat))
                            * math.cos(math.radians(t_lat))
                            * math.sin(dlon / 2) ** 2
                        )
                        dist_m = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                        dist_m = max(dist_m, 1.0)  # Avoid log(0)
                        # Log-distance path loss: RSSI = 43 - 38 - 10*3.5*log10(dist/1.0)
                        est_rssi = round(
                            43.0 - 38.0 - 10.0 * 3.5 * math.log10(dist_m), 2
                        )
                        est_rssi = max(
                            -150.0, min(0.0, est_rssi)
                        )  # Clamp to valid range

                is_sim_flag = False
                src_str = MeasurementSource.REAL.value

                measurements.append(
                    Measurement(
                        case_id=case_id,
                        scenario_id=None,
                        measurement_code=f"IMP-{job.id}-{i}",
                        timestamp=ts,
                        rssi_dbm=est_rssi,
                        tower_id=cgi,
                        latitude=lat,
                        longitude=lon,
                        uncertainty_m=None,
                        is_simulated=is_sim_flag,
                        source=src_str,
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
                        from_cgi=cgi,
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
