import pytest

from irrigation.calculations.pipe_lifecycle_cost import analyze_pipe_lifecycle_cost


def _comparison():
    return {
        "economic_inputs": {"analysis_period_years": 5},
        "scenarios": [
            {
                "pipe_diameter_m": 0.04,
                "economic_status": "calculated",
                "economics": {
                    "pipe_purchase_cost_tnd": 320,
                    "energy_cost_over_period_tnd": 500,
                    "pipe_length_m": 80,
                },
            },
            {
                "pipe_diameter_m": 0.063,
                "economic_status": "calculated",
                "economics": {
                    "pipe_purchase_cost_tnd": 560,
                    "energy_cost_over_period_tnd": 300,
                    "pipe_length_m": 80,
                },
            },
        ],
    }


def test_calculates_discounted_life_cycle_costs():
    result = analyze_pipe_lifecycle_cost(_comparison(), discount_rate_percent=5)
    first = result["scenarios"][0]["costs"]
    assert first["initial_cost_tnd"] == pytest.approx(320)
    assert first["discounted_energy_cost_tnd"] > 0
    assert first["net_present_life_cycle_cost_tnd"] < (
        first["undiscounted_life_cycle_cost_tnd"]
    )


def test_includes_installation_and_annual_maintenance():
    result = analyze_pipe_lifecycle_cost(
        _comparison(),
        discount_rate_percent=0,
        installation_cost_tnd_per_m=2,
        annual_maintenance_cost_tnd_per_m=0.5,
    )
    first = result["scenarios"][0]["costs"]
    assert first["installation_cost_tnd"] == pytest.approx(160)
    assert first["discounted_maintenance_cost_tnd"] == pytest.approx(200)


def test_applies_electricity_price_escalation():
    result = analyze_pipe_lifecycle_cost(
        _comparison(),
        discount_rate_percent=0,
        electricity_price_escalation_percent=10,
    )
    costs = result["scenarios"][0]["yearly_cash_flows"]
    assert costs[1]["energy_cost_tnd"] == pytest.approx(110)
    assert costs[4]["energy_cost_tnd"] == pytest.approx(500 * 1.1 ** 4 / 5)


def test_includes_replacement_and_residual_value():
    result = analyze_pipe_lifecycle_cost(
        _comparison(),
        discount_rate_percent=0,
        replacement_interval_years=2,
        replacement_cost_fraction=0.5,
        residual_value_fraction=0.2,
    )
    first = result["scenarios"][0]["costs"]
    assert first["discounted_replacement_cost_tnd"] == pytest.approx(320)
    assert first["residual_value_tnd"] == pytest.approx(64)


def test_recommends_lowest_net_present_life_cycle_cost():
    result = analyze_pipe_lifecycle_cost(_comparison(), discount_rate_percent=5)
    best = min(
        result["scenarios"],
        key=lambda item: item["costs"]["net_present_life_cycle_cost_tnd"],
    )
    assert result["recommendation"]["pipe_diameter_m"] == best["pipe_diameter_m"]


def test_skips_failed_hydraulic_scenarios():
    data = _comparison()
    data["scenarios"][1]["economic_status"] = "not_calculated"
    result = analyze_pipe_lifecycle_cost(data, discount_rate_percent=5)
    assert result["scenarios"][1]["status"] == "not_calculated"
    assert result["recommendation"]["pipe_diameter_m"] == 0.04


def test_rejects_invalid_lifecycle_inputs():
    with pytest.raises(ValueError, match="Discount rate"):
        analyze_pipe_lifecycle_cost(_comparison(), discount_rate_percent=-1)
    with pytest.raises(ValueError, match="whole number"):
        data = _comparison()
        data["economic_inputs"]["analysis_period_years"] = 2.5
        analyze_pipe_lifecycle_cost(data, discount_rate_percent=5)
    with pytest.raises(ValueError, match="Replacement interval"):
        analyze_pipe_lifecycle_cost(
            _comparison(), discount_rate_percent=5, replacement_interval_years=5
        )
