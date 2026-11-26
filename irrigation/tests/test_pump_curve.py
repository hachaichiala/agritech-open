import pytest

from irrigation.calculations.pump_curve import (
    find_pump_operating_point,
)


def test_finds_piecewise_linear_pump_system_intersection():
    result = find_pump_operating_point(
        pump_curve=[(0.0, 40.0), (0.001, 20.0)],
        system_curve=[(0.0, 10.0), (0.001, 30.0)],
    )

    assert result["flow_m3_s"] == pytest.approx(0.00075)
    assert result["head_m"] == pytest.approx(25.0)
    assert result["pump_head_m"] == pytest.approx(25.0)
    assert result["system_head_m"] == pytest.approx(25.0)


def test_operating_point_uses_only_overlapping_curve_range():
    result = find_pump_operating_point(
        pump_curve=[(0.0, 40.0), (0.002, 20.0)],
        system_curve=[(0.0005, 15.0), (0.0015, 35.0)],
    )

    assert result["flow_m3_s"] == pytest.approx(0.0011666666667)
    assert result["head_m"] == pytest.approx(26.6666666667)


@pytest.mark.parametrize(
    "pump_curve, system_curve",
    [
        ([(0.0, 20.0)], [(0.0, 10.0), (1.0, 20.0)]),
        ([(0.0, 20.0), (1.0, 30.0)], [(0.0, 10.0), (1.0, 20.0)]),
        ([(0.0, 20.0), (0.0, 10.0)], [(0.0, 5.0), (1.0, 15.0)]),
        ([(0.0, float("nan")), (1.0, 10.0)], [(0.0, 5.0), (1.0, 15.0)]),
        ([(0.0, 20.0), (1.0, 10.0)], [(0.0, 15.0), (1.0, 25.0)]),
    ],
)
def test_rejects_invalid_or_non_intersecting_curves(
    pump_curve, system_curve
):
    with pytest.raises(ValueError):
        find_pump_operating_point(pump_curve, system_curve)


def test_rejects_curves_with_multiple_intersections():
    with pytest.raises(ValueError, match="multiple intersections"):
        find_pump_operating_point(
            pump_curve=[(0.0, 10.0), (1.0, 10.0)],
            system_curve=[(0.0, 10.0), (1.0, 10.0)],
        )
