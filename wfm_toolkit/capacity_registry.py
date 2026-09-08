"""Workforce Management Toolkit configuration and capability registry.

Central configuration management with Pydantic validation and
capability definitions for the WFM toolchain.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator


class OperatingProfile(str, Enum):
    """Operating profile types for workforce management."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BLENDED = "blended"


class WFMDataSchema(BaseModel):
    """Pydantic schema for WFM data validation."""

    timestamp: datetime = Field(..., gt=datetime(2020, 1, 1))
    value: float = Field(..., gt=0, lt=1000000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WFMConfig(BaseModel):
    """Configuration for WFM operations with validation."""

    operating_profile: OperatingProfile = Field(default=OperatingProfile.BLENDED)
    interval_minutes: int = Field(default=60, ge=15, le=1440)
    service_level: float = Field(default=0.8, ge=0, le=1)
    average_speed_of_answer: int = Field(default=180, ge=0)
    shrinkage_rate: float = Field(default=0.3, ge=0, le=1)
    half_occupancy: float = Field(default=0.85, gt=0, le=1)
    hours_per_agent: float = Field(default=7.5, gt=0)
    average_handle_time: int = Field(default=180, ge=0)

    @validator("value")
    def validate_value_positive(cls, v):
        if v <= 0:
            raise ValueError("Value must be positive")
        if v > 1000000:
            raise ValueError("Value exceeds maximum allowed")
        return v

    @validator("service_level")
    def validate_service_level_range(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Service level must be between 0 and 1")
        return v

    @validator("shrinkage_rate")
    def validate_shrinkage_range(cls, v):
        if not 0 <= v < 1:
            raise ValueError("Shrinkage rate must be between 0 and 1")
        return v

    @validator("half_occupancy")
    def validate_half_occupancy_range(cls, v):
        if not 0 < v <= 1:
            raise ValueError("Half occupancy must be between 0 and 1")
        return v

    class Config:
        extra = "forbid"


class CapabilityRegistry:
    """Registry of capabilities with schemas and examples."""

    def __init__(self):
        self.capabilities = self._load_capabilities()

    def _load_capabilities(self) -> dict[str, Any]:
        """Load capability definitions."""
        return {
            "forecast": {
                "name": "Forecast Generation",
                "description": "Generate workload forecasts using StatsForecast",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "value": {"type": "number", "gt": 0},
                                    "metadata": {"type": "object"},
                                },
                                "required": ["timestamp", "value"],
                            },
                        },
                        "model": {"type": "string", "default": "AutoARIMA"},
                        "forecast_horizon": {"type": "integer", "default": 7},
                    },
                    "required": ["data"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "value": {"type": "number", "ge": 0},
                                    "metadata": {"type": "object"},
                                },
                            },
                        },
                        "metadata": {"type": "object"},
                    },
                    "required": ["success", "data"],
                },
                "examples": {
                    "inbound_8hr": {
                        "data": [
                            {
                                "timestamp": "2023-01-01T09:00:00",
                                "value": 50,
                                "metadata": {"hour": 9},
                            },
                            {
                                "timestamp": "2023-01-01T10:00:00",
                                "value": 75,
                                "metadata": {"hour": 10},
                            },
                            {
                                "timestamp": "2023-01-01T11:00:00",
                                "value": 120,
                                "metadata": {"hour": 11},
                            },
                        ],
                        "model": "AutoARIMA",
                        "forecast_horizon": 7,
                    }
                },
            },
            "staff": {
                "name": "Staffing Calculation",
                "description": "Calculate staffing requirements using Erlang C",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "value": {"type": "number", "gt": 0},
                                    "metadata": {"type": "object"},
                                },
                                "required": ["timestamp", "value"],
                            },
                        },
                        "service_level": {"type": "number", "default": 0.8, "maximum": 1},
                        "average_speed_of_answer": {
                            "type": "integer",
                            "default": 180,
                            "minimum": 0,
                        },
                        "shrinkage_rate": {"type": "number", "default": 0.3, "maximum": 1},
                        "half_occupancy": {"type": "number", "default": 0.85, "minimum": 0},
                    },
                    "required": ["data"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["success", "data"],
                },
                "examples": {
                    "inbound_8hr": {
                        "data": [
                            {
                                "timestamp": "2023-01-01T09:00:00",
                                "value": 180,
                                "metadata": {"hour": 9, "type": "voice"},
                            },
                            {
                                "timestamp": "2023-01-01T10:00:00",
                                "value": 200,
                                "metadata": {"hour": 10, "type": "voice"},
                            },
                            {
                                "timestamp": "2023-01-01T11:00:00",
                                "value": 150,
                                "metadata": {"hour": 11, "type": "voice"},
                            },
                        ],
                        "service_level": 0.8,
                    }
                },
            },
            "schedule": {
                "name": "Schedule Generation",
                "description": "Generate work schedules using constraint solving",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "value": {"type": "number", "gt": 0},
                                    "metadata": {"type": "object"},
                                },
                                "required": ["timestamp", "value"],
                            },
                        },
                        "constraints": {"type": "object"},
                    },
                    "required": ["data"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["success", "data"],
                },
                "examples": {
                    "inbound_8hr": {
                        "data": [
                            {
                                "timestamp": "2023-01-01T09:00:00",
                                "value": 8,
                                "metadata": {"hour": 9, "skill": "senior"},
                            },
                            {
                                "timestamp": "2023-01-01T10:00:00",
                                "value": 10,
                                "metadata": {"hour": 10, "skill": "senior"},
                            },
                            {
                                "timestamp": "2023-01-01T11:00:00",
                                "value": 12,
                                "metadata": {"hour": 11, "skill": "senior"},
                            },
                        ]
                    }
                },
            },
            "optimize": {
                "name": "Optimization",
                "description": "Optimize schedules and staffing using OR-Tools",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "value": {"type": "number", "gt": 0},
                                    "metadata": {"type": "object"},
                                },
                                "required": ["timestamp", "value"],
                            },
                        },
                        "objectives": {"type": "object"},
                    },
                    "required": ["data"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["success", "data"],
                },
                "examples": {
                    "inbound_8hr": {
                        "data": [
                            {
                                "timestamp": "2023-01-01T09:00:00",
                                "value": 8,
                                "metadata": {"hour": 9, "skill": "senior"},
                            },
                            {
                                "timestamp": "2023-01-01T10:00:00",
                                "value": 10,
                                "metadata": {"hour": 10, "skill": "senior"},
                            },
                            {
                                "timestamp": "2023-01-01T11:00:00",
                                "value": 12,
                                "metadata": {"hour": 11, "skill": "senior"},
                            },
                        ],
                        "objectives": {"minimize_overtime": True, "maximize_coverage": True},
                    }
                },
            },
            "validate": {
                "name": "Validation",
                "description": "Validate data and configurations using Pandera",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "timestamp": {"type": "string", "format": "date-time"},
                                    "value": {"type": "number", "gt": 0},
                                    "metadata": {"type": "object"},
                                },
                                "required": ["timestamp", "value"],
                            },
                        },
                        "schema_name": {"type": "string"},
                    },
                    "required": ["data"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "data": {"type": "object"},
                        "metadata": {"type": "object"},
                    },
                    "required": ["success", "data"],
                },
                "examples": {
                    "inbound_8hr": {
                        "data": [
                            {"timestamp": "2023-01-01T09:00:00", "value": 100, "metadata": {}},
                            {"timestamp": "2023-01-01T10:00:00", "value": 150, "metadata": {}},
                            {"timestamp": "2023-01-01T11:00:00", "value": 200, "metadata": {}},
                        ],
                        "schema_name": "wfm_data_standard",
                    }
                },
            },
        }

    def get_capability(self, name: str) -> dict[str, Any] | None:
        """Get capability by name."""
        return self.capabilities.get(name)

    def get_all_capabilities(self) -> dict[str, Any]:
        """Get all capabilities."""
        return self.capabilities

    def validate_capability_input(
        self, capability_name: str, input_data: dict[str, Any]
    ) -> list[str]:
        """Validate input against capability schema."""
        capability = self.get_capability(capability_name)
        if not capability:
            return [f"Capability '{capability_name}' not found"]

        # Simple validation - in production would use a proper schema validator
        errors = []
        schema = capability.get("input_schema", {})

        if "properties" in schema and "required" in schema:
            for required_field in schema["required"]:
                if required_field not in input_data:
                    errors.append(f"Missing required field: {required_field}")

        return errors

    def get_capability_examples(self, capability_name: str) -> list[dict[str, Any]]:
        """Get examples for a capability."""
        capability = self.get_capability(capability_name)
        if not capability:
            return []

        examples = capability.get("examples", {})
        return list(examples.values())
