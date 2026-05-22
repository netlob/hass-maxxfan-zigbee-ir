"""Constants for the MaxxFan integration.

A single source of truth for the domain string, config-flow keys, default
values, and other magic identifiers used across the integration.  Anything
that gets referenced in more than one module belongs here.
"""

from __future__ import annotations

from typing import Final

# Home Assistant domain — must match `domain` in manifest.json and the
# `custom_components/<domain>/` directory name.
DOMAIN: Final = "maxxfan"

# Integration-wide branding for the device registry entry.
MANUFACTURER: Final = "MaxxAir / Airxcel"
DEFAULT_MODEL: Final = "MaxxFan Deluxe"

# ── Config-flow keys ────────────────────────────────────────────────────────
# Keys used in the `data` and `options` dicts of a config entry.  Kept as
# constants so a typo at one call site can't silently disagree with another.

CONF_MQTT_TOPIC_PREFIX: Final = "mqtt_topic_prefix"
CONF_IR_BLASTER_NAME: Final = "ir_blaster_name"
CONF_FAN_MODEL: Final = "fan_model"

# Optional cooling-loop config (set only if the user picks an indoor sensor).
CONF_INDOOR_TEMP_SENSOR: Final = "indoor_temp_sensor"
CONF_HYSTERESIS: Final = "hysteresis"
CONF_FAN_MODE_SPEEDS: Final = "fan_mode_speeds"

# ── Defaults ────────────────────────────────────────────────────────────────

DEFAULT_MQTT_TOPIC_PREFIX: Final = "zigbee2mqtt"
DEFAULT_HYSTERESIS: Final = 0.5  # °C dead-band around the setpoint
DEFAULT_FAN_MODE_SPEEDS: Final = {
    "off": 0,
    "low": 30,
    "medium": 50,
    "high": 80,
    "max": 100,
}
