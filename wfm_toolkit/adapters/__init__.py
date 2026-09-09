"""Provider adapters for Workforce Management Toolkit.

Each adapter is a thin wrapper around a third-party library. Only the
operations that a provider genuinely performs are executable; all other
BaseAdapter methods return an explicit unsupported result.

The adapters are loaded lazily: importing the toolkit does not require any
optional provider package to be installed. Accessing an adapter whose provider
is missing raises a clear ImportError explaining how to install it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type-checking only
    from .pandera_adapter import PanderaAdapter
    from .pyworkforce_adapter import PyworkforceAdapter
    from .statsforecast_adapter import StatsForecastAdapter

__all__ = [
    "StatsForecastAdapter",
    "PyworkforceAdapter",
    "PanderaAdapter",
]


def __getattr__(name: str):
    """Lazily import an adapter module when the class name is accessed."""
    if name == "StatsForecastAdapter":
        from .statsforecast_adapter import StatsForecastAdapter

        return StatsForecastAdapter
    if name == "PyworkforceAdapter":
        from .pyworkforce_adapter import PyworkforceAdapter

        return PyworkforceAdapter
    if name == "PanderaAdapter":
        from .pandera_adapter import PanderaAdapter

        return PanderaAdapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
