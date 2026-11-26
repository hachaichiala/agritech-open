Hydraulic Calculations


This directory contains the engineering calculation modules for drip irrigation network design.


Planned calculation modules




Flow rate calculations


Water velocity in pipes


Pipe diameter selection


Hazen-Williams head loss


Pressure requirements


Total Dynamic Head (TDH)


Irrigation sector flow calculations




Engineering standards


Each calculation module must include:




Mathematical equations and units.


Input validation.


Documented assumptions.


Reference examples.


Automated tests.




Status


Planned. No calculation code has been implemented yet.

## Dripline Hydraulic Calculations

The `dripline.py` module estimates friction head loss
along a drip irrigation lateral.

Current assumptions:

- Emitters are uniformly spaced.
- Emitter discharge is constant.
- Pipe diameter is constant.
- Flow decreases after each emitter.
- The pipe is horizontal.
- Minor losses and elevation changes are excluded.

The calculation uses the Hazen-Williams equation
for each pipe segment.

The current model is an initial approximation.
Further hydraulic validation is required before
using the results for field installation.


## Pressure-Compensating Emitters

The `emitter_pressure.py` module provides tools
for checking pressure conditions in drip irrigation laterals
using pressure-compensating (PC) emitters.

Current features:

- Configurable minimum and maximum operating pressure.
- Inlet and outlet pressure validation.
- Dripline head loss integration.
- Automatic PC pressure range verification.

Example assumptions:

- Inlet pressure: 2 bar.
- Temporary PC pressure range: 1 to 4 bar.
- Horizontal dripline.
- Uniform emitter spacing.

Important:

The default pressure range is temporary.
Replace these values with the manufacturer's specifications
before using the model for field design.

The current model does not yet calculate pressure
at every individual emitter.

