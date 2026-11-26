import pytest

from irrigation.calculations.operating_analysis import analyze_pump_operation


PUMP_CURVE = [(0.0, 40.0), (0.001, 20.0)]
SYSTEM_CURVE = [(0.0, 10.0), (0.001, 30.0)]


def test_integrates_operating_point_and_efficiency_curve():
    result = analyze_pump_operation(
        {
            "manufacturer": "Example",
            "model": "P-1",
            "pump_curve": PUMP_CURVE,
            "efficiency_curve": [(0.0, 40.0), (0.001, 60.0)],
        },
        SYSTEM_CURVE,
        motor_efficiency_percent=80,
    )

    assert result["operating_point"]["flow_m3_s"] == pytest.approx(0.00075)
    assert result["operating_point"]["head_m"] == pytest.approx(25.0)
    assert result["power"]["pump_efficiency_percent"] == pytest.approx(55.0)
    assert result["power"]["motor_efficiency_percent"] == 80
    assert result["power"]["electrical_input_power_w"] is not None
    assert result["pump_efficiency_source"] == "interpolated_efficiency_curve"


def test_requires_explicit_efficiency_when_no_efficiency_curve():
    with pytest.raises(ValueError, match="Pump efficiency is required"):
        analyze_pump_operation(
            {"pump_curve": PUMP_CURVE},
            SYSTEM_CURVE,
        )


def test_uses_explicit_pump_efficiency_without_efficiency_curve():
    result = analyze_pump_operation(
        {"pump_curve": PUMP_CURVE},
        SYSTEM_CURVE,
        pump_efficiency_percent=50,
    )
    assert result["power"]["pump_efficiency_percent"] == 50
    assert result["pump_efficiency_source"] == "explicit_input"


def test_rejects_efficiency_outside_efficiency_curve_range():
    with pytest.raises(ValueError, match="outside"):
        analyze_pump_operation(
            {
                "pump_curve": PUMP_CURVE,
                "efficiency_curve": [(0.0008, 50), (0.001, 60)],
            },
            SYSTEM_CURVE,
        )


def test_compares_shaft_power_with_rated_motor_output_power():
    result = analyze_pump_operation(
        {
            "rated_motor_power_kw": 0.5,
            "pump_curve": PUMP_CURVE,
        },
        SYSTEM_CURVE,
        pump_efficiency_percent=50,
    )
    check = result["motor_power_check"]
    assert check["required_shaft_power_kw"] == pytest.approx(0.367749375)
    assert check["available_margin_kw"] == pytest.approx(0.132250625)
    assert check["within_rated_power"] is True
    assert check["rating_interpretation"] == "mechanical_shaft_output"


def test_reports_insufficient_rated_motor_output_power():
    result = analyze_pump_operation(
        {
            "rated_motor_power_kw": 0.4,
            "pump_curve": PUMP_CURVE,
        },
        SYSTEM_CURVE,
        pump_efficiency_percent=50,
    )
    assert result["motor_power_check"]["within_rated_power"] is False


def test_does_not_compare_rated_power_with_electrical_input():
    result = analyze_pump_operation(
        {
            "rated_motor_power_kw": 0.5,
            "pump_curve": PUMP_CURVE,
        },
        SYSTEM_CURVE,
        pump_efficiency_percent=50,
        motor_efficiency_percent=80,
    )
    check = result["motor_power_check"]
    assert check["required_shaft_power_kw"] == pytest.approx(0.4903325)
    assert result["power"]["electrical_input_power_w"] > check["required_shaft_power_kw"] * 1000


def test_rejects_conflicting_explicit_efficiency_and_curve():
    with pytest.raises(ValueError, match="Do not supply"):
        analyze_pump_operation(
            {
                "pump_curve": PUMP_CURVE,
                "efficiency_curve": [(0.0, 50), (0.001, 60)],
            },
            SYSTEM_CURVE,
            pump_efficiency_percent=55,
        )


def test_rejects_zero_efficiency_at_operating_point():
    with pytest.raises(ValueError, match="Pump efficiency"):
        analyze_pump_operation(
            {
                "pump_curve": PUMP_CURVE,
                "efficiency_curve": [(0.0, 0), (0.001, 0)],
            },
            SYSTEM_CURVE,
        )
