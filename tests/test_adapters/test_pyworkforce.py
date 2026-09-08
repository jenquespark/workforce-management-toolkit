"""Tests for PyworkforceAdapter - TDD approach with synthetic fixtures."""

import pytest
from datetime import datetime
from typing import List
from unittest.mock import patch, MagicMock

from wfm_harness.adapters.pyworkforce_adapter import PyworkforceAdapter
from wfm_harness.adapters.base import AdapterConfig
from wfm_harness.domain import WFMData

# Synthetic test fixtures for WFM data
@pytest.fixture
def synthetic_forecast_data() -> List[WFMData]:
    """Synthetic forecast data for testing."""
    return [
        WFMData(
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            value=100.5,
            metadata={"channel": "voice", "hour": 0}
        ),
        WFMData(
            timestamp=datetime(2024, 1, 1, 1, 0, 0),
            value=102.3,
            metadata={"channel": "voice", "hour": 1}
        ),
        WFMData(
            timestamp=datetime(2024, 1, 1, 2, 0, 0),
            value=101.8,
            metadata={"channel": "voice", "hour": 2}
        ),
        WFMData(
            timestamp=datetime(2024, 1, 1, 3, 0, 0),
            value=103.2,
            metadata={"channel": "voice", "hour": 3}
        ),
        WFMData(
            timestamp=datetime(2024, 1, 1, 4, 0, 0),
            value=99.7,
            metadata={"channel": "voice", "hour": 4}
        )
    ]

@pytest.fixture
def synthetic_staffing_data() -> List[WFMData]:
    """Synthetic staffing data for testing."""
    return [
        WFMData(
            timestamp=datetime(2024, 1, 1, 0, 0, 0),
            value=180.0,  # Average handle time in seconds
            metadata={"channel": "voice", "hour": 0, "calls": 50}
        ),
        WFMData(
            timestamp=datetime(2024, 1, 1, 1, 0, 0),
            value=195.5,
            metadata={"channel": "voice", "hour": 1, "calls": 55}
        ),
        WFMData(
            timestamp=datetime(2024, 1, 1, 2, 0, 0),
            value=165.0,
            metadata={"channel": "voice", "hour": 2, "calls": 45}
        ),
        WFMData(
            timestamp=datetime(2024, 1, 1, 3, 0, 0),
            value=210.0,
            metadata={"channel": "voice", "hour": 3, "calls": 60}
        ),
        WFMData(
            timestamp=datetime(2024, 1, 1, 4, 0, 0),
            value=175.5,
            metadata={"channel": "voice", "hour": 4, "calls": 50}
        )
    ]

@pytest.fixture
def pyworkforce_config() -> AdapterConfig:
    """Standard configuration for PyworkforceAdapter."""
    return AdapterConfig(
        provider_name="Pyworkforce",
        package_name="pyworkforce",
        license="MIT",
        deterministic_level="high",
        required_dependencies=["pyworkforce"],
        optional_dependencies=[],
        configuration_options={
            "service_level": 0.80,
            "average_speed_of_answer": 180,
            "acceptable_service_level": 0.90,
            "minimum_service_level": 0.95,
            "shrinkage_rate": 0.30,
            "half_occupancy": 0.85,
            "hours_per_agent": 7.5,
            "average_handle_time": 180
        }
    )

class TestPyworkforceAdapter:
    """Test suite for PyworkforceAdapter following TDD principles."""
    
    def test_adapter_initialization_with_default_config(self):
        """Test that adapter initializes with default config."""
        adapter = PyworkforceAdapter()
        assert adapter is not None
        assert adapter.config.provider_name == "Pyworkforce"
        assert adapter.config.package_name == "pyworkforce"
        assert adapter.config.deterministic_level == "high"
        
    def test_adapter_initialization_with_custom_config(self, pyworkforce_config):
        """Test that adapter initializes with custom config."""
        adapter = PyworkforceAdapter(pyworkforce_config)
        assert adapter is not None
        assert adapter.config == pyworkforce_config
        
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    def test_health_check_without_pyworkforce(self, mock_has_pyworkforce):
        """Test health check when pyworkforce is not installed."""
        mock_has_pyworkforce.return_value = False
        adapter = PyworkforceAdapter()
        assert adapter.health_check() is False
        
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    @patch('wfm_harness.adapters.pyworkforce_adapter.erlang_c')
    def test_health_check_with_pyworkforce(self, mock_erlang_c, mock_has_pyworkforce):
        """Test health check when pyworkforce is installed."""
        mock_has_pyworkforce.return_value = True
        mock_erlang_c.return_value = 2.5
        adapter = PyworkforceAdapter()
        assert adapter.health_check() is True
        mock_erlang_c.assert_called_once_with(10.0, 0.80)
        
    def test_forecast_operation_not_supported(self, synthetic_forecast_data):
        """Test that forecast operation returns not supported error."""
        adapter = PyworkforceAdapter()
        result = adapter.forecast(synthetic_forecast_data)
        
        assert result.success is False
        assert result.error_message == "Forecasting operation requires StatsForecast adapter"
        assert result.operation == "forecast"
        assert result.data is None
        
    def test_staff_operation_without_pyworkforce(self, synthetic_staffing_data):
        """Test staff operation when pyworkforce is not installed."""
        with patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce', False):
            adapter = PyworkforceAdapter()
            result = adapter.staff(synthetic_staffing_data)
            
            assert result.success is False
            assert result.error_message == "Pyworkforce not installed"
            assert result.operation == "staff"
            assert result.data is None
            
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    @patch('wfm_harness.adapters.pyworkforce_adapter.erlang_c')
    def test_staff_operation_with_pyworkforce_empty_data(
        self, mock_erlang_c, mock_has_pyworkforce
    ):
        """Test staff operation with empty data."""
        mock_has_pyworkforce.return_value = True
        adapter = PyworkforceAdapter()
        
        result = adapter.staff([])
        
        assert result.success is False
        assert result.error_message == "No valid data provided for staffing calculation"
        assert result.operation == "staff"
        assert result.data is None
        
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    @patch('wfm_harness.adapters.pyworkforce_adapter.erlang_c')
    def test_staff_operation_success(
        self, mock_erlang_c, mock_has_pyworkforce, synthetic_staffing_data
    ):
        """Test successful staff operation."""
        mock_has_pyworkforce.return_value = True
        mock_erlang_c.return_value = 2.5
        adapter = PyworkforceAdapter()
        
        result = adapter.staff(synthetic_staffing_data)
        
        assert result.success is True
        assert result.operation == "staff"
        assert result.data is not None
        assert "calculation_method" in result.metadata
        assert result.metadata["calculation_method"] == "erlang_c_with_shrinkage"
        assert len(result.metadata["arrival_rates"]) == len(synthetic_staffing_data)
        
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    @patch('wfm_harness.adapters.pyworkforce_adapter.erlang_c')
    def test_staff_operation_with_custom_parameters(
        self, mock_erlang_c, mock_has_pyworkforce, synthetic_staffing_data
    ):
        """Test staff operation with custom parameters."""
        mock_has_pyworkforce.return_value = True
        mock_erlang_c.return_value = 3.0
        adapter = PyworkforceAdapter()
        
        custom_params = {
            "service_level": 0.90,
            "shrinkage_rate": 0.35,
            "half_occupancy": 0.80,
            "average_speed_of_answer": 240
        }
        
        result = adapter.staff(synthetic_staffing_data, **custom_params)
        
        assert result.success is True
        assert result.metadata["service_level_target"] == 0.90
        assert result.metadata["shrinkage_rate"] == 0.35
        assert result.metadata["half_occupancy"] == 0.80
        assert result.metadata["average_speed_of_answer"] == 240
        
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    @patch('wfm_harness.adapters.pyworkforce_adapter.erlang_c')
    def test_schedule_operation_without_pyworkforce(
        self, mock_erlang_c, mock_has_pyworkforce, synthetic_staffing_data
    ):
        """Test schedule operation when pyworkforce is not installed."""
        mock_has_pyworkforce.return_value = False
        adapter = PyworkforceAdapter()
        
        result = adapter.schedule(synthetic_staffing_data)
        
        assert result.success is False
        assert result.error_message == "Pyworkforce not installed"
        assert result.operation == "schedule"
        assert result.data is None
        
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    @patch('wfm_harness.adapters.pyworkforce_adapter.erlang_c')
    def test_schedule_operation_success(
        self, mock_erlang_c, mock_has_pyworkforce, synthetic_staffing_data
    ):
        """Test successful schedule operation."""
        mock_has_pyworkforce.return_value = True
        mock_erlang_c.return_value = 2.5
        adapter = PyworkforceAdapter()
        
        result = adapter.schedule(synthetic_staffing_data)
        
        assert result.success is True
        assert result.operation == "schedule"
        assert result.data is not None
        assert "solver" in result.data
        assert result.data["solver"] == "pyworkforce"
        
    def test_optimize_operation_not_supported(self, synthetic_forecast_data):
        """Test that optimize operation returns not supported error."""
        adapter = PyworkforceAdapter()
        result = adapter.optimize(synthetic_forecast_data)
        
        assert result.success is False
        assert result.error_message == "Optimization operation requires OR-Tools adapter"
        assert result.operation == "optimize"
        assert result.data is None
        
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    @patch('wfm_harness.adapters.pyworkforce_adapter.pd')
    @patch('wfm_harness.adapters.pyworkforce_adapter.SchemaError')
    def test_validate_operation_without_pandera(
        self, mock_schema_error, mock_pd, mock_has_pyworkforce, synthetic_forecast_data
    ):
        """Test validate operation when pandera is not installed."""
        mock_has_pyworkforce.return_value = True
        mock_pd.__version__ = "0.13.0"
        
        adapter = PyworkforceAdapter()
        
        result = adapter.validate(synthetic_forecast_data)
        
        assert result.success is False
        assert "Pandera is not installed" in result.error_message
        assert result.operation == "validate"
        assert result.data is None
        
    def test_validate_operation_empty_data(self):
        """Test validate operation with empty data."""
        adapter = PyworkforceAdapter()
        
        result = adapter.validate([])
        
        # Should succeed with empty data (no violations)
        assert result.success is True
        assert result.data is not None
        assert len(result.data) == 0  # Empty DataFrame
        
    def test_erl__calculate_total_agents_from_list(self):
        """Test _calculate_total_agents with list input."""
        from wfm_harness.domain import StaffingResult
        
        adapter = PyworkforceAdapter()
        
        # Create mock staffing results
        staffing_results = [
            StaffingResult(
                algorithm="test",
                allocations={"period_0": [5, 3], "period_1": [2]},
                metrics={}
            ),
            StaffingResult(
                algorithm="test", 
                allocations={"period_0": [1]},  # Single agent
                metrics={}
            )
        ]
        
        total = adapter._calculate_total_agents(staffing_results)
        assert total == 5 + 3 + 2 + 1  # 11 total agents
        
    def test_erl__calculate_total_agents_from_single_object(self):
        """Test _calculate_total_agents with single StaffingResult."""
        from wfm_harness.domain import StaffingResult
        
        adapter = PyworkforceAdapter()
        
        staffing_result = StaffingResult(
            algorithm="test",
            allocations={"period_0": [5, 3], "period_1": [2]},
            metrics={}
        )
        
        total = adapter._calculate_total_agents(staffing_result)
        assert total == 5 + 3 + 2  # 10 total agents
        
    def test_erl__calculate_total_agents_empty_input(self):
        """Test _calculate_total_agents with empty input."""
        adapter = PyworkforceAdapter()
        
        total = adapter._calculate_total_agents(None)
        assert total == 0
        
        total = adapter._calculate_total_agents([])
        assert total == 0
        
    def test_execute_operation_staff_routing(self, synthetic_staffing_data):
        """Test execute_operation routing for staff operation."""
        adapter = PyworkforceAdapter()
        
        result = adapter.execute_operation("staff", synthetic_staffing_data)
        
        assert result.operation == "staff"
        assert result.adapter_name == "Pyworkforce"
        
    def test_execute_operation_unknown_operation(self, synthetic_forecast_data):
        """Test execute_operation with unknown operation."""
        adapter = PyworkforceAdapter()
        
        result = adapter.execute_operation("unknown", synthetic_forecast_data)
        
        assert result.success is False
        assert result.error_message == "Unknown operation: unknown"
        
    def test_get_provider_info(self, pyworkforce_config):
        """Test get_provider_info method."""
        adapter = PyworkforceAdapter(pyworkforce_config)
        
        info = adapter.get_provider_info()
        
        assert info["name"] == "Pyworkforce"
        assert info["package"] == "pyworkforce"
        assert info["license"] == "MIT"
        assert info["deterministic_level"] == "high"
        assert info["required_dependencies"] == ["pyworkforce"]
        
    def test_get_adaptation_metadata(self, synthetic_staffing_data):
        """Test get_adaptation_metadata method."""
        adapter = PyworkforceAdapter()
        
        metadata = adapter.get_adaptation_metadata()
        
        assert "adapter_type" in metadata
        assert metadata["adapter_type"] == "PyworkforceAdapter"
        assert "configured" in metadata
        assert metadata["configured"] is True
        assert "health_check" in metadata
        
    @patch('wfm_harness.adapters.pyworkforce_adapter.has_pyworkforce')
    def test_all_operations_not_supported_by_pyworkforce(
        self, mock_has_pyworkforce, synthetic_forecast_data
    ):
        """Test that operations not explicitly implemented return not supported."""
        mock_has_pyworkforce.return_value = True
        adapter = PyworkforceAdapter()
        
        # Test that forecast, schedule, and optimize return not supported
        forecast_result = adapter.forecast(synthetic_forecast_data)
        schedule_result = adapter.schedule(synthetic_forecast_data)
        optimize_result = adapter.optimize(synthetic_forecast_data)
        
        assert forecast_result.success is False
        assert "Forecasting operation requires StatsForecast adapter" in forecast_result.error_message
        
        assert schedule_result.success is False
        assert "Pyworkforce not installed" in schedule_result.error_message
        
        assert optimize_result.success is False
        assert "Optimization operation requires OR-Tools adapter" in optimize_result.error_message
        
    def test_adapter_config_default_values(self):
        """Test that AdapterConfig has correct default values."""
        config = AdapterConfig(
            provider_name="Test",
            package_name="test-package",
            license="MIT"
        )
        
        assert config.deterministic_level == "high"
        assert config.required_dependencies == []
        assert config.optional_dependencies == []
        assert config.configuration_options == {}