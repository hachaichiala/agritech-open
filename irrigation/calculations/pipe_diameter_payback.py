"""Payback analysis for the additional purchase cost of larger pipes."""

import math


def _positive_number(value, name, allow_zero=False):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    if number < 0 if allow_zero else number <= 0:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {qualifier}.")
    return number


def analyze_pipe_diameter_payback(economic_comparison):
    """Compare every larger calculated diameter with every smaller one.

    Payback uses the incremental pipe purchase cost divided by annual
    electricity-cost savings. A larger pipe with no positive annual savings
    has no finite payback period.
    """
    if not isinstance(economic_comparison, dict):
        raise ValueError("Economic comparison must be a dictionary.")
    scenarios = economic_comparison.get("scenarios")
    if not isinstance(scenarios, list) or len(scenarios) < 2:
        raise ValueError("At least two economic scenarios are required.")

    inputs = economic_comparison.get("economic_inputs")
    if not isinstance(inputs, dict):
        raise ValueError("Economic inputs are required.")
    period = _positive_number(inputs.get("analysis_period_years"), "Analysis period")

    calculated = {}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("Each economic scenario must be a dictionary.")
        if scenario.get("economic_status") != "calculated":
            continue
        diameter = _positive_number(scenario.get("pipe_diameter_m"), "Pipe diameter")
        economics = scenario.get("economics")
        if not isinstance(economics, dict):
            raise ValueError("Calculated scenarios require economics data.")
        capex = _positive_number(economics.get("pipe_purchase_cost_tnd"), "Pipe purchase cost", allow_zero=True)
        annual_energy_cost = _positive_number(
            economics.get("energy_cost_over_period_tnd"), "Energy cost over period", allow_zero=True
        )
        annual_energy_cost /= period
        if diameter in calculated:
            raise ValueError("Economic scenarios must have unique pipe diameters.")
        calculated[diameter] = {
            "pipe_purchase_cost_tnd": capex,
            "annual_energy_cost_tnd": annual_energy_cost,
        }

    diameters = sorted(calculated)
    if len(diameters) < 2:
        raise ValueError("At least two successfully calculated diameters are required.")

    comparisons = []
    for smaller in diameters:
        for larger in diameters:
            if larger <= smaller:
                continue
            small = calculated[smaller]
            large = calculated[larger]
            extra_capital_cost = large["pipe_purchase_cost_tnd"] - small["pipe_purchase_cost_tnd"]
            annual_savings = small["annual_energy_cost_tnd"] - large["annual_energy_cost_tnd"]
            if extra_capital_cost <= 0:
                payback_years = 0.0
                status = "no_additional_capital_cost"
            elif annual_savings > 0:
                payback_years = extra_capital_cost / annual_savings
                status = "payback_available"
            else:
                payback_years = None
                status = "no_payback_from_energy_savings"
            comparisons.append({
                "smaller_diameter_m": smaller,
                "larger_diameter_m": larger,
                "extra_pipe_purchase_cost_tnd": extra_capital_cost,
                "annual_electricity_cost_savings_tnd": annual_savings,
                "payback_period_years": payback_years,
                "status": status,
            })

    return {
        "comparisons": comparisons,
        "comparison_count": len(comparisons),
        "method": "incremental_pipe_purchase_cost_divided_by_annual_electricity_cost_savings",
        "assumptions": [
            "Annual electricity cost equals period energy cost divided by analysis period.",
            "Operating conditions and electricity tariff stay constant.",
            "Installation, maintenance, financing, taxes, and residual value are excluded.",
            "A non-positive annual saving does not produce a finite payback period.",
        ],
    }
