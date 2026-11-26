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


def calculate_minor_head_loss(
    flow_m3_s: float,
    diameter_m: float,
    loss_coefficient: float,
    gravity_m_s2: float = 9.80665,
) -> float:
    """
    Calculate local fitting loss using h_m = K * V^2 / (2g).

    Flow is the flow immediately upstream of the fitting.
    K is specific to the fitting geometry and flow conditions.
    """
    flow_m3_s = _finite_number(flow_m3_s, "Flow rate")
    diameter_m = _finite_number(diameter_m, "Diameter")
    loss_coefficient = _finite_number(
        loss_coefficient, "Local loss coefficient"
    )
    gravity_m_s2 = _finite_number(gravity_m_s2, "Gravity")

    if flow_m3_s < 0:
        raise ValueError("Flow rate cannot be negative.")
    if diameter_m <= 0:
        raise ValueError("Diameter must be positive.")
    if loss_coefficient < 0:
        raise ValueError("Local loss coefficient cannot be negative.")
    if gravity_m_s2 <= 0:
        raise ValueError("Gravity must be positive.")
    if flow_m3_s == 0 or loss_coefficient == 0:
        return 0.0

    area_m2 = math.pi * diameter_m ** 2 / 4.0
    velocity_m_s = flow_m3_s / area_m2
    try:
        head_loss_m = (
            loss_coefficient * velocity_m_s ** 2
            / (2.0 * gravity_m_s2)
        )
    except (OverflowError, ZeroDivisionError):
        raise ValueError(
            "Calculated local head loss must be a finite number."
        ) from None

    if not math.isfinite(head_loss_m):
        raise ValueError(
            "Calculated local head loss must be a finite number."
        )
    return head_loss_m
