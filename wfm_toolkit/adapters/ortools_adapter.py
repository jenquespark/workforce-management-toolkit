"""
OR-Tools adapter for Workforce Management Toolkit.

Adapter for the OR-Tools library - constraint solving and shift scheduling.
Implements optimize() for constraint solving and schedule() for shift scheduling.
Other operations return AdapterResult with error_message='Not supported by OR-Tools'.
"""

from __future__ import annotations

import warnings

warnings.filterwarnings("ignore")

try:
    from ortools.sat.python import cp_model

    has_ortools = True
except ImportError:
    has_ortools = False

from datetime import datetime  # noqa: E402

from ..domain import OptimizationResult, ScheduleResult, WFMData  # noqa: E402
from .base import AdapterConfig, AdapterResult, BaseAdapter  # noqa: E402


class ORToolsAdapter(BaseAdapter):
    """Adapter for OR-Tools library - constraint solving and shift scheduling."""

    def __init__(self, config: AdapterConfig | None = None):
        if config is None:
            config = AdapterConfig(
                provider_name="OR-Tools",
                package_name="ortools",
                license="Apache-2.0",
                deterministic_level="high",
                required_dependencies=["ortools"],
                optional_dependencies=["numpy", "pandas"],
                configuration_options={
                    "solver": "CP-SAT",
                    "time_limit_seconds": 30,
                    "num_search_workers": 4,
                    "log_search_progress": False,
                    "optimization_objective": "minimize_cost",
                },
            )
        super().__init__(config)

    def _validate_dependencies(self):
        """Validate that OR-Tools dependencies are available."""
        if not has_ortools:
            raise ImportError(
                "OR-Tools is not installed. Install with: pip install ortools==9.8.3296"
            )

    def _initialize_adapter(self):
        """Initialize OR-Tools adapter."""
        self.solver_type = self.config.configuration_options.get("solver", "CP-SAT")
        self.time_limit = self.config.configuration_options.get("time_limit_seconds", 30)
        self.num_workers = self.config.configuration_options.get("num_search_workers", 4)
        self.log_progress = self.config.configuration_options.get("log_search_progress", False)
        self.last_solver = None

    def health_check(self) -> bool:
        """Check if OR-Tools adapter is healthy."""
        try:
            if not has_ortools:
                return False

            # Create a simple test model
            model = cp_model.CpModel()
            x = model.NewIntVar(0, 10, "x")
            y = model.NewIntVar(0, 10, "y")
            model.Add(x + y == 10)
            model.Maximize(x)

            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = 5
            solver.parameters.num_search_workers = 1
            solver.parameters.log_search_progress = False
            status = solver.Solve(model)

            return status in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        except Exception:
            return False

    def optimize(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """Optimize operations using OR-Tools CP-SAT solver.

        Solves constraint optimization problems for workforce management:
        - Staff allocation optimization
        - Shift coverage optimization
        - Cost minimization with constraints
        """
        try:
            if not has_ortools:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="optimize",
                    success=False,
                    data=None,
                    error_message="OR-Tools not installed",
                )

            if not data:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="optimize",
                    success=False,
                    data=None,
                    error_message="No data provided for optimization",
                )

            # Extract requirements from kwargs
            requirements = kwargs.get("requirements", {})
            constraints = kwargs.get("constraints", {})

            num_agents = requirements.get("num_agents", 10)
            shifts_per_day = requirements.get("shifts_per_day", 3)
            days = requirements.get("days", 7)
            min_agents_per_shift = requirements.get("min_agents_per_shift", 2)
            max_agents_per_shift = requirements.get("max_agents_per_shift", 5)

            # Create CP-SAT model
            model = cp_model.CpModel()

            # Decision variables: x[a][d][s] = 1 if agent a works shift s on day d
            x = {}
            for a in range(num_agents):
                for d in range(days):
                    for s in range(shifts_per_day):
                        x[(a, d, s)] = model.NewBoolVar(f"x_{a}_{d}_{s}")

            # Constraint: Each shift must have min/max agents
            for d in range(days):
                for s in range(shifts_per_day):
                    shift_vars = [x[(a, d, s)] for a in range(num_agents)]
                    model.Add(sum(shift_vars) >= min_agents_per_shift)
                    model.Add(sum(shift_vars) <= max_agents_per_shift)

            # Constraint: Max consecutive days
            max_consecutive = constraints.get("max_consecutive_days", 5)
            for a in range(num_agents):
                for d in range(days - max_consecutive):
                    window_vars = [
                        x[(a, d + i, s)]
                        for i in range(max_consecutive + 1)
                        for s in range(shifts_per_day)
                    ]
                    model.Add(sum(window_vars) <= max_consecutive * shifts_per_day)

            # Constraint: Min rest hours between shifts (simplified - no back-to-back night/morning)
            min_rest = constraints.get("min_rest_hours", 12)
            if min_rest >= 12:
                for a in range(num_agents):
                    for d in range(days - 1):
                        # Night shift (s=2) followed by morning shift (s=0) next day
                        model.Add(x[(a, d, 2)] + x[(a, d + 1, 0)] <= 1)

            # Constraint: Max weekly hours
            max_weekly = constraints.get("max_weekly_hours", 40)
            for a in range(num_agents):
                weekly_vars = [x[(a, d, s)] for d in range(days) for s in range(shifts_per_day)]
                model.Add(sum(weekly_vars) * 8 <= max_weekly)

            # Objective: Minimize total cost (or maximize fairness)
            # Simple objective: balance workload across agents
            total_shifts = []
            for a in range(num_agents):
                agent_shifts = [x[(a, d, s)] for d in range(days) for s in range(shifts_per_day)]
                total_shifts.append(sum(agent_shifts))

            # Minimize max difference in shifts between agents
            max_shifts = model.NewIntVar(0, days * shifts_per_day, "max_shifts")
            min_shifts = model.NewIntVar(0, days * shifts_per_day, "min_shifts")
            model.AddMaxEquality(max_shifts, total_shifts)
            model.AddMinEquality(min_shifts, total_shifts)
            model.Minimize(max_shifts - min_shifts)

            # Solve
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = self.time_limit
            solver.parameters.num_search_workers = self.num_workers
            solver.parameters.log_search_progress = self.log_progress

            status = solver.Solve(model)

            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="optimize",
                    success=False,
                    data=None,
                    error_message=f"Optimization failed: {cp_model.CpSolver().StatusName(status)}",
                )

            # Extract solution
            assignments = {}
            for a in range(num_agents):
                agent_assignments = []
                for d in range(days):
                    for s in range(shifts_per_day):
                        if solver.Value(x[(a, d, s)]) == 1:
                            agent_assignments.append(
                                {
                                    "agent": f"agent_{a}",
                                    "day": d,
                                    "shift": s,
                                    "timestamp": data[0].timestamp if data else datetime.now(),
                                }
                            )
                if agent_assignments:
                    assignments[f"agent_{a}"] = agent_assignments

            # Calculate objective value
            shifts_per_agent = [len(assignments.get(f"agent_{a}", [])) for a in range(num_agents)]
            objective_value = (
                max(shifts_per_agent) - min(shifts_per_agent) if shifts_per_agent else 0
            )

            # Count number of variables and constraints from the model
            # Use a more compatible approach for OR-Tools
            num_variables = sum(
                1 for a in range(num_agents) for d in range(days) for s in range(shifts_per_day)
            )
            # Estimate constraints - this is approximate for testing
            num_constraints = (
                days * shifts_per_day * 2  # min/max agents
                + num_agents * (days - max_consecutive + 1) * shifts_per_day  # max consecutive
                + num_agents * (days - 1)  # min rest
                + num_agents
            )  # weekly hours estimate

            opt_result = OptimizationResult(
                optimizer="OR-Tools CP-SAT",
                objective_value=float(objective_value),
                solution={"assignments": assignments, "num_agents": num_agents},
                iterations=0,  # CP-SAT doesn't provide iteration count
                metadata={
                    "status": cp_model.CpSolver().StatusName(status),
                    "solve_time": solver.WallTime(),
                    "constraints_applied": list(constraints.keys()),
                    "requirements": requirements,
                },
            )

            self.last_solver = solver

            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="optimize",
                success=True,
                data=opt_result,
                metadata={
                    "solver_status": cp_model.CpSolver().StatusName(status),
                    "solve_time_seconds": solver.WallTime(),
                    "num_variables": num_variables,
                    "num_constraints": num_constraints,
                },
            )

        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="optimize",
                success=False,
                data=None,
                error_message=str(e),
            )

    def schedule(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """Generate schedules using OR-Tools CP-SAT solver.

        Creates shift schedules satisfying:
        - Coverage requirements
        - Agent preferences
        - Labor rules (rest periods, max hours, consecutive days)
        - Fairness objectives
        """
        try:
            if not has_ortools:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="schedule",
                    success=False,
                    data=None,
                    error_message="OR-Tools not installed",
                )

            if not data:
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="schedule",
                    success=False,
                    data=None,
                    error_message="No data provided for scheduling",
                )

            # Extract constraints from kwargs
            constraints = kwargs.get("constraints", {})
            shift_preferences = constraints.get("shift_preferences", {})

            # Parse data to determine scheduling horizon
            unique_dates = sorted(set(d.timestamp.date() for d in data))
            days = len(unique_dates)
            shifts_per_day = 3  # morning, afternoon, night

            # Determine number of agents from data or constraints
            num_agents = constraints.get("num_agents", 10)
            min_per_shift = constraints.get("min_agents_per_shift", 2)
            max_per_shift = constraints.get("max_agents_per_shift", 5)

            # Create CP-SAT model
            model = cp_model.CpModel()

            # Decision variables
            x = {}
            for a in range(num_agents):
                for d in range(days):
                    for s in range(shifts_per_day):
                        x[(a, d, s)] = model.NewBoolVar(f"sched_{a}_{d}_{s}")

            # Coverage constraints
            for d in range(days):
                for s in range(shifts_per_day):
                    shift_vars = [x[(a, d, s)] for a in range(num_agents)]
                    model.Add(sum(shift_vars) >= min_per_shift)
                    model.Add(sum(shift_vars) <= max_per_shift)

            # Agent preferences
            for agent_idx, prefs in shift_preferences.items():
                a = int(agent_idx.split("_")[-1]) if "_" in agent_idx else 0
                if a < num_agents:
                    for d in range(days):
                        for s in range(shifts_per_day):
                            if prefs and s not in prefs:
                                model.Add(x[(a, d, s)] == 0)

            # Labor constraints
            max_consecutive = constraints.get("max_consecutive_days", 5)
            for a in range(num_agents):
                for d in range(days - max_consecutive):
                    window = [
                        x[(a, d + i, s)]
                        for i in range(max_consecutive + 1)
                        for s in range(shifts_per_day)
                    ]
                    model.Add(sum(window) <= max_consecutive * shifts_per_day)

            min_rest = constraints.get("min_rest_hours", 12)
            if min_rest >= 12:
                for a in range(num_agents):
                    for d in range(days - 1):
                        # Simple constraint to prevent night followed by morning
                        model.Add(x[(a, d, 2)] + x[(a, d + 1, 0)] <= 1)

            max_weekly = constraints.get("max_weekly_hours", 40)
            for a in range(num_agents):
                weekly = [x[(a, d, s)] for d in range(days) for s in range(shifts_per_day)]
                model.Add(sum(weekly) * 8 <= max_weekly)

            # Days off constraints
            preferred_days_off = constraints.get("preferred_days_off", 2)
            for a in range(num_agents):
                # Use a simpler approach for days off constraint
                days_worked_vars = []
                for d in range(days):
                    day_vars = [x[(a, d, s)] for s in range(shifts_per_day)]
                    days_worked_vars.append(model.NewSumArray(day_vars))
                # Calculate days with no work
                for d in range(days):
                    # Simple linear constraint: days_off >= preferred_days_off
                    days_off_expr = cp_model.LinearExpr.Sum(
                        [1 for d in range(days) if days_worked_vars[d] == 0]
                    )
                    model.Add(days_off_expr >= preferred_days_off)

            # Objective: maximize preference satisfaction + fairness
            preference_bonuses = []
            for a in range(num_agents):
                for d in range(days):
                    for s in range(shifts_per_day):
                        agent_key = f"agent_{a}"
                        if agent_key in shift_preferences and s in shift_preferences[agent_key]:
                            preference_bonuses.append(x[(a, d, s)])

            if preference_bonuses:
                model.Maximize(sum(preference_bonuses))
            else:
                # Fairness: balance shifts
                agent_totals = [
                    sum(x[(a, d, s)] for d in range(days) for s in range(shifts_per_day))
                    for a in range(num_agents)
                ]
                max_var = model.NewIntVar(0, days * shifts_per_day, "max_sched")
                min_var = model.NewIntVar(0, days * shifts_per_day, "min_sched")
                model.AddMaxEquality(max_var, agent_totals)
                model.AddMinEquality(min_var, agent_totals)
                model.Minimize(max_var - min_var)

            # Solve
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = self.time_limit
            solver.parameters.num_search_workers = self.num_workers
            solver.parameters.log_search_progress = self.log_progress

            status = solver.Solve(model)

            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                return AdapterResult(
                    adapter_name=self.config.provider_name,
                    operation="schedule",
                    success=False,
                    data=None,
                    error_message=f"Scheduling failed: {cp_model.CpSolver().StatusName(status)}",
                )

            # Build roster
            roster = {}
            for a in range(num_agents):
                agent_shifts = []
                for d in range(days):
                    for s in range(shifts_per_day):
                        if solver.Value(x[(a, d, s)]) == 1:
                            shift_name = ["morning", "afternoon", "night"][s]
                            agent_shifts.append(
                                {
                                    "day": d,
                                    "date": str(unique_dates[d])
                                    if d < len(unique_dates)
                                    else f"day_{d}",
                                    "shift": shift_name,
                                    "start_hour": s * 8,
                                    "end_hour": (s + 1) * 8,
                                }
                            )
                if agent_shifts:
                    roster[f"agent_{a}"] = agent_shifts

            # Count satisfied constraints
            constraints_satisfied = 0
            # Coverage check
            for d in range(days):
                for s in range(shifts_per_day):
                    assigned = sum(1 for a in range(num_agents) if solver.Value(x[(a, d, s)]) == 1)
                    if min_per_shift <= assigned <= max_per_shift:
                        constraints_satisfied += 1

            sched_result = ScheduleResult(
                solver="OR-Tools CP-SAT",
                roster=roster,
                constraints_satisfied=constraints_satisfied,
                metadata={
                    "status": cp_model.CpSolver().StatusName(status),
                    "solve_time": solver.WallTime(),
                    "num_agents": num_agents,
                    "days": days,
                    "shifts_per_day": shifts_per_day,
                    "constraints_applied": list(constraints.keys()),
                },
            )

            self.last_solver = solver

            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="schedule",
                success=True,
                data=sched_result,
                metadata={
                    "solver_status": cp_model.CpSolver().StatusName(status),
                    "solve_time_seconds": solver.WallTime(),
                    "agents_scheduled": len(roster),
                    "constraints_satisfied": constraints_satisfied,
                },
            )

        except Exception as e:
            return AdapterResult(
                adapter_name=self.config.provider_name,
                operation="schedule",
                success=False,
                data=None,
                error_message=str(e),
            )

    def forecast(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """OR-Tools adapter - forecasting not supported."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="forecast",
            success=False,
            data=None,
            error_message="Not supported by OR-Tools",
        )

    def staff(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """OR-Tools adapter - staffing not supported."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="staff",
            success=False,
            data=None,
            error_message="Not supported by OR-Tools",
        )

    def validate(self, data: list[WFMData], **kwargs) -> AdapterResult:
        """OR-Tools adapter - validation not supported."""
        return AdapterResult(
            adapter_name=self.config.provider_name,
            operation="validate",
            success=False,
            data=None,
            error_message="Not supported by OR-Tools",
        )
