"""Life-cycle cost analysis for alternative irrigation pipe diameters."""

import math


def _number(value, name, allow_zero=True, allow_negative=False):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    if not allow_negative and (number < 0 if allow_zero else number <= 0):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{name} must be {qualifier}.")
    return number


def analyze_pipe_lifecycle_cost(
    economic_comparison,
    discount_rate_percent,
    installation_cost_tnd_per_m=0.0,
    annual_maintenance_cost_tnd_per_m=0.0,
    electricity_price_escalation_percent=0.0,
    replacement_interval_years=None,
    replacement_cost_fraction=1.0,
    residual_value_fraction=0.0,
):
    """Calculate discounted life-cycle costs for each successful pipe scenario.

    Energy cost in the supplied economic comparison is treated as a level
    annual baseline. Escalation applies from year two onward. Installation
    is paid at year zero, maintenance is paid annually, and optional pipe
    replacement occurs at each stated interval. Residual value is credited
    at the end of the analysis period as a fraction of original pipe cost.
    """
    if not isinstance(economic_comparison, dict):
        raise ValueError("Economic comparison must be a dictionary.")
    scenarios = economic_comparison.get("scenarios")
    inputs = economic_comparison.get("economic_inputs")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("At least one economic scenario is required.")
    if not isinstance(inputs, dict):
        raise ValueError("Economic inputs are required.")

    years_value = inputs.get("analysis_period_years")
    years = _number(years_value, "Analysis period", allow_zero=False)
    if not years.is_integer() or years > 100:
        raise ValueError("Analysis period must be a whole number from 1 to 100 years.")
    years = int(years)

    discount = _number(discount_rate_percent, "Discount rate") / 100.0
    installation_rate = _number(
        installation_cost_tnd_per_m, "Installation cost per meter"
    )
    maintenance_rate = _number(
        annual_maintenance_cost_tnd_per_m, "Annual maintenance cost per meter"
    )
    escalation = _number(
        electricity_price_escalation_percent,
        "Electricity price escalation",
        allow_negative=True,
    ) / 100.0
    if escalation <= -1:
        raise ValueError("Electricity price escalation must be greater than -100 percent.")

    replacement_fraction = _number(
        replacement_cost_fraction, "Replacement cost fraction"
    )
    residual_fraction = _number(
        residual_value_fraction, "Residual value fraction"
    )
    if replacement_fraction > 1 or residual_fraction > 1:
        raise ValueError("Replacement and residual fractions cannot exceed 1.")

    if replacement_interval_years is not None:
        if (
            not isinstance(replacement_interval_years, int)
            or isinstance(replacement_interval_years, bool)
            or replacement_interval_years <= 0
            or replacement_interval_years >= years
        ):
            raise ValueError(
                "Replacement interval must be a positive whole number shorter than the analysis period."
            )

    results = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("Each economic scenario must be a dictionary.")
        if scenario.get("economic_status") != "calculated":
            results.append({
                "pipe_diameter_m": scenario.get("pipe_diameter_m"),
                "status": "not_calculated",
            })
            continue

        economics = scenario.get("economics")
        if not isinstance(economics, dict):
            raise ValueError("Calculated scenarios require economics data.")
        diameter = _number(scenario.get("pipe_diameter_m"), "Pipe diameter", allow_zero=False)
        pipe_cost = _number(
            economics.get("pipe_purchase_cost_tnd"), "Pipe purchase cost"
        )
        annual_energy = _number(
            economics.get("energy_cost_over_period_tnd"), "Energy cost over period"
        ) / years
        pipe_length = _number(
            economics.get("pipe_length_m"), "Pipe length"
        )

        installation_cost = installation_rate * pipe_length
        initial_cost = pipe_cost + installation_cost
        maintenance_per_year = maintenance_rate * pipe_length
        discounted_energy = 0.0
        discounted_maintenance = 0.0
        discounted_replacements = 0.0
        yearly_cash_flows = []

        for year in range(1, years + 1):
            energy_cost = annual_energy * ((1.0 + escalation) ** (year - 1))
            discount_factor = (1.0 + discount) ** year
            maintenance_cost = maintenance_per_year
            replacement_cost = 0.0
            if (
                replacement_interval_years is not None
                and year % replacement_interval_years == 0
            ):
                replacement_cost = pipe_cost * replacement_fraction
                discounted_replacements += replacement_cost / discount_factor
            discounted_energy += energy_cost / discount_factor
            discounted_maintenance += maintenance_cost / discount_factor
            yearly_cash_flows.append({
                "year": year,
                "energy_cost_tnd": energy_cost,
                "maintenance_cost_tnd": maintenance_cost,
                "replacement_cost_tnd": replacement_cost,
                "discount_factor": discount_factor,
            })

        residual_value = pipe_cost * residual_fraction
        discounted_residual = residual_value / ((1.0 + discount) ** years)
        npv = (
            initial_cost
            + discounted_energy
            + discounted_maintenance
            + discounted_replacements
            - discounted_residual
        )
        undiscounted = (
            initial_cost
            + sum(item["energy_cost_tnd"] for item in yearly_cash_flows)
            + maintenance_per_year * years
            + sum(item["replacement_cost_tnd"] for item in yearly_cash_flows)
            - residual_value
        )
        results.append({
            "pipe_diameter_m": diameter,
            "status": "calculated",
            "costs": {
                "pipe_purchase_cost_tnd": pipe_cost,
                "installation_cost_tnd": installation_cost,
                "initial_cost_tnd": initial_cost,
                "annual_energy_cost_tnd_year_1": annual_energy,
                "discounted_energy_cost_tnd": discounted_energy,
                "discounted_maintenance_cost_tnd": discounted_maintenance,
                "discounted_replacement_cost_tnd": discounted_replacements,
                "residual_value_tnd": residual_value,
                "discounted_residual_value_tnd": discounted_residual,
                "net_present_life_cycle_cost_tnd": npv,
                "undiscounted_life_cycle_cost_tnd": undiscounted,
            },
            "yearly_cash_flows": yearly_cash_flows,
        })

    feasible = [item for item in results if item["status"] == "calculated"]
    best = min(
        feasible,
        key=lambda item: item["costs"]["net_present_life_cycle_cost_tnd"],
    ) if feasible else None

    return {
        "scenarios": results,
        "recommendation": {
            "pipe_diameter_m": best["pipe_diameter_m"],
            "net_present_life_cycle_cost_tnd": (
                best["costs"]["net_present_life_cycle_cost_tnd"]
            ),
            "basis": "lowest_net_present_life_cycle_cost",
        } if best else None,
        "inputs": {
            "analysis_period_years": years,
            "discount_rate_percent": discount * 100.0,
            "installation_cost_tnd_per_m": installation_rate,
            "annual_maintenance_cost_tnd_per_m": maintenance_rate,
            "electricity_price_escalation_percent": escalation * 100.0,
            "replacement_interval_years": replacement_interval_years,
            "replacement_cost_fraction": replacement_fraction,
            "residual_value_fraction": residual_fraction,
        },
        "method": "discounted_life_cycle_cost",
        "assumptions": [
            "The supplied annual energy cost is the year-one baseline.",
            "Electricity price escalation starts in year two.",
            "Installation cost occurs at year zero.",
            "Maintenance occurs at each year-end.",
            "Replacement cost is a fraction of original pipe purchase cost.",
            "Residual value is credited at the end of the analysis period.",
            "Discount rate and operating conditions follow the supplied assumptions.",
        ],
        "exclusions": [
            "Taxes, financing fees, and working capital.",
            "Unspecified pump replacement or major equipment renewal.",
            "Inflation in maintenance and installation costs.",
            "Changes in hydraulic performance caused by pipe aging or deposits.",
        ],
    }
