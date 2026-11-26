import pytest

from irrigation.calculations.manifold import (
    calculate_manifold_head_loss,
    calculate_manifold_total_flow,
)


def test_manifold_total_flow_for_parallel_laterals():
    assert calculate_manifold_total_flow(
        number_of_laterals=4,
        lateral_flow_lph=800,
    ) == 3200


def test_single_lateral_manifold_head_loss_matches_single_pipe():
    from irrigation.calculations.pressure_loss import (
        calculate_hazen_williams_head_loss,
    )
    from irrigation.calculations.units import (
        liters_per_hour_to_cubic_meters_per_second,
    )

    expected = calculate_hazen_williams_head_loss(
        length_m=30,
        flow_m3_s=liters_per_hour_to_cubic_meters_per_second(800),
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    result = calculate_manifold_head_loss(
        length_m=30,
        number_of_laterals=1,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    assert result == pytest.approx(expected)


def test_reference_manifold_with_four_parallel_laterals():
    """Reference case: four 800 L/h laterals on a 30 m manifold."""
    result = calculate_manifold_head_loss(
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    assert result == pytest.approx(0.20878353, rel=1e-7)


def test_higher_lateral_flow_increases_manifold_head_loss():
    common = {
        "length_m": 30,
        "number_of_laterals": 4,
        "diameter_m": 0.04,
        "hazen_williams_c": 150,
    }

    low_flow_loss = calculate_manifold_head_loss(
        **common,
        lateral_flow_lph=400,
    )
    high_flow_loss = calculate_manifold_head_loss(
        **common,
        lateral_flow_lph=800,
    )

    assert high_flow_loss > low_flow_loss


@pytest.mark.parametrize(
    "number_of_laterals, lateral_flow",
    [(0, 800), (-1, 800), (2.5, 800), (True, 800), (4, 0), (4, float("inf"))],
)
def test_manifold_total_flow_rejects_invalid_inputs(
    number_of_laterals,
    lateral_flow,
):
    with pytest.raises(ValueError):
        calculate_manifold_total_flow(
            number_of_laterals,
            lateral_flow,
        )


@pytest.mark.parametrize(
    "length, number_of_laterals, lateral_flow, diameter",
    [
        (0, 4, 800, 0.04),
        (30, 0, 800, 0.04),
        (30, 4, -800, 0.04),
        (30, 4, 800, 0),
    ],
)
def test_manifold_head_loss_rejects_invalid_inputs(
    length,
    number_of_laterals,
    lateral_flow,
    diameter,
):
    with pytest.raises(ValueError):
        calculate_manifold_head_loss(
            length_m=length,
            number_of_laterals=number_of_laterals,
            lateral_flow_lph=lateral_flow,
            diameter_m=diameter,
        )



def test_manifold_segment_losses_match_total_head_loss():
    from irrigation.calculations.manifold import (
        calculate_manifold_segment_head_losses,
    )

    segment_losses = calculate_manifold_segment_head_losses(
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )
    total_loss = calculate_manifold_head_loss(
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    assert len(segment_losses) == 4
    assert all(loss > 0 for loss in segment_losses)
    assert sum(segment_losses) == pytest.approx(total_loss)


def test_manifold_segment_losses_decrease_after_each_takeoff():
    from irrigation.calculations.manifold import (
        calculate_manifold_segment_head_losses,
    )

    segment_losses = calculate_manifold_segment_head_losses(
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    assert all(
        earlier > later
        for earlier, later in zip(segment_losses, segment_losses[1:])
    )


def test_single_lateral_has_one_manifold_segment():
    from irrigation.calculations.manifold import (
        calculate_manifold_segment_head_losses,
    )

    losses = calculate_manifold_segment_head_losses(
        length_m=30,
        number_of_laterals=1,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    assert len(losses) == 1
    assert losses[0] == pytest.approx(
        calculate_manifold_head_loss(
            length_m=30,
            number_of_laterals=1,
            lateral_flow_lph=800,
            diameter_m=0.04,
            hazen_williams_c=150,
        )
    )


@pytest.mark.parametrize(
    "length, number_of_laterals, lateral_flow, diameter, coefficient",
    [
        (0, 4, 800, 0.04, 150),
        (30, 0, 800, 0.04, 150),
        (30, 4, 0, 0.04, 150),
        (30, 4, 800, 0, 150),
        (30, 4, 800, 0.04, 0),
        (30, True, 800, 0.04, 150),
    ],
)
def test_manifold_segment_losses_reject_invalid_inputs(
    length,
    number_of_laterals,
    lateral_flow,
    diameter,
    coefficient,
):
    from irrigation.calculations.manifold import (
        calculate_manifold_segment_head_losses,
    )

    with pytest.raises(ValueError):
        calculate_manifold_segment_head_losses(
            length_m=length,
            number_of_laterals=number_of_laterals,
            lateral_flow_lph=lateral_flow,
            diameter_m=diameter,
            hazen_williams_c=coefficient,
        )



def test_pressure_at_each_lateral_takeoff_decreases_along_manifold():
    from irrigation.calculations.manifold import (
        calculate_pressure_at_each_lateral_takeoff,
    )

    pressures = calculate_pressure_at_each_lateral_takeoff(
        inlet_pressure_bar=2.0,
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    assert len(pressures) == 4
    assert all(pressure > 0 for pressure in pressures)
    assert all(
        earlier > later
        for earlier, later in zip(pressures, pressures[1:])
    )


def test_last_lateral_pressure_matches_total_manifold_head_loss():
    from irrigation.calculations.manifold import (
        calculate_pressure_at_each_lateral_takeoff,
    )
    from irrigation.calculations.units import meters_of_water_to_bar

    inlet_pressure_bar = 2.0
    total_loss_m = calculate_manifold_head_loss(
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )
    pressures = calculate_pressure_at_each_lateral_takeoff(
        inlet_pressure_bar=inlet_pressure_bar,
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    expected_last_pressure = (
        inlet_pressure_bar - meters_of_water_to_bar(total_loss_m)
    )
    assert pressures[-1] == pytest.approx(expected_last_pressure)


def test_first_lateral_pressure_uses_only_first_segment_loss():
    from irrigation.calculations.manifold import (
        calculate_manifold_segment_head_losses,
        calculate_pressure_at_each_lateral_takeoff,
    )
    from irrigation.calculations.units import meters_of_water_to_bar

    inlet_pressure_bar = 2.0
    segment_losses = calculate_manifold_segment_head_losses(
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )
    pressures = calculate_pressure_at_each_lateral_takeoff(
        inlet_pressure_bar=inlet_pressure_bar,
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=800,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    assert pressures[0] == pytest.approx(
        inlet_pressure_bar - meters_of_water_to_bar(segment_losses[0])
    )


@pytest.mark.parametrize("inlet_pressure", [0, -1, float("inf"), True])
def test_pressure_at_lateral_takeoffs_rejects_invalid_inlet_pressure(
    inlet_pressure,
):
    from irrigation.calculations.manifold import (
        calculate_pressure_at_each_lateral_takeoff,
    )

    with pytest.raises(ValueError):
        calculate_pressure_at_each_lateral_takeoff(
            inlet_pressure_bar=inlet_pressure,
            length_m=30,
            number_of_laterals=4,
            lateral_flow_lph=800,
            diameter_m=0.04,
        )


def test_pressure_at_lateral_takeoffs_rejects_insufficient_inlet_pressure():
    from irrigation.calculations.manifold import (
        calculate_pressure_at_each_lateral_takeoff,
    )

    with pytest.raises(ValueError, match="reaches zero or below"):
        calculate_pressure_at_each_lateral_takeoff(
            inlet_pressure_bar=0.001,
            length_m=30,
            number_of_laterals=4,
            lateral_flow_lph=800,
            diameter_m=0.04,
        )
