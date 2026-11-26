import pytest

from irrigation.calculations.system_curve import build_system_curve


BASE = {
    "flow_rates_m3_s": [0.0002, 0.0005, 0.001],
    "static_elevation_difference_m": 1.5,
    "required_sector_inlet_pressure_bar": 2.0,
    "upstream_pipe_length_m": 80.0,
    "upstream_pipe_diameter_m": 0.05,
    "hazen_williams_c": 150,
    "local_loss_coefficient": 2.5,
}


def _build(**overrides):
    parameters = {**BASE, **overrides}
    return build_system_curve(**parameters)


def test_static_elevation_change_shifts_entire_curve_equally():
    base = _build()["system_curve"]
    raised = _build(static_elevation_difference_m=2.5)["system_curve"]

    for (_, base_head), (_, raised_head) in zip(base, raised):
        assert raised_head - base_head == pytest.approx(1.0)


def test_sector_pressure_change_shifts_curve_by_pressure_head():
    base = _build()["system_curve"]
    higher_pressure = _build(
        required_sector_inlet_pressure_bar=2.1
    )["system_curve"]

    expected_shift_m = 0.1 * 10.197162129779
    for (_, base_head), (_, higher_head) in zip(base, higher_pressure):
        assert higher_head - base_head == pytest.approx(expected_shift_m)


def test_doubling_pipe_length_doubles_friction_loss():
    base = _build()
    longer = _build(upstream_pipe_length_m=160.0)

    for base_detail, longer_detail in zip(
        base["flow_details"], longer["flow_details"]
    ):
        assert longer_detail["friction_loss_m"] == pytest.approx(
            2.0 * base_detail["friction_loss_m"]
        )


def test_larger_pipe_diameter_reduces_both_loss_components():
    base = _build()
    larger = _build(upstream_pipe_diameter_m=0.063)

    for base_detail, larger_detail in zip(
        base["flow_details"], larger["flow_details"]
    ):
        assert larger_detail["friction_loss_m"] < base_detail["friction_loss_m"]
        assert larger_detail["local_loss_m"] < base_detail["local_loss_m"]


def test_zero_length_pipe_has_no_friction_but_keeps_local_losses():
    result = _build(upstream_pipe_length_m=0.0)

    for detail in result["flow_details"]:
        assert detail["friction_loss_m"] == 0.0
        assert detail["local_loss_m"] > 0.0
