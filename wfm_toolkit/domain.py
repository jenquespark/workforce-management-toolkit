from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class WFMData:
    """Canonical WFM data container."""

    timestamp: datetime
    value: int | float
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WFMData:
        """Create WFMData from a dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return cls(
            timestamp=timestamp,
            value=data.get("value"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ForecastResult:
    """Result from forecasting operations."""

    model_type: str
    predictions: list[WFMData]
    confidence_intervals: list[dict[str, float]] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StaffingResult:
    """Result from staffing operations."""

    algorithm: str
    allocations: dict[str, list[int]]
    metrics: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleResult:
    """Result from scheduling operations."""

    solver: str
    roster: dict[str, list[dict[str, Any]]]
    constraints_satisfied: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Result from optimization operations."""

    optimizer: str
    objective_value: float
    solution: dict[str, Any]
    iterations: int
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result from validation operations."""

    validator: str
    passed: bool
    violations: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
