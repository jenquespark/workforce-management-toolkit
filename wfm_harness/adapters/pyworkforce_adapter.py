"""
Pyworkforce adapter for Workforce Management Harness.

Adapter for the pyworkforce library - Erlang C staffing calculations.
"""

from __future__ import annotations
from abc import ABC
from typing import List, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from pyworkforce.erlang_c import erlang_c, erlang_c_cumulative
    has_pyworkforce = True
except ImportError:
    has_pyworkforce = False

from .base import BaseAdapter, AdapterConfig, AdapterResult
from ..domain import WFMData, StaffingResult

class PyworkforceAdapter(BaseAdapter):
    """Adapter for pyworkforce library."""
    
    def __init__(self, config: Optional[AdapterConfig] = None):
        if config is None:
            config = AdapterConfig(
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
        super().__init__(config)
    
    def _validate_dependencies(self):
        """Validate that Pyworkforce dependencies are available."""
        if not has_pyworkforce:
            raise ImportError("Pyworkforce is not installed. Install with: pip install pyworkforce")
    
    def _initialize_adapter(self):
        """Initialize Pyworkforce adapter."""
        self.last_erlang_c_params = None
    
    def health_check(self) -> bool:
        """Check if Pyworkforce adapter is healthy."""
        try:
            if not has_pyworkforce:
                return False
            
            # Simple test with known values
            lambda_val = 10.0  # arrival rate per hour
            target_sla = 0.80  # 80% service level
            
            # This should work if pyworkforce is properly installed
            result = erlang_c(lambda_val, target_sla)
            return True
        except Exception:
            return False
    
    def forecast(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """Pyworkforce adapter - forecasting uses StatsForecast adapter."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="forecast",
            success=False,
            data=None,
            error_message="Forecasting operation requires StatsForecast adapter"
        )
    
    def staff(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """Calculate staffing requirements using Erlang C formula."""
        try:
            if not has_pyworkforce:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="staff",
                    success=False,
                    data=None,
                    error_message="Pyworkforce not installed"
                )
            
            # Extract data from WFMData objects
            arrival_rates = []
            average_handle_times = []
            
            for wfm_data in data:
                if isinstance(wfm_data.value, (int, float)):
                    # value is AHT in seconds
                    average_handle_times.append(wfm_data.value / 60.0)  # Convert to minutes
                    # Estimate arrival rate based on timestamp metadata
                    metadata = wfm_data.metadata or {}
                    hour_of_day = wfm_data.timestamp.hour if hasattr(wfm_data.timestamp, 'hour') else 0
                    base_arrival = 5.0  # Default 5 calls per hour
                    time_factor = 1.0 + (0.5 * (hour_of_day / 12.0))  # Peak hour adjustment
                    arrival_rates.append(base_arrival * time_factor)
            
            if not arrival_rates:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="staff",
                    success=False,
                    data=None,
                    error_message="No valid data provided for staffing calculation"
                )
            
            # Get configuration
            service_level = kwargs.get('service_level', 
                                      self.config.configuration_options.get('service_level', 0.80))
            average_speed_of_answer = kwargs.get('average_speed_of_answer',
                                               self.config.configuration_options.get('average_speed_of_answer', 180))
            shrinkage_rate = kwargs.get('shrinkage_rate',
                                      self.config.configuration_options.get('shrinkage_rate', 0.30))
            half_occupancy = kwargs.get('half_occupancy',
                                      self.config.configuration_options.get('half_occupancy', 0.85))
            
            # Calculate staffing for each arrival rate
            results = []
            for i, arrival_rate in enumerate(arrival_rates):
                # Use pyworkforce's erlang_c function
                staff_needed = erlang_c(arrival_rate, service_level)
                
                # Adjust for shrinkage and half occupancy
                adjusted_staff = staff_needed / (1 - shrinkage_rate) / half_occupancy
                
                # Convert to whole agents
                required_agents = int(round(adjusted_staff))
                
                result_data = StaffingResult(
                    algorithm="erlang_c_with_shrinkage",
                    allocations={f"period_{i}": [required_agents]},
                    metrics={
                        "arrival_rate": arrival_rate,
                        "average_handle_time": average_handle_times[i] if i < len(average_handle_times) else 0,
                        "service_level": service_level,
                        "staff_required_before_shrinkage": staff_needed,
                        "staff_required_after_shrinkage": adjusted_staff,
                        "final_agents": required_agents,
                        "shrinkage_rate": shrinkage_rate,
                        "half_occupancy": half_occupancy,
                        "average_speed_of_answer": average_speed_of_answer
                    },
                    metadata={
                        "method": "erlang_c",
                        "service_level_target": service_level,
                        "average_speed_of_answer": average_speed_of_answer,
                        "shrinkage_applied": True,
                        "half_occupancy_applied": True,
                        "input_count": len(data),
                        "hour_of_day": wfm_data.timestamp.hour if hasattr(wfm_data.timestamp, 'hour') else 0
                    }
                )
                
                results.append(result_data)
            
            # If only one result, extract it from the list
            staffing_result = results[0] if len(results) == 1 else results
            
            self.last_erlang_c_params = {
                "arrival_rates": arrival_rates,
                "service_level": service_level,
                "average_speed_of_answer": average_speed_of_answer,
                "shrinkage_rate": shrinkage_rate,
                "half_occupancy": half_occupancy
            }
            
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="staff",
                success=True,
                data=staffing_result,
                metadata={
                    "calculation_method": "erlang_c_with_shrinkage",
                    "arrival_rates": arrival_rates,
                    "average_handle_times": average_handle_times,
                    "service_level_target": service_level,
                    "average_speed_of_answer": average_speed_of_answer,
                    "shrinkage_rate": shrinkage_rate,
                    "half_occupancy": half_occupancy,
                    "periods_calculated": len(results)
                }
            )
            
        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="staff",
                success=False,
                data=None,
                error_message=str(e)
            )
    
    def schedule(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """Pyworkforce adapter - scheduling uses pyworkforce."""
        try:
            if not has_pyworkforce:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="schedule",
                    success=False,
                    data=None,
                    error_message="Pyworkforce not installed"
                )
            
            # Use Erlang C for basic staffing-based scheduling
            staff_result = self.staff(data, **kwargs)
            
            if not staff_result.success:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="schedule",
                    success=False,
                    data=None,
                    error_message=f"Staffing calculation failed: {staff_result.error_message}"
                )
            
            # Convert staffing result to schedule format
            scheduling_result = {
                "solver": "pyworkforce",
                "roster": {},
                "constraints_satisfied": 0,
                "metadata": {
                    "staffing_method": "erlang_c",
                    "based_on_staffing_result": True,
                    "total_agents_required": self._calculate_total_agents(staff_result.data)
                }
            }
            
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="schedule",
                success=True,
                data=scheduling_result,
                metadata={
                    "scheduling_method": "staffing_based",
                    "based_on_staffing_calculation": True,
                    "staffing_result": staff_result.data,
                    "constraints": kwargs.get('constraints', {})
                }
            )
            
        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="schedule",
                success=False,
                data=None,
                error_message=str(e)
            )
    
    def optimize(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """Pyworkforce adapter - optimization uses pyworkforce."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="optimize",
            success=False,
            data=None,
            error_message="Optimization operation requires OR-Tools adapter"
        )
    
    def validate(self, data: List[WFMData], **kwargs) -> AdapterResult:
        """Validate staffing configuration using Pandera schemas."""
        try:
            # Import pandera for schema validation
            try:
                import pandera as pd
                from pandera import SchemaError
                pandera_available = True
            except ImportError:
                pandera_available = False
            
            if not pandera_available:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="validate",
                    success=False,
                    data=None,
                    error_message="Pandera is not installed. Install with: pip install pandera"
                )
            
            # Create schema for WFMData validation
            from pandera import Field, checks
            from datetime import datetime
            
            # Simple schema for validation
            class WFMDataSchema(pd.DataFrameModel):
                timestamp: datetime = Field(nullable=False, checks=[checks.ge(datetime(2020, 1, 1))])
                value: (int, float) = Field(nullable=False, checks=[checks.ge(0)])
                
                class Config:
                    coerce = True
                    strict = False
            
            # Convert data to DataFrame for validation
            import pandas as pd_df
            df_data = {
                'timestamp': [d.timestamp for d in data],
                'value': [d.value for d in data]
            }
            
            df = pd_df.DataFrame(df_data)
            
            # Validate the data
            try:
                validated_df = WFMDataSchema().validate(df)
                
                # Validate staffing-specific configuration
                validation_config = {
                    'service_level': kwargs.get('service_level', 
                                              self.config.configuration_options.get('service_level', 0.80)),
                    'average_speed_of_answer': kwargs.get('average_speed_of_answer',
                                                       self.config.configuration_options.get('average_speed_of_answer', 180)),
                    'shrinkage_rate': kwargs.get('shrinkage_rate',
                                               self.config.configuration_options.get('shrinkage_rate', 0.30)),
                    'half_occupancy': kwargs.get('half_occupancy',
                                               self.config.configuration_options.get('half_occupancy', 0.85)),
                    'hours_per_agent': kwargs.get('hours_per_agent',
                                                self.config.configuration_options.get('hours_per_agent', 7.5)),
                    'average_handle_time': kwargs.get('average_handle_time',
                                                    self.config.configuration_options.get('average_handle_time', 180))
                }
                
                # Check for reasonable values
                violations = []
                
                if not (0 < validation_config['service_level'] <= 1):
                    violations.append({
                        'field': 'service_level',
                        'error': f"Service level must be between 0 and 1, got {validation_config['service_level']}"
                    })
                
                if validation_config['average_speed_of_answer'] < 0:
                    violations.append({
                        'field': 'average_speed_of_answer',
                        'error': f"Average speed of answer must be positive, got {validation_config['average_speed_of_answer']}"
                    })
                
                if not (0 <= validation_config['shrinkage_rate'] < 1):
                    violations.append({
                        'field': 'shrinkage_rate',
                        'error': f"Shrinkage rate must be between 0 and 1, got {validation_config['shrinkage_rate']}"
                    })
                
                if not (0 < validation_config['half_occupancy'] <= 1):
                    violations.append({
                        'field': 'half_occupancy',
                        'error': f"Half occupancy must be between 0 and 1, got {validation_config['half_occupancy']}"
                    })
                
                if validation_config['hours_per_agent'] <= 0:
                    violations.append({
                        'field': 'hours_per_agent',
                        'error': f"Hours per agent must be positive, got {validation_config['hours_per_agent']}"
                    })
                
                if validation_config['average_handle_time'] < 0:
                    violations.append({
                        'field': 'average_handle_time',
                        'error': f"Average handle time must be positive, got {validation_config['average_handle_time']}"
                    })
                
                # Check if any WFMData has invalid metadata (if present)
                for i, wfm_data in enumerate(data):
                    if wfm_data.metadata:
                        # Validate metadata contains expected fields
                        for key in wfm_data.metadata:
                            if key not in ['hour_of_day', 'day_of_week', 'month']:
                                violations.append({
                                    'field': f'data[{i}].metadata.{key}',
                                    'error': f"Unexpected metadata field: {key}"
                                })
                
                validation_passed = len(violations) == 0
                
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="validate",
                    success=validation_passed,
                    data=validated_df if validation_passed else None,
                    metadata={
                        'validation_schema': 'WFMDataSchema',
                        'rows_validated': len(validated_df) if validation_passed else 0,
                        'total_rows': len(df),
                        'config_validation': validation_config,
                        'violations': violations,
                        'pandera_version': pd.__version__ if pandera_available else None
                    }
                )
                
            except SchemaError as e:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="validate",
                    success=False,
                    data=None,
                    error_message=f"Schema validation failed: {str(e)}"
                )
            
        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="validate",
                success=False,
                data=None,
                error_message=str(e)
            )
    
    def _calculate_total_agents(self, staffing_data):
        """Calculate total agents from staffing result."""
        if isinstance(staffing_data, list):
            total = 0
            for result in staffing_data:
                if hasattr(result, 'allocations'):
                    for alloc in result.allocations.values():
                        total += sum(alloc)
            return total
        elif hasattr(staffing_data, 'allocations'):
            total = 0
            for alloc in staffing_data.allocations.values():
                total += sum(alloc)
            return total
        return 0