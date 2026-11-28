"""
Soil-water storage and irrigation-trigger calculations.

The module uses the FAO-56 total available water and readily available
water concepts. Inputs are site- and crop-specific measurements or estimates.
"""

import math


def _positive_finite(value, label, allow_zero=False):
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or (value < 0 if allow_zero else value <= 0)
    ):
        qualifier = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{label} must be finite and {qualifier}.")
    return float(value)


def calculate_irrigation_trigger(
    field_capacity_vwc,
    wilting_point_vwc,
    root_depth_m,
    depletion_fraction,
    crop_et_mm_day,
    irrigated_area_m2,
    application_efficiency_percent,
    sector_flow_lph,
):
    """
    Estimate irrigation trigger interval and refill runtime from root-zone water.

    Volumetric soil-water contents are fractions (m3/m3), not percentages.
    Irrigation is triggered when RAW is depleted and refills that depletion.
    """
    fc = _positive_finite(field_capacity_vwc, "Field capacity", allow_zero=True)
    wp = _positive_finite(wilting_point_vwc, "Wilting point", allow_zero=True)
    if fc > 1 or wp > 1 or fc <= wp:
        raise ValueError(
            "Soil water contents must satisfy 0 <= wilting point < field capacity <= 1."
        )

    root_depth = _positive_finite(root_depth_m, "Root depth")
    p = _positive_finite(depletion_fraction, "Depletion fraction")
    if p > 1:
        raise ValueError("Depletion fraction must not exceed 1.")

    etc = _positive_finite(crop_et_mm_day, "Crop ET")
    area = _positive_finite(irrigated_area_m2, "Irrigated area")
    efficiency = _positive_finite(
        application_efficiency_percent, "Application efficiency"
    )
    if efficiency > 100:
        raise ValueError("Application efficiency must not exceed 100 percent.")
    flow = _positive_finite(sector_flow_lph, "Sector flow")

    taw_mm = 1000.0 * (fc - wp) * root_depth
    raw_mm = p * taw_mm
    interval_days = raw_mm / etc
    gross_depth_mm = raw_mm / (efficiency / 100.0)
    net_volume_l = raw_mm * area
    gross_volume_l = gross_depth_mm * area
    runtime_hours = gross_volume_l / flow

    return {
        "method": "FAO56_TAW_RAW_irrigation_trigger",
        "soil_water": {
            "field_capacity_vwc": fc,
            "wilting_point_vwc": wp,
            "available_water_capacity_m3_m3": fc - wp,
            "root_depth_m": root_depth,
            "total_available_water_mm": taw_mm,
            "depletion_fraction": p,
            "readily_available_water_mm": raw_mm,
        },
        "irrigation": {
            "crop_et_mm_day": etc,
            "estimated_interval_days": interval_days,
            "net_refill_depth_mm": raw_mm,
            "gross_application_depth_mm": gross_depth_mm,
            "irrigated_area_m2": area,
            "net_refill_volume_l": net_volume_l,
            "gross_application_volume_l": gross_volume_l,
            "application_efficiency_percent": efficiency,
            "sector_flow_lph": flow,
            "estimated_runtime_hours": runtime_hours,
            "estimated_runtime_minutes": runtime_hours * 60.0,
        },
        "limitations": [
            "The estimate assumes irrigation starts at RAW depletion and refills the root-zone depletion to field capacity.",
            "Soil-water contents, effective root depth, depletion fraction, and crop ET must represent the crop and site.",
            "The calculation assumes uniform soil and root distribution across the entered irrigated area.",
            "The wetted fraction of drip irrigation, rainfall, runoff, capillary rise, salinity leaching, and deep percolation are not modeled.",
            "The interval is a planning estimate. Check soil moisture and adjust for field conditions.",
        ],
    }
