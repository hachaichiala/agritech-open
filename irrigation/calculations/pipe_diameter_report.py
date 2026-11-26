"""Structured JSON-ready and Markdown reporting for pipe diameter decisions."""

import json


def _number(value, digits=3):
    if value is None:
        return "غير متاح"
    return f"{value:,.{digits}f}"


def build_pipe_diameter_report(decision_result):
    """Build a concise report from analyze_pipe_diameter_decision output.

    The returned data is JSON-serializable. The Markdown version is intended
    for readable technical summaries and preserves units in every value.
    """
    if not isinstance(decision_result, dict):
        raise ValueError("Decision result must be a dictionary.")

    recommendation = decision_result.get("recommendation")
    comparison = decision_result.get("hydraulic_and_economic_comparison")
    lifecycle = decision_result.get("life_cycle_analysis")
    if not isinstance(recommendation, dict):
        raise ValueError("Decision recommendation is required.")
    if not isinstance(comparison, dict) or not isinstance(comparison.get("scenarios"), list):
        raise ValueError("Hydraulic and economic scenarios are required.")
    if not isinstance(lifecycle, dict) or not isinstance(lifecycle.get("scenarios"), list):
        raise ValueError("Life-cycle analysis is required.")

    lifecycle_by_diameter = {
        item.get("pipe_diameter_m"): item
        for item in lifecycle["scenarios"]
        if isinstance(item, dict)
    }

    alternatives = []
    for scenario in comparison["scenarios"]:
        if not isinstance(scenario, dict):
            raise ValueError("Each comparison scenario must be a dictionary.")
        diameter = scenario.get("pipe_diameter_m")
        item = {
            "pipe_diameter_m": diameter,
            "hydraulic_status": scenario.get("status"),
            "economic_status": scenario.get("economic_status"),
        }
        analysis = scenario.get("analysis")
        if isinstance(analysis, dict):
            pump = analysis.get("pump_analysis", {})
            point = pump.get("operating_point", {})
            power = pump.get("power", {})
            item["operating_point"] = {
                "flow_m3_s": point.get("flow_m3_s"),
                "flow_l_s": (
                    point.get("flow_m3_s") * 1000
                    if point.get("flow_m3_s") is not None else None
                ),
                "head_m": point.get("head_m"),
            }
            item["power"] = {
                "hydraulic_power_w": power.get("hydraulic_power_w"),
                "shaft_power_w": power.get("shaft_power_w"),
                "electrical_input_power_w": power.get("electrical_input_power_w"),
                "pump_efficiency_percent": power.get("pump_efficiency_percent"),
                "motor_efficiency_percent": power.get("motor_efficiency_percent"),
            }
            motor_check = pump.get("motor_power_check")
            if motor_check is not None:
                item["motor_power_check"] = dict(motor_check)
        economics = scenario.get("economics")
        if isinstance(economics, dict):
            item["economics"] = {
                "pipe_purchase_cost_tnd": economics.get("pipe_purchase_cost_tnd"),
                "energy_cost_over_period_tnd": economics.get("energy_cost_over_period_tnd"),
                "total_cost_over_period_tnd": economics.get("total_cost_over_period_tnd"),
            }
        life = lifecycle_by_diameter.get(diameter)
        if isinstance(life, dict) and life.get("status") == "calculated":
            costs = life.get("costs", {})
            item["life_cycle_cost"] = {
                "net_present_life_cycle_cost_tnd": costs.get(
                    "net_present_life_cycle_cost_tnd"
                ),
                "undiscounted_life_cycle_cost_tnd": costs.get(
                    "undiscounted_life_cycle_cost_tnd"
                ),
            }
        else:
            item["life_cycle_cost"] = None
        if scenario.get("error"):
            item["error"] = scenario["error"]
        alternatives.append(item)

    payback = decision_result.get("payback_analysis") or {}
    sensitivity = decision_result.get("sensitivity_analysis")
    report = {
        "title": "Pipe Diameter Technical Decision Report",
        "recommendation": dict(recommendation),
        "alternatives": alternatives,
        "payback_comparisons": list(payback.get("comparisons", [])),
        "sensitivity": None if sensitivity is None else {
            "case_count": sensitivity.get("case_count"),
            "successful_case_count": sensitivity.get("successful_case_count"),
            "recommendation_counts": dict(sensitivity.get("recommendation_counts", {})),
            "recommendation_is_stable": sensitivity.get("recommendation_is_stable"),
            "stable_recommended_diameter_m": sensitivity.get(
                "stable_recommended_diameter_m"
            ),
        },
        "decision_notes": list(decision_result.get("decision_notes", [])),
        "missing_or_unverified_inputs": list(
            decision_result.get("missing_or_unverified_inputs", [])
        ),
        "method": decision_result.get("method"),
    }

    lines = [
        "# تقرير فني لاختيار قطر أنبوب التغذية",
        "",
        "## التوصية",
        f"- الحالة: {report['recommendation'].get('status', 'غير محدد')}",
        f"- القطر المقترح: {_number(report['recommendation'].get('pipe_diameter_m'))} م",
        f"- صافي القيمة الحالية: {_number(report['recommendation'].get('net_present_life_cycle_cost_tnd'), 2)} دينار",
        "",
        "## مقارنة البدائل",
        "| القطر (م) | الحالة الهيدروليكية | التدفق (ل/ث) | HMT (م) | قدرة العمود (كW) | شراء الأنبوب (د.ت) | الطاقة (د.ت) | NPV (د.ت) |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in alternatives:
        point = item.get("operating_point") or {}
        power = item.get("power") or {}
        economics = item.get("economics") or {}
        life = item.get("life_cycle_cost") or {}
        shaft_kw = power.get("shaft_power_w")
        lines.append(
            "| "
            + " | ".join([
                _number(item.get("pipe_diameter_m")),
                str(item.get("hydraulic_status") or "غير محدد"),
                _number(point.get("flow_l_s")),
                _number(point.get("head_m")),
                _number(shaft_kw / 1000 if shaft_kw is not None else None),
                _number(economics.get("pipe_purchase_cost_tnd"), 2),
                _number(economics.get("energy_cost_over_period_tnd"), 2),
                _number(life.get("net_present_life_cycle_cost_tnd"), 2),
            ])
            + " |"
        )

    lines.extend(["", "## فترة الاسترداد"])
    if report["payback_comparisons"]:
        lines.extend([
            "| القطر الأصغر (م) | القطر الأكبر (م) | فرق الشراء (د.ت) | الوفر السنوي (د.ت) | الاسترداد (سنة) | الحالة |",
            "|---:|---:|---:|---:|---:|---|",
        ])
        for item in report["payback_comparisons"]:
            lines.append(
                "| "
                + " | ".join([
                    _number(item.get("smaller_diameter_m")),
                    _number(item.get("larger_diameter_m")),
                    _number(item.get("extra_pipe_purchase_cost_tnd"), 2),
                    _number(item.get("annual_electricity_cost_savings_tnd"), 2),
                    _number(item.get("payback_period_years"), 2),
                    str(item.get("status")),
                ])
                + " |"
            )
    else:
        lines.append("لا تتوفر بدائل ناجحة كافية لحساب فترة الاسترداد.")

    lines.extend(["", "## تحليل الحساسية"])
    if report["sensitivity"] is None:
        lines.append("لم يُطلب تحليل الحساسية.")
    else:
        lines.append(
            f"- عدد الحالات: {report['sensitivity']['case_count']}"
        )
        lines.append(
            f"- ثبات التوصية: {report['sensitivity']['recommendation_is_stable']}"
        )
        lines.append(
            f"- القطر الثابت الموصى به: "
            f"{_number(report['sensitivity']['stable_recommended_diameter_m'])} م"
        )

    lines.extend(["", "## الافتراضات والقيود"])
    lines.extend(f"- {note}" for note in report["decision_notes"])
    if report["missing_or_unverified_inputs"]:
        lines.extend(["", "## بيانات تحتاج إلى تحقق"])
        lines.extend(
            f"- {entry}" for entry in report["missing_or_unverified_inputs"]
        )

    report["markdown"] = "\n".join(lines)
    report["json"] = json.dumps(
        {key: value for key, value in report.items() if key not in {"markdown", "json"}},
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )
    return report
