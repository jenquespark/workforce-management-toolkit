# Architecture

Workforce Management Toolkit is structured in three layers: consumers, the Toolkit core, and provider libraries.

## Layer overview

### Consumer layer

The consumers that interact with the Toolkit:

- **Python API** — the `wfm_toolkit` module for programmatic access (primary interface)
- **Capability registry** — machine-readable capability descriptions for automation and language-model tool-use
- **CLI** — a `wfm-toolkit` console script is planned; Click commands are not yet wired up

### Toolkit core

The core provides:

- **Capability Registry** — machine-readable catalog with explicit executable/planned status
- **Base Adapter** — abstract interface that all provider adapters implement
- **Domain Models** — canonical data structures (`WFMData`, result types)
- **Configuration** — Pydantic V2 validated settings with explicit units

### Provider layer

External provider libraries:

- **StatsForecast** — statistical forecasting models
- **pyworkforce** — Erlang C staffing calculations
- **Pandera** — schema validation for DataFrames

OR-Tools is present as an adapter class but is **not** a validated core provider in v0.1.0: its scheduling/optimization methods are not operational against the installed API (verified: `schedule()` fails with an API mismatch, `optimize()` returns INFEASIBLE on its default model). It is deferred.

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
- **pyworkforce adapter** — `staff()` executes (Erlang C via explicit business inputs); `forecast()`, `optimize()`, and `schedule()` return explicit unsupported results (scheduling is deferred).
- **Pandera adapter** — `validate()` executes; `forecast()`, `staff()`, `schedule()`, `optimize()` return explicit unsupported results. Pandera is a validation provider; calling `forecast()` on it does not silently validate-and-succeed.
- **OR-Tools adapter** — class present; `optimize()`/`schedule()` are non-operational in this stage and the capabilities are registered as planned.

This design means:

- Capabilities are clearly separated by provider
- Unsupported operations fail explicitly rather than silently doing something else
- Adding a new adapter requires implementing `BaseAdapter`
- `execute_operation` dispatches to the correct operation
- Results are consistently typed as `AdapterResult`

## Domain models

All data flows through `WFMData` containers:

```python
@dataclass
class WFMData:
    timestamp: datetime
    value: float
    metadata: Dict[str, Any]
```

Results are typed per operation:

- `ForecastResult` — predictions with model metadata
- `StaffingResult` — agent allocations with metrics
- `ScheduleResult` — roster assignments (unused until scheduling is implemented)
- `OptimizationResult` — objective value and solution (unused until optimization is implemented)
- `ValidationResult` — pass/fail with violations

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
├── __main__.py              # python -m wfm_toolkit summary
├── version.py               # Version string
├── domain.py                # Data models (WFMData, results)
├── config.py                # Pydantic V2 configuration
├── capability.py            # Capability configuration
├── capability_registry.py   # Capability registry (status-aware)
├── capacity_registry.py     # Capacity planning definitions (planned)
├── skill_registry.py        # Agent skill definitions
├── cli.py                   # WFMCLI programmatic helpers (no wired console script)
└── adapters/
    ├── __init__.py          # Adapter exports
    ├── base.py              # BaseAdapter interface
    ├── statsforecast_adapter.py  # Forecasting (executable)
    ├── pyworkforce_adapter.py    # Staffing (executable)
    ├── pandera_adapter.py        # Validation (executable)
    └── ortools_adapter.py        # Scheduling/optimization (deferred)
```

## Design rationale

**Why adapters instead of direct library calls?** Adapters normalize the interface so consumers don't need to know each library's specific API. This also makes it possible to swap providers or add new ones without changing consumer code.

**Why WFMData instead of raw dicts?** Typed containers prevent common WFM data errors (wrong timestamp format, missing values, type mismatches).

**Why optional extras?** Not every user needs every provider. The `forecast` extra pulls in StatsForecast; the `staffing` extra pulls in pyworkforce. This keeps the dependency footprint small.

**Why a capability registry with status?** Machine-readable capability discovery enables automation to determine what operations are actually executable versus merely registered, without hardcoding that knowledge.