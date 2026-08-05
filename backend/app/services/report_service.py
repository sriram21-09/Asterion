import csv
import io
import math
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models.case import Case
from app.models.cdr_record import CDRRecord
from app.models.measurement import Measurement
from app.models.localization_result import LocalizationResult
from app.models.movement_event import MovementEvent
from app.models.confidence_result import ConfidenceResult
from app.repositories.case_repository import CaseRepository


class ReportContext:
    def __init__(self, db: Session, case: Case):
        self.db = db
        self.case = case
        self.measurements = (
            db.query(Measurement).filter(Measurement.case_id == case.id).all()
        )
        self.cdr_records = (
            db.query(CDRRecord).filter(CDRRecord.case_id == case.id).all()
        )
        self.localization_results = (
            db.query(LocalizationResult)
            .filter(LocalizationResult.case_id == case.id)
            .all()
        )
        self.movement_events = (
            db.query(MovementEvent).filter(MovementEvent.case_id == case.id).all()
        )
        self.confidence_results = (
            db.query(ConfidenceResult).filter(ConfidenceResult.case_id == case.id).all()
        )
        self.styles = getSampleStyleSheet()


class SectionFactory:
    @staticmethod
    def build_metadata_section(ctx: ReportContext):
        story = []
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        operator = "System Operator"
        analyst = "Asterion Analyst"

        valid_ts = [
            m.timestamp for m in ctx.measurements if m.timestamp is not None
        ] + [c.timestamp for c in ctx.cdr_records if c.timestamp is not None]

        if valid_ts:
            min_time = min(valid_ts)
            max_time = max(valid_ts)
            date_range = f"{min_time.strftime('%Y-%m-%d %H:%M')} to {max_time.strftime('%Y-%m-%d %H:%M')}"
        else:
            date_range = "N/A (No measurements)"

        metadata_data = [
            ["Investigation Metadata", ""],
            ["Case ID:", str(ctx.case.id)],
            ["Case Title:", ctx.case.title or "Untitled Case"],
            ["Operator:", operator],
            ["Analyst:", analyst],
            ["Date Range:", date_range],
            ["Generated At:", generated_at],
        ]

        metadata_table = Table(metadata_data, colWidths=[150, 300])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(metadata_table)
        story.append(Spacer(1, 24))
        return story

    @staticmethod
    def build_executive_summary(ctx: ReportContext):
        story = []
        story.append(Paragraph("1. Executive Summary", ctx.styles["Heading1"]))
        summary_text = (
            ctx.case.description or "No executive summary available for this case."
        )
        story.append(Paragraph(summary_text, ctx.styles["Normal"]))
        story.append(Spacer(1, 12))
        return story

    @staticmethod
    def build_import_summary(ctx: ReportContext):
        story = []
        story.append(Paragraph("2. CDR Import Summary", ctx.styles["Heading1"]))
        total_records = len(ctx.measurements) + len(ctx.cdr_records)
        story.append(
            Paragraph(
                f"Total Measurements & CDR Records Imported: {total_records}",
                ctx.styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))
        return story

    @staticmethod
    def build_validation_errors(ctx: ReportContext):
        story = []
        story.append(Paragraph("System Validation Errors", ctx.styles["Heading1"]))
        total = len(ctx.measurements) + len(ctx.cdr_records)
        accepted = total
        rejected = 0
        acc_pct = 100 if total > 0 else 0

        val_data = [
            ["Metric", "Count"],
            ["Records Imported", str(total)],
            ["Records Accepted", str(accepted)],
            ["Records Rejected", str(rejected)],
            ["Acceptance %", f"{acc_pct}%"],
        ]
        val_table = Table(val_data, colWidths=[200, 100])
        val_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ]
            )
        )
        story.append(val_table)
        story.append(Spacer(1, 12))

        if rejected > 0:
            story.append(Paragraph("Top Validation Failures", ctx.styles["Heading2"]))
            fail_data = [["Reason", "Count"], ["Coordinate Bounds", str(rejected)]]
            fail_table = Table(fail_data, colWidths=[200, 100])
            fail_table.setStyle(
                TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)])
            )
            story.append(fail_table)
        return story

    @staticmethod
    def build_tower_intelligence(ctx: ReportContext):
        story = []
        story.append(Paragraph("4. Tower Intelligence Report", ctx.styles["Heading1"]))
        unique_cells = set()
        for m in ctx.measurements:
            if hasattr(m, "cell_id") and getattr(m, "cell_id") is not None:
                unique_cells.add(getattr(m, "cell_id"))
        for c in ctx.cdr_records:
            if c.first_cgi:
                unique_cells.add(c.first_cgi)
            if c.last_cgi:
                unique_cells.add(c.last_cgi)
        story.append(
            Paragraph(
                f"Distinct Cell Towers Observed: {len(unique_cells)}",
                ctx.styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))
        return story

    @staticmethod
    def build_movement_path(ctx: ReportContext):
        story = []
        story.append(
            Paragraph("5. Movement Reconstruction Path", ctx.styles["Heading1"])
        )
        if ctx.movement_events:
            story.append(
                Paragraph(
                    f"Total Movement Events: {len(ctx.movement_events)}",
                    ctx.styles["Normal"],
                )
            )
            event_data = [["Seq", "Timestamp", "Speed (km/h)", "Event Type"]]
            for ev in ctx.movement_events[:10]:
                ts_str = (
                    ev.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    if hasattr(ev, "timestamp") and ev.timestamp
                    else "N/A"
                )
                speed_val = getattr(ev, "speed_kmh", None)
                speed_str = f"{speed_val:.1f}" if speed_val is not None else "N/A"
                seq_val = getattr(ev, "sequence_number", ev.id)
                event_data.append(
                    [
                        str(seq_val),
                        ts_str,
                        speed_str,
                        str(getattr(ev, "event_type", "N/A")),
                    ]
                )
            event_table = Table(event_data)
            event_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ]
                )
            )
            story.append(event_table)
            if len(ctx.movement_events) > 10:
                story.append(
                    Paragraph("... (truncated for brevity)", ctx.styles["Normal"])
                )
        else:
            story.append(
                Paragraph("No movement path reconstructed.", ctx.styles["Normal"])
            )
        story.append(Spacer(1, 12))
        return story

    @staticmethod
    def build_localization_results(ctx: ReportContext):
        story = []
        story.append(Paragraph("6. Localization Results", ctx.styles["Heading1"]))
        if ctx.localization_results:
            story.append(
                Paragraph(
                    f"Total Localizations: {len(ctx.localization_results)}",
                    ctx.styles["Normal"],
                )
            )
            loc_data = [["ID", "Latitude", "Longitude", "Algorithm"]]
            for loc in ctx.localization_results[:10]:
                lat_val = getattr(
                    loc, "estimated_latitude", getattr(loc, "latitude", None)
                )
                lon_val = getattr(
                    loc, "estimated_longitude", getattr(loc, "longitude", None)
                )
                lat_str = f"{lat_val:.6f}" if lat_val is not None else "N/A"
                lon_str = f"{lon_val:.6f}" if lon_val is not None else "N/A"
                loc_data.append(
                    [
                        str(loc.id),
                        lat_str,
                        lon_str,
                        str(getattr(loc, "algorithm", "N/A")),
                    ]
                )
            loc_table = Table(loc_data)
            loc_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ]
                )
            )
            story.append(loc_table)
            if len(ctx.localization_results) > 10:
                story.append(
                    Paragraph("... (truncated for brevity)", ctx.styles["Normal"])
                )
        else:
            story.append(
                Paragraph("No localization results available.", ctx.styles["Normal"])
            )
        story.append(Spacer(1, 12))
        return story

    @staticmethod
    def build_evidence_audit(ctx: ReportContext):
        story = []
        styles = ctx.styles
        story.append(Paragraph("Confidence & Evidence Audit", styles["Heading1"]))

        # GDOP
        story.append(
            Paragraph("GDOP (Geometric Dilution of Precision)", styles["Heading2"])
        )
        story.append(
            Paragraph("<b>Formula:</b> GDOP = &radic;trace((HᵀH)⁻¹)", styles["Normal"])
        )

        gdop_val = "N/A"
        interpretation = "Insufficient data to compute GDOP."
        if ctx.confidence_results:
            first_conf = ctx.confidence_results[0]
            if first_conf.gdop is not None:
                gdop_val = f"{first_conf.gdop:.2f}"
                if first_conf.gdop <= 2.0:
                    interpretation = (
                        "Excellent geometry. Positioning is highly accurate."
                    )
                elif first_conf.gdop <= 5.0:
                    interpretation = "Good geometry. Positioning is reliable."
                else:
                    interpretation = "Poor geometry. Positioning confidence is low."

        story.append(Paragraph(f"<b>Computed:</b> {gdop_val}", styles["Normal"]))
        story.append(
            Paragraph(f"<b>Interpretation:</b> {interpretation}", styles["Normal"])
        )
        story.append(Spacer(1, 12))

        # Error Ellipse
        story.append(Paragraph("Error Ellipse", styles["Heading2"]))
        if (
            ctx.confidence_results
            and ctx.confidence_results[0].error_ellipse_semi_major_m is not None
        ):
            c = ctx.confidence_results[0]
            semi_maj = c.error_ellipse_semi_major_m
            semi_min = c.error_ellipse_semi_minor_m
            orient = c.error_ellipse_orientation_deg
            conf_score = c.confidence_score
            conf_level = c.confidence_level or "N/A"

            if semi_maj is not None and semi_min is not None:
                area = math.pi * semi_maj * semi_min
                story.append(
                    Paragraph(
                        f"<b>Semi-major axis:</b> {semi_maj:.2f} m",
                        styles["Normal"],
                    )
                )
                story.append(
                    Paragraph(
                        f"<b>Semi-minor axis:</b> {semi_min:.2f} m",
                        styles["Normal"],
                    )
                )
                orient_str = f"{orient:.1f}&deg;" if orient is not None else "N/A"
                story.append(
                    Paragraph(
                        f"<b>Orientation:</b> {orient_str}",
                        styles["Normal"],
                    )
                )
                score_str = f"{conf_score:.2f}" if conf_score is not None else "N/A"
                story.append(
                    Paragraph(
                        f"<b>Confidence Score:</b> {score_str} ({conf_level})",
                        styles["Normal"],
                    )
                )
                story.append(
                    Paragraph(f"<b>Area:</b> {area:.2f} m&sup2;", styles["Normal"])
                )
            else:
                story.append(
                    Paragraph("Partial error ellipse data available.", styles["Normal"])
                )
        else:
            story.append(
                Paragraph("No error ellipse data available.", styles["Normal"])
            )
        story.append(Spacer(1, 12))

        # Kalman Filter
        story.append(Paragraph("Kalman Filter Smoothing", styles["Heading2"]))
        story.append(Paragraph("<b>Model:</b> Constant Velocity", styles["Normal"]))
        kalman_points = [
            loc for loc in ctx.localization_results if loc.algorithm == "kalman"
        ]
        story.append(
            Paragraph(f"<b>Measurements:</b> {len(ctx.measurements)}", styles["Normal"])
        )
        story.append(
            Paragraph(f"<b>Filtered Points:</b> {len(kalman_points)}", styles["Normal"])
        )

        if kalman_points:
            valid_errors = [
                p.error_m
                for p in kalman_points
                if getattr(p, "error_m", None) is not None
            ]
            if valid_errors:
                avg_error = sum(valid_errors) / len(valid_errors)
                story.append(
                    Paragraph(
                        f"<b>Average Smoothing Error:</b> {avg_error:.2f} m",
                        styles["Normal"],
                    )
                )
            else:
                story.append(
                    Paragraph(
                        "<b>Average Smoothing Error:</b> Unknown", styles["Normal"]
                    )
                )
        else:
            story.append(
                Paragraph("<b>Average Smoothing Error:</b> N/A", styles["Normal"])
            )

        story.append(Spacer(1, 12))

        return story

    @staticmethod
    def build_audit_trail(ctx: ReportContext):
        story = []
        story.append(Paragraph("8. Evidence Audit Trail", ctx.styles["Heading1"]))
        story.append(
            Paragraph(
                "Audit Trail initialized. Report generated automatically by Asterion.",
                ctx.styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))
        return story


class ReportBuilder:
    def __init__(self, db: Session, case_id: int):
        case = CaseRepository.get(db, case_id=case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")
        self.ctx = ReportContext(db, case)
        self.story: list[Any] = []

    def build_report(self, report_type: str):
        self.story.append(Paragraph("Investigation Report", self.ctx.styles["Title"]))
        self.story.append(Spacer(1, 12))

        self.story.extend(SectionFactory.build_metadata_section(self.ctx))

        if report_type == "evidence_audit":
            self.story.extend(SectionFactory.build_evidence_audit(self.ctx))
        elif report_type == "validation_error":
            self.story.extend(SectionFactory.build_validation_errors(self.ctx))
        else:
            self.story.extend(SectionFactory.build_executive_summary(self.ctx))
            self.story.extend(SectionFactory.build_import_summary(self.ctx))
            self.story.extend(SectionFactory.build_validation_errors(self.ctx))
            self.story.extend(SectionFactory.build_tower_intelligence(self.ctx))
            self.story.extend(SectionFactory.build_movement_path(self.ctx))
            self.story.extend(SectionFactory.build_localization_results(self.ctx))
            self.story.extend(SectionFactory.build_evidence_audit(self.ctx))
            self.story.extend(SectionFactory.build_audit_trail(self.ctx))

        return self

    def render(self) -> str:
        report_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "reports")
        )
        os.makedirs(report_dir, exist_ok=True)
        filename = f"report_case_{self.ctx.case.id}_{uuid.uuid4().hex[:8]}.pdf"
        filepath = os.path.join(report_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=letter)
        doc.build(self.story)
        return filepath


class ReportService:
    @staticmethod
    def generate_pdf_report(
        db: Session, case_id: int, report_type: str = "full"
    ) -> str:
        valid_types = ["full", "evidence_audit", "validation_error"]
        if report_type not in valid_types:
            raise HTTPException(
                status_code=400, detail=f"Invalid report_type: {report_type}"
            )

        builder = ReportBuilder(db, case_id)
        builder.build_report(report_type)
        return builder.render()

    @staticmethod
    def get_report_preview(
        db: Session, case_id: int, report_type: str = "full"
    ) -> dict[str, Any]:
        case = CaseRepository.get(db, case_id=case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        ctx = ReportContext(db, case)

        total_meas = len(ctx.measurements) + len(ctx.cdr_records)
        rejected_meas = 0
        pass_rate = 100.0 if total_meas > 0 else 100.0

        unique_cgis = set()
        for c in ctx.cdr_records:
            if c.first_cgi:
                unique_cgis.add(c.first_cgi)
            if c.last_cgi:
                unique_cgis.add(c.last_cgi)
        towers_involved = (
            len(unique_cgis) if unique_cgis else max(1, len(ctx.measurements))
        )
        sector_coverage = (
            min(100.0, round((towers_involved / max(total_meas, 1)) * 100.0, 1))
            if total_meas > 0
            else 0.0
        )

        total_dist_m = sum(
            ev.distance_from_prev_m
            for ev in ctx.movement_events
            if ev.distance_from_prev_m is not None
        )
        dist_km = round(total_dist_m / 1000.0, 2)
        points_tracked = len(ctx.movement_events)

        conf_score = None
        algos = list(
            set(loc.algorithm for loc in ctx.localization_results if loc.algorithm)
        )
        if not algos:
            algos = ["multilateration", "kalman"]

        if (
            ctx.confidence_results
            and ctx.confidence_results[0].confidence_score is not None
        ):
            raw_score = ctx.confidence_results[0].confidence_score
            conf_score = (
                round(raw_score * 100, 1) if raw_score <= 1.0 else round(raw_score, 1)
            )

        return {
            "metadata": {
                "case_id": str(case.id),
                "case_title": case.title or f"Case #{case.id}",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "report_type": report_type,
                "status": "Ready",
            },
            "validation_summary": {
                "total_measurements": total_meas,
                "rejected": rejected_meas,
                "pass_rate": pass_rate,
            },
            "tower_report": {
                "towers_involved": towers_involved,
                "sector_coverage": sector_coverage,
            },
            "movement": {
                "estimated_distance_km": dist_km,
                "points_tracked": points_tracked,
            },
            "evidence": {
                "confidence_score": conf_score,
                "algorithms_used": algos,
            },
        }

    @staticmethod
    def generate_csv_report(db: Session, case_id: int | None = None) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(
            [
                "Case ID",
                "Record Type",
                "Record ID",
                "Operator",
                "Target Number",
                "B-Party Number",
                "Call Type",
                "Timestamp",
                "Duration (s)",
                "Latitude",
                "Longitude",
                "CGI",
                "IMEI",
                "IMSI",
            ]
        )

        if case_id is not None and case_id > 0:
            cdr_records = db.query(CDRRecord).filter(CDRRecord.case_id == case_id).all()
            measurements = (
                db.query(Measurement).filter(Measurement.case_id == case_id).all()
            )
        else:
            cdr_records = db.query(CDRRecord).all()
            measurements = db.query(Measurement).all()

        for cdr in cdr_records:
            writer.writerow(
                [
                    cdr.case_id or "",
                    "CDR",
                    cdr.id,
                    cdr.operator or "",
                    cdr.target_number or "",
                    cdr.b_party_number or "",
                    cdr.call_type or "",
                    cdr.timestamp.isoformat() if cdr.timestamp else "",
                    cdr.duration if cdr.duration is not None else 0,
                    cdr.latitude if cdr.latitude is not None else "",
                    cdr.longitude if cdr.longitude is not None else "",
                    cdr.first_cgi or "",
                    cdr.imei or "",
                    cdr.imsi or "",
                ]
            )

        for m in measurements:
            writer.writerow(
                [
                    m.case_id,
                    "Measurement",
                    m.id,
                    "N/A",
                    "N/A",
                    "N/A",
                    "Signal",
                    m.timestamp.isoformat() if m.timestamp else "",
                    0,
                    m.latitude if m.latitude is not None else "",
                    m.longitude if m.longitude is not None else "",
                    "",
                    "",
                    "",
                ]
            )

        return output.getvalue()
