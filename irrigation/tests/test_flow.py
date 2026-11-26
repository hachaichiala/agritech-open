import pytest

from irrigation.calculations.flow import calculate_total_flow


def test_total_flow_basic():
    result = calculate_total_flow(200, 8)
    assert result == 1600


def test_total_flow_single_dripper():
    result = calculate_total_flow(1, 4)
    assert result == 4


def test_total_flow_invalid_number():
    with pytest.raises(ValueError):
        calculate_total_flow(0, 8)


def test_total_flow_negative_rate():
    with pytest.raises(ValueError):
        calculate_total_flow(10, -8)


def test_total_flow_invalid_type():
    with pytest.raises(ValueError):
        calculate_total_flow(10.5, 8)


def test_invalid_boolean_rate():
    with pytest.raises(ValueError):
        calculate_total_flow(10, True)


def test_invalid_infinite_rate():
    with pytest.raises(ValueError):
        calculate_total_flow(10, float("inf"))


def test_invalid_nan_rate():
    with pytest.raises(ValueError):
        calculate_total_flow(10, float("nan"))


@pytest.mark.parametrize(
    "number_of_drippers, flow_per_dripper",
    [
        (10**1000, 8),
        (10, 10**1000),
        (10**308, 1e308),
    ],
)
def test_total_flow_rejects_overflowing_inputs_or_result(
    number_of_drippers,
    flow_per_dripper,
):
    with pytest.raises(ValueError, match="finite"):
        calculate_total_flow(
            number_of_drippers,
            flow_per_dripper,
        )

@pytest.mark.parametrize(
    "number_of_drippers",
    [
        -1,
        True,
        "10",
    ],
)
def test_total_flow_rejects_invalid_dripper_counts(number_of_drippers):
    with pytest.raises(ValueError):
        calculate_total_flow(number_of_drippers, 8)

