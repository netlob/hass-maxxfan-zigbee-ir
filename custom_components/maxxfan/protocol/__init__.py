"""Pure-Python protocol layer — no Home Assistant imports.

This package is the heart of the integration: a Python port of the
brown-studios MaxxFan IR encoder + a vendored Tuya base64 codec.  It is
testable in isolation and has no awareness of HA's lifecycle, MQTT, or
asyncio.

The integration's HA-facing modules (``climate.py``, ``coordinator.py``,
``__init__.py``) all import from here and only from here for protocol
concerns.

Public surface
~~~~~~~~~~~~~~

>>> from custom_components.maxxfan.protocol import (
...     MaxxfanState, build_tuya_code, exhaust_state,
... )
>>> code = build_tuya_code(exhaust_state(50))  # exhaust at 50 %
>>> isinstance(code, str) and len(code) > 0
True
"""

from __future__ import annotations

from .maxxfan import (
    BIT_TIME_US,
    CARRIER_HZ,
    PACKET_LEN,
    PREAMBLE,
    build_packet,
    decode_packet,
    packet_to_timings,
)
from .states import (
    AUTO_TEMP_F_MAX,
    AUTO_TEMP_F_MIN,
    CANONICAL_STATES,
    SPEED_MAX,
    SPEED_MIN,
    SPEED_STEP,
    STATE_OFF,
    STATE_VENT_OPEN,
    MaxxfanState,
    ceiling_state,
    exhaust_state,
    intake_state,
)
from .tuya_ir import decode_ir, encode_ir


def build_tuya_code(state: MaxxfanState) -> str:
    """Top-level convenience: state → Tuya base64 IR code in one call.

    Equivalent to::

        encode_ir(packet_to_timings(build_packet(state)))

    This is the only function the integration's HA layer actually needs from
    the protocol package — everything else is exposed for testing and for
    advanced users who want to inspect the intermediate forms.
    """
    return encode_ir(packet_to_timings(build_packet(state)))


__all__ = [
    "AUTO_TEMP_F_MAX",
    "AUTO_TEMP_F_MIN",
    "BIT_TIME_US",
    "CANONICAL_STATES",
    "CARRIER_HZ",
    "PACKET_LEN",
    "PREAMBLE",
    "SPEED_MAX",
    "SPEED_MIN",
    "SPEED_STEP",
    "STATE_OFF",
    "STATE_VENT_OPEN",
    "MaxxfanState",
    "build_packet",
    "build_tuya_code",
    "ceiling_state",
    "decode_ir",
    "decode_packet",
    "encode_ir",
    "exhaust_state",
    "intake_state",
    "packet_to_timings",
]
