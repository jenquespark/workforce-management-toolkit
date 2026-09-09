"""Tests for the capability registry - executable vs planned status.

The v0.1 release executable surface must be exactly the three real provider
capabilities; everything else stays registered metadata (planned).
"""

from wfm_toolkit.capability_registry import (
    CapabilityRegistry,
    CapabilityStatus,
)


class TestCapabilityRegistry:
    """Validate the capability registry's honest status model."""

    def setup_method(self):
        self.registry = CapabilityRegistry()

    def test_executable_capabilities_exactly_three(self):
        executable = {c.identifier for c in self.registry.executable_capabilities()}
        assert executable == {
            "forecast.generate",
            "staffing.erlang_c",
            "validate.dataset",
        }

    def test_registered_capabilities_include_planned(self):
        ids = set(self.registry.capabilities.keys())
        assert "forecast.evaluate" in ids
        assert "staffing.multiskill" in ids
        assert "schedule.generate" in ids
        assert "validate.wfm_config" in ids
        assert "capacity.forecast" in ids
        # All non-executable capabilities are PLANNED (not fake-implemented)
        for ident, cap in self.registry.capabilities.items():
            if ident not in {
                "forecast.generate",
                "staffing.erlang_c",
                "validate.dataset",
            }:
                assert cap.status == CapabilityStatus.PLANNED

    def test_is_executable_only_implemented(self):
        for ident, cap in self.registry.capabilities.items():
            expected = ident in {
                "forecast.generate",
                "staffing.erlang_c",
                "validate.dataset",
            }
            assert cap.is_executable() is expected

    def test_export_json_roundtrip(self):
        exported = self.registry.export_capabilities("json")
        assert '"forecast.generate"' in exported
        # Round-trip import into a fresh registry
        fresh = CapabilityRegistry()
        fresh.import_capabilities(exported, "json")
        assert set(fresh.capabilities.keys()) == set(self.registry.capabilities.keys())

    def test_list_filters_by_status(self):
        planned = self.registry.list_capabilities(status=CapabilityStatus.PLANNED)
        assert all(c.status == CapabilityStatus.PLANNED for c in planned)
        implemented = self.registry.list_capabilities(status=CapabilityStatus.IMPLEMENTED)
        assert len(implemented) == 3

    def test_capability_dict_status_is_string(self):
        cap = self.registry.get_capability("forecast.generate")
        d = cap.to_dict()
        assert d["status"] == "implemented"
        assert d["provider"]["name"] == "StatsForecast"
        assert d["provider"]["license"] == "Apache-2.0"
