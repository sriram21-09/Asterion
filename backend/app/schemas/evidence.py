from pydantic import BaseModel, ConfigDict, Field


class EvidenceSummary(BaseModel):
    """Summary statistics of measurement validation."""

    total_measurements: int = Field(
        ..., description="Total measurements submitted for this case", ge=0
    )
    accepted_measurements: int = Field(
        ..., description="Number of measurements passing validation rules", ge=0
    )
    rejected_measurements: int = Field(
        ..., description="Number of measurements failing validation rules", ge=0
    )
    towers_total: int = Field(
        ..., description="Total number of towers in the linked scenario", ge=0
    )
    towers_used_count: int = Field(
        ..., description="Number of unique towers providing accepted measurements", ge=0
    )


class EvidenceTower(BaseModel):
    """Per-tower measurement audit detail."""

    tower_id: str = Field(..., description="Unique tower identifier", examples=["T001"])
    latitude: float = Field(
        ..., description="Tower latitude coordinate (WGS84)", ge=-90.0, le=90.0
    )
    longitude: float = Field(
        ..., description="Tower longitude coordinate (WGS84)", ge=-180.0, le=180.0
    )
    total_measurements: int = Field(
        ..., description="Total measurements associated with this tower", ge=0
    )
    accepted_measurements: int = Field(
        ..., description="Accepted measurements associated with this tower", ge=0
    )
    rejected_measurements: int = Field(
        ..., description="Rejected measurements associated with this tower", ge=0
    )
    status: str = Field(
        ...,
        description="Operational tower status (e.g. 'active', 'inactive', 'insufficient_data')",
    )


class EvidenceRejectionError(BaseModel):
    """A single rejection error detail."""

    field: str = Field(..., description="Name of the invalid schema or data field")
    message: str = Field(
        ..., description="Detailed description of the validation failure"
    )
    code: str = Field(..., description="Structured domain-error code")
    severity: str = Field(..., description="Severity of the violation (error, warning)")


class EvidenceRejection(BaseModel):
    """Details of a rejected measurement."""

    measurement_id: str | None = Field(
        None, description="Unique measurement identifier", examples=["M001"]
    )
    tower_id: str | None = Field(
        None, description="Linked tower identifier", examples=["T001"]
    )
    timestamp: str | None = Field(
        None, description="Timestamp of the rejected measurement"
    )
    errors: list[EvidenceRejectionError] = Field(
        default=[], description="List of reasons for measurement rejection"
    )


class EvidenceConfidence(BaseModel):
    """Confidence data included in evidence packet."""

    confidence_score: float | None = Field(
        None,
        description="Calculated confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    confidence_level: str | None = Field(
        None, description="Qualitative confidence rating (low, medium, high)"
    )
    gdop: float | None = Field(
        None, description="Geometric Dilution of Precision value"
    )
    method: str | None = Field(
        None, description="Method used for confidence evaluation"
    )


class EvidenceResponse(BaseModel):
    """Full evidence audit packet response."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "case_code": "CASE-001",
                "scenario_id": "SCN-001",
                "summary": {
                    "total_measurements": 5,
                    "accepted_measurements": 4,
                    "rejected_measurements": 1,
                    "towers_total": 3,
                    "towers_used_count": 3,
                },
                "towers": [
                    {
                        "tower_id": "T001",
                        "latitude": 12.9716,
                        "longitude": 77.5946,
                        "total_measurements": 2,
                        "accepted_measurements": 2,
                        "rejected_measurements": 0,
                        "status": "active",
                    }
                ],
                "accepted_measurement_ids": ["M001", "M002", "M003", "M004"],
                "rejections": [
                    {
                        "measurement_id": "M005",
                        "tower_id": "T002",
                        "timestamp": "2026-07-19T13:59:00Z",
                        "errors": [
                            {
                                "field": "rssi_dbm",
                                "message": "RSSI value -155.0 dBm is below the thermal noise floor.",
                                "code": "RSSI_OUT_OF_RANGE",
                                "severity": "error",
                            }
                        ],
                    }
                ],
                "confidence": {
                    "confidence_score": 0.82,
                    "confidence_level": "high",
                    "gdop": 2.1,
                    "method": "gdop_covariance",
                },
            }
        },
    )

    case_code: str = Field(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    )
    scenario_id: str | None = Field(
        None, description="The unique Scenario ID if linked", examples=["SCN-001"]
    )
    summary: EvidenceSummary = Field(
        ..., description="Summary statistics of validation results"
    )
    towers: list[EvidenceTower] = Field(
        ..., description="List of per-tower measurement details"
    )
    accepted_measurement_ids: list[str] = Field(
        ..., description="List of IDs of measurements that passed validation"
    )
    rejections: list[EvidenceRejection] = Field(
        ..., description="List of rejected measurements with error details"
    )
    confidence: EvidenceConfidence | None = Field(
        None, description="Confidence evaluation parameters if computed"
    )
    reproducibility_hash: str | None = Field(
        None, description="SHA-256 reproducibility hash for audit trail verification"
    )


class EvidenceAuditResponse(BaseModel):
    """Detailed evidence audit record for compliance and verification."""

    case_code: str = Field(
        ..., description="The unique Case Code (e.g. CASE-001)", examples=["CASE-001"]
    )
    reproducibility_hash: str = Field(
        ..., description="SHA-256 reproducibility hash computed for audit trail"
    )
    solver_version: str = Field(
        ..., description="Version of the solver algorithm used", examples=["1.0.0"]
    )
    input_record_ids: list[str] = Field(
        ...,
        description="Sorted list of input measurement record IDs used in calculation",
    )
    parameter_strings: str = Field(
        ...,
        description="Canonical parameter string used to compute the reproducibility hash",
    )
    summary: EvidenceSummary = Field(
        ..., description="Summary statistics of validation results"
    )
    towers: list[EvidenceTower] = Field(
        ..., description="List of per-tower measurement details"
    )
    rejections: list[EvidenceRejection] = Field(
        ..., description="List of rejected measurements with error details"
    )
    confidence: EvidenceConfidence | None = Field(
        None, description="Confidence evaluation parameters if computed"
    )
    audit_status: str = Field(
        "VERIFIED", description="Status of evidence audit (e.g. 'VERIFIED')"
    )
    generated_at: str = Field(..., description="ISO 8601 timestamp of audit generation")
