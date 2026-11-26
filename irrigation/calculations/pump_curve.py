"""
Pump and system curve analysis.

Curve points use (flow_m3_s, head_m). Pump head must not increase with
flow, and system head must not decrease with flow. Both curves are
piecewise-linear between supplied points.
"""

import math


def _validate_curve(points, name, head_direction):
    if not isinstance(points, (list, tuple)) or len(points) < 2:
        raise ValueError(f"{name} must contain at least two points.")

    validated = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise ValueError(
                f"Each {name} point must be (flow_m3_s, head_m)."
            )
        flow, head = point
        for value, label in ((flow, "flow"), (head, "head")):
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                raise ValueError(
                    f"{name} {label} values must be finite numbers."
                )
        if flow < 0 or head < 0:
            raise ValueError(
                f"{name} flow and head values cannot be negative."
            )
        validated.append((float(flow), float(head)))

    for previous, current in zip(validated, validated[1:]):
        if current[0] <= previous[0]:
            raise ValueError(
                f"{name} flow values must be strictly increasing."
            )
        if head_direction == "decreasing" and current[1] > previous[1]:
            raise ValueError(f"{name} head must not increase with flow.")
        if head_direction == "increasing" and current[1] < previous[1]:
            raise ValueError(f"{name} head must not decrease with flow.")

    return validated


def _interpolate(curve, flow):
    for (flow_a, head_a), (flow_b, head_b) in zip(curve, curve[1:]):
        if flow_a <= flow <= flow_b:
            ratio = (flow - flow_a) / (flow_b - flow_a)
            return head_a + ratio * (head_b - head_a)
    raise ValueError("Flow lies outside the supplied curve.")


def find_pump_operating_point(pump_curve, system_curve) -> dict:
    """
    Find the intersection of supplied pump and system curves.

    Both curves must be sequences of (flow_m3_s, head_m) points.
    The result is a piecewise-linear intersection, not an extrapolation.
    """
    pump = _validate_curve(pump_curve, "Pump curve", "decreasing")
    system = _validate_curve(system_curve, "System curve", "increasing")

    overlap_min = max(pump[0][0], system[0][0])
    overlap_max = min(pump[-1][0], system[-1][0])
    if overlap_min > overlap_max:
        raise ValueError("Pump and system curves do not overlap.")

    breakpoints = sorted({
        overlap_min,
        overlap_max,
        *(
            flow for flow, _ in pump
            if overlap_min < flow < overlap_max
        ),
        *(
            flow for flow, _ in system
            if overlap_min < flow < overlap_max
        ),
    })

    differences = [
        _interpolate(pump, flow) - _interpolate(system, flow)
        for flow in breakpoints
    ]
    intersections = []

    for index, difference in enumerate(differences):
        if math.isclose(difference, 0.0, abs_tol=1e-12):
            intersections.append(breakpoints[index])

    for index in range(len(breakpoints) - 1):
        left_difference = differences[index]
        right_difference = differences[index + 1]
        if left_difference * right_difference < 0:
            left_flow = breakpoints[index]
            right_flow = breakpoints[index + 1]
            fraction = (
                left_difference
                / (left_difference - right_difference)
            )
            intersections.append(
                left_flow + fraction * (right_flow - left_flow)
            )

    unique_intersections = []
    for flow in sorted(intersections):
        if (
            not unique_intersections
            or not math.isclose(
                flow, unique_intersections[-1], rel_tol=1e-10, abs_tol=1e-12
            )
        ):
            unique_intersections.append(flow)

    if not unique_intersections:
        raise ValueError(
            "Pump and system curves have no intersection in the supplied range."
        )
    if len(unique_intersections) > 1:
        raise ValueError(
            "Pump and system curves have multiple intersections."
        )

    operating_flow = unique_intersections[0]
    pump_head = _interpolate(pump, operating_flow)
    system_head = _interpolate(system, operating_flow)
    operating_head = (pump_head + system_head) / 2

    return {
        "flow_m3_s": operating_flow,
        "head_m": operating_head,
        "pump_head_m": pump_head,
        "system_head_m": system_head,
        "method": "piecewise_linear_intersection",
    }
