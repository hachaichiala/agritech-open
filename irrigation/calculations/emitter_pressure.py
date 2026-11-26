
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
