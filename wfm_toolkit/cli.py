"""
Command-line interface for Workforce Management Toolkit.

NOTE: There is no wired Click console script in this stage. The Python API is
the primary interface. This module provides a small WFMCLI class with only the
operations that genuinely work (health check, capability listing, and
configuration loading). It does not fabricate forecasting, staffing, or
scheduling results, and no `wfm-toolkit` subcommands are registered until a
real CLI is implemented and tested.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .capability_registry import CapabilityRegistry
from .domain import WFMData


class WFMCLI:
    """Programmatic helpers with no fabricated workflow execution.

    Only operations that actually run against the current adapters/registry
    are exposed. There is intentionally no `forecast`/`staff`/`schedule`
    command here: those are Python-API operations delegated to the real
    providers, not stubbed CLI workflows.
    """

    def __init__(self):
        self.capability_registry = CapabilityRegistry()

    def _output_json(
        self,
        data: Any,
        success: bool = True,
        errors: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Output a standardized JSON response."""
        if errors is None:
            errors = []
        if metadata is None:
            metadata = {}

        response = {
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "errors": errors,
            "metadata": metadata,
        }

        return json.dumps(response, indent=2, default=str)

    def doctor(self) -> str:
        """Report which provider packages are importable and which capabilities
        are executable. This only reflects the current environment; it does not
        run any WFM calculation."""
        executable = [c.identifier for c in self.capability_registry.executable_capabilities()]
        registered = sorted(self.capability_registry.capabilities.keys())

        deps = {}
        for pkg in ("statsforecast", "pyworkforce", "pandera"):
            try:
                __import__(pkg)
                deps[pkg] = "installed"
            except ImportError:
                deps[pkg] = "missing"

        health_info = {
            "version": "0.1.0",
            "provider_packages": deps,
            "executable_capabilities": executable,
            "registered_capabilities": registered,
        }
        return self._output_json(health_info, True, [], {"command": "doctor"})

    def capabilities(self, format: str = "json", examples: bool = False) -> str:
        """List all registered capabilities, separating executable from
        registered/planned status."""
        capabilities_data = [c.to_dict() for c in self.capability_registry.capabilities.values()]
        result_data = {
            "capabilities": capabilities_data,
            "count": len(capabilities_data),
            "metadata": {"command": "capabilities", "format": format, "examples": examples},
        }
        return self._output_json(result_data, True, [], {})

    def validate_config(self, data: list[WFMData]) -> str:
        """Validate a list of WFMData using the Pandera adapter (executable).
        Returns an unsupported result if Pandera is not installed."""
        from .adapters.pandera_adapter import PanderaAdapter

        try:
            adapter = PanderaAdapter()
            result = adapter.validate(data)
            return self._output_json(
                {"valid": result.success, "result": result},
                result.success,
                [result.error_message] if result.error_message else [],
                {"command": "validate", "provider": "pandera"},
            )
        except Exception as e:  # pragma: no cover - depends on installed provider
            return self._output_json(None, False, errors=[str(e)], metadata={"command": "validate"})
