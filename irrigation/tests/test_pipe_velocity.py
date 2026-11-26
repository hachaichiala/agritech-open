import math

import pytest

from irrigation.calculations.pipe_velocity import (
    assess_pipe_velocity,
    calculate_pipe_velocity,
)


def test_calculates_mean_pipe_velocity():
    result = calculate_pipe_velocity(0.001, 0.05)
    expected = 0.001 / (math.pi * 0.05 ** 2 / 4)
    assert result["velocity_m_s"] == pytest.approx(expected)


def test_classifies_velocity_within_configured_range():
    result = assess_pipe_velocity(0.001, 0.05, 0.3, 1.0)
    assert result["status"] == "within_range"
    assert result["assessment"] == "acceptable"


def test_classifies_low_velocity():
    result = assess_pipe_velocity(0.0001, 0.1)
    assert result["status"] == "below_minimum"
    assert result["assessment"] == "low_velocity"


def test_classifies_high_velocity():
    result = assess_pipe_velocity(0.01, 0.05)
    assert result["status"] == "above_maximum"
    assert result["assessment"] == "high_velocity"


def test_boundary_values_are_included_in_acceptable_range():
    area = math.pi * 0.05 ** 2 / 4
    low = assess_pipe_velocity(0.6 * area, 0.05, 0.6, 1.5)
    high = assess_pipe_velocity(1.5 * area, 0.05, 0.6, 1.5)
    assert low["status"] == "within_range"
    assert high["status"] == "within_range"


@pytest.mark.parametrize("flow,diameter", [(0, 0.05), (-1, 0.05), (0.1, 0), (0.1, -1), (float("nan"), 0.05)])
def test_rejects_invalid_flow_or_diameter(flow, diameter):
    with pytest.raises(ValueError):
        calculate_pipe_velocity(flow, diameter)


def test_rejects_invalid_velocity_limits():
    with pytest.raises(ValueError, match="lower than"):
        assess_pipe_velocity(0.001, 0.05, 1.5, 0.6)

@pytest.mark.parametrize("diameter", [1e-200, 1e200])
def test_rejects_unrepresentable_cross_sectional_areas(diameter):
    with pytest.raises(ValueError, match="cross-sectional area"):
        calculate_pipe_velocity(0.001, diameter)


@pytest.mark.parametrize(
    "flow, diameter, minimum, maximum",
    [
        (True, 0.05, 0.1, 1.0),
        (0.001, True, 0.1, 1.0),
        (0.001, 0.05, True, 1.0),
        (0.001, 0.05, 0.1, False),
        (0.001, 0.05, float("nan"), 1.0),
        (0.001, 0.05, 0.1, float("inf")),
    ],
)
def test_assessment_rejects_boolean_and_non_finite_inputs(
    flow, diameter, minimum, maximum
):
    with pytest.raises(ValueError):
        assess_pipe_velocity(flow, diameter, minimum, maximum)

@pytest.mark.parametrize(
    "flow, diameter",
    [
        (True, 0.05),
        (0.001, True),
        (float("inf"), 0.05),
        (0.001, float("inf")),
        (10**400, 0.05),
        (0.001, 10**400),
    ],
)
def test_calculation_rejects_boolean_infinite_and_unrepresentable_inputs(
    flow, diameter
):
    with pytest.raises(ValueError):
        calculate_pipe_velocity(flow, diameter)


def test_rejects_non_finite_calculated_velocity():
    with pytest.raises(ValueError, match="velocity must be finite"):
        calculate_pipe_velocity(1e308, 1e-100)


@pytest.mark.parametrize(
    "minimum",
    [0, -0.1, "0.6", 10**400],
)
def test_assessment_rejects_invalid_minimum_velocity(minimum):
    with pytest.raises(ValueError, match="Minimum velocity"):
        assess_pipe_velocity(0.001, 0.05, minimum, 1.5)


@pytest.mark.parametrize(
    "maximum",
    [0, -0.1, "1.5", 10**400],
)
def test_assessment_rejects_invalid_maximum_velocity(maximum):
    with pytest.raises(ValueError, match="Maximum velocity"):
        assess_pipe_velocity(0.001, 0.05, 0.6, maximum)


def test_assessment_rejects_equal_velocity_limits():
    with pytest.raises(ValueError, match="lower than"):
        assess_pipe_velocity(0.001, 0.05, 0.6, 0.6)

