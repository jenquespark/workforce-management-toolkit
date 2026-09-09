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

## Additional dependencies

| Package | License | Role |
|---|---|---|
| numpy | BSD-3-Clause | Numerical computing (core) |
| pandas | BSD-3-Clause | Data manipulation (core) |
| pydantic | MIT | Configuration validation (direct) |
| click | BSD-3-Clause | CLI framework (direct) |
| PyYAML | MIT | YAML configuration loading (direct) |

## Planned providers (not part of v0.1.0)

- **OR-Tools** (`ortools`, Apache-2.0) — scheduling/optimization is deferred; no runtime adapter and no `optimization` extra in v0.1.0. Tracked in [docs/roadmap.md](docs/roadmap.md).

## Compatibility

All listed licenses (Apache-2.0, MIT, BSD-3-Clause) are compatible with commercial use under the Apache-2.0 license selected for the Toolkit itself. No GPL or copyleft dependencies are used.

## Policy

- Third-party packages are used as installable dependencies, not vendored source.
- License compatibility is verified before adding new dependencies.
- This file is maintained alongside the source code and updated when dependencies change.