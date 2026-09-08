# Architecture

Workforce Management Toolkit is structured in three layers: consumers, the Toolkit core, and provider libraries.

> **Naming note (temporary internal namespace):** The public project name is **Workforce Management Toolkit** (`workforce-management-toolkit`), but the Python import package is currently `wfm_harness` — a carry-over from the earlier internal project name "Workforce Management Harness". The package directory, module names, and import statements all use `wfm_harness`. This mismatch is known and will be reconciled by the Cloud Code engineering pass; it is tracked here deliberately rather than fixed now to avoid a churn-heavy rename during the documentation phase.

## Layer overview

### Consumer layer

The consumers that interact with the Toolkit:

- **Python API** — `wfm_harness` module for programmatic access (primary interface)
- **Agent Skills** — Machine-readable capability descriptions for language model tool-use
- **CLI** — `wfm-harness` command-line tool (planned; Click commands not yet wired up)

### Toolkit core

The core provides:

- **Capability Registry** — Machine-readable catalog of available operations
- **Base Adapter** — Abstract interface that all provider adapters implement
- **Domain Models** — Canonical data structures (`WFMData`, result types)
- **Configuration** — Pydantic V2 validated settings with explicit units
- **CLI Framework** — Click-based command structure

### Provider layer

External provider libraries:

- **StatsForecast** — Statistical forecasting models
- **pyworkforce** — Erlang C staffing calculations
- **Pandera** — Schema validation for DataFrames

(OR-Tools is present as an adapter stub and is planned for a future release, but is not a validated core provider.)

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

Each adapter implements the full `forecast()`, `staff()`, `schedule()`, `optimize()`, and `validate()` method surface but only performs real provider work on its domain operations:

- **StatsForecast adapter** — `forecast()` executes; `staff()`, `schedule()`, `optimize()`, `validate()` return structured "requires another provider" errors.
- **pyworkforce adapter** — `staff()` and `schedule()` execute; `forecast()` and `optimize()` return structured "not supported" errors; `validate()` runs a Pandera-based input check.
- **Pandera adapter** — `validate()` executes; `forecast()`, `staff()`, `schedule()`, `optimize()` are **validation-only** (they validate the input through Pandera but do not perform the named operation).
- **OR-Tools adapter** — `optimize()` and `schedule()` present as stubs; not a validated core provider in v0.1.0.

This design means:

- Capabilities are clearly separated by provider
- Adding a new adapter requires implementing `BaseAdapter`
- The `execute_operation` method dispatches to the correct operation
- Results are consistently typed as `AdapterResult`

## Domain models

All data flows through `WFMData` containers:

```python
@dataclass
class WFMData:
    timestamp: datetime
    value: Union[int, float]
    metadata: Dict[str, Any]
```

Results are typed per operation:

- `ForecastResult` — predictions with confidence intervals
- `StaffingResult` — agent allocations with metrics
- `ScheduleResult` — roster assignments
- `OptimizationResult` — objective value and solution
- `ValidationResult` — pass/fail with violations

## Data flow

1. **Input:** Consumer provides `list[WFMData]` (or equivalent)
2. **Adapter dispatch:** `execute_operation` routes to the correct adapter method
3. **Provider execution:** Adapter calls the provider library (e.g., `statsforecast`, `pyworkforce.erlang_c`)
4. **Result normalization:** Adapter wraps library output in typed result objects
5. **Output:** `AdapterResult` returned with success status, data, and metadata

## File structure

```
wfm_harness/
├── __init__.py              # Package exports
├── __main__.py              # Entry point
├── version.py               # Version string
├── domain.py                # Data models (WFMData, results)
├── config.py                # Pydantic V2 configuration
├── capability.py            # Capability configuration
├── capability_registry.py   # Capability registry
├── capacity_registry.py     # Capacity planning registry (planned)
├── skill_registry.py        # Agent skill definitions
├── cli.py                   # Command-line interface (WFMCLI class; Click wired in later release)
└── adapters/
    ├── __init__.py           # Adapter exports
    ├── base.py               # BaseAdapter interface
    ├── statsforecast_adapter.py  # Forecasting
    ├── pyworkforce_adapter.py    # Staffing
    ├── pandera_adapter.py        # Validation
    └── ortools_adapter.py        # Scheduling/optimization
```

## Design rationale

**Why adapters instead of direct library calls?** Adapters normalize the interface so consumers don't need to know each library's specific API. This also makes it possible to swap providers or add new ones without changing consumer code.

**Why WFMData instead of raw dicts?** Typed containers prevent common WFM data errors (wrong timestamp format, missing values, type mismatches).

**Why optional extras?** Not every user needs every provider. The `forecast` extra pulls in StatsForecast; the `staffing` extra pulls in pyworkforce. This keeps the dependency footprint small.

**Why a capability registry?** Machine-readable capability discovery enables language models to programmatically determine what operations are available and what parameters they require, without hardcoding that knowledge into prompts.
