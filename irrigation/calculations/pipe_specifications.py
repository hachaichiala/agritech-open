"""Pipe geometry and pressure-rating checks.

Dimensions use metres. Pressures use bar. Pressure ratings must come from
the pipe manufacturer's data and reflect the operating temperature.
"""

import math


def _positive_finite(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a positive finite number.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{name} must be a positive finite number.") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be a positive finite number.")
    return number


def calculate_pipe_internal_diameter(
    outside_diameter_m: float,
    wall_thickness_m: float,
) -> float:
    """Calculate internal diameter from measured outside diameter and wall.

    The wall thickness is radial, so the calculation subtracts twice its value.
    """
    outside_diameter_m = _positive_finite(outside_diameter_m, "Outside diameter")
    wall_thickness_m = _positive_finite(wall_thickness_m, "Wall thickness")

    internal_diameter_m = outside_diameter_m - 2 * wall_thickness_m
    if not math.isfinite(internal_diameter_m) or internal_diameter_m <= 0:
        raise ValueError(
            "Wall thickness must be less than half the outside diameter."
        )
    return internal_diameter_m


def assess_pipe_pressure_rating(
    design_pressure_bar: float,
    rated_pressure_bar: float,
) -> dict:
    """Compare design pressure with the verified pipe pressure rating.

    design_pressure_bar must include the design allowance for transient
    pressure where water hammer is relevant. rated_pressure_bar must be the
    manufacturer's applicable rating at the actual service temperature.
    """
    design_pressure_bar = _positive_finite(design_pressure_bar, "Design pressure")
    rated_pressure_bar = _positive_finite(rated_pressure_bar, "Rated pressure")

    within_rating = design_pressure_bar <= rated_pressure_bar
    return {
        "design_pressure_bar": design_pressure_bar,
        "rated_pressure_bar": rated_pressure_bar,
        "pressure_margin_bar": rated_pressure_bar - design_pressure_bar,
        "within_rating": within_rating,
        "status": "within_rating" if within_rating else "exceeds_rating",
    }


def analyze_pipe_specification(
    outside_diameter_m: float,
    wall_thickness_m: float,
    design_pressure_bar: float,
    rated_pressure_bar: float,
    material: str,
) -> dict:
    """Combine pipe geometry and pressure-rating checks.

    Supply rated_pressure_bar from the manufacturer's data for the selected
    material, pipe series, nominal pressure class, and service temperature.
    """
    if not isinstance(material, str) or not material.strip():
        raise ValueError("Pipe material must be a non-empty string.")

    internal_diameter_m = calculate_pipe_internal_diameter(
        outside_diameter_m=outside_diameter_m,
        wall_thickness_m=wall_thickness_m,
    )
    pressure = assess_pipe_pressure_rating(
        design_pressure_bar=design_pressure_bar,
        rated_pressure_bar=rated_pressure_bar,
    )
    return {
        "material": material.strip(),
        "outside_diameter_m": outside_diameter_m,
        "wall_thickness_m": wall_thickness_m,
        "internal_diameter_m": internal_diameter_m,
        "design_pressure_bar": design_pressure_bar,
        "rated_pressure_bar": rated_pressure_bar,
        "pressure_check": pressure,
        "status": pressure["status"],
        "manufacturer_rating_required": True,
    }
