# Irrigation Module

## Purpose

The irrigation package provides engineering calculations and an integrated workflow for drip-irrigation sector and pump analysis.

## Implemented capabilities

- Flow and emitter discharge calculations.
- Hazen-Williams pipe and dripline head-loss calculations.
- Emitter pressure analysis, including pressure-compensating and non-compensating emitters.
- Manifold flow, segment losses, and lateral take-off pressure.
- Irrigation sector hydraulic analysis, including optional manifold takeoff and lateral emitter elevation profiles.
- Pipe internal diameter, velocity, pressure rating, and diameter comparison.
- Pipe lifecycle cost, economic sensitivity, and payback analysis.
- Pump curve validation and operating-point calculation.
- System curve, total dynamic head, pump power, and sector-pump compatibility.
- Integrated sector-to-pump design workflow.
- JSON command-line interface.

## Run a design

From the repository root:

```bash
python -m irrigation design examples/drip_irrigation_design.json --output report.json
```

See [QUICKSTART_AR.md](../QUICKSTART_AR.md) for input structure, units, examples, and model limitations.

## Engineering limitations

Results depend on accurate site dimensions, internal pipe diameters, emitter specifications, and manufacturer pump curves. The current integrated sector model uses documented geometric assumptions. Include filters, valves, meters, suction losses, elevation changes, and other components where relevant. Review all model assumptions before field implementation.

## Development status

The package is under active development. Existing functions and their assumptions are documented in the calculation modules and [HYDRAULIC_METHODS.md](../HYDRAULIC_METHODS.md).
