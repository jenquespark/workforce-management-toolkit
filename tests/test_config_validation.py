"""Tests for Workforce Management Toolkit configuration validation.

Tests for Pydantic-based configuration schemas with comprehensive validation
for all WFM operations including forecasting, staffing, scheduling,
optimization, and validation.

Tests follow TDD approach with synthetic fixtures.
"""

import pytest
import json
import yaml
import tempfile
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Import the configuration models
from wfm_harness.config import (
    WFMConfig,
    IntervalConfig,
    TimeInterval,
    SLAConfig,
    ShrinkageConfig,
    OccupancyConfig,
    SkillConfig,
    SkillType,
    ChannelConfig,
    ChannelType,
    ForecastConfig,
    ForecastModel,
    StaffingConfig,
    StaffingAlgorithm,
    SchedulingConfig,
    SchedulingSolver,
    OptimizationConfig,
    OptimizationMethod,
    ValidationConfig,
    OperatingProfile,
    load_config_from_yaml,
    load_config_from_json,
    validate_config_dict,
    get_inbound_example_config,
    get_outbound_example_config,
    get_blended_example_config,
    get_multi_skill_example_config
)
class TestWFMBaseConfig:
    """Test WFMBaseConfig base class."""

    def test_valid_base_config(self):
        """Test creating a valid base configuration."""
        from wfm_harness.config import ForecastConfig, ForecastModel
        
        config = WFMConfig(
            name="test_config",
            version="1.0.0",
            description="Test configuration",
            tags=["test", "example"],
            operating_profile=OperatingProfile.INBOUND,
            interval_config=IntervalConfig(
                interval_size=60,
                interval_unit=TimeInterval.MINUTE
            ),
            sla_config=SLAConfig(
                target=0.80,
                average_speed_of_answer=180
            ),
            shrinkage_config=ShrinkageConfig(rate=0.30),
            occupancy_config=OccupancyConfig(target=0.85),
            forecast_config=ForecastConfig(
                model_type=ForecastModel.AUTO_ARIMA,
                forecast_horizon=168,
                seasonality=7,
                confidence_interval=0.95
            ),
            staffing_config=StaffingConfig(
                algorithm=StaffingAlgorithm.ERLANG_C,
                skills=[],
                channels=[]
            ),
            scheduling_config=SchedulingConfig(
                solver=SchedulingSolver.PYWORKFORCE,
                max_hours_per_agent=8,
                min_hours_per_agent=0,
                shift_length=8
            ),
            skills=[],
            channels=[]
        )
        
        assert config.name == "test_config"
        assert config.version == "1.0.0"
        assert config.description == "Test configuration"
        assert "test" in config.tags
        assert "example" in config.tags
        assert config.operating_profile == OperatingProfile.INBOUND
        assert config.interval_config.interval_size == 60
        assert config.interval_config.interval_unit == TimeInterval.MINUTE
        assert config.sla_config.target == 0.80
        assert config.sla_config.average_speed_of_answer == 180
        assert config.shrinkage_config.rate == 0.30
        assert config.occupancy_config.target == 0.85
        assert config.forecast_config is not None
        assert config.forecast_config.model_type == ForecastModel.AUTO_ARIMA
        assert len(config.skills) == 0
        assert len(config.channels) == 0

    def test_name_validation_empty(self):
        """Test validation for empty name."""
        with pytest.raises(ValueError, match="Configuration name cannot be empty"):
            WFMConfig(
                name="",
                version="1.0.0",
                operating_profile=OperatingProfile.INBOUND,
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                skills=[],
                channels=[]
            )

    def test_name_validation_too_long(self):
        """Test validation for name that's too long."""
        long_name = "a" * 101
        with pytest.raises(ValueError, match="Configuration name cannot exceed 100 characters"):
            WFMConfig(
                name=long_name,
                version="1.0.0",
                operating_profile=OperatingProfile.INBOUND,
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                skills=[],
                channels=[]
            )

    def test_version_validation_empty(self):
        """Test validation for empty version."""
        with pytest.raises(ValueError, match="Version cannot be empty"):
            WFMConfig(
                name="test",
                version="",
                operating_profile=OperatingProfile.INBOUND,
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                skills=[],
                channels=[]
            )

    def test_version_validation_invalid_chars(self):
        """Test validation for version with invalid characters."""
        with pytest.raises(ValueError, match="Version contains invalid characters"):
            WFMConfig(
                name="test",
                version="1.0.0-beta@",
                operating_profile=OperatingProfile.INBOUND,
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                skills=[],
                channels=[]
            )
class TestIntervalConfig:
    """Test IntervalConfig configuration."""

    def test_valid_interval_config(self):
        """Test creating a valid interval configuration."""
        config = IntervalConfig(
            interval_size=60,
            interval_unit=TimeInterval.MINUTE,
            business_start_hour=8,
            business_end_hour=18,
            working_days=[1, 2, 3, 4, 5],
            timezone="UTC"
        )
        
        assert config.interval_size == 60
        assert config.interval_unit == TimeInterval.MINUTE
        assert config.business_start_hour == 8
        assert config.business_end_hour == 18
        assert config.working_days == [1, 2, 3, 4, 5]
        assert config.timezone == "UTC"

    def test_invalid_hours(self):
        """Test validation for invalid business hours."""
        with pytest.raises(ValueError, match="business_start_hour must be between 0 and 23"):
            IntervalConfig(
                interval_size=60,
                interval_unit=TimeInterval.MINUTE,
                business_start_hour=25,
                business_end_hour=18
            )

    def test_end_hour_before_start(self):
        """Test validation for end hour before start hour."""
        with pytest.raises(ValueError, match="business_end_hour must be after business_start_hour"):
            IntervalConfig(
                interval_size=60,
                interval_unit=TimeInterval.MINUTE,
                business_start_hour=17,
                business_end_hour=8
            )

    def test_working_days_empty(self):
        """Test validation for empty working days."""
        with pytest.raises(ValueError, match="At least one working day must be specified"):
            IntervalConfig(
                interval_size=60,
                interval_unit=TimeInterval.MINUTE,
                business_start_hour=8,
                business_end_hour=18,
                working_days=[]
            )

    def test_working_days_invalid(self):
        """Test validation for invalid working day numbers."""
        with pytest.raises(ValueError, match="Working day 0 must be between 1 and 7"):
            IntervalConfig(
                interval_size=60,
                interval_unit=TimeInterval.MINUTE,
                business_start_hour=8,
                business_end_hour=18,
                working_days=[0, 1, 2, 3, 4]
            )

    def test_get_total_business_minutes(self):
        """Test getting total business minutes."""
        config = IntervalConfig(
            interval_size=60,
            interval_unit=TimeInterval.MINUTE,
            business_start_hour=8,
            business_end_hour=18
        )
        assert config.get_total_business_minutes() == 600  # 10 hours * 60 minutes

    def test_get_total_business_minutes_negative(self):
        """Test getting total business minutes with negative result."""
        config = IntervalConfig(
            interval_size=60,
            interval_unit=TimeInterval.MINUTE,
            business_start_hour=17,
            business_end_hour=8
        )
        assert config.get_total_business_minutes() == 0  # End before start = 0
class TestSLAConfig:
    """Test SLAConfig configuration."""

    def test_valid_sla_config(self):
        """Test creating a valid SLA configuration."""
        config = SLAConfig(
            target=0.80,
            average_speed_of_answer=180,
            acceptable_service_level=0.90,
            minimum_service_level=0.95,
            abandoned_rate_target=0.05,
            service_level_measurements=["calls_answered", "average_speed_of_answer"]
        )
        
        assert config.target == 0.80
        assert config.average_speed_of_answer == 180
        assert config.acceptable_service_level == 0.90
        assert config.minimum_service_level == 0.95
        assert config.abandoned_rate_target == 0.05
        assert len(config.service_level_measurements) == 2

    def test_sla_values_out_of_range(self):
        """Test validation for SLA values out of range."""
        with pytest.raises(ValueError, match="Input should be less than or equal to 1"):
            SLAConfig(
                target=1.5,  # Invalid: > 1
                average_speed_of_answer=180
            )

    def test_minimum_less_than_target(self):
        """Test validation for minimum service level less than target."""
        with pytest.raises(ValueError, match="minimum_service_level must be >= target"):
            SLAConfig(
                target=0.90,
                average_speed_of_answer=180,
                minimum_service_level=0.85  # Invalid: < target
            )

    def test_minimum_greater_than_acceptable(self):
        """Test validation for minimum service level greater than acceptable."""
        with pytest.raises(ValueError, match="minimum_service_level must be <= acceptable_service_level"):
            SLAConfig(
                target=0.80,
                average_speed_of_answer=180,
                acceptable_service_level=0.85,
                minimum_service_level=0.90  # Invalid: > acceptable
            )
class TestShrinkageConfig:
    """Test ShrinkageConfig configuration."""

    def test_valid_shrinkage_config(self):
        """Test creating a valid shrinkage configuration."""
        config = ShrinkageConfig(
            rate=0.30,
            factors={"break": 0.15, "training": 0.10, "meeting": 0.05},
            unplanned_absence_rate=0.05,
            planned_absence_rate=0.02,
            training_time_percentage=0.10,
            meeting_time_percentage=0.05,
            break_time_percentage=0.15
        )
        
        assert config.rate == 0.30
        assert config.factors["break"] == 0.15
        assert config.factors["training"] == 0.10
        assert config.factors["meeting"] == 0.05
        assert config.unplanned_absence_rate == 0.05
        assert config.planned_absence_rate == 0.02
        assert config.training_time_percentage == 0.10
        assert config.meeting_time_percentage == 0.05
        assert config.break_time_percentage == 0.15

    def test_shrinkage_rate_out_of_range(self):
        """Test validation for shrinkage rate out of range."""
        with pytest.raises(ValueError, match="Input should be less than or equal to 1"):
            ShrinkageConfig(rate=1.5)  # Invalid: > 1

    def test_shrinkage_rate_too_high(self):
        """Test validation for unusually high shrinkage rate."""
        with pytest.raises(ValueError, match="Shrinkage rate seems unusually high"):
            ShrinkageConfig(rate=0.85)  # Invalid: > 0.80

    def test_factors_sum_exceeds_one(self):
        """Test validation for factors that sum to more than 1."""
        with pytest.raises(ValueError, match="Sum of shrinkage factors cannot exceed 1.0"):
            ShrinkageConfig(
                rate=0.30,
                factors={"break": 0.50, "training": 0.60, "meeting": 0.40}  # Sum = 1.5 > 1.0
            )

    def test_time_percentages_out_of_range(self):
        """Test validation for time percentages out of range."""
        with pytest.raises(ValueError, match="Input should be less than or equal to 1"):
            ShrinkageConfig(
                rate=0.30,
                training_time_percentage=1.5  # Invalid: > 1
            )

    def test_get_productivity_adjustment(self):
        """Test getting productivity adjustment factor."""
        config = ShrinkageConfig(rate=0.30)
        assert config.get_productivity_adjustment() == 0.70  # 1 - 0.30

    def test_get_productivity_adjustment_zero(self):
        """Test getting productivity adjustment factor with zero shrinkage."""
        config = ShrinkageConfig(rate=0.0)
        assert config.get_productivity_adjustment() == 1.0  # 1 - 0.0
class TestOccupancyConfig:
    """Test OccupancyConfig configuration."""

    def test_valid_occupancy_config(self):
        """Test creating a valid occupancy configuration."""
        config = OccupancyConfig(
            target=0.85,
            maximum=0.95,
            minimum=0.60,
            calculation_method="utilization",
            include_break_time=True,
            include_meeting_time=False,
            include_training_time=True
        )
        
        assert config.target == 0.85
        assert config.maximum == 0.95
        assert config.minimum == 0.60
        assert config.calculation_method == "utilization"
        assert config.include_break_time is True
        assert config.include_meeting_time is False
        assert config.include_training_time is True

    def test_occupancy_values_out_of_range(self):
        """Test validation for occupancy values out of range."""
        with pytest.raises(ValueError, match="Input should be less than or equal to 1"):
            OccupancyConfig(target=1.5)

    def test_minimum_greater_than_target(self):
        """Test validation for minimum greater than target."""
        with pytest.raises(ValueError, match="minimum must be <= target"):
            OccupancyConfig(target=0.80, minimum=0.90)

    def test_maximum_less_than_target(self):
        """Test validation for maximum less than target."""
        with pytest.raises(ValueError, match="maximum must be >= target"):
            OccupancyConfig(target=0.80, maximum=0.70)
class TestSkillConfig:
    """Test SkillConfig configuration."""

    def test_valid_skill_config(self):
        """Test creating a valid skill configuration."""
        config = SkillConfig(
            skill_id="voice_support",
            name="Voice Support",
            description="Customer service via phone",
            skill_type=SkillType.VOICE,
            channel_type=ChannelType.VOICE,
            default_handling_time=180,
            default_appointment_length=300,
            required_skills=["customer_service", "technical_support"],
            optional_skills=["escalation"],
            complexity_level=5,
            priority=10,
            is_active=True
        )
        
        assert config.skill_id == "voice_support"
        assert config.name == "Voice Support"
        assert config.description == "Customer service via phone"
        assert config.skill_type == SkillType.VOICE
        assert config.channel_type == ChannelType.VOICE
        assert config.default_handling_time == 180
        assert config.default_appointment_length == 300
        assert config.required_skills == ["customer_service", "technical_support"]
        assert config.optional_skills == ["escalation"]
        assert config.complexity_level == 5
        assert config.priority == 10
        assert config.is_active is True

    def test_skill_id_empty(self):
        """Test validation for empty skill ID."""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            SkillConfig(
                skill_id="",
                name="Test Skill",
                skill_type=SkillType.VOICE,
                channel_type=ChannelType.VOICE,
                default_handling_time=180
            )

    def test_name_empty(self):
        """Test validation for empty skill name."""
        with pytest.raises(ValueError, match="Configuration name cannot be empty"):
            SkillConfig(
                skill_id="test_skill",
                name="",
                skill_type=SkillType.VOICE,
                channel_type=ChannelType.VOICE,
                default_handling_time=180
            )

    def test_default_handling_time_out_of_range(self):
        """Test validation for default handling time out of range."""
        with pytest.raises(ValueError, match="Default handling time must be between 0 and 3600 seconds"):
            SkillConfig(
                skill_id="test_skill",
                name="Test Skill",
                skill_type=SkillType.VOICE,
                channel_type=ChannelType.VOICE,
                default_handling_time=3601  # Invalid: > 3600
            )

    def test_complexity_level_out_of_range(self):
        """Test validation for complexity level out of range."""
        with pytest.raises(ValueError, match="complexity_level must be between 1 and 10"):
            SkillConfig(
                skill_id="test_skill",
                name="Test Skill",
                skill_type=SkillType.VOICE,
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                complexity_level=11  # Invalid: > 10
            )

    def test_priority_out_of_range(self):
        """Test validation for priority out of range."""
        with pytest.raises(ValueError, match="priority must be between 1 and 10"):
            SkillConfig(
                skill_id="test_skill",
                name="Test Skill",
                skill_type=SkillType.VOICE,
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                priority=0  # Invalid: < 1
            )
class TestChannelConfig:
    """Test ChannelConfig configuration."""

    def test_valid_channel_config(self):
        """Test creating a valid channel configuration."""
        config = ChannelConfig(
            channel_id="voice_support",
            name="Voice Support",
            channel_type=ChannelType.VOICE,
            description="Phone-based customer support",
            default_handling_time=180,
            max_concurrent_agents=50,
            average_handle_time=180,
            service_level_targets={"service_level": 0.80, "average_speed_of_answer": 180},
            quality_thresholds={"csat": 4.0, "fcsat": 3.0},
            is_active=True
        )
        
        assert config.channel_id == "voice_support"
        assert config.name == "Voice Support"
        assert config.channel_type == ChannelType.VOICE
        assert config.description == "Phone-based customer support"
        assert config.default_handling_time == 180
        assert config.max_concurrent_agents == 50
        assert config.average_handle_time == 180
        assert config.service_level_targets["service_level"] == 0.80
        assert config.quality_thresholds["csat"] == 4.0
        assert config.is_active is True

    def test_channel_id_empty(self):
        """Test validation for empty channel ID."""
        with pytest.raises(ValueError, match="Field cannot be empty"):
            ChannelConfig(
                channel_id="",
                name="Test Channel",
                channel_type=ChannelType.VOICE,
                default_handling_time=180,
                max_concurrent_agents=1,
                average_handle_time=180
            )

    def test_handling_time_out_of_range(self):
        """Test validation for handling time out of range."""
        with pytest.raises(ValueError, match="Handling time must be between 0 and 7200 seconds"):
            ChannelConfig(
                channel_id="test_channel",
                name="Test Channel",
                channel_type=ChannelType.VOICE,
                default_handling_time=7201,  # Invalid: > 7200
                max_concurrent_agents=1,
                average_handle_time=180
            )
class TestForecastConfig:
    """Test ForecastConfig configuration."""

    def test_valid_forecast_config(self):
        """Test creating a valid forecast configuration."""
        config = ForecastConfig(
            model_type=ForecastModel.AUTO_ARIMA,
            forecast_horizon=168,
            seasonality=7,
            confidence_interval=0.95,
            include_weekend_impact=True,
            include_holidays=True,
            holiday_regions=["US", "UK"],
            model_parameters={"p": 1, "d": 1, "q": 1},
            validation_rules=[]
        )
        
        assert config.model_type == ForecastModel.AUTO_ARIMA
        assert config.forecast_horizon == 168
        assert config.seasonality == 7
        assert config.confidence_interval == 0.95
        assert config.include_weekend_impact is True
        assert config.include_holidays is True
        assert config.holiday_regions == ["US", "UK"]
        assert config.model_parameters == {"p": 1, "d": 1, "q": 1}
        assert config.validation_rules == []

    def test_forecast_horizon_out_of_range(self):
        """Test validation for forecast horizon out of range."""
        with pytest.raises(ValueError, match="Forecast horizon must be between 1 and 365 intervals"):
            ForecastConfig(
                model_type=ForecastModel.AUTO_ARIMA,
                forecast_horizon=366  # Invalid: > 365
            )

    def test_seasonality_out_of_range(self):
        """Test validation for seasonality out of range."""
        with pytest.raises(ValueError, match="Seasonality must be between 1 and 365"):
            ForecastConfig(
                model_type=ForecastModel.AUTO_ARIMA,
                forecast_horizon=168,
                seasonality=366  # Invalid: > 365
            )

    def test_confidence_interval_out_of_range(self):
        """Test validation for confidence interval out of range."""
        with pytest.raises(ValueError, match="Confidence interval must be between 0 and 1"):
            ForecastConfig(
                model_type=ForecastModel.AUTO_ARIMA,
                forecast_horizon=168,
                confidence_interval=1.5  # Invalid: > 1
            )

    def test_confidence_interval_zero(self):
        """Test validation for confidence interval of 0."""
        with pytest.raises(ValueError, match="Confidence interval must be between 0 and 1"):
            ForecastConfig(
                model_type=ForecastModel.AUTO_ARIMA,
                forecast_horizon=168,
                confidence_interval=0.0  # Invalid: <= 0
            )
class TestStaffingConfig:
    """Test StaffingConfig configuration."""

    def test_valid_staffing_config(self):
        """Test creating a valid staffing configuration."""
        config = StaffingConfig(
            algorithm=StaffingAlgorithm.ERLANG_C,
            service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
            interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
            shrinkage_config=ShrinkageConfig(rate=0.30),
            occupancy_config=OccupancyConfig(target=0.85),
            skills=[
                SkillConfig(
                    skill_id="voice_support",
                    name="Voice Support",
                    skill_type=SkillType.VOICE,
                    channel_type=ChannelType.VOICE,
                    default_handling_time=180
                )
            ],
            channels=[
                ChannelConfig(
                    channel_id="voice_support",
                    name="Voice Support",
                    channel_type=ChannelType.VOICE,
                    default_handling_time=180,
                    max_concurrent_agents=1,
                    average_handle_time=180
                )
            ],
            historical_data_hours=168,
            demand_forecast_multiplier=1.0,
            weekend_factor=1.2,
            holiday_factor=1.5
        )
        
        assert config.algorithm == StaffingAlgorithm.ERLANG_C
        assert config.service_level_config.target == 0.80
        assert config.interval_config.interval_size == 60
        assert config.shrinkage_config.rate == 0.30
        assert config.occupancy_config.target == 0.85
        assert len(config.skills) == 1
        assert len(config.channels) == 1
        assert config.historical_data_hours == 168
        assert config.demand_forecast_multiplier == 1.0
        assert config.weekend_factor == 1.2
        assert config.holiday_factor == 1.5

    def test_historical_data_hours_out_of_range(self):
        """Test validation for historical data hours out of range."""
        with pytest.raises(ValueError, match="Historical data hours must be between 1 and 8760"):
            StaffingConfig(
                algorithm=StaffingAlgorithm.ERLANG_C,
                service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                historical_data_hours=8761  # Invalid: > 8760
            )

    def test_demand_forecast_multiplier_negative(self):
        """Test validation for negative demand forecast multiplier."""
        with pytest.raises(ValueError, match="demand_forecast_multiplier must be positive"):
            StaffingConfig(
                algorithm=StaffingAlgorithm.ERLANG_C,
                service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                demand_forecast_multiplier=-1.0  # Invalid: negative
            )

    def test_weekend_factor_unusually_high(self):
        """Test validation for unusually high weekend factor."""
        with pytest.raises(ValueError, match="weekend_factor seems unusually high"):
            StaffingConfig(
                algorithm=StaffingAlgorithm.ERLANG_C,
                service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                weekend_factor=20.0  # Invalid: > 10
            )
class TestSchedulingConfig:
    """Test SchedulingConfig configuration."""

    def test_valid_scheduling_config(self):
        """Test creating a valid scheduling configuration."""
        config = SchedulingConfig(
            solver=SchedulingSolver.PYWORKFORCE,
            max_hours_per_agent=8,
            min_hours_per_agent=0,
            break_policy="standard",
            shift_length=8,
            allowed_shift_patterns=[{"start": "09:00", "end": "17:00"}],
            constraints={"max_consecutive_days": 5},
            optimization_objective="fairness",
            time_window={"start": "09:00", "end": "17:00"}
        )
        
        assert config.solver == SchedulingSolver.PYWORKFORCE
        assert config.max_hours_per_agent == 8
        assert config.min_hours_per_agent == 0
        assert config.break_policy == "standard"
        assert config.shift_length == 8
        assert len(config.allowed_shift_patterns) == 1
        assert config.constraints["max_consecutive_days"] == 5
        assert config.optimization_objective == "fairness"
        assert config.time_window["start"] == "09:00"

    def test_shift_length_out_of_range(self):
        """Test validation for shift length out of range."""
        with pytest.raises(ValueError, match="Shift length must be between 1 and 24 hours"):
            SchedulingConfig(
                solver=SchedulingSolver.PYWORKFORCE,
                max_hours_per_agent=8,
                shift_length=25  # Invalid: > 24
            )
class TestOptimizationConfig:
    """Test OptimizationConfig configuration."""

    def test_valid_optimization_config(self):
        """Test creating a valid optimization configuration."""
        config = OptimizationConfig(
            method=OptimizationMethod.GREEDY,
            objective_weights={"cost": 0.7, "fairness": 0.3},
            constraint_weights={"max_hours": 1.0},
            max_iterations=1000,
            convergence_threshold=0.001,
            population_size=100,
            mutation_rate=0.1,
            crossover_rate=0.8
        )
        
        assert config.method == OptimizationMethod.GREEDY
        assert config.objective_weights["cost"] == 0.7
        assert config.objective_weights["fairness"] == 0.3
        assert config.constraint_weights["max_hours"] == 1.0
        assert config.max_iterations == 1000
        assert config.convergence_threshold == 0.001
        assert config.population_size == 100
        assert config.mutation_rate == 0.1
        assert config.crossover_rate == 0.8

    def test_max_iterations_out_of_range(self):
        """Test validation for max iterations out of range."""
        with pytest.raises(ValueError, match="Max iterations must be between 1 and 100000"):
            OptimizationConfig(
                method=OptimizationMethod.GREEDY,
                max_iterations=100001  # Invalid: > 100000
            )

    def test_convergence_threshold_out_of_range(self):
        """Test validation for convergence threshold out of range."""
        with pytest.raises(ValueError, match="Convergence threshold must be between 0 and 1"):
            OptimizationConfig(
                method=OptimizationMethod.GREEDY,
                convergence_threshold=1.5  # Invalid: > 1
            )

    def test_convergence_threshold_zero(self):
        """Test validation for convergence threshold of 0."""
        with pytest.raises(ValueError, match="Convergence threshold must be between 0 and 1"):
            OptimizationConfig(
                method=OptimizationMethod.GREEDY,
                convergence_threshold=0.0  # Invalid: <= 0
            )
class TestValidationConfig:
    """Test ValidationConfig configuration."""

    def test_valid_validation_config(self):
        """Test creating a valid validation configuration."""
        config = ValidationConfig(
            strict_mode=False,
            auto_fix=True,
            rules=[{"type": "range", "field": "target", "min": 0, "max": 1}],
            schemas=[{"name": "WFMData", "fields": ["timestamp", "value"]}],
            threshold=0.95,
            backup_before_validation=True
        )
        
        assert config.strict_mode is False
        assert config.auto_fix is True
        assert len(config.rules) == 1
        assert len(config.schemas) == 1
        assert config.threshold == 0.95
        assert config.backup_before_validation is True

    def test_validation_threshold_out_of_range(self):
        """Test validation for validation threshold out of range."""
        with pytest.raises(ValueError, match="threshold must be between 0 and 1"):
            ValidationConfig(threshold=1.5)  # Invalid: > 1
class TestWFMConfig:
    """Test WFMConfig main configuration."""

    def test_valid_inbound_config(self):
        """Test creating a valid inbound configuration."""
        config = WFMConfig(
            name="inbound_config",
            version="1.0.0",
            description="Inbound WFM configuration",
            operating_profile=OperatingProfile.INBOUND,
            interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
            sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
            shrinkage_config=ShrinkageConfig(rate=0.30),
            occupancy_config=OccupancyConfig(target=0.85),
            forecast_config=ForecastConfig(
                model_type=ForecastModel.AUTO_ARIMA,
                forecast_horizon=168,
                seasonality=7
            ),
            staffing_config=StaffingConfig(
                algorithm=StaffingAlgorithm.ERLANG_C,
                service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                skills=[],
                channels=[]
            ),
            skills=[],
            channels=[]
        )
        
        assert config.name == "inbound_config"
        assert config.operating_profile == OperatingProfile.INBOUND
        assert config.forecast_config is not None
        assert config.staffing_config is not None
        assert config.get_required_components() == ["forecasting", "staffing"]

    def test_valid_outbound_config(self):
        """Test creating a valid outbound configuration."""
        config = WFMConfig(
            name="outbound_config",
            version="1.0.0",
            description="Outbound WFM configuration",
            operating_profile=OperatingProfile.OUTBOUND,
            interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
            sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
            shrinkage_config=ShrinkageConfig(rate=0.30),
            occupancy_config=OccupancyConfig(target=0.85),
            forecast_config=ForecastConfig(
                model_type=ForecastModel.SEASONAL_NAIVE,
                forecast_horizon=168,
                seasonality=7
            ),
            staffing_config=StaffingConfig(
                algorithm=StaffingAlgorithm.ERLANG_C,
                service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                skills=[],
                channels=[]
            ),
            scheduling_config=SchedulingConfig(
                solver=SchedulingSolver.PYWORKFORCE,
                max_hours_per_agent=8,
                min_hours_per_agent=0,
                shift_length=8
            ),
            skills=[],
            channels=[]
        )
        
        assert config.operating_profile == OperatingProfile.OUTBOUND
        assert config.forecast_config is not None
        assert config.staffing_config is not None
        assert config.scheduling_config is not None
        assert config.get_required_components() == ["forecasting", "staffing", "scheduling"]

    def test_valid_blended_config(self):
        """Test creating a valid blended configuration."""
        config = WFMConfig(
            name="blended_config",
            version="1.0.0",
            description="Blended WFM configuration",
            operating_profile=OperatingProfile.BLENDED,
            interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
            sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
            shrinkage_config=ShrinkageConfig(rate=0.30),
            occupancy_config=OccupancyConfig(target=0.85),
            forecast_config=ForecastConfig(
                model_type=ForecastModel.AUTO_ETS,
                forecast_horizon=168,
                seasonality=7
            ),
            staffing_config=StaffingConfig(
                algorithm=StaffingAlgorithm.ERLANG_C,
                service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                skills=[],
                channels=[]
            ),
            scheduling_config=SchedulingConfig(
                solver=SchedulingSolver.PYWORKFORCE,
                max_hours_per_agent=8,
                min_hours_per_agent=0,
                shift_length=8
            ),
            optimization_config=OptimizationConfig(
                method=OptimizationMethod.GREEDY,
                max_iterations=1000
            ),
            skills=[],
            channels=[]
        )
        
        assert config.operating_profile == OperatingProfile.BLENDED
        assert config.forecast_config is not None
        assert config.staffing_config is not None
        assert config.scheduling_config is not None
        assert config.optimization_config is not None
        assert config.get_required_components() == ["forecasting", "staffing", "scheduling", "optimization"]

    def test_valid_multi_skill_config(self):
        """Test creating a valid multi-skill configuration."""
        config = WFMConfig(
            name="multi_skill_config",
            version="1.0.0",
            description="Multi-skill WFM configuration",
            operating_profile=OperatingProfile.MULTI_SKILL,
            interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
            sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
            shrinkage_config=ShrinkageConfig(rate=0.30),
            occupancy_config=OccupancyConfig(target=0.85),
            forecast_config=ForecastConfig(
                model_type=ForecastModel.AUTO_ARIMA,
                forecast_horizon=168,
                seasonality=7
            ),
            staffing_config=StaffingConfig(
                algorithm=StaffingAlgorithm.ERLANG_C,
                service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                skills=[
                    SkillConfig(
                        skill_id="voice_support",
                        name="Voice Support",
                        skill_type=SkillType.VOICE,
                        channel_type=ChannelType.VOICE,
                        default_handling_time=180
                    ),
                    SkillConfig(
                        skill_id="email_support",
                        name="Email Support",
                        skill_type=SkillType.EMAIL,
                        channel_type=ChannelType.EMAIL,
                        default_handling_time=720
                    )
                ],
                channels=[
                    ChannelConfig(
                        channel_id="voice_support",
                        name="Voice Support",
                        channel_type=ChannelType.VOICE,
                        default_handling_time=180,
                        max_concurrent_agents=1,
                        average_handle_time=180
                    ),
                    ChannelConfig(
                        channel_id="email_support",
                        name="Email Support",
                        channel_type=ChannelType.EMAIL,
                        default_handling_time=720,
                        max_concurrent_agents=1,
                        average_handle_time=720
                    )
                ]
            ),
            scheduling_config=SchedulingConfig(
                solver=SchedulingSolver.PYWORKFORCE,
                max_hours_per_agent=8,
                min_hours_per_agent=0,
                shift_length=8
            ),
            optimization_config=OptimizationConfig(
                method=OptimizationMethod.GREEDY,
                max_iterations=1000
            ),
            skills=[
                SkillConfig(
                    skill_id="voice_support",
                    name="Voice Support",
                    skill_type=SkillType.VOICE,
                    channel_type=ChannelType.VOICE,
                    default_handling_time=180
                ),
                SkillConfig(
                    skill_id="email_support",
                    name="Email Support",
                    skill_type=SkillType.EMAIL,
                    channel_type=ChannelType.EMAIL,
                    default_handling_time=720
                )
            ],
            channels=[
                ChannelConfig(
                    channel_id="voice_support",
                    name="Voice Support",
                    channel_type=ChannelType.VOICE,
                    default_handling_time=180,
                    max_concurrent_agents=1,
                    average_handle_time=180
                ),
                ChannelConfig(
                    channel_id="email_support",
                    name="Email Support",
                    channel_type=ChannelType.EMAIL,
                    default_handling_time=720,
                    max_concurrent_agents=1,
                    average_handle_time=720
                )
            ]
        )
        
        assert config.operating_profile == OperatingProfile.MULTI_SKILL
        assert config.staffing_config is not None
        assert len(config.staffing_config.skills) == 2
        assert len(config.staffing_config.channels) == 2
        assert len(config.skills) == 2
        assert len(config.channels) == 2
        assert config.get_required_components() == ["forecasting", "staffing", "scheduling", "optimization"]

    def test_inbound_missing_forecast_config(self):
        """Test that inbound config requires forecast config."""
        with pytest.raises(ValueError, match="forecast_config is required for operating profile: inbound"):
            WFMConfig(
                name="test_config",
                version="1.0.0",
                operating_profile=OperatingProfile.INBOUND,
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                staffing_config=None,  # This is OK for inbound
                scheduling_config=None,  # This is OK for inbound
                optimization_config=None,  # This is OK for inbound
                validation_config=None,
                skills=[],
                channels=[]
            )

    def test_multi_skill_no_skills(self):
        """Test that multi-skill config requires at least one skill."""
        with pytest.raises(ValueError, match="At least one skill is required for multi_skill operating profile"):
            WFMConfig(
                name="test_config",
                version="1.0.0",
                operating_profile=OperatingProfile.MULTI_SKILL,
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                forecast_config=ForecastConfig(
                    model_type=ForecastModel.AUTO_ARIMA,
                    forecast_horizon=168,
                    seasonality=7
                ),
                staffing_config=StaffingConfig(
                    algorithm=StaffingAlgorithm.ERLANG_C,
                    service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                    interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                    shrinkage_config=ShrinkageConfig(rate=0.30),
                    occupancy_config=OccupancyConfig(target=0.85),
                    skills=[],  # Empty!
                    channels=[]
                ),
                skills=[],  # Empty!
                channels=[]
            )

    def test_no_channels(self):
        """Test that config requires at least one channel."""
        with pytest.raises(ValueError, match="At least one channel is required"):
            WFMConfig(
                name="test_config",
                version="1.0.0",
                operating_profile=OperatingProfile.INBOUND,
                interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                shrinkage_config=ShrinkageConfig(rate=0.30),
                occupancy_config=OccupancyConfig(target=0.85),
                forecast_config=ForecastConfig(
                    model_type=ForecastModel.AUTO_ARIMA,
                    forecast_horizon=168,
                    seasonality=7
                ),
                staffing_config=StaffingConfig(
                    algorithm=StaffingAlgorithm.ERLANG_C,
                    service_level_config=SLAConfig(target=0.80, average_speed_of_answer=180),
                    interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
                    shrinkage_config=ShrinkageConfig(rate=0.30),
                    occupancy_config=OccupancyConfig(target=0.85),
                    skills=[],
                    channels=[]  # Empty!
                ),
                skills=[],
                channels=[]  # Empty!
            )
class TestExampleConfigs:
    """Test example configuration functions."""

    def test_get_inbound_example_config(self):
        """Test getting inbound example configuration."""
        config = get_inbound_example_config()
        
        assert config.name == "inbound_example"
        assert config.operating_profile == OperatingProfile.INBOUND
        assert config.interval_config.interval_size == 60
        assert config.sla_config.target == 0.80
        assert config.shrinkage_config.rate == 0.30
        assert config.occupancy_config.target == 0.85
        assert config.forecast_config.model_type == ForecastModel.AUTO_ARIMA
        assert config.forecast_config.forecast_horizon == 168
        assert config.staffing_config.algorithm == StaffingAlgorithm.ERLANG_C
        assert len(config.skills) == 1
        assert len(config.channels) == 1
        assert config.skills[0].skill_type == SkillType.VOICE
        assert config.channels[0].channel_type == ChannelType.VOICE

    def test_get_outbound_example_config(self):
        """Test getting outbound example configuration."""
        config = get_outbound_example_config()
        
        assert config.name == "outbound_example"
        assert config.operating_profile == OperatingProfile.OUTBOUND
        assert config.interval_config.interval_size == 60
        assert config.sla_config.target == 0.75
        assert config.shrinkage_config.rate == 0.25
        assert config.occupancy_config.target == 0.80
        assert config.forecast_config.model_type == ForecastModel.SEASONAL_NAIVE
        assert config.forecast_config.forecast_horizon == 168
        assert config.staffing_config.algorithm == StaffingAlgorithm.ERLANG_C
        assert len(config.skills) == 1
        assert len(config.channels) == 1
        assert config.skills[0].skill_type == SkillType.SALES
        assert config.channels[0].channel_type == ChannelType.VOICE

    def test_get_blended_example_config(self):
        """Test getting blended example configuration."""
        config = get_blended_example_config()
        
        assert config.name == "blended_example"
        assert config.operating_profile == OperatingProfile.BLENDED
        assert config.interval_config.interval_size == 60
        assert config.sla_config.target == 0.78
        assert config.shrinkage_config.rate == 0.28
        assert config.occupancy_config.target == 0.83
        assert config.forecast_config.model_type == ForecastModel.AUTO_ETS
        assert config.forecast_config.forecast_horizon == 168
        assert config.staffing_config.algorithm == StaffingAlgorithm.ERLANG_C
        assert config.scheduling_config.solver == SchedulingSolver.PYWORKFORCE
        assert len(config.skills) == 2
        assert len(config.channels) == 2
        assert config.skills[0].skill_type == SkillType.CUSTOMER_SERVICE
        assert config.channels[0].channel_type == ChannelType.VOICE

    def test_get_multi_skill_example_config(self):
        """Test getting multi-skill example configuration."""
        config = get_multi_skill_example_config()
        
        assert config.name == "multi_skill_example"
        assert config.operating_profile == OperatingProfile.MULTI_SKILL
        assert config.interval_config.interval_size == 60
        assert config.sla_config.target == 0.75
        assert config.shrinkage_config.rate == 0.32
        assert config.occupancy_config.target == 0.82
        assert config.forecast_config.model_type == ForecastModel.AUTO_ARIMA
        assert config.forecast_config.forecast_horizon == 168
        assert config.staffing_config.algorithm == StaffingAlgorithm.ERLANG_C
        assert config.scheduling_config.solver == SchedulingSolver.PYWORKFORCE
        assert config.optimization_config.method == OptimizationMethod.GREEDY
        assert len(config.staffing_config.skills) == 3
        assert len(config.staffing_config.channels) == 3
        assert len(config.skills) == 3
        assert len(config.channels) == 3
class TestConfigLoadAndValidate:
    """Test loading and validating configuration files."""

    def test_load_config_from_yaml_valid(self):
        """Test loading valid configuration from YAML file."""
        config_dict = {
            "name": "yaml_test",
            "version": "1.0.0",
            "description": "Test YAML config",
            "operating_profile": "inbound",
            "interval_config": {
                "interval_size": 60,
                "interval_unit": "minute"
            },
            "sla_config": {
                "target": 0.80,
                "average_speed_of_answer": 180
            },
            "shrinkage_config": {
                "rate": 0.30
            },
            "occupancy_config": {
                "target": 0.85
            },
            "forecast_config": {
                "model_type": "auto_arima",
                "forecast_horizon": 168,
                "seasonality": 7
            },
            "staffing_config": {
                "algorithm": "erlang_c",
                "service_level_config": {
                    "target": 0.80,
                    "average_speed_of_answer": 180
                },
                "interval_config": {
                    "interval_size": 60,
                    "interval_unit": "minute"
                },
                "shrinkage_config": {
                    "rate": 0.30
                },
                "occupancy_config": {
                    "target": 0.85
                },
                "skills": [],
                "channels": []
            },
            "skills": [],
            "channels": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            config_path = f.name
        
        try:
            config = load_config_from_yaml(config_path)
            
            assert config.name == "yaml_test"
            assert config.operating_profile == OperatingProfile.INBOUND
            assert config.interval_config.interval_size == 60
            assert config.sla_config.target == 0.80
            assert config.forecast_config.model_type == ForecastModel.AUTO_ARIMA
        finally:
            os.unlink(config_path)

    def test_load_config_from_json_valid(self):
        """Test loading valid configuration from JSON file."""
        config_dict = {
            "name": "json_test",
            "version": "1.0.0",
            "description": "Test JSON config",
            "operating_profile": "outbound",
            "interval_config": {
                "interval_size": 60,
                "interval_unit": "minute"
            },
            "sla_config": {
                "target": 0.80,
                "average_speed_of_answer": 180
            },
            "shrinkage_config": {
                "rate": 0.30
            },
            "occupancy_config": {
                "target": 0.85
            },
            "forecast_config": {
                "model_type": "auto_arima",
                "forecast_horizon": 168,
                "seasonality": 7
            },
            "staffing_config": {
                "algorithm": "erlang_c",
                "service_level_config": {
                    "target": 0.80,
                    "average_speed_of_answer": 180
                },
                "interval_config": {
                    "interval_size": 60,
                    "interval_unit": "minute"
                },
                "shrinkage_config": {
                    "rate": 0.30
                },
                "occupancy_config": {
                    "target": 0.85
                },
                "skills": [],
                "channels": []
            },
            "skills": [],
            "channels": []
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f)
            config_path = f.name
        
        try:
            config = load_config_from_json(config_path)
            
            assert config.name == "json_test"
            assert config.operating_profile == OperatingProfile.OUTBOUND
            assert config.interval_config.interval_size == 60
            assert config.sla_config.target == 0.80
            assert config.forecast_config.model_type == ForecastModel.AUTO_ARIMA
        finally:
            os.unlink(config_path)

    def test_validate_config_dict_valid(self):
        """Test validating valid configuration dictionary."""
        config_dict = {
            "name": "dict_test",
            "version": "1.0.0",
            "description": "Test dict config",
            "operating_profile": "blended",
            "interval_config": {
                "interval_size": 60,
                "interval_unit": "minute"
            },
            "sla_config": {
                "target": 0.80,
                "average_speed_of_answer": 180
            },
            "shrinkage_config": {
                "rate": 0.30
            },
            "occupancy_config": {
                "target": 0.85
            },
            "forecast_config": {
                "model_type": "auto_arima",
                "forecast_horizon": 168,
                "seasonality": 7
            },
            "staffing_config": {
                "algorithm": "erlang_c",
                "service_level_config": {
                    "target": 0.80,
                    "average_speed_of_answer": 180
                },
                "interval_config": {
                    "interval_size": 60,
                    "interval_unit": "minute"
                },
                "shrinkage_config": {
                    "rate": 0.30
                },
                "occupancy_config": {
                    "target": 0.85
                },
                "skills": [],
                "channels": []
            },
            "skills": [],
            "channels": []
        }
        
        config = validate_config_dict(config_dict)
        
        assert config.name == "dict_test"
        assert config.operating_profile == OperatingProfile.BLENDED
        assert config.interval_config.interval_size == 60
        assert config.sla_config.target == 0.80
        assert config.forecast_config.model_type == ForecastModel.AUTO_ARIMA

    def test_validate_config_dict_invalid(self):
        """Test validating invalid configuration dictionary."""
        config_dict = {
            "name": "invalid_test",
            "version": "1.0.0",
            "operating_profile": "invalid_profile",  # Invalid enum value
            "interval_config": {
                "interval_size": 60,
                "interval_unit": "minute"
            },
            "sla_config": {
                "target": 0.80,
                "average_speed_of_answer": 180
            },
            "shrinkage_config": {
                "rate": 0.30
            },
            "occupancy_config": {
                "target": 0.85
            },
            "skills": [],
            "channels": []
        }
        
        with pytest.raises(Exception):  # Should raise ValidationError
            validate_config_dict(config_dict)
class TestConfigMergeWithDefault:
    """Test configuration merging functionality."""

    def test_merge_with_default(self):
        """Test merging configuration with default values."""
        base_config = WFMConfig(
            name="merged_config",
            version="1.0.0",
            description="Base configuration",
            operating_profile=OperatingProfile.INBOUND,
            interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
            sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
            shrinkage_config=ShrinkageConfig(rate=0.30),
            occupancy_config=OccupancyConfig(target=0.85),
            skills=[],
            channels=[]
        )
        
        default_config = {
            "forecast_config": {
                "model_type": "auto_arima",
                "forecast_horizon": 168,
                "seasonality": 7
            },
            "staffing_config": {
                "algorithm": "erlang_c"
            },
            "validation_config": {
                "strict_mode": False,
                "threshold": 0.95
            }
        }
        
        merged_config = base_config.merge_with_default(default_config)
        
        assert merged_config.name == "merged_config"
        assert merged_config.operating_profile == OperatingProfile.INBOUND
        assert merged_config.interval_config.interval_size == 60
        assert merged_config.sla_config.target == 0.80
        assert merged_config.forecast_config is not None
        assert merged_config.forecast_config.model_type == ForecastModel.AUTO_ARIMA
        assert merged_config.forecast_config.forecast_horizon == 168
        assert merged_config.staffing_config is not None
        assert merged_config.staffing_config.algorithm == StaffingAlgorithm.ERLANG_C
        assert merged_config.validation_config is not None
        assert merged_config.validation_config.strict_mode is False
        assert merged_config.validation_config.threshold == 0.95

    def test_merge_with_empty_lists(self):
        """Test merging configuration with empty lists."""
        base_config = WFMConfig(
            name="merge_test",
            version="1.0.0",
            description="Test merge",
            operating_profile=OperatingProfile.INBOUND,
            interval_config=IntervalConfig(interval_size=60, interval_unit=TimeInterval.MINUTE),
            sla_config=SLAConfig(target=0.80, average_speed_of_answer=180),
            shrinkage_config=ShrinkageConfig(rate=0.30),
            occupancy_config=OccupancyConfig(target=0.85),
            skills=[],  # Empty
            channels=[]  # Empty
        )
        
        default_config = {
            "skills": ["skill1", "skill2"],
            "channels": ["channel1", "channel2"]
        }
        
        merged_config = base_config.merge_with_default(default_config)
        
        assert merged_config.skills == ["skill1", "skill2"]  # Should use default
        assert merged_config.channels == ["channel1", "channel2"]  # Should use default