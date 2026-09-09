"""
Pandera adapter for Workforce Management Toolkit.

Adapter around the Pandera library - a data validation provider only.

Pandera validates data; it does not forecast, staff, schedule, or optimize.
The only executable capability is `validate()`. The other methods of the
BaseAdapter surface return an explicit unsupported result rather than
pretending to perform the named operation.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from pandera.errors import SchemaError
from pandera.pandas import Check, Column, DataFrameSchema

from ..domain import WFMData
from .base import AdapterConfig, AdapterResult, BaseAdapter

# A WFM timestamp at or after this UTC instant is considered plausible.
# Use timezone-naive for compatibility with test data; pandas will treat
# naive datetimes as UTC for comparison purposes.
_MIN_TIMESTAMP = pd.Timestamp("2020-01-01")
# A WFM value must be a positive finite number below this cap (units-agnostic
# sanity bound; a single interval never legitimately exceeds 1M units).
_MAX_VALUE = 1e6


def _convert_to_dataframe(data: list[WFMData]) -> pd.DataFrame:
    """Convert a list of WFMData to a pandas DataFrame for validation."""
    return pd.DataFrame(
        {
            "timestamp": [d.timestamp for d in data],
            "value": [d.value for d in data],
        }
    )


def _convert_to_wfmdata(df: pd.DataFrame) -> list[WFMData]:
    """Convert a validated DataFrame back to a list of WFMData.

    Note: original per-point ``metadata`` is not preserved through Pandera
    validation; the exported points carry empty metadata.
    """
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
        except ImportError as exc:
            raise ImportError(
                "Pandera is not installed. Install with: pip install pandera"
            ) from exc

    def _initialize_validation(self):
        """Initialize the input/output Pandera schemas for WFMData validation."""
        self.input_schema = DataFrameSchema(
            columns={
                "timestamp": Column(
                    dtype="datetime64[ns]",
                    nullable=False,
                    checks=[
                        Check(lambda x: all(x >= _MIN_TIMESTAMP), name="timestamp_not_before_2020")
                    ],
                ),
                "value": Column(
                    dtype="float64",
                    nullable=False,
                    checks=[
                        Check(lambda x: all(x > 0), name="value_positive"),
                        Check(lambda x: all(x < _MAX_VALUE), name="value_below_1e6"),
                    ],
                ),
            },
            checks=[
                Check(lambda df: len(df) > 0, name="non_empty"),
                Check(
                    lambda df: df["timestamp"].is_monotonic_increasing,
                    name="timestamps_monotonic",
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

    def forecast(self, data: Any, **kwargs) -> AdapterResult:
        """Unsupported - Pandera does not forecast."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="forecast",
            success=False,
            data=None,
            error_message=(
                "Pandera is a data validation provider; it does not forecast. Use the StatsForecast adapter."
            ),
        )

    def staff(self, data: Any, **kwargs) -> AdapterResult:
        """Unsupported - Pandera does not staff."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="staff",
            success=False,
            data=None,
            error_message=(
                "Pandera is a data validation provider; it does not staff. Use the pyworkforce adapter."
            ),
        )

    def schedule(self, data: Any, **kwargs) -> AdapterResult:
        """Unsupported - Pandera does not schedule."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="schedule",
            success=False,
            data=None,
            error_message=(
                "Pandera is a data validation provider; it does not schedule. Scheduling is deferred."
            ),
        )

    def optimize(self, data: Any, **kwargs) -> AdapterResult:
        """Unsupported - Pandera does not optimize."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="optimize",
            success=False,
            data=None,
            error_message=(
                "Pandera is a data validation provider; it does not optimize. Optimization is deferred."
            ),
        )

    def validate(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """Validate WFMData against the canonical schema (the executable capability).

        Returns a structured failure with the Pandera ``SchemaError`` message on
        invalid input; never a fake success. ``data`` may be a list of WFMData.
        """
        try:
            input_df = _convert_to_dataframe(data)
            validated = self.input_schema.validate(input_df)

            # The input schema already guarantees the validated frame conforms to
            # the output shape; validate the round-tripped frame to be explicit
            # about the output contract.
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
                error_message=f"Schema validation failed: {e}",
            )
        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="validate",
                success=False,
                data=None,
                error_message=f"Validation failed: {e}",
            )
