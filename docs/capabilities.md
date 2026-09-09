# Capability Taxonomy

Workforce Management Toolkit organizes WFM functionality as **capabilities** — discrete operations discoverable through consistent interfaces.

The `CapabilityRegistry` defines capabilities as metadata with an explicit **status**. **Registration is separate from implementation**: a registered capability may be `implemented`, `planned`, `experimental`, or `unavailable`. In v0.1.0 only three capabilities are executable.

## Capability definitions (as registered)

| Capability | Provider | Description | License | Status |
|---|---|---|---|---|
| `forecast.generate` | StatsForecast | Statistical time-series forecasting (AutoARIMA, AutoETS, SeasonalNaive) | Apache-2.0 | ✅ implemented — `StatsForecastAdapter.forecast()` |
| `forecast.evaluate` | StatsForecast | Forecast accuracy metrics (MAPE, MAE, RMSE) | Apache-2.0 | ❌ planned |
| `staffing.erlang_c` | pyworkforce | Erlang C required positions for voice queues | MIT | ✅ implemented — `PyworkforceAdapter.staff()` |
| `staffing.multiskill` | pyworkforce | Multi-skill staffing | MIT | ❌ planned |
| `schedule.generate` | OR-Tools | Shift schedule generation (constraint solving) | Apache-2.0 | ❌ planned (no runtime adapter in v0.1.0) |
| `validate.dataset` | Pandera | Dataset schema validation | MIT | ✅ implemented — `PanderaAdapter.validate()` |
| `validate.wfm_config` | Pandera | Configuration dict validation | MIT | ❌ planned |
| `capacity.forecast` | StatsForecast | Long-term capacity planning | Apache-2.0 | ❌ planned |

## Executable vs. registered

Distinguish two things:

- **Implemented adapter operations** — adapter methods that execute real provider work when the provider package is installed.
- **Registry-only (planned) capability definitions** — metadata that describes a capability with no executable provider logic in v0.1.0.

### Implemented adapter operations

| Adapter | Executed operations | Non-operational methods |
|---|---|---|
| StatsForecast | `forecast()` | `staff()`, `schedule()`, `optimize()`, `validate()` → explicit unsupported |
| pyworkforce | `staff()` | `forecast()`, `optimize()` → explicit unsupported; `schedule()` → explicit unsupported (scheduling deferred) |
| Pandera | `validate()` | `forecast()`, `staff()`, `schedule()`, `optimize()` → explicit unsupported |

An unsupported operation returns an `AdapterResult` with `success=False` and an error message explaining which provider handles that domain. No adapter silently performs a different operation to satisfy the interface, and no method named `forecast()`/`staff()`/`schedule()` reports success merely because input validation passed.

### Registry-only (planned) capabilities

`forecast.evaluate`, `staffing.multiskill`, `schedule.generate`, `validate.wfm_config`, and `capacity.forecast` are registered metadata with **no executable adapter logic** in v0.1.0. `Capability.is_executable()` returns `False` for them. Do not call them expecting a result.

The `doctor()` check (`WFMCLI.doctor()`) reports which provider packages are importable and which capabilities are executable; it reflects the current environment.

## Inputs and outputs (per actual adapter)

### `forecast()` — StatsForecast adapter

Signature: `forecast(data: List[WFMData], **kwargs)`

| Parameter | Type | Description |
|---|---|---|
| `data` | List[WFMData] | Historical time series (timestamp + float value) |
| `model` | str | `AutoARIMA`, `AutoETS`, `SeasonalNaive` |
| `forecast_horizon` | int | Steps ahead |
| `season_length` | int | Seasonal period |
| `freq` | str | pandas frequency, e.g. `"D"` |

Returns: `AdapterResult` with `data` = List[WFMData] forecast points and `metadata` (model used, horizon, data points).

### `staff()` — pyworkforce adapter

Signature: `staff(data, **kwargs)`

The adapter **never invents demand**. The caller must supply explicit business inputs as keyword arguments:

| Parameter | Type | Unit | Required |
|---|---|---|---|
| `transactions` | float | contacts per interval | yes |
| `aht` | float | minutes | yes |
| `asa` | float | minutes | yes |
| `interval_min` | int | minutes | yes |
| `service_level` | float | proportion [0,1] | no (default 0.80) |
| `max_occupancy` | float | proportion (0,1] | no (default 0.85) |
| `shrinkage` | float | proportion [0,1) | no (default 0.0) |

Returns: `AdapterResult` with `data` = `StaffingResult` (allocations per period, metrics from `ErlangC.required_positions()`: raw_positions, positions, service_level, occupancy, waiting_probability). The calculation is delegated to pyworkforce; the Toolkit does not implement Erlang math.

### `validate()` — Pandera adapter

Signature: `validate(data: List[WFMData], **kwargs)`

Validates a dataset against a DataFrame schema (timestamp ≥ 2020-01-01, value float > 0). Values must be floats (int values fail the `float64` dtype check).

Returns: `AdapterResult` with `data` = validated WFMData list on success, or `success=False` with a schema error message.

## Capability registry

```python
from wfm_toolkit.capability_registry import CapabilityRegistry

registry = CapabilityRegistry()
caps = registry.capabilities.values()
for cap in caps:
    print(cap.identifier, cap.status.value, cap.is_executable())
```

`registry.executable_capabilities()` returns only the three implemented capabilities. The registry supports machine-readable discovery for automation and language-model tool use.