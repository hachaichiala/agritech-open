"""
Daily FAO-56 Penman-Monteith reference evapotranspiration (ET0).

Weather observations are supplied by the caller. This module does not fetch
weather data or infer missing observations.
"""

import math


def _number(value, label, minimum=None, maximum=None):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be a finite number.")
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"{label} must be a finite number.")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}.")
    if maximum is not None and value > maximum:
        raise ValueError(f"{label} must not exceed {maximum}.")
    return value


def _saturation_vapour_pressure(temp_c):
    return 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))


def calculate_fao56_et0(
    tmin_c,
    tmax_c,
    wind_speed_2m_m_s,
    solar_radiation_mj_m2_day,
    elevation_m,
    latitude_degrees,
    day_of_year,
    actual_vapour_pressure_kpa=None,
    relative_humidity_min_percent=None,
    relative_humidity_max_percent=None,
):
    """
    Calculate daily reference ET0 in mm/day using FAO-56 Penman-Monteith.

    Supply actual vapour pressure directly, or supply both daily minimum
    and maximum relative humidity. Solar radiation is measured daily
    incoming shortwave radiation in MJ/m²/day. Wind speed must be measured
    or adjusted to 2 m height.

    Latitude is positive north and negative south. Day of year is 1..366.
    Daily soil heat flux is assumed to be zero.
    """
    tmin = _number(tmin_c, "Minimum temperature")
    tmax = _number(tmax_c, "Maximum temperature")
    if tmax < tmin:
        raise ValueError("Maximum temperature must not be below minimum temperature.")

    wind = _number(wind_speed_2m_m_s, "Wind speed at 2 m", minimum=0.0)
    rs = _number(solar_radiation_mj_m2_day, "Solar radiation", minimum=0.0)
    elevation = _number(elevation_m, "Elevation", minimum=-500.0, maximum=9000.0)
    latitude = _number(latitude_degrees, "Latitude", minimum=-90.0, maximum=90.0)
    if not isinstance(day_of_year, int) or isinstance(day_of_year, bool) or not 1 <= day_of_year <= 366:
        raise ValueError("Day of year must be an integer from 1 to 366.")

    if actual_vapour_pressure_kpa is not None:
        ea = _number(actual_vapour_pressure_kpa, "Actual vapour pressure", minimum=0.0)
        if relative_humidity_min_percent is not None or relative_humidity_max_percent is not None:
            raise ValueError("Supply actual vapour pressure or relative humidity, not both.")
    else:
        if relative_humidity_min_percent is None or relative_humidity_max_percent is None:
            raise ValueError("Supply actual vapour pressure or both minimum and maximum relative humidity.")
        rh_min = _number(relative_humidity_min_percent, "Minimum relative humidity", minimum=0.0, maximum=100.0)
        rh_max = _number(relative_humidity_max_percent, "Maximum relative humidity", minimum=0.0, maximum=100.0)
        if rh_min > rh_max:
            raise ValueError("Minimum relative humidity must not exceed maximum relative humidity.")
        ea = (
            _saturation_vapour_pressure(tmin) * rh_max / 100.0
            + _saturation_vapour_pressure(tmax) * rh_min / 100.0
        ) / 2.0

    es_tmin = _saturation_vapour_pressure(tmin)
    es_tmax = _saturation_vapour_pressure(tmax)
    es = (es_tmin + es_tmax) / 2.0
    if ea > es:
        raise ValueError("Actual vapour pressure must not exceed mean saturation vapour pressure.")

    tmean = (tmax + tmin) / 2.0
    delta = 4098.0 * _saturation_vapour_pressure(tmean) / ((tmean + 237.3) ** 2)
    pressure = 101.3 * (((293.0 - 0.0065 * elevation) / 293.0) ** 5.26)
    gamma = 0.000665 * pressure

    phi = math.radians(latitude)
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)
    solar_declination = 0.409 * math.sin(2.0 * math.pi * day_of_year / 365.0 - 1.39)
    sunset_argument = -math.tan(phi) * math.tan(solar_declination)
    sunset_angle = math.acos(max(-1.0, min(1.0, sunset_argument)))
    ra = (
        (24.0 * 60.0 / math.pi)
        * 0.0820
        * dr
        * (
            sunset_angle * math.sin(phi) * math.sin(solar_declination)
            + math.cos(phi) * math.cos(solar_declination) * math.sin(sunset_angle)
        )
    )
    rso = (0.75 + 2e-5 * elevation) * ra
    if rso <= 0:
        raise ValueError("Calculated clear-sky radiation must be positive for this day and latitude.")

    net_shortwave = 0.77 * rs
    cloudiness = max(0.0, min(rs / rso, 1.0))
    net_longwave = (
        4.903e-9
        * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2.0)
        * (0.34 - 0.14 * math.sqrt(ea))
        * (1.35 * cloudiness - 0.35)
    )
    net_radiation = net_shortwave - net_longwave

    eto = (
        0.408 * delta * net_radiation
        + gamma * (900.0 / (tmean + 273.0)) * wind * (es - ea)
    ) / (delta + gamma * (1.0 + 0.34 * wind))

    if not math.isfinite(eto):
        raise ValueError("Calculated ET0 is not finite.")
    return {
        "et0_mm_day": max(0.0, eto),
        "method": "FAO56_Penman_Monteith_daily",
        "weather_inputs": {
            "tmin_c": tmin,
            "tmax_c": tmax,
            "wind_speed_2m_m_s": wind,
            "solar_radiation_mj_m2_day": rs,
            "elevation_m": elevation,
            "latitude_degrees": latitude,
            "day_of_year": day_of_year,
            "actual_vapour_pressure_kpa": ea,
        },
        "intermediate_values": {
            "mean_temperature_c": tmean,
            "saturation_vapour_pressure_kpa": es,
            "slope_vapour_pressure_curve_kpa_c": delta,
            "psychrometric_constant_kpa_c": gamma,
            "extraterrestrial_radiation_mj_m2_day": ra,
            "clear_sky_radiation_mj_m2_day": rso,
            "net_radiation_mj_m2_day": net_radiation,
        },
        "assumptions": [
            "Daily soil heat flux is assumed to be zero.",
            "Wind speed is measured or adjusted to 2 m height.",
            "Solar radiation is measured incoming shortwave radiation.",
            "The result is reference-grass ET0, not crop-specific evapotranspiration.",
        ],
    }
