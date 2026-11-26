"""Pipe flow velocity calculation and configurable engineering screening."""

import math


def _positive_finite(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite positive number.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{name} must be a finite positive number.") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be a finite positive number.")
    return number


def calculate_pipe_velocity(flow_m3_s, internal_diameter_m):
    """Calculate mean full-pipe velocity from flow and internal diameter."""
    flow = _positive_finite(flow_m3_s, "Flow")
    diameter = _positive_finite(internal_diameter_m, "Internal pipe diameter")
    try:
        area = math.pi * diameter ** 2 / 4.0
    except OverflowError:
        raise ValueError(
            "Calculated pipe cross-sectional area must be finite and positive."
        ) from None
    if not math.isfinite(area) or area <= 0:
        raise ValueError(
            "Calculated pipe cross-sectional area must be finite and positive."
        )
    velocity = flow / area
    if not math.isfinite(velocity):
        raise ValueError("Calculated pipe velocity must be finite.")
    return {
        "flow_m3_s": flow,
        "internal_diameter_m": diameter,
        "cross_section_area_m2": area,
        "velocity_m_s": velocity,
    }


def assess_pipe_velocity(
    flow_m3_s,
    internal_diameter_m,
    minimum_velocity_m_s=0.6,
    maximum_velocity_m_s=1.5,
):
    """Classify velocity against user-configurable screening limits.

    The default limits are screening assumptions, not universal standards.
    Confirm project requirements, pipe material, water quality, and surge
    constraints before final design.
    """
    minimum = _positive_finite(minimum_velocity_m_s, "Minimum velocity")
    maximum = _positive_finite(maximum_velocity_m_s, "Maximum velocity")
    if minimum >= maximum:
        raise ValueError("Minimum velocity must be lower than maximum velocity.")

    result = calculate_pipe_velocity(flow_m3_s, internal_diameter_m)
    velocity = result["velocity_m_s"]
    if velocity < minimum:
        status = "below_minimum"
        assessment = "low_velocity"
    elif velocity > maximum:
        status = "above_maximum"
        assessment = "high_velocity"
    else:
        status = "within_range"
        assessment = "acceptable"

    return {
        **result,
        "minimum_velocity_m_s": minimum,
        "maximum_velocity_m_s": maximum,
        "status": status,
        "assessment": assessment,
        "limits_are_configurable_screening_values": True,
    }
