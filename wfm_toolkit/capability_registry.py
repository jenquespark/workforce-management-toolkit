"""
Core capability registry for Workforce Management Toolkit.

Provides machine-readable capability definitions. Every capability carries a
status that distinguishes EXECUTABLE (implemented, backed by real adapter
code) from REGISTERED/PLANNED (metadata only, no executable logic yet).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import yaml


class CapabilityStatus(str, Enum):
    """Execution status of a registered capability."""

    IMPLEMENTED = "implemented"  # backed by real, executable adapter code
    PLANNED = "planned"  # defined in metadata; no executable logic yet
    EXPERIMENTAL = "experimental"  # present but not yet stable/verified
    UNAVAILABLE = "unavailable"  # provider/operation not available in this stage


class DeterministicLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LLMRequirement(str, Enum):
    NOT_REQUIRED = "not_required"
    OPTIONAL = "optional"
    REQUIRED = "required"


class NeuralNetworkRequirement(str, Enum):
    NOT_REQUIRED = "not_required"
    OPTIONAL = "optional"
    REQUIRED = "required"


@dataclass
class CapabilityMetadata:
    """Metadata about a capability."""

    version: str = "1.0.0"
    author: str = "Workforce Management Toolkit"
    created_at: datetime = field(default_factory=datetime.utcnow)
    documentation_url: str | None = None
    examples_url: str | None = None


@dataclass
class CapabilityProvider:
    """Provider information for a capability."""

    name: str
    package: str
    license: str
    deterministic_level: DeterministicLevel
    integration_type: str
    core: bool = True


@dataclass
class CapabilityInterface:
    """Input/output contract for a capability."""

    required_inputs: list[str] = field(default_factory=list)
    optional_inputs: list[str] = field(default_factory=list)
    required_outputs: list[str] = field(default_factory=list)
    optional_outputs: list[str] = field(default_factory=list)
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class Capability:
    """Core capability definition."""

    identifier: str
    description: str
    provider: CapabilityProvider
    interface: CapabilityInterface
    status: CapabilityStatus
    deterministic: bool = True
    llm_required: LLMRequirement = LLMRequirement.NOT_REQUIRED
    neural_network_required: NeuralNetworkRequirement = NeuralNetworkRequirement.NOT_REQUIRED
    runtime_requirements: dict[str, Any] = field(default_factory=dict)
    supported_channels: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    documentation: str = ""
    examples: list[dict[str, Any]] = field(default_factory=list)

    def is_executable(self) -> bool:
        """A capability is executable only if its status is IMPLEMENTED."""
        return self.status == CapabilityStatus.IMPLEMENTED

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for serialization."""
        return {
            "identifier": self.identifier,
            "description": self.description,
            "status": self.status.value,
            "provider": {
                "name": self.provider.name,
                "package": self.provider.package,
                "license": self.provider.license,
                "deterministic_level": self.provider.deterministic_level.value,
                "integration_type": self.provider.integration_type,
                "core": self.provider.core,
            },
            "interface": {
                "required_inputs": self.interface.required_inputs,
                "optional_inputs": self.interface.optional_inputs,
                "required_outputs": self.interface.required_outputs,
                "optional_outputs": self.interface.optional_outputs,
                "input_schema": self.interface.input_schema,
                "output_schema": self.interface.output_schema,
            },
            "deterministic": self.deterministic,
            "llm_required": self.llm_required.value,
            "neural_network_required": self.neural_network_required.value,
            "runtime_requirements": self.runtime_requirements,
            "supported_channels": self.supported_channels,
            "limitations": self.limitations,
            "documentation": self.documentation,
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Capability:
        """Create a Capability from a dictionary."""
        return cls(
            identifier=data["identifier"],
            description=data["description"],
            status=CapabilityStatus(data.get("status", "planned")),
            provider=CapabilityProvider(
                name=data["provider"]["name"],
                package=data["provider"]["package"],
                license=data["provider"]["license"],
                deterministic_level=DeterministicLevel(data["provider"]["deterministic_level"]),
                integration_type=data["provider"]["integration_type"],
                core=data["provider"].get("core", True),
            ),
            interface=CapabilityInterface(
                required_inputs=data["interface"]["required_inputs"],
                optional_inputs=data["interface"]["optional_inputs"],
                required_outputs=data["interface"]["required_outputs"],
                optional_outputs=data["interface"]["optional_outputs"],
                input_schema=data["interface"]["input_schema"],
                output_schema=data["interface"]["output_schema"],
            ),
            deterministic=data.get("deterministic", True),
            llm_required=LLMRequirement(data.get("llm_required", "not_required")),
            neural_network_required=NeuralNetworkRequirement(
                data.get("neural_network_required", "not_required")
            ),
            runtime_requirements=data.get("runtime_requirements", {}),
            supported_channels=data.get("supported_channels", []),
            limitations=data.get("limitations", []),
            documentation=data.get("documentation", ""),
            examples=data.get("examples", []),
        )


class CapabilityRegistry:
    """Registry for managing WFM capabilities."""

    def __init__(self):
        self.capabilities: dict[str, Capability] = {}
        self._load_default_capabilities()

    def _load_default_capabilities(self):
        """Load default capability definitions with explicit statuses.

        Only three capabilities are IMPLEMENTED (executable) in this stage:
        forecast.generate (StatsForecast), staffing.erlang_c (pyworkforce),
        and validate.dataset (Pandera). Everything else is PLANNED metadata.
        """
        # --- Implemented: forecasting via StatsForecast ---
        self.register_capability(
            Capability(
                identifier="forecast.generate",
                description="Statistical time-series forecasting (AutoARIMA, AutoETS, SeasonalNaive)",
                status=CapabilityStatus.IMPLEMENTED,
                provider=CapabilityProvider(
                    name="StatsForecast",
                    package="statsforecast",
                    license="Apache-2.0",
                    deterministic_level=DeterministicLevel.HIGH,
                    integration_type="python_api",
                    core=True,
                ),
                interface=CapabilityInterface(
                    required_inputs=["historical_data", "horizon", "model_type"],
                    optional_inputs=["season_length", "freq"],
                    required_outputs=["forecast_values", "model_metadata"],
                    optional_outputs=[],
                    input_schema={
                        "historical_data": "array[float]",
                        "horizon": "int",
                        "model_type": "string",
                    },
                    output_schema={"forecast_values": "array[float]"},
                ),
                deterministic=True,
                llm_required=LLMRequirement.NOT_REQUIRED,
                neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
                documentation="Statistical forecasting via StatsForecastAdapter.forecast()",
            )
        )

        # --- Implemented: Erlang C staffing via pyworkforce ---
        self.register_capability(
            Capability(
                identifier="staffing.erlang_c",
                description="Erlang C staffing: required positions for a target service level in a voice queue",
                status=CapabilityStatus.IMPLEMENTED,
                provider=CapabilityProvider(
                    name="Pyworkforce",
                    package="pyworkforce",
                    license="MIT",
                    deterministic_level=DeterministicLevel.HIGH,
                    integration_type="python_api",
                    core=True,
                ),
                interface=CapabilityInterface(
                    required_inputs=["transactions", "aht", "asa", "interval"],
                    optional_inputs=["service_level", "max_occupancy", "shrinkage"],
                    required_outputs=[
                        "raw_positions",
                        "positions",
                        "service_level",
                        "occupancy",
                        "waiting_probability",
                    ],
                    optional_outputs=[],
                    input_schema={
                        "transactions": "float",
                        "aht": "float (minutes)",
                        "asa": "float (minutes)",
                        "interval": "int (minutes)",
                        "service_level": "float [0,1]",
                        "max_occupancy": "float (0,1]",
                        "shrinkage": "float [0,1)",
                    },
                    output_schema={
                        "positions": "int",
                        "service_level": "float",
                        "occupancy": "float",
                    },
                ),
                deterministic=True,
                llm_required=LLMRequirement.NOT_REQUIRED,
                neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
                documentation="Erlang C staffing via PyworkforceAdapter.staff(); requires explicit business inputs",
            )
        )

        # --- Implemented: dataset validation via Pandera ---
        self.register_capability(
            Capability(
                identifier="validate.dataset",
                description="Validate a WFM dataset (WFMData) against a canonical schema using Pandera",
                status=CapabilityStatus.IMPLEMENTED,
                provider=CapabilityProvider(
                    name="Pandera",
                    package="pandera",
                    license="MIT",
                    deterministic_level=DeterministicLevel.HIGH,
                    integration_type="python_api",
                    core=True,
                ),
                interface=CapabilityInterface(
                    required_inputs=["dataset"],
                    optional_inputs=["strict_mode"],
                    required_outputs=["valid", "errors"],
                    optional_outputs=["corrected_dataset"],
                    input_schema={"dataset": "list[WFMData]"},
                    output_schema={"valid": "bool", "errors": "array[string]"},
                ),
                deterministic=True,
                llm_required=LLMRequirement.NOT_REQUIRED,
                neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
                documentation="Dataset validation via PanderaAdapter.validate()",
            )
        )

        # --- Planned (metadata only, no executable logic yet) ---
        self.register_capability(
            Capability(
                identifier="forecast.evaluate",
                description="Forecast accuracy metrics (MAPE, MAE, RMSE) - not yet executable",
                status=CapabilityStatus.PLANNED,
                provider=CapabilityProvider(
                    name="StatsForecast",
                    package="statsforecast",
                    license="Apache-2.0",
                    deterministic_level=DeterministicLevel.HIGH,
                    integration_type="python_api",
                    core=False,
                ),
                interface=CapabilityInterface(
                    required_inputs=["actual_values", "forecasted_values"],
                    optional_inputs=[],
                    required_outputs=["mape", "mae", "rmse"],
                    optional_outputs=[],
                    input_schema={
                        "actual_values": "array[float]",
                        "forecasted_values": "array[float]",
                    },
                    output_schema={"mape": "float", "mae": "float", "rmse": "float"},
                ),
                deterministic=True,
                llm_required=LLMRequirement.NOT_REQUIRED,
                neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
                documentation="Planned; no executable provider logic in this stage",
            )
        )

        self.register_capability(
            Capability(
                identifier="staffing.multiskill",
                description="Multi-skill staffing - not yet executable",
                status=CapabilityStatus.PLANNED,
                provider=CapabilityProvider(
                    name="Pyworkforce",
                    package="pyworkforce",
                    license="MIT",
                    deterministic_level=DeterministicLevel.HIGH,
                    integration_type="python_api",
                    core=False,
                ),
                interface=CapabilityInterface(
                    required_inputs=["skill_matrix", "arrival_rates_by_skill", "target_sls"],
                    optional_inputs=[],
                    required_outputs=["agents_per_skill"],
                    optional_outputs=[],
                    input_schema={},
                    output_schema={},
                ),
                deterministic=True,
                llm_required=LLMRequirement.NOT_REQUIRED,
                neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
                documentation="Planned; no executable provider logic in this stage",
            )
        )

        self.register_capability(
            Capability(
                identifier="schedule.generate",
                description="Shift schedule generation - deferred (OR-Tools adapter is a stub)",
                status=CapabilityStatus.PLANNED,
                provider=CapabilityProvider(
                    name="OR-Tools",
                    package="ortools",
                    license="Apache-2.0",
                    deterministic_level=DeterministicLevel.HIGH,
                    integration_type="python_api",
                    core=False,
                ),
                interface=CapabilityInterface(
                    required_inputs=["demand_forecast", "shift_rules", "agent_constraints"],
                    optional_inputs=[],
                    required_outputs=["schedule", "coverage"],
                    optional_outputs=[],
                    input_schema={},
                    output_schema={},
                ),
                deterministic=True,
                llm_required=LLMRequirement.NOT_REQUIRED,
                neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
                documentation="Planned; OR-Tools not a validated core provider in this stage",
            )
        )

        self.register_capability(
            Capability(
                identifier="validate.wfm_config",
                description="Validate a WFM configuration dict against a canonical schema - not yet wired",
                status=CapabilityStatus.PLANNED,
                provider=CapabilityProvider(
                    name="Pandera",
                    package="pandera",
                    license="MIT",
                    deterministic_level=DeterministicLevel.HIGH,
                    integration_type="python_api",
                    core=False,
                ),
                interface=CapabilityInterface(
                    required_inputs=["config_dict"],
                    optional_inputs=["strict_mode"],
                    required_outputs=["valid", "errors"],
                    optional_outputs=[],
                    input_schema={},
                    output_schema={},
                ),
                deterministic=True,
                llm_required=LLMRequirement.NOT_REQUIRED,
                neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
                documentation="Planned; distinct from validate.dataset",
            )
        )

        self.register_capability(
            Capability(
                identifier="capacity.forecast",
                description="Long-term capacity planning from demand forecasts - not yet executable",
                status=CapabilityStatus.PLANNED,
                provider=CapabilityProvider(
                    name="StatsForecast",
                    package="statsforecast",
                    license="Apache-2.0",
                    deterministic_level=DeterministicLevel.MEDIUM,
                    integration_type="python_api",
                    core=False,
                ),
                interface=CapabilityInterface(
                    required_inputs=["historical_demand", "planning_horizon"],
                    optional_inputs=[],
                    required_outputs=["capacity_requirements"],
                    optional_outputs=[],
                    input_schema={},
                    output_schema={},
                ),
                deterministic=True,
                llm_required=LLMRequirement.NOT_REQUIRED,
                neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
                documentation="Planned; no executable provider logic in this stage",
            )
        )

    def get_capacities(self):
        """Get all capabilities as dictionaries."""
        return [c.to_dict() for c in self.capabilities.values()]

    def register_capability(self, capability: Capability):
        """Register a new capability."""
        self.capabilities[capability.identifier] = capability

    def get_capability(self, identifier: str) -> Capability | None:
        """Get a capability by identifier."""
        return self.capabilities.get(identifier)

    def list_capabilities(
        self,
        deterministic: bool | None = None,
        llm_required: LLMRequirement | None = None,
        status: CapabilityStatus | None = None,
    ) -> list[Capability]:
        """List capabilities with optional filters."""
        capabilities = list(self.capabilities.values())

        if deterministic is not None:
            capabilities = [c for c in capabilities if c.deterministic == deterministic]

        if llm_required is not None:
            capabilities = [c for c in capabilities if c.llm_required == llm_required]

        if status is not None:
            capabilities = [c for c in capabilities if c.status == status]

        return capabilities

    def executable_capabilities(self) -> list[Capability]:
        """Return only capabilities that are actually executable."""
        return [c for c in self.capabilities.values() if c.is_executable()]

    def export_capabilities(self, format: str = "json") -> str:
        """Export capabilities in the specified format."""
        if format.lower() == "json":
            return json.dumps([c.to_dict() for c in self.capabilities.values()], indent=2)
        elif format.lower() == "yaml":
            return yaml.safe_dump(
                [c.to_dict() for c in self.capabilities.values()], default_flow_style=False
            )
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_capabilities(self, data: str, format: str = "json"):
        """Import capabilities from the specified format."""
        if format.lower() == "json":
            capabilities_data = json.loads(data)
        elif format.lower() == "yaml":
            capabilities_data = yaml.safe_load(data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        for cap_data in capabilities_data:
            capability = Capability.from_dict(cap_data)
            self.register_capability(capability)
