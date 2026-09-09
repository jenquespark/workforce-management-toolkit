"""Tests for PanderaAdapter - a data validation provider only.

Pandera validates; it does not forecast, staff, schedule, or optimize.
The only executable capability is validate(). The other BaseAdapter methods
return explicit unsupported results.
"""

import pytest

pytest.importorskip("pandera", reason="pandera is not installed")

from datetime import datetime, timedelta

import pandas as pd

from wfm_toolkit.adapters.pandera_adapter import PanderaAdapter
from wfm_toolkit.domain import WFMData


def make_data(count=5, value=100.0, start=None):
    start = start or datetime(2024, 1, 1)
    return [WFMData(timestamp=start + timedelta(hours=i), value=value + i) for i in range(count)]


def make_tz_aware_data(count=5, value=100.0):
    start = pd.Timestamp("2024-01-01T08:00:00Z")
    return [WFMData(timestamp=start + pd.Timedelta(hours=i), value=value + i) for i in range(count)]


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
        result = adapter.validate(make_data())
        assert result.success is True

    def test_validate_timezone_aware_timestamps_succeeds(self):
        """ISO-8601 'Z' / timezone-aware timestamps must validate.

        The CLI loader accepts timezone-aware ISO timestamps; the Pandera schema
        requires naive ``datetime64[ns]``. _convert_to_dataframe normalizes
        aware timestamps to naive UTC so both input styles are accepted.
        """
        adapter = PanderaAdapter()
        result = adapter.validate(make_tz_aware_data())
        assert result.success is True

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

    # --- Parity: direct pandera validation vs adapter ---

    def test_parity_valid_dataset(self):
        """Adapter must accept what a direct pandera validation accepts."""
        adapter = PanderaAdapter()
        data = make_data()
        df = pd.DataFrame(
            {
                "timestamp": [d.timestamp for d in data],
                "value": [d.value for d in data],
            }
        )
        # Direct pandera validation of the same frame must pass too.
        validated = adapter.input_schema.validate(df)
        assert len(validated) == len(data)
        result = adapter.validate(data)
        assert result.success is True

    def test_parity_invalid_dataset(self):
        """Adapter must reject what a direct pandera validation rejects."""
        adapter = PanderaAdapter()
        bad = [WFMData(timestamp=datetime(2024, 1, 1), value=-5.0)]
        df = pd.DataFrame(
            {
                "timestamp": [d.timestamp for d in bad],
                "value": [d.value for d in bad],
            }
        )
        with pytest.raises(Exception):
            adapter.input_schema.validate(df)
        result = adapter.validate(bad)
        assert result.success is False

    def test_missing_field_fails(self):
        """A dataset missing the value column must fail structured validation."""
        adapter = PanderaAdapter()
        df = pd.DataFrame({"timestamp": [pd.Timestamp("2024-01-01")]})
        with pytest.raises(Exception):
            adapter.input_schema.validate(df)
        # Through the adapter: WFMData without value becomes NaN -> schema error
        data = [WFMData(timestamp=datetime(2024, 1, 1), value=None)]
        result = adapter.validate(data)
        assert result.success is False
        assert "Schema validation failed" in result.error_message
