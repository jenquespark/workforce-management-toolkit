# Workforce Management Toolkit

A small Python library that provides consistent, WFM-oriented interfaces over selected open-source libraries — forecasting, staffing, and data validation — so these capabilities can be discovered, called, and composed without reimplementing the underlying mathematics.

The Toolkit wraps existing libraries (StatsForecast, pyworkforce, Pandera) behind a common adapter interface. It does not contain forecasting algorithms, Erlang formulas, or optimization solvers; it calls the libraries that do.

## Why this exists

Workforce Management engineering is fragmented. Forecasting, staffing/queueing, validation, optimization, scheduling, and BI/operational systems each have their own libraries, APIs, data formats, units, and error behavior. Teams repeatedly write glue code to connect them.

This Toolkit normalizes part of that glue. It provides a stable, discoverable layer that:

- exposes a shared adapter interface (`BaseAdapter`)
- normalizes input/output across providers
- documents units and parameter expectations explicitly
- reports provider availability honestly
- makes capabilities machine-readable via the registry

It is not a complete WFM platform. It is a thin normalization layer over a small set of open-source calculations.

## Current capabilities

Only three operations are executable in this stage, each delegated to a real provider:

| Capability | Provider | Status | Purpose |
|---|---|---|---|
| `forecast.generate` | StatsForecast | **Implemented** | Statistical time-series forecasting (AutoARIMA, AutoETS, SeasonalNaive) |
| `staffing.erlang_c` | pyworkforce | **Implemented** | Erlang C required positions from explicit contact-volume inputs |
| `validate.dataset` | Pandera | **Implemented** | Schema validation of a WFM dataset |

Everything else in the registry is **registered/planned** — the metadata exists, but there is no executable provider logic yet: `forecast.evaluate`, `staffing.multiskill`, `schedule.generate`, `validate.wfm_config`, `capacity.forecast`, optimization.

The capability registry distinguishes these states explicitly. `Capability.is_executable()` returns `True` only for the three implemented operations.

## What the Toolkit adds

- a shared WFM-oriented adapter interface
- normalized data/contracts (`WFMData`, `AdapterResult`)
- explicit units in adapter metadata and configuration
- provider adapters (thin wrappers, no reimplemented math)
- capability metadata with executable/planned status
- Pydantic v2 configuration models
- provider availability detection (`health_check()`)

## What it does not do

- it is not a complete WFM platform
- it is not a scheduler
- it is not a BI platform
- it is not a forecasting engine (it delegates to StatsForecast)
- it is not an Erlang implementation (it delegates to pyworkforce)
- it is not a SaaS or hosted service
- it is not an LLM runtime
- it is not production-ready

## Providers

### StatsForecast

[StatsForecast](https://github.com/Nixtla/statsforecast) (Apache-2.0) provides statistical time-series forecasting. The Toolkit configures a `StatsForecast` instance with a model and horizon, and executes forecasting through its class-based API. Models supported: `AutoARIMA`, `AutoETS`, `SeasonalNaive`. Forecasts are statistical, provider-executed, and reproducible for a fixed input.

### pyworkforce

[pyworkforce](https://github.com/rodrigo-arenas/pyworkforce) (MIT) provides Erlang C staffing. The Toolkit calls `ErlangC.required_positions()` with explicit business inputs:

- `transactions` — contact volume in the interval
- `aht` — average handling time (minutes)
- `asa` — required average speed of answer (minutes)
- `interval` — interval length (minutes)
- `service_level` — target (proportion, e.g. `0.80`)
- `max_occupancy` — maximum occupancy (proportion)
- `shrinkage` — shrinkage (proportion)

The pyworkforce adapter never invents an arrival rate or contact demand from data. A staffing calculation requires these explicit inputs.

### Pandera

[Pandera](https://github.com/unionai-oss/pandera) (MIT) provides dataframe validation. The Toolkit uses it to validate WFM datasets against a canonical schema. Pandera validates; it does not forecast, staff, schedule, or optimize. Calling those methods returns an explicit unsupported result.

## Installation

The package is **not yet published to PyPI**. There is no `pip install workforce-management-toolkit` that works today.

For development, clone the repository and install with the extras you need:

```bash
git clone https://github.com/jenquespark/workforce-management-toolkit.git
cd workforce-management-toolkit
pip install -e '.[forecast,staffing,validation]'
```

Extras: `forecast` (statsforecast, numpy, pandas), `staffing` (pyworkforce), `validation` (pandera), `full` (all). Scheduling/optimization providers are not part of v0.1.0; see [docs/roadmap.md](docs/roadmap.md).

## Quick start

```python
from datetime import datetime, timedelta
from wfm_toolkit.adapters.statsforecast_adapter import StatsForecastAdapter
from wfm_toolkit.adapters.pyworkforce_adapter import PyworkforceAdapter
from wfm_toolkit.adapters.pandera_adapter import PanderaAdapter
from wfm_toolkit.domain import WFMData

# Forecasting (Statistical, provider-executed)
sf = StatsForecastAdapter()
history = [
    WFMData(timestamp=datetime(2024, 1, 1) + timedelta(days=i), value=100.0 + i * 5)
    for i in range(30)
]
forecast = sf.forecast(history, model="AutoARIMA", forecast_horizon=7, season_length=7, freq="D")
print(forecast.success)  # True when statsforecast is installed

# Staffing (Erlang C, explicit business inputs)
pw = PyworkforceAdapter()
staffing = pw.staff(
    None,
    transactions=100,
    aht=3,
    asa=0.5,
    interval_min=30,
    service_level=0.8,
    max_occupancy=0.85,
    shrinkage=0.3,
)
# staffing.data.metrics["positions"] -> required agents

# Validation (Pandera schema check)
pa = PanderaAdapter()
validation = pa.validate(history)  # value must be float
print(validation.success)  # True when pandera is installed
```

The `WFMCLI` class provides programmatic helpers without fabricating results, and the `wfm-toolkit` console script exposes the same commands:

```bash
wfm-toolkit --help
wfm-toolkit doctor          # provider availability + executable capabilities
wfm-toolkit capabilities    # registered capabilities with status
wfm-toolkit validate data.csv   # validate a dataset against the canonical schema
```

```python
from wfm_toolkit.cli import WFMCLI

cli = WFMCLI()
print(cli.doctor())  # provider availability + executable capabilities
print(cli.capabilities())  # registered capabilities with status
```

## Capability discovery

The capability registry describes every operation: required inputs, outputs, provider, and **status** (`implemented`, `planned`, `experimental`, `unavailable`).

```python
from wfm_toolkit.capability_registry import CapabilityRegistry

registry = CapabilityRegistry()
for cap in registry.capabilities.values():
    print(cap.identifier, cap.status.value, cap.is_executable())
```

A capability definition being present does **not** mean the operation is executable. Check `cap.is_executable()` — in v0.1.0 only `forecast.generate`, `staffing.erlang_c`, and `validate.dataset` return `True`.

## WFM units and semantics

The adapters use these units when calling providers (documented in adapter metadata):

| Quantity | Unit | Notes |
|---|---|---|
| `transactions` | contacts per interval | explicit input, never inferred |
| `interval` | minutes | interval length |
| `aht` (average handle time) | minutes | pyworkforce API |
| `asa` (average speed of answer) | minutes | pyworkforce API |
| `service_level` | proportion 0–1 | `0.80` = 80% |
| `shrinkage` | proportion 0–1 | |
| `occupancy` | proportion 0–1 | |
| `value` (dataset) | float | WFMData.value must be float for Pandera schema |

See [docs/configuration.md](docs/configuration.md) for the full configuration reference. Provider semantics are described in the [Providers](#providers) section above.

## Optional agent usage

An LLM/agent may use the registry to choose a capability and gather parameters; the Toolkit/provider executes the calculation. The LLM is optional — the Toolkit works entirely without one. This is not a "harness"; it is a library with consistent interfaces.

## Project status

- **Early stage** — API may change
- Core adapter interface and three executable capabilities implemented
- Scheduling, optimization, multi-skill staffing, capacity planning: **planned**, not executable
- Further engineering and release hardening are planned
- **Not yet published to PyPI** — no stable release yet

## Roadmap

Short, grouped roadmap — see [docs/roadmap.md](docs/roadmap.md) for details.

- **Forecasting**: forecast accuracy evaluation, multi-provider comparison
- **Staffing**: multi-skill staffing
- **Scheduling/optimization**: evaluate OR-Tools (no runtime adapter in v0.1.0)
- **Pipeline**: compose forecast → staff → validate

## License

Apache-2.0 Toolkit source. Third-party packages retain their own licenses. See [LICENSE](./LICENSE) and [THIRD_PARTY.md](./THIRD_PARTY.md).