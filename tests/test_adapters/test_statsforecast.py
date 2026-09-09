"""Tests for StatsForecastAdapter - verified against the installed statsforecast
upstream API (v2.x). The adapter is a thin normalization layer: it must not
change forecast mathematics, only normalize provider output.

These tests call the REAL installed statsforecast library and compare the
Toolkit result against a direct provider call (parity).
"""

import pytest

pytest.importorskip("statsforecast", reason="statsforecast is not installed")

from datetime import datetime, timedelta

import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA, AutoETS, SeasonalNaive

from wfm_toolkit.adapters.statsforecast_adapter import StatsForecastAdapter
from wfm_toolkit.domain import WFMData


def make_series(n=30, start=None, value=100.0):
    start = start or datetime(2024, 1, 1)
    return [WFMData(timestamp=start + timedelta(days=i), value=value + i % 7) for i in range(n)]


def direct_statsforecast(data, model_name="SeasonalNaive", h=5, season_length=7, freq="D"):
    """Direct call to the upstream library for parity comparison."""
    df = pd.DataFrame(
        {
            "unique_id": ["s1"] * len(data),
            "ds": [d.timestamp for d in data],
            "y": [d.value for d in data],
        }
    )
    if model_name == "SeasonalNaive":
        models = [SeasonalNaive(season_length=season_length)]
    elif model_name == "AutoARIMA":
        models = [AutoARIMA(season_length=season_length)]
    else:
        models = [AutoETS(season_length=season_length)]
    sf = StatsForecast(models=models, freq=freq, n_jobs=1)
    return sf.forecast(df=df, h=h)


class TestStatsForecastAdapter:
    """Test the StatsForecast adapter against the real upstream API."""

    def test_instantiation(self):
        adapter = StatsForecastAdapter()
        assert adapter.config.provider_name == "StatsForecast"
        assert adapter.config.package_name == "statsforecast"

    def test_health_check_reflects_install(self):
        adapter = StatsForecastAdapter()
        try:
            import statsforecast  # noqa: F401

            assert adapter.health_check() is True
        except ImportError:
            assert adapter.health_check() is False

    # --- parity: Toolkit result must match direct upstream call ---

    def test_parity_seasonal_naive(self):
        adapter = StatsForecastAdapter()
        data = make_series(n=30)
        result = adapter.forecast(
            data, model="SeasonalNaive", forecast_horizon=5, season_length=7, freq="D"
        )
        assert result.success is True
        direct = direct_statsforecast(data, "SeasonalNaive", h=5, season_length=7)
        # Direct forecast values (last column)
        col = direct.columns[-1]
        direct_values = direct[col].tolist()
        toolkit_values = [p.value for p in result.data]
        assert len(toolkit_values) == 5
        # Values must be equal within float tolerance (same provider, same model)
        for tv, dv in zip(toolkit_values, direct_values):
            assert abs(tv - dv) < 1e-6

    def test_parity_autoarima(self):
        adapter = StatsForecastAdapter()
        data = make_series(n=60)
        result = adapter.forecast(
            data, model="AutoARIMA", forecast_horizon=5, season_length=7, freq="D"
        )
        assert result.success is True
        direct = direct_statsforecast(data, "AutoARIMA", h=5, season_length=7)
        col = direct.columns[-1]
        direct_values = direct[col].tolist()
        toolkit_values = [p.value for p in result.data]
        assert len(toolkit_values) == 5
        for tv, dv in zip(toolkit_values, direct_values):
            assert abs(tv - dv) < 1e-6

    def test_parity_autoets(self):
        adapter = StatsForecastAdapter()
        data = make_series(n=60)
        result = adapter.forecast(
            data, model="AutoETS", forecast_horizon=5, season_length=7, freq="D"
        )
        assert result.success is True
        direct = direct_statsforecast(data, "AutoETS", h=5, season_length=7)
        col = direct.columns[-1]
        direct_values = direct[col].tolist()
        toolkit_values = [p.value for p in result.data]
        assert len(toolkit_values) == 5
        for tv, dv in zip(toolkit_values, direct_values):
            assert abs(tv - dv) < 1e-6

    # --- domain boundaries ---

    def test_empty_input_fails(self):
        adapter = StatsForecastAdapter()
        result = adapter.forecast([])
        assert result.success is False
        assert "No historical data" in result.error_message

    def test_single_point_fails(self):
        adapter = StatsForecastAdapter()
        result = adapter.forecast([WFMData(timestamp=datetime(2024, 1, 1), value=5.0)])
        assert result.success is False
        assert "At least two" in result.error_message

    def test_invalid_model_fails(self):
        adapter = StatsForecastAdapter()
        result = adapter.forecast(make_series(10), model="NotAModel")
        assert result.success is False
        assert "Unsupported model" in result.error_message

    def test_zero_horizon_fails(self):
        adapter = StatsForecastAdapter()
        result = adapter.forecast(make_series(10), forecast_horizon=0)
        assert result.success is False
        assert "forecast_horizon must be >= 1" in result.error_message

    def test_non_numeric_value_fails(self):
        adapter = StatsForecastAdapter()
        data = [
            WFMData(timestamp=datetime(2024, 1, 1), value=1.0),
            WFMData(timestamp=datetime(2024, 1, 2), value="not-a-number"),
        ]
        result = adapter.forecast(data)
        assert result.success is False

    # --- unsupported operations ---

    def test_staff_not_supported(self):
        adapter = StatsForecastAdapter()
        result = adapter.staff([])
        assert result.success is False
        assert "pyworkforce" in result.error_message.lower()

    def test_schedule_not_supported(self):
        adapter = StatsForecastAdapter()
        result = adapter.schedule([])
        assert result.success is False

    def test_optimize_not_supported(self):
        adapter = StatsForecastAdapter()
        result = adapter.optimize([])
        assert result.success is False

    def test_validate_not_supported(self):
        adapter = StatsForecastAdapter()
        result = adapter.validate([])
        assert result.success is False
        assert "pandera" in result.error_message.lower()
