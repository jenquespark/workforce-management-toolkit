"""
Pyworkforce adapter for Workforce Management Toolkit.

Adapter around the pyworkforce library for Erlang C staffing calculations.

The pyworkforce ErlangC API takes explicit business inputs - it never invents
contact demand. All staffing parameters (transactions, average handling time,
target answer speed, interval duration, shrinkage, occupancy) must be supplied
by the caller; the adapter only converts and delegates to pyworkforce.

Units (matching the current upstream pyworkforce API):

  transactions : total number of transactions arriving in the interval (float)
  aht          : average handling time of a transaction, in MINUTES (float)
  asa          : required average speed of answer, in MINUTES (float)
  interval     : interval length, in MINUTES (int)
  shrinkage    : fraction of time an operator is not available, in [0, 1) (float)
  service_level: target service level, in [0, 1] (float)
  max_occupancy: max fraction of time a transaction occupies a position, (0, 1] (float)
"""

from __future__ import annotations

from typing import Any

try:
    from pyworkforce import ErlangC

    has_pyworkforce = True
except ImportError:  # pragma: no cover - depends on optional install
    has_pyworkforce = False

from ..domain import StaffingRequest, StaffingResult
from .base import AdapterConfig, AdapterResult, BaseAdapter


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

    def forecast(self, data: Any, **kwargs) -> AdapterResult:
        """Not supported - forecasting is delegated to the StatsForecast adapter."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="forecast",
            success=False,
            data=None,
            error_message="Forecasting is not provided by pyworkforce; use the StatsForecast adapter.",
        )

    def staff(
        self, data: Any = None, *, request: StaffingRequest | None = None, **kwargs
    ) -> AdapterResult:
        """
        Compute required positions using pyworkforce Erlang C.

        This adapter never invents contact demand. The caller must supply an
        explicit :class:`StaffingRequest` (recommended) or the equivalent
        keyword arguments:

          transactions : float - total transactions arriving in the interval (REQUIRED)
          aht          : float - average handling time in MINUTES (REQUIRED)
          asa          : float - required average speed of answer in MINUTES (REQUIRED)
          interval_min : int   - interval length in MINUTES (REQUIRED)
          service_level: float - target service level in [0, 1], default 0.80
          max_occupancy: float - max occupancy fraction in (0, 1], default 0.85
          shrinkage    : float - shrinkage fraction in [0, 1), default 0.0

        The ``data`` argument is accepted for BaseAdapter interface
        compatibility but is never used to fabricate demand. Returns an
        explicit error AdapterResult if any required business input is missing.
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

            if request is None:
                # Build from explicit kwargs (all required).
                # Accept both short names (aht, asa) and _min-suffixed names (aht_min, asa_min).
                resolved = dict(kwargs)
                if "aht_min" in resolved and "aht" not in resolved:
                    resolved["aht"] = resolved.pop("aht_min")
                if "asa_min" in resolved and "asa" not in resolved:
                    resolved["asa"] = resolved.pop("asa_min")
                missing = [
                    name
                    for name in ("transactions", "aht", "asa", "interval_min")
                    if resolved.get(name) is None
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
                            + ". The adapter does not infer demand from data; pass a StaffingRequest."
                        ),
                    )
                request = StaffingRequest(
                    transactions=float(resolved["transactions"]),
                    aht=float(resolved["aht"]),
                    asa=float(resolved["asa"]),
                    interval_min=int(resolved["interval_min"]),
                    service_level=float(
                        resolved.get(
                            "service_level",
                            self.config.configuration_options.get("service_level", 0.80),
                        )
                    ),
                    max_occupancy=float(
                        resolved.get(
                            "max_occupancy",
                            self.config.configuration_options.get("max_occupancy", 0.85),
                        )
                    ),
                    shrinkage=float(
                        resolved.get(
                            "shrinkage", self.config.configuration_options.get("shrinkage", 0.0)
                        )
                    ),
                )

            erlang = ErlangC(
                transactions=request.transactions,
                aht=request.aht,
                asa=request.asa,
                interval=int(request.interval_min),
                shrinkage=request.shrinkage,
            )
            result = erlang.required_positions(
                service_level=request.service_level,
                max_occupancy=request.max_occupancy,
            )

            staffing_result = StaffingResult(
                algorithm="erlang_c",
                raw_positions=int(result["raw_positions"]),
                positions=int(result["positions"]),
                service_level=float(result["service_level"]),
                occupancy=float(result["occupancy"]),
                waiting_probability=float(result["waiting_probability"]),
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
                        "transactions": float(request.transactions),
                        "aht": float(request.aht),
                        "asa": float(request.asa),
                        "interval_min": int(request.interval_min),
                        "service_level": float(request.service_level),
                        "max_occupancy": float(request.max_occupancy),
                        "shrinkage": float(request.shrinkage),
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
                error_message=f"staff() failed: {e}",
            )

    def schedule(self, data: Any, **kwargs) -> AdapterResult:
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

    def optimize(self, data: Any, **kwargs) -> AdapterResult:
        """Not supported - optimization is not wired in this stage."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="optimize",
            success=False,
            data=None,
            error_message="Optimization is not implemented in this stage.",
        )

    def validate(self, data: Any, **kwargs) -> AdapterResult:
        """Not supported here - data validation is delegated to the Pandera adapter."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="validate",
            success=False,
            data=None,
            error_message="Data validation is delegated to the Pandera adapter.",
        )
