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
- Integrated sector-to-pump design workflow, with sequential analysis of multiple independent irrigation sectors.
- Daily crop-water requirement calculation from user-supplied ET₀, crop coefficient (Kc), planted area, and application efficiency.
- Daily sequential irrigation scheduling from user-supplied water volumes, with runtime and available-hours checks.
- JSON command-line interface.

## Run a design

From the repository root:

```bash
python -m irrigation design examples/drip_irrigation_design.json --output report.json
```

See [QUICKSTART_AR.md](../QUICKSTART_AR.md) for input structure, units, examples, and model limitations.

Daily crop-water volumes can be estimated with `calculate_crop_water_requirements`. Supply ET₀ in mm/day, a crop name, Kc for its current growth stage, planted area in m², and application efficiency as a percentage. The result reports net crop water use and gross irrigation volume in litres/day and m³/day. Pass each sector gross daily volume to `schedule_irrigation_sectors`. ET₀ is not fetched or calculated by this function.

Daily operation times can be calculated with `schedule_irrigation_sectors`, using the multi-sector design result, a daily water volume for each sector in litres, and available pump runtime in hours per day. The function reports each sector runtime and whether the total fits the daily time window. Water demand must be supplied by the user. Crop evapotranspiration and application efficiency are not estimated.

Multiple sectors can be analyzed through `design_irrigation_sectors`. Each sector receives an independent pump/system analysis using the shared upstream and pump data. Simultaneous operation of several sectors and shared-header hydraulics are not modeled by this function.

## Engineering limitations

Results depend on accurate site dimensions, internal pipe diameters, emitter specifications, and manufacturer pump curves. The current integrated sector model uses documented geometric assumptions. Include filters, valves, meters, suction losses, elevation changes, and other components where relevant. Review all model assumptions before field implementation.

## Development status

The package is under active development. Existing functions and their assumptions are documented in the calculation modules and [HYDRAULIC_METHODS.md](../HYDRAULIC_METHODS.md).
