# Capability Taxonomy

Workforce Management Toolkit organizes WFM functionality as **capabilities** — discrete operations that can be discovered through consistent interfaces.

The `CapabilityRegistry` defines the following capabilities statically. Each has an identifier, provider, license, deterministic flag, and input/output schema.

## Capability definitions (from the registry)

| Capability | Provider | Description | License |
|---|---|---|---|
| `forecast.generate` | StatsForecast | Generate deterministic forecasts (AutoARIMA, AutoETS, SeasonalNaive) | Apache-2.0 |
| `forecast.evaluate` | StatsForecast | Forecast accuracy metrics (MAPE, MAE, RMSE) | Apache-2.0 |
| `staffing.erlang_c` | pyworkforce | Erlang C staffing calculation for voice queues | MIT |
| `staffing.multiskill` | pyworkforce | Multi-skill staffing calculation | MIT |
| `schedule.generate` | OR-Tools | Shift schedule generation (constraint solving) | Apache-2.0 |
| `validate.wfm_config` | Pandera | WFM configuration validation against a canonical schema | MIT |
| `capacity.forecast` | StatsForecast | Long-term capacity planning from demand forecasts | Apache-2.0 |

## What is actually implemented and tested

The adapter implementations exist for:

- **StatsForecast adapter** — `forecast()` implemented; `staff()`, `schedule()`, `optimize()`, `validate()` return structured errors (they require other providers)
- **pyworkforce adapter** — `staff()` and `schedule()` implemented; `forecast()`, `optimize()`, `validate()` return structured errors
- **Pandera adapter** — `validate()` implemented; `forecast()`, `staff()`, `schedule()`, `optimize()` return structured errors
- **OR-Tools adapter** — `optimize()` and `schedule()` present; this provider is not yet a validated core capability

The registry's capability definitions are static metadata. Whether a capability actually executes depends on the provider package being installed and the corresponding adapter being invoked. The `doctor()` check reports which provider packages are installed in the environment.

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

## Non-operational capabilities

`forecast.evaluate`, `staffing.multiskill`, `schedule.generate`, `validate.wfm_config`, `capacity.forecast` are defined in the registry as metadata but have no executable adapter logic in v0.1.0. They represent the roadmap direction, not current functionality.

## Capability registry

```python
from wfm_harness.capability_registry import CapabilityRegistry

registry = CapabilityRegistry()
caps = registry.list_capabilities()
for cap in caps:
    print(cap.identifier, cap.provider.name, cap.deterministic)
```

The registry is meant to support machine-readable discovery (useful for automation and language model tool-use).