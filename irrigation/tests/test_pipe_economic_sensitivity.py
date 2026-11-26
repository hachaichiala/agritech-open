import pytest

from irrigation.calculations.pipe_economic_sensitivity import (
    analyze_pipe_economic_sensitivity,
)

PUMP = {
    "manufacturer": "Test", "model": "P-1",
    "pump_curve": [(0.0, 40.0), (0.001, 20.0)],
    "efficiency_curve": [(0.0, 50.0), (0.001, 60.0)],
}
SYSTEM = {
    "flow_rates_m3_s": [0.0, 0.0005, 0.001],
    "static_elevation_difference_m": 2.0,
    "required_sector_inlet_pressure_bar": 2.0,
    "upstream_pipe_length_m": 80.0,
    "upstream_pipe_diameter_m": 0.05,
    "hazen_williams_c": 150, "local_loss_coefficient": 2.0,
}
COSTS = [
    {"diameter_m": 0.04, "cost_tnd_per_m": 4.0},
    {"diameter_m": 0.063, "cost_tnd_per_m": 7.0},
]

def _analyze(cases=None):
    return analyze_pipe_economic_sensitivity(
        pump_data=PUMP, system_curve_parameters=SYSTEM,
        pipe_diameters_m=[0.04, 0.063], pipe_costs_tnd_per_m=COSTS,
        electricity_cost_tnd_per_kwh=0.2, operating_hours_per_day=4,
        operating_days_per_year=300, analysis_period_years=5,
        motor_efficiency_percent=90,
        sensitivity_cases=cases if cases is not None else [
            {"name": "baseline", "overrides": {}},
            {"name": "higher tariff", "overrides": {"electricity_cost_tnd_per_kwh": 0.3}},
        ],
    )

def test_evaluates_each_named_scenario_and_reports_winners():
    result = _analyze()
    assert result["case_count"] == 2
    assert result["successful_case_count"] == 2
    assert all(case["recommended_diameter_m"] in [0.04, 0.063] for case in result["cases"])

def test_identical_cases_report_stable_recommendation():
    result = _analyze([{"name": "a", "overrides": {}}, {"name": "b", "overrides": {}}])
    assert result["recommendation_is_stable"] is True
    assert result["stable_recommended_diameter_m"] == result["cases"][0]["recommended_diameter_m"]

def test_changes_pipe_prices_for_selected_case():
    changed = [
        {"diameter_m": 0.04, "cost_tnd_per_m": 20.0},
        {"diameter_m": 0.063, "cost_tnd_per_m": 1.0},
    ]
    result = _analyze([{"name": "price change", "overrides": {"pipe_costs_tnd_per_m": changed}}])
    assert result["cases"][0]["comparison"]["economic_inputs"]["electricity_cost_tnd_per_kwh"] == 0.2

def test_rejects_unknown_override():
    with pytest.raises(ValueError, match="Unsupported sensitivity override"):
        _analyze([{"name": "bad", "overrides": {"upstream_pipe_length_m": 100}}])

def test_rejects_duplicate_case_names():
    with pytest.raises(ValueError, match="unique"):
        _analyze([{"name": "same", "overrides": {}}, {"name": "same", "overrides": {}}])

def test_rejects_empty_cases():
    with pytest.raises(ValueError, match="At least one"):
        _analyze([])

def test_reports_no_stable_winner_when_case_has_no_hydraulic_solution():
    weak = {"pump_curve": [(0.0, 1.0), (0.001, 0.5)], "efficiency_curve": [(0.0, 50.0), (0.001, 60.0)]}
    result = analyze_pipe_economic_sensitivity(
        pump_data=weak, system_curve_parameters=SYSTEM, pipe_diameters_m=[0.04, 0.063],
        pipe_costs_tnd_per_m=COSTS, electricity_cost_tnd_per_kwh=0.2,
        operating_hours_per_day=4, operating_days_per_year=300,
        analysis_period_years=5, motor_efficiency_percent=90,
        sensitivity_cases=[{"name": "weak pump", "overrides": {}}],
    )
    assert result["successful_case_count"] == 0
    assert result["recommendation_is_stable"] is False
