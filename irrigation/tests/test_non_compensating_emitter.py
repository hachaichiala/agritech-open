import pytest

from irrigation.calculations import analyze_non_compensating_dripline


def _base(**overrides):
    values = dict(
        inlet_pressure_bar=2.0,
        length_m=30.0,
        number_of_emitters=12,
        reference_flow_lph=4.0,
        reference_pressure_bar=1.0,
        discharge_exponent=0.5,
        diameter_m=0.020,
        hazen_williams_c=150,
    )
    values.update(overrides)
    return values


def test_non_compensating_solver_converges_and_reports_flow_distribution():
    result = analyze_non_compensating_dripline(**_base())
    assert result["converged"] is True
    assert result["iterations"] > 0
    assert len(result["emitter_flows_lph"]) == 12
    assert len(result["emitter_pressures_bar"]) == 12
    assert result["total_flow_lph"] == pytest.approx(sum(result["emitter_flows_lph"]))
    assert result["minimum_flow_lph"] < result["maximum_flow_lph"]
    assert 0 < result["flow_uniformity_percentage"] <= 100


def test_zero_discharge_exponent_preserves_constant_emitter_flow():
    result = analyze_non_compensating_dripline(**_base(discharge_exponent=0.0))
    assert result["emitter_flows_lph"] == pytest.approx([4.0] * 12)
    assert result["total_flow_lph"] == pytest.approx(48.0)


def test_positive_discharge_exponent_responds_to_local_pressure():
    result = analyze_non_compensating_dripline(**_base())
    assert result["emitter_pressures_bar"][0] > result["emitter_pressures_bar"][-1]
    assert result["emitter_flows_lph"][0] > result["emitter_flows_lph"][-1]


def test_reference_pressure_changes_calculated_emitter_flow():
    at_reference = analyze_non_compensating_dripline(**_base(reference_pressure_bar=2.0))
    lower_reference = analyze_non_compensating_dripline(**_base(reference_pressure_bar=1.0))
    assert lower_reference["total_flow_lph"] > at_reference["total_flow_lph"]


def test_elevation_profile_affects_pressure_and_flow():
    flat = analyze_non_compensating_dripline(**_base())
    uphill = analyze_non_compensating_dripline(
        **_base(emitter_elevations_m=[i * 0.1 for i in range(12)])
    )
    assert uphill["outlet_pressure_bar"] < flat["outlet_pressure_bar"]
    assert uphill["total_flow_lph"] < flat["total_flow_lph"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"inlet_pressure_bar": 0},
        {"reference_flow_lph": 0},
        {"reference_pressure_bar": 0},
        {"discharge_exponent": -0.1},
        {"length_m": 0},
        {"diameter_m": 0},
        {"emitter_connection_k": -1},
        {"tolerance": 0},
        {"number_of_emitters": 0},
        {"max_iterations": 0},
        {"emitter_elevations_m": [0.0]},
    ],
)
def test_invalid_non_compensating_inputs_are_rejected(overrides):
    with pytest.raises(ValueError):
        analyze_non_compensating_dripline(**_base(**overrides))


def test_solver_reports_non_convergence_when_iteration_limit_is_too_low():
    with pytest.raises(ValueError, match="did not converge"):
        analyze_non_compensating_dripline(
            **_base(max_iterations=1, tolerance=1e-14)
        )


def test_segment_losses_sum_to_total_head_loss():
    result = analyze_non_compensating_dripline(**_base(emitter_connection_k=0.0))
    assert all(loss > 0 for loss in result["segment_head_losses_m"])
    assert sum(result["segment_head_losses_m"]) == pytest.approx(result["head_loss_m"])


from irrigation.calculations import analyze_emitter_flow_distribution


def test_flow_distribution_reports_low_quarter_uniformity():
    result = analyze_emitter_flow_distribution([2.0, 3.0, 4.0, 5.0])

    assert result["low_quarter_emitters"] == 1
    assert result["low_quarter_mean_flow_lph"] == pytest.approx(2.0)
    assert result["mean_flow_lph"] == pytest.approx(3.5)
    assert result["low_quarter_distribution_uniformity_percentage"] == pytest.approx(
        2.0 / 3.5 * 100.0
    )
    assert result["minimum_to_maximum_flow_ratio_percentage"] == pytest.approx(40.0)


def test_flow_distribution_uses_ceil_for_low_quarter_sample_count():
    result = analyze_emitter_flow_distribution([1.0, 2.0, 3.0, 4.0, 5.0])

    assert result["low_quarter_emitters"] == 2
    assert result["low_quarter_mean_flow_lph"] == pytest.approx(1.5)


def test_equal_emitter_flows_have_full_distribution_uniformity():
    result = analyze_emitter_flow_distribution([4.0] * 8)

    assert result["low_quarter_distribution_uniformity_percentage"] == pytest.approx(100.0)
    assert result["minimum_to_maximum_flow_ratio_percentage"] == pytest.approx(100.0)


def test_flow_distribution_is_independent_of_input_order():
    first = analyze_emitter_flow_distribution([1.0, 2.0, 3.0, 4.0])
    second = analyze_emitter_flow_distribution([4.0, 3.0, 2.0, 1.0])

    assert first == second


def test_flow_distribution_scales_with_flow_units():
    base = analyze_emitter_flow_distribution([1.0, 2.0, 3.0, 4.0])
    scaled = analyze_emitter_flow_distribution([10.0, 20.0, 30.0, 40.0])

    assert scaled["low_quarter_distribution_uniformity_percentage"] == pytest.approx(
        base["low_quarter_distribution_uniformity_percentage"]
    )


@pytest.mark.parametrize(
    "flows",
    [[], [0.0, 1.0], [-1.0, 2.0], [float("nan"), 1.0],
     [float("inf"), 1.0], [True, 2.0], ["2", 3.0], None],
)
def test_flow_distribution_rejects_invalid_inputs(flows):
    with pytest.raises(ValueError):
        analyze_emitter_flow_distribution(flows)


def test_non_compensating_solver_reports_standard_low_quarter_uniformity():
    result = analyze_non_compensating_dripline(**_base())

    expected = analyze_emitter_flow_distribution(result["emitter_flows_lph"])
    assert result["low_quarter_distribution_uniformity_percentage"] == pytest.approx(
        expected["low_quarter_distribution_uniformity_percentage"]
    )
    assert result["flow_uniformity_percentage"] == pytest.approx(
        result["minimum_to_maximum_flow_ratio_percentage"]
    )


def test_solver_reports_downstream_segment_flows_and_mass_balance():
    result = analyze_non_compensating_dripline(**_base())

    segment_flows = result["segment_flows_lph"]
    emitter_flows = result["emitter_flows_lph"]

    assert len(segment_flows) == len(emitter_flows)
    assert segment_flows[0] == pytest.approx(result["total_flow_lph"])
    assert segment_flows[-1] == pytest.approx(emitter_flows[-1])
    assert all(
        segment_flows[index] > segment_flows[index + 1]
        for index in range(len(segment_flows) - 1)
    )
    for index, segment_flow in enumerate(segment_flows):
        assert segment_flow == pytest.approx(sum(emitter_flows[index:]))


def test_zero_discharge_exponent_segment_flows_match_constant_outlets():
    result = analyze_non_compensating_dripline(
        **_base(discharge_exponent=0.0)
    )

    assert result["segment_flows_lph"] == pytest.approx(
        [4.0 * count for count in range(12, 0, -1)]
    )


def test_uphill_profile_reduces_local_pressure_and_total_flow():
    flat = analyze_non_compensating_dripline(**_base())
    uphill = analyze_non_compensating_dripline(
        **_base(emitter_elevations_m=[0.25 * i for i in range(12)])
    )

    # Compare the downstream endpoint. Intermediate pressures also reflect
    # the solver's redistribution of emitter flows and segment friction losses.
    assert uphill["outlet_pressure_bar"] < flat["outlet_pressure_bar"]
    assert uphill["total_flow_lph"] < flat["total_flow_lph"]


def test_downhill_profile_increases_local_pressure_and_total_flow():
    flat = analyze_non_compensating_dripline(**_base())
    downhill = analyze_non_compensating_dripline(
        **_base(emitter_elevations_m=[-0.25 * i for i in range(12)])
    )

    # Compare the downstream endpoint. Intermediate pressures also reflect
    # the solver's redistribution of emitter flows and segment friction losses.
    assert downhill["outlet_pressure_bar"] > flat["outlet_pressure_bar"]
    assert downhill["total_flow_lph"] > flat["total_flow_lph"]


def test_emitter_connection_losses_reduce_pressure_and_flow():
    without_connections = analyze_non_compensating_dripline(
        **_base(emitter_connection_k=0.0)
    )
    with_connections = analyze_non_compensating_dripline(
        **_base(emitter_connection_k=1.0)
    )

    assert all(
        connected < plain
        for connected, plain in zip(
            with_connections["emitter_pressures_bar"],
            without_connections["emitter_pressures_bar"],
        )
    )
    assert with_connections["total_flow_lph"] < without_connections["total_flow_lph"]
    assert with_connections["head_loss_m"] > without_connections["head_loss_m"]


def test_zero_exponent_pressure_profile_matches_independent_head_balance():
    result = analyze_non_compensating_dripline(
        **_base(
            discharge_exponent=0.0,
            emitter_connection_k=0.75,
            emitter_elevations_m=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5,
                                  0.6, 0.7, 0.8, 0.9, 1.0, 1.1],
        )
    )

    cumulative_loss = 0.0
    for index, segment_loss in enumerate(result["segment_head_losses_m"]):
        cumulative_loss += segment_loss
        expected_pressure = (
            2.0
            - (cumulative_loss + 0.1 * index) * 0.0980665
        )
        assert result["emitter_pressures_bar"][index] == pytest.approx(
            expected_pressure, rel=1e-10, abs=1e-10
        )


def test_non_compensating_emitter_curve_holds_at_each_converged_pressure():
    result = analyze_non_compensating_dripline(**_base())

    expected_flows = [
        4.0 * (pressure / 1.0) ** 0.5
        for pressure in result["emitter_pressures_bar"]
    ]
    assert result["emitter_flows_lph"] == pytest.approx(
        expected_flows, rel=1e-7
    )
