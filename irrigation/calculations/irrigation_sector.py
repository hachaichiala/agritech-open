"""
Integrated hydraulic analysis for a sector of parallel drip laterals.

Model assumptions:
- Laterals have equal lengths, emitter counts, and emitter flow rates.
- Laterals are equally spaced along a straight, horizontal manifold.
- The manifold and laterals are horizontal.
- Each manifold segment ends at one lateral takeoff.
- Hazen-Williams friction losses are included.
- Local losses, elevation differences, valves, filters, and fittings are
  excluded and must be assessed separately in a full system design.
"""

from .emitter_pressure import (
    EmitterPressureRange,
    analyze_dripline_emitter_pressures,
)
from .flow import calculate_total_flow
from .manifold import (
    calculate_manifold_head_loss,
    calculate_manifold_total_flow,
    calculate_pressure_at_each_lateral_takeoff,
)


def analyze_irrigation_sector(
    number_of_laterals: int,
    emitters_per_lateral: int,
    emitter_flow_lph: float,
    lateral_length_m: float,
    lateral_diameter_m: float,
    manifold_length_m: float,
    manifold_diameter_m: float,
    inlet_pressure_bar: float,
    pressure_range: EmitterPressureRange,
    hazen_williams_c: float = 150,
) -> dict:
    """
    Analyze manifold pressure and every emitter in a parallel-lateral sector.

    Returns total sector flow, manifold head loss, pressure at each lateral
    inlet, emitter pressures, and sector-wide pressure compliance.
    """
    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    lateral_flow_lph = calculate_total_flow(
        number_of_drippers=emitters_per_lateral,
        flow_per_dripper_lph=emitter_flow_lph,
    )

    total_flow_lph = calculate_manifold_total_flow(
        number_of_laterals=number_of_laterals,
        lateral_flow_lph=lateral_flow_lph,
    )

    manifold_head_loss_m = calculate_manifold_head_loss(
        length_m=manifold_length_m,
        number_of_laterals=number_of_laterals,
        lateral_flow_lph=lateral_flow_lph,
        diameter_m=manifold_diameter_m,
        hazen_williams_c=hazen_williams_c,
    )

    lateral_inlet_pressures_bar = calculate_pressure_at_each_lateral_takeoff(
        inlet_pressure_bar=inlet_pressure_bar,
        length_m=manifold_length_m,
        number_of_laterals=number_of_laterals,
        lateral_flow_lph=lateral_flow_lph,
        diameter_m=manifold_diameter_m,
        hazen_williams_c=hazen_williams_c,
    )

    laterals = []
    all_emitter_pressures_bar = []

    for index, lateral_inlet_pressure_bar in enumerate(
        lateral_inlet_pressures_bar,
        start=1,
    ):
        lateral_result = analyze_dripline_emitter_pressures(
            inlet_pressure_bar=lateral_inlet_pressure_bar,
            length_m=lateral_length_m,
            number_of_emitters=emitters_per_lateral,
            emitter_flow_lph=emitter_flow_lph,
            diameter_m=lateral_diameter_m,
            pressure_range=pressure_range,
            hazen_williams_c=hazen_williams_c,
        )
        all_emitter_pressures_bar.extend(
            lateral_result["emitter_pressures_bar"]
        )
        laterals.append({
            "lateral_number": index,
            **lateral_result,
        })

    total_emitters = len(all_emitter_pressures_bar)
    lateral_inlet_pressures = [
        lateral["inlet_pressure_bar"] for lateral in laterals
    ]
    lateral_outlet_pressures = [
        lateral["outlet_pressure_bar"] for lateral in laterals
    ]
    lateral_head_losses = [
        lateral["head_loss_m"] for lateral in laterals
    ]
    emitters_within_range = sum(
        pressure_range.minimum_bar <= pressure <= pressure_range.maximum_bar
        for pressure in all_emitter_pressures_bar
    )
    emitters_outside_range = total_emitters - emitters_within_range
    compliance_percentage = (
        emitters_within_range / total_emitters * 100.0
    )

    return {
        "inlet_pressure_bar": inlet_pressure_bar,
        "total_flow_lph": total_flow_lph,
        "lateral_flow_lph": lateral_flow_lph,
        "manifold_head_loss_m": manifold_head_loss_m,
        "lateral_inlet_pressures_bar": lateral_inlet_pressures_bar,
        "minimum_lateral_inlet_pressure_bar": min(lateral_inlet_pressures),
        "maximum_lateral_inlet_pressure_bar": max(lateral_inlet_pressures),
        "minimum_lateral_outlet_pressure_bar": min(lateral_outlet_pressures),
        "maximum_lateral_outlet_pressure_bar": max(lateral_outlet_pressures),
        "minimum_lateral_head_loss_m": min(lateral_head_losses),
        "maximum_lateral_head_loss_m": max(lateral_head_losses),
        "laterals": laterals,
        "total_emitters": total_emitters,
        "emitters_within_range": emitters_within_range,
        "emitters_outside_range": emitters_outside_range,
        "minimum_emitter_pressure_bar": min(all_emitter_pressures_bar),
        "maximum_emitter_pressure_bar": max(all_emitter_pressures_bar),
        "compliance_percentage": compliance_percentage,
        "all_emitters_within_range": (
            emitters_within_range == total_emitters
        ),
    }
