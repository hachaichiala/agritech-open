import pytest

from irrigation.calculations.emitter_pressure import EmitterPressureRange
from irrigation.calculations.irrigation_sector import analyze_irrigation_sector


def _reference_sector(**overrides):
    values = {
        "number_of_laterals": 4,
        "emitters_per_lateral": 3,
        "emitter_flow_lph": 8,
        "lateral_length_m": 20,
        "lateral_diameter_m": 0.016,
        "manifold_length_m": 30,
        "manifold_diameter_m": 0.04,
        "inlet_pressure_bar": 2.0,
        "pressure_range": EmitterPressureRange(1.0, 4.0),
        "hazen_williams_c": 150,
    }
    values.update(overrides)
    return analyze_irrigation_sector(**values)


def test_sector_total_flow_and_emitter_count():
    result = _reference_sector()

    assert result["lateral_flow_lph"] == pytest.approx(24)
    assert result["total_flow_lph"] == pytest.approx(96)
    assert result["total_emitters"] == 12


def test_sector_calculates_distinct_pressure_at_each_lateral_inlet():
    result = _reference_sector()

    pressures = result["lateral_inlet_pressures_bar"]
    assert len(pressures) == 4
    assert all(pressure > 0 for pressure in pressures)
    assert all(
        earlier > later
        for earlier, later in zip(pressures, pressures[1:])
    )


def test_sector_analyzes_each_lateral_at_its_own_inlet_pressure():
    result = _reference_sector()

    for lateral, expected_inlet_pressure in zip(
        result["laterals"],
        result["lateral_inlet_pressures_bar"],
    ):
        assert lateral["inlet_pressure_bar"] == pytest.approx(
            expected_inlet_pressure
        )
        assert len(lateral["emitter_pressures_bar"]) == 3


def test_sector_aggregates_emitter_pressure_compliance():
    result = _reference_sector()

    lateral_pressures = [
        pressure
        for lateral in result["laterals"]
        for pressure in lateral["emitter_pressures_bar"]
    ]
    expected_within = sum(
        1.0 <= pressure <= 4.0 for pressure in lateral_pressures
    )

    assert result["emitters_within_range"] == expected_within
    assert result["emitters_outside_range"] == 12 - expected_within
    assert result["minimum_emitter_pressure_bar"] == pytest.approx(
        min(lateral_pressures)
    )
    assert result["maximum_emitter_pressure_bar"] == pytest.approx(
        max(lateral_pressures)
    )
    assert result["compliance_percentage"] == pytest.approx(
        expected_within / 12 * 100
    )


def test_sector_reports_manifold_head_loss():
    from irrigation.calculations.manifold import calculate_manifold_head_loss

    result = _reference_sector()
    expected = calculate_manifold_head_loss(
        length_m=30,
        number_of_laterals=4,
        lateral_flow_lph=24,
        diameter_m=0.04,
        hazen_williams_c=150,
    )

    assert result["manifold_head_loss_m"] == pytest.approx(expected)


def test_sector_accepts_custom_emitter_pressure_range():
    result = _reference_sector(
        pressure_range=EmitterPressureRange(0.5, 2.5)
    )

    assert result["total_emitters"] == 12
    assert isinstance(result["all_emitters_within_range"], bool)


def test_sector_rejects_invalid_pressure_range():
    with pytest.raises(ValueError, match="Invalid emitter pressure range"):
        _reference_sector(pressure_range=None)


@pytest.mark.parametrize(
    "overrides",
    [
        {"number_of_laterals": 0},
        {"emitters_per_lateral": 0},
        {"emitter_flow_lph": 0},
        {"lateral_length_m": 0},
        {"lateral_diameter_m": 0},
        {"manifold_length_m": 0},
        {"manifold_diameter_m": 0},
        {"inlet_pressure_bar": 0},
    ],
)
def test_sector_rejects_invalid_hydraulic_inputs(overrides):
    with pytest.raises(ValueError):
        _reference_sector(**overrides)


def test_sector_rejects_pressure_below_zero_at_lateral_or_emitter():
    with pytest.raises(ValueError, match="pressure reaches zero or below"):
        _reference_sector(inlet_pressure_bar=1e-12)
