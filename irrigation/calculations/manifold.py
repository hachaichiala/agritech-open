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

    try:
        total_flow_lph = number_of_laterals * lateral_flow_lph
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

    try:
        segment_length_m = length_m / number_of_laterals
    except OverflowError:
        raise ValueError(
            "Calculated manifold segment length must be finite."
        ) from None

    if not math.isfinite(segment_length_m) or segment_length_m <= 0:
        raise ValueError(
            "Calculated manifold segment length must be positive and finite."
        )

    segment_losses_m = []

    for index in range(number_of_laterals):
        remaining_laterals = number_of_laterals - index

        try:
            segment_flow_lph = remaining_laterals * lateral_flow_lph
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
    and the takeoff elevation relative to the manifold inlet. Positive
    elevations are uphill and reduce pressure.
    """
    _validate_positive_finite(inlet_pressure_bar, "Manifold inlet pressure")

    segment_losses_m = calculate_manifold_segment_head_losses(
        length_m=length_m,
        number_of_laterals=number_of_laterals,
        lateral_flow_lph=lateral_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
    )

    if takeoff_elevations_m is None:
        takeoff_elevations_m = [0.0] * number_of_laterals
    if (
        not isinstance(takeoff_elevations_m, (list, tuple))
        or len(takeoff_elevations_m) != number_of_laterals
    ):
        raise ValueError(
            "Lateral takeoff elevations must contain one value per lateral."
        )
    for elevation in takeoff_elevations_m:
        if (
            not isinstance(elevation, (int, float))
            or isinstance(elevation, bool)
            or not math.isfinite(elevation)
        ):
            raise ValueError(
                "Lateral takeoff elevations must be finite numbers."
            )

    pressures_bar = []
    cumulative_loss_m = 0.0

    for segment_loss_m, elevation_m in zip(
        segment_losses_m, takeoff_elevations_m
    ):
        cumulative_loss_m += segment_loss_m
        pressure_head_m = (
            inlet_pressure_bar / 0.0980665
            - cumulative_loss_m
            - elevation_m
        )
        takeoff_pressure_bar = pressure_head_m * 0.0980665

        if not math.isfinite(takeoff_pressure_bar) or takeoff_pressure_bar <= 0:
            raise ValueError(
                "Manifold pressure reaches zero or below at a lateral takeoff. "
                "Increase inlet pressure, reduce manifold friction losses, "
                "or review the elevation profile."
            )

        pressures_bar.append(takeoff_pressure_bar)

    return pressures_bar
