# Hardening Audit Findings (internal)

Branch: `hardening/v0.1.0-candidate`
Base: `7e4eed30185edcf27e134760df0450bef8117967`
Python: 3.12.3 (venv), deps: statsforecast 2.1.1, pyworkforce 0.5.4, pandera 0.33.1,
ortools 9.15.6755, pydantic 2.13.5, pytest 9.1.1, ruff 0.16.6

## Blockers / Must-fix

1. **`wfm_toolkit/capacity_registry.py` (395 lines)** — a *second*, independent,
   Pydantic **v1** config model (`from pydantic import BaseModel, Field, validator`),
   entirely unused (only self-references). Dead code + Pydantic v1 leftover. **DELETE.**
2. **`wfm_toolkit/skill_registry.py` (274 lines)** — completely unused (0 references
   outside itself). **DELETE.**
3. **`wfm_toolkit/capability.py` (94 lines)** — `CapabilityConfig` unused; the real
   capability model is `capability_registry.Capability`. **DELETE.**
4. **`wfm_toolkit/adapters/ortools_adapter.py` (516 lines)** — broken against the
   installed OR-Tools 9.15 API (`model.NewSumArray(...)` no longer exists;
   `cp_model.LinearExpr.Sum([1 for d ... if days_worked_vars[d] == 0])` is nonsense —
   comparing IntVar to int inside a list comprehension, then `LinearExpr.Sum` of a
   plain Python list of ints). The "scheduling" logic invents dates (`datetime.now()`),
   fabricates `num_constraints` estimates, and reports `success=True` for fake results.
   **DELETE from v0.1 runtime.** Roadmap doc keeps the intent.
5. **Global `warnings.filterwarnings("ignore")`** in three adapters (pyworkforce,
   statsforecast, ortools) — a library must not globally suppress warnings. **REMOVE.**
6. **`datetime.utcnow()`** in `config.py` (WFMBaseConfig.created_at) and
   `capability_registry.py` (CapabilityMetadata.created_at) — deprecated in 3.12,
   causes 300 warnings in the test suite. **Replace with `datetime.now(timezone.utc)`.**
7. **`pyproject.toml` claims `requires-python >=3.9`** — false: current deps
   (pyworkforce>=0.5.2, pandera>=0.33, statsforecast>=2.1) all require >=3.12/>=3.10.
   **Raise to `>=3.12`** (the true current floor), update classifiers, CI matrix.
8. **`StaffingAlgorithm.eRLANG_X`** — bad generated name; normalize to `ERLANG_X`
   (pre-release, no compat reason). Update `get_multi_skill_example_config()`.
9. **`pyproject.toml` `optimization` extra + `ortools` dep** — dangling now that the
   adapter is removed; **remove extra** and keep deps to the three real providers.
10. **No console script** — implement `wfm-toolkit` (doctor, capabilities, validate)
    and wire `[project.scripts]`.
11. **CLI version hardcoded "0.1.0"** in `cli.py`; **`datetime.utcnow()`** there too.

## Secondary / quality

12. `domain.py`: `ForecastResult`, `ScheduleResult`, `OptimizationResult`,
    `ValidationResult` unused (only OR-Tools used 2 of them). Keep `WFMData`,
    `StaffingResult`; delete unused types.
13. `config.py` `merge_with_default`/`get_required_components` —
    `get_required_components` is used; keep. Verify `merge_with_default` usage.
14. Adapter `staff()` signature `staff(data, transactions=..., aht=..., ...)` — awkward
    positional args; evaluate a typed `StaffingRequest` dataclass for domain clarity
    (pre-release, deliberate API change).
15. `PyworkforceAdapter` unit metadata: `transactions` documented as
    "transactions per interval" but upstream computes `intensity = (transactions/interval)*aht`.
    Verify and document exact semantics.
16. `BaseAdapter` has `forecast/staff/schedule/optimize/validate` all abstract — every
    adapter must implement all; that's fine but `schedule`/`optimize` are dead across
    all three real adapters (all return unsupported). Consider keeping them explicit
    (honest) — they are.
17. `pandera_adapter`: `_convert_to_wfmdata` metadata={} drops metadata — acceptable,
    document. `output_schema.validate()` is meaningless double-validation (input schema
    already validated); simplify.
18. Docs: `docs/architecture.md`, `capabilities.md`, `roadmap.md`, `configuration.md`
    reference OR-Tools/scheduling as if available — update to match final surface.
19. `THIRD_PARTY.md`: update to remove OR-Tools "planned provider" section; add
    missing transitive deps (numpy/pandas/pydantic/click) — already listed; verify.
20. Tests: no parity tests yet (kitchen-sink asserts only). Add:
    - real pyworkforce direct call vs adapter parity
    - real statsforecast direct call vs adapter parity
    - real pandera direct vs adapter parity
    - missing-optional-dep boundary tests
    - CLI tests (doctor/capabilities/validate exit codes + output)
    - registry executable/planned status
21. CI: no GitHub Actions workflow. Add minimal matrix (3.12, 3.13):
    ruff check, ruff format --check, pytest, build, wheel-install smoke.
22. README: verify it matches final surface (OR-Tools mentions must be removed).
23. `version.py` → `0.1.0` — stays.

## Security / privacy scan (preliminary)
- No secrets/private refs found in tree (will run full scan with git history).
- `load_config_from_yaml/json`: filesystem reads only, no writes, no eval.
- No network calls in adapters.