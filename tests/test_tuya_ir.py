"""Tests for the Tuya IR base64 codec.

Round-trip coverage at both levels (literal-only and LZSS) over real
MaxxFan packet timings, plus a couple of edge cases around clamping and
the literal-block size boundary.
"""

from __future__ import annotations

import pytest
from custom_components.maxxfan.protocol import (
    CANONICAL_STATES,
    build_packet,
    decode_ir,
    encode_ir,
    packet_to_timings,
)

# ── Round-trip over all canonical states ─────────────────────────────────


@pytest.mark.parametrize("state", CANONICAL_STATES.values(), ids=list(CANONICAL_STATES))
def test_round_trip_lzss(state) -> None:
    """Encoding at the default level then decoding returns the original."""
    timings = packet_to_timings(build_packet(state))
    assert decode_ir(encode_ir(timings)) == timings


@pytest.mark.parametrize("state", CANONICAL_STATES.values(), ids=list(CANONICAL_STATES))
def test_round_trip_literal_only(state) -> None:
    """``level=0`` (literal blocks, no back-refs) also round-trips."""
    timings = packet_to_timings(build_packet(state))
    assert decode_ir(encode_ir(timings, compression_level=0)) == timings


def test_lzss_output_at_least_as_small_as_literal_only() -> None:
    """The whole point of level=2 is it's never worse than level=0."""
    timings = packet_to_timings(build_packet(next(iter(CANONICAL_STATES.values()))))
    assert len(encode_ir(timings, 2)) <= len(encode_ir(timings, 0))


# ── Edge cases ────────────────────────────────────────────────────────────


def test_empty_signal() -> None:
    """Edge case: degenerate empty input round-trips to empty output."""
    assert decode_ir(encode_ir([])) == []


def test_clamping_above_uint16() -> None:
    """Values above 65535 are clamped — the Tuya wire format uses uint16."""
    decoded = decode_ir(encode_ir([100, 200, 100_000]))
    assert decoded == [100, 200, 65535]


def test_minimal_two_pulse_signal() -> None:
    decoded = decode_ir(encode_ir([800, 1600]))
    assert decoded == [800, 1600]


def test_literal_block_boundary() -> None:
    """The literal-block format caps each block at 32 bytes — ensure the
    encoder correctly emits multiple blocks for a longer literal payload.
    """
    signal = list(range(1, 50))  # 49 distinct values → no LZSS back-refs available
    assert decode_ir(encode_ir(signal)) == signal


def test_output_is_ascii_base64() -> None:
    """The encoded form is valid base64 ASCII (no embedded newlines)."""
    code = encode_ir([800, 800, 1600, 1600])
    assert "\n" not in code
    # Every char must be in the base64 alphabet (plus padding).
    legal = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
    assert set(code) <= legal
