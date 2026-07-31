"""
Report Data Formatter & Validation Summary Engine
===================================================

Transforms raw scientific pipeline outputs into structured, report-ready
data dictionaries suitable for PDF report generation.

All generated text complies with Section 3F neutral terminology standards.
Prohibited terms (suspect, criminal, perpetrator, guilty party) will raise
``ValueError`` if detected in any user-supplied text field.

Consumed Upstream Modules:
    - ``scientific.pipeline.movement.MovementSummary``
    - ``scientific.models.result.ConfidenceResult``
    - ``scientific.models.result.LocalizationResult``
    - ``scientific.pipeline.summary_generator.InvestigationSummaryGenerator``
    - ``scientific.pipeline.summary_generator.validate_neutral_terminology``
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from scientific.models.result import ConfidenceResult, LocalizationResult
from scientific.pipeline.movement import MovementSummary
from scientific.pipeline.summary_generator import (
    InvestigationSummaryGenerator,
    validate_neutral_terminology,
)


class ReportFormatter:
    """Formats pipeline outputs into report-ready data structures.

    Each ``format_*`` method returns a dictionary whose keys match the
    expected report schema for the corresponding PDF section.  All
    human-readable text is validated against Section 3F neutral
    terminology before inclusion.

    Usage::

        formatter = ReportFormatter()
        validation = formatter.format_validation_summary(records_by_operator)
        tower_intel = formatter.format_tower_intelligence_summary(tower_data)
        full_report = formatter.format_full_report(...)
    """

    # ------------------------------------------------------------------
    # 1. Validation Summary
    # ------------------------------------------------------------------

    def format_validation_summary(
        self,
        records_by_operator: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Format a per-operator validation summary table.

        Args:
            records_by_operator: A list of dicts, each containing:
                - ``operator`` (str): Operator name (e.g. Airtel, BSNL).
                - ``records_imported`` (int): Total records ingested.
                - ``records_validated`` (int): Records passing validation.
                - ``records_rejected`` (int): Records failing validation.
                - ``warnings_count`` (int): Warning-level findings.

        Returns:
            A dictionary with ``operator_rows`` (list) and ``totals`` (dict).
        """
        if not records_by_operator:
            return {
                "section": "Validation Summary",
                "operator_rows": [],
                "totals": {
                    "records_imported": 0,
                    "records_validated": 0,
                    "records_rejected": 0,
                    "warnings_count": 0,
                },
            }

        rows: list[dict[str, Any]] = []
        total_imported = 0
        total_validated = 0
        total_rejected = 0
        total_warnings = 0

        for entry in records_by_operator:
            operator = str(entry.get("operator", "Unknown"))
            validate_neutral_terminology(operator)

            imported = int(entry.get("records_imported", 0))
            validated = int(entry.get("records_validated", 0))
            rejected = int(entry.get("records_rejected", 0))
            warnings = int(entry.get("warnings_count", 0))

            rows.append(
                {
                    "operator": operator,
                    "records_imported": imported,
                    "records_validated": validated,
                    "records_rejected": rejected,
                    "warnings_count": warnings,
                }
            )

            total_imported += imported
            total_validated += validated
            total_rejected += rejected
            total_warnings += warnings

        return {
            "section": "Validation Summary",
            "operator_rows": rows,
            "totals": {
                "records_imported": total_imported,
                "records_validated": total_validated,
                "records_rejected": total_rejected,
                "warnings_count": total_warnings,
            },
        }

    # ------------------------------------------------------------------
    # 2. Tower Intelligence Summary
    # ------------------------------------------------------------------

    def format_tower_intelligence_summary(
        self,
        tower_data: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Format tower coordinate resolution intelligence summary.

        Each tower entry should contain:
            - ``tower_id`` (str): Unique tower identifier.
            - ``resolution_method`` (str): One of ``'exact'``, ``'prefix_lac'``,
              ``'prefix_mnc'``, ``'prefix_mcc'``, ``'unresolved'``.

        Resolution methods are classified as:
            - **Known**: ``exact``
            - **Estimated**: ``prefix_lac``, ``prefix_mnc``, ``prefix_mcc``
            - **Unknown**: ``unresolved`` or missing

        Returns:
            A dictionary with Known/Estimated/Unknown counts and percentages.
        """
        known_count = 0
        estimated_count = 0
        unknown_count = 0

        for tower in tower_data:
            method = str(tower.get("resolution_method", "unresolved")).lower()
            if method == "exact":
                known_count += 1
            elif method in ("prefix_lac", "prefix_mnc", "prefix_mcc"):
                estimated_count += 1
            else:
                unknown_count += 1

        total = known_count + estimated_count + unknown_count

        def _pct(count: int) -> float:
            if total == 0:
                return 0.0
            return round((count / total) * 100.0, 2)

        return {
            "section": "Tower Intelligence Summary",
            "total_towers": total,
            "known": {
                "count": known_count,
                "percentage": _pct(known_count),
                "label": "Known (exact site coordinates)",
            },
            "estimated": {
                "count": estimated_count,
                "percentage": _pct(estimated_count),
                "label": "Estimated (resolved via secondary lookups)",
            },
            "unknown": {
                "count": unknown_count,
                "percentage": _pct(unknown_count),
                "label": "Unknown (unresolved coordinates)",
            },
        }

    # ------------------------------------------------------------------
    # 3. Movement Reconstruction Summary
    # ------------------------------------------------------------------

    def format_movement_reconstruction_summary(
        self,
        movement_summary: MovementSummary,
    ) -> dict[str, Any]:
        """Format movement reconstruction metrics for report consumption.

        Consumes the existing ``MovementSummary`` dataclass produced by
        ``reconstruct_movement_events()``.

        Returns:
            A dictionary with distance, speed, handover, and velocity
            distribution statistics.
        """
        return {
            "section": "Movement Reconstruction Summary",
            "total_events": movement_summary.total_events,
            "total_distance_km": movement_summary.total_distance_km,
            "total_distance_m": movement_summary.total_distance_m,
            "time_span_seconds": movement_summary.time_span_seconds,
            "handover_count": movement_summary.handover_count,
            "anomaly_count": movement_summary.anomaly_count,
            "speed_statistics": {
                "average_speed_kmh": movement_summary.avg_speed_kmh,
                "max_speed_kmh": movement_summary.max_speed_kmh,
            },
            "velocity_distribution": dict(movement_summary.velocity_distribution),
        }

    # ------------------------------------------------------------------
    # 4. Localization & Confidence Summary
    # ------------------------------------------------------------------

    def format_localization_summary(
        self,
        confidence_result: ConfidenceResult,
        localization_result: LocalizationResult,
    ) -> dict[str, Any]:
        """Format localization and confidence metrics for report consumption.

        Args:
            confidence_result: Output of ``compute_confidence()``.
            localization_result: Output of the localization algorithm.

        Returns:
            A dictionary with confidence classification, GDOP, error ellipse
            parameters, and algorithm metadata.
        """
        return {
            "section": "Localization & Confidence Summary",
            "confidence": {
                "score": confidence_result.confidence_score,
                "level": confidence_result.confidence_level,
                "method": confidence_result.method,
                "gdop": confidence_result.gdop,
            },
            "error_ellipse": {
                "semi_major_m": confidence_result.error_ellipse_semi_major_m,
                "semi_minor_m": confidence_result.error_ellipse_semi_minor_m,
                "orientation_deg": confidence_result.error_ellipse_orientation_deg,
            },
            "localization": {
                "algorithm": localization_result.algorithm,
                "estimated_latitude": localization_result.estimated_latitude,
                "estimated_longitude": localization_result.estimated_longitude,
                "error_m": localization_result.error_m,
                "signals_used": localization_result.signals_used,
            },
        }

    # ------------------------------------------------------------------
    # 5. Investigation Narrative
    # ------------------------------------------------------------------

    def format_investigation_narrative(
        self,
        target_identifier: str,
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
    ) -> dict[str, Any]:
        """Generate the full investigation narrative and wrap in a report dict.

        Delegates text generation to
        ``InvestigationSummaryGenerator.generate_full_investigation_summary()``
        and returns the result in a structured dictionary with individual
        section text blocks.

        All text is validated for neutral terminology compliance.

        Returns:
            A dictionary with the full narrative and individual section texts.
        """
        generator = InvestigationSummaryGenerator(
            target_identifier=target_identifier,
        )

        full_narrative = generator.generate_full_investigation_summary(
            total_records=total_records,
            active_period=active_period,
            total_distance_km=total_distance_km,
            avg_speed_kmh=avg_speed_kmh,
            max_speed_kmh=max_speed_kmh,
            total_towers=total_towers,
            primary_tower_id=primary_tower_id,
            first_seen=first_seen,
            first_location=first_location,
            last_seen=last_seen,
            last_location=last_location,
            primary_operator=primary_operator,
            handover_count=handover_count,
            high_velocity_count=high_velocity_count,
            known_towers=known_towers,
            estimated_towers=estimated_towers,
            unknown_towers=unknown_towers,
            peak_period=peak_period,
            custom_notes=custom_notes,
        )

        # Generate individual sections for granular access
        device_overview = generator.generate_device_overview(
            total_records=total_records,
            active_period=active_period,
            primary_operator=primary_operator,
        )
        movement_patterns = generator.generate_movement_patterns(
            total_distance_km=total_distance_km,
            avg_speed_kmh=avg_speed_kmh,
            max_speed_kmh=max_speed_kmh,
            handover_count=handover_count,
            high_velocity_count=high_velocity_count,
        )
        tower_associations = generator.generate_tower_associations(
            total_towers=total_towers,
            primary_tower_id=primary_tower_id,
            known_count=known_towers,
            estimated_count=estimated_towers,
            unknown_count=unknown_towers,
        )
        timeline_narrative = generator.generate_timeline_narrative(
            first_seen=first_seen,
            first_location=first_location,
            last_seen=last_seen,
            last_location=last_location,
            peak_period=peak_period,
        )

        return {
            "section": "Investigation Narrative",
            "full_narrative": full_narrative,
            "sections": {
                "device_overview": device_overview,
                "movement_patterns": movement_patterns,
                "tower_associations": tower_associations,
                "timeline_narrative": timeline_narrative,
            },
        }

    # ------------------------------------------------------------------
    # 6. Full Report Assembly
    # ------------------------------------------------------------------

    def format_full_report(
        self,
        *,
        records_by_operator: list[dict[str, Any]],
        tower_data: list[dict[str, Any]],
        movement_summary: MovementSummary,
        confidence_result: ConfidenceResult,
        localization_result: LocalizationResult,
        target_identifier: str,
        total_records: int,
        active_period: str,
        total_towers: int,
        primary_tower_id: str,
        first_seen: str,
        first_location: str,
        last_seen: str,
        last_location: str,
        primary_operator: str = "Unknown",
        high_velocity_count: int = 0,
        known_towers: int = 0,
        estimated_towers: int = 0,
        unknown_towers: int = 0,
        peak_period: str = "N/A",
        custom_notes: Optional[str] = None,
        report_title: str = "Asterion CDR Analysis Report",
    ) -> dict[str, Any]:
        """Assemble a complete report-ready data structure from all pipeline outputs.

        Aggregates all individual section formatters into a single dictionary
        with ``report_metadata``, ``validation_summary``, ``tower_intelligence``,
        ``movement_reconstruction``, ``localization_confidence``, and
        ``investigation_narrative`` top-level keys.

        Args:
            records_by_operator: Per-operator validation records.
            tower_data: Tower resolution data with resolution methods.
            movement_summary: Output of ``reconstruct_movement_events()``.
            confidence_result: Output of ``compute_confidence()``.
            localization_result: Output of the localization algorithm.
            target_identifier: Neutral device identifier string.
            total_records: Total CDR records analyzed.
            active_period: Date range of activity.
            total_towers: Total unique towers observed.
            primary_tower_id: Most-associated tower ID.
            first_seen: Timestamp of first observation.
            first_location: Location of first observation.
            last_seen: Timestamp of last observation.
            last_location: Location of last observation.
            primary_operator: Primary network operator name.
            high_velocity_count: Count of anomalous velocity events.
            known_towers: Count of exactly resolved towers.
            estimated_towers: Count of estimated-coordinate towers.
            unknown_towers: Count of unresolved towers.
            peak_period: Peak activity time window.
            custom_notes: Optional executive notes (validated for terminology).
            report_title: Title for the report header.

        Returns:
            A complete report dictionary with all sections.
        """
        validate_neutral_terminology(report_title)

        return {
            "report_metadata": {
                "title": report_title,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "target_identifier": target_identifier,
                "scenario_id": localization_result.scenario_id,
            },
            "validation_summary": self.format_validation_summary(
                records_by_operator,
            ),
            "tower_intelligence": self.format_tower_intelligence_summary(
                tower_data,
            ),
            "movement_reconstruction": self.format_movement_reconstruction_summary(
                movement_summary,
            ),
            "localization_confidence": self.format_localization_summary(
                confidence_result,
                localization_result,
            ),
            "investigation_narrative": self.format_investigation_narrative(
                target_identifier=target_identifier,
                total_records=total_records,
                active_period=active_period,
                total_distance_km=movement_summary.total_distance_km,
                avg_speed_kmh=movement_summary.avg_speed_kmh,
                max_speed_kmh=movement_summary.max_speed_kmh,
                total_towers=total_towers,
                primary_tower_id=primary_tower_id,
                first_seen=first_seen,
                first_location=first_location,
                last_seen=last_seen,
                last_location=last_location,
                primary_operator=primary_operator,
                handover_count=movement_summary.handover_count,
                high_velocity_count=high_velocity_count,
                known_towers=known_towers,
                estimated_towers=estimated_towers,
                unknown_towers=unknown_towers,
                peak_period=peak_period,
                custom_notes=custom_notes,
            ),
        }


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------


def format_full_report(
    *,
    records_by_operator: list[dict[str, Any]],
    tower_data: list[dict[str, Any]],
    movement_summary: MovementSummary,
    confidence_result: ConfidenceResult,
    localization_result: LocalizationResult,
    target_identifier: str,
    total_records: int,
    active_period: str,
    total_towers: int,
    primary_tower_id: str,
    first_seen: str,
    first_location: str,
    last_seen: str,
    last_location: str,
    primary_operator: str = "Unknown",
    high_velocity_count: int = 0,
    known_towers: int = 0,
    estimated_towers: int = 0,
    unknown_towers: int = 0,
    peak_period: str = "N/A",
    custom_notes: Optional[str] = None,
    report_title: str = "Asterion CDR Analysis Report",
) -> dict[str, Any]:
    """Module-level convenience wrapper for ``ReportFormatter.format_full_report()``.

    See :meth:`ReportFormatter.format_full_report` for full argument documentation.
    """
    formatter = ReportFormatter()
    return formatter.format_full_report(
        records_by_operator=records_by_operator,
        tower_data=tower_data,
        movement_summary=movement_summary,
        confidence_result=confidence_result,
        localization_result=localization_result,
        target_identifier=target_identifier,
        total_records=total_records,
        active_period=active_period,
        total_towers=total_towers,
        primary_tower_id=primary_tower_id,
        first_seen=first_seen,
        first_location=first_location,
        last_seen=last_seen,
        last_location=last_location,
        primary_operator=primary_operator,
        high_velocity_count=high_velocity_count,
        known_towers=known_towers,
        estimated_towers=estimated_towers,
        unknown_towers=unknown_towers,
        peak_period=peak_period,
        custom_notes=custom_notes,
        report_title=report_title,
    )
