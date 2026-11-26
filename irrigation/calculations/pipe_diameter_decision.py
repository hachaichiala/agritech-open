"""Integrated hydraulic and economic decision support for pipe diameters."""

from .pipe_economic_comparison import compare_pipe_diameter_economics
from .pipe_diameter_payback import analyze_pipe_diameter_payback
from .pipe_economic_sensitivity import analyze_pipe_economic_sensitivity
from .pipe_lifecycle_cost import analyze_pipe_lifecycle_cost


def analyze_pipe_diameter_decision(
    pump_data,
    system_curve_parameters,
    pipe_diameters_m,
    pipe_costs_tnd_per_m,
    electricity_cost_tnd_per_kwh,
    operating_hours_per_day,
    operating_days_per_year,
    analysis_period_years,
    motor_efficiency_percent,
    discount_rate_percent,
    installation_cost_tnd_per_m=0.0,
    annual_maintenance_cost_tnd_per_m=0.0,
    electricity_price_escalation_percent=0.0,
    replacement_interval_years=None,
    replacement_cost_fraction=1.0,
    residual_value_fraction=0.0,
    pump_efficiency_percent=None,
    sensitivity_cases=None,
):
    """Run hydraulic, operating, economic, payback, and life-cycle analyses.

    The hydraulic and economic comparison is the shared source for the
    downstream payback and life-cycle calculations. Sensitivity analysis
    is optional because it requires a separately defined set of cases.
    """
    economic = compare_pipe_diameter_economics(
        pump_data=pump_data,
        system_curve_parameters=system_curve_parameters,
        pipe_diameters_m=pipe_diameters_m,
        pipe_costs_tnd_per_m=pipe_costs_tnd_per_m,
        electricity_cost_tnd_per_kwh=electricity_cost_tnd_per_kwh,
        operating_hours_per_day=operating_hours_per_day,
        operating_days_per_year=operating_days_per_year,
        analysis_period_years=analysis_period_years,
        motor_efficiency_percent=motor_efficiency_percent,
        pump_efficiency_percent=pump_efficiency_percent,
    )

    lifecycle = analyze_pipe_lifecycle_cost(
        economic_comparison=economic,
        discount_rate_percent=discount_rate_percent,
        installation_cost_tnd_per_m=installation_cost_tnd_per_m,
        annual_maintenance_cost_tnd_per_m=annual_maintenance_cost_tnd_per_m,
        electricity_price_escalation_percent=electricity_price_escalation_percent,
        replacement_interval_years=replacement_interval_years,
        replacement_cost_fraction=replacement_cost_fraction,
        residual_value_fraction=residual_value_fraction,
    )

    successful = [
        item for item in economic["scenarios"]
        if item["economic_status"] == "calculated"
    ]
    if len(successful) >= 2:
        payback = analyze_pipe_diameter_payback(economic)
    else:
        payback = {
            "comparisons": [],
            "comparison_count": 0,
            "status": "insufficient_successful_hydraulic_scenarios",
        }

    sensitivity = None
    if sensitivity_cases is not None:
        sensitivity = analyze_pipe_economic_sensitivity(
            pump_data=pump_data,
            system_curve_parameters=system_curve_parameters,
            pipe_diameters_m=pipe_diameters_m,
            pipe_costs_tnd_per_m=pipe_costs_tnd_per_m,
            electricity_cost_tnd_per_kwh=electricity_cost_tnd_per_kwh,
            operating_hours_per_day=operating_hours_per_day,
            operating_days_per_year=operating_days_per_year,
            analysis_period_years=analysis_period_years,
            motor_efficiency_percent=motor_efficiency_percent,
            sensitivity_cases=sensitivity_cases,
            pump_efficiency_percent=pump_efficiency_percent,
        )

    recommended = lifecycle["recommendation"]
    recommended_diameter = (
        recommended["pipe_diameter_m"] if recommended else None
    )
    selected = next(
        (
            item for item in economic["scenarios"]
            if item["pipe_diameter_m"] == recommended_diameter
            and item["economic_status"] == "calculated"
        ),
        None,
    )

    missing_data = []
    if pump_efficiency_percent is None and not pump_data.get("efficiency_curve"):
        missing_data.append("Measured pump efficiency or manufacturer efficiency curve.")
    if not pump_data.get("rated_motor_power_kw"):
        missing_data.append("Verified motor rated output power.")
    if installation_cost_tnd_per_m == 0:
        missing_data.append("Actual pipe installation and excavation cost.")
    if annual_maintenance_cost_tnd_per_m == 0:
        missing_data.append("Expected annual pipe maintenance cost.")
    if sensitivity is None:
        missing_data.append("Defined sensitivity cases for uncertainty testing.")

    return {
        "recommendation": {
            "pipe_diameter_m": recommended_diameter,
            "net_present_life_cycle_cost_tnd": (
                recommended["net_present_life_cycle_cost_tnd"]
                if recommended else None
            ),
            "basis": "lowest_net_present_life_cycle_cost",
            "status": "recommended" if recommended else "no_feasible_diameter",
        },
        "selected_hydraulic_result": selected,
        "hydraulic_and_economic_comparison": economic,
        "payback_analysis": payback,
        "life_cycle_analysis": lifecycle,
        "sensitivity_analysis": sensitivity,
        "decision_notes": [
            "Only diameters with a valid pump operating point enter economic ranking.",
            "The recommendation minimizes modeled net present life-cycle cost.",
            "The recommendation depends on user-supplied pump, pipe, tariff, and cost data.",
            "A recommendation is not a substitute for checking pressure ratings, water velocity, water hammer, and manufacturer limits.",
        ],
        "missing_or_unverified_inputs": missing_data,
        "method": "integrated_hydraulic_economic_payback_sensitivity_and_life_cycle_decision",
    }
