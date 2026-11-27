"""
Daily crop-water requirement calculations from reference evapotranspiration.

ET0 is supplied by the caller. This module does not estimate climate data or
calculate ET0 from weather observations.
"""

import math


def _finite_number(value, label, minimum=None, maximum=None, minimum_inclusive=True):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number.")
    if minimum is not None:
        invalid = value < minimum if minimum_inclusive else value <= minimum
        if invalid:
            relation = "at least" if minimum_inclusive else "greater than"
            raise ValueError(f"{label} must be {relation} {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must not exceed {maximum}.")
    return value


def calculate_crop_water_requirements(
    crops,
    et0_mm_day,
    application_efficiency_percent=90.0,
):
    """
    Calculate daily net and gross irrigation volumes for a group of crops.

    Each crop is a dictionary containing a unique non-empty name, crop
    coefficient kc, and planted area area_m2.

    Since 1 mm over 1 m² equals 1 litre:
        net_l_day = et0_mm_day * kc * area_m2
        gross_l_day = net_l_day / (application_efficiency_percent / 100)

    ET0 must represent the selected site's daily reference
    evapotranspiration. Kc must match the crop and its current growth stage.
    Rainfall, leaching, soil-water storage, and salinity adjustments are
    outside this calculation.
    """
    et0 = _finite_number(et0_mm_day, "ET0", minimum=0.0)
    efficiency = _finite_number(
        application_efficiency_percent,
        "Application efficiency",
        minimum=0.0,
        maximum=100.0,
        minimum_inclusive=False,
    )
    if not isinstance(crops, (list, tuple)) or not crops:
        raise ValueError("Crops must be a non-empty list or tuple.")

    names = set()
    crop_results = []
    total_area_m2 = 0.0
    total_net_l_day = 0.0
    total_gross_l_day = 0.0

    for index, crop in enumerate(crops, start=1):
        if not isinstance(crop, dict):
            raise ValueError(f"Crop {index} must be a dictionary.")
        name = crop.get("name")
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f"Crop {index} must have a non-empty name.")
        if name in names:
            raise ValueError(f"Duplicate crop name: {name}.")
        names.add(name)

        kc = _finite_number(crop.get("kc"), f"Kc for crop '{name}'", minimum=0.0)
        area = _finite_number(
            crop.get("area_m2"),
            f"Area for crop '{name}'",
            minimum=0.0,
            minimum_inclusive=False,
        )
        net = et0 * kc * area
        gross = net / (efficiency / 100.0)
        crop_results.append({
            "name": name,
            "kc": kc,
            "area_m2": area,
            "net_water_l_day": net,
            "gross_irrigation_l_day": gross,
            "gross_irrigation_m3_day": gross / 1000.0,
        })
        total_area_m2 += area
        total_net_l_day += net
        total_gross_l_day += gross

    return {
        "method": "ET0_times_Kc_times_area_adjusted_for_application_efficiency",
        "et0_mm_day": et0,
        "application_efficiency_percent": efficiency,
        "crops": crop_results,
        "summary": {
            "total_area_m2": total_area_m2,
            "net_crop_water_requirement_l_day": total_net_l_day,
            "gross_irrigation_requirement_l_day": total_gross_l_day,
            "gross_irrigation_requirement_m3_day": total_gross_l_day / 1000.0,
        },
        "limitations": [
            "ET0 is supplied by the user and is not calculated from weather data.",
            "Kc must represent the crop, growth stage, and local growing conditions.",
            "Rainfall, leaching, salinity, and changes in soil-water storage are not included.",
            "Application efficiency is a user-supplied estimate and should reflect the installed irrigation system.",
        ],
    }
