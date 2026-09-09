"""Tests for PyworkforceAdapter - verified against the installed pyworkforce
upstream API (v0.5.x). The adapter must NEVER invent an arrival rate from data;
staffing requires explicit business inputs (transactions, aht, asa, interval_min).

Parity: the Toolkit result must match a direct upstream ``ErlangC`` call.
"""

import pytest

pytest.importorskip("pyworkforce", reason="pyworkforce is not installed")

from pyworkforce import ErlangC

from wfm_toolkit.adapters.base import AdapterConfig
from wfm_toolkit.adapters.pyworkforce_adapter import PyworkforceAdapter
from wfm_toolkit.domain import StaffingRequest


@pytest.fixture
def pyworkforce_config() -> AdapterConfig:
    """Standard configuration for PyworkforceAdapter."""
    return AdapterConfig(
        provider_name="Pyworkforce",
        package_name="pyworkforce",
        license="MIT",
        deterministic_level="high",
        required_dependencies=["pyworkforce"],
        optional_dependencies=[],
        configuration_options={
            "service_level": 0.80,
            "max_occupancy": 0.85,
            "shrinkage": 0.30,
        },
    )


class TestPyworkforceAdapter:
    """Test suite for PyworkforceAdapter against the real upstream API."""

    def test_initialization_with_default_config(self):
        adapter = PyworkforceAdapter()
        assert adapter.config.provider_name == "Pyworkforce"
        assert adapter.config.package_name == "pyworkforce"

    def test_initialization_with_custom_config(self, pyworkforce_config):
        adapter = PyworkforceAdapter(pyworkforce_config)
        assert adapter.config == pyworkforce_config

    def test_health_check_reflects_installed_provider(self):
        """health_check must reflect whether pyworkforce is importable."""
        adapter = PyworkforceAdapter()
        try:
            import pyworkforce  # noqa: F401

            assert adapter.health_check() is True
        except ImportError:
            assert adapter.health_check() is False

    # --- staff(): explicit business inputs required, no invented demand ---

    def test_staff_requires_explicit_business_inputs(self):
        """staff() with no business inputs must fail explicitly - never
        silently invent an arrival rate from data."""
        adapter = PyworkforceAdapter()
        result = adapter.staff([])
        assert result.success is False
        assert "transactions" in result.error_message
        assert "does not" in result.error_message  # does not infer demand

    def test_staff_missing_single_required_input(self):
        adapter = PyworkforceAdapter()
        result = adapter.staff([], transactions=100, aht=180, asa=20)
        assert result.success is False
        assert "interval_min" in result.error_message

    def test_staff_success_with_explicit_inputs(self):
        adapter = PyworkforceAdapter()
        result = adapter.staff(
            None,
            transactions=100,
            aht=180,
            asa=20,
            interval_min=60,
            service_level=0.8,
            max_occupancy=0.85,
            shrinkage=0.3,
        )
        assert result.success is True
        assert result.operation == "staff"
        # Delegated to upstream ErlangC.required_positions
        assert result.metadata["method"] == "ErlangC.required_positions"
        # positions is an int >= 0
        assert result.data.allocations
        assert "positions" in result.data.metrics
        assert result.data.metrics["positions"] >= 0

    # --- forecast(): pyworkforce does not forecast ---

    def test_forecast_not_supported(self):
        adapter = PyworkforceAdapter()
        result = adapter.forecast([])
        assert result.success is False
        assert "StatsForecast" in result.error_message

    # --- schedule(): must be explicit unsupported (no fake roster) ---

    def test_schedule_is_explicitly_deferred(self):
        """schedule() must NOT return a fake roster. It must be an explicit
        unsupported result until a real rostering operation is wired."""
        adapter = PyworkforceAdapter()
        result = adapter.schedule(None)
        assert result.success is False
        assert (
            "not implemented" in result.error_message.lower()
            or "deferred" in result.error_message.lower()
        )
        # It must not fabricate an empty-but-plausible roster
        assert result.data is None

    # --- optimize(): not supported ---

    def test_optimize_not_supported(self):
        adapter = PyworkforceAdapter()
        result = adapter.optimize([])
        assert result.success is False
        assert "not implemented" in result.error_message.lower()

    # --- provider info ---

    def test_get_provider_info(self, pyworkforce_config):
        adapter = PyworkforceAdapter(pyworkforce_config)
        info = adapter.get_provider_info()
        assert info["name"] == "Pyworkforce"
        assert info["license"] == "MIT"

    def test_execute_operation_routing(self):
        adapter = PyworkforceAdapter()
        result = adapter.execute_operation("unknown", [])
        assert result.success is False
        assert "Unknown operation" in result.error_message

    # --- StaffingRequest typed request + parity with direct upstream ---

    def test_staff_with_typed_request_parity(self):
        """Toolkit result must equal a direct upstream ErlangC call."""
        adapter = PyworkforceAdapter()
        request = StaffingRequest(
            transactions=100,
            aht=3.0,
            asa=0.5,
            interval_min=30,
            service_level=0.8,
            max_occupancy=0.85,
            shrinkage=0.3,
        )
        result = adapter.staff(request=request)
        assert result.success is True
        # Direct upstream call
        erlang = ErlangC(transactions=100, aht=3.0, asa=0.5, interval=30, shrinkage=0.3)
        direct = erlang.required_positions(service_level=0.8, max_occupancy=0.85)
        assert result.data.positions == direct["positions"]
        assert result.data.raw_positions == direct["raw_positions"]
        assert result.data.service_level == direct["service_level"]
        assert result.data.occupancy == direct["occupancy"]
        assert result.data.waiting_probability == direct["waiting_probability"]

    def test_staff_kwargs_parity(self):
        """kwargs form must produce the same result as the typed request."""
        adapter = PyworkforceAdapter()
        result = adapter.staff(
            transactions=200,
            aht=2.5,
            asa=20 / 60,
            interval_min=30,
            service_level=0.85,
            max_occupancy=0.8,
            shrinkage=0.25,
        )
        assert result.success is True
        erlang = ErlangC(transactions=200, aht=2.5, asa=20 / 60, interval=30, shrinkage=0.25)
        direct = erlang.required_positions(service_level=0.85, max_occupancy=0.8)
        assert result.data.positions == direct["positions"]
        # Metrics view is consistent
        assert result.data.metrics["positions"] == float(direct["positions"])
