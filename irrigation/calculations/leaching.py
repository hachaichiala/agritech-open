"""
Leaching requirement estimates for high-frequency drip irrigation.

The FAO high-frequency drip screening equation is LR = ECw / (2 * ECe_max).
It requires crop-specific salinity tolerance and adequate drainage.
"""

import math


def _finite(value, label, minimum=0.0, inclusive=True):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number.")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"{label} must be a finite number.") from None
    if not math.isfinite(number):
        raise ValueError(f"{label} must be a finite number.")
    if minimum is not None:
        invalid = number < minimum if inclusive else number <= minimum
        if invalid:
            relation = "at least" if inclusive else "greater than"
            raise ValueError(f"{label} must be {relation} {minimum}.")
    return number


def calculate_drip_leaching_requirement(
    irrigation_water_ec_ds_m,
    crop_max_soil_ec_ds_m,
    net_irrigation_depth_mm,
    irrigated_area_m2,
    application_efficiency_percent,
    sector_flow_lph,
):
    """
    Estimate salinity leaching water and drip-sector runtime.

    EC values are in dS/m. crop_max_soil_ec_ds_m is the maximum tolerated
    ECe for the selected crop and acceptable yield. net_irrigation_depth_mm
    is the crop irrigation requirement after effective rainfall, before
    leaching and application-efficiency adjustments.
    """
    ecw = _finite(irrigation_water_ec_ds_m, "Irrigation-water EC")
    ece = _finite(
        crop_max_soil_ec_ds_m,
        "Crop maximum soil EC",
        minimum=0.0,
        inclusive=False,
    )
    net_depth = _finite(net_irrigation_depth_mm, "Net irrigation depth")
    area = _finite(
        irrigated_area_m2, "Irrigated area", minimum=0.0, inclusive=False
    )
    efficiency = _finite(
        application_efficiency_percent,
        "Application efficiency",
        minimum=0.0,
        inclusive=False,
    )
    if efficiency > 100:
        raise ValueError("Application efficiency must not exceed 100 percent.")
    flow = _finite(
        sector_flow_lph, "Sector flow", minimum=0.0, inclusive=False
    )

    leaching_fraction = ecw / (2.0 * ece)
    if leaching_fraction >= 1.0:
        raise ValueError(
            "The estimated leaching fraction is at least 1. "
            "The selected water quality and crop tolerance require a different assessment."
        )

    net_depth_with_leaching = net_depth / (1.0 - leaching_fraction)
    gross_depth = net_depth_with_leaching / (efficiency / 100.0)
    net_volume_l = net_depth_with_leaching * area
    gross_volume_l = gross_depth * area
    runtime_hours = gross_volume_l / flow

    return {
        "method": "FAO_high_frequency_drip_leaching_requirement",
        "water_quality": {
            "irrigation_water_ec_ds_m": ecw,
            "crop_max_soil_ec_ds_m": ece,
        },
        "leaching": {
            "required_leaching_fraction": leaching_fraction,
            "required_leaching_percent": leaching_fraction * 100.0,
            "net_crop_irrigation_depth_mm": net_depth,
            "net_depth_including_leaching_mm": net_depth_with_leaching,
            "additional_net_leaching_depth_mm": (
                net_depth_with_leaching - net_depth
            ),
        },
        "application": {
            "irrigated_area_m2": area,
            "application_efficiency_percent": efficiency,
            "gross_application_depth_mm": gross_depth,
            "net_application_volume_l": net_volume_l,
            "gross_application_volume_l": gross_volume_l,
            "sector_flow_lph": flow,
            "estimated_runtime_hours": runtime_hours,
            "estimated_runtime_minutes": runtime_hours * 60.0,
        },
        "limitations": [
            "Uses the FAO screening equation for high-frequency drip irrigation: LR = ECw / (2 × maximum tolerated ECe).",
            "The crop ECe threshold must match the crop, growth stage, and acceptable yield target.",
            "Assumes adequate drainage and a long-term salinity balance. Leaching without drainage can worsen waterlogging and salinity.",
            "Does not model soil texture, wetted fraction, rainfall salt balance, groundwater contribution, or spatial salt distribution.",
            "Use laboratory water and soil analyses and local drainage assessment before applying a leaching program.",
        ],
    }
