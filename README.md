# Workforce Management Toolkit

A thin Python library that puts consistent interfaces around existing Workforce Management tooling — forecasting, staffing, and validation — so that these capabilities can be discovered, called, and composed without reimplementing the underlying mathematics.

## Why this exists

WFM engineering typically involves multiple specialized libraries for different problems: one for forecasting, another for Erlang C staffing, another for data validation, and so on. Each has its own API, data format, units, and error behavior. Teams end up writing custom glue code to connect them.

Workforce Management Toolkit wraps those libraries behind a common adapter interface. The goal is not to replace them but to provide a stable, discoverable layer that:

- Normalizes input and output structures across providers
- Makes capabilities machine-readable (useful for automation and language models)
- Documents units and parameter expectations explicitly
- Reports provider availability honestly

The Toolkit does not contain forecasting algorithms, Erlang formulas, or optimization solvers. It calls the libraries that do.

## Current providers

Three providers are implemented and tested in v0.1.0:

| Capability | Provider | What it does | License |
|---|---|---|---|
| Forecasting | [StatsForecast](https://github.com/Nixtla/statsforecast) | Time series forecasting (AutoARIMA, AutoETS, SeasonalNaive) | Apache-2.0 |
| Staffing | [pyworkforce](https://github.com/inside_outside/pyworkforce) | Erlang C staffing calculations for voice queues | MIT |
| Validation | [Pandera](https://github.com/pandera-dev/pandera) | Schema validation for WFM datasets | MIT |

Each adapter implements `forecast()`, `staff()`, `schedule()`, `optimize()`, and `validate()` methods. Operations outside the provider's domain return a structured error (e.g., calling `staff()` on the StatsForecast adapter returns an error indicating staffing requires pyworkforce).

## What the Toolkit owns

- Common adapter interface (`BaseAdapter`)
- Canonical data structure (`WFMData`)
- Capability registry with machine-readable descriptions
- Provider availability detection
- Input/output normalization
- Configuration with Pydantic V2 validation

## What it does not own

- Forecast algorithms
- Erlang C formulas
- Schema validation internals
- Any optimization or scheduling logic (planned, not implemented)
- BI platforms, dashboards, or data stores
- LLM inference or prompting

## Installation

```bash
pip install workforce-management-harness
```

Provider dependencies are optional extras:

```bash
pip install workforce-management-harness[forecast]   # adds statsforecast, numpy, pandas
pip install workforce-management-harness[staffing]   # adds pyworkforce
pip install workforce-management-harness[validation] # adds pandera
pip install workforce-management-harness[full]       # all three
```

## Quick start

```python
from wfm_harness.adapters.statsforecast_adapter import StatsForecastAdapter
from wfm_harness.adapters.pyworkforce_adapter import PyworkforceAdapter
from wfm_harness.adapters.pandera_adapter import PanderaAdapter
from wfm_harness.domain import WFMData
from datetime import datetime

# Forecasting
sf = StatsForecastAdapter()
data = [WFMData(timestamp=datetime(2024, 1, i, 0, 0), value=100 + i*5) for i in range(30)]
result = sf.forecast(data, forecast_horizon=7, model="AutoARIMA")

# Staffing
pw = PyworkforceAdapter()
result = pw.staff(data, service_level=0.80, average_speed_of_answer=20)

# Validation
pa = PanderaAdapter()
result = pa.validate(data)
```

The `WFMCLI` class provides a higher-level interface for `doctor()`, `capabilities()`, and `validate()`:

```python
from wfm_harness.cli import WFMCLI

cli = WFMCLI()
print(cli.doctor())      # provider availability check
print(cli.capabilities()) # registered capabilities
```

**Note:** A `wfm-harness` console script is planned but not yet registered — the Click commands are not wired up in v0.1.0. The Python API is the interface.

## Capability discovery

The capability registry provides machine-readable descriptions of available operations:

```python
from wfm_harness.capability_registry import CapabilityRegistry

registry = CapabilityRegistry()
for cap in registry.list_capabilities():
    print(cap.identifier, cap.provider.name, cap.deterministic)
```

Each capability describes its required inputs, outputs, provider, and whether it requires an LLM. This is designed for automation and for language models that need to discover what operations are available without hardcoding that knowledge.

## Configuration

Configuration uses Pydantic V2. Key parameters with their actual units:

| Parameter | Type | Default | Units |
|---|---|---|---|
| `timezone` | str | "UTC" | IANA timezone |
| `average_speed_of_answer` | float | required | seconds |
| `average_handle_time` | float | required | seconds |
| `target` (occupancy) | float | required | proportion (0.0–1.0) |
| `shrinkage_rate` | float | configurable | proportion (0.0–1.0) |

**Common mistake:** Service level and shrinkage are proportions (0.0–1.0), not percentages. `0.80` means 80%, not `80`. See [docs/configuration.md](docs/configuration.md) for the full configuration reference.

## Project status

**v0.1.0 — Early stage, functional core.**

Working:
- Forecasting via StatsForecast (AutoARIMA, AutoETS, SeasonalNaive)
- Staffing via pyworkforce (Erlang C)
- Validation via Pandera (schema enforcement)
- Capability registry
- Python API (WFMCLI class, adapter classes)
- Configuration with validation
- Unit and integration tests

Not yet working:
- Click-based CLI (entry point exists, commands not wired)
- OR-Tools integration (adapter exists but is deferred)
- Scheduling and optimization (planned)
- Capacity planning (planned)
- End-to-end pipeline composition
- Multi-skill staffing
- Intraday management
- BI integration patterns

The API surface may change. The architecture is stable but incomplete.

## Roadmap

**Near-term:**
- Click CLI commands wired up
- Forecast accuracy evaluation (MAPE, MAE, RMSE)
- Multi-provider forecast comparison

**Medium-term:**
- OR-Tools integration finalized
- Multi-skill staffing
- Scheduling and optimization capabilities
- Pipeline composition API

**Longer-term:**
- Intraday management
- Chat/async workload modeling
- Capacity planning
- BI integration patterns
- MCP/tool protocol support

## Architecture

```
Consumer (Python / Agent / Script)
        │
        ▼
┌──────────────────────────┐
│  Workforce Management    │
│  Toolkit                 │
│                          │
│  Capability Registry     │
│  BaseAdapter Interface   │
│  Configuration (Pydantic)│
│                          │
│  ┌──────┬──────┬──────┐  │
│  │Stats │pywork│Pandera│  │
│  │Fore- │force │      │  │
│  │cast  │      │      │  │
│  └──┬───┴──┬───┴──┬───┘  │
└─────┼──────┼──────┼──────┘
      │      │      │
      ▼      ▼      ▼
  StatsFore- pywork- Pandera
  cast       force   (external
  (external) (external) packages)
```

## Engineering decisions

**Thin adapters, not reimplementations.** The Toolkit wraps existing libraries rather than rewriting Erlang C or ARIMA. This keeps the code small and the math correct.

**Optional extras.** Each provider is independently installable. You don't need StatsForecast if you only want staffing.

**No LLM requirement.** The Toolkit works entirely without language models. If a model is used, it handles intent and parameter gathering; the provider handles the calculation.

**Explicit units.** WFM tools frequently fail because units are ambiguous. The configuration documents and validates units for every parameter.

## Contributing

Contributions make sense for:
- Additional provider adapters
- Tests for edge cases
- Documentation of WFM domain concepts
- Bug reports with reproducible examples

This is a small project with a specific scope. Contributions should stay within it.

## License

Apache-2.0. See [LICENSE](./LICENSE) for the full text and [THIRD_PARTY.md](./THIRD_PARTY.md) for provider licenses.
