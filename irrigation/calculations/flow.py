"""
Flow rate calculations for drip irrigation networks.
"""


def calculate_total_flow(
    number_of_drippers: int,
    flow_per_dripper_lph: float
) -> float:
    """
    Calculate the total irrigation flow rate.

    Args:
        number_of_drippers: Total number of drippers.
        flow_per_dripper_lph: Flow rate per dripper in liters/hour.

    Returns:
        Total flow rate in liters/hour.

    Raises:
        ValueError: If an input is invalid.
    """

    if not isinstance(number_of_drippers, int) or isinstance(number_of_drippers, bool):
        raise ValueError("Number of drippers must be an integer.")

    if number_of_drippers <= 0:
        raise ValueError("Number of drippers must be positive.")

    if not isinstance(flow_per_dripper_lph, (int, float)):
        raise ValueError("Dripper flow rate must be numeric.")

    if flow_per_dripper_lph <= 0:
        raise ValueError("Dripper flow rate must be positive.")

    return number_of_drippers * flow_per_dripper_lph
