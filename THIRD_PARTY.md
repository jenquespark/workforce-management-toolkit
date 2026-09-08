# Third-Party Licenses

Workforce Management Toolkit depends on third-party open-source packages. Each retains its own license. No third-party source code is vendored.

## Provisioning providers (current v0.1.0)

### StatsForecast

- **Package:** `statsforecast`
- **Upstream:** https://github.com/Nixtla/statsforecast
- **License:** Apache-2.0
- **Role in Toolkit:** Time series forecasting (AutoARIMA, AutoETS, SeasonalNaive)
- **License text:** https://github.com/Nixtla/statsforecast/blob/main/LICENSE

### pyworkforce

- **Package:** `pyworkforce`
- **Upstream:** https://github.com/rodrigo-arenas/pyworkforce
- **License:** MIT
- **Role in Toolkit:** Erlang C staffing calculations for contact center queues
- **License text:** https://github.com/rodrigo-arenas/pyworkforce/blob/main/LICENSE

### Pandera

- **Package:** `pandera`
- **Upstream:** https://github.com/unionai-oss/pandera
- **License:** MIT
- **Role in Toolkit:** Schema validation for WFM datasets
- **License text:** https://github.com/unionai-oss/pandera/blob/main/LICENSE.txt

## Planned provider (not yet a validated core provider)

### OR-Tools

- **Package:** `ortools`
- **Upstream:** https://github.com/google/or-tools
- **License:** Apache-2.0
- **Status:** Adapter class present but non-operational (scheduling/optimization not validated against the installed API); deferred to a future release, not a validated core provider in v0.1.0
- **License text:** https://github.com/google/or-tools/blob/main/LICENSE

## Additional dependencies

| Package | License | Role |
|---|---|---|
| numpy | BSD-3-Clause | Numerical computing (transitive) |
| pandas | BSD-3-Clause | Data manipulation (transitive) |
| pydantic | MIT | Configuration validation |
| click | BSD-3-Clause | CLI framework |

## Compatibility

All listed licenses (Apache-2.0, MIT, BSD-3-Clause) are compatible with commercial use under the Apache-2.0 license selected for the Toolkit itself. No GPL or copyleft dependencies are used.

## Policy

- Third-party packages are used as installable dependencies, not vendored source.
- License compatibility is verified before adding new dependencies.
- This file is maintained alongside the source code and updated when dependencies change.
