
import pytest

from irrigation.calculations.dripline import (
    calculate_dripline_head_loss,
)


def test_dripline_single_emitter():
    result = calculate_dripline_head_loss(
        length_m=20,
        number_of_emitters=1,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert result == pytest.approx(0.00037762, rel=1e-4)


def test_dripline_two_emitters():
    result = calculate_dripline_head_loss(
        length_m=20,
        number_of_emitters=2,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert result == pytest.approx(0.00087042, rel=1e-4)


def test_dripline_three_emitters():
    result = calculate_dripline_head_loss(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert result == pytest.approx(0.00154314, rel=1e-4)


@pytest.mark.parametrize(
    "number_of_emitters",
    [0, -1, 1.5, True],
)
def test_invalid_emitter_count(number_of_emitters):
    with pytest.raises(ValueError):
        calculate_dripline_head_loss(
            20, number_of_emitters, 8, 0.016
        )


def test_negative_emitter_flow():
    with pytest.raises(ValueError):
        calculate_dripline_head_loss(20, 2, -8, 0.016)


def test_zero_length():
    with pytest.raises(ValueError):
        calculate_dripline_head_loss(0, 2, 8, 0.016)


def test_invalid_diameter():
    with pytest.raises(ValueError):
        calculate_dripline_head_loss(20, 2, 8, 0)
        
@pytest.mark.parametrize(
    "length, emitter_flow",
    [
        (True, 8),
        (float("inf"), 8),
        (float("nan"), 8),
        (20, True),
        (20, float("inf")),
        (20, float("nan")),
    ],
)
def test_invalid_length_and_emitter_flow(length, emitter_flow):
    with pytest.raises(ValueError):
        calculate_dripline_head_loss(
            length_m=length,
            number_of_emitters=2,
            emitter_flow_lph=emitter_flow,
            diameter_m=0.016,
        )

