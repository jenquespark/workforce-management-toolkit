from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

UTC_MIN_DATETIME = datetime(2020, 1, 1, tzinfo=UTC)


@dataclass(frozen=True)
class WFMData:
    """Canonical WFM time-series data point.

    ``timestamp`` should be timezone-aware when available; naive datetimes are
    accepted for local-time series but callers should be consistent.
    """

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


@dataclass(frozen=True)
class StaffingRequest:
    """Explicit business inputs for an Erlang C staffing calculation.

    All fields follow the units of the upstream pyworkforce ``ErlangC`` API:

    transactions : total number of transactions arriving in the interval
    aht          : average handling time of a transaction, in MINUTES
    asa          : required average speed of answer, in MINUTES
    interval_min : interval length, in MINUTES
    service_level: target service level, fraction in [0, 1]
    max_occupancy: max fraction of time a transaction occupies a position, in (0, 1]
    shrinkage    : fraction of time an operator is unavailable, in [0, 1)
    """

    transactions: float
    aht: float
    asa: float
    interval_min: int
    service_level: float = 0.80
    max_occupancy: float = 0.85
    shrinkage: float = 0.0


@dataclass(frozen=True)
class StaffingResult:
    """Result from a staffing (Erlang C) operation."""

    algorithm: str
    raw_positions: int
    positions: int
    service_level: float
    occupancy: float
    waiting_probability: float
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def allocations(self) -> dict[str, list[int]]:
        """Backwards-compatible view: positions per (single) period."""
        return {"period_0": [self.positions]}

    @property
    def metrics(self) -> dict[str, float]:
        """Backwards-compatible view of the scalar metrics."""
        return {
            "raw_positions": float(self.raw_positions),
            "positions": float(self.positions),
            "service_level": float(self.service_level),
            "occupancy": float(self.occupancy),
            "waiting_probability": float(self.waiting_probability),
        }
