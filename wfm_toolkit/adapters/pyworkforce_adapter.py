"""
Pyworkforce adapter for Workforce Management Toolkit.

Adapter around the pyworkforce library for Erlang C staffing calculations.

The pyworkforce ErlangC API takes explicit business inputs - it never invents
contact demand. All staffing parameters (transactions, average handling time,
target answer speed, interval duration, shrinkage, occupancy) must be supplied
by the caller; the adapter only converts and delegates to pyworkforce.
"""

from __future__ import annotations

import warnings
from typing import Any

warnings.filterwarnings("ignore")

try:
    from pyworkforce import ErlangC

    has_pyworkforce = True
except ImportError:
    has_pyworkforce = False

from ..domain import StaffingResult  # noqa: E402  (after optional-dep guard)
from .base import AdapterConfig, AdapterResult, BaseAdapter  # noqa: E402

# pyworkforce parameter units (per the current upstream API).
#   transactions : total number of transactions arriving in the interval (float)
#   aht          : average handling time of a transaction, in MINUTES (float)
#   asa          : required average speed of answer, in MINUTES (float)
#   interval     : interval length, in MINUTES (int)
#   shrinkage    : fraction of time an operator is not available, in [0, 1) (float)
#   service_level: target service level, in [0, 1] (float)        [via required_positions]
#   max_occupancy: max fraction of time a transaction occupies a position, (0, 1] [via required_positions]


class PyworkforceAdapter(BaseAdapter):
    """Adapter for the pyworkforce library (Erlang C staffing)."""

    def __init__(self, config: AdapterConfig | None = None):
        if config is None:
            config = AdapterConfig(
                provider_name="Pyworkforce",
                package_name="pyworkforce",
                license="MIT",
                deterministic_level="high",
                required_dependencies=["pyworkforce"],
                optional_dependencies=[],
                configuration_options={
                    # Defaults mirror pyworkforce's own reference example.
                    "service_level": 0.80,
                    "max_occupancy": 0.85,
                    "shrinkage": 0.0,
                },
            )
        super().__init__(config)

    def _validate_dependencies(self):
        """Validate that pyworkforce is available."""
        if not has_pyworkforce:
            raise ImportError("pyworkforce is not installed. Install with: pip install pyworkforce")

    def _initialize_adapter(self):
        """Initialize the adapter."""
        self.last_staffing_result = None

    def health_check(self) -> bool:
        """Check that pyworkforce is importable and ErlangC can be constructed."""
        try:
            if not has_pyworkforce:
                return False
            # Constructing exercises the upstream input validation (positive floats, shrinkage range).
            ErlangC(transactions=100, aht=3, asa=0.5, interval=30, shrinkage=0.0)
            return True
        except Exception:
            return False

    def forecast(self, data: list[Any], **kwargs) -> AdapterResult:
        """Not supported - forecasting is delegated to the StatsForecast adapter."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="forecast",
            success=False,
            data=None,
            error_message="Forecasting is not provided by pyworkforce; use the StatsForecast adapter.",
        )

    def staff(self, data: list[Any], **kwargs) -> AdapterResult:
        """
        Compute required positions using pyworkforce Erlang C.

        Unlike the earlier generated version, this adapter never invents an
        arrival rate from timestamp metadata. The caller must supply explicit
        business inputs in the kwargs (or via adapter configuration):

          transactions : int/float  - total transactions arriving in the interval (REQUIRED)
          aht          : float      - average handling time in MINUTES (REQUIRED)
          asa          : float      - required average speed of answer in MINUTES (REQUIRED)
          interval     : int        - interval length in MINUTES (REQUIRED)
          shrinkage    : float      - in [0, 1), default from config (0.0)
          service_level: float      - in [0, 1], default 0.80
          max_occupancy: float      - in (0, 1], default 0.85

        The `data` argument is accepted for interface compatibility but is not
        used to fabricate demand. Returns an explicit error if any required
        business input is missing.
        """
        try:
            if not has_pyworkforce:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="staff",
                    success=False,
                    data=None,
                    error_message="pyworkforce is not installed",
                )

            # Required explicit business inputs (no invention).
            transactions = kwargs.get("transactions")
            aht = kwargs.get("aht")
            asa = kwargs.get("asa")
            interval = kwargs.get("interval")

            missing = [
                name
                for name, val in (
                    ("transactions", transactions),
                    ("aht", aht),
                    ("asa", asa),
                    ("interval", interval),
                )
                if val is None
            ]
            if missing:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="staff",
                    success=False,
                    data=None,
                    error_message=(
                        "staff() requires explicit business inputs: "
                        + ", ".join(missing)
                        + ". The adapter does not infer demand from data."
                    ),
                )

            # Convert seconds->minutes for aht/asa if the caller supplied seconds,
            # matching the upstream API which expects minutes. Callers may also
            # pass minutes directly; we treat the value as the unit the caller
            # documents. Here we require minutes to match pyworkforce exactly.
            shrinkage = kwargs.get(
                "shrinkage", self.config.configuration_options.get("shrinkage", 0.0)
            )
            service_level = kwargs.get(
                "service_level", self.config.configuration_options.get("service_level", 0.80)
            )
            max_occupancy = kwargs.get(
                "max_occupancy", self.config.configuration_options.get("max_occupancy", 0.85)
            )

            erlang = ErlangC(
                transactions=float(transactions),
                aht=float(aht),
                asa=float(asa),
                interval=int(interval),
                shrinkage=float(shrinkage),
            )
            result = erlang.required_positions(
                service_level=float(service_level),
                max_occupancy=float(max_occupancy),
            )

            staffing_result = StaffingResult(
                algorithm="erlang_c",
                allocations={"period_0": [result["positions"]]},
                metrics={
                    "raw_positions": float(result["raw_positions"]),
                    "positions": float(result["positions"]),
                    "service_level": float(result["service_level"]),
                    "occupancy": float(result["occupancy"]),
                    "waiting_probability": float(result["waiting_probability"]),
                },
                metadata={
                    "provider": "pyworkforce",
                    "pyworkforce_method": "ErlangC.required_positions",
                    "units": {
                        "transactions": "transactions per interval",
                        "aht": "minutes",
                        "asa": "minutes",
                        "interval": "minutes",
                        "shrinkage": "proportion [0, 1)",
                        "service_level": "proportion [0, 1]",
                        "max_occupancy": "proportion (0, 1]",
                    },
                    "inputs": {
                        "transactions": float(transactions),
                        "aht": float(aht),
                        "asa": float(asa),
                        "interval": int(interval),
                        "service_level": float(service_level),
                        "max_occupancy": float(max_occupancy),
                        "shrinkage": float(shrinkage),
                    },
                },
            )

            self.last_staffing_result = staffing_result
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="staff",
                success=True,
                data=staffing_result,
                metadata={
                    "provider": "pyworkforce",
                    "method": "ErlangC.required_positions",
                },
            )

        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="staff",
                success=False,
                data=None,
                error_message=str(e),
            )

    def schedule(self, data: list[Any], **kwargs) -> AdapterResult:
        """
        Scheduling is not implemented. pyworkforce does provide rostering
        solvers (e.g. MinHoursRoster), but wiring one is out of scope for this
        stage. This returns an explicit unsupported result rather than a fake
        roster.
        """
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="schedule",
            success=False,
            data=None,
            error_message=(
                "Scheduling is not implemented in this stage. "
                "pyworkforce rostering solvers are not yet wired up; scheduling is deferred."
            ),
        )

    def optimize(self, data: list[Any], **kwargs) -> AdapterResult:
        """Not supported - optimization is not wired in this stage."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="optimize",
            success=False,
            data=None,
            error_message="Optimization is not implemented in this stage.",
        )

    def validate(self, data: list[Any], **kwargs) -> AdapterResult:
        """Not supported here - data validation is delegated to the Pandera adapter."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="validate",
            success=False,
            data=None,
            error_message="Data validation is delegated to the Pandera adapter.",
        )
