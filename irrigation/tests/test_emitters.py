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
