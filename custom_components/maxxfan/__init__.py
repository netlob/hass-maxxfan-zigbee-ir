"""MaxxFan (Zigbee IR) — Home Assistant custom integration.

Drives a MAXXAIR MaxxFan Deluxe roof fan from Home Assistant by sending
fully-formed IR packets to a Tuya-class Zigbee IR-blaster (TS1201 family,
e.g. Moes UFO-R11, HSENO) paired in Zigbee2MQTT.

Real logic lives in:

* ``protocol/`` — pure-Python MaxxFan packet encoder + Tuya base64 IR
  codec.  No HA imports.  Unit-tested in isolation, which is why this
  package's ``__init__`` keeps its imports deferred — running
  ``import custom_components.maxxfan.protocol`` from a plain Python env
  (no HA installed) must succeed.
* ``climate.py`` — the user-facing ``climate.maxxfan`` entity (commit 3).
* ``coordinator.py`` — optional cooling-thermostat loop (commit 4).
* ``config_flow.py`` — UI-driven setup (commit 3).

This stub passes hassfest + HACS validation against the scaffold; commit 3
fills in ``async_setup_entry`` and wires the platforms.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Type-only imports — never trigger an actual ``homeassistant`` import at
    # module-load time, which keeps the protocol submodule importable from
    # plain Python environments without HA installed (the test runner does
    # this).
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.typing import ConfigType


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Stub setup — real wiring lands in commit 3 alongside the config flow."""
    return True
