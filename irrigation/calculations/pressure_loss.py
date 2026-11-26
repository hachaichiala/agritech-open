"""
Hydraulic head loss calculations using the Hazen-Williams equation.
"""

import math


def _finite_number(value, name):
    """Convert a real numeric input to float and reject invalid values."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{name} must be a finite number.") from None
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    return number


def calculate_hazen_williams_head_loss(
    length_m: float,
    flow_m3_s: float,
    diameter_m: float,
    hazen_williams_c: float
) -> float:
    """
    Calculate friction head loss using the Hazen-Williams equation.

    SI units:
        Length: meters
        Flow: cubic meters per second
        Diameter: meters
        Head loss: meters of water column
    """
    length_m = _finite_number(length_m, "Length")
    flow_m3_s = _finite_number(flow_m3_s, "Flow rate")
    diameter_m = _finite_number(diameter_m, "Diameter")
    hazen_williams_c = _finite_number(
        hazen_williams_c, "Hazen-Williams coefficient"
    )

    if length_m < 0:
        raise ValueError("Length cannot be negative.")

    if flow_m3_s < 0:
        raise ValueError("Flow rate cannot be negative.")

    if diameter_m <= 0:
        raise ValueError("Diameter must be positive.")

    if hazen_williams_c <= 0:
        raise ValueError("Hazen-Williams coefficient must be positive.")

    if length_m == 0 or flow_m3_s == 0:
        return 0.0

    try:
        head_loss = (
            10.67
            * length_m
            * (flow_m3_s ** 1.852)
            / (
                (hazen_williams_c ** 1.852)
                * (diameter_m ** 4.871)
            )
        )
    except (OverflowError, ZeroDivisionError):
        raise ValueError(
            "Calculated head loss must be a finite number."
        ) from None

    if not math.isfinite(head_loss):
        raise ValueError(
            "Calculated head loss must be a finite number."
        )

    return head_loss
