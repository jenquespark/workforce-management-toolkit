# Changelog

All notable changes to the Workforce Management Toolkit will be documented in this file.

## v0.1.0

Initial public release.

### Capabilities

- `forecast.generate` — statistical time-series forecasting via StatsForecast (AutoARIMA, AutoETS, SeasonalNaive)
- `staffing.erlang_c` — Erlang C staffing calculations via pyworkforce
- `validate.dataset` — WFM dataset validation via Pandera

### Features

- Capability registry with metadata for all planned and implemented operations
- Click-based CLI (`wfm-toolkit`) with `doctor`, `capabilities`, and `validate` commands
- Typed `StaffingRequest` dataclass with unit-clarity (`aht_min`, `asa_min`, `interval_min`)
- Lazy adapter imports — bare package installs cleanly without optional providers
- GitHub Actions CI (lint, test on Python 3.12 + 3.13, build, wheel smoke)

### Packages

- `statsforecast` (Apache-2.0) — forecasting
- `pyworkforce` (MIT) — Erlang C staffing
- `pandera` (MIT) — dataset validation
- `numpy`, `pandas`, `pydantic`, `PyYAML`, `click` — core dependencies