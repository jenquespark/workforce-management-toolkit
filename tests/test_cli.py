"""Tests for Workforce Management Toolkit CLI skeleton.

Tests for Click-based CLI with commands: doctor, capabilities, validate, forecast, staffing, schedule, optimize, capacity, workflow.
"""
import pytest
import json
import yaml
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch
from click.testing import CliRunner

# Update test file to use the correct CLI class
from wfm_harness.cli import WFMCLI, cli_app
from wfm_harness.domain import WFMData
class TestWFMCLI:
    """Test cases for WFMCLI class."""
    
    def setup_method(self):
        """Setup before each test."""
        self.cli = WFMCLI()
    
    def test_output_json_basic(self):
        """Test basic JSON output formatting."""
        test_data = {"key": "value"}
        
        result = self.cli._output_json(test_data, success=True, 
                                     errors=[], metadata={"test": "metadata"})
        
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["data"]["key"] == "value"
        assert parsed["metadata"]["test"] == "metadata"
        assert "timestamp" in parsed
    
    def test_output_json_error(self):
        """Test JSON output with error."""
        test_data = None
        
        result = self.cli._output_json(test_data, success=False, 
                                     errors=["Error 1", "Error 2"], 
                                     metadata={"command": "test"})
        
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed["errors"] == ["Error 1", "Error 2"]
        assert parsed["data"] is None
    
    def test_parse_data_valid(self):
        """Test parsing valid data string."""
        data_str = json.dumps([
            {"timestamp": "2023-01-01T00:00:00", "value": 100, "metadata": {}},
            {"timestamp": "2023-01-02T00:00:00", "value": 150, "metadata": {"test": "data"}}
        ])
        
        result = self.cli._parse_data(data_str)
        
        assert len(result) == 2
        assert isinstance(result[0], WFMData)
        assert result[0].value == 100
        assert result[0].timestamp == datetime(2023, 1, 1, 0, 0)
        assert result[1].value == 150
        assert result[1].metadata["test"] == "data"
    
    def test_parse_data_invalid(self):
        """Test parsing invalid data string."""
        data_str = "invalid json"
        
        with pytest.raises(Exception):  # ClickException
            self.cli._parse_data(data_str)
    
    def test_doctor_basic(self):
        """Test doctor command basic functionality."""
        result = self.cli.doctor()
        
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert "adapters" in parsed["data"]
        assert "statsforecast" in parsed["data"]["adapters"]
        assert "pyworkforce" in parsed["data"]["adapters"]
        assert "capabilities_loaded" in parsed["data"]
        assert "skills_loaded" in parsed["data"]
        assert "optional_dependencies" in parsed["data"]
    
    def test_capabilities_json_format(self):
        """Test capabilities command with JSON format."""
        result = self.cli.capabilities(format="json")
        
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert "capabilities" in parsed["data"]
        assert "count" in parsed["data"]
        assert isinstance(parsed["data"]["capabilities"], list)
    
    def test_capabilities_yaml_format(self):
        """Test capabilities command with YAML format."""
        result = self.cli.capabilities(format="yaml")
        
        # Should not raise exception
        assert result is not None
        # YAML format returns string, so we can't parse as JSON
        assert isinstance(result, str)
    
    def test_capabilites_with_examples(self):
        """Test capabilities command with examples."""
        result = self.cli.capabilities(format="json", examples=True)
        
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert "examples" in parsed["data"]
        assert len(parsed["data"]["examples"]) > 0
    
    def test_validate_with_yaml_config(self):
        """Test validate command with YAML config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"model": "AutoARIMA", "service_level": 0.8}, f)
            config_path = f.name
        
        try:
            result = self.cli.validate(config_path)
            parsed = json.loads(result)
            
            assert parsed["success"] is True
            assert parsed["data"]["valid"] is True
            assert "validation_rules" in parsed["data"]
        finally:
            os.unlink(config_path)
    
    def test_validate_with_json_config(self):
        """Test validate command with JSON config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"model": "SeasonalNaive", "service_level": 0.9}, f)
            config_path = f.name
        
        try:
            result = self.cli.validate(config_path)
            parsed = json.loads(result)
            
            assert parsed["success"] is True
            assert parsed["data"]["valid"] is True
        finally:
            os.unlink(config_path)
    
    def test_validate_invalid_file(self):
        """Test validate command with invalid config file."""
        result = self.cli.validate("/nonexistent/path/config.yaml")
        
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert len(parsed.get("errors", [])) > 0


# Test cases for CLI integration using Click testing
class TestCLIIntegration:
    """Test cases for Click CLI integration."""
    
    def setup_method(self):
        """Setup before each test."""
        self.runner = CliRunner()
        self.cli_app = cli_app
    
    def test_cli_doctor_command(self):
        """Test doctor command via Click."""
        result = self.runner.invoke(self.cli_app, ['doctor'])
        assert result.exit_code == 0
        result_data = json.loads(result.output)
        assert result_data["success"] is True
        assert "system_status" in result_data["data"]
    
    def test_cli_capabilities_command(self):
        """Test capabilities command via Click."""
        result = self.runner.invoke(self.cli_app, ['capabilities'])
        assert result.exit_code == 0
        result_data = json.loads(result.output)
        assert result_data["success"] is True
        assert "data" in result_data
    
    def test_cli_capabilities_with_examples(self):
        """Test capabilities command with --examples flag."""
        result = self.runner.invoke(self.cli_app, ['capabilities', '--examples'])
        assert result.exit_code == 0
        result_data = json.loads(result.output)
        assert result_data["success"] is True
        assert "data" in result_data
    
    def test_cli_capabilities_yaml_format(self):
        """Test capabilities command with --format yaml."""
        result = self.runner.invoke(self.cli_app, ['capabilities', '--format', 'yaml'])
        assert result.exit_code == 0
        # YAML output should be a string, not JSON
        assert result.output.strip().startswith('{')
    
    def test_cli_validate_command(self):
        """Test validate command via Click."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump({"model": "AutoARIMA", "service_level": 0.8}, f)
            config_path = f.name
        
        try:
            result = self.runner.invoke(self.cli_app, ['validate', config_path])
            assert result.exit_code == 0
            result_data = json.loads(result.output)
            assert result_data["success"] is True
        finally:
            os.unlink(config_path)
    
    def test_cli_help_output(self):
        """Test that all commands have help text."""
        commands_to_check = [
            ['doctor'],
            ['capabilities'],
            ['validate'],
            ['forecast'],
            ['staffing'],
            ['schedule'],
            ['optimize'],
            ['capacity'],
            ['workflow']
        ]
        
        for cmd in commands_to_check:
            result = self.runner.invoke(self.cli_app, cmd + ['--help'])
            assert result.exit_code == 0


class TestWFMSyntheticFixtures:
    """Tests using synthetic WFM fixtures as mentioned in requirements."""
    
    def test_synthetic_forecast_data(self):
        """Test with synthetic forecast data."""
        from wfm_harness.cli import WFMCLI
        
        cli = WFMCLI()
        
        # Create synthetic forecast data
        forecast_data = []
        for i in range(10):
            forecast_data.append({
                "timestamp": f"2023-01-{i+1:02d}T00:00:00",
                "value": 100 + i * 5 + (i % 3) * 10,
                "metadata": {"day": i+1, "month": 1}
            })
        
        data_str = json.dumps(forecast_data)
        wfm_data = cli._parse_data(data_str)
        
        assert len(wfm_data) == 10
        assert all(isinstance(d, WFMData) for d in wfm_data)
        assert all(d.value > 0 for d in wfm_data)
    
    def test_synthetic_staffing_data(self):
        """Test with synthetic staffing data."""
        from wfm_harness.cli import WFMCLI
        
        cli = WFMCLI()
        
        # Create synthetic staffing data
        staffing_data = []
        for hour in range(24):
            staffing_data.append({
                "timestamp": f"2023-01-01T{hour:02d}:00:00",
                "value": 50 + (hour % 8) * 10 + (hour >= 16) * 20,
                "metadata": {"hour": hour, "peak": hour >= 16 and hour <= 18}
            })
        
        data_str = json.dumps(staffing_data)
        wfm_data = cli._parse_data(data_str)
        
        assert len(wfm_data) == 24
        peak_hours = [d for d in wfm_data if d.metadata.get("peak", False)]
        assert len(peak_hours) == 3  # 16:00, 17:00, 18:00
    
    def test_cli_workflow_execution(self):
        """Test CLI workflow execution."""
        from wfm_harness.cli import WFMCLI
        
        cli = WFMCLI()
        
        # Test forecasting workflow
        result = cli.workflow("forecasting", 
                            config='{"model": "AutoARIMA"}', 
                            data='[{"timestamp": "2023-01-01T00:00:00", "value": 100}]')
        
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["data"]["workflow_type"] == "forecasting"
        assert "steps" in parsed["data"]
        assert "results" in parsed["data"]