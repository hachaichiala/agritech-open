import math

import pytest

from irrigation.calculations import calculate_dripline_flushing_requirement


def test_calculates_per_lateral_and_network_flushing_requirements():
    area = math.pi * 0.016 ** 2 / 4.0
    expected_flow_lph = 0.3 * area * 3_600_000.0
    expected_pipe_volume_l = area * 50.0 * 1000.0
    expected_runtime_minutes = (2.0 * 50.0 / 0.3) / 60.0

    result = calculate_dripline_flushing_requirement(
        internal_diameter_m=0.016,
        lateral_length_m=50.0,
        flushing_velocity_m_s=0.3,
        number_of_laterals=10,
        pipe_volume_exchanges=2.0,
        available_flow_lph=expected_flow_lph * 3.0,
    )

    assert result["per_lateral"]["flushing_flow_lph"] == pytest.approx(
        expected_flow_lph
    )
    assert result["per_lateral"]["internal_pipe_volume_l"] == pytest.approx(
        expected_pipe_volume_l
    )
    assert result["per_lateral"]["flushing_water_volume_l"] == pytest.approx(
        expected_pipe_volume_l * 2.0
    )
    assert result["per_lateral"]["estimated_runtime_minutes"] == pytest.approx(
        expected_runtime_minutes
    )
    assert result["all_laterals"]["total_flushing_water_volume_l"] == pytest.approx(
        expected_pipe_volume_l * 2.0 * 10
    )
    assert result["all_laterals"]["simultaneous_required_flow_lph"] == pytest.approx(
        expected_flow_lph * 10
    )
    assert result["all_laterals"]["sequential_runtime_minutes"] == pytest.approx(
        expected_runtime_minutes * 10
    )
    capacity = result["source_capacity_assessment"]
    assert capacity["maximum_simultaneous_laterals"] == 3
    assert capacity["number_of_batches"] == 4
    assert capacity["status"] == "multiple_batches"
    assert capacity["estimated_runtime_minutes_at_available_flow"] == pytest.approx(
        expected_runtime_minutes * 4
    )
