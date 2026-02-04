"""Centralized constants for the telemetry_studio application.

All unit options, defaults, and other shared constants should be defined here.
Values match gopro-dashboard CLI arguments which are then passed to pint.
"""

# =============================================================================
# UNIT DEFAULTS
# =============================================================================

DEFAULT_UNITS_SPEED = "kph"
DEFAULT_UNITS_ALTITUDE = "metre"
DEFAULT_UNITS_DISTANCE = "km"
DEFAULT_UNITS_TEMPERATURE = "degC"
DEFAULT_MAP_STYLE = "osm"

# =============================================================================
# UNIT OPTIONS
# =============================================================================

UNIT_OPTIONS = {
    "speed": {
        "label": "Speed",
        "options": [
            {"value": "kph", "label": "km/h"},
            {"value": "mph", "label": "mph"},
            {"value": "mps", "label": "m/s"},
            {"value": "knot", "label": "knots"},
        ],
        "default": DEFAULT_UNITS_SPEED,
    },
    "altitude": {
        "label": "Altitude",
        "options": [
            {"value": "metre", "label": "Meters"},
            {"value": "foot", "label": "Feet"},
        ],
        "default": DEFAULT_UNITS_ALTITUDE,
    },
    "distance": {
        "label": "Distance",
        "options": [
            {"value": "km", "label": "Kilometers"},
            {"value": "mile", "label": "Miles"},
            {"value": "foot", "label": "Feet"},
            {"value": "nmi", "label": "Nautical Miles"},
        ],
        "default": DEFAULT_UNITS_DISTANCE,
    },
    "temperature": {
        "label": "Temperature",
        "options": [
            {"value": "degC", "label": "Celsius"},
            {"value": "degF", "label": "Fahrenheit"},
            {"value": "kelvin", "label": "Kelvin"},
        ],
        "default": DEFAULT_UNITS_TEMPERATURE,
    },
}

# =============================================================================
# GPX/FIT OPTIONS
# =============================================================================

DEFAULT_GPX_MERGE_MODE = "OVERWRITE"

# =============================================================================
# GPS FILTER DEFAULTS
# =============================================================================
# These values are less strict than gopro-dashboard CLI defaults:
# - CLI default DOP max: 10 (too strict for moving vehicles)
# - CLI default speed max: 60 kph (too low for motorcycles/cars)

DEFAULT_GPS_DOP_MAX = 20.0  # GPS dilution of precision max (CLI default: 10)
DEFAULT_GPS_SPEED_MAX = 200.0  # Max speed in kph to filter outliers (CLI default: 60)
