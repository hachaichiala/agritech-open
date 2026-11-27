"""
End-to-end design workflow for a drip-irrigation sector and its pump.

This module orchestrates existing calculation modules. It does not introduce
new hydraulic equations or replace manufacturer pump/emitter data.
"""

import math

from .emitter_pressure import EmitterPressureRange
from .irrigation_sector import analyze_irrigation_sector
from .operating_analysis import analyze_pump_system


def design_drip_irrigation_system(
    sector_parameters,
    upstream_system_parameters,
    pump_data,
    pressure_range,
    pump_efficiency_percent=None,
    motor_efficiency_percent=None,
    flow_match_tolerance_percent=5.0,
):
    """
    Run a complete sector, system-curve, pump operating-point workflow.

    sector_parameters:
        Keyword arguments for analyze_irrigation_sector, excluding
        pressure_range, which is supplied separately.

    upstream_system_parameters:
        Keyword arguments for build_system_curve, excluding
        required_sector_inlet_pressure_bar and flow_rates_m3_s.
        flow_rates_m3_s is required and defines the curve sampling range.

    The sector inlet pressure from the sector analysis is passed to the
    system-curve calculation. The sector design flow is inserted into the
    requested system-curve flow points so the curve includes the exact
    hydraulic design duty.

    The function reports whether all emitters meet the configured pressure
    range and whether the pump operating flow is close to the sector design
    flow. A successful intersection alone does not establish field suitability.
    """
    if not isinstance(sector_parameters, dict):
        raise ValueError("Sector parameters must be a dictionary.")
    if not isinstance(upstream_system_parameters, dict):
        raise ValueError("Upstream system parameters must be a dictionary.")
    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("A valid emitter pressure range is required.")
    if not isinstance(pump_data, dict):
        raise ValueError("Pump data must be a dictionary.")

    if "pressure_range" in sector_parameters:
        raise ValueError(
            "Pass pressure_range separately, not inside sector_parameters."
        )

    raw_flow_points = upstream_system_parameters.get("flow_rates_m3_s")
    if not isinstance(raw_flow_points, (list, tuple)) or len(raw_flow_points) < 2:
        raise ValueError(
            "Upstream parameters must include at least two flow-rate points."
        )

    design_tolerance = (
        flow_match_tolerance_percent
        if isinstance(flow_match_tolerance_percent, (int, float))
        and not isinstance(flow_match_tolerance_percent, bool)
        else None
    )
    if design_tolerance is None:
        raise ValueError("Flow-match tolerance must be a finite number.")
    try:
        design_tolerance = float(design_tolerance)
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Flow-match tolerance must be a finite number.") from None
    if not math.isfinite(design_tolerance) or not 0 <= design_tolerance < 100:
        raise ValueError(
            "Flow-match tolerance must be from 0 inclusive to 100 exclusive."
        )

    sector = analyze_irrigation_sector(
        **sector_parameters,
        pressure_range=pressure_range,
    )
    design_flow_m3_s = sector["total_flow_lph"] / 3_600_000.0
    if not math.isfinite(design_flow_m3_s) or design_flow_m3_s <= 0:
        raise ValueError("Calculated sector design flow must be positive and finite.")

    normalized_flow_points = []
    for value in raw_flow_points:
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
        ):
            raise ValueError("System-curve flow points must be finite numbers.")
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("System-curve flow points must be finite numbers.") from None
        if not math.isfinite(value) or value < 0:
            raise ValueError(
                "System-curve flow points must be non-negative and finite."
            )
        normalized_flow_points.append(value)

    curve_flow_points = sorted(set(normalized_flow_points + [design_flow_m3_s]))
    if len(curve_flow_points) < 2:
        raise ValueError(
            "At least two distinct system-curve flow points are required."
        )

    system_parameters = {
        key: value
        for key, value in upstream_system_parameters.items()
        if key != "flow_rates_m3_s"
    }
    system_parameters.update({
        "flow_rates_m3_s": curve_flow_points,
        "required_sector_inlet_pressure_bar": sector["inlet_pressure_bar"],
    })

    pump_result = analyze_pump_system(
        pump_data=pump_data,
        system_curve_parameters=system_parameters,
        pump_efficiency_percent=pump_efficiency_percent,
        motor_efficiency_percent=motor_efficiency_percent,
    )

    operating_flow_m3_s = pump_result["pump_analysis"]["operating_point"]["flow_m3_s"]
    flow_difference_percent = (
        abs(operating_flow_m3_s - design_flow_m3_s)
        / design_flow_m3_s
        * 100.0
    )

    return {
        "sector_analysis": sector,
        "pump_system_analysis": pump_result,
        "design_duty": {
            "sector_design_flow_lph": sector["total_flow_lph"],
            "sector_design_flow_m3_s": design_flow_m3_s,
            "operating_flow_m3_s": operating_flow_m3_s,
            "flow_difference_percent": flow_difference_percent,
            "flow_match_tolerance_percent": design_tolerance,
            "operating_flow_matches_sector_design": (
                flow_difference_percent <= design_tolerance
            ),
            "all_emitters_within_pressure_range": (
                sector["all_emitters_within_range"]
            ),
        },
        "method": "integrated_sector_system_curve_and_pump_operating_analysis",
        "limitations": [
            "The sector model assumes equal laterals and equally spaced manifold takeoffs. Optional elevation profiles account for static level changes along the manifold and laterals.",
            "The upstream system model represents one pipe and one combined local-loss coefficient.",
            "Pump and emitter curves must come from the selected manufacturers.",
            "The flow-match result is a screening comparison, not a field-performance guarantee.",
            "Filter, valve, suction, and transient-pressure losses must be included when material. Static elevations within the sector belong in the sector elevation profiles, while source-to-sector elevation belongs in the upstream system parameters.",
        ],
    }

def design_irrigation_sectors(
    sectors,
    upstream_system_parameters,
    pump_data,
    pressure_range,
    pump_efficiency_percent=None,
    motor_efficiency_percent=None,
    flow_match_tolerance_percent=5.0,
):
    """
    Analyze multiple irrigation sectors as independent sequential operations.

    Each item in sectors is a dictionary with a unique non-empty "name"
    and a "sector_parameters" dictionary accepted by
    analyze_irrigation_sector. Shared upstream and pump data are evaluated
    separately for every sector. This function does not model simultaneous
    sector operation or shared-header flow between active sectors.
    """
    if not isinstance(sectors, (list, tuple)) or not sectors:
        raise ValueError("Sectors must be a non-empty list or tuple.")

    names = set()
    results = []
    for index, item in enumerate(sectors, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Sector {index} must be a dictionary.")
        name = item.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Sector {index} must have a non-empty name.")
        if name in names:
            raise ValueError(f"Duplicate sector name: {name}.")
        names.add(name)
        parameters = item.get("sector_parameters")
        if not isinstance(parameters, dict):
            raise ValueError(
                f"Sector '{name}' must include a sector_parameters dictionary."
            )

        analysis = design_drip_irrigation_system(
            sector_parameters=parameters,
            upstream_system_parameters=upstream_system_parameters,
            pump_data=pump_data,
            pressure_range=pressure_range,
            pump_efficiency_percent=pump_efficiency_percent,
            motor_efficiency_percent=motor_efficiency_percent,
            flow_match_tolerance_percent=flow_match_tolerance_percent,
        )
        results.append({
            "name": name,
            "analysis": analysis,
        })

    return {
        "operation_mode": "sequential_independent_sector_analysis",
        "sector_count": len(results),
        "sectors": results,
        "summary": {
            "sectors_meeting_flow_match": sum(
                item["analysis"]["design_duty"][
                    "operating_flow_matches_sector_design"
                ]
                for item in results
            ),
            "sectors_with_all_emitters_in_pressure_range": sum(
                item["analysis"]["design_duty"][
                    "all_emitters_within_pressure_range"
                ]
                for item in results
            ),
            "maximum_sector_design_flow_lph": max(
                item["analysis"]["design_duty"]["sector_design_flow_lph"]
                for item in results
            ),
        },
    }

def schedule_irrigation_sectors(
    sector_design,
    daily_water_requirements_l,
    available_runtime_hours_per_day,
):
    """
    Convert daily sector water volumes into sequential operating times.

    The sector_design argument must be the result of
    design_irrigation_sectors. Daily water requirements are supplied
    explicitly in litres per sector. This function does not estimate crop
    water demand or account for irrigation efficiency.
    """
    if not isinstance(sector_design, dict):
        raise ValueError("Sector design must be a dictionary.")
    sectors = sector_design.get("sectors")
    if not isinstance(sectors, list) or not sectors:
        raise ValueError("Sector design must contain a non-empty sectors list.")
    if not isinstance(daily_water_requirements_l, dict):
        raise ValueError("Daily water requirements must be a dictionary.")

    if (
        not isinstance(available_runtime_hours_per_day, (int, float))
        or isinstance(available_runtime_hours_per_day, bool)
        or not math.isfinite(available_runtime_hours_per_day)
        or available_runtime_hours_per_day <= 0
    ):
        raise ValueError("Available daily runtime must be positive and finite.")

    sector_names = [item.get("name") for item in sectors if isinstance(item, dict)]
    if len(sector_names) != len(sectors) or any(
        not isinstance(name, str) or not name.strip() for name in sector_names
    ):
        raise ValueError("Every designed sector must have a non-empty name.")
    if len(set(sector_names)) != len(sector_names):
        raise ValueError("Designed sector names must be unique.")
    if set(daily_water_requirements_l) != set(sector_names):
        raise ValueError(
            "Daily water requirements must match the designed sector names exactly."
        )

    schedule = []
    total_volume_l = 0.0
    total_runtime_hours = 0.0
    for item in sectors:
        name = item["name"]
        requirement = daily_water_requirements_l[name]
        if (
            not isinstance(requirement, (int, float))
            or isinstance(requirement, bool)
            or not math.isfinite(requirement)
            or requirement < 0
        ):
            raise ValueError(
                f"Daily water requirement for sector '{name}' must be finite and non-negative."
            )

        try:
            flow_lph = float(
                item["analysis"]["design_duty"]["sector_design_flow_lph"]
            )
        except (KeyError, TypeError, ValueError, OverflowError):
            raise ValueError(
                f"Sector '{name}' is missing a valid design flow."
            ) from None
        if not math.isfinite(flow_lph) or flow_lph <= 0:
            raise ValueError(
                f"Sector '{name}' design flow must be positive and finite."
            )

        volume_l = float(requirement)
        runtime_hours = volume_l / flow_lph
        total_volume_l += volume_l
        total_runtime_hours += runtime_hours
        schedule.append({
            "name": name,
            "daily_water_requirement_l": volume_l,
            "design_flow_lph": flow_lph,
            "runtime_hours": runtime_hours,
            "runtime_minutes": runtime_hours * 60.0,
        })

    available_hours = float(available_runtime_hours_per_day)
    return {
        "operation_mode": "sequential_daily_irrigation_schedule",
        "sectors": schedule,
        "summary": {
            "total_daily_water_requirement_l": total_volume_l,
            "total_runtime_hours": total_runtime_hours,
            "total_runtime_minutes": total_runtime_hours * 60.0,
            "available_runtime_hours_per_day": available_hours,
            "remaining_runtime_hours": available_hours - total_runtime_hours,
            "fits_available_runtime": total_runtime_hours <= available_hours,
        },
        "limitations": [
            "Daily water requirements are user-supplied and are not estimated from crop or climate data.",
            "Runtime is calculated from sector design flow and assumes the sector operates at that flow.",
            "Sectors are scheduled sequentially. Simultaneous operation is not modeled.",
            "Application efficiency, refill constraints, and soil-water storage are not included.",
        ],
    }

