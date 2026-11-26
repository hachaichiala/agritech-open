
"""
Pressure loss calculations for drip irrigation laterals.
"""

import math

from .pressure_loss import calculate_hazen_williams_head_loss
from .units import liters_per_hour_to_cubic_meters_per_second


def calculate_dripline_head_loss(
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
) -> float:
    """
    Calculate friction head loss along a dripline.

    Emitters are uniformly spaced.
    Each segment ends at an emitter.
    Flow decreases after each emitter.

    Returns:
        Total head loss in meters of water column.
    """

    if (
        not isinstance(length_m, (int, float))
        or isinstance(length_m, bool)
        or not math.isfinite(length_m)
        or length_m <= 0
    ):
        raise ValueError("Length must be a positive finite number.")

    if (
        not isinstance(number_of_emitters, int)
        or isinstance(number_of_emitters, bool)
        or number_of_emitters <= 0
    ):
        raise ValueError("Number of emitters must be a positive integer.")

    if (
        not isinstance(emitter_flow_lph, (int, float))
        or isinstance(emitter_flow_lph, bool)
        or not math.isfinite(emitter_flow_lph)
        or emitter_flow_lph <= 0
    ):
        raise ValueError("Emitter flow must be a positive finite number.")

    segment_length = length_m / number_of_emitters
    total_head_loss = 0.0

    for index in range(number_of_emitters):
        remaining_emitters = number_of_emitters - index
        flow_lph = remaining_emitters * emitter_flow_lph

        flow_m3_s = liters_per_hour_to_cubic_meters_per_second(
            flow_lph
        )

        segment_loss = calculate_hazen_williams_head_loss(
            length_m=segment_length,
            flow_m3_s=flow_m3_s,
            diameter_m=diameter_m,
            hazen_williams_c=hazen_williams_c,
        )

        total_head_loss += segment_loss

    return total_head_loss

def calculate_dripline_segment_head_losses(
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
) -> list:
    """
    Calculate head loss for each dripline segment.

    Emitters are uniformly spaced.
    Each segment ends at an emitter.
    Flow decreases after each emitter.

    Returns:
        List of head losses in meters of water column.
    """

    if (
        not isinstance(length_m, (int, float))
        or isinstance(length_m, bool)
        or not math.isfinite(length_m)
        or length_m <= 0
    ):
        raise ValueError("Length must be a positive finite number.")

    if (
        not isinstance(number_of_emitters, int)
        or isinstance(number_of_emitters, bool)
        or number_of_emitters <= 0
    ):
        raise ValueError("Number of emitters must be a positive integer.")

    if (
        not isinstance(emitter_flow_lph, (int, float))
        or isinstance(emitter_flow_lph, bool)
        or not math.isfinite(emitter_flow_lph)
        or emitter_flow_lph <= 0
    ):
        raise ValueError("Emitter flow must be a positive finite number.")

    segment_length = length_m / number_of_emitters
    segment_losses = []

    for index in range(number_of_emitters):
        remaining_emitters = number_of_emitters - index

        flow_lph = remaining_emitters * emitter_flow_lph

        flow_m3_s = liters_per_hour_to_cubic_meters_per_second(
            flow_lph
        )

        segment_loss = calculate_hazen_williams_head_loss(
            length_m=segment_length,
            flow_m3_s=flow_m3_s,
            diameter_m=diameter_m,
            hazen_williams_c=hazen_williams_c,
        )

        segment_losses.append(segment_loss)

    return segment_losses

def calculate_pressure_at_each_emitter(
    inlet_pressure_bar: float,
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
) -> list:
    """
    Calculate pressure at each emitter along a horizontal dripline.

    Pressure is calculated cumulatively from the inlet.
    Each emitter is located at the end of an equal-length segment.

    Returns:
        List of emitter pressures in bar.
    """

    if (
        not isinstance(inlet_pressure_bar, (int, float))
        or isinstance(inlet_pressure_bar, bool)
        or not math.isfinite(inlet_pressure_bar)
        or inlet_pressure_bar <= 0
    ):
        raise ValueError(
            "Inlet pressure must be a positive finite number."
        )

    segment_losses = calculate_dripline_segment_head_losses(
        length_m=length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
    )

    pressures = []
    cumulative_loss_m = 0.0

    for segment_loss_m in segment_losses:
        cumulative_loss_m += segment_loss_m

        pressure_loss_bar = cumulative_loss_m * 0.0980665

        emitter_pressure_bar = (
            inlet_pressure_bar - pressure_loss_bar
        )

        pressures.append(emitter_pressure_bar)

    return pressures
