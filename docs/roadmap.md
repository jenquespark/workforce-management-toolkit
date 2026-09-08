# Roadmap

Workforce Management Toolkit v0.1.0 provides the foundational capability set. This document describes directions for future development based on the current architecture.

## Near-term (v0.2)

### Forecast evaluation

Compute accuracy metrics (MAPE, MAE, RMSE) against held-out data. This enables comparing models and monitoring forecast degradation over time.

### Multi-provider forecasting

Allow different forecasting libraries to be swapped or compared through the same interface. Candidates include Prophet, statsmodels (SARIMAX), and custom implementations.

### Multi-skill staffing

Extend the staffing capability to handle environments where agents have multiple skills and calls are routed by skill matching. This is a common requirement in blended contact centers.

### Pipeline composition

A higher-level API that sequences forecast → staffing → schedule as a single executable workflow, with intermediate results accessible at each step.

### Enhanced configuration

More granular configuration for per-skill, per-interval, and per-channel settings. Configuration versioning and migration support.

## Medium-term (v0.3)

### Intraday management

Real-time adjustments to staffing based on actual vs. predicted volume. This requires integration with live data feeds and intraday optimization algorithms.

### Chat and async workloads

Voice staffing is based on concurrent agent requirements. Chat staffing requires concurrency modeling (agents handle multiple simultaneous conversations). Email and back-office work use different queueing models.

### Capacity planning

Long-term capacity modeling: headcount forecasting, hiring plans, training pipeline effects, and attrition modeling.

### Scenario analysis

Run multiple what-if scenarios with different parameters (shrinkage assumptions, volume changes, service level targets) and compare outcomes.

### BI integration patterns

Documented patterns for connecting Toolkit output to common BI platforms (Metabase, Grafana, Power BI) and databases (PostgreSQL, SQLite).

## Longer-term

### MCP/tool protocol

Support for the Model Context Protocol or similar standards that allow language models to discover and use tools through standardized interfaces.

### Additional providers

Evaluate and integrate additional open-source WFM libraries as they become mature and actively maintained.

### Provider benchmarking

Systematic comparison of different providers for the same capability (e.g., multiple forecasting libraries, multiple staffing algorithms) with documented accuracy and performance characteristics.

### Reproducibility

Ensure every calculation produces identical results given identical input, with metadata documenting the exact provider version and parameters used.

### Workflow engine

A more sophisticated workflow engine that handles branching, error recovery, conditional logic, and partial execution in multi-step WFM processes.

## Design constraints

Future development will maintain:

- Calculations delegated to explicit software providers (never performed by the model itself)
- LLM independence (the Toolkit works without any language model)
- Optional dependencies (each provider remains independently installable)
- License compatibility (all dependencies remain commercially usable)
- Explicit units and validation for all parameters
