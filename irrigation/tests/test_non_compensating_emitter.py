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



def test_higher_inlet_pressure_increases_emitter_flows_and_local_pressures():
    low = analyze_non_compensating_dripline(
        **_base(inlet_pressure_bar=1.5)
    )
    nominal = analyze_non_compensating_dripline(
        **_base(inlet_pressure_bar=2.0)
    )
    high = analyze_non_compensating_dripline(
        **_base(inlet_pressure_bar=2.5)
    )

    assert low["converged"] is True
    assert nominal["converged"] is True
    assert high["converged"] is True
    assert low["total_flow_lph"] < nominal["total_flow_lph"] < high["total_flow_lph"]
    assert low["head_loss_m"] < nominal["head_loss_m"] < high["head_loss_m"]

    for low_pressure, nominal_pressure, high_pressure in zip(
        low["emitter_pressures_bar"],
        nominal["emitter_pressures_bar"],
        high["emitter_pressures_bar"],
    ):
        assert low_pressure < nominal_pressure < high_pressure


def test_inlet_pressure_shift_preserves_flows_for_zero_discharge_exponent():
    low = analyze_non_compensating_dripline(
        **_base(inlet_pressure_bar=1.5, discharge_exponent=0.0)
    )
    high = analyze_non_compensating_dripline(
        **_base(inlet_pressure_bar=2.5, discharge_exponent=0.0)
    )

    assert high["emitter_flows_lph"] == pytest.approx(
        low["emitter_flows_lph"]
    )
    assert high["segment_flows_lph"] == pytest.approx(
        low["segment_flows_lph"]
    )
    assert high["segment_head_losses_m"] == pytest.approx(
        low["segment_head_losses_m"]
    )
    assert [
        high_pressure - low_pressure
        for high_pressure, low_pressure in zip(
            high["emitter_pressures_bar"],
            low["emitter_pressures_bar"],
        )
    ] == pytest.approx([1.0] * 12)


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


def test_connection_k_losses_match_independent_velocity_head_calculation():
    import math

    connection_k = 0.75
    diameter_m = 0.020
    segment_length_m = 30.0 / 12
    hazen_williams_c = 150.0
    gravity_m_s2 = 9.80665
    result = analyze_non_compensating_dripline(
        **_base(
            discharge_exponent=0.0,
            emitter_connection_k=connection_k,
            emitter_elevations_m=[0.1 * i for i in range(12)],
        )
    )

    area_m2 = math.pi * diameter_m ** 2 / 4.0
    cumulative_loss_m = 0.0

    for index in range(12):
        downstream_flow_lph = 4.0 * (12 - index)
        flow_m3_s = downstream_flow_lph / 3_600_000.0
        velocity_m_s = flow_m3_s / area_m2

        friction_loss_m = (
            10.67
            * segment_length_m
            * flow_m3_s ** 1.852
            / (
                hazen_williams_c ** 1.852
                * diameter_m ** 4.871
            )
        )
        connection_loss_m = (
            connection_k
            * velocity_m_s ** 2
            / (2.0 * gravity_m_s2)
        )
        expected_segment_loss_m = friction_loss_m + connection_loss_m
        cumulative_loss_m += expected_segment_loss_m

        assert result["segment_head_losses_m"][index] == pytest.approx(
            expected_segment_loss_m, rel=1e-10, abs=1e-12
        )

        expected_pressure_bar = (
            2.0
            - (cumulative_loss_m + 0.1 * index) * 0.0980665
        )
        assert result["emitter_pressures_bar"][index] == pytest.approx(
            expected_pressure_bar, rel=1e-10, abs=1e-10
        )

    assert result["head_loss_m"] == pytest.approx(cumulative_loss_m)


def test_doubling_lateral_length_doubles_friction_loss_with_fixed_outlet_flows():
    common = _base(
        discharge_exponent=0.0,
        emitter_connection_k=0.0,
    )
    standard = analyze_non_compensating_dripline(**common)
    doubled = analyze_non_compensating_dripline(
        **{**common, "length_m": common["length_m"] * 2.0}
    )

    assert doubled["emitter_flows_lph"] == pytest.approx(
        standard["emitter_flows_lph"]
    )
    assert doubled["segment_flows_lph"] == pytest.approx(
        standard["segment_flows_lph"]
    )
    assert doubled["head_loss_m"] == pytest.approx(
        standard["head_loss_m"] * 2.0, rel=1e-10
    )
    assert doubled["head_loss_m"] == pytest.approx(
        sum(doubled["segment_head_losses_m"]), rel=1e-12
    )
    assert doubled["outlet_pressure_bar"] < standard["outlet_pressure_bar"]


def test_larger_lateral_diameter_matches_hazen_williams_scaling():
    standard_diameter_m = 0.020
    larger_diameter_m = 0.025
    common = _base(
        discharge_exponent=0.0,
        emitter_connection_k=0.0,
        diameter_m=standard_diameter_m,
    )
    standard = analyze_non_compensating_dripline(**common)
    larger = analyze_non_compensating_dripline(
        **{**common, "diameter_m": larger_diameter_m}
    )

    expected_loss_ratio = (
        standard_diameter_m / larger_diameter_m
    ) ** 4.871

    assert larger["emitter_flows_lph"] == pytest.approx(
        standard["emitter_flows_lph"]
    )
    assert larger["segment_flows_lph"] == pytest.approx(
        standard["segment_flows_lph"]
    )
    assert larger["head_loss_m"] / standard["head_loss_m"] == pytest.approx(
        expected_loss_ratio, rel=1e-10
    )
    assert larger["head_loss_m"] == pytest.approx(
        sum(larger["segment_head_losses_m"]), rel=1e-12
    )
    assert larger["outlet_pressure_bar"] > standard["outlet_pressure_bar"]


def test_longer_lateral_reduces_coupled_emitter_flow_and_outlet_pressure():
    standard = analyze_non_compensating_dripline(**_base())
    longer = analyze_non_compensating_dripline(
        **_base(length_m=60.0)
    )

    assert longer["converged"] is True
    assert longer["total_flow_lph"] < standard["total_flow_lph"]
    assert longer["outlet_pressure_bar"] < standard["outlet_pressure_bar"]
    assert longer["head_loss_m"] > standard["head_loss_m"]
    assert longer["total_flow_lph"] == pytest.approx(
        sum(longer["emitter_flows_lph"])
    )
    assert longer["segment_flows_lph"] == pytest.approx(
        [
            sum(longer["emitter_flows_lph"][index:])
            for index in range(len(longer["emitter_flows_lph"]))
        ]
    )
    assert longer["head_loss_m"] == pytest.approx(
        sum(longer["segment_head_losses_m"])
    )


def test_larger_diameter_improves_coupled_emitter_flow_and_pressure():
    standard = analyze_non_compensating_dripline(**_base())
    larger = analyze_non_compensating_dripline(
        **_base(diameter_m=0.025)
    )

    assert larger["converged"] is True
    assert larger["total_flow_lph"] > standard["total_flow_lph"]
    assert larger["outlet_pressure_bar"] > standard["outlet_pressure_bar"]
    assert larger["head_loss_m"] < standard["head_loss_m"]
    assert larger["total_flow_lph"] == pytest.approx(
        sum(larger["emitter_flows_lph"])
    )
    assert larger["segment_flows_lph"] == pytest.approx(
        [
            sum(larger["emitter_flows_lph"][index:])
            for index in range(len(larger["emitter_flows_lph"]))
        ]
    )
    assert larger["head_loss_m"] == pytest.approx(
        sum(larger["segment_head_losses_m"])
    )


def test_more_emitters_at_fixed_spacing_increase_total_flow_and_head_loss():
    standard = analyze_non_compensating_dripline(
        **_base(discharge_exponent=0.0)
    )
    increased_count = analyze_non_compensating_dripline(
        **_base(
            discharge_exponent=0.0,
            number_of_emitters=24,
            length_m=60.0,
        )
    )

    assert increased_count["total_flow_lph"] == pytest.approx(
        standard["total_flow_lph"] * 2.0
    )
    assert increased_count["segment_flows_lph"][0] == pytest.approx(
        increased_count["total_flow_lph"]
    )
    assert increased_count["segment_flows_lph"] == pytest.approx(
        [4.0 * count for count in range(24, 0, -1)]
    )
    assert increased_count["head_loss_m"] > standard["head_loss_m"]
    assert increased_count["outlet_pressure_bar"] < standard["outlet_pressure_bar"]
    assert increased_count["head_loss_m"] == pytest.approx(
        sum(increased_count["segment_head_losses_m"])
    )


def test_closer_emitter_spacing_reduces_friction_loss_at_fixed_emitter_count():
    standard = analyze_non_compensating_dripline(
        **_base(discharge_exponent=0.0)
    )
    closer_spacing = analyze_non_compensating_dripline(
        **_base(discharge_exponent=0.0, length_m=15.0)
    )

    assert closer_spacing["emitter_flows_lph"] == pytest.approx(
        standard["emitter_flows_lph"]
    )
    assert closer_spacing["segment_flows_lph"] == pytest.approx(
        standard["segment_flows_lph"]
    )
    assert closer_spacing["head_loss_m"] == pytest.approx(
        standard["head_loss_m"] * 0.5, rel=1e-10
    )
    assert closer_spacing["outlet_pressure_bar"] > standard["outlet_pressure_bar"]
    assert closer_spacing["head_loss_m"] == pytest.approx(
        sum(closer_spacing["segment_head_losses_m"])
    )


def test_higher_hazen_williams_coefficient_reduces_friction_loss():
    standard_c = 150.0
    smoother_pipe_c = 160.0
    common = _base(
        discharge_exponent=0.0,
        emitter_connection_k=0.0,
        hazen_williams_c=standard_c,
    )
    standard = analyze_non_compensating_dripline(**common)
    smoother_pipe = analyze_non_compensating_dripline(
        **{**common, "hazen_williams_c": smoother_pipe_c}
    )

    expected_loss_ratio = (standard_c / smoother_pipe_c) ** 1.852

    assert smoother_pipe["emitter_flows_lph"] == pytest.approx(
        standard["emitter_flows_lph"]
    )
    assert smoother_pipe["head_loss_m"] / standard["head_loss_m"] == pytest.approx(
        expected_loss_ratio, rel=1e-10
    )
    assert smoother_pipe["outlet_pressure_bar"] > standard["outlet_pressure_bar"]
    assert smoother_pipe["head_loss_m"] == pytest.approx(
        sum(smoother_pipe["segment_head_losses_m"])
    )


def test_emitter_connection_k_adds_expected_minor_head_loss():
    connection_k = 0.75
    no_connection_loss = analyze_non_compensating_dripline(
        **_base(discharge_exponent=0.0, emitter_connection_k=0.0)
    )
    with_connection_loss = analyze_non_compensating_dripline(
        **_base(
            discharge_exponent=0.0,
            emitter_connection_k=connection_k,
        )
    )

    import math

    diameter_m = 0.020
    area_m2 = math.pi * diameter_m ** 2 / 4.0
    expected_minor_loss_m = 0.0
    for count in range(12, 0, -1):
        flow_m3_s = (4.0 * count) / 3_600_000.0
        velocity_m_s = flow_m3_s / area_m2
        expected_minor_loss_m += (
            connection_k * velocity_m_s ** 2 / (2.0 * 9.80665)
        )

    assert with_connection_loss["emitter_flows_lph"] == pytest.approx(
        no_connection_loss["emitter_flows_lph"]
    )
    assert (
        with_connection_loss["head_loss_m"]
        - no_connection_loss["head_loss_m"]
    ) == pytest.approx(expected_minor_loss_m, rel=1e-10)
    assert with_connection_loss["outlet_pressure_bar"] < (
        no_connection_loss["outlet_pressure_bar"]
    )
    assert with_connection_loss["head_loss_m"] == pytest.approx(
        sum(with_connection_loss["segment_head_losses_m"])
    )


def test_tighter_solver_tolerance_stabilizes_emitter_flows_and_pressures():
    loose = analyze_non_compensating_dripline(
        **_base(tolerance=1e-6, max_iterations=1000)
    )
    tight = analyze_non_compensating_dripline(
        **_base(tolerance=1e-10, max_iterations=1000)
    )
    reference = analyze_non_compensating_dripline(
        **_base(tolerance=1e-12, max_iterations=2000)
    )

    loose_flow_error = max(
        abs(value - reference_value)
        for value, reference_value in zip(
            loose["emitter_flows_lph"], reference["emitter_flows_lph"]
        )
    )
    tight_flow_error = max(
        abs(value - reference_value)
        for value, reference_value in zip(
            tight["emitter_flows_lph"], reference["emitter_flows_lph"]
        )
    )
    loose_pressure_error = max(
        abs(value - reference_value)
        for value, reference_value in zip(
            loose["emitter_pressures_bar"], reference["emitter_pressures_bar"]
        )
    )
    tight_pressure_error = max(
        abs(value - reference_value)
        for value, reference_value in zip(
            tight["emitter_pressures_bar"], reference["emitter_pressures_bar"]
        )
    )

    assert loose["converged"] is True
    assert tight["converged"] is True
    assert reference["converged"] is True
    assert tight["iterations"] >= loose["iterations"]
    assert tight_flow_error <= loose_flow_error
    assert tight_pressure_error <= loose_pressure_error
    assert tight["total_flow_lph"] == pytest.approx(
        sum(tight["emitter_flows_lph"])
    )


def test_solver_results_are_deterministic_for_identical_inputs():
    first = analyze_non_compensating_dripline(
        **_base(tolerance=1e-9)
    )
    second = analyze_non_compensating_dripline(
        **_base(tolerance=1e-9)
    )

    assert second["emitter_flows_lph"] == pytest.approx(
        first["emitter_flows_lph"], rel=0.0, abs=0.0
    )
    assert second["emitter_pressures_bar"] == pytest.approx(
        first["emitter_pressures_bar"], rel=0.0, abs=0.0
    )
    assert second["segment_flows_lph"] == pytest.approx(
        first["segment_flows_lph"], rel=0.0, abs=0.0
    )
    assert second["segment_head_losses_m"] == pytest.approx(
        first["segment_head_losses_m"], rel=0.0, abs=0.0
    )
    assert second["iterations"] == first["iterations"]



@pytest.mark.parametrize("elevation_offset_m", [1.0, -1.0])
def test_uniform_elevation_offset_shifts_pressure_without_changing_fixed_emitter_flows(
    elevation_offset_m,
):
    flat = analyze_non_compensating_dripline(
        **_base(discharge_exponent=0.0)
    )
    shifted = analyze_non_compensating_dripline(
        **_base(
            discharge_exponent=0.0,
            emitter_elevations_m=[elevation_offset_m] * 12,
        )
    )

    expected_pressure_shift_bar = -elevation_offset_m * 0.0980665

    assert shifted["converged"] is True
    assert shifted["emitter_flows_lph"] == pytest.approx(
        flat["emitter_flows_lph"]
    )
    assert shifted["segment_flows_lph"] == pytest.approx(
        flat["segment_flows_lph"]
    )
    assert shifted["segment_head_losses_m"] == pytest.approx(
        flat["segment_head_losses_m"]
    )
    assert [
        shifted_pressure - flat_pressure
        for shifted_pressure, flat_pressure in zip(
            shifted["emitter_pressures_bar"],
            flat["emitter_pressures_bar"],
        )
    ] == pytest.approx([expected_pressure_shift_bar] * 12)
    assert shifted["outlet_pressure_bar"] - flat["outlet_pressure_bar"] == pytest.approx(
        expected_pressure_shift_bar
    )


@pytest.mark.parametrize(
    ("elevation_offset_m", "pressure_comparison", "flow_comparison", "loss_comparison"),
    [
        (1.0, "lower", "lower", "lower"),
        (-1.0, "higher", "higher", "higher"),
    ],
)
def test_uniform_elevation_offset_changes_pressure_dependent_emitter_operation(
    elevation_offset_m,
    pressure_comparison,
    flow_comparison,
    loss_comparison,
):
    flat = analyze_non_compensating_dripline(**_base())
    shifted = analyze_non_compensating_dripline(
        **_base(emitter_elevations_m=[elevation_offset_m] * 12)
    )

    assert shifted["converged"] is True

    for shifted_pressure, flat_pressure in zip(
        shifted["emitter_pressures_bar"],
        flat["emitter_pressures_bar"],
    ):
        if pressure_comparison == "lower":
            assert shifted_pressure < flat_pressure
        else:
            assert shifted_pressure > flat_pressure

    for shifted_flow, flat_flow in zip(
        shifted["emitter_flows_lph"],
        flat["emitter_flows_lph"],
    ):
        if flow_comparison == "lower":
            assert shifted_flow < flat_flow
        else:
            assert shifted_flow > flat_flow

    if loss_comparison == "lower":
        assert shifted["total_flow_lph"] < flat["total_flow_lph"]
        assert shifted["head_loss_m"] < flat["head_loss_m"]
    else:
        assert shifted["total_flow_lph"] > flat["total_flow_lph"]
        assert shifted["head_loss_m"] > flat["head_loss_m"]

    assert shifted["total_flow_lph"] == pytest.approx(
        sum(shifted["emitter_flows_lph"])
    )
    assert shifted["head_loss_m"] == pytest.approx(
        sum(shifted["segment_head_losses_m"])
    )


def test_non_monotonic_elevation_profile_applies_each_emitter_elevation_independently():
    import math

    elevations_m = [
        0.0, 0.3, 0.1, 0.6, 0.2, 0.8,
        0.4, 1.0, 0.5, 0.7, 0.2, -0.1,
    ]
    connection_k = 0.5
    result = analyze_non_compensating_dripline(
        **_base(
            discharge_exponent=0.0,
            emitter_connection_k=connection_k,
            emitter_elevations_m=elevations_m,
        )
    )

    assert result["converged"] is True
    assert result["emitter_flows_lph"] == pytest.approx([4.0] * 12)
    assert result["segment_flows_lph"] == pytest.approx(
        [4.0 * count for count in range(12, 0, -1)]
    )

    area_m2 = math.pi * 0.020 ** 2 / 4.0
    cumulative_loss_m = 0.0

    for index, elevation_m in enumerate(elevations_m):
        flow_m3_s = (4.0 * (12 - index)) / 3_600_000.0
        velocity_m_s = flow_m3_s / area_m2
        friction_loss_m = (
            10.67
            * (30.0 / 12)
            * flow_m3_s ** 1.852
            / (150.0 ** 1.852 * 0.020 ** 4.871)
        )
        connection_loss_m = (
            connection_k * velocity_m_s ** 2 / (2.0 * 9.80665)
        )
        cumulative_loss_m += friction_loss_m + connection_loss_m

        expected_pressure_bar = (
            2.0 - (cumulative_loss_m + elevation_m) * 0.0980665
        )
        assert result["emitter_pressures_bar"][index] == pytest.approx(
            expected_pressure_bar, rel=1e-10, abs=1e-10
        )

    assert result["head_loss_m"] == pytest.approx(
        sum(result["segment_head_losses_m"])
    )


def test_permuting_elevation_profile_preserves_fixed_flow_hydraulics():
    elevations_m = [
        -0.2, 0.0, 0.15, 0.4, 0.25, 0.7,
        0.5, 0.9, 0.1, 0.6, 0.3, 0.8,
    ]
    permuted_elevations_m = list(reversed(elevations_m))

    original = analyze_non_compensating_dripline(
        **_base(
            discharge_exponent=0.0,
            emitter_elevations_m=elevations_m,
        )
    )
    permuted = analyze_non_compensating_dripline(
        **_base(
            discharge_exponent=0.0,
            emitter_elevations_m=permuted_elevations_m,
        )
    )
    flat = analyze_non_compensating_dripline(
        **_base(discharge_exponent=0.0)
    )

    assert original["converged"] is True
    assert permuted["converged"] is True
    assert permuted["emitter_flows_lph"] == pytest.approx(
        original["emitter_flows_lph"]
    )
    assert permuted["segment_flows_lph"] == pytest.approx(
        original["segment_flows_lph"]
    )
    assert permuted["segment_head_losses_m"] == pytest.approx(
        original["segment_head_losses_m"]
    )
    assert permuted["head_loss_m"] == pytest.approx(original["head_loss_m"])
    assert permuted["total_flow_lph"] == pytest.approx(original["total_flow_lph"])

    for result, profile in (
        (original, elevations_m),
        (permuted, permuted_elevations_m),
    ):
        expected_pressures = [
            flat_pressure - elevation_m * 0.0980665
            for flat_pressure, elevation_m in zip(
                flat["emitter_pressures_bar"], profile
            )
        ]
        assert result["emitter_pressures_bar"] == pytest.approx(
            expected_pressures
        )


def test_single_emitter_has_one_segment_and_balanced_flow():
    result = analyze_non_compensating_dripline(
        **_base(
            number_of_emitters=1,
            discharge_exponent=0.0,
            emitter_connection_k=0.0,
        )
    )

    assert result["converged"] is True
    assert result["emitter_flows_lph"] == pytest.approx([4.0])
    assert result["emitter_pressures_bar"] == pytest.approx(
        [result["outlet_pressure_bar"]]
    )
    assert result["segment_flows_lph"] == pytest.approx([4.0])
    assert len(result["segment_head_losses_m"]) == 1
    assert result["total_flow_lph"] == pytest.approx(4.0)
    assert result["minimum_flow_lph"] == pytest.approx(4.0)
    assert result["maximum_flow_lph"] == pytest.approx(4.0)
    assert result["head_loss_m"] == pytest.approx(
        sum(result["segment_head_losses_m"])
    )

