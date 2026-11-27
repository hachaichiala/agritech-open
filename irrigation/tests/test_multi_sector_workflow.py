import pytest

from irrigation.calculations import (
    EmitterPressureRange,
    design_irrigation_sectors,
)


def test_multiple_sectors_receive_independent_sequential_pump_analysis():
    base_sector = {
        "number_of_laterals": 2,
        "emitters_per_lateral": 2,
        "emitter_flow_lph": 4.0,
        "lateral_length_m": 10.0,
        "lateral_diameter_m": 0.016,
        "manifold_length_m": 5.0,
        "manifold_diameter_m": 0.032,
        "inlet_pressure_bar": 1.0,
        "hazen_williams_c": 150,
    }
    larger_sector = {**base_sector, "number_of_laterals": 3}

    result = design_irrigation_sectors(
        sectors=[
            {"name": "trees", "sector_parameters": base_sector},
            {"name": "vegetables", "sector_parameters": larger_sector},
        ],
        upstream_system_parameters={
            "flow_rates_m3_s": [0.0, 0.0001],
            "static_elevation_difference_m": 0.0,
            "upstream_pipe_length_m": 5.0,
            "upstream_pipe_diameter_m": 0.04,
            "hazen_williams_c": 150,
            "local_loss_coefficient": 1.0,
        },
        pump_data={
            "manufacturer": "Example",
            "model": "P-1",
            "pump_curve": [(0.0, 30.0), (0.0001, 5.0)],
            "efficiency_curve": [(0.0, 50.0), (0.0001, 60.0)],
        },
        pressure_range=EmitterPressureRange(0.5, 3.0),
        motor_efficiency_percent=80.0,
    )

    assert result["operation_mode"] == "sequential_independent_sector_analysis"
    assert result["sector_count"] == 2
    assert [item["name"] for item in result["sectors"]] == [
        "trees",
        "vegetables",
    ]
    flows = [
        item["analysis"]["design_duty"]["sector_design_flow_lph"]
        for item in result["sectors"]
    ]
    assert flows == pytest.approx([16.0, 24.0])
    assert result["summary"]["maximum_sector_design_flow_lph"] == pytest.approx(24.0)
    assert all(
        item["analysis"]["pump_system_analysis"]["pump_analysis"]["operating_point"]
        for item in result["sectors"]
    )
