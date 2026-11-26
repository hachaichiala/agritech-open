"""
Pump power calculations at a defined operating point.

Flow is in m3/s, head in meters, efficiencies in percent, and
calculated power values in watts. Electrical input power is omitted
when motor efficiency is not supplied.
"""

import math


def _finite_float(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    try:
        converted = float(value)
    except (OverflowError, TypeError, ValueError):
        raise ValueError(f"{name} must be a finite number.") from None
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be a finite number.")
    return converted


def calculate_pump_power(
    flow_m3_s,
    head_m,
    pump_efficiency_percent,
    motor_efficiency_percent=None,
    water_density_kg_m3=1000.0,
    gravity_m_s2=9.80665,
) -> dict:
    """
    Calculate hydraulic and shaft power at a pump operating point.

    Hydraulic power = density * gravity * flow * head.
    Shaft power = hydraulic power / pump efficiency.
    Electrical input power is calculated only when motor efficiency
    is supplied. Omitting motor efficiency avoids assuming an ideal
    100% efficient motor when its data is unknown.
    """
    flow = _finite_float(flow_m3_s, "Flow")
    head = _finite_float(head_m, "Head")
    pump_eff = _finite_float(
        pump_efficiency_percent, "Pump efficiency"
    )
    density = _finite_float(water_density_kg_m3, "Water density")
    gravity = _finite_float(gravity_m_s2, "Gravity")

    if flow <= 0:
        raise ValueError("Flow must be positive.")
    if head <= 0:
        raise ValueError("Head must be positive.")
    if not 0 < pump_eff <= 100:
        raise ValueError("Pump efficiency must be in the range (0, 100].")
    if density <= 0:
        raise ValueError("Water density must be positive.")
    if gravity <= 0:
        raise ValueError("Gravity must be positive.")

    motor_eff = None
    if motor_efficiency_percent is not None:
        motor_eff = _finite_float(
            motor_efficiency_percent, "Motor efficiency"
        )
        if not 0 < motor_eff <= 100:
            raise ValueError(
                "Motor efficiency must be in the range (0, 100]."
            )

    hydraulic_power = density * gravity * flow * head
    shaft_power = hydraulic_power / (pump_eff / 100.0)
    electrical_power = (
        shaft_power / (motor_eff / 100.0)
        if motor_eff is not None
        else None
    )

    powers = (hydraulic_power, shaft_power)
    if electrical_power is not None:
        powers += (electrical_power,)
    if not all(math.isfinite(value) for value in powers):
        raise ValueError("Calculated pump power is not finite.")

    return {
        "flow_m3_s": flow,
        "head_m": head,
        "pump_efficiency_percent": pump_eff,
        "motor_efficiency_percent": motor_eff,
        "hydraulic_power_w": hydraulic_power,
        "shaft_power_w": shaft_power,
        "electrical_input_power_w": electrical_power,
    }
