
import pytest

from irrigation.calculations.emitter_pressure import (
    EmitterPressureRange,
    is_pressure_in_compensation_range,
    check_dripline_pressure,
    analyze_dripline_pressure,
    analyze_emitter_pressure_distribution,
)


def test_default_pressure_range():
    pressure_range = EmitterPressureRange()

    assert pressure_range.minimum_bar == 1.0
    assert pressure_range.maximum_bar == 4.0


def test_pressure_inside_range():
    assert is_pressure_in_compensation_range(
        2.5, EmitterPressureRange()
    ) is True


def test_pressure_at_minimum():
    assert is_pressure_in_compensation_range(
        1.0, EmitterPressureRange()
    ) is True


def test_pressure_at_maximum():
    assert is_pressure_in_compensation_range(
        4.0, EmitterPressureRange()
    ) is True


def test_pressure_below_range():
    assert is_pressure_in_compensation_range(
        0.8, EmitterPressureRange()
    ) is False


def test_pressure_above_range():
    assert is_pressure_in_compensation_range(
        4.5, EmitterPressureRange()
    ) is False


def test_invalid_pressure_range():
    with pytest.raises(ValueError):
        EmitterPressureRange(4.0, 1.0)


@pytest.mark.parametrize(
    "pressure",
    [0, -1, True, float("inf"), float("nan")],
)
def test_invalid_pressure(pressure):
    with pytest.raises(ValueError):
        is_pressure_in_compensation_range(
            pressure, EmitterPressureRange()
        )


def test_invalid_pressure_range_values():
    with pytest.raises(ValueError):
        EmitterPressureRange(1.0, float("inf"))


def test_dripline_pressure_within_range():
    result = check_dripline_pressure(
        inlet_pressure_bar=2.0,
        head_loss_m=2.0,
        pressure_range=EmitterPressureRange(),
    )

    assert result["inlet_pressure_bar"] == 2.0
    assert result["outlet_pressure_bar"] == pytest.approx(1.803867)
    assert result["inlet_within_range"] is True
    assert result["outlet_within_range"] is True
    assert result["uniform_compensation"] is True


def test_dripline_outlet_below_compensation_range():
    result = check_dripline_pressure(
        inlet_pressure_bar=2.0,
        head_loss_m=15.0,
        pressure_range=EmitterPressureRange(),
    )

    assert result["outlet_within_range"] is False
    assert result["uniform_compensation"] is False


def test_analyze_dripline_pressure():
    result = analyze_dripline_pressure(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
    )

    assert result["head_loss_m"] == pytest.approx(
        0.00154314, rel=1e-4
    )
    assert result["inlet_pressure_bar"] == 2.0
    assert result["outlet_pressure_bar"] == pytest.approx(
        1.9998487, rel=1e-4
    )
    assert result["uniform_compensation"] is True


def test_analyze_dripline_invalid_length():
    with pytest.raises(ValueError):
        analyze_dripline_pressure(
            inlet_pressure_bar=2.0,
            length_m=0,
            number_of_emitters=3,
            emitter_flow_lph=8,
            diameter_m=0.016,
            pressure_range=EmitterPressureRange(),
        )


def test_analyze_dripline_invalid_inlet_pressure():
    with pytest.raises(ValueError):
        analyze_dripline_pressure(
            inlet_pressure_bar=0,
            length_m=20,
            number_of_emitters=3,
            emitter_flow_lph=8,
            diameter_m=0.016,
            pressure_range=EmitterPressureRange(),
        )


def test_emitter_pressure_distribution_all_within_range():
    result = analyze_emitter_pressure_distribution(
        emitter_pressures_bar=[2.0, 1.8, 1.5, 1.2],
        pressure_range=EmitterPressureRange(),
    )

    assert result["total_emitters"] == 4
    assert result["emitters_within_range"] == 4
    assert result["emitters_outside_range"] == 0
    assert result["minimum_pressure_bar"] == 1.2
    assert result["maximum_pressure_bar"] == 2.0
    assert result["all_emitters_within_range"] is True


def test_emitter_pressure_distribution_some_outside_range():
    result = analyze_emitter_pressure_distribution(
        emitter_pressures_bar=[2.0, 1.5, 0.8, 0.5],
        pressure_range=EmitterPressureRange(),
    )

    assert result["total_emitters"] == 4
    assert result["emitters_within_range"] == 2
    assert result["emitters_outside_range"] == 2
    assert result["all_emitters_within_range"] is False


def test_emitter_pressure_distribution_empty_list():
    with pytest.raises(ValueError):
        analyze_emitter_pressure_distribution(
            [],
            EmitterPressureRange(),
        )


def test_emitter_pressure_distribution_invalid_pressure():
    with pytest.raises(ValueError):
        analyze_emitter_pressure_distribution(
            [2.0, float("nan")],
            EmitterPressureRange(),
        )


def test_pressure_range_rejects_boolean_and_unrepresentable_values():
    with pytest.raises(ValueError):
        EmitterPressureRange(True, 4.0)

    with pytest.raises(ValueError):
        EmitterPressureRange(1.0, 10 ** 1000)


def test_check_dripline_pressure_rejects_unrepresentable_values():
    with pytest.raises(ValueError):
        check_dripline_pressure(
            inlet_pressure_bar=10 ** 1000,
            head_loss_m=0,
            pressure_range=EmitterPressureRange(),
        )


def test_analyze_emitter_pressure_distribution_reports_compliance():
    result = analyze_emitter_pressure_distribution(
        emitter_pressures_bar=[2.0, 1.5, 0.8, 0.5],
        pressure_range=EmitterPressureRange(),
    )

    assert result["compliance_percentage"] == pytest.approx(50.0)


def test_analyze_dripline_emitter_pressures():
    from irrigation.calculations.emitter_pressure import (
        analyze_dripline_emitter_pressures,
    )

    result = analyze_dripline_emitter_pressures(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
    )

    assert result["total_emitters"] == 3
    assert len(result["emitter_pressures_bar"]) == 3
    assert result["outlet_pressure_bar"] == pytest.approx(
        result["emitter_pressures_bar"][-1]
    )
    assert result["head_loss_m"] == pytest.approx(0.00154314, rel=1e-4)
    assert result["all_emitters_within_range"] is True
    assert result["all_pressures_within_range"] is True
    assert result["compliance_percentage"] == pytest.approx(100.0)


def test_analyze_dripline_emitter_pressures_checks_inlet_range():
    from irrigation.calculations.emitter_pressure import (
        analyze_dripline_emitter_pressures,
    )

    result = analyze_dripline_emitter_pressures(
        inlet_pressure_bar=0.8,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
    )

    assert result["inlet_within_range"] is False
    assert result["all_emitters_within_range"] is False
    assert result["all_pressures_within_range"] is False


def test_analyze_dripline_emitter_pressures_rejects_invalid_range():
    from irrigation.calculations.emitter_pressure import (
        analyze_dripline_emitter_pressures,
    )

    with pytest.raises(ValueError, match="Invalid emitter pressure range"):
        analyze_dripline_emitter_pressures(
            inlet_pressure_bar=2.0,
            length_m=20,
            number_of_emitters=3,
            emitter_flow_lph=8,
            diameter_m=0.016,
            pressure_range=None,
        )



def test_new_pressure_analysis_functions_are_publicly_exported():
    from irrigation.calculations import (
        analyze_dripline_emitter_pressures,
        calculate_pressure_at_each_emitter,
    )

    assert callable(analyze_dripline_emitter_pressures)
    assert callable(calculate_pressure_at_each_emitter)



@pytest.mark.parametrize(
    "emitter_pressures",
    [[0.0, -0.1], [0.8, 0.0], [0.8, -0.2]],
)
def test_dripline_analysis_rejects_zero_or_negative_emitter_pressure(
    monkeypatch,
    emitter_pressures,
):
    import irrigation.calculations.emitter_pressure as pressure_module

    monkeypatch.setattr(
        pressure_module,
        "calculate_pressure_at_each_emitter",
        lambda **kwargs: emitter_pressures,
    )

    with pytest.raises(ValueError, match="Pressure reaches zero or below"):
        pressure_module.analyze_dripline_emitter_pressures(
            inlet_pressure_bar=2.0,
            length_m=20,
            number_of_emitters=len(emitter_pressures),
            emitter_flow_lph=8,
            diameter_m=0.016,
            pressure_range=EmitterPressureRange(),
        )


def test_dripline_analysis_reports_positive_pressures_below_pc_range(
    monkeypatch,
):
    import irrigation.calculations.emitter_pressure as pressure_module

    monkeypatch.setattr(
        pressure_module,
        "calculate_pressure_at_each_emitter",
        lambda **kwargs: [0.9, 0.7, 0.5],
    )

    result = pressure_module.analyze_dripline_emitter_pressures(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
    )

    assert result["emitters_within_range"] == 0
    assert result["emitters_outside_range"] == 3
    assert result["compliance_percentage"] == pytest.approx(0.0)
    assert result["all_emitters_within_range"] is False
    assert result["all_pressures_within_range"] is False



def test_realistic_lateral_with_positive_pressure_below_pc_limit():
    from irrigation.calculations.emitter_pressure import (
        analyze_dripline_emitter_pressures,
    )

    result = analyze_dripline_emitter_pressures(
        inlet_pressure_bar=1.2,
        length_m=100,
        number_of_emitters=10,
        emitter_flow_lph=8,
        diameter_m=0.006,
        pressure_range=EmitterPressureRange(),
    )

    assert result["minimum_pressure_bar"] > 0
    assert result["minimum_pressure_bar"] < 1.0
    assert result["emitters_outside_range"] > 0
    assert result["compliance_percentage"] < 100.0
    assert result["all_pressures_within_range"] is False


def test_realistic_lateral_rejects_pressure_loss_exceeding_inlet_pressure():
    from irrigation.calculations.emitter_pressure import (
        analyze_dripline_emitter_pressures,
    )

    with pytest.raises(ValueError, match="Pressure reaches zero or below"):
        analyze_dripline_emitter_pressures(
            inlet_pressure_bar=0.4,
            length_m=100,
            number_of_emitters=10,
            emitter_flow_lph=8,
            diameter_m=0.005,
            pressure_range=EmitterPressureRange(),
        )


def test_reference_100m_lateral_emitter_pressure_distribution():
    """Validate pressure at all 200 emitters in the reference lateral."""
    from irrigation.calculations.emitter_pressure import (
        analyze_dripline_emitter_pressures,
    )

    result = analyze_dripline_emitter_pressures(
        inlet_pressure_bar=1.5,
        length_m=100,
        number_of_emitters=200,
        emitter_flow_lph=2,
        diameter_m=0.016,
        hazen_williams_c=150,
        pressure_range=EmitterPressureRange(
            minimum_bar=1.0,
            maximum_bar=4.0,
        ),
    )

    pressures = result["emitter_pressures_bar"]

    assert result["total_emitters"] == 200
    assert len(pressures) == 200
    assert pressures[0] == pytest.approx(1.4987028, rel=1e-6)
    assert pressures[-1] == pytest.approx(1.4083823, rel=1e-6)
    assert all(
        pressures[index] > pressures[index + 1]
        for index in range(len(pressures) - 1)
    )
    assert result["head_loss_m"] == pytest.approx(0.9342403, rel=1e-6)
    assert result["emitters_within_range"] == 200
    assert result["emitters_outside_range"] == 0
    assert result["compliance_percentage"] == pytest.approx(100.0)
    assert result["all_pressures_within_range"] is True




def test_pressure_analysis_passes_emitter_connection_k_to_model():
    baseline = analyze_dripline_pressure(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
    )
    with_local_losses = analyze_dripline_pressure(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
        emitter_connection_k=1.0,
    )
    assert with_local_losses["head_loss_m"] > baseline["head_loss_m"]
    assert (
        with_local_losses["outlet_pressure_bar"]
        < baseline["outlet_pressure_bar"]
    )
