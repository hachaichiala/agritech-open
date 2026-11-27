import pytest

from irrigation.calculations.dripline import calculate_dripline_head_loss
from irrigation.calculations.emitters import calculate_tree_zone_flow
from irrigation.calculations.pump_head import calculate_sector_pump_requirement
from irrigation.calculations.units import liters_per_hour_to_cubic_meters_per_second


@pytest.mark.parametrize(
    "number_of_trees, lateral_length_m, lateral_diameter_m",
    [
        (12, 60.0, 0.016),
        (20, 100.0, 0.020),
    ],
)
def test_tree_zone_to_lateral_and_pump_requirement(
    number_of_trees,
    lateral_length_m,
    lateral_diameter_m,
):
    emitters_per_tree = 2
    emitter_flow_lph = 8.0
    target_emitter_pressure_bar = 1.5
    static_elevation_difference_m = 3.2
    upstream_friction_losses_m = 0.75
    upstream_local_losses_m = 0.20

    total_flow_lph = calculate_tree_zone_flow(
        number_of_trees=number_of_trees,
        emitters_per_tree=emitters_per_tree,
        flow_per_emitter_lph=emitter_flow_lph,
    )
    total_emitters = number_of_trees * emitters_per_tree

    lateral_loss_m = calculate_dripline_head_loss(
        length_m=lateral_length_m,
        number_of_emitters=total_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=lateral_diameter_m,
    )

    required_lateral_inlet_pressure_bar = (
        target_emitter_pressure_bar + lateral_loss_m * 0.0980665
    )
    sector_analysis = {
        "total_flow_lph": total_flow_lph,
        "inlet_pressure_bar": required_lateral_inlet_pressure_bar,
    }

    pump_requirement = calculate_sector_pump_requirement(
        sector_analysis=sector_analysis,
        static_elevation_difference_m=static_elevation_difference_m,
        upstream_friction_losses_m=upstream_friction_losses_m,
        upstream_local_losses_m=upstream_local_losses_m,
    )

    assert total_flow_lph == pytest.approx(
        total_emitters * emitter_flow_lph
    )
    assert pump_requirement["sector_total_flow_m3_s"] == pytest.approx(
        liters_per_hour_to_cubic_meters_per_second(total_flow_lph)
    )
    assert pump_requirement["total_dynamic_head_m"] == pytest.approx(
        static_elevation_difference_m
        + required_lateral_inlet_pressure_bar * 10.197162129779
        + upstream_friction_losses_m
        + upstream_local_losses_m
    )
