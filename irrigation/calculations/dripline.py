
"""
Pressure loss calculations for drip irrigation laterals.
"""

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
    Calculate total friction head loss along a dripline.

    Emitters are assumed to be uniformly spaced.
    Flow is assumed to decrease after each emitter.
    The pipe is assumed to be horizontal.

    Returns:
        Total friction head loss in meters of water column.
    """

    if (
        not isinstance(number_of_emitters, int)
        or isinstance(number_of_emitters, bool)
        or number_of_emitters <= 0
    ):
        raise ValueError("Number of emitters must be a positive integer.")

    total_length = length_m

    if total_length <= 0:
        raise ValueError("Length must be positive.")

    segment_length = total_length / number_of_emitters

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
