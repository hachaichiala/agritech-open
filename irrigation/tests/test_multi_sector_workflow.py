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


def test_daily_schedule_calculates_sequential_runtime_and_capacity():
    from irrigation.calculations import schedule_irrigation_sectors

    design = {
        "sectors": [
            {"name": "trees", "analysis": {"design_duty": {"sector_design_flow_lph": 16.0}}},
            {"name": "vegetables", "analysis": {"design_duty": {"sector_design_flow_lph": 24.0}}},
        ]
    }
    result = schedule_irrigation_sectors(
        sector_design=design,
        daily_water_requirements_l={"trees": 80.0, "vegetables": 120.0},
        available_runtime_hours_per_day=8.0,
    )

    assert result["operation_mode"] == "sequential_daily_irrigation_schedule"
    assert [item["runtime_hours"] for item in result["sectors"]] == pytest.approx([5.0, 5.0])
    assert result["summary"]["total_daily_water_requirement_l"] == pytest.approx(200.0)
    assert result["summary"]["total_runtime_hours"] == pytest.approx(10.0)
    assert result["summary"]["remaining_runtime_hours"] == pytest.approx(-2.0)
    assert result["summary"]["fits_available_runtime"] is False


def test_crop_water_planning_connects_sector_demand_to_daily_runtime():
    from irrigation.calculations import plan_daily_irrigation_from_crops

    design = {
        "sectors": [
            {"name": "trees", "analysis": {"design_duty": {"sector_design_flow_lph": 16.0}}},
            {"name": "vegetables", "analysis": {"design_duty": {"sector_design_flow_lph": 24.0}}},
        ]
    }

    result = plan_daily_irrigation_from_crops(
        sector_design=design,
        crops_by_sector={
            "trees": [{"name": "young_trees", "kc": 0.8, "area_m2": 10.0}],
            "vegetables": [{"name": "vegetables", "kc": 1.2, "area_m2": 10.0}],
        },
        et0_mm_day=5.0,
        application_efficiency_percent=80.0,
        available_runtime_hours_per_day=7.0,
    )

    assert result["daily_irrigation_requirements_l"] == pytest.approx({
        "trees": 50.0,
        "vegetables": 75.0,
    })
    assert [
        item["runtime_hours"] for item in result["schedule"]["sectors"]
    ] == pytest.approx([3.125, 3.125])
    assert result["schedule"]["summary"]["total_runtime_hours"] == pytest.approx(6.25)
    assert result["schedule"]["summary"]["fits_available_runtime"] is True
