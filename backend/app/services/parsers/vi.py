"""
Vi (Vodafone Idea) CDR Parser
=============================
"""

import csv
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.services.parsers.base import BaseCDRParser


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
            if (
                "TARGET /A PARTY NUMBER" in line_upper
                or "TARGET / A PARTY NUMBER" in line_upper
                or "FIRST CELL GLOBAL ID" in line_upper
            ):
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
