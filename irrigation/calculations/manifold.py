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
from .units import (
    liters_per_hour_to_cubic_meters_per_second,
    meters_of_water_to_bar,
)


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
    try:
        finite_total_flow = math.isfinite(total_flow_lph)
    except OverflowError:
        finite_total_flow = False

    if not finite_total_flow:
        raise ValueError("Calculated manifold flow must be finite.")

    return total_flow_lph


def calculate_manifold_segment_head_losses(
    length_m: float,
    number_of_laterals: int,
    lateral_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
) -> list:
    """
    Return friction head loss for each equal manifold segment, in meters.

    The first segment carries the flow for all laterals. Flow decreases
    after each takeoff, so the final segment carries one lateral flow.
    """
    _validate_positive_finite(length_m, "Manifold length")
    _validate_lateral_count(number_of_laterals)
    _validate_positive_finite(lateral_flow_lph, "Lateral flow rate")
    _validate_positive_finite(diameter_m, "Manifold diameter")
    _validate_positive_finite(hazen_williams_c, "Hazen-Williams coefficient")

    segment_length_m = length_m / number_of_laterals
    segment_losses_m = []

    for index in range(number_of_laterals):
        remaining_laterals = number_of_laterals - index
        segment_flow_lph = remaining_laterals * lateral_flow_lph

        try:
            finite_segment_flow = math.isfinite(segment_flow_lph)
        except OverflowError:
            finite_segment_flow = False

        if not finite_segment_flow:
            raise ValueError("Calculated manifold segment flow must be finite.")

        segment_flow_m3_s = liters_per_hour_to_cubic_meters_per_second(
            segment_flow_lph
        )

        segment_loss_m = calculate_hazen_williams_head_loss(
            length_m=segment_length_m,
            flow_m3_s=segment_flow_m3_s,
            diameter_m=diameter_m,
            hazen_williams_c=hazen_williams_c,
        )
        segment_losses_m.append(segment_loss_m)

    return segment_losses_m


def calculate_manifold_head_loss(
    length_m: float,
    number_of_laterals: int,
    lateral_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
) -> float:
    """
    Calculate total manifold friction loss in meters of water column.

    The manifold is divided into equal segments. The first segment carries
    the flow for all laterals, and flow decreases after each takeoff.
    """
    segment_losses_m = calculate_manifold_segment_head_losses(
        length_m=length_m,
        number_of_laterals=number_of_laterals,
        lateral_flow_lph=lateral_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
    )

    total_head_loss_m = sum(segment_losses_m)

    if not math.isfinite(total_head_loss_m):
        raise ValueError("Calculated manifold head loss must be finite.")

    return total_head_loss_m



def calculate_pressure_at_each_lateral_takeoff(
    inlet_pressure_bar: float,
    length_m: float,
    number_of_laterals: int,
    lateral_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
) -> list:
    """
    Calculate pressure at each lateral takeoff, in bar.

    Each returned pressure includes cumulative manifold friction losses
    from the manifold inlet to that lateral takeoff.
    """
    _validate_positive_finite(inlet_pressure_bar, "Manifold inlet pressure")

    segment_losses_m = calculate_manifold_segment_head_losses(
        length_m=length_m,
        number_of_laterals=number_of_laterals,
        lateral_flow_lph=lateral_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
    )

    pressures_bar = []
    cumulative_loss_m = 0.0

    for segment_loss_m in segment_losses_m:
        cumulative_loss_m += segment_loss_m
        pressure_loss_bar = meters_of_water_to_bar(cumulative_loss_m)
        takeoff_pressure_bar = inlet_pressure_bar - pressure_loss_bar

        if not math.isfinite(takeoff_pressure_bar) or takeoff_pressure_bar <= 0:
            raise ValueError(
                "Manifold pressure reaches zero or below at a lateral takeoff. "
                "Increase inlet pressure or reduce manifold friction losses."
            )

        pressures_bar.append(takeoff_pressure_bar)

    return pressures_bar
