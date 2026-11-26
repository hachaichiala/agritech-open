"""
Pressure operating range and pressure checks
for pressure-compensating drip emitters.
"""

import math
from dataclasses import dataclass

from .dripline import (
    calculate_dripline_head_loss,
    calculate_pressure_at_each_emitter,
)


BAR_PER_METER_WATER = 0.0980665


def _is_positive_finite_number(value) -> bool:
    """Return whether value is a positive, finite int or float."""
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        return False

    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        return False


def _is_non_negative_finite_number(value) -> bool:
    """Return whether value is a non-negative, finite int or float."""
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        return False

    try:
        return math.isfinite(value) and value >= 0
    except OverflowError:
        return False


@dataclass(frozen=True)
class EmitterPressureRange:
    """Operating pressure limits in bar."""

    minimum_bar: float = 1.0
    maximum_bar: float = 4.0

    def __post_init__(self):
        if not _is_positive_finite_number(self.minimum_bar):
            raise ValueError(
                "Minimum pressure must be a positive finite number."
            )

        if not _is_positive_finite_number(self.maximum_bar):
            raise ValueError(
                "Maximum pressure must be a positive finite number."
            )

        if self.minimum_bar >= self.maximum_bar:
            raise ValueError(
                "Minimum pressure must be lower than maximum pressure."
            )


def is_pressure_in_compensation_range(
    pressure_bar: float,
    pressure_range: EmitterPressureRange,
) -> bool:
    """Check whether pressure is inside the PC operating range."""

    if not _is_positive_finite_number(pressure_bar):
        raise ValueError("Pressure must be a positive finite number.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    return (
        pressure_range.minimum_bar
        <= pressure_bar
        <= pressure_range.maximum_bar
    )


def check_dripline_pressure(
    inlet_pressure_bar: float,
    head_loss_m: float,
    pressure_range: EmitterPressureRange,
) -> dict:
    """
    Check inlet and outlet pressures against the PC range.

    uniform_compensation is retained for backward compatibility.
    It means both checked endpoint pressures are within the PC range.
    It is not a hydraulic distribution uniformity coefficient.
    """

    if not _is_positive_finite_number(inlet_pressure_bar):
        raise ValueError("Inlet pressure must be positive and finite.")

    if not _is_non_negative_finite_number(head_loss_m):
        raise ValueError("Head loss must be non-negative and finite.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    outlet_pressure_bar = (
        inlet_pressure_bar - head_loss_m * BAR_PER_METER_WATER
    )

    inlet_ok = is_pressure_in_compensation_range(
        inlet_pressure_bar, pressure_range
    )

    outlet_ok = (
        is_pressure_in_compensation_range(
            outlet_pressure_bar, pressure_range
        )
        if outlet_pressure_bar > 0
        else False
    )

    endpoints_within_range = inlet_ok and outlet_ok

    return {
        "inlet_pressure_bar": inlet_pressure_bar,
        "outlet_pressure_bar": outlet_pressure_bar,
        "inlet_within_range": inlet_ok,
        "outlet_within_range": outlet_ok,
        "all_checked_pressures_within_range": endpoints_within_range,
        "uniform_compensation": endpoints_within_range,
    }


def analyze_dripline_pressure(
    inlet_pressure_bar: float,
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    pressure_range: EmitterPressureRange,
    hazen_williams_c: float = 150,
) -> dict:
    """Calculate dripline head loss and check endpoint PC pressure limits."""

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    head_loss_m = calculate_dripline_head_loss(
        length_m=length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
    )

    result = check_dripline_pressure(
        inlet_pressure_bar=inlet_pressure_bar,
        head_loss_m=head_loss_m,
        pressure_range=pressure_range,
    )
    result["head_loss_m"] = head_loss_m

    return result


def analyze_emitter_pressure_distribution(
    emitter_pressures_bar: list,
    pressure_range: EmitterPressureRange,
) -> dict:
    """Analyze pressure distribution across all emitters."""

    if not isinstance(emitter_pressures_bar, list):
        raise ValueError("Emitter pressures must be a list.")

    if not emitter_pressures_bar:
        raise ValueError("Emitter pressure list cannot be empty.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    for pressure in emitter_pressures_bar:
        if not _is_positive_finite_number(pressure):
            raise ValueError(
                "All emitter pressures must be positive finite numbers."
            )

    pressures_within_range = [
        pressure_range.minimum_bar <= pressure <= pressure_range.maximum_bar
        for pressure in emitter_pressures_bar
    ]

    within_count = sum(pressures_within_range)
    total_count = len(emitter_pressures_bar)
    compliance_percentage = within_count / total_count * 100.0

    return {
        "total_emitters": total_count,
        "emitters_within_range": within_count,
        "emitters_outside_range": total_count - within_count,
        "minimum_pressure_bar": min(emitter_pressures_bar),
        "maximum_pressure_bar": max(emitter_pressures_bar),
        "all_emitters_within_range": within_count == total_count,
        "compliance_percentage": compliance_percentage,
    }


def analyze_dripline_emitter_pressures(
    inlet_pressure_bar: float,
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    pressure_range: EmitterPressureRange,
    hazen_williams_c: float = 150,
) -> dict:
    """
    Calculate and assess pressure at every emitter along a dripline.

    Emitters are assumed to be equally spaced on a horizontal lateral,
    matching calculate_pressure_at_each_emitter.
    """

    if not _is_positive_finite_number(inlet_pressure_bar):
        raise ValueError("Inlet pressure must be positive and finite.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    emitter_pressures_bar = calculate_pressure_at_each_emitter(
        inlet_pressure_bar=inlet_pressure_bar,
        length_m=length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
    )

    if any(pressure <= 0 for pressure in emitter_pressures_bar):
        raise ValueError(
            "Pressure reaches zero or below before the last emitter. "
            "Check inlet pressure, dripline dimensions, and emitter flow."
        )

    distribution = analyze_emitter_pressure_distribution(
        emitter_pressures_bar=emitter_pressures_bar,
        pressure_range=pressure_range,
    )

    head_loss_m = (
        inlet_pressure_bar - emitter_pressures_bar[-1]
    ) / BAR_PER_METER_WATER

    inlet_within_range = is_pressure_in_compensation_range(
        inlet_pressure_bar, pressure_range
    )

    return {
        "inlet_pressure_bar": inlet_pressure_bar,
        "outlet_pressure_bar": emitter_pressures_bar[-1],
        "head_loss_m": head_loss_m,
        "emitter_pressures_bar": emitter_pressures_bar,
        "inlet_within_range": inlet_within_range,
        **distribution,
        "all_pressures_within_range": (
            inlet_within_range
            and distribution["all_emitters_within_range"]
        ),
    }
