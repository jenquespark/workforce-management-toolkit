"""Tests for the WFMCLI programmatic helpers.

There is no wired Click console script in this stage; the CLI must not
fabricate forecasting/staffing/scheduling results. The WFMCLI class exposes
only doctor(), capabilities(), and validate_config() that run against the real
registry/adapters.
"""

import json
from datetime import datetime

from wfm_toolkit.cli import WFMCLI
from wfm_toolkit.domain import WFMData


class TestWFMCLI:
    """Test the honest, minimal WFMCLI helpers."""

    def setup_method(self):
        self.cli = WFMCLI()

    def test_output_json_basic(self):
        result = self.cli._output_json({"key": "value"}, success=True, errors=[], metadata={"m": 1})
        parsed = json.loads(result)
        assert parsed["success"] is True
        assert parsed["data"]["key"] == "value"
        assert parsed["metadata"]["m"] == 1
        assert "timestamp" in parsed

    def test_output_json_error(self):
        result = self.cli._output_json(None, success=False, errors=["boom"], metadata={})
        parsed = json.loads(result)
        assert parsed["success"] is False
        assert parsed["errors"] == ["boom"]

    def test_doctor_reports_executable_capabilities(self):
        out = self.cli.doctor()
        parsed = json.loads(out)
        assert parsed["success"] is True
        assert parsed["data"]["version"] == "0.1.0"
        # The executable core must be exactly the three real providers
        assert set(parsed["data"]["executable_capabilities"]) == {
            "forecast.generate",
            "staffing.erlang_c",
            "validate.dataset",
        }
        # provider packages are reported as present/absent based on env
        assert "statsforecast" in parsed["data"]["provider_packages"]
        assert "pyworkforce" in parsed["data"]["provider_packages"]
        assert "pandera" in parsed["data"]["provider_packages"]

    def test_capabilities_lists_registered(self):
        out = self.cli.capabilities()
        parsed = json.loads(out)
        assert parsed["success"] is True
        assert parsed["data"]["count"] >= 3
        ids = [c["identifier"] for c in parsed["data"]["capabilities"]]
        assert "forecast.generate" in ids
        assert "validate.dataset" in ids
        # every capability has an explicit status field
        for c in parsed["data"]["capabilities"]:
            assert c["status"] in {"implemented", "planned", "experimental", "unavailable"}

    def test_validate_config_uses_pandera(self):
        data = [WFMData(timestamp=datetime(2024, 1, 1), value=100.0)]
        out = self.cli.validate_config(data)
        parsed = json.loads(out)
        # The command must run and return a structured JSON response.
        assert "success" in parsed
        assert parsed["metadata"]["command"] == "validate"
        # 'valid' reflects whether the dataset passed the Pandera schema.
        assert "valid" in parsed["data"]


class TestCLICommands:
    """Test the real Click CLI commands and their exit codes.

    Uses pytest's CliRunner instead of the programmatic WFMCLI so the
    installed console-script behavior is exercised.
    """

    def test_help_exits_zero(self):
        from click.testing import CliRunner

        from wfm_toolkit.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Workforce Management Toolkit CLI" in result.output

    def test_doctor_exits_zero_and_lists_three(self):
        from click.testing import CliRunner

        from wfm_toolkit.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["success"] is True
        assert set(parsed["data"]["executable_capabilities"]) == {
            "forecast.generate",
            "staffing.erlang_c",
            "validate.dataset",
        }

    def test_capabilities_exits_zero(self):
        from click.testing import CliRunner

        from wfm_toolkit.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["capabilities"])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["data"]["count"] >= 3

    def test_validate_command_valid_csv(self, tmp_path):
        from click.testing import CliRunner

        from wfm_toolkit.cli import main

        csv_file = tmp_path / "valid.csv"
        csv_file.write_text(
            "timestamp,value\n2024-01-01T08:00:00,120.0\n2024-01-01T09:00:00,150.0\n"
        )
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(csv_file)])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["data"]["valid"] is True

    def test_validate_command_invalid_csv_exits_1(self, tmp_path):
        from click.testing import CliRunner

        from wfm_toolkit.cli import main

        csv_file = tmp_path / "invalid.csv"
        csv_file.write_text("timestamp,value\n2024-01-01T08:00:00,-5.0\n")
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(csv_file)])
        assert result.exit_code == 1
        parsed = json.loads(result.output)
        assert parsed["data"]["valid"] is False

    def test_validate_command_missing_file_exits_2(self, tmp_path):
        from click.testing import CliRunner

        from wfm_toolkit.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(tmp_path / "nope.csv")])
        assert result.exit_code == 2

    def test_validate_command_timezone_aware_csv_exits_0(self, tmp_path):
        """ISO-8601 'Z' timestamps are valid input and must exit 0."""
        from click.testing import CliRunner

        from wfm_toolkit.cli import main

        csv_file = tmp_path / "tz.csv"
        csv_file.write_text(
            "timestamp,value\n2026-09-01T08:00:00Z,120.0\n2026-09-01T09:00:00Z,150.0\n"
        )
        runner = CliRunner()
        result = runner.invoke(main, ["validate", str(csv_file)])
        assert result.exit_code == 0
        parsed = json.loads(result.output)
        assert parsed["data"]["valid"] is True
