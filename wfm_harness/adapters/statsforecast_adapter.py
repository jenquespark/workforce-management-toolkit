"""
StatsForecast adapter for Workforce Management Harness.

Adapter for the StatsForecast library - deterministic forecasting.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    from statsforecast import StatsForecast
    from statsforecast.models import SeasonalNaive, AutoARIMA, AutoETS
    from statsforecast.utils import difference, forecast_accuracy
    has_statsforecast = True
except ImportError:
    has_statsforecast = False

from .base import BaseAdapter, AdapterConfig, AdapterResult
from ..domain import WFMData, ForecastResult

class StatsForecastAdapter(BaseAdapter):
    """Adapter for StatsForecast library."""
    
    def __init__(self, config: Optional[AdapterConfig] = None):
        if config is None:
            config = AdapterConfig(
                provider_name="StatsForecast",
                package_name="statsforecast",
                license="MIT",
                deterministic_level="high",
                required_dependencies=["numpy", "pandas", "statsforecast"],
                optional_dependencies=[],
                configuration_options={
                    "model": "AutoARIMA",
                    "seasonality": 7,
                    "forecast_horizon": 7,
                    "interval": 0.95
                }
            )
        super().__init__(config)
    
    def _validate_dependencies(self):
        """Validate that StatsForecast dependencies are available."""
        if not has_statsforecast:
            raise ImportError("StatsForecast is not installed. Install with: pip install statsforecast")
    
    def _initialize_adapter(self):
        """Initialize StatsForecast adapter."""
        self.available_models = {
            "SeasonalNaive": SeasonalNaive,
            "AutoARIMA": AutoARIMA,
            "AutoETS": AutoETS
        }
        self.last_model = None
    
    def health_check(self) -> bool:
        """Check if StatsForecast adapter is healthy."""
        try:
            if not has_statsforecast:
                return False
            
            # Create a simple test forecast
            test_data = pd.DataFrame({
                'ds': pd.date_range('2023-01-01', periods=10, freq='D'),
                'y': np.random.randn(10).cumsum()
            })
            
            models = [SeasonalNaive()]
            forecast = StatsForecast.forecast(test_data, models, 7)
            return True
        except Exception:
            return False
    
    def forecast(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """Generate forecasts using StatsForecast."""
        try:
            if not has_statsforecast:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="forecast",
                    success=False,
                    data=None,
                    error_message="StatsForecast not installed"
                )
            
            # Convert WFMData to pandas DataFrame
            df_data = {
                'ds': [d.timestamp for d in data],
                'y': [d.value for d in data]
            }
            df = pd.DataFrame(df_data)
            
            # Get model configuration
            model_name = kwargs.get('model', self.config.configuration_options.get('model', 'AutoARIMA'))
            forecast_horizon = kwargs.get('forecast_horizon', self.config.configuration_options.get('forecast_horizon', 7))
            season = kwargs.get('seasonality', self.config.configuration_options.get('seasonality', 7))
            interval = kwargs.get('interval', self.config.configuration_options.get('interval', 0.95))
            
            # Initialize model
            model_class = self.available_models.get(model_name)
            if model_class is None:
                model_class = AutoARIMA
            
            model = model_class()
            
            # Generate forecast
            forecast_df = StatsForecast.forecast(
                df, 
                [model], 
                forecast_horizon,
                season=season,
                interval=interval
            )
            
            # Convert back to WFMData format
            forecast_results = []
            for _, row in forecast_df.iterrows():
                forecast_results.append(WFMData(
                    timestamp=row['ds'],
                    value=row['yhat'],
                    metadata={
                        'yhat_lower': row.get('yhat_lower', row['yhat'] - 1.96 * row.get('yhat_upper_std', 1)),
                        'yhat_upper': row.get('yhat_upper', row['yhat'] + 1.96 * row.get('yhat_upper_std', 1)),
                        'model': model_name
                    }
                ))
            
            result = AdapterResult(
                adapter_name=self.config.provider_name,
                operation="forecast",
                success=True,
                data=forecast_results,
                metadata={
                    'model_used': model_name,
                    'forecast_horizon': forecast_horizon,
                    'seasonality': season,
                    'interval': interval,
                    'data_points': len(data),
                    'forecast_points': len(forecast_results)
                }
            )
            
            self.last_model = model_name
            return result
            
        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="forecast",
                success=False,
                data=None,
                error_message=str(e)
            )
    
    def staff(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """StatsForecast adapter - staffing uses pyworkforce."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="staff",
            success=False,
            data=None,
            error_message="Staffing operation requires pyworkforce adapter"
        )
    
    def schedule(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """StatsForecast adapter - scheduling uses pyworkforce or OR-Tools."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="schedule",
            success=False,
            data=None,
            error_message="Scheduling operation requires pyworkforce or OR-Tools adapter"
        )
    
    def optimize(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """StatsForecast adapter - optimization uses OR-Tools."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="optimize",
            success=False,
            data=None,
            error_message="Optimization operation requires OR-Tools adapter"
        )
    
    def validate(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """StatsForecast adapter - validation uses Pandera."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="validate",
            success=False,
            data=None,
            error_message="Validation operation requires Pandera adapter"
        )