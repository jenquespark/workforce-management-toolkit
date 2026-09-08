# Capability Taxonomy

Workforce Management Toolkit organizes WFM functionality as **capabilities** — discrete operations that can be discovered through consistent interfaces.

The `CapabilityRegistry` defines capabilities as static metadata. **Registration is separate from implementation**: a registered capability may or may not have executable adapter logic in the current version.

## Capability definitions (as registered)

| Capability | Provider | Description | License | Executable in v0.1.0 |
|---|---|---|---|---|
| `forecast.generate` | StatsForecast | Time series forecasting (AutoARIMA, AutoETS, SeasonalNaive) | Apache-2.0 | ✅ via `StatsForecastAdapter.forecast()` |
| `forecast.evaluate` | StatsForecast | Forecast accuracy metrics (MAPE, MAE, RMSE) | Apache-2.0 | ❌ registry-only |
| `staffing.erlang_c` | pyworkforce | Erlang C staffing calculation for voice queues | MIT | ✅ via `PyworkforceAdapter.staff()` |
| `staffing.multiskill` | pyworkforce | Multi-skill staffing calculation | MIT | ❌ registry-only |
| `schedule.generate` | OR-Tools | Shift schedule generation (constraint solving) | Apache-2.0 | ❌ registry-only (adapter stub present) |
| `validate.wfm_config` | Pandera | WFM configuration validation against a canonical schema | MIT | ✅ via `PanderaAdapter.validate()` |
| `capacity.forecast` | StatsForecast | Long-term capacity planning from demand forecasts | Apache-2.0 | ❌ registry-only |

## Capability implementations vs. registry definitions

Distinguish two things:

- **Implemented adapter operations** — adapter methods that execute real provider work when the provider package is installed.
- **Registry-only capability definitions** — static metadata rows that describe a capability but have no executable provider logic in v0.1.0.

### Implemented adapter operations

| Adapter | Executed operations | Non-operational methods |
|---|---|---|
| StatsForecast | `forecast()` | `staff()`, `schedule()`, `optimize()`, `validate()` → structured "requires other provider" errors |
| pyworkforce | `staff()`, `schedule()` | `forecast()`, `optimize()` → structured errors; `validate()` → validation-only |
| Pandera | `validate()` | `forecast()`, `staff()`, `schedule()`, `optimize()` → **validation-only** (validate input, do not perform the named operation) |

Note: the Pandera adapter's `forecast()`, `staff()`, `schedule()`, and `optimize()` methods exist and return successfully, but they only run input validation through Pandera — they do not actually forecast, staff, schedule, or optimize. They are validation-only, not the real operations. Similarly, `PyworkforceAdapter.forecast()` and `optimize()` are "not supported" stubs, not real forecasting/optimization.

### Registry-only capability definitions

`forecast.evaluate`, `staffing.multiskill`, `schedule.generate`, `validate.wfm_config`, and `capacity.forecast` are defined in the registry as static metadata but have **no executable adapter logic** in v0.1.0. They describe the roadmap direction, not current functionality. Do not call them expecting a result.

The `doctor()` check (`WFMCLI.doctor()`) reports which provider packages are actually installed in the current environment; it does not by itself confirm that a named operation is executable.

## Inputs and outputs (per actual adapter)

### `forecast()` — StatsForecast adapter

Signature: `forecast(data: List[WFMData], **kwargs)`

| Parameter | Type | Description |
|---|---|---|
| `data` | List[WFMData] | Historical time series (timestamp + value) |
| `model` | str | `AutoARIMA`, `AutoETS`, `SeasonalNaive` |
| `forecast_horizon` | int | Steps ahead |
| `seasonality` | int | Seasonal period |
| `interval` | float | Confidence interval (0–1) |

Returns: `AdapterResult` with `data` = List[WFMData] forecast points, `metadata` with model used and horizon.

### `staff()` — pyworkforce adapter

Signature: `staff(data: List[WFMData], **kwargs)`

The adapter estimates arrival rates from the input data (using timestamp hour of day) and applies Erlang C with shrinkage and occupancy adjustments.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `service_level` | float | 0.80 | Target service level (0–1) |
| `average_speed_of_answer` | float | 180 | Target ASA (seconds) |
| `shrinkage_rate` | float | 0.30 | Agent shrinkage (0–1) |
| `half_occupancy` | float | 0.85 | Max occupancy (0–1) |

Returns: `AdapterResult` with `data` = `StaffingResult` (allocations per period, metrics).

### `validate()` — Pandera adapter

Signature: `validate(data: List[WFMData], **kwargs)`

Validates input data against a DataFrame schema (timestamp ≥ 2020-01-01, value > 0, monotonic timestamps).

Returns: `AdapterResult` with `data` = validated WFMData list, `metadata` with validation result.

## Capability registry

```python
from wfm_harness.capability_registry import CapabilityRegistry

registry = CapabilityRegistry()
caps = registry.list_capabilities()
for cap in caps:
    print(cap.identifier, cap.provider.name, cap.deterministic)
```

The registry is meant to support machine-readable discovery (useful for automation and language model tool-use).

## Naming note

The public project name is **Workforce Management Toolkit** (`workforce-management-toolkit`), but the Python import package is currently `wfm_harness` (a carry-over from the earlier internal name "Workforce Management Harness"). This temporary mismatch is tracked for the Cloud Code engineering pass.
