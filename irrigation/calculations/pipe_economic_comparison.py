"""
Economic comparison of upstream pipe diameters.

Pipe purchase cost and electricity cost are user-supplied. The model
excludes installation, maintenance, financing, taxes, and residual value.
Electrical energy cost requires an explicit motor efficiency.
"""

import math

from .pipe_diameter_comparison import compare_pipe_diameters


def _finite(value, name, allow_zero=False):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    try:
        converted = float(value)
    except (OverflowError, TypeError, ValueError):
        raise ValueError(f"{name} must be a finite number.") from None
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be a finite number.")
    if converted < 0 if allow_zero else converted <= 0:
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {qualifier}.")
    return converted


def _validate_pipe_costs(pipe_diameters_m, pipe_costs_tnd_per_m):
    if not isinstance(pipe_costs_tnd_per_m, (list, tuple)):
        raise ValueError("Pipe costs must be a list of diameter and unit-cost records.")

    costs = {}
    for item in pipe_costs_tnd_per_m:
        if not isinstance(item, dict):
            raise ValueError("Each pipe cost record must be a dictionary.")
        if set(item) != {"diameter_m", "cost_tnd_per_m"}:
            raise ValueError(
                "Each pipe cost record requires diameter_m and cost_tnd_per_m only."
            )
        diameter = _finite(item["diameter_m"], "Cost-record diameter")
        unit_cost = _finite(
            item["cost_tnd_per_m"], "Pipe unit cost", allow_zero=True
        )
        if diameter in costs:
            raise ValueError("Pipe cost diameters must be unique.")
        costs[diameter] = unit_cost

    requested = set(float(value) for value in pipe_diameters_m)
    if set(costs) != requested:
        raise ValueError(
            "Pipe cost records must match every requested diameter exactly."
        )
    return costs


def compare_pipe_diameter_economics(
    pump_data,
    system_curve_parameters,
    pipe_diameters_m,
    pipe_costs_tnd_per_m,
    electricity_cost_tnd_per_kwh,
    operating_hours_per_day,
    operating_days_per_year,
    analysis_period_years,
    motor_efficiency_percent,
    pump_efficiency_percent=None,
):
    """
    Compare pipe purchase and electricity costs over a stated period.

    Pipe unit costs are TND per meter. Pipe length comes from
    system_curve_parameters.upstream_pipe_length_m. Motor efficiency is
    required to calculate electrical input power and energy cost.
    """
    if not isinstance(system_curve_parameters, dict):
        raise ValueError("System curve parameters must be a dictionary.")
    if not isinstance(pipe_diameters_m, (list, tuple)) or len(pipe_diameters_m) < 2:
        raise ValueError("At least two pipe diameters are required.")
    if "upstream_pipe_length_m" not in system_curve_parameters:
        raise ValueError("Upstream pipe length is required for purchase cost.")

    electricity_price = _finite(
        electricity_cost_tnd_per_kwh,
        "Electricity cost",
        allow_zero=True,
    )
    hours_per_day = _finite(operating_hours_per_day, "Operating hours per day")
    days_per_year = _finite(operating_days_per_year, "Operating days per year")
    years = _finite(analysis_period_years, "Analysis period")
    motor_efficiency = _finite(
        motor_efficiency_percent, "Motor efficiency"
    )
    if hours_per_day > 24:
        raise ValueError("Operating hours per day cannot exceed 24.")
    if days_per_year > 366:
        raise ValueError("Operating days per year cannot exceed 366.")
    if motor_efficiency > 100:
        raise ValueError("Motor efficiency cannot exceed 100 percent.")
    if years > 100:
        raise ValueError("Analysis period cannot exceed 100 years.")

    pipe_length = _finite(
        system_curve_parameters["upstream_pipe_length_m"],
        "Upstream pipe length",
        allow_zero=True,
    )
    costs = _validate_pipe_costs(pipe_diameters_m, pipe_costs_tnd_per_m)

    hydraulic = compare_pipe_diameters(
        pump_data=pump_data,
        system_curve_parameters=system_curve_parameters,
        pipe_diameters_m=pipe_diameters_m,
        pump_efficiency_percent=pump_efficiency_percent,
        motor_efficiency_percent=motor_efficiency,
    )

    scenarios = []
    for scenario in hydraulic["scenarios"]:
        diameter = scenario["pipe_diameter_m"]
        if scenario["status"] != "success":
            scenarios.append({
                **scenario,
                "economic_status": "not_calculated",
            })
            continue

        pump_analysis = scenario["analysis"]["pump_analysis"]
        electrical_power_w = pump_analysis["power"]["electrical_input_power_w"]
        if electrical_power_w is None:
            raise ValueError(
                "Electrical input power is required for energy cost calculation."
            )

        electrical_power_kw = electrical_power_w / 1000.0
        energy_kwh_per_day = electrical_power_kw * hours_per_day
        energy_kwh_per_year = energy_kwh_per_day * days_per_year
        energy_kwh_over_period = energy_kwh_per_year * years
        pipe_purchase_cost = costs[diameter] * pipe_length
        energy_cost_over_period = energy_kwh_over_period * electricity_price
        total_cost = pipe_purchase_cost + energy_cost_over_period

        scenarios.append({
            **scenario,
            "economic_status": "calculated",
            "economics": {
                "pipe_unit_cost_tnd_per_m": costs[diameter],
                "pipe_length_m": pipe_length,
                "pipe_purchase_cost_tnd": pipe_purchase_cost,
                "electrical_input_power_kw": electrical_power_kw,
                "energy_kwh_per_day": energy_kwh_per_day,
                "energy_kwh_per_year": energy_kwh_per_year,
                "energy_kwh_over_period": energy_kwh_over_period,
                "energy_cost_over_period_tnd": energy_cost_over_period,
                "total_cost_over_period_tnd": total_cost,
            },
        })

    feasible = [
        item for item in scenarios
        if item["economic_status"] == "calculated"
    ]
    recommendation = None
    if feasible:
        best = min(
            feasible,
            key=lambda item: item["economics"]["total_cost_over_period_tnd"],
        )
        recommendation = {
            "pipe_diameter_m": best["pipe_diameter_m"],
            "total_cost_over_period_tnd": (
                best["economics"]["total_cost_over_period_tnd"]
            ),
            "basis": "lowest_calculated_pipe_purchase_plus_energy_cost",
        }

    return {
        "scenarios": scenarios,
        "recommendation": recommendation,
        "economic_inputs": {
            "electricity_cost_tnd_per_kwh": electricity_price,
            "operating_hours_per_day": hours_per_day,
            "operating_days_per_year": days_per_year,
            "analysis_period_years": years,
            "motor_efficiency_percent": motor_efficiency,
            "pipe_length_m": pipe_length,
        },
        "method": "pipe_purchase_cost_plus_electricity_cost_over_analysis_period",
        "exclusions": [
            "Installation and excavation costs.",
            "Maintenance and repair costs.",
            "Financing, taxes, and residual pipe value.",
            "Changes in electricity tariffs over the analysis period.",
        ],
    }
