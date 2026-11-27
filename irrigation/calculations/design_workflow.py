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
            "The sector model assumes equal laterals and a level, equally spaced manifold.",
            "The upstream system model represents one pipe and one combined local-loss coefficient.",
            "Pump and emitter curves must come from the selected manufacturers.",
            "The flow-match result is a screening comparison, not a field-performance guarantee.",
            "Filter, valve, suction, transient-pressure, and site elevation effects must be included when material.",
        ],
    }
