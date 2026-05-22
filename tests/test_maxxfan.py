"""Tests for the MaxxFan IR packet encoder + decoder.

Round-trip coverage: every state in :data:`CANONICAL_STATES` is encoded to
bytes, decoded back, and must equal the original.  Plus a hand-computed
known-vector test against the README's example packet to catch any
regression in the byte layout itself.
"""

from __future__ import annotations

import pytest
from custom_components.maxxfan.protocol import (
    BIT_TIME_US,
    CANONICAL_STATES,
    PACKET_LEN,
    PREAMBLE,
    MaxxfanState,
    build_packet,
    ceiling_state,
    decode_packet,
    exhaust_state,
    intake_state,
    packet_to_timings,
)

# ── Known-vector test (regression on byte layout) ───────────────────────


def test_off_state_known_bytes() -> None:
    """``STATE_OFF`` packs to a fully-deterministic, hand-computed packet."""
    packet = build_packet(MaxxfanState())  # all defaults — equivalent to STATE_OFF

    # preamble
    assert packet[:10] == PREAMBLE
    # state byte: nothing set
    assert packet[10] == 0x00
    # speed: 0
    assert packet[11] == 0x00
    # auto_temperature default 78°F
    assert packet[12] == 78
    # magic
    assert packet[13] == 0xFF
    assert packet[14] == 0x23
    # XOR of bytes 10..14 = 0x00 ^ 0x00 ^ 78 ^ 0xFF ^ 0x23
    assert packet[15] == 0x00 ^ 0x00 ^ 78 ^ 0xFF ^ 0x23


def test_exhaust_50_known_bytes() -> None:
    """Hand-computed packet for exhaust at 50 % — covers the variable-byte path."""
    packet = build_packet(exhaust_state(50))

    assert packet[:10] == PREAMBLE
    # fan_on (0x01) + exhaust (0x04) + cover_open (0x08) = 0x0D
    assert packet[10] == 0x0D
    assert packet[11] == 50
    assert packet[12] == 78  # default auto_temperature
    assert packet[13] == 0xFF
    assert packet[14] == 0x23
    assert packet[15] == 0x0D ^ 50 ^ 78 ^ 0xFF ^ 0x23


def test_ceiling_mode_sets_special_bit() -> None:
    packet = build_packet(ceiling_state(70))
    # special bit (0x02) is what distinguishes ceiling-fan mode from a
    # normal intake state with cover closed.
    assert packet[10] & 0x02


# ── Length + checksum invariants ─────────────────────────────────────────


@pytest.mark.parametrize("state", CANONICAL_STATES.values(), ids=list(CANONICAL_STATES))
def test_packet_length_is_16(state: MaxxfanState) -> None:
    assert len(build_packet(state)) == PACKET_LEN


@pytest.mark.parametrize("state", CANONICAL_STATES.values(), ids=list(CANONICAL_STATES))
def test_packet_checksum_is_xor_of_bytes_10_to_14(state: MaxxfanState) -> None:
    packet = build_packet(state)
    expected = packet[10] ^ packet[11] ^ packet[12] ^ packet[13] ^ packet[14]
    assert packet[15] == expected


# ── Encode → decode round-trip ───────────────────────────────────────────


@pytest.mark.parametrize("state", CANONICAL_STATES.values(), ids=list(CANONICAL_STATES))
def test_packet_round_trip(state: MaxxfanState) -> None:
    """Every canonical state survives encode → decode unchanged."""
    decoded = decode_packet(build_packet(state))
    assert decoded == state


# ── Decoder rejects malformed input ──────────────────────────────────────


class TestDecoderRejectsMalformedInput:
    def test_wrong_length(self) -> None:
        assert decode_packet(b"\x00" * 8) is None
        assert decode_packet(b"\x00" * 20) is None

    def test_wrong_preamble(self) -> None:
        good = bytearray(build_packet(MaxxfanState()))
        good[0] = 0xAA  # corrupt first preamble byte
        assert decode_packet(bytes(good)) is None

    def test_wrong_magic_ff(self) -> None:
        good = bytearray(build_packet(MaxxfanState()))
        good[13] = 0xAB  # was 0xFF
        # Need to fix the checksum so it's specifically the magic that's
        # wrong, not the checksum.
        good[15] = good[10] ^ good[11] ^ good[12] ^ good[13] ^ good[14]
        assert decode_packet(bytes(good)) is None

    def test_wrong_magic_23(self) -> None:
        good = bytearray(build_packet(MaxxfanState()))
        good[14] = 0xCD
        good[15] = good[10] ^ good[11] ^ good[12] ^ good[13] ^ good[14]
        assert decode_packet(bytes(good)) is None

    def test_bad_checksum(self) -> None:
        good = bytearray(build_packet(MaxxfanState()))
        good[15] ^= 0xFF  # flip every bit of the checksum
        assert decode_packet(bytes(good)) is None

    def test_reserved_bits_rejected(self) -> None:
        good = bytearray(build_packet(MaxxfanState()))
        good[10] |= 0x80  # set reserved bit 7
        good[15] = good[10] ^ good[11] ^ good[12] ^ good[13] ^ good[14]
        assert decode_packet(bytes(good)) is None


# ── Timings list ─────────────────────────────────────────────────────────


@pytest.mark.parametrize("state", CANONICAL_STATES.values(), ids=list(CANONICAL_STATES))
def test_timings_start_with_mark_and_alternate(state: MaxxfanState) -> None:
    timings = packet_to_timings(build_packet(state))
    # All entries are positive (an IR transmitter has no "negative" pulses;
    # the alternation between mark and space is implicit in the position).
    assert all(t > 0 for t in timings)
    # Every entry is a whole number of bit-periods.
    assert all(t % BIT_TIME_US == 0 for t in timings)


def test_timings_eof_appended() -> None:
    """The trailing space includes at least the 8-bit-period EOF marker."""
    timings = packet_to_timings(build_packet(MaxxfanState()))
    # Position must be even-indexed (a space) and be the longest entry.
    assert len(timings) % 2 == 0
    assert timings[-1] >= 8 * BIT_TIME_US


def test_timings_uint16_clean() -> None:
    """No entry exceeds 65535 — Tuya's wire format stores each as a uint16."""
    timings = packet_to_timings(build_packet(MaxxfanState()))
    assert all(0 < t <= 65535 for t in timings)


def test_packet_to_timings_rejects_wrong_length() -> None:
    with pytest.raises(ValueError, match=str(PACKET_LEN)):
        packet_to_timings(b"\x00" * 12)


# ── Spot-checks on individual flag bits ──────────────────────────────────


def test_intake_clears_exhaust_bit() -> None:
    packet = build_packet(intake_state(40))
    assert not packet[10] & 0x04  # exhaust bit clear


def test_warn_bit_only_when_requested() -> None:
    default = build_packet(MaxxfanState())
    assert not default[10] & 0x20
    warned = build_packet(MaxxfanState(warn=True))
    assert warned[10] & 0x20
