"""
Hydraulic calculations for a manifold supplying parallel drip laterals.

Assumptions:
- Laterals are equally spaced along a straight, level manifold.
- Each lateral withdraws the same flow rate.
- Each manifold segment ends at one lateral takeoff.
- Flow decreases after each takeoff.
"""

import math

from .pressure_loss import calculate_hazen_williams_head_loss
from .units import liters_per_hour_to_cubic_meters_per_second


def _validate_positive_finite(value, name):
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        raise ValueError(f"{name} must be a positive finite number.")

    try:
        valid = math.isfinite(value) and value > 0
    except OverflowError:
        valid = False

    if not valid:
        raise ValueError(f"{name} must be a positive finite number.")


def _validate_lateral_count(number_of_laterals):
    if (
        not isinstance(number_of_laterals, int)
        or isinstance(number_of_laterals, bool)
        or number_of_laterals <= 0
    ):
        raise ValueError("Number of laterals must be a positive integer.")


def calculate_manifold_total_flow(
    number_of_laterals: int,
    lateral_flow_lph: float,
) -> float:
    """Return the total inlet flow required by parallel laterals, in L/h."""
    _validate_lateral_count(number_of_laterals)
    _validate_positive_finite(lateral_flow_lph, "Lateral flow rate")

    total_flow_lph = number_of_laterals * lateral_flow_lph
    if not math.isfinite(total_flow_lph):
        raise ValueError("Calculated manifold flow must be finite.")

    return total_flow_lph


def calculate_manifold_head_loss(
    length_m: float,
    number_of_laterals: int,
    lateral_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
) -> float:
    """
    Calculate manifold friction loss in meters of water column.

    The manifold is divided into equal segments. The first segment carries
    the flow for all laterals, and flow decreases after each takeoff.
    """
    _validate_positive_finite(length_m, "Manifold length")
    _validate_lateral_count(number_of_laterals)
    _validate_positive_finite(lateral_flow_lph, "Lateral flow rate")

    segment_length_m = length_m / number_of_laterals
    total_head_loss_m = 0.0

    for index in range(number_of_laterals):
        remaining_laterals = number_of_laterals - index
        segment_flow_lph = remaining_laterals * lateral_flow_lph
        segment_flow_m3_s = liters_per_hour_to_cubic_meters_per_second(
            segment_flow_lph
        )

        segment_loss_m = calculate_hazen_williams_head_loss(
            length_m=segment_length_m,
            flow_m3_s=segment_flow_m3_s,
            diameter_m=diameter_m,
            hazen_williams_c=hazen_williams_c,
        )
        total_head_loss_m += segment_loss_m

    if not math.isfinite(total_head_loss_m):
        raise ValueError("Calculated manifold head loss must be finite.")

    return total_head_loss_m
