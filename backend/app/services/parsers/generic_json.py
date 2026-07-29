"""
Generic JSON CDR Parser
=======================
"""

import json
from datetime import datetime
from typing import Any

from app.services.parsers.base import BaseCDRParser


class GenericJSONParser(BaseCDRParser):
    """Parser for generic JSON CDR files."""

    def detect(self, content_sample: str) -> bool:
        content_sample = content_sample.strip()
        if not (content_sample.startswith("{") or content_sample.startswith("[")):
            return False

        try:
            # Try parsing a small snippet to see if it's valid JSON format
            # We can't parse the whole thing here if it's huge, but if it starts with [ or {
            # it's a good indicator. Let's just return true if it looks like JSON.
            return True
        except Exception:
            return False

    def _parse_dt(self, dt_str: str) -> datetime | None:
        if not dt_str:
            return None

        # Try common iso formats
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            pass

        for fmt in (
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
        ):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None

    def parse(self, content: str) -> tuple[list[dict[str, Any]], int]:
        records: list[dict[str, Any]] = []
        failed_count = 0

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return [], 1

        # If data is a dictionary containing a list, extract the list
        if isinstance(data, dict):
            for val in data.values():
                if isinstance(val, list):
                    data = val
                    break
            else:
                data = [data]

        if not isinstance(data, list):
            data = [data]

        for item in data:
            if not isinstance(item, dict):
                failed_count += 1
                continue

            try:
                # Try to extract fields dynamically (case-insensitive keys)
                keys = {k.lower(): k for k in item.keys()}

                def get_val(*possible_keys):
                    for k in possible_keys:
                        if k in keys:
                            return item[keys[k]]
                    return None

                target_number = get_val(
                    "target_number", "calling_party", "caller", "from"
                )
                b_party_number = get_val(
                    "b_party_number", "called_party", "callee", "to"
                )

                ts_str = get_val("timestamp", "date", "time", "datetime")
                timestamp = self._parse_dt(str(ts_str)) if ts_str else None

                dur_val = get_val("duration", "duration_sec")
                duration = int(dur_val) if dur_val and str(dur_val).isdigit() else 0

                lat_val = get_val("latitude", "lat")
                lon_val = get_val("longitude", "lon", "lng")

                lat = float(lat_val) if lat_val is not None else None
                lon = float(lon_val) if lon_val is not None else None

                call_type = get_val("call_type", "type")
                service_type = get_val("service_type", "service")
                if not service_type:
                    service_type = (
                        "SMS"
                        if call_type and "SMS" in str(call_type).upper()
                        else "Voice"
                    )

                first_cgi = get_val("first_cgi", "cgi", "cell_id")
                last_cgi = get_val("last_cgi")

                imei = get_val("imei")
                imsi = get_val("imsi")

                record = {
                    "operator": "generic_json",
                    "target_number": str(target_number) if target_number else None,
                    "b_party_number": str(b_party_number) if b_party_number else None,
                    "call_type": str(call_type) if call_type else None,
                    "service_type": str(service_type),
                    "timestamp": timestamp,
                    "duration": duration,
                    "latitude": lat,
                    "longitude": lon,
                    "first_cgi": str(first_cgi) if first_cgi else None,
                    "first_bts_location": None,
                    "last_latitude": None,
                    "last_longitude": None,
                    "last_cgi": str(last_cgi) if last_cgi else None,
                    "last_bts_location": None,
                    "imei": str(imei) if imei else None,
                    "imsi": str(imsi) if imsi else None,
                    "smsc_number": str(get_val("smsc_number", "smsc")) or None,
                    "roaming_network": str(get_val("roaming_network", "roaming"))
                    or None,
                    "raw_data": {"json": item},
                }
                records.append(record)
            except Exception:
                failed_count += 1

        return records, failed_count
