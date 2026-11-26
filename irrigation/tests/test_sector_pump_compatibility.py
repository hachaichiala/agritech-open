import pytest

from irrigation.calculations.sector_pump_compatibility import (
    analyze_sector_pump_compatibility,
)


PUMP = {
    "manufacturer": "Example",
    "model": "P-1",
    "pump_curve": [(0.0, 40.0), (0.001, 20.0)],
}
SECTOR = {
    "total_flow_lph": 1800.0,
    "inlet_pressure_bar": 2.0,
}


def test_sector_pump_compatibility_reports_sufficient_pump_head():
    result = analyze_sector_pump_compatibility(
        pump_data=PUMP,
        sector_analysis=SECTOR,
        static_elevation_difference_m=2.0,
        upstream_friction_losses_m=1.0,
        upstream_local_losses_m=0.5,
    )

    assert result["sector_total_flow_lph"] == pytest.approx(1800.0)
    assert result["sector_total_flow_m3_s"] == pytest.approx(0.0005)
    assert result["available_pump_head_m"] == pytest.approx(30.0)
    assert result["required_total_dynamic_head_m"] == pytest.approx(
        2.0 + 2.0 * 10.197162129779 + 1.0 + 0.5
    )
    assert result["head_margin_m"] > 0
    assert result["pump_meets_design_duty"] is True


def test_sector_pump_compatibility_reports_insufficient_head():
    result = analyze_sector_pump_compatibility(
        pump_data=PUMP,
        sector_analysis={
            "total_flow_lph": 1800.0,
            "inlet_pressure_bar": 3.0,
        },
        static_elevation_difference_m=5.0,
    )

    assert result["head_margin_m"] < 0
    assert result["pump_meets_design_duty"] is False


def test_sector_pump_compatibility_interpolates_at_design_flow():
    result = analyze_sector_pump_compatibility(
        pump_data=PUMP,
        sector_analysis=SECTOR,
        static_elevation_difference_m=0.0,
    )

    assert result["available_pump_head_m"] == pytest.approx(30.0)
    assert result["method"] == (
        "pump_head_interpolation_at_sector_design_flow"
    )


@pytest.mark.parametrize("flow_lph", [0.0, 4000.0])
def test_sector_pump_compatibility_rejects_flow_outside_pump_curve(
    flow_lph,
):
    with pytest.raises(ValueError, match="outside the supplied pump curve"):
        analyze_sector_pump_compatibility(
            pump_data=PUMP,
            sector_analysis={
                "total_flow_lph": flow_lph,
                "inlet_pressure_bar": 2.0,
            },
            static_elevation_difference_m=0.0,
        )


@pytest.mark.parametrize(
    "sector",
    [
        None,
        {},
        {"total_flow_lph": 1000.0},
        {"total_flow_lph": 1000.0, "inlet_pressure_bar": 0.0},
    ],
)
def test_sector_pump_compatibility_rejects_invalid_sector(sector):
    with pytest.raises(ValueError):
        analyze_sector_pump_compatibility(
            pump_data=PUMP,
            sector_analysis=sector,
            static_elevation_difference_m=0.0,
        )


def test_sector_pump_compatibility_rejects_invalid_pump_data():
    with pytest.raises(ValueError):
        analyze_sector_pump_compatibility(
            pump_data={"pump_curve": [(0.0, 20.0)]},
            sector_analysis=SECTOR,
            static_elevation_difference_m=0.0,
        )


def test_sector_pump_compatibility_reports_scope_of_check():
    result = analyze_sector_pump_compatibility(
        pump_data=PUMP,
        sector_analysis=SECTOR,
        static_elevation_difference_m=0.0,
    )

    assert "complete system curve" in result["warning"]
