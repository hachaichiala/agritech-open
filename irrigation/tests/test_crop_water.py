import pytest

from irrigation.calculations import calculate_crop_water_requirements


def test_crop_water_requirements_calculate_net_and_gross_daily_volumes():
    result = calculate_crop_water_requirements(
        crops=[
            {"name": "young_trees", "kc": 0.8, "area_m2": 100.0},
            {"name": "vegetables", "kc": 1.2, "area_m2": 50.0},
        ],
        et0_mm_day=5.0,
        application_efficiency_percent=80.0,
    )

    assert result["summary"]["total_area_m2"] == pytest.approx(150.0)
    assert result["summary"]["net_crop_water_requirement_l_day"] == pytest.approx(700.0)
    assert result["summary"]["gross_irrigation_requirement_l_day"] == pytest.approx(875.0)
    assert result["summary"]["gross_irrigation_requirement_m3_day"] == pytest.approx(0.875)
    assert result["crops"][0]["gross_irrigation_l_day"] == pytest.approx(500.0)
    assert result["crops"][1]["gross_irrigation_l_day"] == pytest.approx(375.0)
