# Architecture

Workforce Management Toolkit is structured in three layers: consumers, the Toolkit core, and provider libraries.

## Layer overview

### Consumer layer

The consumers that interact with the Toolkit:

- **Python API** — the `wfm_toolkit` module for programmatic access (primary interface)
- **CLI** — the `wfm-toolkit` console script (`doctor`, `capabilities`, `validate`)
- **Capability registry** — machine-readable capability descriptions for automation and language-model tool-use

### Toolkit core

The core provides:

- **Capability Registry** — machine-readable catalog with explicit executable/planned status
- **Base Adapter** — abstract interface that all provider adapters implement
- **Domain Models** — canonical data structures (`WFMData`, `StaffingRequest`, `StaffingResult`)
- **Configuration** — Pydantic V2 validated settings with explicit units

### Provider layer

External provider libraries:

- **StatsForecast** — statistical forecasting models
- **pyworkforce** — Erlang C staffing calculations
- **Pandera** — schema validation for DataFrames

OR-Tools scheduling/optimization is **deferred**: there is no runtime adapter in
v0.1.0 and no `optimization` install extra. The intent is tracked in the
roadmap; no dead adapter ships in the package.

## Adapter interface

Every adapter implements `BaseAdapter`:

```python
class BaseAdapter(ABC):
    @abstractmethod
    def health_check(self) -> bool: ...

    @abstractmethod
    def forecast(self, data, **kwargs) -> AdapterResult: ...

    @abstractmethod
    def staff(self, data, **kwargs) -> AdapterResult: ...

    @abstractmethod
    def schedule(self, data, **kwargs) -> AdapterResult: ...

    @abstractmethod
    def optimize(self, data, **kwargs) -> AdapterResult: ...

    @abstractmethod
    def validate(self, data, **kwargs) -> AdapterResult: ...
```

Each adapter implements the full method surface but only performs real provider work on its domain operations:

- **StatsForecast adapter** — `forecast()` executes; `staff()`, `schedule()`, `optimize()`, `validate()` return explicit unsupported results.
- **pyworkforce adapter** — `staff()` executes (Erlang C via explicit business inputs, a `StaffingRequest` or kwargs); `forecast()`, `optimize()`, and `schedule()` return explicit unsupported results (scheduling is deferred).
- **Pandera adapter** — `validate()` executes; `forecast()`, `staff()`, `schedule()`, `optimize()` return explicit unsupported results. Pandera is a validation provider; calling `forecast()` on it does not silently validate-and-succeed.

This design means:

- Capabilities are clearly separated by provider
- Unsupported operations fail explicitly rather than silently doing something else
- Adding a new adapter requires implementing `BaseAdapter`
- `execute_operation` dispatches to the correct operation
- Results are consistently typed as `AdapterResult`

## Domain models

All time-series data flows through `WFMData` containers:

```python
@dataclass(frozen=True)
class WFMData:
    timestamp: datetime
    value: int | float
    metadata: dict[str, Any]
```

Staffing inputs use the typed `StaffingRequest` (explicit units, no invented demand):

```python
@dataclass(frozen=True)
class StaffingRequest:
    transactions: float  # total transactions in the interval
    aht: float  # minutes
    asa: float  # minutes
    interval_min: int  # interval length in minutes
    service_level: float = 0.80  # [0, 1]
    max_occupancy: float = 0.85  # (0, 1]
    shrinkage: float = 0.0  # [0, 1)
```

Results are typed per operation:

- `StaffingResult` — positions and Erlang C metrics from pyworkforce
- `AdapterResult` — uniform envelope for all adapter operations (success, data, metadata, error)

Forecast and validation results are returned inside the `AdapterResult` envelope
(`data` is `list[WFMData]` for forecast and validation).

## Data flow

1. **Input:** Consumer provides `list[WFMData]` (or explicit business parameters for staffing)
2. **Adapter dispatch:** `execute_operation` routes to the correct adapter method
3. **Provider execution:** Adapter calls the provider library (e.g., StatsForecast `StatsForecast(models=[...]).forecast()`, pyworkforce `ErlangC(...).required_positions()`, Pandera `DataFrameSchema.validate()`)
4. **Result normalization:** Adapter wraps library output in typed result objects
5. **Output:** `AdapterResult` returned with success status, data, and metadata

## File structure

```
wfm_toolkit/
├── __init__.py              # Package exports
├── __main__.py              # python -m wfm_toolkit -> CLI
├── version.py               # Version string
├── domain.py                # Data models (WFMData, StaffingRequest, StaffingResult)
├── config.py                # Pydantic V2 configuration
├── capability_registry.py   # Capability registry (status-aware)
├── cli.py                   # wfm-toolkit CLI (doctor, capabilities, validate)
└── adapters/
    ├── __init__.py          # Adapter exports
    ├── base.py              # BaseAdapter interface
    ├── statsforecast_adapter.py  # Forecasting (executable)
    ├── pyworkforce_adapter.py    # Staffing (executable)
    └── pandera_adapter.py        # Validation (executable)
```

## Design rationale

**Why adapters instead of direct library calls?** Adapters normalize the interface so consumers don't need to know each library's specific API. This also makes it possible to swap providers or add new ones without changing consumer code.

**Why WFMData instead of raw dicts?** Typed containers prevent common WFM data errors (wrong timestamp format, missing values, type mismatches).

**Why optional extras?** Not every user needs every provider. The `forecast` extra pulls in StatsForecast; the `staffing` extra pulls in pyworkforce. This keeps the dependency footprint small.

**Why a capability registry with status?** Machine-readable capability discovery enables automation to determine what operations are actually executable versus merely registered, without hardcoding that knowledge.