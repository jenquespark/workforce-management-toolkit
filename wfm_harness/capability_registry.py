"""
Core capability registry for Workforce Management Harness.

Provides machine-readable capability definitions and deterministic execution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
import json
import yaml
from pathlib import Path

class OperationType(str, Enum):
    FORECAST = "forecast"
    FORECAST_EVALUATE = "forecast.evaluate"
    STAFFING_VOICE = "staffing.voice"
    STAFFING_QUEUE = "staffing.queue"
    STAFFING_SERVICE_LEVEL = "staffing.service_level"
    STAFFING_OCCUPANCY = "staffing.occupancy_aware"
    STAFFING_MULTI_SKILL = "staffing.multiskill"
    SCHEDULE_SHIFT = "schedule.shift"
    SCHEDULE_ROSTER = "schedule.roster"
    SCHEDULE_BREAKS = "schedule.breaks"
    SCHEDULE_COVERAGE = "schedule.coverage"
    SCHEDULE_AGENT_ASSIGNMENT = "schedule.agent_assignment"
    OPTIMIZE_COVERAGE = "optimize.coverage"
    OPTIMIZE_SHIFTS = "optimize.shifts"
    OPTIMIZE_SKILL_ALLOCATION = "optimize.skill_allocation"
    OPTIMIZE_COST_MINIMIZATION = "optimize.cost_minimization"
    OPTIMIZE_CONSTRAINT_SOLVING = "optimize.constraint_solving"
    CAPACITY_FORECAST = "capacity.forecast"
    CAPACITY_WORKLOAD = "capacity.workload"
    CAPACITY_STAFFING = "capacity.staffing"
    CAPACITY_SHRINKAGE = "capacity.shrinkage"
    CAPACITY_SCHEDULE = "capacity.schedule"
    CAPACITY_OPTIMIZATION = "capacity.optimization"
    CAPACITY_SCENARIO = "capacity.scenario"
    VALIDATE_DATASET = "validate.dataset"
    VALIDATE_SCHEMA = "validate.schema"
    VALIDATE_TYPES = "validate.types"
    VALIDATE_REQUIRED_FIELDS = "validate.required_fields"
    VALIDATE_DUPLICATES = "validate.duplicates"
    VALIDATE_NULLS = "validate.nulls"
    VALIDATE_RANGES = "validate.ranges"
    VALIDATE_INTERVAL_INTEGRITY = "validate.interval_integrity"
    VALIDATE_WFM_CONFIG = "validate.wfm_config"
    VALIDATE_CANONICAL_CONTRACTS = "validate.canonical_contracts"

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
    author: str = "Workforce Management Harness"
    created_at: datetime = field(default_factory=datetime.utcnow)
    documentation_url: Optional[str] = None
    examples_url: Optional[str] = None

@dataclass
class CapabilityProvider:
    """Third-party provider information."""
    name: str
    package: str
    license: str
    deterministic_level: DeterministicLevel
    integration_type: str
    core: bool = True

@dataclass
class CapabilityInterface:
    """Input/output contract for capability."""
    required_inputs: List[str] = field(default_factory=list)
    optional_inputs: List[str] = field(default_factory=list)
    required_outputs: List[str] = field(default_factory=list)
    optional_outputs: List[str] = field(default_factory=list)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Capability:
    """Core capability definition."""
    identifier: str
    description: str
    provider: CapabilityProvider
    interface: CapabilityInterface
    deterministic: bool = True
    llm_required: LLMRequirement = LLMRequirement.NOT_REQUIRED
    neural_network_required: NeuralNetworkRequirement = NeuralNetworkRequirement.NOT_REQUIRED
    runtime_requirements: Dict[str, Any] = field(default_factory=dict)
    supported_channels: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    documentation: str = ""
    examples: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "identifier": self.identifier,
            "description": self.description,
            "provider": {
                "name": self.provider.name,
                "package": self.provider.package,
                "license": self.provider.license,
                "deterministic_level": self.provider.deterministic_level.value,
                "integration_type": self.provider.integration_type,
                "core": self.provider.core
            },
            "interface": {
                "required_inputs": self.interface.required_inputs,
                "optional_inputs": self.interface.optional_inputs,
                "required_outputs": self.interface.required_outputs,
                "optional_outputs": self.interface.optional_outputs,
                "input_schema": self.interface.input_schema,
                "output_schema": self.interface.output_schema
            },
            "deterministic": self.deterministic,
            "llm_required": self.llm_required.value,
            "neural_network_required": self.neural_network_required.value,
            "runtime_requirements": self.runtime_requirements,
            "supported_channels": self.supported_channels,
            "limitations": self.limitations,
            "documentation": self.documentation,
            "examples": self.examples
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Capability":
        """Create Capability from dictionary."""
        return cls(
            identifier=data["identifier"],
            description=data["description"],
            provider=CapabilityProvider(
                name=data["provider"]["name"],
                package=data["provider"]["package"],
                license=data["provider"]["license"],
                deterministic_level=DeterministicLevel(data["provider"]["deterministic_level"]),
                integration_type=data["provider"]["integration_type"],
                core=data["provider"]["core"]
            ),
            interface=CapabilityInterface(
                required_inputs=data["interface"]["required_inputs"],
                optional_inputs=data["interface"]["optional_inputs"],
                required_outputs=data["interface"]["required_outputs"],
                optional_outputs=data["interface"]["optional_outputs"],
                input_schema=data["interface"]["input_schema"],
                output_schema=data["interface"]["output_schema"]
            ),
            deterministic=data.get("deterministic", True),
            llm_required=LLMRequirement(data.get("llm_required", "not_required")),
            neural_network_required=NeuralNetworkRequirement(data.get("neural_network_required", "not_required")),
            runtime_requirements=data.get("runtime_requirements", {}),
            supported_channels=data.get("supported_channels", []),
            limitations=data.get("limitations", []),
            documentation=data.get("documentation", ""),
            examples=data.get("examples", [])
        )

class CapabilityRegistry:
    """Registry for managing WFM capabilities."""

    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self._load_default_capabilities()

    def _load_default_capabilities(self):
        """Load default capability definitions."""
        # Core Forecasting Capabilities
        self.register_capability(Capability(
            identifier="forecast.evaluate",
            description="Evaluate forecast accuracy using MAPE, MAE, RMSE metrics",
            provider=CapabilityProvider(
                name="StatsForecast",
                package="statsforecast",
                license="Apache-2.0",
                deterministic_level=DeterministicLevel.HIGH,
                integration_type="python_api",
                core=True
            ),
            interface=CapabilityInterface(
                required_inputs=["actual_values", "forecasted_values"],
                optional_inputs=["confidence_intervals"],
                required_outputs=["mape", "mae", "rmse", "mape_per_interval"],
                optional_outputs=["bias", "tracking_signal"],
                input_schema={"actual_values": "array[float]", "forecasted_values": "array[float]"},
                output_schema={"mape": "float", "mae": "float", "rmse": "float"}
            ),
            deterministic=True,
            llm_required=LLMRequirement.NOT_REQUIRED,
            neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
            documentation="Computes standard forecast accuracy metrics for time series evaluation",
            examples=[{"actual": [100, 120, 110], "forecast": [95, 125, 105], "mape": 4.17}]
        ))
        
        self.register_capability(Capability(
            identifier="forecast.generate",
            description="Generate deterministic forecasts using AutoARIMA, AutoETS, or SeasonalNaive",
            provider=CapabilityProvider(
                name="StatsForecast",
                package="statsforecast",
                license="Apache-2.0",
                deterministic_level=DeterministicLevel.HIGH,
                integration_type="python_api",
                core=True
            ),
            interface=CapabilityInterface(
                required_inputs=["historical_data", "horizon", "model_type"],
                optional_inputs=["seasonality", "confidence_level"],
                required_outputs=["forecast_values", "confidence_intervals", "model_metadata"],
                optional_outputs=["feature_importance", "residuals"],
                input_schema={"historical_data": "array[float]", "horizon": "int", "model_type": "string"},
                output_schema={"forecast_values": "array[float]", "confidence_intervals": "array[array[float]]"}
            ),
            deterministic=True,
            llm_required=LLMRequirement.NOT_REQUIRED,
            neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
            documentation="Generates forecasts using statistical models with full reproducibility",
            examples=[{"historical": [100, 110, 120, 115], "horizon": 5, "model": "AutoARIMA"}]
        ))
        
        # Core Staffing Capabilities
        self.register_capability(Capability(
            identifier="staffing.erlang_c",
            description="Calculate required agents using Erlang-C formula for voice queues",
            provider=CapabilityProvider(
                name="Pyworkforce",
                package="pyworkforce",
                license="BSD-3-Clause",
                deterministic_level=DeterministicLevel.HIGH,
                integration_type="python_api",
                core=True
            ),
            interface=CapabilityInterface(
                required_inputs=["arrival_rate", "aht", "target_service_level", "target_answer_time"],
                optional_inputs=["shrinkage", "occupancy"],
                required_outputs=["required_agents", "service_level", "occupancy", "asa"],
                optional_outputs=["queue_probability", "wait_time_distribution"],
                input_schema={"arrival_rate": "float", "aht": "float", "target_service_level": "float"},
                output_schema={"required_agents": "int", "service_level": "float", "occupancy": "float"}
            ),
            deterministic=True,
            llm_required=LLMRequirement.NOT_REQUIRED,
            neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
            documentation="Calculates minimum agents needed to achieve target service level using Erlang-C",
            examples=[{"arrival_rate": 100, "aht": 300, "sl": 0.8, "target_asa": 20, "agents": 12}]
        ))
        
        self.register_capability(Capability(
            identifier="staffing.multiskill",
            description="Calculate staffing for multi-skill environments with skill-based routing",
            provider=CapabilityProvider(
                name="Pyworkforce",
                package="pyworkforce",
                license="BSD-3-Clause",
                deterministic_level=DeterministicLevel.HIGH,
                integration_type="python_api",
                core=True
            ),
            interface=CapabilityInterface(
                required_inputs=["skill_matrix", "arrival_rates_by_skill", "target_sls"],
                optional_inputs=["agent_skills", "shift_patterns"],
                required_outputs=["agents_per_skill", "skill_coverage", "overall_sl"],
                optional_outputs=["skill_utilization", "cross_skill_efficiency"],
                input_schema={"skill_matrix": "array[array[int]]", "arrival_rates": "array[float]"},
                output_schema={"agents_per_skill": "array[int]", "skill_coverage": "float"}
            ),
            deterministic=True,
            llm_required=LLMRequirement.NOT_REQUIRED,
            neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
            documentation="Multi-skill staffing optimization with skill-based routing considerations",
            examples=[{"skills": 3, "agents": [5, 8, 4], "coverage": 0.92}]
        ))
        
        # Core Scheduling Capabilities
        self.register_capability(Capability(
            identifier="schedule.generate",
            description="Generate shift schedules using constraint programming",
            provider=CapabilityProvider(
                name="OR-Tools",
                package="ortools",
                license="Apache-2.0",
                deterministic_level=DeterministicLevel.HIGH,
                integration_type="python_api",
                core=True
            ),
            interface=CapabilityInterface(
                required_inputs=["demand_forecast", "shift_rules", "agent_constraints"],
                optional_inputs=["preferences", "skill_requirements"],
                required_outputs=["schedule", "coverage", "utilization"],
                optional_outputs=["fairness_metrics", "preference_satisfaction"],
                input_schema={"demand_forecast": "array[float]", "shift_rules": "object", "agent_constraints": "object"},
                output_schema={"schedule": "array[object]", "coverage": "float", "utilization": "float"}
            ),
            deterministic=True,
            llm_required=LLMRequirement.NOT_REQUIRED,
            neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
            documentation="Generates optimized shift schedules meeting all constraints",
            examples=[{"agents": 10, "shifts": 3, "coverage": 0.95}]
        ))
        
        # Core Validation Capabilities
        self.register_capability(Capability(
            identifier="validate.wfm_config",
            description="Validate WFM configuration against canonical schema",
            provider=CapabilityProvider(
                name="Pandera",
                package="pandera",
                license="MIT",
                deterministic_level=DeterministicLevel.HIGH,
                integration_type="python_api",
                core=True
            ),
            interface=CapabilityInterface(
                required_inputs=["config_dict"],
                optional_inputs=["strict_mode"],
                required_outputs=["valid", "errors", "warnings"],
                optional_outputs=["corrected_config"],
                input_schema={"config_dict": "object"},
                output_schema={"valid": "bool", "errors": "array[string]", "warnings": "array[string]"}
            ),
            deterministic=True,
            llm_required=LLMRequirement.NOT_REQUIRED,
            neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
            documentation="Validates WFM configuration files against canonical schema",
            examples=[{"config": {"model": "AutoARIMA", "sl": 0.8}, "valid": True, "errors": []}]
        ))
        
        # Core Capacity Capabilities
        self.register_capability(Capability(
            identifier="capacity.forecast",
            description="Long-term capacity planning based on demand forecasts",
            provider=CapabilityProvider(
                name="StatsForecast",
                package="statsforecast",
                license="Apache-2.0",
                deterministic_level=DeterministicLevel.MEDIUM,
                integration_type="python_api",
                core=True
            ),
            interface=CapabilityInterface(
                required_inputs=["historical_demand", "planning_horizon"],
                optional_inputs=["growth_rate", "seasonality"],
                required_outputs=["capacity_requirements", "hiring_plan", "cost_estimate"],
                optional_outputs=["scenario_analysis", "risk_assessment"],
                input_schema={"historical_demand": "array[float]", "planning_horizon": "int"},
                output_schema={"capacity_requirements": "array[int]", "hiring_plan": "array[object]"}
            ),
            deterministic=True,
            llm_required=LLMRequirement.NOT_REQUIRED,
            neural_network_required=NeuralNetworkRequirement.NOT_REQUIRED,
            documentation="Projects long-term capacity needs from demand forecasts",
            examples=[{"horizon": 12, "months": [50, 52, 55, 58, 60, 62, 65, 68, 70, 72, 75, 78]}]
        ))

    def get_capacities(self):
        """Get all capacities as dictionaries."""
        return [c.to_dict() for c in self.capabilities.values()]

    def register_capability(self, capability: Capability):
        """Register a new capability."""
        self.capabilities[capability.identifier] = capability

    def get_capability(self, identifier: str) -> Optional[Capability]:
        """Get capability by identifier."""
        return self.capabilities.get(identifier)

    def list_capabilities(self, deterministic: Optional[bool] = None, llm_required: Optional[LLMRequirement] = None) -> List[Capability]:
        """List capabilities with optional filters."""
        capabilities = list(self.capabilities.values())
        
        if deterministic is not None:
            capabilities = [c for c in capabilities if c.deterministic == deterministic]
        
        if llm_required is not None:
            capabilities = [c for c in capabilities if c.llm_required == llm_required]
        
        return capabilities

    def export_capabilities(self, format: str = "json") -> str:
        """Export capabilities in specified format."""
        if format.lower() == "json":
            return json.dumps([c.to_dict() for c in self.capabilities.values()], indent=2)
        elif format.lower() == "yaml":
            return yaml.dump([c.to_dict() for c in self.capabilities.values()], default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def import_capabilities(self, data: str, format: str = "json"):
        """Import capabilities from specified format."""
        if format.lower() == "json":
            capabilities_data = json.loads(data)
        elif format.lower() == "yaml":
            capabilities_data = yaml.safe_load(data)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        for cap_data in capabilities_data:
            capability = Capability.from_dict(cap_data)
            self.register_capability(capability)
