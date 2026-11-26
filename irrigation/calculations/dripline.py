
"""
Pressure loss calculations for drip irrigation laterals.
"""

import math

from .pressure_loss import (\n    calculate_hazen_williams_head_loss,\n    calculate_minor_head_loss,\n)
from .units import liters_per_hour_to_cubic_meters_per_second


def calculate_dripline_head_loss(
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
    emitter_connection_k: float = 0.0,
) -> float:
    """
    Calculate friction and emitter-connection local losses.

    Emitters are uniformly spaced. Each segment ends at one emitter.
    One connection loss is applied at each segment end, using the
    segment's upstream flow and lateral velocity. K is geometry-specific.

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

    segment_losses = calculate_dripline_segment_head_losses(
        length_m=length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
        emitter_connection_k=emitter_connection_k,
    )
    return sum(segment_losses)

def calculate_dripline_segment_head_losses(
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
    emitter_connection_k: float = 0.0,
) -> list:
    """
    Calculate friction plus one emitter-connection loss per segment.

    Emitters are uniformly spaced. Each segment ends at one emitter.
    Connection K is applied once at that segment's downstream end,
    using the flow and velocity immediately upstream of the connection.

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

    if (
        not isinstance(emitter_connection_k, (int, float))
        or isinstance(emitter_connection_k, bool)
        or not math.isfinite(emitter_connection_k)
        or emitter_connection_k < 0
    ):
        raise ValueError(
            "Emitter connection K must be a non-negative finite number."
        )

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

        connection_loss = calculate_minor_head_loss(
            flow_m3_s=flow_m3_s,
            diameter_m=diameter_m,
            loss_coefficient=emitter_connection_k,
        )
        segment_losses.append(segment_loss + connection_loss)

    return segment_losses

def calculate_pressure_at_each_emitter(
    inlet_pressure_bar: float,
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
    emitter_connection_k: float = 0.0,
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
        emitter_connection_k=emitter_connection_k,
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
