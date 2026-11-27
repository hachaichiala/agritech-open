
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



def test_emitter_pressure_analysis_accounts_for_lateral_elevation():
    from irrigation.calculations.emitter_pressure import (
        analyze_dripline_emitter_pressures,
    )

    common = dict(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
    )
    horizontal = analyze_dripline_emitter_pressures(**common)
    uphill = analyze_dripline_emitter_pressures(
        **common, emitter_elevations_m=[0.5, 1.0, 1.5]
    )
    assert uphill["outlet_pressure_bar"] < horizontal["outlet_pressure_bar"]
    assert uphill["head_loss_m"] == pytest.approx(horizontal["head_loss_m"])
    assert uphill["emitter_pressures_bar"][-1] == pytest.approx(
        horizontal["emitter_pressures_bar"][-1] - 1.5 * 0.0980665
    )



def test_analyze_dripline_pressure_accounts_for_uphill_elevation():
    common = dict(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
    )
    horizontal = analyze_dripline_pressure(**common)
    uphill = analyze_dripline_pressure(
        **common, emitter_elevations_m=[0.5, 1.0, 1.5]
    )
    assert uphill["head_loss_m"] == pytest.approx(horizontal["head_loss_m"])
    assert uphill["outlet_pressure_bar"] == pytest.approx(
        horizontal["outlet_pressure_bar"] - 1.5 * 0.0980665
    )
    assert uphill["pressure_head_change_m"] > horizontal["pressure_head_change_m"]


def test_analyze_dripline_pressure_accounts_for_downhill_elevation():
    common = dict(
        inlet_pressure_bar=2.0,
        length_m=20,
        number_of_emitters=3,
        emitter_flow_lph=8,
        diameter_m=0.016,
        pressure_range=EmitterPressureRange(),
    )
    horizontal = analyze_dripline_pressure(**common)
    downhill = analyze_dripline_pressure(
        **common, emitter_elevations_m=[-0.5, -1.0, -1.5]
    )
    assert downhill["outlet_pressure_bar"] > horizontal["outlet_pressure_bar"]
    assert downhill["pressure_head_change_m"] < horizontal["pressure_head_change_m"]


def test_analyze_dripline_pressure_rejects_invalid_elevation_profile():
    with pytest.raises(ValueError, match="Emitter elevations"):
        analyze_dripline_pressure(
            inlet_pressure_bar=2.0,
            length_m=20,
            number_of_emitters=3,
            emitter_flow_lph=8,
            diameter_m=0.016,
            pressure_range=EmitterPressureRange(),
            emitter_elevations_m=[0.0, 1.0],
        )



def _non_compensating_inputs(**overrides):
    from irrigation.calculations.emitter_pressure import (
        analyze_non_compensating_dripline,
    )

    parameters = {
        "inlet_pressure_bar": 2.5,
        "length_m": 100.0,
        "number_of_emitters": 40,
        "reference_flow_lph": 2.0,
        "reference_pressure_bar": 1.0,
        "discharge_exponent": 0.5,
        "diameter_m": 0.012,
        "hazen_williams_c": 150.0,
    }
    parameters.update(overrides)
    return analyze_non_compensating_dripline(**parameters)


def test_non_compensating_zero_exponent_preserves_constant_emitter_flow():
    from irrigation.calculations.emitter_pressure import (
        analyze_non_compensating_dripline,
    )

    result = analyze_non_compensating_dripline(
        inlet_pressure_bar=2.0,
        length_m=30.0,
        number_of_emitters=12,
        reference_flow_lph=2.0,
        reference_pressure_bar=1.0,
        discharge_exponent=0.0,
        diameter_m=0.016,
    )

    assert result["converged"] is True
    assert result["iterations"] == 1
    assert result["emitter_flows_lph"] == pytest.approx([2.0] * 12)
    assert result["total_flow_lph"] == pytest.approx(24.0)
    assert result["low_quarter_distribution_uniformity_percentage"] == pytest.approx(100.0)


def test_non_compensating_emitter_flow_decreases_with_pressure():
    result = _non_compensating_inputs()

    pressures = result["emitter_pressures_bar"]
    flows = result["emitter_flows_lph"]

    assert all(p > 0 for p in pressures)
    assert all(pressures[i] > pressures[i + 1] for i in range(len(pressures) - 1))
    assert all(flows[i] > flows[i + 1] for i in range(len(flows) - 1))
    assert result["maximum_flow_lph"] == pytest.approx(flows[0])
    assert result["minimum_flow_lph"] == pytest.approx(flows[-1])
    assert result["minimum_to_maximum_flow_ratio_percentage"] < 100.0


def test_non_compensating_segment_flows_satisfy_mass_balance():
    result = _non_compensating_inputs()

    expected_segment_flows = [
        sum(result["emitter_flows_lph"][index:])
        for index in range(len(result["emitter_flows_lph"]))
    ]

    assert result["segment_flows_lph"] == pytest.approx(expected_segment_flows)
    assert result["total_flow_lph"] == pytest.approx(
        sum(result["emitter_flows_lph"])
    )
    assert result["segment_flows_lph"][0] == pytest.approx(
        result["total_flow_lph"]
    )
    assert result["segment_flows_lph"][-1] == pytest.approx(
        result["emitter_flows_lph"][-1]
    )


def test_non_compensating_solver_reports_consistent_segment_losses():
    result = _non_compensating_inputs()

    assert len(result["segment_head_losses_m"]) == 40
    assert all(loss > 0 for loss in result["segment_head_losses_m"])
    assert result["head_loss_m"] == pytest.approx(
        sum(result["segment_head_losses_m"])
    )
    assert result["converged"] is True
    assert 1 <= result["iterations"] <= 500


def test_non_compensating_uphill_elevation_reduces_downstream_emitter_flow():
    flat = _non_compensating_inputs()
    uphill = _non_compensating_inputs(
        emitter_elevations_m=[
            0.05 * index for index in range(40)
        ]
    )

    assert uphill["emitter_pressures_bar"][-1] < flat["emitter_pressures_bar"][-1]
    assert uphill["emitter_flows_lph"][-1] < flat["emitter_flows_lph"][-1]


def test_non_compensating_connection_losses_reduce_outlet_pressure_and_flow():
    baseline = _non_compensating_inputs()
    with_connections = _non_compensating_inputs(emitter_connection_k=2.0)

    assert with_connections["head_loss_m"] > baseline["head_loss_m"]
    assert (
        with_connections["emitter_pressures_bar"][-1]
        < baseline["emitter_pressures_bar"][-1]
    )
    assert (
        with_connections["emitter_flows_lph"][-1]
        < baseline["emitter_flows_lph"][-1]
    )


@pytest.mark.parametrize(
    "parameter,value",
    [
        ("inlet_pressure_bar", 0.0),
        ("reference_flow_lph", -1.0),
        ("reference_pressure_bar", 0.0),
        ("discharge_exponent", -0.1),
        ("length_m", 0.0),
        ("diameter_m", 0.0),
        ("hazen_williams_c", 0.0),
        ("emitter_connection_k", -1.0),
        ("tolerance", 0.0),
        ("inlet_pressure_bar", float("inf")),
        ("reference_flow_lph", float("nan")),
        ("discharge_exponent", float("inf")),
    ],
)
def test_non_compensating_solver_rejects_invalid_numeric_inputs(
    parameter, value
):
    with pytest.raises(ValueError):
        _non_compensating_inputs(**{parameter: value})


@pytest.mark.parametrize("count", [0, -1, 2.5, True])
def test_non_compensating_solver_rejects_invalid_emitter_counts(count):
    with pytest.raises(ValueError, match="Number of emitters"):
        _non_compensating_inputs(number_of_emitters=count)


@pytest.mark.parametrize("iterations", [0, -1, 1.5, True])
def test_non_compensating_solver_rejects_invalid_iteration_limits(iterations):
    with pytest.raises(ValueError, match="Maximum iterations"):
        _non_compensating_inputs(max_iterations=iterations)


@pytest.mark.parametrize(
    "elevations",
    [
        [0.0],
        [0.0] * 39,
        [0.0] * 39 + [float("nan")],
        [0.0] * 39 + [float("inf")],
        [0.0] * 39 + [True],
    ],
)
def test_non_compensating_solver_rejects_invalid_elevation_profiles(elevations):
    with pytest.raises(ValueError, match="Emitter elevations"):
        _non_compensating_inputs(emitter_elevations_m=elevations)


def test_non_compensating_solver_raises_when_iteration_limit_is_insufficient():
    with pytest.raises(ValueError, match="did not converge"):
        _non_compensating_inputs(
            max_iterations=1,
            tolerance=1e-14,
        )


def test_non_compensating_solver_rejects_pressure_collapse():
    with pytest.raises(ValueError, match="Pressure reaches zero or below"):
        _non_compensating_inputs(
            inlet_pressure_bar=0.05,
            length_m=500.0,
            number_of_emitters=100,
            reference_flow_lph=8.0,
            reference_pressure_bar=1.0,
            discharge_exponent=0.5,
            diameter_m=0.004,
        )


def test_non_compensating_solver_supports_public_package_export():
    from irrigation.calculations import analyze_non_compensating_dripline

    assert callable(analyze_non_compensating_dripline)


def test_emitter_flow_distribution_uses_ceiling_for_low_quarter_count():
    from irrigation.calculations.emitter_pressure import (
        analyze_emitter_flow_distribution,
    )

    result = analyze_emitter_flow_distribution([1, 2, 3, 4, 5])

    assert result["low_quarter_emitters"] == 2
    assert result["low_quarter_mean_flow_lph"] == pytest.approx(1.5)
    assert result["mean_flow_lph"] == pytest.approx(3.0)
    assert result["low_quarter_distribution_uniformity_percentage"] == pytest.approx(50.0)
    assert result["minimum_to_maximum_flow_ratio_percentage"] == pytest.approx(20.0)


def test_emitter_flow_distribution_is_independent_of_input_order():
    from irrigation.calculations.emitter_pressure import (
        analyze_emitter_flow_distribution,
    )

    forward = analyze_emitter_flow_distribution([1, 2, 3, 4, 5, 6, 7])
    reverse = analyze_emitter_flow_distribution([7, 6, 5, 4, 3, 2, 1])

    assert forward["low_quarter_emitters"] == reverse["low_quarter_emitters"]
    assert forward["low_quarter_mean_flow_lph"] == pytest.approx(
        reverse["low_quarter_mean_flow_lph"]
    )
    assert forward["mean_flow_lph"] == pytest.approx(reverse["mean_flow_lph"])
    assert forward["low_quarter_distribution_uniformity_percentage"] == pytest.approx(
        reverse["low_quarter_distribution_uniformity_percentage"]
    )
    assert forward["minimum_to_maximum_flow_ratio_percentage"] == pytest.approx(
        reverse["minimum_to_maximum_flow_ratio_percentage"]
    )


def test_emitter_flow_distribution_percentages_are_scale_invariant():
    from irrigation.calculations.emitter_pressure import (
        analyze_emitter_flow_distribution,
    )

    baseline = analyze_emitter_flow_distribution([1, 2, 3, 4, 5, 6, 7, 8])
    scaled = analyze_emitter_flow_distribution([10, 20, 30, 40, 50, 60, 70, 80])

    assert scaled["low_quarter_distribution_uniformity_percentage"] == pytest.approx(
        baseline["low_quarter_distribution_uniformity_percentage"]
    )
    assert scaled["minimum_to_maximum_flow_ratio_percentage"] == pytest.approx(
        baseline["minimum_to_maximum_flow_ratio_percentage"]
    )
    assert scaled["mean_flow_lph"] == pytest.approx(
        baseline["mean_flow_lph"] * 10
    )
    assert scaled["low_quarter_mean_flow_lph"] == pytest.approx(
        baseline["low_quarter_mean_flow_lph"] * 10
    )


def test_emitter_flow_distribution_handles_single_emitter():
    from irrigation.calculations.emitter_pressure import (
        analyze_emitter_flow_distribution,
    )

    result = analyze_emitter_flow_distribution([3.5])

    assert result["total_emitters"] == 1
    assert result["low_quarter_emitters"] == 1
    assert result["mean_flow_lph"] == pytest.approx(3.5)
    assert result["low_quarter_mean_flow_lph"] == pytest.approx(3.5)
    assert result["low_quarter_distribution_uniformity_percentage"] == pytest.approx(100.0)
    assert result["minimum_to_maximum_flow_ratio_percentage"] == pytest.approx(100.0)


@pytest.mark.parametrize(
    "flows",
    [
        [],
        [0.0],
        [-1.0],
        [1.0, float("nan")],
        [1.0, float("inf")],
        [True],
        [1.0, "2.0"],
    ],
)
def test_emitter_flow_distribution_rejects_invalid_flows(flows):
    from irrigation.calculations.emitter_pressure import (
        analyze_emitter_flow_distribution,
    )

    with pytest.raises(ValueError):
        analyze_emitter_flow_distribution(flows)

