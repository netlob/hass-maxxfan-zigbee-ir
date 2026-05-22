"""Tests for the top-level :func:`build_tuya_code` convenience wrapper."""

from __future__ import annotations

import pytest
from custom_components.maxxfan.protocol import (
    CANONICAL_STATES,
    build_packet,
    build_tuya_code,
    decode_ir,
    encode_ir,
    packet_to_timings,
)


@pytest.mark.parametrize("state", CANONICAL_STATES.values(), ids=list(CANONICAL_STATES))
def test_build_tuya_code_matches_manual_pipeline(state) -> None:
    """``build_tuya_code`` is exactly ``encode_ir ∘ packet_to_timings ∘ build_packet``."""
    assert build_tuya_code(state) == encode_ir(packet_to_timings(build_packet(state)))


@pytest.mark.parametrize("state", CANONICAL_STATES.values(), ids=list(CANONICAL_STATES))
def test_build_tuya_code_round_trips_to_original_timings(state) -> None:
    """End-to-end: code → timings → matches what we generated from the state."""
    code = build_tuya_code(state)
    assert decode_ir(code) == packet_to_timings(build_packet(state))


def test_distinct_states_produce_distinct_codes() -> None:
    """Sanity: no two canonical states encode to the same Tuya string."""
    codes = {name: build_tuya_code(s) for name, s in CANONICAL_STATES.items()}
    assert len(set(codes.values())) == len(codes), "duplicate code across states"
