
"""
Pressure operating range and pressure checks
for pressure-compensating drip emitters.
"""

import math
from dataclasses import dataclass

from .dripline import calculate_dripline_head_loss


@dataclass(frozen=True)
class EmitterPressureRange:
    """Operating pressure limits in bar."""

    minimum_bar: float = 1.0
    maximum_bar: float = 4.0

    def __post_init__(self):
        for name, value in (
            ("Minimum pressure", self.minimum_bar),
            ("Maximum pressure", self.maximum_bar),
        ):
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                or value <= 0
            ):
                raise ValueError(
                    f"{name} must be a positive finite number."
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

    if (
        not isinstance(pressure_bar, (int, float))
        or isinstance(pressure_bar, bool)
        or not math.isfinite(pressure_bar)
    ):
        raise ValueError("Pressure must be a finite number.")

    if pressure_bar <= 0:
        raise ValueError("Pressure must be positive.")

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
    """Check inlet and outlet pressures against the PC range."""

    if (
        not isinstance(inlet_pressure_bar, (int, float))
        or isinstance(inlet_pressure_bar, bool)
        or not math.isfinite(inlet_pressure_bar)
        or inlet_pressure_bar <= 0
    ):
        raise ValueError("Inlet pressure must be positive and finite.")

    if (
        not isinstance(head_loss_m, (int, float))
        or isinstance(head_loss_m, bool)
        or not math.isfinite(head_loss_m)
        or head_loss_m < 0
    ):
        raise ValueError("Head loss must be non-negative and finite.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    outlet_pressure_bar = (
        inlet_pressure_bar - head_loss_m * 0.0980665
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

    return {
        "inlet_pressure_bar": inlet_pressure_bar,
        "outlet_pressure_bar": outlet_pressure_bar,
        "inlet_within_range": inlet_ok,
        "outlet_within_range": outlet_ok,
        "uniform_compensation": inlet_ok and outlet_ok,
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
    """
    Calculate dripline head loss and check PC pressure limits.

    Assumptions:
    - Horizontal dripline.
    - Uniform emitter spacing.
    - Constant emitter discharge.
    - Constant internal pipe diameter.
    """

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
