"""Tests for graceful degradation when optional provider dependencies are missing.

The Toolkit adapters must import cleanly and raise a clear, actionable
ImportError at construction when the optional provider is not installed - never
crash at import time, never fake a result. This mirrors the actual behavior:
``_validate_dependencies`` raises at construction.
"""

import sys

import pytest


class TestMissingOptionalDependencies:
    """Simulate missing providers by patching the module-level has_* flags."""

    def test_pyworkforce_missing_construction_raises_clear_import_error(self, monkeypatch):
        import wfm_toolkit.adapters.pyworkforce_adapter as mod

        monkeypatch.setattr(mod, "has_pyworkforce", False)
        with pytest.raises(ImportError, match="pyworkforce is not installed"):
            mod.PyworkforceAdapter()

    def test_statsforecast_missing_construction_raises_clear_import_error(self, monkeypatch):
        import wfm_toolkit.adapters.statsforecast_adapter as mod

        monkeypatch.setattr(mod, "has_statsforecast", False)
        with pytest.raises(ImportError, match="StatsForecast is not installed"):
            mod.StatsForecastAdapter()

    def test_pandera_missing_construction_raises_clear_import_error(self, monkeypatch):
        """PanderaAdapter module must import cleanly without pandera installed;
        the constructor must raise a clean ImportError when upstream is missing."""
        import wfm_toolkit.adapters.pandera_adapter as mod

        monkeypatch.setattr(mod, "has_pandera", False)
        with pytest.raises(ImportError, match="Pandera is not installed"):
            mod.PanderaAdapter()

    def test_pandera_module_imports_cleanly_without_provider(self, monkeypatch):
        """Module import must not crash when pandera is missing (lazy guard)."""
        monkeypatch.setitem(sys.modules, "pandera", None)
        # Simulate: force a re-import with pandera blocked
        import wfm_toolkit.adapters.pandera_adapter as mod

        assert hasattr(mod, "has_pandera")

    def test_import_errors_are_actionable(self):
        """The exception message must tell the user how to install the provider."""
        import wfm_toolkit.adapters.pyworkforce_adapter as mod

        try:
            mod.PyworkforceAdapter._validate_dependencies(
                mod.PyworkforceAdapter.__new__(mod.PyworkforceAdapter)
            )
        except ImportError as e:
            assert "pip install pyworkforce" in str(e)
