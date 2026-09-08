"""
Pandera adapter for Workforce Management Toolkit.

Adapter around the Pandera library - a data validation provider only.

Pandera validates data; it does not forecast, staff, schedule, or optimize.
The only executable capability is `validate()`. The other methods of the
BaseAdapter surface return an explicit unsupported result rather than
pretending to perform the named operation.
"""

from __future__ import annotations

import pandas as pd
from pandera import Check, Column, DataFrameSchema
from pandera.errors import SchemaError

from ..domain import WFMData
from .base import AdapterConfig, AdapterResult, BaseAdapter


def _convert_to_dataframe(data: list[WFMData]) -> pd.DataFrame:
    """Convert a list of WFMData to a pandas DataFrame for validation."""
    return pd.DataFrame(
        {
            "timestamp": [d.timestamp for d in data],
            "value": [d.value for d in data],
        }
    )


def _convert_to_wfmdata(df: pd.DataFrame) -> list[WFMData]:
    """Convert a validated DataFrame back to a list of WFMData."""
    return [
        WFMData(
            timestamp=row["timestamp"],
            value=row["value"],
            metadata={},
        )
        for _, row in df.iterrows()
    ]


class PanderaAdapter(BaseAdapter):
    """Adapter for the Pandera library - data validation only."""

    def __init__(self, config: AdapterConfig | None = None):
        if config is None:
            config = AdapterConfig(
                provider_name="Pandera",
                package_name="pandera",
                license="MIT",
                deterministic_level="high",
                required_dependencies=["numpy", "pandas", "pandera"],
                optional_dependencies=[],
                configuration_options={
                    "strict_mode": True,
                    "input_schema": "wfm_data",
                    "output_schema": "wfm_data",
                },
            )
        super().__init__(config)
        self._initialize_validation()

    def _validate_dependencies(self):
        """Validate that Pandera is available."""
        try:
            import pandera

            if not getattr(pandera, "__version__", None):
                raise ImportError("Pandera version not detected")
        except ImportError:
            raise ImportError("Pandera is not installed. Install with: pip install pandera")

    def _initialize_validation(self):
        """Initialize the input/output Pandera schemas for WFMData validation."""
        self.input_schema = DataFrameSchema(
            columns={
                "timestamp": Column(
                    dtype="datetime64[ns]",
                    nullable=False,
                    checks=[Check(lambda x: all(x >= pd.Timestamp("2020-01-01")))],
                ),
                "value": Column(
                    dtype="float64",
                    nullable=False,
                    checks=[Check(lambda x: all(x > 0)), Check(lambda x: all(x < 1e6))],
                ),
            },
            checks=[
                Check(lambda df: len(df) > 0, name="non_empty"),
                Check(
                    lambda df: df["timestamp"].is_monotonic_increasing, name="timestamps_monotonic"
                ),
            ],
        )
        self.output_schema = DataFrameSchema(
            columns={
                "timestamp": Column(dtype="datetime64[ns]", nullable=False),
                "value": Column(dtype="float64", nullable=False),
            },
        )

    def health_check(self) -> bool:
        """Check that Pandera is importable and the input schema accepts valid data."""
        try:
            test_df = pd.DataFrame(
                {
                    "timestamp": [pd.Timestamp("2023-01-01"), pd.Timestamp("2023-01-02")],
                    "value": [100.0, 150.0],
                }
            )
            validated = self.input_schema.validate(test_df)
            return len(validated) == 2
        except Exception:
            return False

    def forecast(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """Unsupported - Pandera does not forecast."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="forecast",
            success=False,
            data=None,
            error_message="Pandera is a data validation provider; it does not forecast. Use the StatsForecast adapter.",
        )

    def staff(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """Unsupported - Pandera does not staff."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="staff",
            success=False,
            data=None,
            error_message="Pandera is a data validation provider; it does not staff. Use the pyworkforce adapter.",
        )

    def schedule(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """Unsupported - Pandera does not schedule."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="schedule",
            success=False,
            data=None,
            error_message="Pandera is a data validation provider; it does not schedule. Scheduling is deferred.",
        )

    def optimize(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """Unsupported - Pandera does not optimize."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="optimize",
            success=False,
            data=None,
            error_message="Pandera is a data validation provider; it does not optimize. Optimization is deferred.",
        )

    def validate(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """Validate WFMData against the input/output schemas (the executable capability)."""
        try:
            input_df = _convert_to_dataframe(data)
            validated = self.input_schema.validate(input_df)
            output_df = _convert_to_dataframe(_convert_to_wfmdata(validated))
            self.output_schema.validate(output_df)

            result_data = _convert_to_wfmdata(validated)
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="validate",
                success=True,
                data=result_data,
                metadata={
                    "adapter_version": self.config.package_name,
                    "row_count": len(result_data),
                    "schema_version": "1.0",
                },
            )
        except SchemaError as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="validate",
                success=False,
                data=None,
                error_message=f"Schema validation failed: {str(e)}",
            )
        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="validate",
                success=False,
                data=None,
                error_message=f"Validation failed: {str(e)}",
            )
