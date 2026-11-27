import math

import pytest

from irrigation.calculations.pump_power import calculate_pump_power


def test_calculates_hydraulic_and_shaft_power():
    result = calculate_pump_power(
        flow_m3_s=0.001,
        head_m=20,
        pump_efficiency_percent=50,
    )

    assert result["hydraulic_power_w"] == pytest.approx(196.133)
    assert result["shaft_power_w"] == pytest.approx(392.266)
    assert result["electrical_input_power_w"] is None
    assert result["motor_efficiency_percent"] is None


def test_calculates_electrical_input_when_motor_efficiency_is_known():
    result = calculate_pump_power(
        flow_m3_s=0.001,
        head_m=20,
        pump_efficiency_percent=50,
        motor_efficiency_percent=80,
    )

    assert result["hydraulic_power_w"] == pytest.approx(196.133)
    assert result["shaft_power_w"] == pytest.approx(392.266)
    assert result["electrical_input_power_w"] == pytest.approx(490.3325)


def test_supports_custom_water_density_and_gravity():
    result = calculate_pump_power(
        0.001, 10, 50,
        water_density_kg_m3=998,
        gravity_m_s2=9.81,
    )
    assert result["hydraulic_power_w"] == pytest.approx(97.9038)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"flow_m3_s": 0, "head_m": 10, "pump_efficiency_percent": 50},
        {"flow_m3_s": -1, "head_m": 10, "pump_efficiency_percent": 50},
        {"flow_m3_s": 0.1, "head_m": 0, "pump_efficiency_percent": 50},
        {"flow_m3_s": 0.1, "head_m": -1, "pump_efficiency_percent": 50},
        {"flow_m3_s": True, "head_m": 10, "pump_efficiency_percent": 50},
        {"flow_m3_s": 0.1, "head_m": False, "pump_efficiency_percent": 50},
        {"flow_m3_s": float("nan"), "head_m": 10, "pump_efficiency_percent": 50},
        {"flow_m3_s": 0.1, "head_m": float("inf"), "pump_efficiency_percent": 50},
        {"flow_m3_s": 10**1000, "head_m": 10, "pump_efficiency_percent": 50},
    ],
)
def test_rejects_invalid_flow_or_head(kwargs):
    with pytest.raises(ValueError):
        calculate_pump_power(**kwargs)


@pytest.mark.parametrize(
    "efficiency",
    [0, -1, 100.1, True, float("nan"), float("inf"), 10**1000],
)
def test_rejects_invalid_pump_efficiency(efficiency):
    with pytest.raises(ValueError):
        calculate_pump_power(0.001, 10, efficiency)


@pytest.mark.parametrize(
    "efficiency",
    [0, -1, 100.1, True, float("nan"), float("inf")],
)
def test_rejects_invalid_motor_efficiency(efficiency):
    with pytest.raises(ValueError):
        calculate_pump_power(0.001, 10, 70, efficiency)


@pytest.mark.parametrize("density", [0, -1, True, float("nan"), float("inf")])
def test_rejects_invalid_water_density(density):
    with pytest.raises(ValueError):
        calculate_pump_power(0.001, 10, 70, water_density_kg_m3=density)


@pytest.mark.parametrize("gravity", [0, -1, True, float("nan"), float("inf")])
def test_rejects_invalid_gravity(gravity):
    with pytest.raises(ValueError):
        calculate_pump_power(0.001, 10, 70, gravity_m_s2=gravity)


def test_rejects_non_finite_calculated_power():
    with pytest.raises(ValueError, match="not finite"):
        calculate_pump_power(
            flow_m3_s=1e308,
            head_m=1e308,
            pump_efficiency_percent=1,
        )


def test_rejects_non_numeric_values():
    with pytest.raises(ValueError):
        calculate_pump_power("0.001", 10, 70)

@pytest.mark.parametrize(
    "kwargs",
    [
        {"water_density_kg_m3": 10**400},
        {"gravity_m_s2": 10**400},
    ],
)
def test_rejects_unrepresentable_integer_physical_constants(kwargs):
    with pytest.raises(ValueError, match="finite number"):
        calculate_pump_power(0.001, 10, 70, **kwargs)


def test_accepts_full_efficiency_boundaries():
    result = calculate_pump_power(
        flow_m3_s=0.001,
        head_m=10,
        pump_efficiency_percent=100,
        motor_efficiency_percent=100,
    )

    assert result["shaft_power_w"] == pytest.approx(
        result["hydraulic_power_w"]
    )
    assert result["electrical_input_power_w"] == pytest.approx(
        result["hydraulic_power_w"]
    )


def test_scales_hydraulic_power_linearly_with_flow():
    low_flow = calculate_pump_power(0.0005, 20, 50)
    high_flow = calculate_pump_power(0.001, 20, 50)

    assert high_flow["hydraulic_power_w"] == pytest.approx(
        2.0 * low_flow["hydraulic_power_w"]
    )


def test_scales_hydraulic_power_linearly_with_head():
    low_head = calculate_pump_power(0.001, 10, 50)
    high_head = calculate_pump_power(0.001, 20, 50)

    assert high_head["hydraulic_power_w"] == pytest.approx(
        2.0 * low_head["hydraulic_power_w"]
    )


def test_preserves_power_relationship_at_low_valid_flow_and_head():
    result = calculate_pump_power(
        flow_m3_s=1e-9,
        head_m=1e-6,
        pump_efficiency_percent=25.0,
        motor_efficiency_percent=50.0,
    )

    assert result["hydraulic_power_w"] > 0.0
    assert result["shaft_power_w"] == pytest.approx(
        result["hydraulic_power_w"] / 0.25
    )
    assert result["electrical_input_power_w"] == pytest.approx(
        result["shaft_power_w"] / 0.5
    )


def test_preserves_power_relationship_for_large_finite_inputs():
    result = calculate_pump_power(
        flow_m3_s=1e100,
        head_m=1e100,
        pump_efficiency_percent=80.0,
        motor_efficiency_percent=90.0,
    )

    assert math.isfinite(result["hydraulic_power_w"])
    assert math.isfinite(result["shaft_power_w"])
    assert math.isfinite(result["electrical_input_power_w"])
    assert result["shaft_power_w"] == pytest.approx(
        result["hydraulic_power_w"] / 0.8
    )
    assert result["electrical_input_power_w"] == pytest.approx(
        result["shaft_power_w"] / 0.9
    )


def test_shaft_power_is_not_less_than_hydraulic_power():
    result = calculate_pump_power(0.001, 15, 65)

    assert result["shaft_power_w"] >= result["hydraulic_power_w"]


def test_electrical_input_is_not_less_than_shaft_power():
    result = calculate_pump_power(
        0.001,
        15,
        pump_efficiency_percent=65,
        motor_efficiency_percent=88,
    )

    assert result["electrical_input_power_w"] >= result["shaft_power_w"]


def test_lower_efficiencies_increase_required_input_power():
    efficient = calculate_pump_power(
        0.001, 15, 80, motor_efficiency_percent=90
    )
    less_efficient = calculate_pump_power(
        0.001, 15, 40, motor_efficiency_percent=70
    )

    assert less_efficient["shaft_power_w"] > efficient["shaft_power_w"]
    assert (
        less_efficient["electrical_input_power_w"]
        > efficient["electrical_input_power_w"]
    )
