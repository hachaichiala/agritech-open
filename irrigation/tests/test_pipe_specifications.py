import pytest

from irrigation.calculations.pipe_specifications import (
    analyze_pipe_specification,
    assess_pipe_pressure_rating,
    calculate_pipe_internal_diameter,
)


def test_calculates_internal_diameter_from_outside_diameter_and_wall():
    assert calculate_pipe_internal_diameter(0.050, 0.003) == pytest.approx(0.044)


@pytest.mark.parametrize(
    "outside, wall",
    [
        (0, 0.002),
        (-0.05, 0.002),
        (0.05, 0),
        (0.05, -0.002),
        (True, 0.002),
        (0.05, float("inf")),
        (0.05, float("nan")),
        (0.05, 0.025),
    ],
)
def test_internal_diameter_rejects_invalid_dimensions(outside, wall):
    with pytest.raises(ValueError):
        calculate_pipe_internal_diameter(outside, wall)


def test_pressure_rating_accepts_pressure_equal_to_rating():
    result = assess_pipe_pressure_rating(6, 6)
    assert result["within_rating"] is True
    assert result["status"] == "within_rating"
    assert result["pressure_margin_bar"] == 0


def test_pressure_rating_accepts_pressure_below_rating():
    result = assess_pipe_pressure_rating(4, 6)
    assert result["within_rating"] is True
    assert result["pressure_margin_bar"] == 2


def test_pressure_rating_rejects_pressure_above_rating():
    result = assess_pipe_pressure_rating(8, 6)
    assert result["within_rating"] is False
    assert result["status"] == "exceeds_rating"


@pytest.mark.parametrize(
    "design, rated",
    [
        (0, 6),
        (-1, 6),
        (True, 6),
        (float("inf"), 6),
        (4, 0),
        (4, -1),
        (4, False),
        (4, float("nan")),
    ],
)
def test_pressure_rating_rejects_invalid_pressures(design, rated):
    with pytest.raises(ValueError):
        assess_pipe_pressure_rating(design, rated)


def test_analyzes_complete_pipe_specification():
    result = analyze_pipe_specification(
        outside_diameter_m=0.050,
        wall_thickness_m=0.003,
        design_pressure_bar=5,
        rated_pressure_bar=6,
        material="PE",
    )
    assert result["internal_diameter_m"] == pytest.approx(0.044)
    assert result["material"] == "PE"
    assert result["status"] == "within_rating"
    assert result["manufacturer_rating_required"] is True


def test_pipe_specification_rejects_empty_material():
    with pytest.raises(ValueError, match="material"):
        analyze_pipe_specification(0.05, 0.003, 5, 6, "  ")
