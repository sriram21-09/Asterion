"""
Jio CDR Parser
==============
"""

import csv
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.services.parsers.base import BaseCDRParser


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
