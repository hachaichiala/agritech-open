"""
Pressure operating range and pressure checks
for pressure-compensating drip emitters.
"""

import math
from dataclasses import dataclass

from .dripline import (
    calculate_dripline_head_loss,
    calculate_pressure_at_each_emitter,
)


BAR_PER_METER_WATER = 0.0980665


def _is_positive_finite_number(value) -> bool:
    """Return whether value is a positive, finite int or float."""
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        return False

    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        return False


def _is_non_negative_finite_number(value) -> bool:
    """Return whether value is a non-negative, finite int or float."""
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        return False

    try:
        return math.isfinite(value) and value >= 0
    except OverflowError:
        return False


@dataclass(frozen=True)
class EmitterPressureRange:
    """Operating pressure limits in bar."""

    minimum_bar: float = 1.0
    maximum_bar: float = 4.0

    def __post_init__(self):
        if not _is_positive_finite_number(self.minimum_bar):
            raise ValueError(
                "Minimum pressure must be a positive finite number."
            )

        if not _is_positive_finite_number(self.maximum_bar):
            raise ValueError(
                "Maximum pressure must be a positive finite number."
            )

        if self.minimum_bar >= self.maximum_bar:
            raise ValueError(
                "Minimum pressure must be lower than maximum pressure."
            )


def is_pressure_in_compensation_range(
    pressure_bar: float,
    pressure_range: EmitterPressureRange,
) -> bool:
    """Check whether pressure is inside the PC operating range."""

    if not _is_positive_finite_number(pressure_bar):
        raise ValueError("Pressure must be a positive finite number.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    return (
        pressure_range.minimum_bar
        <= pressure_bar
        <= pressure_range.maximum_bar
    )


def check_dripline_pressure(
    inlet_pressure_bar: float,
    head_loss_m: float,
    pressure_range: EmitterPressureRange,
) -> dict:
    """
    Check inlet and outlet pressures against the PC range.

    uniform_compensation is retained for backward compatibility.
    It means both checked endpoint pressures are within the PC range.
    It is not a hydraulic distribution uniformity coefficient.
    """

    if not _is_positive_finite_number(inlet_pressure_bar):
        raise ValueError("Inlet pressure must be positive and finite.")

    if not _is_non_negative_finite_number(head_loss_m):
        raise ValueError("Head loss must be non-negative and finite.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    outlet_pressure_bar = (
        inlet_pressure_bar - head_loss_m * BAR_PER_METER_WATER
    )

    inlet_ok = is_pressure_in_compensation_range(
        inlet_pressure_bar, pressure_range
    )

    outlet_ok = (
        is_pressure_in_compensation_range(
            outlet_pressure_bar, pressure_range
        )
        if outlet_pressure_bar > 0
        else False
    )

    endpoints_within_range = inlet_ok and outlet_ok

    return {
        "inlet_pressure_bar": inlet_pressure_bar,
        "outlet_pressure_bar": outlet_pressure_bar,
        "inlet_within_range": inlet_ok,
        "outlet_within_range": outlet_ok,
        "all_checked_pressures_within_range": endpoints_within_range,
        "uniform_compensation": endpoints_within_range,
    }


def analyze_dripline_pressure(
    inlet_pressure_bar: float,
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    pressure_range: EmitterPressureRange,
    hazen_williams_c: float = 150,
    emitter_connection_k: float = 0.0,
    emitter_elevations_m: list | None = None,
) -> dict:
    """Calculate dripline losses and check endpoint PC pressure limits."""

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    head_loss_m = calculate_dripline_head_loss(
        length_m=length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
        emitter_connection_k=emitter_connection_k,
    )

    emitter_pressures_bar = calculate_pressure_at_each_emitter(
        inlet_pressure_bar=inlet_pressure_bar,
        length_m=length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
        emitter_connection_k=emitter_connection_k,
        emitter_elevations_m=emitter_elevations_m,
    )
    outlet_pressure_bar = emitter_pressures_bar[-1]
    if outlet_pressure_bar <= 0:
        raise ValueError(
            "Pressure reaches zero or below before the last emitter. "
            "Check inlet pressure, dripline dimensions, and emitter flow."
        )

    inlet_within_range = is_pressure_in_compensation_range(
        inlet_pressure_bar, pressure_range
    )
    outlet_within_range = is_pressure_in_compensation_range(
        outlet_pressure_bar, pressure_range
    )
    endpoints_within_range = inlet_within_range and outlet_within_range
    pressure_head_change_m = (
        inlet_pressure_bar - outlet_pressure_bar
    ) / BAR_PER_METER_WATER

    return {
        "inlet_pressure_bar": inlet_pressure_bar,
        "outlet_pressure_bar": outlet_pressure_bar,
        "inlet_within_range": inlet_within_range,
        "outlet_within_range": outlet_within_range,
        "all_checked_pressures_within_range": endpoints_within_range,
        "uniform_compensation": endpoints_within_range,
        "head_loss_m": head_loss_m,
        "pressure_head_change_m": pressure_head_change_m,
    }


def analyze_emitter_pressure_distribution(
    emitter_pressures_bar: list,
    pressure_range: EmitterPressureRange,
) -> dict:
    """Analyze pressure distribution across all emitters."""

    if not isinstance(emitter_pressures_bar, list):
        raise ValueError("Emitter pressures must be a list.")

    if not emitter_pressures_bar:
        raise ValueError("Emitter pressure list cannot be empty.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    for pressure in emitter_pressures_bar:
        if not _is_positive_finite_number(pressure):
            raise ValueError(
                "All emitter pressures must be positive finite numbers."
            )

    pressures_within_range = [
        pressure_range.minimum_bar <= pressure <= pressure_range.maximum_bar
        for pressure in emitter_pressures_bar
    ]

    within_count = sum(pressures_within_range)
    total_count = len(emitter_pressures_bar)
    compliance_percentage = within_count / total_count * 100.0

    return {
        "total_emitters": total_count,
        "emitters_within_range": within_count,
        "emitters_outside_range": total_count - within_count,
        "minimum_pressure_bar": min(emitter_pressures_bar),
        "maximum_pressure_bar": max(emitter_pressures_bar),
        "all_emitters_within_range": within_count == total_count,
        "compliance_percentage": compliance_percentage,
    }


def analyze_dripline_emitter_pressures(
    inlet_pressure_bar: float,
    length_m: float,
    number_of_emitters: int,
    emitter_flow_lph: float,
    diameter_m: float,
    pressure_range: EmitterPressureRange,
    hazen_williams_c: float = 150,
    emitter_connection_k: float = 0.0,
    emitter_elevations_m: list | None = None,
) -> dict:
    """
    Calculate and assess pressure at every emitter along a dripline.

    Emitters are assumed to be equally spaced. Optional elevations are
    measured relative to the lateral inlet, with positive values uphill.
    """

    if not _is_positive_finite_number(inlet_pressure_bar):
        raise ValueError("Inlet pressure must be positive and finite.")

    if not isinstance(pressure_range, EmitterPressureRange):
        raise ValueError("Invalid emitter pressure range.")

    emitter_pressures_bar = calculate_pressure_at_each_emitter(
        inlet_pressure_bar=inlet_pressure_bar,
        length_m=length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
        emitter_connection_k=emitter_connection_k,
        emitter_elevations_m=emitter_elevations_m,
    )

    if any(pressure <= 0 for pressure in emitter_pressures_bar):
        raise ValueError(
            "Pressure reaches zero or below before the last emitter. "
            "Check inlet pressure, dripline dimensions, and emitter flow."
        )

    distribution = analyze_emitter_pressure_distribution(
        emitter_pressures_bar=emitter_pressures_bar,
        pressure_range=pressure_range,
    )

    head_loss_m = calculate_dripline_head_loss(
        length_m=length_m,
        number_of_emitters=number_of_emitters,
        emitter_flow_lph=emitter_flow_lph,
        diameter_m=diameter_m,
        hazen_williams_c=hazen_williams_c,
        emitter_connection_k=emitter_connection_k,
    )
    pressure_head_change_m = (
        inlet_pressure_bar - emitter_pressures_bar[-1]
    ) / BAR_PER_METER_WATER

    inlet_within_range = is_pressure_in_compensation_range(
        inlet_pressure_bar, pressure_range
    )

    return {
        "inlet_pressure_bar": inlet_pressure_bar,
        "outlet_pressure_bar": emitter_pressures_bar[-1],
        "head_loss_m": head_loss_m,
        "pressure_head_change_m": pressure_head_change_m,
        "emitter_pressures_bar": emitter_pressures_bar,
        "inlet_within_range": inlet_within_range,
        **distribution,
        "all_pressures_within_range": (
            inlet_within_range
            and distribution["all_emitters_within_range"]
        ),
    }


def analyze_non_compensating_dripline(
    inlet_pressure_bar: float,
    length_m: float,
    number_of_emitters: int,
    reference_flow_lph: float,
    reference_pressure_bar: float,
    discharge_exponent: float,
    diameter_m: float,
    hazen_williams_c: float = 150,
    emitter_connection_k: float = 0.0,
    emitter_elevations_m: list | None = None,
    tolerance: float = 1e-8,
    max_iterations: int = 500,
) -> dict:
    """
    Solve a non-pressure-compensating lateral using q = q_ref*(P/P_ref)^x.

    All emitter curve parameters must come from the emitter manufacturer.
    The iteration updates emitter flows from local pressures, then recomputes
    each segment flow from the sum of its emitter and all downstream flows.
    """
    from .pressure_loss import (
        calculate_hazen_williams_head_loss,
        calculate_minor_head_loss,
    )
    from .units import liters_per_hour_to_cubic_meters_per_second

    numeric_inputs = {
        "Inlet pressure": inlet_pressure_bar,
        "Reference emitter flow": reference_flow_lph,
        "Reference pressure": reference_pressure_bar,
        "Discharge exponent": discharge_exponent,
        "Length": length_m,
        "Diameter": diameter_m,
        "Hazen-Williams coefficient": hazen_williams_c,
        "Emitter connection K": emitter_connection_k,
        "Tolerance": tolerance,
    }
    normalized = {}
    for name, value in numeric_inputs.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{name} must be a finite number.")
        try:
            value = float(value)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(f"{name} must be a finite number.") from None
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number.")
        normalized[name] = value

    inlet_pressure_bar = normalized["Inlet pressure"]
    reference_flow_lph = normalized["Reference emitter flow"]
    reference_pressure_bar = normalized["Reference pressure"]
    discharge_exponent = normalized["Discharge exponent"]
    length_m = normalized["Length"]
    diameter_m = normalized["Diameter"]
    hazen_williams_c = normalized["Hazen-Williams coefficient"]
    emitter_connection_k = normalized["Emitter connection K"]
    tolerance = normalized["Tolerance"]

    if inlet_pressure_bar <= 0 or reference_flow_lph <= 0:
        raise ValueError("Inlet pressure and reference flow must be positive.")
    if reference_pressure_bar <= 0:
        raise ValueError("Reference pressure must be positive.")
    if discharge_exponent < 0:
        raise ValueError("Discharge exponent cannot be negative.")
    if length_m <= 0 or diameter_m <= 0 or hazen_williams_c <= 0:
        raise ValueError("Length, diameter, and Hazen-Williams C must be positive.")
    if emitter_connection_k < 0:
        raise ValueError("Emitter connection K cannot be negative.")
    if tolerance <= 0:
        raise ValueError("Tolerance must be positive.")
    if (
        not isinstance(number_of_emitters, int)
        or isinstance(number_of_emitters, bool)
        or number_of_emitters <= 0
    ):
        raise ValueError("Number of emitters must be a positive integer.")
    if (
        not isinstance(max_iterations, int)
        or isinstance(max_iterations, bool)
        or max_iterations <= 0
    ):
        raise ValueError("Maximum iterations must be a positive integer.")

    if emitter_elevations_m is None:
        elevations = [0.0] * number_of_emitters
    else:
        if (
            not isinstance(emitter_elevations_m, (list, tuple))
            or len(emitter_elevations_m) != number_of_emitters
        ):
            raise ValueError("Emitter elevations must contain one value per emitter.")
        elevations = []
        for elevation in emitter_elevations_m:
            if (
                not isinstance(elevation, (int, float))
                or isinstance(elevation, bool)
            ):
                raise ValueError("Emitter elevations must be finite numbers.")
            try:
                elevation = float(elevation)
            except (TypeError, ValueError, OverflowError):
                raise ValueError("Emitter elevations must be finite numbers.") from None
            if not math.isfinite(elevation):
                raise ValueError("Emitter elevations must be finite numbers.")
            elevations.append(elevation)

    segment_length = length_m / number_of_emitters

    def hydraulic_state(flows_lph):
        pressures = []
        segment_losses = []
        cumulative_loss = 0.0
        for index, flow in enumerate(flows_lph):
            downstream_flow_lph = sum(flows_lph[index:])
            flow_m3_s = liters_per_hour_to_cubic_meters_per_second(
                downstream_flow_lph
            )
            friction = calculate_hazen_williams_head_loss(
                segment_length, flow_m3_s, diameter_m, hazen_williams_c
            )
            local = calculate_minor_head_loss(
                flow_m3_s, diameter_m, emitter_connection_k
            )
            segment_loss = friction + local
            segment_losses.append(segment_loss)
            cumulative_loss += segment_loss
            pressure_head_change = cumulative_loss + elevations[index]
            pressure = (
                inlet_pressure_bar
                - pressure_head_change * BAR_PER_METER_WATER
            )
            if not math.isfinite(pressure) or pressure <= 0:
                raise ValueError(
                    "Pressure reaches zero or below. Check inlet pressure, "
                    "lateral dimensions, emitter data, and elevations."
                )
            pressures.append(pressure)
        return pressures, segment_losses

    flows = [reference_flow_lph] * number_of_emitters
    converged = False
    iteration_count = 0

    for iteration_count in range(1, max_iterations + 1):
        pressures, _ = hydraulic_state(flows)
        try:
            target_flows = [
                reference_flow_lph
                * (pressure / reference_pressure_bar) ** discharge_exponent
                for pressure in pressures
            ]
        except (OverflowError, ZeroDivisionError):
            raise ValueError(
                "Emitter discharge calculation produced an invalid value."
            ) from None
        if any(not math.isfinite(flow) or flow <= 0 for flow in target_flows):
            raise ValueError("Calculated emitter flows must be positive and finite.")
        relative_change = max(
            abs(new - old) / max(abs(new), 1e-12)
            for new, old in zip(target_flows, flows)
        )
        if relative_change <= tolerance:
            flows = target_flows
            converged = True
            break
        flows = [
            0.5 * old + 0.5 * new
            for old, new in zip(flows, target_flows)
        ]

    if not converged:
        raise ValueError(
            f"Emitter flow calculation did not converge within {max_iterations} iterations."
        )

    pressures, segment_losses = hydraulic_state(flows)
    total_head_loss = sum(segment_losses)
    total_flow_lph = sum(flows)
    return {
        "emitter_flows_lph": flows,
        "emitter_pressures_bar": pressures,
        "segment_head_losses_m": segment_losses,
        "head_loss_m": total_head_loss,
        "inlet_pressure_bar": inlet_pressure_bar,
        "outlet_pressure_bar": pressures[-1],
        "total_flow_lph": total_flow_lph,
        "iterations": iteration_count,
        "converged": True,
        "maximum_flow_lph": max(flows),
        "minimum_flow_lph": min(flows),
        "flow_uniformity_percentage": min(flows) / max(flows) * 100.0,
    }
