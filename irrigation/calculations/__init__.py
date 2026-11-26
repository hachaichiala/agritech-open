
"""
Hydraulic calculation modules for drip irrigation networks.
"""

from .flow import calculate_total_flow

from .emitters import (
    calculate_total_emitters,
    calculate_tree_zone_flow,
)

from .pressure_loss import (
    calculate_hazen_williams_head_loss,
)

from .units import (
    liters_per_hour_to_cubic_meters_per_second,
    cubic_meters_per_second_to_liters_per_hour,
    bar_to_meters_of_water,
    meters_of_water_to_bar,
)

from .dripline import (
    calculate_dripline_head_loss,
    calculate_pressure_at_each_emitter,
)

from .emitter_pressure import (
    EmitterPressureRange,
    is_pressure_in_compensation_range,
    check_dripline_pressure,
    analyze_dripline_pressure,
    analyze_emitter_pressure_distribution,
    analyze_dripline_emitter_pressures,
)

from .manifold import (
    calculate_manifold_total_flow,
    calculate_manifold_head_loss,
    calculate_manifold_segment_head_losses,
    calculate_pressure_at_each_lateral_takeoff,
)

from .irrigation_sector import (
    analyze_irrigation_sector,
)

from .pump_curve import (
    validate_pump_curve,
    validate_system_curve,
    find_pump_operating_point,
)

from .pump_head import (
    calculate_required_pump_head,
    calculate_sector_pump_requirement,
)

from .pump_data import (
    validate_pump_data,
)

from .pump_power import (
    calculate_pump_power,
)
