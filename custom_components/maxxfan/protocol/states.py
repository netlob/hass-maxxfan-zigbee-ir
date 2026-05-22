"""MaxxFan state model.

A single immutable ``MaxxfanState`` dataclass represents one complete IR
command — fan on/off, speed, direction, cover position, mode flags.  Every IR
packet on the wire encodes a full state (the fan keeps no memory between
packets), so this dataclass is the natural unit of work for the integration.

Factory helpers (``intake_state``, ``exhaust_state``, ``ceiling_state``) cover
the common parameterised cases and keep call sites readable.  Module-level
``STATE_OFF`` / ``STATE_VENT_OPEN`` constants are the two zero-argument
canonical states.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# Fan speed is expressed on the wire as a single byte holding 0, 10, 20,
# 30 ... 100.  The fan ignores intermediate values — values that aren't a
# multiple of 10 are simply not part of its addressable state space.
SPEED_MIN: Final = 0
SPEED_MAX: Final = 100
SPEED_STEP: Final = 10

# Thermostat setpoint is exchanged in Fahrenheit by the protocol — the fan's
# own thermostat is a US-market design.  We expose this faithfully so the
# auto-mode bit is usable; the integration's own cooling loop works in
# Celsius and never touches this field.
AUTO_TEMP_F_MIN: Final = 29
AUTO_TEMP_F_MAX: Final = 99


@dataclass(frozen=True, slots=True)
class MaxxfanState:
    """One full command-state for the MaxxFan.

    Mirrors the byte-level layout the IR remote sends (see ``maxxfan.py``).
    All fields are validated in ``__post_init__``; constructing an invalid
    state raises :class:`ValueError`.

    Attributes:
        fan_on: Motor energised (``True``) or off (``False``).
        fan_speed: 0..100 in steps of 10.  ``0`` is only valid alongside
            ``fan_on=False``; non-zero speeds require ``fan_on=True``.
        fan_exhaust: ``True`` = exhaust (push air out), ``False`` = intake.
        cover_open: ``True`` = lid raised, ``False`` = lid closed.  Fan can
            only physically move air with the lid open, except in
            ``special`` (ceiling-fan) mode.
        auto_mode: Hand control over to the fan's own thermostat using
            ``auto_temperature`` as the setpoint.  Generally **not** used by
            this integration — HA does the thermostat work and we treat the
            fan as a dumb actuator.
        auto_temperature: Setpoint in °F, 29..99.  Only consulted when
            ``auto_mode=True``.  Default 78 °F (≈ 25.5 °C) matches the
            remote's factory default.
        special: Ceiling-fan mode — fan runs with lid closed, recirculating
            cabin air instead of exchanging with outside.  Useful in winter
            while a separate heater runs.
        warn: Trigger the fan's "out of range" double-beep.  Reserved; we
            never set this from the integration.
    """

    fan_on: bool = False
    fan_speed: int = 0
    fan_exhaust: bool = False
    cover_open: bool = False
    auto_mode: bool = False
    auto_temperature: int = 78
    special: bool = False
    warn: bool = False

    def __post_init__(self) -> None:
        """Validate the field combination.

        Frozen dataclasses can't reassign in ``__post_init__``, so we only
        raise — the caller is responsible for picking sensible values.
        """
        if not SPEED_MIN <= self.fan_speed <= SPEED_MAX:
            raise ValueError(f"fan_speed must be {SPEED_MIN}..{SPEED_MAX}, got {self.fan_speed}")
        if self.fan_speed % SPEED_STEP != 0:
            raise ValueError(f"fan_speed must be a multiple of {SPEED_STEP}, got {self.fan_speed}")
        if not AUTO_TEMP_F_MIN <= self.auto_temperature <= AUTO_TEMP_F_MAX:
            raise ValueError(
                f"auto_temperature must be {AUTO_TEMP_F_MIN}..{AUTO_TEMP_F_MAX} °F,"
                f" got {self.auto_temperature}"
            )
        if self.fan_on and self.fan_speed == 0:
            raise ValueError("fan_on=True requires fan_speed > 0")
        if not self.fan_on and self.fan_speed != 0:
            raise ValueError("fan_on=False requires fan_speed == 0")


# ── Canonical zero-argument states ────────────────────────────────────────


STATE_OFF: Final = MaxxfanState()
"""All-off: motor off, lid closed.  Idempotent — sending it again is a no-op."""

STATE_VENT_OPEN: Final = MaxxfanState(cover_open=True)
"""Passive ventilation: lid open, fan off.  Air moves by convection only."""


# ── Factory helpers for the common parameterised states ───────────────────


def intake_state(speed: int) -> MaxxfanState:
    """Fan blowing air *into* the cabin at the given speed (10..100, step 10).

    Lid is opened automatically — running an intake state with the lid closed
    would just stall the motor against air pressure.
    """
    return MaxxfanState(fan_on=True, fan_speed=speed, fan_exhaust=False, cover_open=True)


def exhaust_state(speed: int) -> MaxxfanState:
    """Fan pushing air *out* of the cabin at the given speed (10..100, step 10).

    Lid is opened automatically.  This is the workhorse state for the
    cooling thermostat — when indoor > setpoint, drive an exhaust state.
    """
    return MaxxfanState(fan_on=True, fan_speed=speed, fan_exhaust=True, cover_open=True)


def ceiling_state(speed: int) -> MaxxfanState:
    """Ceiling-fan mode: fan runs with the lid closed (recirculates cabin air).

    Useful for winter operation while a separate heater is running — moves
    warm air around without losing it through the roof.  Uses the protocol's
    ``special`` bit to override the lid-open-when-fan-on default.

    Direction (intake vs exhaust) is irrelevant with the lid closed; we pick
    intake for consistency.
    """
    return MaxxfanState(
        fan_on=True,
        fan_speed=speed,
        fan_exhaust=False,
        cover_open=False,
        special=True,
    )


# ── Canonical state catalogue ─────────────────────────────────────────────
#
# A name → state mapping covering everything the integration needs to ask the
# fan to do.  Used by the climate entity's fan-mode mapping and by the
# protocol round-trip tests.

CANONICAL_STATES: Final[dict[str, MaxxfanState]] = {
    "off": STATE_OFF,
    "vent_open": STATE_VENT_OPEN,
    **{f"intake_{s:03d}": intake_state(s) for s in range(10, 101, 10)},
    **{f"exhaust_{s:03d}": exhaust_state(s) for s in range(10, 101, 10)},
    **{f"ceiling_{s:03d}": ceiling_state(s) for s in range(10, 101, 10)},
}
"""All states the integration knows how to produce, keyed by stable name.

Used as a regression fixture for protocol tests and as the lookup table for
the climate entity's fan-mode → speed mapping.  Has 32 entries:

* ``off`` (1)
* ``vent_open`` (1)
* ``intake_010`` .. ``intake_100`` (10)
* ``exhaust_010`` .. ``exhaust_100`` (10)
* ``ceiling_010`` .. ``ceiling_100`` (10)
"""
