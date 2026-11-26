import pytest

from irrigation.calculations.pipe_diameter_decision import (
    analyze_pipe_diameter_decision,
)


PUMP = {
    "manufacturer": "Test",
    "model": "P-1",
    "rated_motor_power_kw": 1.1,
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
DIAMETERS = [0.04, 0.063]
COSTS = [
    {"diameter_m": 0.04, "cost_tnd_per_m": 4.0},
    {"diameter_m": 0.063, "cost_tnd_per_m": 7.0},
]


def _analyze(**overrides):
    args = {
        "pump_data": PUMP,
        "system_curve_parameters": SYSTEM,
        "pipe_diameters_m": DIAMETERS,
        "pipe_costs_tnd_per_m": COSTS,
        "electricity_cost_tnd_per_kwh": 0.2,
        "operating_hours_per_day": 4,
        "operating_days_per_year": 300,
        "analysis_period_years": 5,
        "motor_efficiency_percent": 90,
        "discount_rate_percent": 5,
    }
    args.update(overrides)
    return analyze_pipe_diameter_decision(**args)


def test_integrates_hydraulic_economic_payback_and_lifecycle_results():
    result = _analyze()
    assert len(result["hydraulic_and_economic_comparison"]["scenarios"]) == 2
    assert result["payback_analysis"]["comparison_count"] == 1
    assert len(result["life_cycle_analysis"]["scenarios"]) == 2
    assert result["recommendation"]["status"] == "recommended"


def test_recommendation_matches_lowest_lifecycle_cost():
    result = _analyze()
    lowest = min(
        (
            item for item in result["life_cycle_analysis"]["scenarios"]
            if item["status"] == "calculated"
        ),
        key=lambda item: item["costs"]["net_present_life_cycle_cost_tnd"],
    )
    assert result["recommendation"]["pipe_diameter_m"] == lowest["pipe_diameter_m"]


def test_runs_optional_sensitivity_cases():
    cases = [
        {"name": "base", "overrides": {}},
        {"name": "higher tariff", "overrides": {"electricity_cost_tnd_per_kwh": 0.3}},
    ]
    result = _analyze(sensitivity_cases=cases)
    assert result["sensitivity_analysis"]["case_count"] == 2


def test_sensitivity_is_none_when_no_cases_are_supplied():
    assert _analyze()["sensitivity_analysis"] is None


def test_reports_insufficient_hydraulic_scenarios_for_payback():
    weak = {
        "pump_curve": [(0.0, 1.0), (0.001, 0.5)],
        "efficiency_curve": [(0.0, 50.0), (0.001, 60.0)],
    }
    result = _analyze(pump_data=weak)
    assert result["recommendation"]["status"] == "no_feasible_diameter"
    assert result["payback_analysis"]["status"] == "insufficient_successful_hydraulic_scenarios"


def test_reports_unverified_inputs():
    result = _analyze(
        installation_cost_tnd_per_m=0,
        annual_maintenance_cost_tnd_per_m=0,
    )
    assert "Actual pipe installation and excavation cost." in result["missing_or_unverified_inputs"]
    assert "Expected annual pipe maintenance cost." in result["missing_or_unverified_inputs"]


def test_invalid_lifecycle_input_is_rejected():
    with pytest.raises(ValueError, match="Discount rate"):
        _analyze(discount_rate_percent=-1)



def test_recommendation_excludes_diameters_outside_velocity_range():
    result = _analyze(minimum_velocity_m_s=0.7, maximum_velocity_m_s=1.0)
    assessments = result["velocity_assessments"]
    assert len(assessments) == 2
    assert all(item["status"] in {"below_minimum", "within_range", "above_maximum"} for item in assessments)
    acceptable = {
        item["pipe_diameter_m"]
        for item in assessments
        if item["status"] == "within_range"
    }
    if acceptable:
        assert result["recommendation"]["pipe_diameter_m"] in acceptable
    else:
        assert result["recommendation"]["status"] == "no_velocity_acceptable_diameter"


def test_returns_no_recommendation_when_all_velocities_are_too_low():
    result = _analyze(minimum_velocity_m_s=100.0, maximum_velocity_m_s=200.0)
    assert result["recommendation"]["status"] == "no_velocity_acceptable_diameter"
    assert result["recommendation"]["pipe_diameter_m"] is None


def test_rejects_invalid_velocity_range():
    with pytest.raises(ValueError, match="lower than"):
        _analyze(minimum_velocity_m_s=1.5, maximum_velocity_m_s=0.6)
