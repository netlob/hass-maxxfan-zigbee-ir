"""MaxxFan (Zigbee IR) — Home Assistant custom integration.

Drives a MAXXAIR MaxxFan Deluxe roof fan from Home Assistant by sending
fully-formed IR packets to a Tuya-class Zigbee IR-blaster (TS1201 family,
e.g. Moes UFO-R11, HSENO) paired in Zigbee2MQTT.

This package's `__init__.py` is intentionally minimal — it wires the config
entry to the platforms.  Real logic lives in:

* `protocol/` — pure-Python MaxxFan packet encoder + Tuya base64 IR codec.
  No HA imports.  Unit-tested in isolation.
* `climate.py` — the user-facing `climate.maxxfan` entity.
* `coordinator.py` — optional cooling-thermostat loop (engaged when the user
  picks an indoor temperature sensor in options).
* `config_flow.py` — UI-driven setup.

The integration shape will fill in over commits 2–4.  This scaffold passes
hassfest + HACS validation against an empty placeholder.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Stub setup — real wiring lands in commit 3 alongside the config flow."""
    return True
