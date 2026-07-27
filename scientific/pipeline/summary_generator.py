"""
Investigation Summary Generator Module
=======================================

Template-based neutral investigation summary text generator adhering to 
strict terminology standards (Section 3F of the Master Execution Plan).

Approved Terminology:
    - analyzed device / the analyzed device
    - observed device / the observed device
    - target identifier / the target identifier
    - analyzed subscriber / the analyzed subscriber

Prohibited Terms (Raises ValueError if detected):
    - suspect
    - criminal
    - perpetrator
    - guilty party
"""

import re
from typing import Any, Dict, List, Optional

APPROVED_TERMS: set[str] = {
    "analyzed device",
    "the analyzed device",
    "observed device",
    "the observed device",
    "target identifier",
    "the target identifier",
    "analyzed subscriber",
    "the analyzed subscriber",
}

PROHIBITED_TERMS: set[str] = {
    "suspect",
    "criminal",
    "perpetrator",
    "guilty party",
}

# Regex pattern matching prohibited terms on word boundaries (case-insensitive)
_PROHIBITED_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(term) for term in sorted(PROHIBITED_TERMS)) + r")\b",
    re.IGNORECASE,
)


def validate_neutral_terminology(text: str) -> str:
    """
    Validates that text contains no prohibited non-neutral terminology.

    Args:
        text: The string to validate.

    Returns:
        The validated text string if clean.

    Raises:
        ValueError: If any prohibited term is detected.
    """
    if not text:
        return text

    match = _PROHIBITED_REGEX.search(text)
    if match:
        raise ValueError(
            f"Prohibited non-neutral term detected: '{match.group(0)}'. "
            f"Investigation summaries must use approved neutral terminology only."
        )

    return text


class InvestigationSummaryGenerator:
    """
    Generates structured, neutral investigation summaries using approved terminology.
    """

    def __init__(self, target_identifier: str = "Target Device"):
        validate_neutral_terminology(target_identifier)
        self.target_identifier = target_identifier

    def generate_device_overview(
        self,
        total_records: int,
        active_period: str,
        primary_operator: str = "Unknown",
        imei: Optional[str] = None,
        imsi: Optional[str] = None,
        msisdn: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Generates the device overview narrative section.
        """
        if notes:
            validate_neutral_terminology(notes)

        id_details = []
        if imei:
            id_details.append(f"IMEI: {imei}")
        if imsi:
            id_details.append(f"IMSI: {imsi}")
        if msisdn:
            id_details.append(f"MSISDN: {msisdn}")

        id_str = f" ({', '.join(id_details)})" if id_details else ""

        overview = (
            f"Device Overview:\n"
            f"The analyzed device associated with target identifier {self.target_identifier}{id_str} "
            f"has {total_records} recorded Telecom CDR entries across the active period {active_period}. "
            f"Primary network operator registered: {primary_operator}. "
            f"All activity records for the observed device have been normalized and cataloged for analysis."
        )

        if notes:
            overview += f"\nAdditional Notes: {notes}"

        return validate_neutral_terminology(overview)

    def generate_movement_patterns(
        self,
        total_distance_km: float,
        avg_speed_kmh: float,
        max_speed_kmh: float,
        handover_count: int = 0,
        high_velocity_count: int = 0,
        notes: Optional[str] = None,
    ) -> str:
        """
        Generates the movement patterns narrative section.
        """
        if notes:
            validate_neutral_terminology(notes)

        movement = (
            f"Movement Patterns:\n"
            f"Spatial analysis of the observed device indicates a cumulative estimated travel distance "
            f"of {total_distance_km:.2f} km with an average reconstructed velocity of {avg_speed_kmh:.1f} km/h "
            f"(maximum recorded velocity: {max_speed_kmh:.1f} km/h). "
            f"A total of {handover_count} network handover events (same site sector transitions) were identified."
        )


        if high_velocity_count > 0:
            movement += (
                f" Additionally, {high_velocity_count} anomaly events with velocities exceeding physical thresholds "
                f"(>350 km/h) were detected for the observed device and tagged as network roaming or handover artifacts."
            )
        else:
            movement += (
                " No physically implausible velocity anomalies (>350 km/h) were detected during the observed period."
            )

        if notes:
            movement += f"\nAdditional Notes: {notes}"

        return validate_neutral_terminology(movement)

    def generate_tower_associations(
        self,
        total_towers: int,
        primary_tower_id: str,
        known_count: int = 0,
        estimated_count: int = 0,
        unknown_count: int = 0,
        notes: Optional[str] = None,
    ) -> str:
        """
        Generates the tower associations narrative section.
        """
        if notes:
            validate_neutral_terminology(notes)

        tower = (
            f"Tower Associations:\n"
            f"The observed device registered connections across {total_towers} unique cell tower sites. "
            f"The primary tower site of highest dwell time/frequency is {primary_tower_id}. "
            f"Tower location confidence breakdown: {known_count} Known (exact site coordinates), "
            f"{estimated_count} Estimated (resolved via secondary lookups), and {unknown_count} Unknown "
            f"(unresolved coordinates preserved with zero spatial bias). "
            f"All tower interactions for the analyzed subscriber have been validated against operator registry standards."
        )

        if notes:
            tower += f"\nAdditional Notes: {notes}"

        return validate_neutral_terminology(tower)

    def generate_timeline_narrative(
        self,
        first_seen: str,
        first_location: str,
        last_seen: str,
        last_location: str,
        peak_period: str = "N/A",
        notes: Optional[str] = None,
    ) -> str:
        """
        Generates the timeline narrative section.
        """
        if notes:
            validate_neutral_terminology(notes)

        timeline = (
            f"Timeline Narrative:\n"
            f"Chronological record analysis for the analyzed device establishes initial observation at {first_seen} "
            f"in the vicinity of {first_location}. The final recorded observation occurred at {last_seen} "
            f"near {last_location}. Peak transaction density occurred during {peak_period}. "
            f"Strict chronological ordering was maintained throughout the timeline reconstruction for the target identifier."
        )

        if notes:
            timeline += f"\nAdditional Notes: {notes}"

        return validate_neutral_terminology(timeline)

    def generate_full_investigation_summary(
        self,
        total_records: int,
        active_period: str,
        total_distance_km: float,
        avg_speed_kmh: float,
        max_speed_kmh: float,
        total_towers: int,
        primary_tower_id: str,
        first_seen: str,
        first_location: str,
        last_seen: str,
        last_location: str,
        primary_operator: str = "Unknown",
        handover_count: int = 0,
        high_velocity_count: int = 0,
        known_towers: int = 0,
        estimated_towers: int = 0,
        unknown_towers: int = 0,
        peak_period: str = "N/A",
        custom_notes: Optional[str] = None,
    ) -> str:
        """
        Generates a complete multi-section neutral investigation summary report.
        """
        if custom_notes:
            validate_neutral_terminology(custom_notes)

        section_overview = self.generate_device_overview(
            total_records=total_records,
            active_period=active_period,
            primary_operator=primary_operator,
        )
        section_movement = self.generate_movement_patterns(
            total_distance_km=total_distance_km,
            avg_speed_kmh=avg_speed_kmh,
            max_speed_kmh=max_speed_kmh,
            handover_count=handover_count,
            high_velocity_count=high_velocity_count,
        )
        section_towers = self.generate_tower_associations(
            total_towers=total_towers,
            primary_tower_id=primary_tower_id,
            known_count=known_towers,
            estimated_count=estimated_towers,
            unknown_count=unknown_towers,
        )
        section_timeline = self.generate_timeline_narrative(
            first_seen=first_seen,
            first_location=first_location,
            last_seen=last_seen,
            last_location=last_location,
            peak_period=peak_period,
        )

        full_summary = (
            f"=== NEUTRAL INVESTIGATION SUMMARY ===\n\n"
            f"{section_overview}\n\n"
            f"{section_movement}\n\n"
            f"{section_towers}\n\n"
            f"{section_timeline}"
        )

        if custom_notes:
            full_summary += f"\n\nExecutive Notes:\n{custom_notes}"

        return validate_neutral_terminology(full_summary)


# Module-level convenience functions

def generate_device_overview(
    device_id: str,
    total_records: int,
    active_period: str,
    operator: str = "Unknown",
    imei: Optional[str] = None,
    imsi: Optional[str] = None,
    msisdn: Optional[str] = None,
    notes: Optional[str] = None,
) -> str:
    generator = InvestigationSummaryGenerator(target_identifier=device_id)
    return generator.generate_device_overview(
        total_records=total_records,
        active_period=active_period,
        primary_operator=operator,
        imei=imei,
        imsi=imsi,
        msisdn=msisdn,
        notes=notes,
    )


def generate_movement_summary(
    device_id: str,
    total_distance_km: float,
    avg_speed_kmh: float,
    max_speed_kmh: float,
    handover_count: int = 0,
    high_velocity_count: int = 0,
    notes: Optional[str] = None,
) -> str:
    generator = InvestigationSummaryGenerator(target_identifier=device_id)
    return generator.generate_movement_patterns(
        total_distance_km=total_distance_km,
        avg_speed_kmh=avg_speed_kmh,
        max_speed_kmh=max_speed_kmh,
        handover_count=handover_count,
        high_velocity_count=high_velocity_count,
        notes=notes,
    )


def generate_tower_summary(
    device_id: str,
    total_towers: int,
    primary_tower_id: str,
    known_count: int = 0,
    estimated_count: int = 0,
    unknown_count: int = 0,
    notes: Optional[str] = None,
) -> str:
    generator = InvestigationSummaryGenerator(target_identifier=device_id)
    return generator.generate_tower_associations(
        total_towers=total_towers,
        primary_tower_id=primary_tower_id,
        known_count=known_count,
        estimated_count=estimated_count,
        unknown_count=unknown_count,
        notes=notes,
    )


def generate_timeline_summary(
    device_id: str,
    first_seen: str,
    first_location: str,
    last_seen: str,
    last_location: str,
    peak_period: str = "N/A",
    notes: Optional[str] = None,
) -> str:
    generator = InvestigationSummaryGenerator(target_identifier=device_id)
    return generator.generate_timeline_narrative(
        first_seen=first_seen,
        first_location=first_location,
        last_seen=last_seen,
        last_location=last_location,
        peak_period=peak_period,
        notes=notes,
    )
