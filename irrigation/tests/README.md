Irrigation Tests


This directory contains tests for verifying the accuracy and reliability of hydraulic calculations.


Testing objectives




Verify calculation results against reference examples.


Test normal and extreme input values.


Detect invalid or inconsistent inputs.


Check unit conversions.


Verify Hazen-Williams head loss calculations.


Ensure consistent results across calculation modules.




Testing principles


Every calculation module must include automated tests before integration into the main application.


Status


Testing framework planned.
def test_invalid_boolean_rate():
    with pytest.raises(ValueError):
        calculate_total_flow(10, True)


def test_invalid_infinite_rate():
    with pytest.raises(ValueError):
        calculate_total_flow(10, float("inf"))


def test_invalid_nan_rate():
    with pytest.raises(ValueError):
        calculate_total_flow(10, float("nan"))

