from typing import List

from pydantic import BaseModel, ConfigDict, Field


class BenchmarkMetric(BaseModel):
    """Represents a single pipeline validation benchmark metric."""

    metric_name: str = Field(..., description="Name of the benchmark metric")
    value: float = Field(..., description="Calculated value for the case")
    threshold: float = Field(..., description="Configured threshold for passing")
    passed: bool = Field(..., description="Whether the metric meets or exceeds the threshold")


class BenchmarkResponse(BaseModel):
    """Structured response containing all benchmark metrics for a case."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "case_passed": True,
                "metrics": [
                    {
                        "metric_name": "Validation Pass Rate",
                        "value": 100.0,
                        "threshold": 90.0,
                        "passed": True,
                    },
                    {
                        "metric_name": "Tower Resolution Rate",
                        "value": 100.0,
                        "threshold": 80.0,
                        "passed": True,
                    },
                    {
                        "metric_name": "Unknown Tower Percentage",
                        "value": 0.0,
                        "threshold": 20.0,
                        "passed": True,
                    },
                    {
                        "metric_name": "Kalman Improvement Factor",
                        "value": 1.5,
                        "threshold": 1.2,
                        "passed": True,
                    }
                ]
            }
        }
    )

    case_passed: bool = Field(..., description="True if all configured benchmark metrics passed")
    metrics: List[BenchmarkMetric] = Field(..., description="List of individual benchmark metrics")
