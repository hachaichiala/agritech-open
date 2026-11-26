
"""
Pressure operating range for pressure-compensating emitters.
"""

from dataclasses import dataclass


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
                or value <= 0
            ):
                raise ValueError(
                    f"{name} must be a positive number."
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
    ):
        raise ValueError("Pressure must be numeric.")

    if pressure_bar <= 0:
        raise ValueError("Pressure must be positive.")

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

    Assumes a horizontal pipe and water density of 1000 kg/m³.
    """

    if (
        not isinstance(inlet_pressure_bar, (int, float))
        or isinstance(inlet_pressure_bar, bool)
        or inlet_pressure_bar <= 0
    ):
        raise ValueError("Inlet pressure must be positive.")

    if (
        not isinstance(head_loss_m, (int, float))
        or isinstance(head_loss_m, bool)
        or head_loss_m < 0
    ):
        raise ValueError("Head loss must be non-negative.")

    outlet_pressure_bar = (
        inlet_pressure_bar - head_loss_m * 0.0980665
    )

    return {
        "inlet_pressure_bar": inlet_pressure_bar,
        "outlet_pressure_bar": outlet_pressure_bar,
        "inlet_within_range": is_pressure_in_compensation_range(
            inlet_pressure_bar, pressure_range
        ),
        "outlet_within_range": (
            is_pressure_in_compensation_range(
                outlet_pressure_bar, pressure_range
            )
            if outlet_pressure_bar > 0
            else False
        ),
        "uniform_compensation": (
            is_pressure_in_compensation_range(
                inlet_pressure_bar, pressure_range
            )
            and is_pressure_in_compensation_range(
                outlet_pressure_bar, pressure_range
            )
        ),
    }
