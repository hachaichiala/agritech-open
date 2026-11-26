import pytest

from irrigation.calculations.pipe_diameter_comparison import (
    compare_pipe_diameters,
)


PUMP = {
    "manufacturer": "Test",
    "model": "P-1",
    "pump_curve": [(0.0, 40.0), (0.001, 20.0)],
    "efficiency_curve": [(0.0, 50.0), (0.001, 60.0)],
}

SYSTEM = {
    "flow_rates_m3_s": [0.0, 0.0005, 0.001],
    "static_elevation_difference_m": 2.0,
    "required_sector_inlet_pressure_bar": 2.0,
    "upstream_pipe_length_m": 80.0,
    "upstream_pipe_diameter_m": 0.05,
    "hazen_williams_c": 150,
    "local_loss_coefficient": 2.0,
}


def test_compares_each_diameter_and_preserves_input_order():
    result = compare_pipe_diameters(PUMP, SYSTEM, [0.04, 0.05, 0.063])

    scenarios = result["scenarios"]
    assert [item["pipe_diameter_m"] for item in scenarios] == [
        0.04, 0.05, 0.063
    ]
    assert all(item["status"] == "success" for item in scenarios)
    assert all("analysis" in item for item in scenarios)


def test_larger_diameter_reduces_friction_and_operating_head():
    result = compare_pipe_diameters(PUMP, SYSTEM, [0.04, 0.063])
    small, large = result["scenarios"]

    small_detail = small["analysis"]["system"]["flow_details"][-1]
    large_detail = large["analysis"]["system"]["flow_details"][-1]
    assert large_detail["friction_loss_m"] < small_detail["friction_loss_m"]

    small_head = small["analysis"]["pump_analysis"]["operating_point"]["head_m"]
    large_head = large["analysis"]["pump_analysis"]["operating_point"]["head_m"]
    assert large_head < small_head


def test_each_scenario_returns_operating_flow_and_power():
    result = compare_pipe_diameters(PUMP, SYSTEM, [0.04, 0.063])

    for scenario in result["scenarios"]:
        analysis = scenario["analysis"]["pump_analysis"]
        assert analysis["operating_point"]["flow_m3_s"] > 0
        assert analysis["power"]["shaft_power_w"] > 0


def test_rejects_invalid_or_duplicate_diameters():
    with pytest.raises(ValueError, match="unique"):
        compare_pipe_diameters(PUMP, SYSTEM, [0.05, 0.05])
    with pytest.raises(ValueError, match="positive"):
        compare_pipe_diameters(PUMP, SYSTEM, [0.05, 0.0])


def test_rejects_fewer_than_two_diameters():
    with pytest.raises(ValueError, match="At least two"):
        compare_pipe_diameters(PUMP, SYSTEM, [0.05])


def test_records_a_diameter_without_operating_point():
    weak_pump = {
        "pump_curve": [(0.0, 1.0), (0.001, 0.5)],
        "efficiency_curve": [(0.0, 50.0), (0.001, 60.0)],
    }
    result = compare_pipe_diameters(weak_pump, SYSTEM, [0.04, 0.063])

    assert all(
        scenario["status"] == "no_valid_operating_analysis"
        for scenario in result["scenarios"]
    )
    assert all("error" in scenario for scenario in result["scenarios"])

@pytest.mark.parametrize(
    "invalid_diameter",
    [
        True,
        float("nan"),
        float("inf"),
        10**400,
        "0.05",
    ],
)
def test_rejects_boolean_non_finite_huge_and_non_numeric_diameters(
    invalid_diameter,
):
    with pytest.raises(ValueError, match="finite positive number"):
        compare_pipe_diameters(
            PUMP, SYSTEM, [0.04, invalid_diameter]
        )


def test_rejects_non_dictionary_system_parameters():
    with pytest.raises(ValueError, match="must be a dictionary"):
        compare_pipe_diameters(PUMP, [], [0.04, 0.063])


def test_rejects_non_sequence_diameter_collection():
    with pytest.raises(ValueError, match="At least two"):
        compare_pipe_diameters(PUMP, SYSTEM, "0.04,0.063")
