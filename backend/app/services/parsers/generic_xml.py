"""
Generic XML CDR Parser
======================
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

from app.services.parsers.base import BaseCDRParser


class GenericXMLParser(BaseCDRParser):
    """Parser for generic XML CDR files."""

    def detect(self, content_sample: str) -> bool:
        content_sample = content_sample.strip()
        if not content_sample.startswith("<?xml") and not content_sample.startswith("<"):
            return False
            
        try:
            # Check if it's parseable XML
            # Just parsing the snippet might fail if it's truncated, 
            # so we just return True if it looks like XML tags
            return True
        except Exception:
            return False

    def _parse_dt(self, dt_str: str) -> datetime | None:
        if not dt_str:
            return None
            
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
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
            root = ET.fromstring(content)
        except ET.ParseError:
            return [], 1
            
        # Try to find all elements that might be records. 
        # Typically, in XML, the root contains a list of children which are the records.
        # If the root only has one child, maybe that child is the list of records.
        elements = list(root)
        if len(elements) == 1 and len(list(elements[0])) > 0:
            elements = list(elements[0])

        for el in elements:
            try:
                # Extract fields dynamically from child elements or attributes
                # Also convert tags to lowercase for case-insensitive matching
                data = {child.tag.lower(): child.text for child in el}
                data.update({k.lower(): v for k, v in el.attrib.items()})
                
                if not data:
                    continue

                def get_val(*possible_keys):
                    for k in possible_keys:
                        if k in data:
                            return data[k]
                    return None

                target_number = get_val("target_number", "calling_party", "caller", "from")
                b_party_number = get_val("b_party_number", "called_party", "callee", "to")
                
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
                    service_type = "SMS" if call_type and "SMS" in str(call_type).upper() else "Voice"

                first_cgi = get_val("first_cgi", "cgi", "cell_id")
                last_cgi = get_val("last_cgi")
                
                imei = get_val("imei")
                imsi = get_val("imsi")

                record = {
                    "operator": "generic_xml",
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
                    "roaming_network": str(get_val("roaming_network", "roaming")) or None,
                    "raw_data": {"xml_tag": el.tag},
                }
                records.append(record)
            except Exception:
                failed_count += 1

        return records, failed_count
