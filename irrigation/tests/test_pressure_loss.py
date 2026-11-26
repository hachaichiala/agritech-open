import pytest

from irrigation.calculations.pressure_loss import (
    calculate_hazen_williams_head_loss,
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
