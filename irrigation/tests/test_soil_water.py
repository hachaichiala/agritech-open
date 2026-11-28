import pytest

from irrigation.calculations import calculate_irrigation_trigger


def test_fao56_irrigation_trigger_calculates_interval_refill_and_runtime():
    result = calculate_irrigation_trigger(
        field_capacity_vwc=0.30,
        wilting_point_vwc=0.15,
        root_depth_m=0.60,
        depletion_fraction=0.50,
        crop_et_mm_day=5.0,
        irrigated_area_m2=100.0,
        application_efficiency_percent=90.0,
        sector_flow_lph=1000.0,
    )

    assert result["soil_water"]["total_available_water_mm"] == pytest.approx(90.0)
    assert result["soil_water"]["readily_available_water_mm"] == pytest.approx(45.0)
    assert result["irrigation"]["estimated_interval_days"] == pytest.approx(9.0)
    assert result["irrigation"]["gross_application_depth_mm"] == pytest.approx(50.0)
    assert result["irrigation"]["gross_application_volume_l"] == pytest.approx(5000.0)
    assert result["irrigation"]["estimated_runtime_hours"] == pytest.approx(5.0)
