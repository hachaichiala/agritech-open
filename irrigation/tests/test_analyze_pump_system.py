import pytest

from irrigation.calculations.operating_analysis import analyze_pump_system


PUMP_DATA = {
    "manufacturer": "Test",
    "model": "P-1",
    "pump_curve": [(0.0, 40.0), (0.001, 20.0)],
    "efficiency_curve": [(0.0, 50.0), (0.001, 60.0)],
}

SYSTEM_PARAMETERS = {
    "flow_rates_m3_s": [0.0, 0.0005, 0.001],
    "static_elevation_difference_m": 2.0,
    "required_sector_inlet_pressure_bar": 2.0,
    "upstream_pipe_length_m": 10.0,
    "upstream_pipe_diameter_m": 0.05,
    "hazen_williams_c": 150,
    "local_loss_coefficient": 2.0,
}


def test_builds_system_curve_and_finds_operating_point():
    result = analyze_pump_system(PUMP_DATA, SYSTEM_PARAMETERS)

    curve = result["system"]["system_curve"]
    point = result["pump_analysis"]["operating_point"]

    assert len(curve) == 3
    assert 0.0 < point["flow_m3_s"] < 0.001
    assert point["pump_head_m"] == pytest.approx(point["system_head_m"])
    assert point["head_m"] == pytest.approx(point["system_head_m"])
    assert result["method"] == (
        "generated_system_curve_then_pump_operating_analysis"
    )


def test_uses_efficiency_curve_at_generated_operating_flow():
    result = analyze_pump_system(PUMP_DATA, SYSTEM_PARAMETERS)

    efficiency = result["pump_analysis"]["power"]["pump_efficiency_percent"]
    assert 50.0 < efficiency < 60.0
    assert result["pump_analysis"]["pump_efficiency_source"] == (
        "interpolated_efficiency_curve"
    )


def test_returns_system_curve_details_and_assumptions():
    result = analyze_pump_system(PUMP_DATA, SYSTEM_PARAMETERS)

    assert len(result["system"]["flow_details"]) == 3
    assert len(result["system"]["assumptions"]) == 4
    assert result["system"]["flow_details"][-1]["friction_loss_m"] > 0.0


def test_rejects_non_dictionary_system_parameters():
    with pytest.raises(ValueError, match="dictionary"):
        analyze_pump_system(PUMP_DATA, [(0.0, 1.0), (0.001, 2.0)])


def test_rejects_operating_flow_outside_pump_efficiency_curve():
    pump = {
        "pump_curve": [(0.0, 40.0), (0.001, 20.0)],
        "efficiency_curve": [(0.0009, 50.0), (0.001, 60.0)],
    }
    with pytest.raises(ValueError, match="outside"):
        analyze_pump_system(pump, SYSTEM_PARAMETERS)


def test_requires_explicit_efficiency_without_efficiency_curve():
    pump = {
        "pump_curve": [(0.0, 40.0), (0.001, 20.0)],
    }
    with pytest.raises(ValueError, match="Pump efficiency is required"):
        analyze_pump_system(pump, SYSTEM_PARAMETERS)



def test_integrated_analysis_checks_rated_motor_shaft_power():
    pump = {
        **PUMP_DATA,
        "rated_motor_power_kw": 1.0,
    }
    result = analyze_pump_system(
        pump,
        SYSTEM_PARAMETERS,
        motor_efficiency_percent=80.0,
    )

    analysis = result["pump_analysis"]
    check = analysis["motor_power_check"]

    assert check["rated_motor_power_kw"] == pytest.approx(1.0)
    assert check["required_shaft_power_kw"] == pytest.approx(
        analysis["power"]["shaft_power_w"] / 1000.0
    )
    assert check["available_margin_kw"] == pytest.approx(
        1.0 - check["required_shaft_power_kw"]
    )
    assert check["within_rated_power"] is True
    assert check["rating_interpretation"] == "mechanical_shaft_output"


def test_integrated_analysis_applies_motor_efficiency_to_electrical_input():
    result = analyze_pump_system(
        PUMP_DATA,
        SYSTEM_PARAMETERS,
        motor_efficiency_percent=80.0,
    )

    power = result["pump_analysis"]["power"]

    assert power["electrical_input_power_w"] == pytest.approx(
        power["shaft_power_w"] / 0.8
    )
    assert power["electrical_input_power_w"] > power["shaft_power_w"]


def test_integrated_analysis_accepts_explicit_pump_efficiency_without_curve():
    pump = {
        "manufacturer": "Test",
        "model": "P-1",
        "pump_curve": PUMP_DATA["pump_curve"],
    }
    result = analyze_pump_system(
        pump,
        SYSTEM_PARAMETERS,
        pump_efficiency_percent=55.0,
    )

    analysis = result["pump_analysis"]

    assert analysis["power"]["pump_efficiency_percent"] == pytest.approx(55.0)
    assert analysis["pump_efficiency_source"] == "explicit_input"


def test_integrated_analysis_flags_insufficient_rated_motor_power():
    pump = {
        **PUMP_DATA,
        "rated_motor_power_kw": 0.01,
    }
    result = analyze_pump_system(
        pump,
        SYSTEM_PARAMETERS,
        motor_efficiency_percent=80.0,
    )

    check = result["pump_analysis"]["motor_power_check"]

    assert check["within_rated_power"] is False
    assert check["available_margin_kw"] < 0.0
    assert check["required_shaft_power_kw"] > check["rated_motor_power_kw"]


def test_integrated_analysis_accepts_exact_rated_motor_power_boundary():
    baseline = analyze_pump_system(
        PUMP_DATA,
        SYSTEM_PARAMETERS,
        motor_efficiency_percent=80.0,
    )
    required_shaft_power_kw = (
        baseline["pump_analysis"]["power"]["shaft_power_w"] / 1000.0
    )
    pump = {
        **PUMP_DATA,
        "rated_motor_power_kw": required_shaft_power_kw,
    }

    result = analyze_pump_system(
        pump,
        SYSTEM_PARAMETERS,
        motor_efficiency_percent=80.0,
    )

    check = result["pump_analysis"]["motor_power_check"]

    assert check["available_margin_kw"] == pytest.approx(0.0)
    assert check["within_rated_power"] is True


def test_integrated_analysis_omits_electrical_input_without_motor_efficiency():
    result = analyze_pump_system(PUMP_DATA, SYSTEM_PARAMETERS)

    power = result["pump_analysis"]["power"]

    assert power["shaft_power_w"] > 0.0
    assert power["motor_efficiency_percent"] is None
    assert power["electrical_input_power_w"] is None

