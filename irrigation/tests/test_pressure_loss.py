import pytest

from irrigation.calculations.pressure_loss import (
    calculate_hazen_williams_head_loss,
    calculate_minor_head_loss,
)


def test_hazen_williams_basic():
    result = calculate_hazen_williams_head_loss(
        length_m=100,
        flow_m3_s=0.001,
        diameter_m=0.05,
        hazen_williams_c=150,
    )

    assert result == pytest.approx(0.601673, rel=1e-5)


def test_zero_length():
    result = calculate_hazen_williams_head_loss(
        0, 0.001, 0.05, 150
    )

    assert result == 0.0


def test_zero_flow():
    result = calculate_hazen_williams_head_loss(
        100, 0, 0.05, 150
    )

    assert result == 0.0


@pytest.mark.parametrize(
    "length, flow, diameter, coefficient",
    [
        (-100, 0.001, 0.05, 150),
        (100, -0.001, 0.05, 150),
        (100, 0.001, 0, 150),
        (100, 0.001, 0.05, 0),
    ],
)
def test_invalid_inputs(length, flow, diameter, coefficient):
    with pytest.raises(ValueError):
        calculate_hazen_williams_head_loss(
            length, flow, diameter, coefficient
        )


def test_infinite_flow():
    with pytest.raises(ValueError):
        calculate_hazen_williams_head_loss(
            100, float("inf"), 0.05, 150
        )


def test_boolean_diameter():
    with pytest.raises(ValueError):
        calculate_hazen_williams_head_loss(
            100, 0.001, True, 150
        )


@pytest.mark.parametrize(
    "length, flow, diameter, coefficient",
    [
        (100, 1e308, 0.05, 150),
        (100, 0.001, 1e-100, 150),
    ],
)
def test_hazen_williams_rejects_unrepresentable_results(
    length, flow, diameter, coefficient
):
    with pytest.raises(ValueError, match="finite"):
        calculate_hazen_williams_head_loss(
            length, flow, diameter, coefficient
        )



@pytest.mark.parametrize(
    "length, flow, diameter, coefficient",
    [
        (10**400, 0.001, 0.05, 150),
        (100, 10**400, 0.05, 150),
        (100, 0.001, 10**400, 150),
        (100, 0.001, 0.05, 10**400),
        ("100", 0.001, 0.05, 150),
        (100, 0.001, 0.05, float("nan")),
        (True, 0.001, 0.05, 150),
    ],
)
def test_hazen_williams_rejects_non_numeric_or_unrepresentable_inputs(
    length, flow, diameter, coefficient
):
    with pytest.raises(ValueError, match="finite number"):
        calculate_hazen_williams_head_loss(
            length, flow, diameter, coefficient
        )


def test_minor_head_loss_matches_velocity_formula():
    import math

    flow = 0.001
    diameter = 0.05
    coefficient = 2.0
    gravity = 9.80665
    area = math.pi * diameter ** 2 / 4.0
    velocity = flow / area
    expected = coefficient * velocity ** 2 / (2.0 * gravity)

    result = calculate_minor_head_loss(
        flow, diameter, coefficient, gravity
    )

    assert result == pytest.approx(expected)


@pytest.mark.parametrize(
    "flow, coefficient",
    [
        (0.0, 2.0),
        (0.001, 0.0),
    ],
)
def test_minor_head_loss_zero_flow_or_coefficient(flow, coefficient):
    assert calculate_minor_head_loss(
        flow, 0.05, coefficient
    ) == 0.0


@pytest.mark.parametrize(
    "flow, diameter, coefficient, gravity",
    [
        (-0.001, 0.05, 1.0, 9.80665),
        (0.001, 0.0, 1.0, 9.80665),
        (0.001, 0.05, -1.0, 9.80665),
        (0.001, 0.05, 1.0, 0.0),
        (True, 0.05, 1.0, 9.80665),
        (0.001, True, 1.0, 9.80665),
        (0.001, 0.05, True, 9.80665),
        (0.001, 0.05, 1.0, True),
    ],
)
def test_minor_head_loss_rejects_invalid_inputs(
    flow, diameter, coefficient, gravity
):
    with pytest.raises(ValueError):
        calculate_minor_head_loss(
            flow, diameter, coefficient, gravity
        )


@pytest.mark.parametrize(
    "flow, diameter, coefficient, gravity",
    [
        (float("inf"), 0.05, 1.0, 9.80665),
        (0.001, float("nan"), 1.0, 9.80665),
        (0.001, 0.05, float("inf"), 9.80665),
        (0.001, 0.05, 1.0, float("nan")),
    ],
)
def test_minor_head_loss_rejects_non_finite_inputs(
    flow, diameter, coefficient, gravity
):
    with pytest.raises(ValueError, match="finite number"):
        calculate_minor_head_loss(
            flow, diameter, coefficient, gravity
        )


def test_hazen_williams_loss_scales_linearly_with_pipe_length():
    base = calculate_hazen_williams_head_loss(100, 0.001, 0.05, 150)
    doubled = calculate_hazen_williams_head_loss(200, 0.001, 0.05, 150)
    assert doubled == pytest.approx(2.0 * base)


def test_hazen_williams_loss_follows_flow_exponent():
    base = calculate_hazen_williams_head_loss(100, 0.001, 0.05, 150)
    doubled_flow = calculate_hazen_williams_head_loss(100, 0.002, 0.05, 150)
    assert doubled_flow == pytest.approx(base * (2.0 ** 1.852))


def test_hazen_williams_loss_decreases_with_larger_diameter():
    smaller = calculate_hazen_williams_head_loss(100, 0.001, 0.05, 150)
    larger = calculate_hazen_williams_head_loss(100, 0.001, 0.06, 150)
    assert larger < smaller
    assert larger == pytest.approx(smaller * ((0.06 / 0.05) ** -4.871))

