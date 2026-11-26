import pytest

from irrigation.calculations.pump_head import (
    calculate_required_pump_head,
    calculate_sector_pump_requirement,
)


def test_required_pump_head_sums_all_components():
    result = calculate_required_pump_head(
        static_elevation_difference_m=5,
        required_sector_inlet_pressure_bar=2,
        upstream_friction_losses_m=3,
        upstream_local_losses_m=1.5,
    )

    assert result["pressure_head_m"] == pytest.approx(20.39432, rel=1e-5)
    assert result["total_dynamic_head_m"] == pytest.approx(
        5 + 20.39432 + 3 + 1.5,
        rel=1e-5,
    )


def test_required_pump_head_allows_negative_elevation_difference():
    result = calculate_required_pump_head(
        static_elevation_difference_m=-2,
        required_sector_inlet_pressure_bar=2,
    )

    assert result["total_dynamic_head_m"] == pytest.approx(
        20.39432 - 2,
        rel=1e-5,
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"static_elevation_difference_m": float("nan")},
        {"static_elevation_difference_m": True},
        {"required_sector_inlet_pressure_bar": 0},
        {"required_sector_inlet_pressure_bar": float("inf")},
        {"upstream_friction_losses_m": -1},
        {"upstream_friction_losses_m": float("nan")},
        {"upstream_local_losses_m": -1},
        {"upstream_local_losses_m": True},
    ],
)
def test_required_pump_head_rejects_invalid_inputs(overrides):
    values = {
        "static_elevation_difference_m": 5,
        "required_sector_inlet_pressure_bar": 2,
        "upstream_friction_losses_m": 3,
        "upstream_local_losses_m": 1,
    }
    values.update(overrides)

    with pytest.raises(ValueError):
        calculate_required_pump_head(**values)


def test_required_pump_head_rejects_non_positive_total():
    with pytest.raises(ValueError, match="must be positive and finite"):
        calculate_required_pump_head(
            static_elevation_difference_m=-30,
            required_sector_inlet_pressure_bar=1,
        )



def test_sector_pump_requirement_combines_sector_flow_and_head():
    from irrigation.calculations.pump_head import (
        calculate_sector_pump_requirement,
    )

    sector = {
        "total_flow_lph": 720,
        "inlet_pressure_bar": 2,
    }
    result = calculate_sector_pump_requirement(
        sector_analysis=sector,
        static_elevation_difference_m=4,
        upstream_friction_losses_m=2,
        upstream_local_losses_m=1,
    )

    assert result["sector_total_flow_lph"] == pytest.approx(720)
    assert result["sector_total_flow_m3_s"] == pytest.approx(0.0002)
    assert result["total_dynamic_head_m"] == pytest.approx(
        4 + 2 * 10.197162129779 + 2 + 1,
        rel=1e-5,
    )


@pytest.mark.parametrize(
    "sector",
    [
        None,
        {},
        {"total_flow_lph": 0, "inlet_pressure_bar": 2},
        {"total_flow_lph": float("inf"), "inlet_pressure_bar": 2},
        {"total_flow_lph": 100, "inlet_pressure_bar": 0},
    ],
)
def test_sector_pump_requirement_rejects_invalid_sector_analysis(sector):
    from irrigation.calculations.pump_head import (
        calculate_sector_pump_requirement,
    )

    with pytest.raises(ValueError):
        calculate_sector_pump_requirement(
            sector_analysis=sector,
            static_elevation_difference_m=2,
        )


@pytest.mark.parametrize(
    "overrides",
    [
        {"static_elevation_difference_m": 10**400},
        {"required_sector_inlet_pressure_bar": 10**400},
        {"upstream_friction_losses_m": 10**400},
        {"upstream_local_losses_m": 10**400},
    ],
)
def test_required_pump_head_rejects_unrepresentable_integer_inputs(overrides):
    values = {
        "static_elevation_difference_m": 5,
        "required_sector_inlet_pressure_bar": 2,
        "upstream_friction_losses_m": 1,
        "upstream_local_losses_m": 1,
    }
    values.update(overrides)
    with pytest.raises(ValueError):
        calculate_required_pump_head(**values)


def test_required_pump_head_accepts_zero_upstream_losses():
    result = calculate_required_pump_head(
        static_elevation_difference_m=3,
        required_sector_inlet_pressure_bar=1.5,
    )
    assert result["upstream_friction_losses_m"] == 0.0
    assert result["upstream_local_losses_m"] == 0.0
    assert result["total_dynamic_head_m"] == pytest.approx(
        3 + result["pressure_head_m"]
    )


@pytest.mark.parametrize(
    "sector",
    [
        {"total_flow_lph": -1, "inlet_pressure_bar": 2},
        {"total_flow_lph": True, "inlet_pressure_bar": 2},
        {"total_flow_lph": float("nan"), "inlet_pressure_bar": 2},
        {"total_flow_lph": 100, "inlet_pressure_bar": float("nan")},
        {"total_flow_lph": 100, "inlet_pressure_bar": True},
        {"total_flow_lph": 100},
    ],
)
def test_sector_pump_requirement_rejects_invalid_flow_or_pressure(sector):
    with pytest.raises(ValueError):
        calculate_sector_pump_requirement(
            sector_analysis=sector,
            static_elevation_difference_m=2,
        )


def test_required_pump_head_rejects_overflowing_total():
    with pytest.raises(ValueError, match="positive and finite"):
        calculate_required_pump_head(
            static_elevation_difference_m=1e308,
            required_sector_inlet_pressure_bar=1,
            upstream_friction_losses_m=1e308,
        )

