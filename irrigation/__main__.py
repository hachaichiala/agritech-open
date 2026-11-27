"""Command-line entry point for AgriTech Open irrigation workflows."""

import argparse
import json
import sys
from pathlib import Path

from .calculations import EmitterPressureRange, design_drip_irrigation_system


def _load_payload(source):
    if source == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(source).read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must contain an object.")
    return payload


def _run_design(payload):
    required = {
        "sector_parameters",
        "pressure_range",
        "upstream_system_parameters",
        "pump_data",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(
            "Missing required input sections: " + ", ".join(missing)
        )

    pressure_data = payload["pressure_range"]
    if not isinstance(pressure_data, dict):
        raise ValueError("pressure_range must be a JSON object.")
    unknown_pressure_fields = set(pressure_data) - {
        "minimum_bar",
        "maximum_bar",
    }
    if unknown_pressure_fields:
        raise ValueError(
            "Unknown pressure_range fields: "
            + ", ".join(sorted(unknown_pressure_fields))
        )

    pressure_range = EmitterPressureRange(**pressure_data)
    return design_drip_irrigation_system(
        sector_parameters=payload["sector_parameters"],
        pressure_range=pressure_range,
        upstream_system_parameters=payload["upstream_system_parameters"],
        pump_data=payload["pump_data"],
        pump_efficiency_percent=payload.get("pump_efficiency_percent"),
        motor_efficiency_percent=payload.get("motor_efficiency_percent"),
        flow_match_tolerance_percent=payload.get(
            "flow_match_tolerance_percent", 5.0
        ),
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python -m irrigation",
        description="Run an integrated drip-irrigation sector and pump analysis.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    design_parser = subparsers.add_parser(
        "design",
        help="Analyze a sector, system curve, pump operating point, and power.",
    )
    design_parser.add_argument(
        "input",
        help="Path to a JSON input file, or '-' to read JSON from standard input.",
    )
    design_parser.add_argument(
        "--output",
        help="Write the JSON report to this path. Standard output is used by default.",
    )

    args = parser.parse_args(argv)

    try:
        payload = _load_payload(args.input)
        result = _run_design(payload)
        rendered = json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            sys.stdout.write(rendered + "\n")
        return 0
    except (OSError, TypeError, ValueError) as exc:
        sys.stderr.write(f"irrigation: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
