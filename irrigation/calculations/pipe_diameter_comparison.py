"""
Compare pump operation across alternative upstream pipe diameters.

All hydraulic inputs and pump data stay fixed except pipe diameter.
Each diameter is evaluated independently. A diameter with no operating
point is reported as an unsuccessful scenario rather than aborting the
entire comparison.
"""

import math

from .operating_analysis import analyze_pump_system
from .pump_data import validate_pump_data
from .system_curve import build_system_curve


def _positive_finite(value, name):
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
    ):
        raise ValueError(f"{name} must be a finite positive number.")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid or value <= 0:
        raise ValueError(f"{name} must be a finite positive number.")
    return float(value)


def compare_pipe_diameters(
    pump_data,
    system_curve_parameters,
    pipe_diameters_m,
    pump_efficiency_percent=None,
    motor_efficiency_percent=None,
):
    """
    Compare operating conditions for multiple upstream pipe diameters.

    system_curve_parameters uses the build_system_curve arguments.
    Its upstream_pipe_diameter_m value, if present, is replaced for each
    scenario. Results preserve the input diameter order.
    """
    if not isinstance(system_curve_parameters, dict):
        raise ValueError("System curve parameters must be a dictionary.")
    if (
        not isinstance(pipe_diameters_m, (list, tuple))
        or len(pipe_diameters_m) < 2
    ):
        raise ValueError("At least two pipe diameters are required.")

    diameters = [
        _positive_finite(value, "Pipe diameter")
        for value in pipe_diameters_m
    ]
    if len(set(diameters)) != len(diameters):
        raise ValueError("Pipe diameters must be unique.")

    validate_pump_data(pump_data)

    base_parameters = dict(system_curve_parameters)
    base_parameters.pop("upstream_pipe_diameter_m", None)
    # Validate all shared hydraulic inputs before evaluating scenarios.
    build_system_curve(
        upstream_pipe_diameter_m=diameters[0],
        **base_parameters,
    )

    scenarios = []
    for diameter in diameters:
        parameters = {
            **base_parameters,
            "upstream_pipe_diameter_m": diameter,
        }
        try:
            analysis = analyze_pump_system(
                pump_data=pump_data,
                system_curve_parameters=parameters,
                pump_efficiency_percent=pump_efficiency_percent,
                motor_efficiency_percent=motor_efficiency_percent,
            )
            scenarios.append({
                "pipe_diameter_m": diameter,
                "status": "success",
                "analysis": analysis,
            })
        except ValueError as exc:
            scenarios.append({
                "pipe_diameter_m": diameter,
                "status": "no_valid_operating_analysis",
                "error": str(exc),
            })

    return {
        "scenarios": scenarios,
        "method": "independent_pump_analysis_for_each_pipe_diameter",
        "assumptions": [
            "Only upstream pipe internal diameter changes between scenarios.",
            "Pump curve and all other hydraulic inputs stay constant.",
            "No pipe purchase or installation costs are included.",
            "Operating points use the supplied pump and system curves without extrapolation.",
        ],
    }
