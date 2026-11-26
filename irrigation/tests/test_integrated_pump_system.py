import pytest

from irrigation.calculations import analyze_pump_system


def _parameters(**overrides):
    values = {
        "flow_rates_m3_s": [0.0, 0.0005, 0.001],
        "static_elevation_difference_m": 0.0,
        "required_sector_inlet_pressure_bar": 1.0,
        "upstream_pipe_length_m": 10.0,
        "upstream_pipe_diameter_m": 0.05,
        "hazen_williams_c": 150,
        "local_loss_coefficient": 2.0,
    }
    values.update(overrides)
    return values


def test_builds_system_curve_and_finds_pump_operating_point():
    result = analyze_pump_system(
        {
            "manufacturer": "Example",
            "model": "P-1",
            "pump_curve": [(0.0, 40.0), (0.001, 5.0)],
            "efficiency_curve": [(0.0, 40.0), (0.001, 60.0)],
        },
        _parameters(),
        motor_efficiency_percent=80,
    )

    assert len(result["system"]["system_curve"]) == 3
    assert result["pump_analysis"]["operating_point"]["flow_m3_s"] > 0
    assert result["pump_analysis"]["operating_point"]["head_m"] > 0
    assert result["pump_analysis"]["power"]["shaft_power_w"] > 0
    assert result["pump_analysis"]["power"]["electrical_input_power_w"] > 0
    assert result["method"] == "generated_system_curve_then_pump_operating_analysis"


def test_integrated_analysis_requires_efficiency_data_or_input():
    with pytest.raises(ValueError, match="Pump efficiency is required"):
        analyze_pump_system(
            {"pump_curve": [(0.0, 40.0), (0.001, 5.0)]},
            _parameters(),
        )


def test_integrated_analysis_rejects_invalid_system_parameters():
    with pytest.raises(ValueError, match="diameter"):
        analyze_pump_system(
            {
                "pump_curve": [(0.0, 40.0), (0.001, 5.0)],
            },
            _parameters(upstream_pipe_diameter_m=0.0),
            pump_efficiency_percent=50,
        )


def test_integrated_analysis_rejects_non_dictionary_parameters():
    with pytest.raises(ValueError, match="dictionary"):
        analyze_pump_system(
            {"pump_curve": [(0.0, 40.0), (0.001, 5.0)]},
            [("flow_rates_m3_s", [0.0, 0.001])],
            pump_efficiency_percent=50,
        )
