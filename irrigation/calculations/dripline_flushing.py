"""Dripline flushing flow, water volume, and runtime estimates.

The required flushing velocity and number of pipe-volume exchanges are
explicit user inputs. This module does not prescribe universal maintenance
settings.
"""

import math


def _positive_finite(value, label):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be a finite positive number.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{label} must be a finite positive number.") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be a finite positive number.")
    return number


def calculate_dripline_flushing_requirement(
    internal_diameter_m,
    lateral_length_m,
    flushing_velocity_m_s,
    number_of_laterals=1,
    pipe_volume_exchanges=2.0,
):
    """Estimate flushing demand for identical laterals.

    Args:
        internal_diameter_m: Measured internal diameter of one lateral (m).
        lateral_length_m: Length of one lateral (m).
        flushing_velocity_m_s: User-selected mean water velocity (m/s).
        number_of_laterals: Number of identical laterals to flush.
        pipe_volume_exchanges: Flushing volume as a multiple of one lateral's
            internal water volume. The value must be selected by the designer.

    Returns per-lateral and total quantities. Sequential runtime assumes one
    lateral is flushed at a time. Simultaneous flow assumes all laterals are
    flushed together at the specified velocity.
    """
    diameter = _positive_finite(internal_diameter_m, "Internal diameter")
    length = _positive_finite(lateral_length_m, "Lateral length")
    velocity = _positive_finite(flushing_velocity_m_s, "Flushing velocity")
    exchanges = _positive_finite(pipe_volume_exchanges, "Pipe-volume exchanges")

    if (
        not isinstance(number_of_laterals, int)
        or isinstance(number_of_laterals, bool)
        or number_of_laterals <= 0
    ):
        raise ValueError("Number of laterals must be a positive integer.")

    try:
        area = math.pi * diameter ** 2 / 4.0
        pipe_volume_m3 = area * length
        flow_m3_s = velocity * area
        volume_per_lateral_m3 = pipe_volume_m3 * exchanges
        flow_lph = flow_m3_s * 3_600_000.0
        volume_per_lateral_l = volume_per_lateral_m3 * 1000.0
        runtime_seconds = volume_per_lateral_m3 / flow_m3_s
    except (OverflowError, ZeroDivisionError):
        raise ValueError("Flushing calculation produced an invalid result.") from None

    values = (
        area,
        pipe_volume_m3,
        flow_m3_s,
        volume_per_lateral_m3,
        flow_lph,
        volume_per_lateral_l,
        runtime_seconds,
    )
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise ValueError("Flushing calculation produced a non-finite result.")

    total_volume_l = volume_per_lateral_l * number_of_laterals
    simultaneous_flow_lph = flow_lph * number_of_laterals
    sequential_runtime_seconds = runtime_seconds * number_of_laterals

    if not all(math.isfinite(value) for value in (
        total_volume_l, simultaneous_flow_lph, sequential_runtime_seconds
    )):
        raise ValueError("Total flushing requirement is not finite.")

    return {
        "method": "dripline_pipe_volume_and_selected_flushing_velocity",
        "inputs": {
            "internal_diameter_m": diameter,
            "lateral_length_m": length,
            "flushing_velocity_m_s": velocity,
            "number_of_laterals": number_of_laterals,
            "pipe_volume_exchanges": exchanges,
        },
        "per_lateral": {
            "internal_pipe_volume_l": pipe_volume_m3 * 1000.0,
            "flushing_flow_lph": flow_lph,
            "flushing_water_volume_l": volume_per_lateral_l,
            "estimated_runtime_seconds": runtime_seconds,
            "estimated_runtime_minutes": runtime_seconds / 60.0,
        },
        "all_laterals": {
            "total_flushing_water_volume_l": total_volume_l,
            "simultaneous_required_flow_lph": simultaneous_flow_lph,
            "sequential_runtime_minutes": sequential_runtime_seconds / 60.0,
            "simultaneous_runtime_minutes": runtime_seconds / 60.0,
        },
        "limitations": [
            "Uses the measured internal diameter and a uniform full-pipe velocity.",
            "Flushing velocity and pipe-volume exchanges are user-selected inputs, not universal recommendations.",
            "Assumes identical laterals and excludes manifold, filter, and mainline flushing volumes.",
            "Does not calculate available source flow, pressure, outlet restrictions, or sediment transport.",
            "Confirm the manufacturer's flushing instructions and ensure the flush outlet is fully open.",
        ],
    }
