"""
Integrated pump operating-point and power analysis.

The rated motor power is treated as rated mechanical shaft output power.
It is compared with calculated pump shaft power, not electrical input.
"""

import math

from .pump_curve import find_pump_operating_point
from .pump_power import calculate_pump_power
from .pump_data import validate_pump_data
from .system_curve import build_system_curve


def _interpolate_efficiency(curve, flow):
    if flow < curve[0][0] or flow > curve[-1][0]:
        raise ValueError(
            "Operating flow lies outside the supplied efficiency curve."
        )
    for (flow_a, eff_a), (flow_b, eff_b) in zip(curve, curve[1:]):
        if flow_a <= flow <= flow_b:
            ratio = (flow - flow_a) / (flow_b - flow_a)
            return eff_a + ratio * (eff_b - eff_a)
    raise ValueError("Unable to interpolate pump efficiency at operating flow.")


def analyze_pump_operation(
    pump_data,
    system_curve,
    pump_efficiency_percent=None,
    motor_efficiency_percent=None,
):
    """
    Find the operating point and calculate power requirements.

    Pump efficiency comes from pump_data.efficiency_curve when supplied.
    Otherwise pump_efficiency_percent is required explicitly.
    Motor efficiency is optional. Rated motor power, when present, is
    compared with required shaft power as a mechanical output rating.
    """
    pump = validate_pump_data(pump_data)
    operating_point = find_pump_operating_point(
        pump["pump_curve"], system_curve
    )

    if "efficiency_curve" in pump:
        if pump_efficiency_percent is not None:
            raise ValueError(
                "Do not supply pump efficiency when an efficiency curve exists."
            )
        efficiency = _interpolate_efficiency(
            pump["efficiency_curve"], operating_point["flow_m3_s"]
        )
        efficiency_source = "interpolated_efficiency_curve"
    else:
        if pump_efficiency_percent is None:
            raise ValueError(
                "Pump efficiency is required when no efficiency curve is supplied."
            )
        efficiency = pump_efficiency_percent
        efficiency_source = "explicit_input"

    power = calculate_pump_power(
        flow_m3_s=operating_point["flow_m3_s"],
        head_m=operating_point["head_m"],
        pump_efficiency_percent=efficiency,
        motor_efficiency_percent=motor_efficiency_percent,
    )

    result = {
        "operating_point": operating_point,
        "power": power,
        "pump_efficiency_source": efficiency_source,
    }

    rated_power_kw = pump.get("rated_motor_power_kw")
    if rated_power_kw is not None:
        shaft_power_kw = power["shaft_power_w"] / 1000.0
        margin_kw = rated_power_kw - shaft_power_kw
        result["motor_power_check"] = {
            "rated_motor_power_kw": rated_power_kw,
            "required_shaft_power_kw": shaft_power_kw,
            "available_margin_kw": margin_kw,
            "within_rated_power": margin_kw >= 0,
            "rating_interpretation": "mechanical_shaft_output",
        }

    return result



def analyze_pump_system(
    pump_data,
    system_curve_parameters,
    pump_efficiency_percent=None,
    motor_efficiency_percent=None,
):
    """
    Build a system curve from hydraulic inputs, then analyze pump operation.

    system_curve_parameters must contain the keyword arguments accepted by
    build_system_curve. The returned result includes the generated curve,
    its hydraulic details, assumptions, and the operating/power analysis.
    """
    if not isinstance(system_curve_parameters, dict):
        raise ValueError("System curve parameters must be a dictionary.")

    system = build_system_curve(**system_curve_parameters)
    analysis = analyze_pump_operation(
        pump_data=pump_data,
        system_curve=system["system_curve"],
        pump_efficiency_percent=pump_efficiency_percent,
        motor_efficiency_percent=motor_efficiency_percent,
    )

    return {
        "system": system,
        "pump_analysis": analysis,
        "method": "generated_system_curve_then_pump_operating_analysis",
    }
