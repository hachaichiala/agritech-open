"""Sensitivity analysis for pipe diameter economic comparisons."""

from .pipe_economic_comparison import compare_pipe_diameter_economics

_ALLOWED_OVERRIDES = {
    "pipe_costs_tnd_per_m",
    "electricity_cost_tnd_per_kwh",
    "operating_hours_per_day",
    "operating_days_per_year",
    "analysis_period_years",
    "motor_efficiency_percent",
    "pump_efficiency_percent",
}


def analyze_pipe_economic_sensitivity(
    pump_data, system_curve_parameters, pipe_diameters_m,
    pipe_costs_tnd_per_m, electricity_cost_tnd_per_kwh,
    operating_hours_per_day, operating_days_per_year, analysis_period_years,
    motor_efficiency_percent, sensitivity_cases, pump_efficiency_percent=None,
):
    """Evaluate named economic scenarios while holding hydraulics fixed."""
    if not isinstance(sensitivity_cases, (list, tuple)) or not sensitivity_cases:
        raise ValueError("At least one sensitivity case is required.")

    baseline = {
        "pump_data": pump_data,
        "system_curve_parameters": system_curve_parameters,
        "pipe_diameters_m": pipe_diameters_m,
        "pipe_costs_tnd_per_m": pipe_costs_tnd_per_m,
        "electricity_cost_tnd_per_kwh": electricity_cost_tnd_per_kwh,
        "operating_hours_per_day": operating_hours_per_day,
        "operating_days_per_year": operating_days_per_year,
        "analysis_period_years": analysis_period_years,
        "motor_efficiency_percent": motor_efficiency_percent,
        "pump_efficiency_percent": pump_efficiency_percent,
    }
    results = []
    names = set()
    for case in sensitivity_cases:
        if not isinstance(case, dict) or set(case) != {"name", "overrides"}:
            raise ValueError("Each case requires name and overrides only.")
        name, overrides = case["name"], case["overrides"]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Sensitivity case name must be a non-empty string.")
        if name in names:
            raise ValueError("Sensitivity case names must be unique.")
        names.add(name)
        if not isinstance(overrides, dict):
            raise ValueError("Case overrides must be a dictionary.")
        unknown = set(overrides) - _ALLOWED_OVERRIDES
        if unknown:
            raise ValueError("Unsupported sensitivity override(s): " + ", ".join(sorted(unknown)))
        comparison = compare_pipe_diameter_economics(**{**baseline, **overrides})
        recommendation = comparison["recommendation"]
        results.append({
            "name": name,
            "overrides": dict(overrides),
            "comparison": comparison,
            "recommended_diameter_m": recommendation["pipe_diameter_m"] if recommendation else None,
        })

    winners = [item["recommended_diameter_m"] for item in results if item["recommended_diameter_m"] is not None]
    counts = {}
    for diameter in winners:
        counts[diameter] = counts.get(diameter, 0) + 1
    stable = bool(winners) and len(counts) == 1
    return {
        "cases": results,
        "case_count": len(results),
        "successful_case_count": len(winners),
        "recommendation_counts": counts,
        "stable_recommended_diameter_m": winners[0] if stable else None,
        "recommendation_is_stable": stable,
        "method": "named_scenario_comparison_with_fixed_hydraulic_inputs",
        "limitations": [
            "Each case is evaluated independently against the supplied baseline.",
            "Hydraulic geometry and pump data remain fixed across cases.",
            "Results depend on user-supplied scenario values.",
            "No probability or statistical confidence is assigned to scenarios.",
        ],
    }
