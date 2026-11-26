import pytest

from irrigation.calculations.emitters import (
    calculate_total_emitters,
    calculate_tree_zone_flow,
)


def test_total_emitters():
    result = calculate_total_emitters(200, 2)
    assert result == 400


def test_tree_zone_flow():
    result = calculate_tree_zone_flow(200, 2, 8)
    assert result == 3200


def test_invalid_tree_count():
    with pytest.raises(ValueError):
        calculate_total_emitters(0, 2)


def test_invalid_emitters_per_tree():
    with pytest.raises(ValueError):
        calculate_total_emitters(10, 0)


def test_boolean_tree_count():
    with pytest.raises(ValueError):
        calculate_total_emitters(True, 2)


def test_boolean_emitters_per_tree():
    with pytest.raises(ValueError):
        calculate_total_emitters(10, True)

@pytest.mark.parametrize(
    "invalid_count",
    [-1, 1.5, "10", None],
)
def test_invalid_tree_count_types_and_negative_values(invalid_count):
    with pytest.raises(ValueError, match="Number of trees"):
        calculate_total_emitters(invalid_count, 2)


@pytest.mark.parametrize(
    "invalid_count",
    [-1, 1.5, "2", None],
)
def test_invalid_emitters_per_tree_types_and_negative_values(invalid_count):
    with pytest.raises(ValueError, match="Emitters per tree"):
        calculate_total_emitters(10, invalid_count)


@pytest.mark.parametrize("invalid_flow", [0, -8, float("inf"), float("nan"), True])
def test_tree_zone_flow_rejects_invalid_emitter_flow(invalid_flow):
    with pytest.raises(ValueError):
        calculate_tree_zone_flow(10, 2, invalid_flow)

