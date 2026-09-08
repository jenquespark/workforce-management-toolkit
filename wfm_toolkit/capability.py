"""
Capability configuration for Workforce Management Toolkit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CapabilityType(str, Enum):
    """Type of capability."""

    FORECASTING = "forecasting"
    STAFFING = "staffing"
    SCHEDULING = "scheduling"
    OPTIMIZATION = "optimization"
    VALIDATION = "validation"
    CAPACITY = "capacity"


@dataclass
class CapabilityConfig:
    """Configuration for a capability."""

    identifier: str
    description: str
    capability_type: CapabilityType
    provider: str = "deterministic"
    deterministic: bool = True
    llm_required: bool = False
    neural_network_required: bool = False
    version: str = "1.0.0"
    author: str = "Workforce Management Toolkit"
    created_at: datetime = field(default_factory=datetime.utcnow)
    documentation_url: str = ""
    examples_url: str = ""
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    runtime_requirements: dict[str, Any] = field(default_factory=dict)
    supported_channels: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    examples: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "identifier": self.identifier,
            "description": self.description,
            "capability_type": self.capability_type.value,
            "provider": self.provider,
            "deterministic": self.deterministic,
            "llm_required": self.llm_required,
            "neural_network_required": self.neural_network_required,
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "documentation_url": self.documentation_url,
            "examples_url": self.examples_url,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "runtime_requirements": self.runtime_requirements,
            "supported_channels": self.supported_channels,
            "limitations": self.limitations,
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CapabilityConfig:
        """Create CapabilityConfig from dictionary."""
        return cls(
            identifier=data["identifier"],
            description=data["description"],
            capability_type=CapabilityType(data["capability_type"]),
            provider=data.get("provider", "deterministic"),
            deterministic=data.get("deterministic", True),
            llm_required=data.get("llm_required", False),
            neural_network_required=data.get("neural_network_required", False),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "Workforce Management Toolkit"),
            created_at=datetime.fromisoformat(
                data.get("created_at", datetime.utcnow().isoformat())
            ),
            documentation_url=data.get("documentation_url", ""),
            examples_url=data.get("examples_url", ""),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            runtime_requirements=data.get("runtime_requirements", {}),
            supported_channels=data.get("supported_channels", []),
            limitations=data.get("limitations", []),
            examples=data.get("examples", []),
        )
