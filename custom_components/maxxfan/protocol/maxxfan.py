"""MaxxFan IR packet encoder and decoder.

Ported from the ESPHome external component at
https://github.com/brown-studios/esphome-maxxfan-protocol (MIT-licensed,
original work by `dancrossnyc` building on the reverse-engineering by
`skypeachblue` and `wingspinner`).  The wire-format reference below is
copied (and slightly re-organised) from that repo's README so this file is
self-contained for anyone diving into the code.

Wire format
-----------

The MaxxFan remote does not use any of the well-known IR protocols
(NEC / Sony / RC-5).  It uses a custom RS-232-style frame:

* **Carrier**: 38 kHz, 50 % duty.
* **Bit period**: 800 µs.
* **Bit encoding**: mark = ``0``, space = ``1`` (i.e. carrier present = ``0``).
* **Frame per byte**: 1 start bit (always ``0``), 8 data bits LSB-first,
  2 stop bits (always ``1``).
* **Frame end**: a long trailing space (≥ 8 bit periods).

A full message is **16 bytes** transmitted back-to-back, with the layout::

    offset  field         comment
    ------  ------------  -------------------------------------------------
    0-9     preamble      fixed pattern (see PREAMBLE below)
    10      state byte    bit flags (fan_on, special, exhaust, cover, ...)
    11      fan_speed     0/10/20/.../100 — literal byte, not BCD
    12      auto_temp     Fahrenheit setpoint, 29..99
    13      0xFF          fixed
    14      0x23          fixed
    15      checksum      XOR of bytes 10..14

Every packet is a complete state-set — the fan retains nothing between
packets.  That fact is what makes this protocol so pleasant to drive from
software: no need to track current state, no risk of toggle-style drift, no
need for a "learn mode" to capture intermediate states.

State byte
~~~~~~~~~~

Bits in byte 10, LSB-first::

    bit 0   fan_on          (motor energised)
    bit 1   special         (ceiling-fan mode override — fan runs lid-closed)
    bit 2   fan_exhaust     (True = exhaust, False = intake)
    bit 3   cover_open      (lid raised)
    bit 4   auto_mode       (fan's own thermostat takes over)
    bit 5   warn            (double-beep "out of range" tone)
    bit 6   reserved
    bit 7   reserved
"""

from __future__ import annotations

from typing import Final

from .states import MaxxfanState

# ── Constants ────────────────────────────────────────────────────────────

PREAMBLE: Final = bytes([0x5A, 0xA5, 0x80, 0x7F, 0x40, 0xBF, 0x20, 0xDF, 0x10, 0xCC])
"""Fixed 10-byte preamble that opens every MaxxFan IR packet."""

BIT_TIME_US: Final = 800
"""Width of one bit symbol in microseconds."""

CARRIER_HZ: Final = 38_000
"""IR sub-carrier frequency."""

EOF_BIT_PERIODS: Final = 8
"""Number of bit-periods of trailing space the remote emits at frame end."""

# Byte positions for the variable fields in the 16-byte packet.
_STATE_OFFSET: Final = 10
_SPEED_OFFSET: Final = 11
_AUTO_TEMP_OFFSET: Final = 12
_MAGIC_FF_OFFSET: Final = 13
_MAGIC_23_OFFSET: Final = 14
_CHECKSUM_OFFSET: Final = 15

# State-byte bit masks.
_BIT_FAN_ON: Final = 0x01
_BIT_SPECIAL: Final = 0x02
_BIT_FAN_EXHAUST: Final = 0x04
_BIT_COVER_OPEN: Final = 0x08
_BIT_AUTO_MODE: Final = 0x10
_BIT_WARN: Final = 0x20
_BIT_RESERVED_MASK: Final = 0xC0  # bits 6+7 — must be zero for a valid frame

# Magic bytes at positions 13 and 14.  Purpose unknown; the original brown-
# studios decode treats any deviation as a malformed frame.
_MAGIC_FF: Final = 0xFF
_MAGIC_23: Final = 0x23

PACKET_LEN: Final = 16


# ── Encoding ─────────────────────────────────────────────────────────────


def build_packet(state: MaxxfanState) -> bytes:
    """Pack a :class:`MaxxfanState` into its 16-byte wire form.

    Args:
        state: The desired fan state.

    Returns:
        Exactly 16 bytes — preamble + state + speed + auto_temp + magic + XOR.
    """
    state_byte = (
        (_BIT_FAN_ON if state.fan_on else 0)
        | (_BIT_SPECIAL if state.special else 0)
        | (_BIT_FAN_EXHAUST if state.fan_exhaust else 0)
        | (_BIT_COVER_OPEN if state.cover_open else 0)
        | (_BIT_AUTO_MODE if state.auto_mode else 0)
        | (_BIT_WARN if state.warn else 0)
    )

    packet = bytearray(PREAMBLE)
    packet.append(state_byte)
    packet.append(state.fan_speed)
    packet.append(state.auto_temperature)
    packet.append(_MAGIC_FF)
    packet.append(_MAGIC_23)
    packet.append(
        packet[_STATE_OFFSET]
        ^ packet[_SPEED_OFFSET]
        ^ packet[_AUTO_TEMP_OFFSET]
        ^ packet[_MAGIC_FF_OFFSET]
        ^ packet[_MAGIC_23_OFFSET]
    )
    assert len(packet) == PACKET_LEN
    return bytes(packet)


def packet_to_timings(packet: bytes) -> list[int]:
    """Convert a packed packet into the µs-timing list a transmitter consumes.

    The list alternates strictly mark / space / mark / space and always
    starts with a mark (the leading start-bit of byte 0).  Adjacent same-value
    bits collapse into a single longer pulse — that's what makes the list
    much shorter than the naive ``11 bits * 16 bytes = 176 entries``.

    The trailing EOF (≥ 8 bit-periods of space) is appended as the final
    space, or merged into the last existing space if the bit stream happens
    to end on a ``1``.

    Args:
        packet: 16 bytes from :func:`build_packet`.

    Returns:
        A list of unsigned 16-bit-clean microsecond durations suitable for
        feeding to :func:`tuya_ir.encode_ir` (or any IR transmitter
        expecting alternating mark/space timings).
    """
    if len(packet) != PACKET_LEN:
        raise ValueError(f"packet must be {PACKET_LEN} bytes, got {len(packet)}")

    # Build the full bit stream, including per-byte framing.
    bits: list[int] = []
    for byte in packet:
        bits.append(0)  # start bit (mark)
        for j in range(8):  # 8 data bits, LSB-first
            bits.append((byte >> j) & 1)
        bits.extend([1, 1])  # two stop bits (spaces)

    # Run-length encode adjacent same-value bits into single pulses.  The
    # first entry corresponds to bits[0] == 0 (the first start bit) which is
    # a mark, so the resulting list is automatically mark-leading and
    # mark/space-alternating.
    timings: list[int] = []
    run_value = bits[0]
    run_length = 1
    for b in bits[1:]:
        if b == run_value:
            run_length += 1
        else:
            timings.append(run_length * BIT_TIME_US)
            run_value = b
            run_length = 1
    timings.append(run_length * BIT_TIME_US)

    # Append the EOF trailing space.  If the bit-stream already ended on a
    # space-run (even-indexed last entry), extend it instead of appending a
    # second space — keeping the list strictly alternating.
    eof = BIT_TIME_US * EOF_BIT_PERIODS
    if len(timings) % 2 == 0:
        timings[-1] += eof
    else:
        timings.append(eof)

    return timings


# ── Decoding (mainly for round-trip tests) ───────────────────────────────


def decode_packet(packet: bytes) -> MaxxfanState | None:
    """Decode a 16-byte packet back into a :class:`MaxxfanState`.

    Returns ``None`` if the packet is malformed (wrong length, wrong preamble,
    wrong magic bytes, reserved bits set, or checksum mismatch).  This is a
    convenience for unit tests — the integration itself only encodes.
    """
    if not _packet_structure_valid(packet):
        return None

    state_byte = packet[_STATE_OFFSET]
    try:
        return MaxxfanState(
            fan_on=bool(state_byte & _BIT_FAN_ON),
            special=bool(state_byte & _BIT_SPECIAL),
            fan_exhaust=bool(state_byte & _BIT_FAN_EXHAUST),
            cover_open=bool(state_byte & _BIT_COVER_OPEN),
            auto_mode=bool(state_byte & _BIT_AUTO_MODE),
            warn=bool(state_byte & _BIT_WARN),
            fan_speed=packet[_SPEED_OFFSET],
            auto_temperature=packet[_AUTO_TEMP_OFFSET],
        )
    except ValueError:
        # Speed or auto_temp byte out of the valid range — treat as malformed.
        return None


def _packet_structure_valid(packet: bytes) -> bool:
    """Frame-level validation: length, preamble, magic, reserved bits, checksum.

    Split out from :func:`decode_packet` so the decode stays under ruff's
    ``PLR0911`` (too-many-returns) ceiling without us having to relax it.
    """
    if len(packet) != PACKET_LEN:
        return False
    if packet[:_STATE_OFFSET] != PREAMBLE:
        return False
    if packet[_MAGIC_FF_OFFSET] != _MAGIC_FF or packet[_MAGIC_23_OFFSET] != _MAGIC_23:
        return False
    if packet[_STATE_OFFSET] & _BIT_RESERVED_MASK:
        return False
    expected_checksum = (
        packet[_STATE_OFFSET]
        ^ packet[_SPEED_OFFSET]
        ^ packet[_AUTO_TEMP_OFFSET]
        ^ packet[_MAGIC_FF_OFFSET]
        ^ packet[_MAGIC_23_OFFSET]
    )
    return packet[_CHECKSUM_OFFSET] == expected_checksum
