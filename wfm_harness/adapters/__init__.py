"""
Adapters for Workforce Management Harness.

Adapters provide thin wrappers around third-party libraries:
- StatsForecastAdapter - forecasting
- PyworkforceAdapter - staffing and scheduling
- PanderaAdapter - validation
- ORToolsAdapter - constraint solving and shift scheduling
"""

try:
    from .statsforecast_adapter import StatsForecastAdapter
except ImportError:
    StatsForecastAdapter = None

try:
    from .pyworkforce_adapter import PyworkforceAdapter
except ImportError:
    PyworkforceAdapter = None

try:
    from .pandera_adapter import PanderaAdapter
except ImportError:
    PanderaAdapter = None

try:
    from .ortools_adapter import ORToolsAdapter
except ImportError:
    ORToolsAdapter = None