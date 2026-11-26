import pytest

from irrigation.calculations.pipe_economic_comparison import (
    compare_pipe_diameter_economics,
)


PUMP = {
    "manufacturer": "Test",
    "model": "P-1",
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

COSTS = [
    {"diameter_m": 0.04, "cost_tnd_per_m": 4.0},
    {"diameter_m": 0.063, "cost_tnd_per_m": 7.0},
]


def _compare(**overrides):
    arguments = {
        "pump_data": PUMP,
        "system_curve_parameters": SYSTEM,
        "pipe_diameters_m": [0.04, 0.063],
        "pipe_costs_tnd_per_m": COSTS,
        "electricity_cost_tnd_per_kwh": 0.2,
        "operating_hours_per_day": 4,
        "operating_days_per_year": 300,
        "analysis_period_years": 5,
        "motor_efficiency_percent": 90,
    }
    arguments.update(overrides)
    return compare_pipe_diameter_economics(**arguments)


def test_calculates_pipe_purchase_energy_and_total_costs():
    result = _compare()
    for scenario in result["scenarios"]:
        economics = scenario["economics"]
        assert economics["pipe_purchase_cost_tnd"] > 0
        assert economics["energy_kwh_per_day"] > 0
        assert economics["energy_cost_over_period_tnd"] > 0
        assert economics["total_cost_over_period_tnd"] == pytest.approx(
            economics["pipe_purchase_cost_tnd"]
            + economics["energy_cost_over_period_tnd"]
        )


def test_pipe_purchase_cost_uses_unit_price_and_pipe_length():
    result = _compare()
    first = result["scenarios"][0]["economics"]
    assert first["pipe_purchase_cost_tnd"] == pytest.approx(4.0 * 80.0)


def test_returns_lowest_total_cost_recommendation():
    result = _compare()
    calculated = [
        item for item in result["scenarios"]
        if item["economic_status"] == "calculated"
    ]
    cheapest = min(
        calculated,
        key=lambda item: item["economics"]["total_cost_over_period_tnd"],
    )
    assert result["recommendation"]["pipe_diameter_m"] == cheapest["pipe_diameter_m"]


def test_requires_matching_cost_record_for_every_diameter():
    with pytest.raises(ValueError, match="match every requested diameter"):
        _compare(pipe_costs_tnd_per_m=COSTS[:1])


def test_rejects_invalid_operating_hours_and_motor_efficiency():
    with pytest.raises(ValueError, match="cannot exceed 24"):
        _compare(operating_hours_per_day=25)
    with pytest.raises(ValueError, match="Motor efficiency"):
        _compare(motor_efficiency_percent=0)


def test_reports_economic_inputs_and_exclusions():
    result = _compare()
    assert result["economic_inputs"]["analysis_period_years"] == 5.0
    assert len(result["exclusions"]) >= 4


def test_failed_hydraulic_scenarios_are_not_ranked_economically():
    weak_pump = {
        "pump_curve": [(0.0, 1.0), (0.001, 0.5)],
        "efficiency_curve": [(0.0, 50.0), (0.001, 60.0)],
    }
    result = _compare(pump_data=weak_pump)
    assert all(
        item["economic_status"] == "not_calculated"
        for item in result["scenarios"]
    )
    assert result["recommendation"] is None
