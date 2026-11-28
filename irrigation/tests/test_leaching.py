import pytest

from irrigation.calculations import calculate_drip_leaching_requirement


def test_fao_high_frequency_drip_leaching_requirement_and_runtime():
    result = calculate_drip_leaching_requirement(
        irrigation_water_ec_ds_m=1.2,
        crop_max_soil_ec_ds_m=3.0,
        net_irrigation_depth_mm=5.0,
        irrigated_area_m2=100.0,
        application_efficiency_percent=90.0,
        sector_flow_lph=1000.0,
    )

    assert result["leaching"]["required_leaching_fraction"] == pytest.approx(0.2)
    assert result["leaching"]["net_depth_including_leaching_mm"] == pytest.approx(6.25)
    assert result["leaching"]["additional_net_leaching_depth_mm"] == pytest.approx(1.25)
    assert result["application"]["gross_application_depth_mm"] == pytest.approx(6.25 / 0.9)
    assert result["application"]["gross_application_volume_l"] == pytest.approx(694.4444444444)
    assert result["application"]["estimated_runtime_hours"] == pytest.approx(0.6944444444)
