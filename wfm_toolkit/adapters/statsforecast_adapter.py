"""
StatsForecast adapter for Workforce Management Toolkit.

Adapter around the StatsForecast library for statistical time-series
forecasting. The adapter configures a StatsForecast instance with the chosen
model and delegates the forecast to it - it does not implement forecasting
mathematics itself.

Supported models (current StatsForecast 2.x API): AutoARIMA, AutoETS,
SeasonalNaive.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

try:
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA, AutoETS, SeasonalNaive

    has_statsforecast = True
except ImportError:  # pragma: no cover - depends on optional install
    has_statsforecast = False

from ..domain import WFMData
from .base import AdapterConfig, AdapterResult, BaseAdapter

_SUPPORTED_MODELS = ("AutoARIMA", "AutoETS", "SeasonalNaive")


class StatsForecastAdapter(BaseAdapter):
    """Adapter for the StatsForecast library (statistical forecasting)."""

    def __init__(self, config: AdapterConfig | None = None):
        if config is None:
            config = AdapterConfig(
                provider_name="StatsForecast",
                package_name="statsforecast",
                license="Apache-2.0",
                deterministic_level="high",
                required_dependencies=["numpy", "pandas", "statsforecast"],
                optional_dependencies=[],
                configuration_options={
                    "model": "AutoARIMA",
                    "season_length": 7,
                    "forecast_horizon": 7,
                    "freq": "D",
                },
            )
        super().__init__(config)

    def _validate_dependencies(self):
        """Validate that StatsForecast is available."""
        if not has_statsforecast:
            raise ImportError(
                "StatsForecast is not installed. Install with: pip install statsforecast"
            )

    def _initialize_adapter(self):
        """Initialize the adapter."""
        self._model_constructors = {
            "SeasonalNaive": SeasonalNaive,
            "AutoARIMA": AutoARIMA,
            "AutoETS": AutoETS,
        }
        self.last_model = None

    def health_check(self) -> bool:
        """Check that StatsForecast is importable and a small forecast runs."""
        try:
            if not has_statsforecast:
                return False
            df = pd.DataFrame(
                {
                    "unique_id": ["s1"] * 10,
                    "ds": pd.date_range("2023-01-01", periods=10, freq="D"),
                    "y": list(range(10)),
                }
            )
            sf = StatsForecast(models=[SeasonalNaive(season_length=7)], freq="D", n_jobs=1)
            fcst = sf.forecast(df=df, h=3)
            return len(fcst) == 3
        except Exception:
            return False

    def forecast(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """
        Generate a statistical forecast using StatsForecast.

        Parameters (kwargs):
          model           : str  - "AutoARIMA" (default), "AutoETS", or "SeasonalNaive"
          forecast_horizon: int  - number of steps ahead to forecast (default 7)
          season_length   : int  - seasonal period, e.g. 7 for weekly seasonality (default 7)
          freq            : str  - pandas frequency of the data (default "D")

        The ``value`` of each WFMData is treated as the target series. Returns an
        AdapterResult whose ``data`` is a list of WFMData forecast points with the
        point forecast in ``value``.
        """
        try:
            if not has_statsforecast:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="forecast",
                    success=False,
                    data=None,
                    error_message="StatsForecast is not installed",
                )

            if len(data) == 0:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="forecast",
                    success=False,
                    data=None,
                    error_message="No historical data provided for forecasting",
                )

            if len(data) < 2:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="forecast",
                    success=False,
                    data=None,
                    error_message="At least two historical data points are required for forecasting",
                )

            model_name = kwargs.get(
                "model", self.config.configuration_options.get("model", "AutoARIMA")
            )
            if model_name not in _SUPPORTED_MODELS:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="forecast",
                    success=False,
                    data=None,
                    error_message=(
                        f"Unsupported model: {model_name!r}. Supported models: {', '.join(_SUPPORTED_MODELS)}"
                    ),
                )
            horizon = int(
                kwargs.get(
                    "forecast_horizon", self.config.configuration_options.get("forecast_horizon", 7)
                )
            )
            if horizon < 1:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="forecast",
                    success=False,
                    data=None,
                    error_message="forecast_horizon must be >= 1",
                )
            season_length = int(
                kwargs.get(
                    "season_length", self.config.configuration_options.get("season_length", 7)
                )
            )
            if season_length < 1:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="forecast",
                    success=False,
                    data=None,
                    error_message="season_length must be >= 1",
                )
            freq = kwargs.get("freq", self.config.configuration_options.get("freq", "D"))

            df = pd.DataFrame(
                {
                    "unique_id": ["s1"] * len(data),
                    "ds": [d.timestamp for d in data],
                    "y": [d.value for d in data],
                }
            )

            # Build the model using the current StatsForecast 2.x class API.
            constructor = self._model_constructors[model_name]
            models = [constructor(season_length=season_length)]

            sf = StatsForecast(models=models, freq=freq, n_jobs=1)
            forecast_df = sf.forecast(df=df, h=horizon)

            # Locate the forecast column (named after the model alias).
            forecast_col = forecast_df.columns[-1]
            forecast_results = []
            for _, row in forecast_df.iterrows():
                forecast_results.append(
                    WFMData(
                        timestamp=row["ds"],
                        value=float(row[forecast_col]),
                        metadata={"model": model_name, "series": "s1"},
                    )
                )

            self.last_model = model_name
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="forecast",
                success=True,
                data=forecast_results,
                metadata={
                    "provider": "statsforecast",
                    "model_used": model_name,
                    "forecast_horizon": horizon,
                    "season_length": season_length,
                    "freq": freq,
                    "data_points": len(data),
                    "forecast_points": len(forecast_results),
                },
            )

        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="forecast",
                success=False,
                data=None,
                error_message=f"forecast() failed: {e}",
            )

    def staff(self, data: Any, **kwargs) -> AdapterResult:
        """Unsupported - staffing is delegated to the pyworkforce adapter."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="staff",
            success=False,
            data=None,
            error_message="Staffing is not provided by StatsForecast; use the pyworkforce adapter.",
        )

    def schedule(self, data: Any, **kwargs) -> AdapterResult:
        """Unsupported - Scheduling is deferred."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="schedule",
            success=False,
            data=None,
            error_message="Scheduling is not implemented in this stage.",
        )

    def optimize(self, data: Any, **kwargs) -> AdapterResult:
        """Unsupported - optimization is deferred."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="optimize",
            success=False,
            data=None,
            error_message="Optimization is not implemented in this stage.",
        )

    def validate(self, data: Any, **kwargs) -> AdapterResult:
        """Unsupported - data validation is delegated to the Pandera adapter."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="validate",
            success=False,
            data=None,
            error_message="Data validation is delegated to the Pandera adapter.",
        )
