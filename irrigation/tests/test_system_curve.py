import math
import pytest

from irrigation.calculations.system_curve import build_system_curve


def _build(**overrides):
    values = {
        "flow_rates_m3_s": [0.0, 0.0005, 0.001],
        "static_elevation_difference_m": 2.0,
        "required_sector_inlet_pressure_bar": 2.0,
        "upstream_pipe_length_m": 100.0,
        "upstream_pipe_diameter_m": 0.05,
        "hazen_williams_c": 150,
        "local_loss_coefficient": 3.0,
    }
    values.update(overrides)
    return build_system_curve(**values)


def test_builds_curve_with_friction_and_local_losses():
    result = _build()
    curve = result["system_curve"]
    details = result["flow_details"]

    assert len(curve) == 3
    assert curve[0][0] == 0.0
    assert curve[0][1] == pytest.approx(2.0 + 2.0 * 10.197162129779)
    assert curve[1][1] > curve[0][1]
    assert curve[2][1] > curve[1][1]
    assert details[0]["friction_loss_m"] == 0.0
    assert details[0]["local_loss_m"] == 0.0
    assert details[2]["velocity_m_s"] > details[1]["velocity_m_s"]


def test_builds_curve_without_local_losses():
    result = _build(local_loss_coefficient=0.0)
    assert result["flow_details"][1]["local_loss_m"] == 0.0
    assert result["flow_details"][1]["friction_loss_m"] > 0.0


def test_curve_head_increases_with_flow():
    result = _build(flow_rates_m3_s=[0.0001, 0.0003, 0.0008])
    heads = [head for _, head in result["system_curve"]]
    assert heads[0] < heads[1] < heads[2]


@pytest.mark.parametrize("flows", [
    [], [0.0], [0.0, 0.0], [0.001, 0.0005],
    [-0.001, 0.001], [0.0, float("nan")],
    [0.0, float("inf")], [0.0, True],
])
def test_rejects_invalid_flow_points(flows):
    with pytest.raises(ValueError):
        _build(flow_rates_m3_s=flows)


@pytest.mark.parametrize("overrides", [
    {"upstream_pipe_length_m": -1.0},
    {"upstream_pipe_diameter_m": 0.0},
    {"hazen_williams_c": 0.0},
    {"local_loss_coefficient": -1.0},
    {"local_loss_coefficient": float("nan")},
    {"static_elevation_difference_m": float("inf")},
    {"required_sector_inlet_pressure_bar": 0.0},
])
def test_rejects_invalid_system_parameters(overrides):
    with pytest.raises(ValueError):
        _build(**overrides)


def test_all_returned_hydraulic_details_are_finite():
    result = _build()
    for item in result["flow_details"]:
        assert all(math.isfinite(value) for value in item.values())


def test_returns_model_assumptions():
    result = _build()
    assert result["method"] == "hazen_williams_friction_plus_k_factor_local_losses"
    assert len(result["assumptions"]) == 4


@pytest.mark.parametrize("diameter", [1e-200, 1e200])
def test_rejects_unrepresentable_pipe_cross_section_area(diameter):
    with pytest.raises(ValueError, match="cross-sectional area"):
        _build(upstream_pipe_diameter_m=diameter)
