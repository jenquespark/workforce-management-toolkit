"""
Command-line interface for Workforce Management Toolkit.

Provides a small, honest ``wfm-toolkit`` CLI:

  wfm-toolkit doctor        - report installed provider packages + executable capabilities
  wfm-toolkit capabilities  - list registered capability metadata (JSON)
  wfm-toolkit validate      - validate a WFM dataset file (CSV/JSON) against the canonical schema

Only operations that genuinely run against the real adapters/registry are
exposed. There is intentionally no ``forecast``/``staff`` command: those are
Python-API operations with explicit business-input contracts, not stubbed CLI
workflows. No fake workflows or fabricated results.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import click

from .capability_registry import CapabilityRegistry
from .domain import WFMData
from .version import __version__


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
            "timestamp": datetime.now(UTC).isoformat(),
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
            "version": __version__,
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
                {"valid": result.success},
                result.success,
                [result.error_message] if result.error_message else [],
                {"command": "validate", "provider": "pandera"},
            )
        except Exception as e:  # pragma: no cover - depends on installed provider
            return self._output_json(None, False, errors=[str(e)], metadata={"command": "validate"})


@click.group()
@click.version_option(__version__, prog_name="wfm-toolkit")
def main() -> None:
    """Workforce Management Toolkit CLI.

    A small, honest interface over the Toolkit's executable capabilities.
    """


@main.command()
def doctor() -> None:
    """Report installed provider packages and executable capabilities."""
    click.echo(WFMCLI().doctor())


@main.command("capabilities")
@click.option("--format", "fmt", default="json", show_default=True, type=click.Choice(["json"]))
@click.option("--examples/--no-examples", default=False, show_default=True)
def capabilities_cmd(fmt: str, examples: bool) -> None:
    """List registered capabilities with executable/planned status."""
    click.echo(WFMCLI().capabilities(format=fmt, examples=examples))


def _load_dataset(path: str) -> list[WFMData]:
    """Load a dataset from a CSV (timestamp,value) or JSON file of WFMData dicts."""
    if path.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        raw_items = payload if isinstance(payload, list) else payload.get("data", [])
        return [WFMData.from_dict(item) for item in raw_items]
    # CSV: expect header timestamp,value
    import csv

    records = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            records.append(
                WFMData(
                    timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                    value=float(row["value"]),
                    metadata={},
                )
            )
    return records


@main.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def validate(path: str) -> None:
    """Validate a WFM dataset file (CSV or JSON) against the canonical schema."""
    try:
        data = _load_dataset(path)
    except Exception as e:
        click.echo(
            json.dumps({"success": False, "errors": [f"Failed to load dataset: {e}"]}, indent=2)
        )
        raise SystemExit(2)

    out = WFMCLI().validate_config(data)
    click.echo(out)
    parsed = json.loads(out)
    if not parsed["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
