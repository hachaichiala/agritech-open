
import pytest

from irrigation.calculations.units import (
    liters_per_hour_to_cubic_meters_per_second,
    cubic_meters_per_second_to_liters_per_hour,
    bar_to_meters_of_water,
    meters_of_water_to_bar,
)


def test_liters_per_hour_to_cubic_meters_per_second():
    result = liters_per_hour_to_cubic_meters_per_second(3600)
    assert result == pytest.approx(0.001)


def test_cubic_meters_per_second_to_liters_per_hour():
    result = cubic_meters_per_second_to_liters_per_hour(0.001)
    assert result == pytest.approx(3600)


def test_bar_to_meters_of_water():
    result = bar_to_meters_of_water(1)
    assert result == pytest.approx(10.19716, rel=1e-5)


def test_meters_of_water_to_bar():
    result = meters_of_water_to_bar(10.19716)
    assert result == pytest.approx(1, rel=1e-5)


@pytest.mark.parametrize(
    "function, value",
    [
        (liters_per_hour_to_cubic_meters_per_second, -1),
        (cubic_meters_per_second_to_liters_per_hour, -1),
        (liters_per_hour_to_cubic_meters_per_second, float("inf")),
        (bar_to_meters_of_water, float("nan")),
        (meters_of_water_to_bar, True),
    ],
)
def test_invalid_inputs(function, value):
    with pytest.raises(ValueError):
        function(value)
