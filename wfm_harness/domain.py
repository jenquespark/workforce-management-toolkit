from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import yaml
from pydantic import BaseModel, validator
import json
from datetime import datetime

class OperatingProfile(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BLENDED = "blended"

class Direction(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BLENDED = "blended"

@dataclass
class WFMData:
    """Canonical WFM data container with type safety."""
    timestamp: datetime
    value: Union[int, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @validator('value')
    def validate_value(cls, v):
        if v is None:
            raise ValueError("Value cannot be None")
        return v
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WFMData":
        """Create WFMData from dictionary."""
        if isinstance(data.get("timestamp"), str):
            timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        else:
            timestamp = data.get("timestamp")
        return cls(
            timestamp=timestamp,
            value=data.get("value"),
            metadata=data.get("metadata", {})
        )

@dataclass
class ForecastResult:
    """Result from forecasting operations."""
    model_type: str
    predictions: List[WFMData]
    confidence_intervals: Optional[List[Dict[str, float]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StaffingResult:
    """Result from staffing operations."""
    algorithm: str
    allocations: Dict[str, List[int]]
    metrics: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScheduleResult:
    """Result from scheduling operations."""
    solver: str
    roster: Dict[str, List[Dict[str, Any]]]
    constraints_satisfied: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationResult:
    """Result from optimization operations."""
    optimizer: str
    objective_value: float
    solution: Dict[str, Any]
    iterations: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    """Result from validation operations."""
    validator: str
    passed: bool
    violations: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

# Type aliases for better readability
ForecastResultType = ForecastResult
StaffingResultType = StaffingResult
ScheduleResultType = ScheduleResult
OptimizationResultType = OptimizationResult
ValidationResultType = ValidationResult
