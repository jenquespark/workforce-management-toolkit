"""Tests for PanderaAdapter - a data validation provider only.

Pandera validates; it does not forecast, staff, schedule, or optimize.
The only executable capability is validate(). The other BaseAdapter methods
return explicit unsupported results.
"""

import pytest

pytest.importorskip("pandera", reason="pandera is not installed")

from datetime import datetime, timedelta

from wfm_toolkit.adapters.pandera_adapter import PanderaAdapter
from wfm_toolkit.domain import WFMData


def make_data(count=5, value=100.0, start=None):
    start = start or datetime(2024, 1, 1)
    return [WFMData(timestamp=start + timedelta(hours=i), value=value + i) for i in range(count)]


class TestPanderaAdapter:
    """Test the Pandera adapter against its real validation contract."""

    def test_instantiation(self):
        adapter = PanderaAdapter()
        assert adapter.config.provider_name == "Pandera"
        assert adapter.config.package_name == "pandera"

    def test_health_check_reflects_install(self):
        adapter = PanderaAdapter()
        try:
            import pandera  # noqa: F401

            assert adapter.health_check() is True
        except ImportError:
            assert adapter.health_check() is False

    # --- validate() is the only executable operation ---

    def test_validate_valid_data_succeeds(self):
        adapter = PanderaAdapter()
        data = make_data()
        result = adapter.validate(data)
        assert result.success is True
        assert result.operation == "validate"
        # Returns the validated dataset
        assert result.data is not None
        assert len(result.data) == len(data)

    def test_validate_negative_value_fails(self):
        """A negative contact value must fail schema validation."""
        adapter = PanderaAdapter()
        data = [WFMData(timestamp=datetime(2024, 1, 1), value=-5.0)]
        result = adapter.validate(data)
        assert result.success is False
        assert "Schema validation failed" in result.error_message

    def test_validate_empty_data(self):
        adapter = PanderaAdapter()
        # An empty dataset has no typed columns, so the schema check fails.
        # This is the adapter's actual behavior - empty input is not silently
        # accepted as valid.
        result = adapter.validate([])
        assert result.success is False
        assert "Schema validation failed" in result.error_message

    # --- forecast/staff/schedule/optimize must be explicit unsupported ---

    def test_forecast_not_supported(self):
        adapter = PanderaAdapter()
        result = adapter.forecast(make_data())
        assert result.success is False
        assert "does not forecast" in result.error_message.lower()

    def test_staff_not_supported(self):
        adapter = PanderaAdapter()
        result = adapter.staff(make_data())
        assert result.success is False
        assert "does not staff" in result.error_message.lower()

    def test_schedule_not_supported(self):
        adapter = PanderaAdapter()
        result = adapter.schedule(make_data())
        assert result.success is False
        assert (
            "deferred" in result.error_message.lower()
            or "does not schedule" in result.error_message.lower()
        )

    def test_optimize_not_supported(self):
        adapter = PanderaAdapter()
        result = adapter.optimize(make_data())
        assert result.success is False
        assert (
            "deferred" in result.error_message.lower()
            or "does not optimize" in result.error_message.lower()
        )

    def test_execute_operation_unknown(self):
        adapter = PanderaAdapter()
        result = adapter.execute_operation("unknown", [])
        assert result.success is False
        assert "Unknown operation" in result.error_message
