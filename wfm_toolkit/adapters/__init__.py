"""Provider adapters for Workforce Management Toolkit.

Each adapter is a thin wrapper around a third-party library. Only the
operations that a provider genuinely performs are executable; all other
BaseAdapter methods return an explicit unsupported result.
"""

from .pandera_adapter import PanderaAdapter
from .pyworkforce_adapter import PyworkforceAdapter
from .statsforecast_adapter import StatsForecastAdapter

# OR-Tools is deferred in this stage; the adapter class is exported for
# completeness but is not part of the executable core.
try:
    from .ortools_adapter import ORToolsAdapter
except ImportError:
    ORToolsAdapter = None

__all__ = [
    "StatsForecastAdapter",
    "PyworkforceAdapter",
    "PanderaAdapter",
    "ORToolsAdapter",
]
