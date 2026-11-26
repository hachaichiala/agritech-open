
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
)

from .emitter_pressure import (
    EmitterPressureRange,
    is_pressure_in_compensation_range,
    check_dripline_pressure,
    analyze_dripline_pressure,
)
