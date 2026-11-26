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
    assert result["head_m"] == pytest.approx(28.3333333333)


@pytest.mark.parametrize(
    "pump_curve, system_curve",
    [
        ([(0.0, 20.0)], [(0.0, 10.0), (1.0, 20.0)]),
        ([(0.0, 20.0), (1.0, 30.0)], [(0.0, 10.0), (1.0, 20.0)]),
        ([(0.0, 20.0), (0.0, 10.0)], [(0.0, 5.0), (1.0, 15.0)]),
        ([(0.0, float("nan")), (1.0, 10.0)], [(0.0, 5.0), (1.0, 15.0)]),
        ([(0.0, 20.0), (1.0, 10.0)], [(0.0, 30.0), (1.0, 40.0)]),
    ],
)
def test_rejects_invalid_or_non_intersecting_curves(
    pump_curve, system_curve
):
    with pytest.raises(ValueError):
        find_pump_operating_point(pump_curve, system_curve)



def test_finds_intersection_without_overflow_for_large_finite_heads():
    result = find_pump_operating_point(
        pump_curve=[(0.0, 1e308), (1.0, 0.0)],
        system_curve=[(0.0, 0.0), (1.0, 1e308)],
    )

    assert result["flow_m3_s"] == pytest.approx(0.5)
    assert result["pump_head_m"] == pytest.approx(5e307)
    assert result["system_head_m"] == pytest.approx(5e307)
    assert result["head_m"] == pytest.approx(5e307)




def test_endpoint_intersection_head_average_does_not_overflow():
    result = find_pump_operating_point(
        pump_curve=[(0.0, 1e308), (1.0, 1e308)],
        system_curve=[(1.0, 1e308), (2.0, 1e308)],
    )

    assert result["flow_m3_s"] == pytest.approx(1.0)
    assert result["head_m"] == pytest.approx(1e308)



def test_rejects_curves_with_multiple_intersections():
    with pytest.raises(ValueError, match="multiple intersections"):
        find_pump_operating_point(
            pump_curve=[(0.0, 10.0), (1.0, 10.0)],
            system_curve=[(0.0, 10.0), (1.0, 10.0)],
        )



def test_validates_and_normalizes_pump_curve_points():
    from irrigation.calculations.pump_curve import validate_pump_curve

    assert validate_pump_curve([(0, 40), (0.5, 20)]) == [
        (0.0, 40.0),
        (0.5, 20.0),
    ]


def test_validates_system_curve_points():
    from irrigation.calculations.pump_curve import validate_system_curve

    assert validate_system_curve([(0, 5), (0.5, 15)]) == [
        (0.0, 5.0),
        (0.5, 15.0),
    ]


@pytest.mark.parametrize(
    "curve",
    [
        None,
        [],
        [(0.0, 10.0)],
        [(0.0, 10.0), (1.0, 20.0), (0.5, 30.0)],
        [(0.0, 10.0), (1.0, 11.0), (2.0, 9.0)],
        [(0.0, True), (1.0, 10.0)],
        [(0.0, 10**1000), (1.0, 10.0)],
        [(0.0, -1.0), (1.0, 10.0)],
    ],
)
def test_public_pump_curve_validator_rejects_invalid_data(curve):
    from irrigation.calculations.pump_curve import validate_pump_curve

    with pytest.raises(ValueError):
        validate_pump_curve(curve)


@pytest.mark.parametrize(
    "curve",
    [
        None,
        [],
        [(0.0, 10.0)],
        [(0.0, 10.0), (1.0, 5.0)],
        [(0.0, 10.0), (0.0, 20.0)],
        [(0.0, float("inf")), (1.0, 20.0)],
    ],
)
def test_public_system_curve_validator_rejects_invalid_data(curve):
    from irrigation.calculations.pump_curve import validate_system_curve

    with pytest.raises(ValueError):
        validate_system_curve(curve)

def test_does_not_treat_small_absolute_head_difference_as_intersection():
    with pytest.raises(ValueError, match="no intersection"):
        find_pump_operating_point(
            pump_curve=[(0.0, 1e-13), (1.0, 1e-13)],
            system_curve=[(1.0, 0.0), (2.0, 0.0)],
        )


def test_finds_real_intersection_at_small_head_values():
    result = find_pump_operating_point(
        pump_curve=[(0.0, 2e-13), (1.0, 0.0)],
        system_curve=[(0.0, 0.0), (1.0, 2e-13)],
    )

    assert result["flow_m3_s"] == pytest.approx(0.5)
    assert result["pump_head_m"] == pytest.approx(1e-13)
    assert result["system_head_m"] == pytest.approx(1e-13)

