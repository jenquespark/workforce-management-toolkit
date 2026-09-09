"""Workforce Management Toolkit - a thin, vendor-neutral Python library for
Workforce Management forecasting, staffing, and data-validation tooling.

The internal import package is ``wfm_toolkit`` (the public project name is
``workforce-management-toolkit``). Importing the package does not require any
optional provider (statsforecast, pyworkforce, pandera) to be installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .capability_registry import CapabilityRegistry
from .config import WFMConfig
from .domain import StaffingRequest, StaffingResult, WFMData
from .version import __version__

if TYPE_CHECKING:  # pragma: no cover - type-checking only
    from .adapters import PanderaAdapter, PyworkforceAdapter, StatsForecastAdapter

__all__ = [
    "__version__",
    "WFMData",
    "StaffingRequest",
    "StaffingResult",
    "WFMConfig",
    "CapabilityRegistry",
    "StatsForecastAdapter",
    "PyworkforceAdapter",
    "PanderaAdapter",
]


def __getattr__(name: str):
    """Lazily resolve adapter classes (and other deferred exports)."""
    if name in ("StatsForecastAdapter", "PyworkforceAdapter", "PanderaAdapter"):
        from . import adapters

        return getattr(adapters, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
