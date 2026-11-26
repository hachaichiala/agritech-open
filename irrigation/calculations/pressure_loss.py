"""
Hydraulic head loss calculations using the Hazen-Williams equation.
"""

import math


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

    inputs = {
        "Length": length_m,
        "Flow rate": flow_m3_s,
        "Diameter": diameter_m,
        "Hazen-Williams coefficient": hazen_williams_c,
    }

    for name, value in inputs.items():
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
        ):
            raise ValueError(f"{name} must be a finite number.")

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
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError(
            "Calculated head loss must be a finite number."
        ) from exc

    if not math.isfinite(head_loss):
        raise ValueError(
            "Calculated head loss must be a finite number."
        )

    return head_loss
