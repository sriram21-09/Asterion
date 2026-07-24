import csv
import io
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy.orm import Session
from app.models.import_job import ImportJob
from app.models.cdr_record import CDRRecord


class BaseCDRParser(ABC):
    """Base interface for operator-specific CDR CSV parsers."""

    @abstractmethod
    def detect(self, content_sample: str) -> bool:
        """Return True if the content matches this operator's format."""
        pass

    @abstractmethod
    def parse(self, content: str) -> Tuple[List[Dict[str, Any]], int]:
        """
        Parse CSV content string.
        Returns a tuple of (parsed_records_dicts, failed_count).
        """
        pass


class AirtelCDRParser(BaseCDRParser):
    """CSV parser for Bharti Airtel CDR files."""

    def detect(self, content_sample: str) -> bool:
        content_upper = content_sample.upper()
        return "AIRTEL" in content_upper or "FIRST CGI LAT/LONG" in content_upper

    def _clean_val(self, val: str) -> str:
        if not val:
            return ""
        val = val.strip()
        if val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        elif val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        return val.strip()

    def _parse_coords(self, coord_str: str) -> Tuple[Optional[float], Optional[float]]:
        clean_str = self._clean_val(coord_str)
        if not clean_str or "/" not in clean_str:
            return None, None
        parts = clean_str.split("/")
        if len(parts) >= 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return lat, lon
            except ValueError:
                return None, None
        return None, None

    def _parse_dt(self, date_str: str, time_str: str) -> Optional[datetime]:
        d_clean = self._clean_val(date_str)
        t_clean = self._clean_val(time_str)
        if not d_clean:
            return None
        dt_str = f"{d_clean} {t_clean}".strip()
        for fmt in (
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None

    def parse(self, content: str) -> Tuple[List[Dict[str, Any]], int]:
        records: List[Dict[str, Any]] = []
        failed_count = 0

        lines = content.splitlines()
        header_idx = -1

        for i, line in enumerate(lines):
            line_upper = line.upper()
            if "TARGET NO" in line_upper or "FIRST CGI" in line_upper:
                header_idx = i
                break

        if header_idx == -1:
            # Fallback: assume line 0 if header not found
            header_idx = 0

        data_lines = lines[header_idx:]
        reader = csv.reader(data_lines)
        header_parsed = False

        for row in reader:
            if not row or not any(row):
                continue

            # First non-empty row is header
            if not header_parsed:
                header_parsed = True
                continue

            try:
                target_no = self._clean_val(row[0]) if len(row) > 0 else None
                call_type = self._clean_val(row[1]) if len(row) > 1 else None
                b_party = self._clean_val(row[3]) if len(row) > 3 else None
                date_str = row[6] if len(row) > 6 else ""
                time_str = row[7] if len(row) > 7 else ""
                dur_str = self._clean_val(row[8]) if len(row) > 8 else "0"

                duration = 0
                if dur_str.isdigit():
                    duration = int(dur_str)

                first_cgi_lat_lon = row[9] if len(row) > 9 else ""
                lat, lon = self._parse_coords(first_cgi_lat_lon)

                first_cgi = self._clean_val(row[10]) if len(row) > 10 else None
                last_cgi_lat_lon = row[11] if len(row) > 11 else ""
                last_lat, last_lon = self._parse_coords(last_cgi_lat_lon)

                last_cgi = self._clean_val(row[12]) if len(row) > 12 else None
                smsc = self._clean_val(row[13]) if len(row) > 13 else None
                service_type = self._clean_val(row[14]) if len(row) > 14 else None
                imei = self._clean_val(row[15]) if len(row) > 15 else None
                imsi = self._clean_val(row[16]) if len(row) > 16 else None
                roaming_nw = self._clean_val(row[18]) if len(row) > 18 else None

                timestamp = self._parse_dt(date_str, time_str)

                record = {
                    "operator": "airtel",
                    "target_number": target_no,
                    "b_party_number": b_party,
                    "call_type": call_type,
                    "service_type": service_type,
                    "timestamp": timestamp,
                    "duration": duration,
                    "latitude": lat,
                    "longitude": lon,
                    "first_cgi": first_cgi,
                    "first_bts_location": first_cgi_lat_lon,
                    "last_latitude": last_lat,
                    "last_longitude": last_lon,
                    "last_cgi": last_cgi,
                    "last_bts_location": last_cgi_lat_lon,
                    "imei": imei,
                    "imsi": imsi,
                    "smsc_number": smsc,
                    "roaming_network": roaming_nw,
                    "raw_data": {"row": row},
                }
                records.append(record)
            except Exception:
                failed_count += 1

        return records, failed_count


class BSNLCDRParser(BaseCDRParser):
    """CSV parser for BSNL CDR files."""

    # Pattern matches Lat-22.39711; Long-88.43938 or Lat:22.39711 Long:88.43938
    COORD_PATTERN = re.compile(
        r"Lat[-:\s]*([0-9\.]+).*?Long[-:\s]*([0-9\.]+)", re.IGNORECASE
    )

    def detect(self, content_sample: str) -> bool:
        content_upper = content_sample.upper()
        return "BSNL" in content_upper or "FIRST BTS LOCATION" in content_upper or "SEARCH CRITERIA" in content_upper

    def _clean_val(self, val: str) -> str:
        if not val:
            return ""
        return val.strip().strip("'").strip('"').strip()

    def _extract_coords(self, location_str: str) -> Tuple[Optional[float], Optional[float]]:
        if not location_str:
            return None, None
        match = self.COORD_PATTERN.search(location_str)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                return lat, lon
            except ValueError:
                return None, None
        return None, None

    def _parse_dt(self, date_str: str, time_str: str) -> Optional[datetime]:
        d_clean = self._clean_val(date_str)
        t_clean = self._clean_val(time_str)
        if not d_clean:
            return None
        dt_str = f"{d_clean} {t_clean}".strip()
        for fmt in (
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None

    def parse(self, content: str) -> Tuple[List[Dict[str, Any]], int]:
        records: List[Dict[str, Any]] = []
        failed_count = 0

        lines = content.splitlines()
        header_idx = -1

        for i, line in enumerate(lines):
            line_upper = line.upper()
            if "TARGET/A-PARTY NUMBER" in line_upper or "FIRST BTS LOCATION" in line_upper or "CALL DATE" in line_upper:
                header_idx = i
                break

        if header_idx == -1:
            header_idx = 0

        data_lines = lines[header_idx:]
        reader = csv.reader(data_lines)
        header_parsed = False

        for row in reader:
            if not row or not any(row):
                continue

            row_str = " ".join(row)
            if "***" in row_str or "CDR COUNT" in row_str:
                continue

            if not header_parsed:
                header_parsed = True
                continue

            try:
                target_no = self._clean_val(row[0]) if len(row) > 0 else None
                call_type = self._clean_val(row[1]) if len(row) > 1 else None
                b_party = self._clean_val(row[3]) if len(row) > 3 else None
                date_str = row[6] if len(row) > 6 else ""
                time_str = row[7] if len(row) > 7 else ""
                dur_str = self._clean_val(row[8]) if len(row) > 8 else "0"

                duration = 0
                if dur_str.isdigit():
                    duration = int(dur_str)

                first_bts_loc = self._clean_val(row[9]) if len(row) > 9 else ""
                lat, lon = self._extract_coords(first_bts_loc)

                first_cgi = self._clean_val(row[10]) if len(row) > 10 else None
                last_bts_loc = self._clean_val(row[11]) if len(row) > 11 else ""
                last_lat, last_lon = self._extract_coords(last_bts_loc)

                last_cgi = self._clean_val(row[12]) if len(row) > 12 else None
                smsc = self._clean_val(row[13]) if len(row) > 13 else None
                service_type = self._clean_val(row[14]) if len(row) > 14 else None
                imei = self._clean_val(row[15]) if len(row) > 15 else None
                imsi = self._clean_val(row[16]) if len(row) > 16 else None
                roaming_nw = self._clean_val(row[18]) if len(row) > 18 else None

                timestamp = self._parse_dt(date_str, time_str)

                record = {
                    "operator": "bsnl",
                    "target_number": target_no,
                    "b_party_number": b_party,
                    "call_type": call_type,
                    "service_type": service_type,
                    "timestamp": timestamp,
                    "duration": duration,
                    "latitude": lat,
                    "longitude": lon,
                    "first_cgi": first_cgi,
                    "first_bts_location": first_bts_loc,
                    "last_latitude": last_lat,
                    "last_longitude": last_lon,
                    "last_cgi": last_cgi,
                    "last_bts_location": last_bts_loc,
                    "imei": imei,
                    "imsi": imsi,
                    "smsc_number": smsc,
                    "roaming_network": roaming_nw,
                    "raw_data": {"row": row},
                }
                records.append(record)
            except Exception:
                failed_count += 1

        return records, failed_count



class JioCDRParser(BaseCDRParser):
    """CSV parser for Reliance Jio CDR files."""

    def detect(self, content_sample: str) -> bool:
        content_upper = content_sample.upper()
        return (
            "RELIANCE JIO INFOCOMM" in content_upper
            or "CALLING PARTY TELEPHONE NUMBER" in content_upper
            or ("FIRST CELL ID" in content_upper and "FIRST CELL GLOBAL ID" not in content_upper)
        )

    def _clean_val(self, val: str) -> str:
        if not val:
            return ""
        val = val.strip()
        if val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        elif val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        val = val.strip()
        return "" if val == "-" else val

    def _parse_dt(self, date_str: str, time_str: str) -> Optional[datetime]:
        d_clean = self._clean_val(date_str)
        t_clean = self._clean_val(time_str)
        if not d_clean:
            return None
        dt_str = f"{d_clean} {t_clean}".strip()
        for fmt in (
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y %H:%M",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None

    def parse(self, content: str) -> Tuple[List[Dict[str, Any]], int]:
        records: List[Dict[str, Any]] = []
        failed_count = 0

        lines = content.splitlines()
        header_idx = -1

        for i, line in enumerate(lines):
            line_upper = line.upper()
            if "CALLING PARTY TELEPHONE NUMBER" in line_upper or "FIRST CELL ID" in line_upper:
                header_idx = i
                break

        if header_idx == -1:
            header_idx = 18 if len(lines) > 18 else 0

        data_lines = lines[header_idx:]
        reader = csv.reader(data_lines)
        header_parsed = False

        for row in reader:
            if not row or not any(row):
                continue

            if not header_parsed:
                header_parsed = True
                continue

            row_str = " ".join(row).upper()
            if "REPORT" in row_str and "END" in row_str:
                continue

            try:
                calling_party = self._clean_val(row[0]) if len(row) > 0 else None
                called_party = self._clean_val(row[1]) if len(row) > 1 else None
                date_str = row[4] if len(row) > 4 else ""
                time_str = row[5] if len(row) > 5 else ""
                dur_str = self._clean_val(row[7]) if len(row) > 7 else "0"

                duration = 0
                if dur_str.isdigit():
                    duration = int(dur_str)

                first_cgi = self._clean_val(row[8]) if len(row) > 8 else None
                last_cgi = self._clean_val(row[9]) if len(row) > 9 else None
                call_type = self._clean_val(row[10]) if len(row) > 10 else None
                smsc = self._clean_val(row[11]) if len(row) > 11 else None
                imei = self._clean_val(row[12]) if len(row) > 12 else None
                imsi = self._clean_val(row[13]) if len(row) > 13 else None
                roaming_nw = self._clean_val(row[14]) if len(row) > 14 else None

                service_type = "SMS" if call_type and "SMS" in call_type.upper() else "Voice"
                timestamp = self._parse_dt(date_str, time_str)

                record = {
                    "operator": "jio",
                    "target_number": calling_party,
                    "b_party_number": called_party,
                    "call_type": call_type,
                    "service_type": service_type,
                    "timestamp": timestamp,
                    "duration": duration,
                    "latitude": None,
                    "longitude": None,
                    "first_cgi": first_cgi,
                    "first_bts_location": None,
                    "last_latitude": None,
                    "last_longitude": None,
                    "last_cgi": last_cgi,
                    "last_bts_location": None,
                    "imei": imei,
                    "imsi": imsi,
                    "smsc_number": smsc,
                    "roaming_network": roaming_nw,
                    "raw_data": {"row": row},
                }
                records.append(record)
            except Exception:
                failed_count += 1

        return records, failed_count


class ViCDRParser(BaseCDRParser):
    """CSV parser for Vodafone Idea (Vi) CDR files."""

    def detect(self, content_sample: str) -> bool:
        content_upper = content_sample.upper()
        return (
            "VODAFONE" in content_upper
            or "VODAFONE IDEA" in content_upper
            or "TARGET /A PARTY NUMBER" in content_upper
            or "TARGET / A PARTY NUMBER" in content_upper
            or "VI " in content_upper
        )

    def _clean_val(self, val: str) -> str:
        if not val:
            return ""
        val = val.strip()
        if val.startswith("'") and val.endswith("'"):
            val = val[1:-1]
        elif val.startswith('"') and val.endswith('"'):
            val = val[1:-1]
        val = val.strip()
        return "" if val == "-" else val

    def _parse_dt(self, date_str: str, time_str: str) -> Optional[datetime]:
        d_clean = self._clean_val(date_str)
        t_clean = self._clean_val(time_str)
        if not d_clean:
            return None
        dt_str = f"{d_clean} {t_clean}".strip()
        for fmt in (
            "%d-%m-%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%d-%m-%Y %H:%M",
            "%d/%m/%Y %H:%M",
            "%d-%m-%Y",
            "%d/%m/%Y",
        ):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None

    def parse(self, content: str) -> Tuple[List[Dict[str, Any]], int]:
        records: List[Dict[str, Any]] = []
        failed_count = 0

        lines = content.splitlines()
        header_idx = -1

        for i, line in enumerate(lines):
            line_upper = line.upper()
            if "TARGET /A PARTY NUMBER" in line_upper or "TARGET / A PARTY NUMBER" in line_upper or "FIRST CELL GLOBAL ID" in line_upper:
                header_idx = i
                break

        if header_idx == -1:
            header_idx = 10 if len(lines) > 10 else 0

        data_lines = lines[header_idx:]
        reader = csv.reader(data_lines)
        header_parsed = False

        for row in reader:
            if not row or not any(row):
                continue

            row_str = "".join(row).strip()
            if row_str.startswith("---") or set(row_str) == {"-"}:
                continue

            if not header_parsed:
                header_parsed = True
                continue

            if "REPORT" in row_str.upper() and "END" in row_str.upper():
                continue

            try:
                target_no = self._clean_val(row[0]) if len(row) > 0 else None
                call_type = self._clean_val(row[1]) if len(row) > 1 else None
                b_party = self._clean_val(row[3]) if len(row) > 3 else None
                date_str = row[6] if len(row) > 6 else ""
                time_str = row[7] if len(row) > 7 else ""
                dur_str = self._clean_val(row[8]) if len(row) > 8 else "0"

                duration = 0
                if dur_str.isdigit():
                    duration = int(dur_str)

                first_bts_loc = self._clean_val(row[9]) if len(row) > 9 else None
                first_cgi = self._clean_val(row[10]) if len(row) > 10 else None
                last_bts_loc = self._clean_val(row[11]) if len(row) > 11 else None
                last_cgi = self._clean_val(row[12]) if len(row) > 12 else None
                smsc = self._clean_val(row[13]) if len(row) > 13 else None
                service_type = self._clean_val(row[14]) if len(row) > 14 else None
                imei = self._clean_val(row[15]) if len(row) > 15 else None
                imsi = self._clean_val(row[16]) if len(row) > 16 else None
                roaming_nw = self._clean_val(row[18]) if len(row) > 18 else None

                timestamp = self._parse_dt(date_str, time_str)

                record = {
                    "operator": "vi",
                    "target_number": target_no,
                    "b_party_number": b_party,
                    "call_type": call_type,
                    "service_type": service_type,
                    "timestamp": timestamp,
                    "duration": duration,
                    "latitude": None,
                    "longitude": None,
                    "first_cgi": first_cgi,
                    "first_bts_location": first_bts_loc,
                    "last_latitude": None,
                    "last_longitude": None,
                    "last_cgi": last_cgi,
                    "last_bts_location": last_bts_loc,
                    "imei": imei,
                    "imsi": imsi,
                    "smsc_number": smsc,
                    "roaming_network": roaming_nw,
                    "raw_data": {"row": row},
                }
                records.append(record)
            except Exception:
                failed_count += 1

        return records, failed_count



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
