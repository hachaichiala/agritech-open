"""Integrated hydraulic and economic decision support for pipe diameters."""

import math

from .pipe_economic_comparison import compare_pipe_diameter_economics
from .pipe_diameter_payback import analyze_pipe_diameter_payback
from .pipe_economic_sensitivity import analyze_pipe_economic_sensitivity
from .pipe_lifecycle_cost import analyze_pipe_lifecycle_cost
from .pipe_velocity import assess_pipe_velocity
from .pipe_specifications import analyze_pipe_specification


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
    minimum_velocity_m_s=0.6,
    maximum_velocity_m_s=1.5,
    pipe_specifications=None,
):
    """Run hydraulic, operating, economic, payback, and life-cycle analyses.

    The hydraulic and economic comparison is the shared source for the
    downstream payback and life-cycle calculations. Sensitivity analysis
    is optional because it requires a separately defined set of cases.
    """
    specifications_by_diameter = {}
    if pipe_specifications is not None:
        if not isinstance(pipe_specifications, (list, tuple)):
            raise ValueError("Pipe specifications must be a list of manufacturer records.")
        for record in pipe_specifications:
            if not isinstance(record, dict):
                raise ValueError("Each pipe specification must be a dictionary.")
            required = {
                "pipe_diameter_m", "outside_diameter_m", "wall_thickness_m",
                "design_pressure_bar", "rated_pressure_bar", "material",
            }
            if set(record) != required:
                raise ValueError(
                    "Each pipe specification requires pipe_diameter_m, outside_diameter_m, "
                    "wall_thickness_m, design_pressure_bar, rated_pressure_bar, and material."
                )
            identifier = record["pipe_diameter_m"]
            if identifier in specifications_by_diameter:
                raise ValueError("Pipe specification diameters must be unique.")
            checked = analyze_pipe_specification(
                outside_diameter_m=record["outside_diameter_m"],
                wall_thickness_m=record["wall_thickness_m"],
                design_pressure_bar=record["design_pressure_bar"],
                rated_pressure_bar=record["rated_pressure_bar"],
                material=record["material"],
            )
            if not math.isclose(
                float(identifier), checked["internal_diameter_m"],
                rel_tol=1e-7, abs_tol=1e-9,
            ):
                raise ValueError(
                    "pipe_diameter_m must equal the calculated manufacturer internal diameter."
                )
            specifications_by_diameter[identifier] = checked
        if set(specifications_by_diameter) != set(pipe_diameters_m):
            raise ValueError(
                "Pipe specifications must cover every candidate internal diameter exactly."
            )

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

    lifecycle_by_diameter = {
        item["pipe_diameter_m"]: item
        for item in lifecycle["scenarios"]
        if item.get("status") == "calculated"
    }
    velocity_assessments = []
    pressure_assessments = []
    eligible_lifecycle = []
    for scenario in economic["scenarios"]:
        diameter = scenario["pipe_diameter_m"]
        if scenario["economic_status"] != "calculated":
            velocity_assessments.append({
                "pipe_diameter_m": diameter,
                "status": "not_calculated",
                "assessment": "hydraulic_analysis_unavailable",
            })
            continue
        specification = specifications_by_diameter.get(diameter)
        if pipe_specifications is None:
            pressure_result = {
                "status": "not_provided",
                "within_rating": None,
                "assessment": "manufacturer_pressure_rating_not_verified",
            }
            internal_diameter = diameter
        else:
            pressure_result = {
                **specification["pressure_check"],
                "status": specification["pressure_check"]["status"],
                "internal_diameter_m": specification["internal_diameter_m"],
                "material": specification["material"],
            }
            internal_diameter = specification["internal_diameter_m"]
        pressure_assessments.append({
            "pipe_diameter_m": diameter,
            **pressure_result,
        })
        operating_flow = scenario["analysis"]["pump_analysis"]["operating_point"]["flow_m3_s"]
        velocity_result = assess_pipe_velocity(
            flow_m3_s=operating_flow,
            internal_diameter_m=internal_diameter,
            minimum_velocity_m_s=minimum_velocity_m_s,
            maximum_velocity_m_s=maximum_velocity_m_s,
        )
        velocity_assessments.append({
            "pipe_diameter_m": diameter,
            **velocity_result,
        })
        pressure_eligible = (
            pipe_specifications is None
            or pressure_result["within_rating"] is True
        )
        if velocity_result["status"] == "within_range" and pressure_eligible:
            life = lifecycle_by_diameter.get(diameter)
            if life is not None:
                eligible_lifecycle.append(life)

    best_lifecycle = min(
        eligible_lifecycle,
        key=lambda item: item["costs"]["net_present_life_cycle_cost_tnd"],
    ) if eligible_lifecycle else None
    recommended_diameter = (
        best_lifecycle["pipe_diameter_m"] if best_lifecycle else None
    )
    pressure_compliant_count = sum(
        1 for item in pressure_assessments
        if item.get("within_rating") is True
    )
    recommendation = {
        "pipe_diameter_m": recommended_diameter,
        "net_present_life_cycle_cost_tnd": (
            best_lifecycle["costs"]["net_present_life_cycle_cost_tnd"]
            if best_lifecycle else None
        ),
        "basis": "lowest_net_present_life_cycle_cost_among_velocity_acceptable_diameters",
        "status": (
    "recommended" if best_lifecycle else
    "no_feasible_diameter" if not successful else
    "no_pressure_compliant_diameter" if pipe_specifications is not None and pressure_compliant_count == 0 else
    "no_velocity_acceptable_diameter" if not eligible_lifecycle else
    "no_feasible_lifecycle_cost"
),
        "velocity_limits_m_s": {
            "minimum": minimum_velocity_m_s,
            "maximum": maximum_velocity_m_s,
        },
    }
    selected = next(
        (
            item for item in economic["scenarios"]
            if item["pipe_diameter_m"] == recommended_diameter
            and item["economic_status"] == "calculated"
        ),
        None,
    )

    missing_data = []
    if pipe_specifications is None:
        missing_data.append("Manufacturer pipe dimensions and pressure ratings were not supplied; pressure suitability is unverified.")
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
    if minimum_velocity_m_s == 0.6 and maximum_velocity_m_s == 1.5:
        missing_data.append("Confirm project-specific minimum and maximum pipe velocity limits.")

    return {
        "recommendation": recommendation,
        "velocity_assessments": velocity_assessments,
        "pressure_assessments": pressure_assessments,
        "pipe_specifications_verified": pipe_specifications is not None,
        "selected_hydraulic_result": selected,
        "hydraulic_and_economic_comparison": economic,
        "payback_analysis": payback,
        "life_cycle_analysis": lifecycle,
        "sensitivity_analysis": sensitivity,
        "decision_notes": [
            "Only diameters with a valid pump operating point enter economic ranking.",
            "The recommendation minimizes modeled net present life-cycle cost among alternatives within the configured velocity range.",
            "Velocity limits are configurable screening values, not universal regulatory limits.",
            "Economic sensitivity cases do not replace the velocity eligibility check applied to the baseline recommendation.",
            "The recommendation depends on user-supplied pump, pipe, tariff, and cost data.",
            "A recommendation is not a substitute for checking pressure ratings, water velocity, water hammer, and manufacturer limits.",
            "When manufacturer pipe specifications are supplied, only pressure-compliant candidates are eligible for recommendation; candidate diameters must match calculated internal diameters.",
            "Without manufacturer pipe specifications, pressure suitability is unverified and the legacy diameter-only recommendation path is retained for compatibility.",
        ],
        "missing_or_unverified_inputs": missing_data,
        "method": "integrated_hydraulic_economic_payback_sensitivity_and_life_cycle_decision",
    }
