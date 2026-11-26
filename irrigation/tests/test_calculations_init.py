
from irrigation.calculations import (
    calculate_total_flow,
    calculate_total_emitters,
    calculate_tree_zone_flow,
    calculate_hazen_williams_head_loss,
    liters_per_hour_to_cubic_meters_per_second,
    cubic_meters_per_second_to_liters_per_hour,
    bar_to_meters_of_water,
    meters_of_water_to_bar,
    calculate_dripline_head_loss,
    EmitterPressureRange,
    is_pressure_in_compensation_range,
    check_dripline_pressure,
    analyze_dripline_pressure,
)


def test_public_imports():
    assert callable(calculate_total_flow)
    assert callable(calculate_total_emitters)
    assert callable(calculate_tree_zone_flow)
    assert callable(calculate_hazen_williams_head_loss)
    assert callable(liters_per_hour_to_cubic_meters_per_second)
    assert callable(cubic_meters_per_second_to_liters_per_hour)
    assert callable(bar_to_meters_of_water)
    assert callable(meters_of_water_to_bar)
    assert callable(calculate_dripline_head_loss)
    assert callable(is_pressure_in_compensation_range)
    assert callable(check_dripline_pressure)
    assert callable(analyze_dripline_pressure)

    assert EmitterPressureRange is not None
