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


from irrigation.calculations.dripline import calculate_pressure_at_each_emitter
from irrigation.calculations.system_curve import build_system_curve


@pytest.mark.parametrize(
    "number_of_emitters, lateral_length_m, lateral_diameter_m",
    [
        (12, 60.0, 0.016),
        (20, 100.0, 0.020),
    ],
)
def test_lateral_emitter_pressure_and_system_curve_integration(
    number_of_emitters,
    lateral_length_m,
    lateral_diameter_m,
):
    emitter_flow_lph = 8.0
    target_emitter_pressure_bar = 1.5
    static_elevation_difference_m = 2.4
    upstream_pipe_length_m = 75.0
    upstream_pipe_diameter_m = 0.04
    local_loss_coefficient = 2.0

    lateral_loss_m = calculate_dripline_head_loss(
        length_m=lateral_length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=lateral_diameter_m,
    )
    required_inlet_pressure_bar = (
        target_emitter_pressure_bar + lateral_loss_m * 0.0980665
    )

    emitter_pressures = calculate_pressure_at_each_emitter(
        inlet_pressure_bar=required_inlet_pressure_bar,
        length_m=lateral_length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=lateral_diameter_m,
    )

    assert emitter_pressures[-1] == pytest.approx(
        target_emitter_pressure_bar
    )
    assert all(
        upstream >= downstream
        for upstream, downstream in zip(
            emitter_pressures, emitter_pressures[1:]
        )
    )

    total_flow_lph = number_of_emitters * emitter_flow_lph
    total_flow_m3_s = liters_per_hour_to_cubic_meters_per_second(
        total_flow_lph
    )
    sector_analysis = {
        "total_flow_lph": total_flow_lph,
        "inlet_pressure_bar": required_inlet_pressure_bar,
    }

    pump_requirement = calculate_sector_pump_requirement(
        sector_analysis=sector_analysis,
        static_elevation_difference_m=static_elevation_difference_m,
    )

    system_curve = build_system_curve(
        flow_rates_m3_s=[total_flow_m3_s, 2.0 * total_flow_m3_s],
        static_elevation_difference_m=static_elevation_difference_m,
        required_sector_inlet_pressure_bar=required_inlet_pressure_bar,
        upstream_pipe_length_m=upstream_pipe_length_m,
        upstream_pipe_diameter_m=upstream_pipe_diameter_m,
        local_loss_coefficient=local_loss_coefficient,
    )

    design_point = system_curve["flow_details"][0]
    integrated_head = (
        pump_requirement["total_dynamic_head_m"]
        + design_point["friction_loss_m"]
        + design_point["local_loss_m"]
    )
    assert system_curve["system_curve"][0][0] == pytest.approx(
        total_flow_m3_s
    )
    assert system_curve["system_curve"][0][1] == pytest.approx(
        integrated_head
    )
