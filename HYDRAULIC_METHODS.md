# Hydraulic Methods and Model Scope

This document describes the equations and assumptions used by the current irrigation calculation engine. It is a description of the implemented model, not a substitute for manufacturer data, field measurements, or a site-specific engineering review.

## 1. Hazen-Williams pipe friction

The engine calculates friction head loss in a full, pressurized pipe with the SI form of the Hazen-Williams equation:

\[
h_f = 10.67\,L\,\frac{Q^{1.852}}{C^{1.852}D^{4.87}}
\]

Where:

- \(h_f\): friction head loss, metres of water.
- \(L\): pipe length, metres.
- \(Q\): flow rate, cubic metres per second.
- \(D\): actual internal pipe diameter, metres.
- \(C\): dimensionless Hazen-Williams coefficient.

The implementation uses the rounded constants and exponents 10.67, 1.852 and 4.871. The code currently uses 4.871 in the denominator. The coefficient \(C\) must reflect the pipe material, age, and design assumptions. A default value of 150 is not a universal material property and should be replaced when better pipe data is available.

Hazen-Williams is an empirical relationship for water in pressurized pipes. Do not treat it as a general-purpose equation for every fluid or flow regime. For conditions outside its intended range, assess a Darcy-Weisbach model.

## 2. Multiple-outlet drip laterals

The current lateral model divides the lateral into equal-length segments. It assumes:

- Emitters have equal spacing.
- The final emitter is located at the downstream end.
- Each emitter discharges the same nominal flow.
- The segment flow equals the sum of the nominal flows from that segment's emitter and all downstream emitters.
- Pipe internal diameter is constant.
- The detailed pressure-distribution functions accept an optional elevation for each emitter, measured relative to the lateral inlet. If no elevation profile is supplied, the lateral is treated as horizontal.

For each segment, the engine applies Hazen-Williams to the remaining downstream flow, then sums segment losses. Pressure at each emitter is calculated by accumulating the segment losses from the inlet.

This is a constant-discharge approximation. It is suitable for a first hydraulic estimate when emitter discharge is effectively constant, such as within the operating range of a pressure-compensating emitter. The current constant-discharge functions do not solve the pressure-discharge relationship. A separate `analyze_non_compensating_dripline` function provides an iterative model for non-pressure-compensating emitters using the manufacturer equation q = q_ref × (P/P_ref)^x. The caller must supply the reference discharge, reference pressure, and exponent from the selected emitter's technical data. The solver recalculates each segment flow from the current and downstream emitter discharges until the relative flow change meets the configured tolerance. It reports convergence, iteration count, individual emitter flows and pressures, total lateral flow, and a minimum-to-maximum flow ratio expressed as a percentage. The original constant-discharge API remains unchanged.

### 2.1 Emitter-connection local losses

The lateral model supports an optional local-loss coefficient, `emitter_connection_k`, for the connection at each emitter. It calculates each connection loss with:

\[
h_{m,i} = K_e\frac{V_i^2}{2g}
\]

The velocity \(V_i\) is based on the lateral flow immediately upstream of that connection. Under the current segment convention, each segment ends at one emitter, so the model applies one connection loss per segment. The flow for successive segments is based on the remaining downstream nominal emitter flow.

The default coefficient is zero to preserve the earlier friction-only result. Supply a measured or manufacturer-supported K value for the specific connector geometry. Do not treat one generic K value as valid for every emitter, barb, take-off, or inline emitter design. The current interface uses one shared K value for all emitter connections along a lateral.

The pressure-distribution function accepts an optional `emitter_elevations_m` sequence with one elevation per emitter, measured in metres relative to the lateral inlet. Positive values represent uphill locations and reduce local pressure. Negative values represent downhill locations and increase local pressure. When omitted, all elevations default to zero, preserving the horizontal-lateral result. Elevation changes affect pressure distribution, not friction head loss. The detailed pressure-analysis function reports friction and connection head loss separately from the resulting emitter pressures.

## 3. Local losses in upstream pipes

For upstream fittings and components represented by a combined loss coefficient, the engine uses:

\[
h_m = K\frac{V^2}{2g}
\]

Where:

- \(h_m\): local head loss, metres.
- \(K\): combined dimensionless local-loss coefficient.
- \(V\): mean velocity in the pipe, metres per second.
- \(g\): gravitational acceleration, 9.80665 metres per second squared.

The velocity is calculated from the pipe's actual internal cross-sectional area:

\[
V = \frac{Q}{A}, \qquad A = \frac{\pi D^2}{4}
\]

The system-curve implementation applies this K-factor loss to the single upstream pipe described by its inputs. The coefficient must represent the fittings and components included in that upstream section. Do not use this term to imply that emitter-connection losses inside the laterals are already included.

## 4. Pressure and pump head

The conversion between pressure and water head uses:

\[
H_p = 10.197162\,P
\]

Where \(P\) is pressure in bar and \(H_p\) is the equivalent water head in metres.

The current required pump head model sums:

\[
H_{TDH} = \Delta z + H_p + h_f + h_m
\]

Where:

- \(\Delta z\): elevation difference between the source water level and the sector inlet. A positive value means the sector inlet is higher.
- \(H_p\): required pressure head at the sector manifold inlet.
- \(h_f\): friction loss in upstream pipes.
- \(h_m\): local losses in upstream fittings and components.

The upstream losses must stop at the sector inlet. Do not add lateral or manifold losses again if their effect is already represented in the required sector inlet pressure.

This simplified pump-head calculation does not explicitly include a difference in velocity head between the source and delivery points, nor does it independently model suction-side losses or all pump-station components. Include these terms when they are material to the installation.

## 5. Pressure-compensating emitter checks

The emitter pressure analysis compares calculated pressure values with the configured minimum and maximum operating pressures. The current default range of 1 to 4 bar is provisional. Replace it with the exact operating range from the selected emitter manufacturer's technical sheet.

The endpoint check compares inlet and outlet pressures. The detailed distribution function checks the calculated pressure at each emitter. These checks indicate pressure-range compliance. They are not, by themselves, a complete calculation of application uniformity, manufacturing variation, clogging, or actual emitter discharge.

## 6. Validation still required for detailed design

Before using results for construction or field operation, confirm:

1. Actual internal pipe diameters, not nominal outside diameters.
2. Pipe material and justified Hazen-Williams C values.
3. Emitter model, nominal discharge, pressure-discharge curve, and compensation range.
4. Emitter spacing and actual position of the first and last emitters.
5. Local-loss data for emitter connectors and upstream fittings.
6. Ground elevations at the source, pump, manifold, and along laterals.
7. Filter, valve, meter, backflow, and other equipment losses.
8. Pump curve and operating point at the calculated flow and head.

## References

1. U.S. Army Corps of Engineers, *Liquid Process Piping*, EM 1110-1-4008. Discusses Hazen-Williams use and its empirical limits. https://www.publications.usace.army.mil/portals/76/publications/engineermanuals/em_1110-1-4008.pdf
2. University of Florida IFAS Extension, *Hydraulic Considerations for Citrus Microirrigation Systems*, CH156. Describes the multiple-outlet reduction factor for laterals with regularly spaced outlets. https://ask.ifas.ufl.edu/publication/CH156
3. Provenzano, G., Pumo, D., and Di Dio, P. (2005). “Simplified Procedure to Evaluate Head Losses in Drip Irrigation Laterals.” *Journal of Irrigation and Drainage Engineering*, 131(6), 525-532. https://doi.org/10.1061/(ASCE)0733-9437(2005)131:6(525)
4. Provenzano, G. and Pumo, D. (2006). “Experimental Analysis of Local Pressure Losses for Microirrigation Laterals.” *Journal of Irrigation and Drainage Engineering*. https://ascelibrary.org/doi/full/10.1061/(ASCE)0733-9437(2006)132:2(193)
5. Stern, F., University of Iowa, *Mechanics of Fluids and Transport Processes*, Chapter 8. Defines minor head loss as K times velocity head. https://stern.lab.uiowa.edu/sites/stern.lab.uiowa.edu/files/2025-02/Chapter8.pdf
6. USDA Natural Resources Conservation Service, *National Engineering Handbook*, Part 623, Chapter 7, Microirrigation. Covers emitter pressure-discharge relationships and microirrigation hydraulic design. https://directives.nrcs.usda.gov/sites/default/files2/1712930539/25340.pdf
