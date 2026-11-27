import pytest

from irrigation.calculations import calculate_fao56_et0


def test_fao56_daily_et0_matches_published_climate_example():
    result = calculate_fao56_et0(
        tmin_c=25.6,
        tmax_c=34.8,
        wind_speed_2m_m_s=2.0,
        solar_radiation_mj_m2_day=22.65,
        elevation_m=2.0,
        latitude_degrees=13.73,
        day_of_year=105,
        actual_vapour_pressure_kpa=2.85,
    )

    assert result["method"] == "FAO56_Penman_Monteith_daily"
    assert result["et0_mm_day"] == pytest.approx(5.76, abs=0.03)
    assert result["intermediate_values"]["net_radiation_mj_m2_day"] == pytest.approx(14.33, abs=0.03)
