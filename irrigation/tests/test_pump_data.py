import pytest

from irrigation.calculations.pump_data import validate_pump_data


def test_validates_and_normalizes_minimum_pump_data():
    result = validate_pump_data({
        "pump_curve": [(0, 40), (0.001, 20)],
    })

    assert result == {
        "pump_curve": [(0.0, 40.0), (0.001, 20.0)],
    }


def test_validates_complete_pump_specification():
    result = validate_pump_data({
        "manufacturer": "LEO",
        "model": "5DWm4/5-0.92P",
        "rated_motor_power_kw": 0.92,
        "pump_curve": [(0, 40), (0.001, 20)],
        "efficiency_curve": [(0, 0), (0.001, 65)],
    })

    assert result["manufacturer"] == "LEO"
    assert result["model"] == "5DWm4/5-0.92P"
    assert result["rated_motor_power_kw"] == pytest.approx(0.92)
    assert result["efficiency_curve"] == [(0.0, 0.0), (0.001, 65.0)]


@pytest.mark.parametrize("data", [None, [], "pump"])
def test_rejects_non_dictionary_pump_data(data):
    with pytest.raises(ValueError):
        validate_pump_data(data)


def test_rejects_missing_pump_curve():
    with pytest.raises(ValueError, match="pump_curve"):
        validate_pump_data({"model": "Example"})


def test_rejects_unknown_fields():
    with pytest.raises(ValueError, match="Unknown"):
        validate_pump_data({
            "pump_curve": [(0, 40), (0.001, 20)],
            "power": 0.92,
        })


@pytest.mark.parametrize("value", ["", "  ", None, 123])
def test_rejects_invalid_manufacturer_or_model(value):
    with pytest.raises(ValueError):
        validate_pump_data({
            "manufacturer": value,
            "pump_curve": [(0, 40), (0.001, 20)],
        })


@pytest.mark.parametrize("power", [0, -1, True, float("inf"), float("nan")])
def test_rejects_invalid_rated_motor_power(power):
    with pytest.raises(ValueError):
        validate_pump_data({
            "pump_curve": [(0, 40), (0.001, 20)],
            "rated_motor_power_kw": power,
        })


@pytest.mark.parametrize(
    "curve",
    [
        None,
        [],
        [(0, 60)],
        [(0, 60), (0, 65)],
        [(0, 60), (0.001, 101)],
        [(0, 60), (0.001, -1)],
        [(0, 60), (0.001, float("nan"))],
        [(0, True), (0.001, 65)],
    ],
)
def test_rejects_invalid_efficiency_curve(curve):
    with pytest.raises(ValueError):
        validate_pump_data({
            "pump_curve": [(0, 40), (0.001, 20)],
            "efficiency_curve": curve,
        })
