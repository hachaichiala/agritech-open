
"""
Unit conversion functions for irrigation hydraulic calculations.
"""

import math


def _validate_number(value: float, name: str) -> None:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        raise ValueError(f"{name} must be a finite number.")


def liters_per_hour_to_cubic_meters_per_second(
    flow_lph: float,
) -> float:
    """Convert flow from liters/hour to cubic meters/second."""
    _validate_number(flow_lph, "Flow rate")

    if flow_lph < 0:
        raise ValueError("Flow rate cannot be negative.")

    return flow_lph / 3_600_000


def cubic_meters_per_second_to_liters_per_hour(
    flow_m3_s: float,
) -> float:
    """Convert flow from cubic meters/second to liters/hour."""
    _validate_number(flow_m3_s, "Flow rate")

    if flow_m3_s < 0:
        raise ValueError("Flow rate cannot be negative.")

    return flow_m3_s * 3_600_000


def bar_to_meters_of_water(bar: float) -> float:
    """Convert pressure from bar to meters of water column."""
    _validate_number(bar, "Pressure")

    return bar * 100_000 / (1000 * 9.80665)


def meters_of_water_to_bar(meters: float) -> float:
    """Convert meters of water column to bar."""
    _validate_number(meters, "Water column")

    return meters * (1000 * 9.80665) / 100_000
