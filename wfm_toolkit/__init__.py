"""Workforce Management Toolkit - a thin, vendor-neutral Python library for
Workforce Management forecasting, staffing, and data-validation tooling.

The internal import package is ``wfm_toolkit`` (the public project name is
``workforce-management-toolkit``).
"""

from .adapters import (
    PanderaAdapter,
    PyworkforceAdapter,
    StatsForecastAdapter,
)
from .capability_registry import CapabilityRegistry
from .config import WFMConfig
from .domain import WFMData
from .version import __version__

__all__ = [
    "__version__",
    "WFMData",
    "WFMConfig",
    "CapabilityRegistry",
    "StatsForecastAdapter",
    "PyworkforceAdapter",
    "PanderaAdapter",
]
