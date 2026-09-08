"""
Configuration validation for Workforce Management Toolkit.

Pydantic-based configuration schemas with comprehensive validation
for all WFM operations including forecasting, staffing, scheduling,
optimization, and validation.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


class OperatingProfile(str, Enum):
    """Operating profile for workforce management."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BLENDED = "blended"
    MULTI_SKILL = "multi_skill"


class Direction(str, Enum):
    """Call direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BLENDED = "blended"


class TimeInterval(str, Enum):
    """Time interval for WFM calculations."""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ForecastModel(str, Enum):
    """Forecasting model types."""

    SEASONAL_NAIVE = "seasonal_naive"
    AUTO_ARIMA = "auto_arima"
    AUTO_ETS = "auto_ets"
    ETS = "ets"
    PROPHET = "prophet"
    LWES = "lwe"
    ETS_ANDAR_COSSO = "ets_andar_cc"


class StaffingAlgorithm(str, Enum):
    """Staffing calculation algorithms."""

    ERLANG_C = "erlang_c"
    ERLANG_C_CUMULATIVE = "erlang_c_cumulative"
    eRLANG_X = "erlang_x"
    ADJUSTED_ERLANG_C = "adjusted_erlang_c"


class SchedulingSolver(str, Enum):
    """Scheduling optimization solvers."""

    PYWORKFORCE = "pyworkforce"
    ORTOOLS = "ortools"
    HIORIENT = "hiorient"
    CPLEX = "cplex"
    GUROBI = "gurobi"
    SCIP = "scip"


class OptimizationMethod(str, Enum):
    """Optimization methods."""

    GREEDY = "greedy"
    SIMULATED_ANNEALING = "simulated_annealing"
    GENETIC_ALGORITHM = "genetic_algorithm"
    ANT_COLONY = "ant_colony"
    MULTI_START = "multi_start"
    BARRIER_METHOD = "barrier_method"
    COUPLED_ALGORITHM = "coupled_algorithm"


class ValidationRuleType(str, Enum):
    """Types of validation rules."""

    RANGE = "range"
    ENUM = "enum"
    REGEX = "regex"
    SCHEMA = "schema"
    BUSINESS_LOGIC = "business_logic"
    CONSISTENCY = "consistency"


class SkillType(str, Enum):
    """Skill types for workforce management."""

    VOICE = "voice"
    EMAIL = "email"
    CHAT = "chat"
    SOCIAL_MEDIA = "social_media"
    TECHNICAL_SUPPORT = "technical_support"
    SALES = "sales"
    CUSTOMER_SERVICE = "customer_service"
    BACK_OFFICE = "back_office"


class ChannelType(str, Enum):
    """Channel types."""

    VOICE = "voice"
    EMAIL = "email"
    CHAT = "chat"
    SOCIAL = "social"
    VIDEO = "video"
    FAX = "fax"


class WFMBaseConfig(BaseModel):
    """Base configuration for all WFM operations."""

    name: str | None = Field(
        default=None, description="Configuration name", example="production_config"
    )
    version: str = Field(default="1.0.0", description="Configuration version")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    description: str | None = Field(None, description="Configuration description")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")

    @field_validator("name")
    def validate_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError("Configuration name cannot be empty")
            if len(v) > 100:
                raise ValueError("Configuration name cannot exceed 100 characters")
            return v.strip()
        return v

    @field_validator("version")
    def validate_version(cls, v):
        if not v:
            raise ValueError("Version cannot be empty")
        if not all(c.isalnum() or c in ".-_" for c in v):
            raise ValueError(
                "Version contains invalid characters. Use alphanumeric, dots, hyphens, and underscores only"
            )
        return v


class IntervalConfig(WFMBaseConfig):
    """Configuration for time intervals in WFM calculations."""

    interval_size: int = Field(..., gt=0, description="Size of time interval", example=60)
    interval_unit: TimeInterval = Field(
        ..., description="Unit of time interval", example=TimeInterval.MINUTE
    )
    business_start_hour: int = Field(
        default=9, ge=0, le=23, description="Business start hour (0-23)"
    )
    business_end_hour: int = Field(default=17, ge=0, le=23, description="Business end hour (0-23)")
    working_days: list[int] = Field(
        default_factory=lambda: list(range(1, 6)), description="Working days (1=Monday, 7=Sunday)"
    )
    timezone: str = Field(default="UTC", description="Timezone for calculations")

    @field_validator("business_start_hour", "business_end_hour")
    def validate_hours(cls, v, info):
        field_name = info.field_name
        if v < 0 or v > 23:
            raise ValueError(f"{field_name} must be between 0 and 23")
        return v

    @field_validator("business_end_hour")
    def validate_end_hour(cls, v, info):
        if "business_start_hour" in info.data and v <= info.data["business_start_hour"]:
            raise ValueError("business_end_hour must be after business_start_hour")
        return v

    @field_validator("working_days")
    def validate_working_days(cls, v):
        if not v:
            raise ValueError("At least one working day must be specified")
        for day in v:
            if day < 1 or day > 7:
                raise ValueError(f"Working day {day} must be between 1 and 7")
        return v

    def get_total_business_minutes(self) -> int:
        """Get total business minutes per day."""
        start_minutes = self.business_start_hour * 60
        end_minutes = self.business_end_hour * 60
        return max(0, end_minutes - start_minutes)


class SLAConfig(WFMBaseConfig):
    """Service Level Agreement configuration."""

    target: float = Field(..., gt=0, le=1, description="Target service level", example=0.80)
    average_speed_of_answer: float = Field(
        ..., gt=0, description="Average speed of answer in seconds", example=180
    )
    acceptable_service_level: float = Field(
        default=0.90, gt=0, le=1, description="Acceptable service level"
    )
    minimum_service_level: float = Field(
        default=0.85, gt=0, le=1, description="Minimum service level"
    )
    abandoned_rate_target: float | None = Field(
        None, ge=0, le=1, description="Abandoned call rate target"
    )
    service_level_measurements: list[str] = Field(
        default_factory=list, description="Service level measurement types"
    )

    @field_validator(
        "target", "acceptable_service_level", "minimum_service_level", "abandoned_rate_target"
    )
    def validate_sla_values(cls, v, info):
        field_name = info.field_name
        # Basic range validation (0 to 1)
        if v is not None and (v < 0 or v > 1):
            raise ValueError(f"{field_name} must be between 0 and 1")

        # Cross-field validation using info.data
        if (
            "target" in info.data
            and field_name == "minimum_service_level"
            and v < info.data["target"]
        ):
            raise ValueError("minimum_service_level must be >= target")
        if (
            "acceptable_service_level" in info.data
            and field_name == "minimum_service_level"
            and v > info.data["acceptable_service_level"]
        ):
            raise ValueError("minimum_service_level must be <= acceptable_service_level")

        return v


class ShrinkageConfig(WFMBaseConfig):
    """Shrinkage configuration for workforce management."""

    rate: float = Field(..., ge=0, le=1, description="Shrinkage rate", example=0.30)
    factors: dict[str, float] = Field(
        default_factory=dict, description="Shrinkage factors by category"
    )
    unplanned_absence_rate: float = Field(
        default=0.05, ge=0, le=1, description="Unplanned absence rate"
    )
    planned_absence_rate: float = Field(
        default=0.02, ge=0, le=1, description="Planned absence rate"
    )
    training_time_percentage: float = Field(
        default=0.10, ge=0, le=1, description="Training time percentage"
    )
    meeting_time_percentage: float = Field(
        default=0.05, ge=0, le=1, description="Meeting time percentage"
    )
    break_time_percentage: float = Field(
        default=0.15, ge=0, le=1, description="Break time percentage"
    )

    @field_validator("rate")
    def validate_shrinkage_rate(cls, v):
        if v < 0 or v > 1:
            raise ValueError("Shrinkage rate must be between 0 and 1")
        if v > 0.80:
            raise ValueError("Shrinkage rate seems unusually high (max 0.80)")
        return v

    @field_validator("factors")
    def validate_factors(cls, v):
        if v:
            total_factors = sum(v.values())
            if total_factors > 1.0:
                raise ValueError("Sum of shrinkage factors cannot exceed 1.0")
        return v

    @field_validator("training_time_percentage", "meeting_time_percentage", "break_time_percentage")
    def validate_time_percentages(cls, v, info):
        field_name = info.field_name
        if v < 0 or v > 1:
            raise ValueError(f"{field_name} must be between 0 and 1")
        return v

    def get_productivity_adjustment(self) -> float:
        """Get productivity adjustment factor (1 - shrinkage_rate)."""
        return 1.0 - self.rate


class OccupancyConfig(WFMBaseConfig):
    """Occupancy configuration for workforce management."""

    target: float = Field(..., gt=0, le=1, description="Target occupancy rate", example=0.85)
    maximum: float = Field(default=0.95, gt=0, le=1, description="Maximum occupancy rate")
    minimum: float = Field(default=0.60, gt=0, le=1, description="Minimum occupancy rate")
    calculation_method: str = Field(
        default="utilization", description="Occupancy calculation method"
    )
    include_break_time: bool = Field(default=True, description="Include break time in calculation")
    include_meeting_time: bool = Field(
        default=False, description="Include meeting time in calculation"
    )
    include_training_time: bool = Field(
        default=True, description="Include training time in calculation"
    )

    @field_validator("target", "maximum", "minimum")
    def validate_occupancy_values(cls, v, info):
        field_name = info.field_name
        if v < 0 or v > 1:
            raise ValueError(f"{field_name} must be between 0 and 1")
        return v

    @field_validator("minimum")
    def validate_min_le_target(cls, v, info):
        if "target" in info.data and v > info.data["target"]:
            raise ValueError("minimum must be <= target")
        return v

    @field_validator("maximum")
    def validate_max_ge_target(cls, v, info):
        if "target" in info.data and v < info.data["target"]:
            raise ValueError("maximum must be >= target")
        return v


class SkillConfig(WFMBaseConfig):
    """Skill configuration for workforce management."""

    skill_id: str = Field(..., description="Skill identifier")
    name: str = Field(..., description="Skill name")
    description: str | None = Field(None, description="Skill description")
    skill_type: SkillType = Field(..., description="Skill type")
    channel_type: ChannelType = Field(..., description="Channel type")
    default_handling_time: float = Field(..., gt=0, description="Default handling time in seconds")
    default_appointment_length: float | None = Field(
        None, gt=0, description="Default appointment length in seconds"
    )
    required_skills: list[str] = Field(
        default_factory=list, description="Required skills for this skill"
    )
    optional_skills: list[str] = Field(
        default_factory=list, description="Optional skills for this skill"
    )
    complexity_level: int = Field(default=1, ge=1, le=10, description="Complexity level (1-10)")
    priority: int = Field(default=1, ge=1, le=10, description="Priority (1=lowest, 10=highest)")
    is_active: bool = Field(default=True, description="Whether skill is active")

    @field_validator("skill_id", "name")
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("default_handling_time")
    def validate_handling_time(cls, v):
        if v < 0 or v > 3600:
            raise ValueError("Default handling time must be between 0 and 3600 seconds")
        return v

    @field_validator("complexity_level", "priority")
    def validate_levels(cls, v, info):
        field_name = info.field_name
        if v < 1 or v > 10:
            raise ValueError(f"{field_name} must be between 1 and 10")
        return v


class ChannelConfig(WFMBaseConfig):
    """Channel configuration for workforce management."""

    channel_id: str = Field(..., description="Channel identifier")
    name: str = Field(..., description="Channel name")
    channel_type: ChannelType = Field(..., description="Channel type")
    default_handling_time: float = Field(..., gt=0, description="Default handling time in seconds")
    default_appointment_length: float | None = Field(
        None, gt=0, description="Default appointment length in seconds"
    )
    max_concurrent_agents: int = Field(..., gt=0, description="Maximum concurrent agents")
    average_handle_time: float = Field(..., gt=0, description="Average handle time in seconds")
    queue_limit: int | None = Field(None, gt=0, description="Queue limit")
    skill_required: bool = Field(
        default=True, description="Whether channel requires specific skills"
    )

    @field_validator("channel_id", "name")
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("default_handling_time")
    def validate_handling_time(cls, v):
        if v < 0 or v > 7200:
            raise ValueError("Handling time must be between 0 and 7200 seconds")
        return v


class ForecastConfig(WFMBaseConfig):
    """Forecasting configuration for workforce management."""

    model_type: ForecastModel = Field(..., description="Forecasting model type")
    forecast_horizon: int = Field(..., gt=0, description="Forecast horizon in intervals")
    seasonality: int | None = Field(None, gt=0, description="Seasonality pattern")
    confidence_interval: float = Field(default=0.95, ge=0, le=1, description="Confidence interval")
    include_external_factors: bool = Field(default=False, description="Include external factors")
    data_sources: list[str] = Field(
        default_factory=list, description="Data sources for forecasting"
    )

    @field_validator("forecast_horizon")
    def validate_forecast_horizon(cls, v):
        if v < 1 or v > 8760:
            raise ValueError("Forecast horizon must be between 1 and 8760 intervals")
        return v

    @field_validator("seasonality")
    def validate_seasonality(cls, v):
        if v is not None and (v < 1 or v > 365):
            raise ValueError("Seasonality must be between 1 and 365")
        return v

    @field_validator("confidence_interval")
    def validate_confidence_interval(cls, v):
        if v <= 0 or v >= 1:
            raise ValueError("Confidence interval must be between 0 and 1")
        return v


class StaffingConfig(WFMBaseConfig):
    """Staffing configuration for workforce management."""

    algorithm: StaffingAlgorithm = Field(..., description="Staffing algorithm")
    service_level_config: SLAConfig | None = Field(None, description="Service level configuration")
    interval_config: IntervalConfig | None = Field(None, description="Interval configuration")
    shrinkage_config: ShrinkageConfig | None = Field(None, description="Shrinkage configuration")
    occupancy_config: OccupancyConfig | None = Field(None, description="Occupancy configuration")
    skills: list[SkillConfig] = Field(default_factory=list, description="Skills configuration")
    channels: list[ChannelConfig] = Field(
        default_factory=list, description="Channels configuration"
    )
    historical_data_hours: int = Field(
        default=168, gt=0, description="Historical data hours to analyze"
    )
    demand_forecast_multiplier: float = Field(
        default=1.0, gt=0, description="Demand forecast multiplier"
    )
    weekend_factor: float = Field(default=1.2, gt=0, description="Weekend demand factor")
    holiday_factor: float = Field(default=1.5, gt=0, description="Holiday demand factor")

    @field_validator("historical_data_hours")
    def validate_historical_data_hours(cls, v):
        if v < 1 or v > 8760:
            raise ValueError("Historical data hours must be between 1 and 8760")
        return v

    @field_validator("demand_forecast_multiplier", "weekend_factor", "holiday_factor")
    def validate_factors(cls, v, info):
        field_name = info.field_name
        if v < 0:
            raise ValueError(f"{field_name} must be positive")
        if v > 10:
            raise ValueError(f"{field_name} seems unusually high (max 10)")
        return v


class SchedulingConfig(WFMBaseConfig):
    """Scheduling configuration for workforce management."""

    solver: SchedulingSolver = Field(..., description="Scheduling solver")
    max_hours_per_agent: float = Field(..., gt=0, description="Maximum hours per agent per period")
    min_hours_per_agent: float = Field(
        default=0, ge=0, description="Minimum hours per agent per period"
    )
    break_policy: str = Field(default="standard", description="Break policy")
    shift_length: int = Field(default=8, gt=0, description="Shift length in hours")
    allowed_shift_patterns: list[dict[str, Any]] = Field(
        default_factory=list, description="Allowed shift patterns"
    )
    constraints: dict[str, Any] = Field(default_factory=dict, description="Scheduling constraints")
    optimization_objective: str = Field(default="fairness", description="Optimization objective")
    time_window: dict[str, Any] = Field(
        default_factory=dict, description="Time window for scheduling"
    )

    @field_validator("shift_length")
    def validate_shift_length(cls, v):
        if v < 1 or v > 24:
            raise ValueError("Shift length must be between 1 and 24 hours")
        return v


class OptimizationConfig(WFMBaseConfig):
    """Optimization configuration for workforce management."""

    method: OptimizationMethod = Field(..., description="Optimization method")
    objective_weights: dict[str, float] = Field(
        default_factory=dict, description="Objective weights"
    )
    constraint_weights: dict[str, float] = Field(
        default_factory=dict, description="Constraint weights"
    )
    max_iterations: int = Field(default=1000, gt=0, description="Maximum iterations")
    convergence_threshold: float = Field(default=0.001, gt=0, description="Convergence threshold")
    population_size: int = Field(
        default=100, gt=0, description="Population size for evolutionary algorithms"
    )
    mutation_rate: float = Field(default=0.1, ge=0, le=1, description="Mutation rate")
    crossover_rate: float = Field(default=0.8, ge=0, le=1, description="Crossover rate")

    @field_validator("max_iterations")
    def validate_max_iterations(cls, v):
        if v < 1 or v > 100000:
            raise ValueError("Max iterations must be between 1 and 100000")
        return v

    @field_validator("convergence_threshold")
    def validate_convergence_threshold(cls, v):
        if v <= 0 or v >= 1:
            raise ValueError("Convergence threshold must be between 0 and 1")
        return v


class ValidationConfig(WFMBaseConfig):
    """Validation configuration for workforce management."""

    strict_mode: bool = Field(default=False, description="Enable strict validation mode")
    auto_fix: bool = Field(default=True, description="Auto-fix validation errors")
    rules: list[dict[str, Any]] = Field(default_factory=list, description="Validation rules")
    schemas: list[dict[str, Any]] = Field(default_factory=list, description="Validation schemas")
    threshold: float = Field(default=0.95, ge=0, le=1, description="Validation threshold")
    backup_before_validation: bool = Field(
        default=True, description="Create backup before validation"
    )


class WFMConfig(WFMBaseConfig):
    """Main Workforce Management configuration containing all sub-configurations."""

    operating_profile: OperatingProfile = Field(..., description="Operating profile")
    interval_config: IntervalConfig = Field(..., description="Interval configuration")
    sla_config: SLAConfig = Field(..., description="SLA configuration")
    shrinkage_config: ShrinkageConfig = Field(..., description="Shrinkage configuration")
    occupancy_config: OccupancyConfig = Field(..., description="Occupancy configuration")
    forecast_config: ForecastConfig | None = Field(None, description="Forecasting configuration")
    staffing_config: StaffingConfig | None = Field(None, description="Staffing configuration")
    scheduling_config: SchedulingConfig | None = Field(None, description="Scheduling configuration")
    optimization_config: OptimizationConfig | None = Field(
        None, description="Optimization configuration"
    )
    validation_config: ValidationConfig | None = Field(None, description="Validation configuration")
    skills: list[SkillConfig] = Field(default_factory=list, description="Skills configuration")
    channels: list[ChannelConfig] = Field(
        default_factory=list, description="Channels configuration"
    )

    @model_validator(mode="after")
    def validate_configs_exist(self):
        """Ensure required configs exist based on operating profile."""
        if self.operating_profile in [
            OperatingProfile.INBOUND,
            OperatingProfile.BLENDED,
            OperatingProfile.MULTI_SKILL,
        ]:
            if self.forecast_config is None:
                raise ValueError(
                    f"forecast_config is required for operating profile: {self.operating_profile}"
                )
        if self.operating_profile in [
            OperatingProfile.INBOUND,
            OperatingProfile.OUTBOUND,
            OperatingProfile.BLENDED,
            OperatingProfile.MULTI_SKILL,
        ]:
            if self.staffing_config is None:
                raise ValueError(
                    f"staffing_config is required for operating profile: {self.operating_profile}"
                )
        if self.operating_profile in [
            OperatingProfile.INBOUND,
            OperatingProfile.OUTBOUND,
            OperatingProfile.BLENDED,
            OperatingProfile.MULTI_SKILL,
        ]:
            if self.scheduling_config is None:
                raise ValueError(
                    f"scheduling_config is required for operating profile: {self.operating_profile}"
                )
        return self

    @field_validator("channels")
    def validate_channels_exist(cls, v, info):
        """Ensure channels are defined."""
        # Only require channels for multi-skill profile, not all profiles
        if (
            info.data
            and "operating_profile" in info.data
            and info.data["operating_profile"] == OperatingProfile.MULTI_SKILL
        ):
            if not v:
                raise ValueError(
                    "At least one channel is required for multi_skill operating profile"
                )
        return v

    @field_validator("skills")
    def validate_skills_exist(cls, v, info):
        """Ensure skills are defined for multi-skill operating profile."""
        if (
            info.data
            and "operating_profile" in info.data
            and info.data["operating_profile"] == OperatingProfile.MULTI_SKILL
        ):
            if not v:
                raise ValueError("At least one skill is required for multi_skill operating profile")
        return v

    def get_valid_operating_profile(self) -> OperatingProfile:
        """Get valid operating profile based on configuration."""
        return self.operating_profile

    def get_required_components(self) -> list[str]:
        """Get required components based on operating profile."""
        components = []
        if self.operating_profile in [
            OperatingProfile.INBOUND,
            OperatingProfile.BLENDED,
            OperatingProfile.MULTI_SKILL,
        ]:
            components.append("forecasting")
        if self.operating_profile in [
            OperatingProfile.INBOUND,
            OperatingProfile.OUTBOUND,
            OperatingProfile.BLENDED,
            OperatingProfile.MULTI_SKILL,
        ]:
            components.append("staffing")
        if self.operating_profile in [
            OperatingProfile.INBOUND,
            OperatingProfile.OUTBOUND,
            OperatingProfile.BLENDED,
            OperatingProfile.MULTI_SKILL,
        ]:
            components.append("scheduling")
        if self.operating_profile in [
            OperatingProfile.INBOUND,
            OperatingProfile.OUTBOUND,
            OperatingProfile.BLENDED,
        ]:
            components.append("optimization")
        return components

    def merge_with_default(self, default_config: dict[str, Any]) -> WFMConfig:
        """Merge configuration with default values."""
        config_dict = self.model_dump()

        def merge_dicts(target, default):
            for key, value in default.items():
                if key not in target or target[key] is None:
                    target[key] = value
                elif isinstance(target[key], dict) and isinstance(value, dict):
                    merge_dicts(target[key], value)
                elif isinstance(target[key], list) and isinstance(value, list):
                    if not target[key]:
                        target[key] = value
            return target

        merged_dict = merge_dicts(config_dict, default_config)
        return WFMConfig(**merged_dict)


def load_config_from_yaml(file_path: str) -> WFMConfig:
    """Load configuration from YAML file."""
    with open(file_path) as f:
        data = yaml.safe_load(f)

    return WFMConfig(**data)


def load_config_from_json(file_path: str) -> WFMConfig:
    """Load configuration from JSON file."""
    with open(file_path) as f:
        data = json.load(f)

    return WFMConfig(**data)


def validate_config_dict(config_dict: dict[str, Any]) -> WFMConfig:
    """Validate configuration dictionary and return WFMConfig object."""
    try:
        return WFMConfig(**config_dict)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            error_msg = error["msg"]
            errors.append(f"{field_path}: {error_msg}")

        raise ValueError("Configuration validation failed: " + "; ".join(errors))


# Example configurations for different operating profiles
def get_inbound_example_config() -> WFMConfig:
    """Get example configuration for inbound operating profile."""
    return WFMConfig(
        name="inbound_example",
        version="1.0.0",
        description="Example configuration for inbound operating profile",
        operating_profile=OperatingProfile.INBOUND,
        interval_config=IntervalConfig(
            interval_size=60,
            interval_unit=TimeInterval.MINUTE,
            business_start_hour=8,
            business_end_hour=18,
            working_days=list(range(1, 6)),
            timezone="UTC",
        ),
        sla_config=SLAConfig(
            target=0.80,
            average_speed_of_answer=180,
            acceptable_service_level=0.90,
            minimum_service_level=0.80,
        ),
        shrinkage_config=ShrinkageConfig(
            rate=0.30,
            factors={},
            unplanned_absence_rate=0.05,
            planned_absence_rate=0.02,
            training_time_percentage=0.10,
            meeting_time_percentage=0.05,
            break_time_percentage=0.15,
        ),
        occupancy_config=OccupancyConfig(target=0.85, maximum=0.95, minimum=0.60),
        forecast_config=ForecastConfig(
            model_type=ForecastModel.AUTO_ARIMA,
            forecast_horizon=168,
            seasonality=7,
            confidence_interval=0.95,
        ),
        staffing_config=StaffingConfig(
            algorithm=StaffingAlgorithm.ERLANG_C,
            service_level_config=None,
            interval_config=None,
            shrinkage_config=None,
            occupancy_config=None,
            skills=[],
            channels=[],
        ),
        scheduling_config=SchedulingConfig(
            solver=SchedulingSolver.PYWORKFORCE,
            max_hours_per_agent=8,
            min_hours_per_agent=0,
            shift_length=8,
        ),
        optimization_config=OptimizationConfig(
            method=OptimizationMethod.GREEDY,
            objective_weights={},
            constraint_weights={},
            max_iterations=1000,
        ),
        validation_config=ValidationConfig(strict_mode=False, auto_fix=True, rules=[]),
        skills=[
            SkillConfig(
                skill_id="voice_call",
                name="Voice Call",
                skill_type=SkillType.VOICE,
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                complexity_level=5,
                priority=10,
            )
        ],
        channels=[
            ChannelConfig(
                channel_id="voice_support",
                name="Voice Support",
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                max_concurrent_agents=50,
                average_handle_time=180,
            )
        ],
    )


def get_outbound_example_config() -> WFMConfig:
    """Get example configuration for outbound operating profile."""
    return WFMConfig(
        name="outbound_example",
        version="1.0.0",
        description="Example configuration for outbound operating profile",
        operating_profile=OperatingProfile.OUTBOUND,
        interval_config=IntervalConfig(
            interval_size=60,
            interval_unit=TimeInterval.MINUTE,
            business_start_hour=8,
            business_end_hour=18,
            working_days=list(range(1, 6)),
            timezone="UTC",
        ),
        sla_config=SLAConfig(
            target=0.75,
            average_speed_of_answer=240,
            acceptable_service_level=0.85,
            minimum_service_level=0.75,
        ),
        shrinkage_config=ShrinkageConfig(
            rate=0.35,
            factors={},
            unplanned_absence_rate=0.06,
            planned_absence_rate=0.03,
            training_time_percentage=0.08,
            meeting_time_percentage=0.06,
            break_time_percentage=0.12,
        ),
        occupancy_config=OccupancyConfig(target=0.80, maximum=0.90, minimum=0.60),
        forecast_config=ForecastConfig(
            model_type=ForecastModel.AUTO_ETS,
            forecast_horizon=144,
            seasonality=7,
            confidence_interval=0.90,
        ),
        staffing_config=StaffingConfig(
            algorithm=StaffingAlgorithm.ERLANG_C_CUMULATIVE,
            service_level_config=None,
            interval_config=None,
            shrinkage_config=None,
            occupancy_config=None,
            skills=[],
            channels=[],
        ),
        scheduling_config=SchedulingConfig(
            solver=SchedulingSolver.ORTOOLS,
            max_hours_per_agent=8,
            min_hours_per_agent=0,
            shift_length=8,
        ),
        optimization_config=OptimizationConfig(
            method=OptimizationMethod.SIMULATED_ANNEALING,
            objective_weights={},
            constraint_weights={},
            max_iterations=2000,
        ),
        validation_config=ValidationConfig(strict_mode=False, auto_fix=True, rules=[]),
        skills=[
            SkillConfig(
                skill_id="sales_call",
                name="Sales Call",
                skill_type=SkillType.SALES,
                channel_type=ChannelType.VOICE,
                default_handling_time=240,
                complexity_level=7,
                priority=8,
            )
        ],
        channels=[],
    )


def get_blended_example_config() -> WFMConfig:
    """Get example configuration for blended operating profile."""
    return WFMConfig(
        name="blended_example",
        version="1.0.0",
        description="Example configuration for blended operating profile",
        operating_profile=OperatingProfile.BLENDED,
        interval_config=IntervalConfig(
            interval_size=60,
            interval_unit=TimeInterval.MINUTE,
            business_start_hour=8,
            business_end_hour=18,
            working_days=list(range(1, 6)),
            timezone="UTC",
        ),
        sla_config=SLAConfig(
            target=0.80,
            average_speed_of_answer=180,
            acceptable_service_level=0.85,
            minimum_service_level=0.80,
        ),
        shrinkage_config=ShrinkageConfig(
            rate=0.30,
            factors={},
            unplanned_absence_rate=0.05,
            planned_absence_rate=0.02,
            training_time_percentage=0.10,
            meeting_time_percentage=0.05,
            break_time_percentage=0.15,
        ),
        occupancy_config=OccupancyConfig(target=0.85, maximum=0.95, minimum=0.60),
        forecast_config=ForecastConfig(
            model_type=ForecastModel.AUTO_ARIMA,
            forecast_horizon=168,
            seasonality=7,
            confidence_interval=0.95,
        ),
        staffing_config=StaffingConfig(
            algorithm=StaffingAlgorithm.ERLANG_C,
            service_level_config=None,
            interval_config=None,
            shrinkage_config=None,
            occupancy_config=None,
            skills=[],
            channels=[],
        ),
        scheduling_config=SchedulingConfig(
            solver=SchedulingSolver.PYWORKFORCE,
            max_hours_per_agent=8,
            min_hours_per_agent=0,
            shift_length=8,
        ),
        optimization_config=OptimizationConfig(
            method=OptimizationMethod.GREEDY,
            objective_weights={},
            constraint_weights={},
            max_iterations=1000,
        ),
        validation_config=ValidationConfig(strict_mode=False, auto_fix=True, rules=[]),
        skills=[
            SkillConfig(
                skill_id="voice_call",
                name="Voice Call",
                skill_type=SkillType.VOICE,
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                complexity_level=5,
                priority=10,
            ),
            SkillConfig(
                skill_id="email_support",
                name="Email Support",
                skill_type=SkillType.EMAIL,
                channel_type=ChannelType.EMAIL,
                default_handling_time=600,
                complexity_level=4,
                priority=8,
            ),
        ],
        channels=[
            ChannelConfig(
                channel_id="voice_support",
                name="Voice Support",
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                max_concurrent_agents=50,
                average_handle_time=180,
            ),
            ChannelConfig(
                channel_id="email_support",
                name="Email Support",
                channel_type=ChannelType.EMAIL,
                default_handling_time=600,
                max_concurrent_agents=100,
                average_handle_time=600,
            ),
        ],
    )


def get_multi_skill_example_config() -> WFMConfig:
    """Get example configuration for multi-skill operating profile."""
    return WFMConfig(
        name="multi_skill_example",
        version="1.0.0",
        description="Example configuration for multi-skill operating profile",
        operating_profile=OperatingProfile.MULTI_SKILL,
        interval_config=IntervalConfig(
            interval_size=60,
            interval_unit=TimeInterval.MINUTE,
            business_start_hour=8,
            business_end_hour=18,
            working_days=list(range(1, 6)),
            timezone="UTC",
        ),
        sla_config=SLAConfig(
            target=0.85,
            average_speed_of_answer=120,
            acceptable_service_level=0.90,
            minimum_service_level=0.85,
        ),
        shrinkage_config=ShrinkageConfig(
            rate=0.25,
            factors={},
            unplanned_absence_rate=0.04,
            planned_absence_rate=0.01,
            training_time_percentage=0.12,
            meeting_time_percentage=0.05,
            break_time_percentage=0.15,
        ),
        occupancy_config=OccupancyConfig(target=0.88, maximum=0.95, minimum=0.65),
        forecast_config=ForecastConfig(
            model_type=ForecastModel.AUTO_ARIMA,
            forecast_horizon=168,
            seasonality=7,
            confidence_interval=0.95,
        ),
        staffing_config=StaffingConfig(
            algorithm=StaffingAlgorithm.eRLANG_X,
            service_level_config=None,
            interval_config=None,
            shrinkage_config=None,
            occupancy_config=None,
            skills=[],
            channels=[],
        ),
        scheduling_config=SchedulingConfig(
            solver=SchedulingSolver.ORTOOLS,
            max_hours_per_agent=8,
            min_hours_per_agent=0,
            shift_length=8,
        ),
        optimization_config=OptimizationConfig(
            method=OptimizationMethod.GENETIC_ALGORITHM,
            objective_weights={},
            constraint_weights={},
            max_iterations=5000,
        ),
        validation_config=ValidationConfig(strict_mode=True, auto_fix=False, rules=[]),
        skills=[
            SkillConfig(
                skill_id="voice_call",
                name="Voice Call",
                skill_type=SkillType.VOICE,
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                complexity_level=5,
                priority=10,
            ),
            SkillConfig(
                skill_id="chat_support",
                name="Chat Support",
                skill_type=SkillType.CHAT,
                channel_type=ChannelType.CHAT,
                default_handling_time=300,
                complexity_level=6,
                priority=9,
            ),
            SkillConfig(
                skill_id="email_support",
                name="Email Support",
                skill_type=SkillType.EMAIL,
                channel_type=ChannelType.EMAIL,
                default_handling_time=600,
                complexity_level=4,
                priority=8,
            ),
            SkillConfig(
                skill_id="technical_support",
                name="Technical Support",
                skill_type=SkillType.TECHNICAL_SUPPORT,
                channel_type=ChannelType.CHAT,
                default_handling_time=420,
                complexity_level=8,
                priority=10,
            ),
        ],
        channels=[
            ChannelConfig(
                channel_id="voice_support",
                name="Voice Support",
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                max_concurrent_agents=50,
                average_handle_time=180,
            ),
            ChannelConfig(
                channel_id="chat_support",
                name="Chat Support",
                channel_type=ChannelType.CHAT,
                default_handling_time=300,
                max_concurrent_agents=75,
                average_handle_time=300,
            ),
            ChannelConfig(
                channel_id="email_support",
                name="Email Support",
                channel_type=ChannelType.EMAIL,
                default_handling_time=600,
                max_concurrent_agents=100,
                average_handle_time=600,
            ),
        ],
    )
