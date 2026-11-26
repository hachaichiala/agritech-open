"""
Emitter quantity and flow calculations.
"""

from .flow import calculate_total_flow


def calculate_total_emitters(
    number_of_trees: int,
    emitters_per_tree: int
) -> int:
    """
    Calculate the total number of emitters.

    Args:
        number_of_trees: Number of trees in the irrigation zone.
        emitters_per_tree: Number of emitters per tree.

    Returns:
        Total number of emitters.
    """

    if (
        not isinstance(number_of_trees, int)
        or isinstance(number_of_trees, bool)
        or number_of_trees <= 0
    ):
        raise ValueError("Number of trees must be a positive integer.")

    if (
        not isinstance(emitters_per_tree, int)
        or isinstance(emitters_per_tree, bool)
        or emitters_per_tree <= 0
    ):
        raise ValueError("Emitters per tree must be a positive integer.")

    return number_of_trees * emitters_per_tree


def calculate_tree_zone_flow(
    number_of_trees: int,
    emitters_per_tree: int,
    flow_per_emitter_lph: float
) -> float:
    """
    Calculate the total flow rate for a tree irrigation zone.
    """

    total_emitters = calculate_total_emitters(
        number_of_trees,
        emitters_per_tree
    )

    return calculate_total_flow(
        total_emitters,
        flow_per_emitter_lph
    )
