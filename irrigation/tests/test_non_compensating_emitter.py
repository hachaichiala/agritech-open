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
