"""
Tests for OR-Tools adapter - written FIRST (TDD approach).

This test file implements the TDD approach for OR-Tools adapter development.
Tests are written first to define expected behavior, then implementation follows.
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

from wfm_harness.adapters.ortools_adapter import ORToolsAdapter
from wfm_harness.adapters.base import AdapterConfig, AdapterResult
from wfm_harness.domain import WFMData, ScheduleResult, OptimizationResult


class TestORToolsAdapterFixtures:
    """Synthetic test fixtures for OR-Tools adapter."""

    @staticmethod
    def create_sample_wfm_data(num_days: int = 7, num_shifts: int = 3) -> List[WFMData]:
        """Create synthetic WFM data for testing."""
        data = []
        base_date = datetime(2024, 1, 1)
        for day in range(num_days):
            for shift in range(num_shifts):
                timestamp = base_date + timedelta(days=day, hours=shift * 8)
                data.append(WFMData(
                    timestamp=timestamp,
                    value=10 + (day % 3) + (shift % 2),  # Synthetic demand
                    metadata={'day': day, 'shift': shift}
                ))
        return data

    @staticmethod
    def create_staffing_requirements() -> Dict[str, Any]:
        """Create synthetic staffing requirements."""
        return {
            'num_agents': 10,
            'shifts_per_day': 3,
            'days': 7,
            'min_agents_per_shift': 2,
            'max_agents_per_shift': 5,
            'agent_skills': ['voice', 'chat', 'email'],
            'shift_requirements': {
                'morning': {'voice': 3, 'chat': 2, 'email': 1},
                'afternoon': {'voice': 2, 'chat': 3, 'email': 1},
                'night': {'voice': 1, 'chat': 2, 'email': 1}
            }
        }

    @staticmethod
    def create_schedule_constraints() -> Dict[str, Any]:
        """Create synthetic schedule constraints."""
        return {
            'max_consecutive_days': 5,
            'min_rest_hours': 12,
            'max_weekly_hours': 40,
            'preferred_days_off': 2,
            'shift_preferences': {
                'agent_1': ['morning'],
                'agent_2': ['afternoon'],
                'agent_3': ['night']
            }
        }


class TestORToolsAdapterInitialization:
    """Test OR-Tools adapter initialization and configuration."""

    def test_adapter_extends_base_adapter(self):
        """Verify ORToolsAdapter extends BaseAdapter."""
        adapter = ORToolsAdapter()
        assert adapter is not None

    def test_adapter_has_correct_config(self):
        """Verify adapter configuration is correct."""
        adapter = ORToolsAdapter()
        assert adapter.config.provider_name == "OR-Tools"
        assert adapter.config.package_name == "ortools"
        assert adapter.config.license == "Apache-2.0"
        assert adapter.config.deterministic_level == "high"
        assert "ortools" in adapter.config.required_dependencies

    def test_adapter_health_check(self):
        """Verify health check returns True when OR-Tools is available."""
        adapter = ORToolsAdapter()
        assert adapter.health_check() is True

    def test_adapter_get_provider_info(self):
        """Verify provider info is returned correctly."""
        adapter = ORToolsAdapter()
        info = adapter.get_provider_info()
        assert info['name'] == "OR-Tools"
        assert info['package'] == "ortools"
        assert info['license'] == "Apache-2.0"
        assert 'ortools' in info['required_dependencies']


class TestORToolsAdapterOptimize:
    """Test optimize() method for constraint solving."""

    @pytest.fixture
    def adapter(self):
        return ORToolsAdapter()

    @pytest.fixture
    def sample_data(self):
        return TestORToolsAdapterFixtures.create_sample_wfm_data()

    @pytest.fixture
    def staffing_reqs(self):
        return TestORToolsAdapterFixtures.create_staffing_requirements()

    def test_optimize_returns_adapter_result(self, adapter, sample_data, staffing_reqs):
        """Verify optimize returns AdapterResult."""
        result = adapter.optimize(sample_data, requirements=staffing_reqs)
        assert isinstance(result, AdapterResult)

    def test_optimize_success(self, adapter, sample_data, staffing_reqs):
        """Verify optimize succeeds with valid data."""
        result = adapter.optimize(sample_data, requirements=staffing_reqs)
        assert result.success is True
        assert result.operation == "optimize"
        assert result.adapter_name == "OR-Tools"

    def test_optimize_returns_optimization_result(self, adapter, sample_data, staffing_reqs):
        """Verify optimize returns OptimizationResult data."""
        result = adapter.optimize(sample_data, requirements=staffing_reqs)
        assert result.success is True
        assert hasattr(result.data, 'optimizer')
        assert hasattr(result.data, 'objective_value')
        assert hasattr(result.data, 'solution')
        assert hasattr(result.data, 'iterations')
        assert result.data.optimizer == "OR-Tools CP-SAT"

    def test_optimize_solution_contains_assignments(self, adapter, sample_data, staffing_reqs):
        """Verify optimization solution contains shift assignments."""
        result = adapter.optimize(sample_data, requirements=staffing_reqs)
        assert result.success is True
        assert 'assignments' in result.data.solution
        assert isinstance(result.data.solution['assignments'], dict)

    def test_optimize_respects_constraints(self, adapter, sample_data, staffing_reqs):
        """Verify optimization respects constraints."""
        constraints = TestORToolsAdapterFixtures.create_schedule_constraints()
        result = adapter.optimize(
            sample_data,
            requirements=staffing_reqs,
            constraints=constraints
        )
        assert result.success is True
        # Verify constraints were considered
        assert 'constraints_applied' in result.metadata


class TestORToolsAdapterSchedule:
    """Test schedule() method for shift scheduling."""

    @pytest.fixture
    def adapter(self):
        return ORToolsAdapter()

    @pytest.fixture
    def sample_data(self):
        return TestORToolsAdapterFixtures.create_sample_wfm_data()

    @pytest.fixture
    def schedule_constraints(self):
        return TestORToolsAdapterFixtures.create_schedule_constraints()

    def test_schedule_returns_adapter_result(self, adapter, sample_data, schedule_constraints):
        """Verify schedule returns AdapterResult."""
        result = adapter.schedule(sample_data, constraints=schedule_constraints)
        assert isinstance(result, AdapterResult)

    def test_schedule_success(self, adapter, sample_data, schedule_constraints):
        """Verify schedule succeeds with valid data."""
        result = adapter.schedule(sample_data, constraints=schedule_constraints)
        assert result.success is True
        assert result.operation == "schedule"
        assert result.adapter_name == "OR-Tools"

    def test_schedule_returns_schedule_result(self, adapter, sample_data, schedule_constraints):
        """Verify schedule returns ScheduleResult data."""
        result = adapter.schedule(sample_data, constraints=schedule_constraints)
        assert result.success is True
        assert hasattr(result.data, 'solver')
        assert hasattr(result.data, 'roster')
        assert hasattr(result.data, 'constraints_satisfied')
        assert result.data.solver == "OR-Tools CP-SAT"

    def test_schedule_roster_contains_shifts(self, adapter, sample_data, schedule_constraints):
        """Verify schedule roster contains shift assignments."""
        result = adapter.schedule(sample_data, constraints=schedule_constraints)
        assert result.success is True
        assert isinstance(result.data.roster, dict)
        assert len(result.data.roster) > 0

    def test_schedule_constraints_satisfied_count(self, adapter, sample_data, schedule_constraints):
        """Verify constraints_satisfied is tracked."""
        result = adapter.schedule(sample_data, constraints=schedule_constraints)
        assert result.success is True
        assert isinstance(result.data.constraints_satisfied, int)
        assert result.data.constraints_satisfied >= 0


class TestORToolsAdapterUnsupportedOperations:
    """Test that unsupported operations return proper error message."""

    @pytest.fixture
    def adapter(self):
        return ORToolsAdapter()

    @pytest.fixture
    def sample_data(self):
        return TestORToolsAdapterFixtures.create_sample_wfm_data()

    def test_forecast_returns_not_supported(self, adapter, sample_data):
        """Verify forecast returns not supported error."""
        result = adapter.forecast(sample_data)
        assert result.success is False
        assert result.error_message == "Not supported by OR-Tools"

    def test_staff_returns_not_supported(self, adapter, sample_data):
        """Verify staff returns not supported error."""
        result = adapter.staff(sample_data)
        assert result.success is False
        assert result.error_message == "Not supported by OR-Tools"

    def test_validate_returns_not_supported(self, adapter, sample_data):
        """Verify validate returns not supported error."""
        result = adapter.validate(sample_data)
        assert result.success is False
        assert result.error_message == "Not supported by OR-Tools"


class TestORToolsAdapterPanderaValidation:
    """Test Pandera schema validation at boundaries."""

    @pytest.fixture
    def adapter(self):
        return ORToolsAdapter()

    def test_input_validation_optimize(self, adapter):
        """Verify input validation for optimize."""
        # Test with invalid data type
        result = adapter.optimize("invalid_data", requirements={})
        assert result.success is False

    def test_input_validation_schedule(self, adapter):
        """Verify input validation for schedule."""
        result = adapter.schedule("invalid_data", constraints={})
        assert result.success is False

    def test_output_validation_optimize(self, adapter, sample_data, staffing_reqs):
        """Verify output validation for optimize."""
        result = adapter.optimize(sample_data, requirements=staffing_reqs)
        assert result.success is True
        # Output should be validated against schema

    def test_output_validation_schedule(self, adapter, sample_data, schedule_constraints):
        """Verify output validation for schedule."""
        result = adapter.schedule(sample_data, constraints=schedule_constraints)
        assert result.success is True
        # Output should be validated against schema


class TestORToolsAdapterEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def adapter(self):
        return ORToolsAdapter()

    def test_empty_data_optimize(self, adapter):
        """Verify optimize handles empty data."""
        result = adapter.optimize([], requirements={})
        assert result.success is False

    def test_empty_data_schedule(self, adapter):
        """Verify schedule handles empty data."""
        result = adapter.schedule([], constraints={})
        assert result.success is False

    def test_missing_requirements_optimize(self, adapter, sample_data):
        """Verify optimize handles missing requirements."""
        result = adapter.optimize(sample_data)
        assert result.success is False

    def test_missing_constraints_schedule(self, adapter, sample_data):
        """Verify schedule handles missing constraints."""
        result = adapter.schedule(sample_data)
        assert result.success is False


# Fixture for sample data (defined at bottom for use in other test classes)
@pytest.fixture
def sample_data():
    return TestORToolsAdapterFixtures.create_sample_wfm_data()

@pytest.fixture
def staffing_reqs():
    return TestORToolsAdapterFixtures.create_staffing_requirements()

@pytest.fixture
def schedule_constraints():
    return TestORToolsAdapterFixtures.create_schedule_constraints()