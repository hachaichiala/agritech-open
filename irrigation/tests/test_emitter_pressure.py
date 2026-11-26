
import pytest

from irrigation.calculations.emitter_pressure import (
    EmitterPressureRange,
    is_pressure_in_compensation_range,
)


def test_default_pressure_range():
    pressure_range = EmitterPressureRange()

    assert pressure_range.minimum_bar == 1.0
    assert pressure_range.maximum_bar == 4.0


def test_pressure_inside_range():
    pressure_range = EmitterPressureRange()

    assert is_pressure_in_compensation_range(
        2.5, pressure_range
    ) is True


def test_pressure_at_minimum():
    pressure_range = EmitterPressureRange()

    assert is_pressure_in_compensation_range(
        1.0, pressure_range
    ) is True


def test_pressure_at_maximum():
    pressure_range = EmitterPressureRange()

    assert is_pressure_in_compensation_range(
        4.0, pressure_range
    ) is True


def test_pressure_below_range():
    pressure_range = EmitterPressureRange()

    assert is_pressure_in_compensation_range(
        0.8, pressure_range
    ) is False


def test_pressure_above_range():
    pressure_range = EmitterPressureRange()

    assert is_pressure_in_compensation_range(
        4.5, pressure_range
    ) is False


def test_invalid_pressure_range():
    with pytest.raises(ValueError):
        EmitterPressureRange(4.0, 1.0)


@pytest.mark.parametrize("pressure", [0, -1, True])
def test_invalid_pressure(pressure):
    with pytest.raises(ValueError):
        is_pressure_in_compensation_range(
            pressure, EmitterPressureRange()
        )
