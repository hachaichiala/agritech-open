"""
Build a system curve for an upstream pipe feeding an irrigation sector.

Hazen-Williams calculates pipe friction. A combined K coefficient
calculates local losses from velocity head.
"""
import math

from .pressure_loss import calculate_hazen_williams_head_loss
from .pump_head import calculate_required_pump_head


def _finite(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number.")
    try:
        valid = math.isfinite(value)
    except OverflowError:
        valid = False
    if not valid:
        raise ValueError(f"{name} must be a finite number.")
    return float(value)


def build_system_curve(
    flow_rates_m3_s,
    static_elevation_difference_m,
    required_sector_inlet_pressure_bar,
    upstream_pipe_length_m,
    upstream_pipe_diameter_m,
    hazen_williams_c=150,
    local_loss_coefficient=0.0,
):
    """Return system curve points and hydraulic loss details per flow."""
    if not isinstance(flow_rates_m3_s, (list, tuple)) or len(flow_rates_m3_s) < 2:
        raise ValueError("At least two flow-rate points are required.")

    flows = [_finite(v, "Flow rate") for v in flow_rates_m3_s]
    if any(v < 0 for v in flows):
        raise ValueError("Flow rates cannot be negative.")
    if any(b <= a for a, b in zip(flows, flows[1:])):
        raise ValueError("Flow rates must be strictly increasing.")

    elevation = _finite(static_elevation_difference_m, "Static elevation difference")
    length = _finite(upstream_pipe_length_m, "Upstream pipe length")
    diameter = _finite(upstream_pipe_diameter_m, "Upstream pipe diameter")
    hw_c = _finite(hazen_williams_c, "Hazen-Williams coefficient")
    local_k = _finite(local_loss_coefficient, "Local loss coefficient")

    if length < 0:
        raise ValueError("Upstream pipe length cannot be negative.")
    if diameter <= 0:
        raise ValueError("Upstream pipe diameter must be positive.")
    if hw_c <= 0:
        raise ValueError("Hazen-Williams coefficient must be positive.")
    if local_k < 0:
        raise ValueError("Local loss coefficient cannot be negative.")

    area = math.pi * diameter ** 2 / 4.0
    curve = []
    details = []

    for flow in flows:
        friction = calculate_hazen_williams_head_loss(
            length_m=length,
            flow_m3_s=flow,
            diameter_m=diameter,
            hazen_williams_c=hw_c,
        )
        velocity = flow / area
        try:
            local = local_k * velocity ** 2 / (2.0 * 9.80665)
        except OverflowError as exc:
            raise ValueError("Calculated local head loss must be finite.") from exc
        if not math.isfinite(local):
            raise ValueError("Calculated local head loss must be finite.")

        total = calculate_required_pump_head(
            static_elevation_difference_m=elevation,
            required_sector_inlet_pressure_bar=required_sector_inlet_pressure_bar,
            upstream_friction_losses_m=friction,
            upstream_local_losses_m=local,
        )["total_dynamic_head_m"]

        curve.append((flow, total))
        details.append({
            "flow_m3_s": flow,
            "velocity_m_s": velocity,
            "friction_loss_m": friction,
            "local_loss_m": local,
            "total_head_m": total,
        })

    return {
        "system_curve": curve,
        "flow_details": details,
        "method": "hazen_williams_friction_plus_k_factor_local_losses",
        "assumptions": [
            "Single upstream pipe with constant internal diameter.",
            "Combined local-loss coefficient K is constant.",
            "Sector inlet pressure is held at the specified design value.",
            "Sector internal losses are represented by the required inlet pressure.",
        ],
    }
