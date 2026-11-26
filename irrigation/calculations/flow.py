"""
Flow rate calculations for drip irrigation networks.
"""

import math


def _is_finite_number(value) -> bool:
    """Return whether value is a finite int or float, excluding booleans."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False

    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def calculate_total_flow(
    number_of_drippers: int,
    flow_per_dripper_lph: float
) -> float:
    """
    Calculate total irrigation flow in liters per hour.

    Raises:
        ValueError: If an input or the calculated result is invalid.
    """
    if (
        not isinstance(number_of_drippers, int)
        or isinstance(number_of_drippers, bool)
    ):
        raise ValueError("Number of drippers must be an integer.")

    if number_of_drippers <= 0:
        raise ValueError("Number of drippers must be positive.")

    if not _is_finite_number(flow_per_dripper_lph):
        raise ValueError("Dripper flow rate must be a finite number.")

    if flow_per_dripper_lph <= 0:
        raise ValueError("Dripper flow rate must be positive.")

    try:
        total_flow_lph = number_of_drippers * flow_per_dripper_lph
    except OverflowError as exc:
        raise ValueError("Calculated total flow must be finite.") from exc

    if not _is_finite_number(total_flow_lph):
        raise ValueError("Calculated total flow must be finite.")

    return total_flow_lph
