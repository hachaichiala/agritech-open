"""
Check whether a pump meets the design duty of an irrigation sector.

The check compares pump head available at the sector design flow with
the total dynamic head required by that sector. It does not replace a
full pump/system-curve operating-point analysis.
"""

import math

from .pump_data import validate_pump_data
from .pump_head import calculate_sector_pump_requirement


def _pump_head_at_flow(pump_curve, flow_m3_s):
    if flow_m3_s < pump_curve[0][0] or flow_m3_s > pump_curve[-1][0]:
        raise ValueError(
            "Sector design flow lies outside the supplied pump curve."
        )

    for (flow_a, head_a), (flow_b, head_b) in zip(
        pump_curve, pump_curve[1:]
    ):
        if flow_a <= flow_m3_s <= flow_b:
            fraction = (flow_m3_s - flow_a) / (flow_b - flow_a)
            return head_a + fraction * (head_b - head_a)

    raise ValueError("Unable to evaluate pump head at sector design flow.")


def analyze_sector_pump_compatibility(
    pump_data,
    sector_analysis,
    static_elevation_difference_m,
    upstream_friction_losses_m=0.0,
    upstream_local_losses_m=0.0,
):
    """
    Compare pump head with the head required by one irrigation sector.

    The sector flow is taken from sector_analysis.total_flow_lph.
    Required head includes sector inlet pressure, elevation difference,
    and upstream friction and local losses.
    Pump head is linearly interpolated at the exact design flow.
    No extrapolation is performed.
    """
    pump = validate_pump_data(pump_data)
    requirement = calculate_sector_pump_requirement(
        sector_analysis=sector_analysis,
        static_elevation_difference_m=static_elevation_difference_m,
        upstream_friction_losses_m=upstream_friction_losses_m,
        upstream_local_losses_m=upstream_local_losses_m,
    )

    available_head_m = _pump_head_at_flow(
        pump["pump_curve"],
        requirement["sector_total_flow_m3_s"],
    )
    required_head_m = requirement["total_dynamic_head_m"]
    margin_m = available_head_m - required_head_m

    if not math.isfinite(margin_m):
        raise ValueError("Calculated pump head margin must be finite.")

    return {
        "sector_total_flow_lph": requirement["sector_total_flow_lph"],
        "sector_total_flow_m3_s": requirement["sector_total_flow_m3_s"],
        "required_total_dynamic_head_m": required_head_m,
        "available_pump_head_m": available_head_m,
        "head_margin_m": margin_m,
        "pump_meets_design_duty": margin_m >= 0,
        "method": "pump_head_interpolation_at_sector_design_flow",
        "warning": (
            "Design-duty check only. Confirm the actual operating point "
            "with the complete system curve."
        ),
    }
