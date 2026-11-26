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
        "minimum_velocity_m_s": 0.1,
        "maximum_velocity_m_s": 1.5,
        "allow_unverified_pipe_specifications": True,
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


def _pipe_specs(first_design=5, second_design=5):
    return [
        {
            "pipe_diameter_m": 0.04,
            "outside_diameter_m": 0.05,
            "wall_thickness_m": 0.005,
            "design_pressure_bar": first_design,
            "rated_pressure_bar": 6,
            "material": "PE",
        },
        {
            "pipe_diameter_m": 0.063,
            "outside_diameter_m": 0.07,
            "wall_thickness_m": 0.0035,
            "design_pressure_bar": second_design,
            "rated_pressure_bar": 6,
            "material": "PVC",
        },
    ]


def test_pressure_compliant_pipes_remain_eligible_for_recommendation():
    result = _analyze(pipe_specifications=_pipe_specs())
    assert result["pipe_specifications_verified"] is True
    assert all(item["within_rating"] for item in result["pressure_assessments"])
    assert result["recommendation"]["status"] == "recommended"


def test_pipe_exceeding_pressure_rating_is_excluded_from_recommendation():
    result = _analyze(pipe_specifications=_pipe_specs(second_design=8))
    failed = next(
        item for item in result["pressure_assessments"]
        if item["pipe_diameter_m"] == 0.063
    )
    assert failed["status"] == "exceeds_rating"
    assert result["recommendation"]["pipe_diameter_m"] != 0.063


def test_no_pressure_compliant_pipe_produces_no_recommendation():
    result = _analyze(
        pipe_specifications=_pipe_specs(first_design=8, second_design=9)
    )
    assert result["recommendation"]["status"] == "no_pressure_compliant_diameter"
    assert result["recommendation"]["pipe_diameter_m"] is None


def test_velocity_uses_manufacturer_calculated_internal_diameter():
    result = _analyze(pipe_specifications=_pipe_specs())
    for item in result["velocity_assessments"]:
        specification = next(
            spec for spec in _pipe_specs()
            if spec["pipe_diameter_m"] == item["pipe_diameter_m"]
        )
        expected = specification["outside_diameter_m"] - 2 * specification["wall_thickness_m"]
        assert item["internal_diameter_m"] == pytest.approx(expected)


def test_missing_manufacturer_specifications_are_reported_as_unverified():
    result = _analyze(allow_unverified_pipe_specifications=False)
    assert result["pipe_specifications_verified"] is False
    assert result["recommendation"]["status"] == "unverified_pipe_specifications"
    assert result["recommendation"]["pipe_diameter_m"] is None
    assert all(
        item["status"] == "not_provided"
        for item in result["pressure_assessments"]
    )
    assert any(
        "pressure suitability is unverified" in item
        for item in result["missing_or_unverified_inputs"]
    )


def test_specification_diameter_must_match_calculated_internal_diameter():
    specs = _pipe_specs()
    specs[0]["pipe_diameter_m"] = 0.041
    with pytest.raises(ValueError, match="calculated manufacturer internal diameter"):
        _analyze(pipe_specifications=specs)
