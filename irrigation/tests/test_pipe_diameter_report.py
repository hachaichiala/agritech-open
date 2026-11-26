import json

import pytest

from irrigation.calculations.pipe_diameter_report import build_pipe_diameter_report


def _decision():
    return {
        "recommendation": {
            "pipe_diameter_m": 0.063,
            "net_present_life_cycle_cost_tnd": 900.0,
            "basis": "lowest_net_present_life_cycle_cost",
            "status": "recommended",
        },
        "hydraulic_and_economic_comparison": {
            "scenarios": [
                {
                    "pipe_diameter_m": 0.05,
                    "status": "success",
                    "economic_status": "calculated",
                    "analysis": {
                        "pump_analysis": {
                            "operating_point": {"flow_m3_s": 0.0005, "head_m": 25},
                            "power": {
                                "hydraulic_power_w": 122.58,
                                "shaft_power_w": 245.16,
                                "electrical_input_power_w": 272.4,
                                "pump_efficiency_percent": 50,
                                "motor_efficiency_percent": 90,
                            },
                        }
                    },
                    "economics": {
                        "pipe_purchase_cost_tnd": 300,
                        "energy_cost_over_period_tnd": 500,
                        "total_cost_over_period_tnd": 800,
                    },
                },
                {
                    "pipe_diameter_m": 0.063,
                    "status": "success",
                    "economic_status": "calculated",
                    "analysis": {
                        "pump_analysis": {
                            "operating_point": {"flow_m3_s": 0.0006, "head_m": 24},
                            "power": {
                                "hydraulic_power_w": 141.2,
                                "shaft_power_w": 235.3,
                                "electrical_input_power_w": 261.4,
                                "pump_efficiency_percent": 60,
                                "motor_efficiency_percent": 90,
                            },
                        }
                    },
                    "economics": {
                        "pipe_purchase_cost_tnd": 450,
                        "energy_cost_over_period_tnd": 400,
                        "total_cost_over_period_tnd": 850,
                    },
                },
            ]
        },
        "life_cycle_analysis": {
            "scenarios": [
                {"pipe_diameter_m": 0.05, "status": "calculated", "costs": {"net_present_life_cycle_cost_tnd": 950}},
                {"pipe_diameter_m": 0.063, "status": "calculated", "costs": {"net_present_life_cycle_cost_tnd": 900}},
            ]
        },
        "payback_analysis": {
            "comparisons": [
                {
                    "smaller_diameter_m": 0.05,
                    "larger_diameter_m": 0.063,
                    "extra_pipe_purchase_cost_tnd": 150,
                    "annual_electricity_cost_savings_tnd": 20,
                    "payback_period_years": 7.5,
                    "status": "payback_available",
                }
            ]
        },
        "sensitivity_analysis": None,
        "decision_notes": ["توصية تجريبية."],
        "missing_or_unverified_inputs": ["بيانات المضخة تحتاج إلى تحقق."],
        "method": "test",
    }


def test_builds_structured_report_with_all_diameters():
    report = build_pipe_diameter_report(_decision())
    assert len(report["alternatives"]) == 2
    assert report["alternatives"][1]["operating_point"]["flow_l_s"] == pytest.approx(0.6)
    assert report["alternatives"][1]["life_cycle_cost"]["net_present_life_cycle_cost_tnd"] == 900


def test_builds_arabic_markdown_table_and_recommendation():
    report = build_pipe_diameter_report(_decision())
    assert "تقرير فني لاختيار قطر أنبوب التغذية" in report["markdown"]
    assert "0.063" in report["markdown"]
    assert "فترة الاسترداد" in report["markdown"]


def test_exports_valid_json_without_markdown_field():
    report = build_pipe_diameter_report(_decision())
    parsed = json.loads(report["json"])
    assert parsed["recommendation"]["pipe_diameter_m"] == 0.063
    assert "markdown" not in parsed


def test_reports_optional_sensitivity_summary():
    data = _decision()
    data["sensitivity_analysis"] = {
        "case_count": 3,
        "successful_case_count": 3,
        "recommendation_counts": {0.063: 3},
        "recommendation_is_stable": True,
        "stable_recommended_diameter_m": 0.063,
    }
    report = build_pipe_diameter_report(data)
    assert report["sensitivity"]["case_count"] == 3
    assert "تحليل الحساسية" in report["markdown"]


def test_rejects_missing_decision_sections():
    with pytest.raises(ValueError, match="recommendation"):
        build_pipe_diameter_report({})
