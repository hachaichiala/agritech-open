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
