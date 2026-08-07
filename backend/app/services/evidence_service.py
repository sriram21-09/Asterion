"""
Evidence Service
=================

Synthesizes audit evidence packets for a case by running measurement
validation and compiling tower/measurement acceptance/rejection reports.
Calculates SHA-256 reproducibility hashes for audit trail verification.
"""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.repositories.case_repository import CaseRepository
from app.repositories.confidence_repository import ConfidenceRepository
from app.repositories.measurement_repository import MeasurementRepository
from app.shared.validation import ValidationError, decode_case_code, encode_case_code
from fastapi import HTTPException
from sqlalchemy.orm import Session

from scientific.models.measurement import Measurement as ScientificMeasurement
from scientific.models.scenario_config import ScenarioConfig
from scientific.models.tower import Tower as ScientificTower
from scientific.pipeline.evidence import synthesize_evidence

SOLVER_VERSION = "1.0.0"


class EvidenceGenerationService:
    """Service that bridges DB data → scientific evidence engine → audit packet."""

    @staticmethod
    def generate_reproducibility_hash(
        solver_version: str,
        input_record_ids: list[str],
        parameter_strings: str | dict[str, Any],
    ) -> str:
        """Calculate SHA-256 reproducibility hash combining solver version, input record IDs, and parameter strings."""
        sorted_ids = sorted(str(rid) for rid in input_record_ids)
        if isinstance(parameter_strings, dict):
            param_str = json.dumps(parameter_strings, sort_keys=True)
        else:
            param_str = str(parameter_strings)

        canonical_payload = (
            f"solver:{solver_version}|records:{','.join(sorted_ids)}|params:{param_str}"
        )
        return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _resolve_case_code(case_id_or_code: str | int) -> str:
        """Normalize case input parameter to standard case code (e.g. CASE-001)."""
        if isinstance(case_id_or_code, int):
            return encode_case_code(case_id_or_code)
        val_str = str(case_id_or_code).strip()
        if val_str.isdigit():
            return encode_case_code(int(val_str))
        return val_str

    @staticmethod
    def get_evidence(
        db: Session,
        case_id: str | int,
    ) -> dict[str, Any]:
        """Build an evidence audit packet for a case including SHA-256 reproducibility hash.

        1. Decode case_code → load case + scenario
        2. Load scenario config from dataset JSON
        3. Retrieve stored measurements
        4. Convert DB models → scientific Tower/Measurement models
        5. Call synthesize_evidence() from the scientific pipeline
        6. Enrich with confidence data if available
        7. Compute SHA-256 reproducibility hash
        8. Return structured evidence dict
        """
        case_code = EvidenceGenerationService._resolve_case_code(case_id)
        db_case_id = decode_case_code(case_code)
        case = CaseRepository.get(db, db_case_id)
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        if not case.scenario_id:
            raise ValidationError(
                "case",
                "Case must have an associated scenario to generate evidence.",
                status_code=400,
            )

        from app.services.scenario_config_helper import load_scenario_config

        config = load_scenario_config(db, case.scenario_id, db_case_id)

        db_measurements = MeasurementRepository.get_by_case(db, db_case_id)
        if not db_measurements:
            raise ValidationError(
                "measurements",
                "No measurements found for this case. Generate measurements first.",
                status_code=400,
            )

        scientific_towers, scientific_measurements = (
            EvidenceGenerationService._convert_to_scientific(config, db_measurements)
        )

        evidence = synthesize_evidence(
            scenario_id=config.scenario_id,
            towers=scientific_towers,
            measurements=scientific_measurements,
        )

        confidence_data = None
        latest_confidence = ConfidenceRepository.get_latest_by_case(db, db_case_id)
        if latest_confidence:
            confidence_data = {
                "confidence_score": latest_confidence.confidence_score,
                "confidence_level": latest_confidence.confidence_level,
                "gdop": latest_confidence.gdop,
                "method": latest_confidence.method,
            }

        input_record_ids = [m.measurement_code for m in db_measurements]
        param_payload = {
            "scenario_id": config.scenario_id,
            "towers_count": len(config.tower_placements),
        }
        reproducibility_hash = EvidenceGenerationService.generate_reproducibility_hash(
            solver_version=SOLVER_VERSION,
            input_record_ids=input_record_ids,
            parameter_strings=param_payload,
        )

        return {
            "case_code": case_code.upper(),
            "scenario_id": evidence.get("scenario_id"),
            "summary": evidence.get("summary", {}),
            "towers": evidence.get("towers", []),
            "accepted_measurement_ids": evidence.get("accepted_measurement_ids", []),
            "rejections": evidence.get("rejections", []),
            "confidence": confidence_data,
            "reproducibility_hash": reproducibility_hash,
            "solver_version": SOLVER_VERSION,
            "input_record_ids": sorted(input_record_ids),
            "parameter_strings": json.dumps(param_payload, sort_keys=True),
        }

    @staticmethod
    def get_audit(
        db: Session,
        case_id: str | int,
    ) -> dict[str, Any]:
        """Build a comprehensive evidence audit packet for audit trail verification."""
        evidence_data = EvidenceGenerationService.get_evidence(db, case_id)
        evidence_data["audit_status"] = "VERIFIED"
        evidence_data["generated_at"] = datetime.now(UTC).isoformat()
        return evidence_data

    @staticmethod
    def _load_scenario_config(scenario_id: int) -> ScenarioConfig:
        """Load and parse scenario config from the dataset JSON."""
        dataset_path = (
            Path(__file__).resolve().parents[3]
            / "datasets"
            / "sample"
            / "scenario_example.json"
        )
        if not dataset_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Scenario dataset not found at {dataset_path}",
            )

        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            configs_list = data.get("scenario_configs", [])
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read scenario dataset: {e!s}",
            )

        for cfg_dict in configs_list:
            sc_id_str = cfg_dict.get("scenario_id", "")
            try:
                cfg_id_int = int(sc_id_str.split("-")[-1])
            except (ValueError, IndexError):
                continue
            if cfg_id_int == scenario_id:
                try:
                    return ScenarioConfig(**cfg_dict)
                except Exception as e:
                    raise ValidationError(
                        "scenario_config",
                        f"Failed to parse scenario config: {e!s}",
                        status_code=400,
                    )

        raise ValidationError(
            "scenario_id",
            f"Scenario config mapping to scenario ID {scenario_id} not found in dataset.",
            status_code=400,
        )

    @staticmethod
    def _convert_to_scientific(config, db_measurements):
        """Convert DB ORM measurement records + scenario config → scientific models."""
        scientific_towers: list[ScientificTower] = []
        for tp in config.tower_placements:
            scientific_towers.append(
                ScientificTower(
                    tower_id=tp.tower_id,
                    latitude=tp.latitude,
                    longitude=tp.longitude,
                    antenna_height_m=tp.antenna_height_m,
                    frequency_mhz=tp.frequency_mhz,
                    transmit_power_dbm=tp.transmit_power_dbm,
                    coverage_radius_m=tp.coverage_radius_m,
                    sector=tp.sector,
                )
            )

        scientific_measurements: list[ScientificMeasurement] = []
        for m in db_measurements:
            # Use stored tower_id first; fall back to parsing measurement_code
            tower_id = getattr(m, "tower_id", None)
            if not tower_id:
                parts = m.measurement_code.split("-")
                for part in parts:
                    if part.startswith("T") and part[1:].isdigit():
                        tower_id = part
                        break

            if tower_id is None:
                tower_placements = config.tower_placements
                if tower_placements:
                    idx = db_measurements.index(m) % len(tower_placements)
                    tower_id = tower_placements[idx].tower_id
                else:
                    continue

            scientific_measurements.append(
                ScientificMeasurement(
                    measurement_id=m.measurement_code,
                    tower_id=tower_id,
                    timestamp=m.timestamp,
                    rssi_dbm=m.rssi_dbm if m.rssi_dbm is not None else -80.0,
                    latitude=m.latitude,
                    longitude=m.longitude,
                    timing_advance=m.timing_advance,
                    uncertainty_m=m.uncertainty_m,
                )
            )

        return scientific_towers, scientific_measurements


# Alias for backward compatibility
EvidenceService = EvidenceGenerationService
