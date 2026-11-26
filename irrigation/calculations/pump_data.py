"""
Validated pump specification data.

Flow is expressed in m3/s, head in meters of water column,
motor rated power in kW, and efficiency in percent.
"""

import math

from .pump_curve import validate_pump_curve


def _is_finite_number(value):
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _validate_efficiency_curve(points):
    if not isinstance(points, (list, tuple)) or len(points) < 2:
        raise ValueError(
            "Efficiency curve must contain at least two points."
        )

    validated = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(
                "Each efficiency point must be (flow_m3_s, efficiency_percent)."
            )
        flow, efficiency = point
        if not _is_finite_number(flow) or flow < 0:
            raise ValueError(
                "Efficiency curve flow must be a non-negative finite number."
            )
        if (
            not _is_finite_number(efficiency)
            or efficiency < 0
            or efficiency > 100
        ):
            raise ValueError(
                "Efficiency must be a finite percentage from 0 to 100."
            )
        validated.append((float(flow), float(efficiency)))

    for previous, current in zip(validated, validated[1:]):
        if current[0] <= previous[0]:
            raise ValueError(
                "Efficiency curve flow values must be strictly increasing."
            )

    return validated


def validate_pump_data(data):
    """
    Validate and normalize a pump specification dictionary.

    Required:
      pump_curve: sequence of (flow_m3_s, head_m) points.

    Optional:
      manufacturer: non-empty string.
      model: non-empty string.
      rated_motor_power_kw: positive motor rated power in kW.
      efficiency_curve: (flow_m3_s, efficiency_percent) points.

    Unknown fields are rejected to avoid silently ignoring input mistakes.
    """
    if not isinstance(data, dict):
        raise ValueError("Pump data must be a dictionary.")

    allowed_fields = {
        "manufacturer",
        "model",
        "rated_motor_power_kw",
        "pump_curve",
        "efficiency_curve",
    }
    unknown_fields = set(data) - allowed_fields
    if unknown_fields:
        names = ", ".join(sorted(str(field) for field in unknown_fields))
        raise ValueError(f"Unknown pump data fields: {names}.")

    if "pump_curve" not in data:
        raise ValueError("Pump data must include pump_curve.")

    normalized = {
        "pump_curve": validate_pump_curve(data["pump_curve"])
    }

    for field in ("manufacturer", "model"):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string.")
            normalized[field] = value.strip()

    if "rated_motor_power_kw" in data:
        power = data["rated_motor_power_kw"]
        if not _is_finite_number(power) or power <= 0:
            raise ValueError(
                "Rated motor power must be a positive finite value in kW."
            )
        normalized["rated_motor_power_kw"] = float(power)

    if "efficiency_curve" in data:
        normalized["efficiency_curve"] = _validate_efficiency_curve(
            data["efficiency_curve"]
        )

    return normalized
