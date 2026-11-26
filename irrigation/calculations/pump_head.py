"""
Pump head calculations for irrigation systems.

The required sector inlet pressure is supplied by the downstream network
analysis. Upstream elevation, pipe friction, and local losses are added
to determine the required pump total dynamic head.
"""

import math

from .units import (
    bar_to_meters_of_water,
    liters_per_hour_to_cubic_meters_per_second,
)


def _is_finite_number(value):
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        return False

    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def calculate_required_pump_head(
    static_elevation_difference_m: float,
    required_sector_inlet_pressure_bar: float,
    upstream_friction_losses_m: float = 0.0,
    upstream_local_losses_m: float = 0.0,
) -> dict:
    """
    Calculate required pump head in meters of water column.

    Positive elevation difference means the sector inlet is higher than
    the source water level. The required pressure is specified at the
    sector manifold inlet, not at the pump.

    Friction and local losses cover only components upstream of the
    sector inlet. Manifold and lateral losses must not be added again.
    """
    if not _is_finite_number(static_elevation_difference_m):
        raise ValueError(
            "Static elevation difference must be a finite number."
        )

    if (
        not _is_finite_number(required_sector_inlet_pressure_bar)
        or required_sector_inlet_pressure_bar <= 0
    ):
        raise ValueError(
            "Required sector inlet pressure must be positive and finite."
        )

    for value, name in (
        (upstream_friction_losses_m, "Upstream friction losses"),
        (upstream_local_losses_m, "Upstream local losses"),
    ):
        if not _is_finite_number(value) or value < 0:
            raise ValueError(
                f"{name} must be a non-negative finite number."
            )

    pressure_head_m = bar_to_meters_of_water(
        required_sector_inlet_pressure_bar
    )
    total_head_m = (
        static_elevation_difference_m
        + pressure_head_m
        + upstream_friction_losses_m
        + upstream_local_losses_m
    )

    if not _is_finite_number(total_head_m) or total_head_m <= 0:
        raise ValueError(
            "Calculated required pump head must be positive and finite."
        )

    return {
        "static_elevation_difference_m": static_elevation_difference_m,
        "required_sector_inlet_pressure_bar": (
            required_sector_inlet_pressure_bar
        ),
        "pressure_head_m": pressure_head_m,
        "upstream_friction_losses_m": upstream_friction_losses_m,
        "upstream_local_losses_m": upstream_local_losses_m,
        "total_dynamic_head_m": total_head_m,
    }



def calculate_sector_pump_requirement(
    sector_analysis: dict,
    static_elevation_difference_m: float,
    upstream_friction_losses_m: float = 0.0,
    upstream_local_losses_m: float = 0.0,
) -> dict:
    """
    Combine an irrigation-sector analysis with upstream system losses.

    The sector analysis must contain total_flow_lph and inlet_pressure_bar.
    The latter is the required pressure at the sector manifold inlet.
    """
    if not isinstance(sector_analysis, dict):
        raise ValueError("Sector analysis must be a dictionary.")

    total_flow_lph = sector_analysis.get("total_flow_lph")
    inlet_pressure_bar = sector_analysis.get("inlet_pressure_bar")

    if not _is_finite_number(total_flow_lph) or total_flow_lph <= 0:
        raise ValueError(
            "Sector total flow must be positive and finite."
        )

    result = calculate_required_pump_head(
        static_elevation_difference_m=static_elevation_difference_m,
        required_sector_inlet_pressure_bar=inlet_pressure_bar,
        upstream_friction_losses_m=upstream_friction_losses_m,
        upstream_local_losses_m=upstream_local_losses_m,
    )
    result["sector_total_flow_lph"] = total_flow_lph
    result["sector_total_flow_m3_s"] = (
        liters_per_hour_to_cubic_meters_per_second(total_flow_lph)
    )
    return result
