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


def test_larger_diameter_reduces_dripline_head_loss():
    common = {
        "length_m": 100,
        "number_of_emitters": 40,
        "emitter_flow_lph": 4,
    }

    small_diameter_loss = calculate_dripline_head_loss(
        **common,
        diameter_m=0.016,
    )
    large_diameter_loss = calculate_dripline_head_loss(
        **common,
        diameter_m=0.020,
    )

    assert large_diameter_loss < small_diameter_loss


def test_higher_emitter_flow_increases_dripline_head_loss():
    common = {
        "length_m": 100,
        "number_of_emitters": 40,
        "diameter_m": 0.020,
    }

    low_flow_loss = calculate_dripline_head_loss(
        **common,
        emitter_flow_lph=2,
    )
    high_flow_loss = calculate_dripline_head_loss(
        **common,
        emitter_flow_lph=4,
    )

    assert high_flow_loss > low_flow_loss


def test_more_emitters_increase_dripline_head_loss():
    common = {
        "length_m": 100,
        "emitter_flow_lph": 4,
        "diameter_m": 0.020,
    }

    fewer_emitters_loss = calculate_dripline_head_loss(
        **common,
        number_of_emitters=20,
    )
    more_emitters_loss = calculate_dripline_head_loss(
        **common,
        number_of_emitters=40,
    )

    assert more_emitters_loss > fewer_emitters_loss


def test_higher_emitter_flow_reduces_pressure_at_first_and_last_emitters():
    common = {
        "inlet_pressure_bar": 2.0,
        "length_m": 100,
        "number_of_emitters": 40,
        "diameter_m": 0.020,
    }

    low_flow_pressures = calculate_pressure_at_each_emitter(
        **common,
        emitter_flow_lph=2,
    )
    high_flow_pressures = calculate_pressure_at_each_emitter(
        **common,
        emitter_flow_lph=4,
    )

    assert high_flow_pressures[0] < low_flow_pressures[0]
    assert high_flow_pressures[-1] < low_flow_pressures[-1]

def test_reference_100m_lateral_with_200_emitters():
    """Check a practical reference case for a 100 m, 16 mm lateral."""
    head_loss_m = calculate_dripline_head_loss(
        length_m=100,
        number_of_emitters=200,
        emitter_flow_lph=2,
        diameter_m=0.016,
        hazen_williams_c=150,
    )

    assert head_loss_m == pytest.approx(0.9342403, rel=1e-6)
    assert head_loss_m * 0.0980665 == pytest.approx(
        0.0916177, rel=1e-6
    )



def test_zero_emitter_connection_k_preserves_reference_head_loss():
    result = calculate_dripline_head_loss(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        emitter_connection_k=0.0,
    )
    assert result == pytest.approx(0.00154314, rel=1e-4)


def test_positive_emitter_connection_k_increases_head_loss():
    common = dict(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )
    friction_only = calculate_dripline_head_loss(**common)
    with_connections = calculate_dripline_head_loss(
        **common, emitter_connection_k=1.0
    )
    assert with_connections > friction_only


def test_connection_losses_use_remaining_downstream_flow_at_each_segment():
    from irrigation.calculations.dripline import (
        calculate_dripline_segment_head_losses,
    )
    from irrigation.calculations.pressure_loss import calculate_minor_head_loss
    from irrigation.calculations.units import (
        liters_per_hour_to_cubic_meters_per_second,
    )

    common = dict(
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )
    friction_segments = calculate_dripline_segment_head_losses(
        **common, emitter_connection_k=0.0
    )
    combined_segments = calculate_dripline_segment_head_losses(
        **common, emitter_connection_k=1.0
    )
    expected_minor_losses = [
        calculate_minor_head_loss(
            liters_per_hour_to_cubic_meters_per_second(flow_lph),
            0.016,
            1.0,
        )
        for flow_lph in (24, 16, 8)
    ]
    actual_minor_losses = [
        combined - friction
        for combined, friction in zip(combined_segments, friction_segments)
    ]
    assert actual_minor_losses == pytest.approx(expected_minor_losses)


@pytest.mark.parametrize(
    "invalid_k",
    [-1, float("inf"), float("nan"), True, 10 ** 1000],
)
def test_invalid_emitter_connection_k_is_rejected(invalid_k):
    with pytest.raises(ValueError, match="Emitter connection K"):
        calculate_dripline_head_loss(
            length_m=20,
            number_of_emitters=3,
            emitter_flow_lph=8,
            diameter_m=0.016,
            emitter_connection_k=invalid_k,
        )


def test_connection_losses_reduce_pressure_at_emitters():
    common = dict(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
    )
    from irrigation.calculations.dripline import (
        calculate_pressure_at_each_emitter,
    )
    without_connections = calculate_pressure_at_each_emitter(**common)
    with_connections = calculate_pressure_at_each_emitter(
        **common, emitter_connection_k=1.0
    )
    assert all(
        with_k < without_k
        for with_k, without_k in zip(with_connections, without_connections)
    )
