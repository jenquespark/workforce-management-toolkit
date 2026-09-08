"""Tests for ORToolsAdapter - deferred status.

OR-Tools scheduling/optimization is REGISTERED but NOT part of the executable
core in this stage. The adapter class exists and exposes the full BaseAdapter
surface, but optimize()/schedule() are not verified working against the
installed ortools API. This test verifies the DEFERRED semantics only.
"""

from wfm_toolkit.adapters.ortools_adapter import ORToolsAdapter


class TestORToolsAdapter:
    """Tests reflecting the deferred OR-Tools status."""

    def test_instantiation(self):
        """Adapter can be instantiated (ortools importable in this env)."""
        adapter = ORToolsAdapter()
        assert adapter is not None
        assert adapter.config.provider_name == "OR-Tools"

    def test_health_check_reflects_install(self):
        adapter = ORToolsAdapter()
        try:
            import ortools  # noqa: F401

            assert adapter.health_check() is True
        except ImportError:
            assert adapter.health_check() is False

    def test_forecast_not_supported(self):
        adapter = ORToolsAdapter()
        r = adapter.forecast([])
        assert r.success is False
        assert "Not supported" in r.error_message

    def test_staff_not_supported(self):
        adapter = ORToolsAdapter()
        r = adapter.staff([])
        assert r.success is False
        assert "Not supported" in r.error_message

    def test_validate_not_supported(self):
        adapter = ORToolsAdapter()
        r = adapter.validate([])
        assert r.success is False
        assert "Not supported" in r.error_message

    def test_registry_marks_scheduling_planned(self):
        """schedule.generate must be PLANNED, not implemented, in this stage."""
        from wfm_toolkit.capability_registry import CapabilityRegistry

        registry = CapabilityRegistry()
        cap = registry.get_capability("schedule.generate")
        assert cap is not None
        assert not cap.is_executable()  # planned, not executable
