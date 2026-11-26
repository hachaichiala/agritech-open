import pytest

from irrigation.calculations.pipe_diameter_payback import analyze_pipe_diameter_payback

def _comparison(scenarios=None, years=5):
    return {
        "economic_inputs": {"analysis_period_years": years},
        "scenarios": scenarios if scenarios is not None else [
            {"pipe_diameter_m": 0.04, "economic_status": "calculated", "economics": {
                "pipe_purchase_cost_tnd": 320, "energy_cost_over_period_tnd": 500}},
            {"pipe_diameter_m": 0.063, "economic_status": "calculated", "economics": {
                "pipe_purchase_cost_tnd": 560, "energy_cost_over_period_tnd": 300}},
        ],
    }

def test_calculates_incremental_cost_annual_savings_and_payback():
    result = analyze_pipe_diameter_payback(_comparison())
    pair = result["comparisons"][0]
    assert pair["extra_pipe_purchase_cost_tnd"] == pytest.approx(240)
    assert pair["annual_electricity_cost_savings_tnd"] == pytest.approx(40)
    assert pair["payback_period_years"] == pytest.approx(6)
    assert pair["status"] == "payback_available"

def test_reports_no_payback_when_larger_pipe_uses_more_energy():
    data = _comparison()
    data["scenarios"][1]["economics"]["energy_cost_over_period_tnd"] = 600
    pair = analyze_pipe_diameter_payback(data)["comparisons"][0]
    assert pair["annual_electricity_cost_savings_tnd"] < 0
    assert pair["payback_period_years"] is None
    assert pair["status"] == "no_payback_from_energy_savings"

def test_zero_savings_has_no_finite_payback():
    data = _comparison()
    data["scenarios"][1]["economics"]["energy_cost_over_period_tnd"] = 500
    pair = analyze_pipe_diameter_payback(data)["comparisons"][0]
    assert pair["payback_period_years"] is None

def test_compares_all_ordered_diameter_pairs():
    data = _comparison()
    data["scenarios"].append({"pipe_diameter_m": 0.075, "economic_status": "calculated",
        "economics": {"pipe_purchase_cost_tnd": 700, "energy_cost_over_period_tnd": 200}})
    result = analyze_pipe_diameter_payback(data)
    assert result["comparison_count"] == 3

def test_ignores_hydraulically_failed_scenarios():
    data = _comparison()
    data["scenarios"].append({"pipe_diameter_m": 0.09, "economic_status": "not_calculated"})
    assert analyze_pipe_diameter_payback(data)["comparison_count"] == 1

def test_rejects_missing_or_invalid_analysis_period():
    with pytest.raises(ValueError, match="Analysis period"):
        analyze_pipe_diameter_payback(_comparison(years=0))

def test_requires_two_successful_scenarios():
    data = _comparison()
    data["scenarios"][1]["economic_status"] = "not_calculated"
    with pytest.raises(ValueError, match="two successfully calculated"):
        analyze_pipe_diameter_payback(data)
