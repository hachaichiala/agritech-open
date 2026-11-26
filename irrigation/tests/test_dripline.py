from irrigation.calculations.dripline import (
    calculate_pressure_at_each_emitter,
)
from irrigation.calculations.dripline import (
    calculate_dripline_segment_head_losses,
)
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

def test_dripline_segment_head_losses_count():
    losses = calculate_dripline_segment_head_losses(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert len(losses) == 3


def test_dripline_segment_head_losses_are_positive():
    losses = calculate_dripline_segment_head_losses(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert all(loss > 0 for loss in losses)


def test_segment_losses_sum_matches_total_head_loss():
    losses = calculate_dripline_segment_head_losses(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    total_loss = calculate_dripline_head_loss(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert sum(losses) == pytest.approx(total_loss)


def test_segment_losses_decrease_along_dripline():
    losses = calculate_dripline_segment_head_losses(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert losses[0] > losses[1] > losses[2]

def test_pressure_at_each_emitter_count():
    pressures = calculate_pressure_at_each_emitter(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert len(pressures) == 3


def test_pressure_decreases_along_dripline():
    pressures = calculate_pressure_at_each_emitter(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert pressures[0] > pressures[1] > pressures[2]


def test_first_emitter_pressure():
    pressures = calculate_pressure_at_each_emitter(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    assert pressures[0] == pytest.approx(
        1.999949, rel=1e-4
    )


def test_last_emitter_pressure_matches_total_loss():
    pressures = calculate_pressure_at_each_emitter(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    total_loss = calculate_dripline_head_loss(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )

    expected_pressure = 2.0 - total_loss * 0.0980665

    assert pressures[-1] == pytest.approx(expected_pressure)


def test_invalid_inlet_pressure():
    with pytest.raises(ValueError):
        calculate_pressure_at_each_emitter(
            inlet_pressure_bar=0,
            length_m=20,
            number_of_emitters=3,
            emitter_flow_lph=8,
            diameter_m=0.016,
        )

