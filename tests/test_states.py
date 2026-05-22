"""Tests for the :mod:`states` module."""

from __future__ import annotations

import pytest
from custom_components.maxxfan.protocol import (
    CANONICAL_STATES,
    STATE_OFF,
    STATE_VENT_OPEN,
    MaxxfanState,
    ceiling_state,
    exhaust_state,
    intake_state,
)


class TestMaxxfanStateValidation:
    """Constructor invariants."""

    def test_default_state_is_off(self) -> None:
        state = MaxxfanState()
        assert state.fan_on is False
        assert state.fan_speed == 0
        assert state.cover_open is False

    @pytest.mark.parametrize("speed", [0, 10, 20, 50, 100])
    def test_valid_speed_accepted(self, speed: int) -> None:
        # fan_on must match: 0 -> off, non-zero -> on
        MaxxfanState(fan_on=speed > 0, fan_speed=speed)

    @pytest.mark.parametrize("speed", [-10, 5, 15, 33, 101, 110])
    def test_invalid_speed_rejected(self, speed: int) -> None:
        with pytest.raises(ValueError, match="fan_speed"):
            MaxxfanState(fan_on=True, fan_speed=speed)

    def test_fan_on_requires_nonzero_speed(self) -> None:
        with pytest.raises(ValueError, match="fan_speed > 0"):
            MaxxfanState(fan_on=True, fan_speed=0)

    def test_fan_off_requires_zero_speed(self) -> None:
        with pytest.raises(ValueError, match="fan_speed == 0"):
            MaxxfanState(fan_on=False, fan_speed=10)

    @pytest.mark.parametrize("temp", [29, 50, 78, 99])
    def test_valid_auto_temperature_accepted(self, temp: int) -> None:
        MaxxfanState(auto_temperature=temp)

    @pytest.mark.parametrize("temp", [28, 100, -5, 200])
    def test_invalid_auto_temperature_rejected(self, temp: int) -> None:
        with pytest.raises(ValueError, match="auto_temperature"):
            MaxxfanState(auto_temperature=temp)

    def test_state_is_frozen(self) -> None:
        # ``slots=True`` + ``frozen=True`` dataclass — attribute assignment
        # is rejected with AttributeError ("cannot assign to field …" or
        # similar; the exact message varies across CPython versions).
        state = MaxxfanState()
        with pytest.raises(AttributeError, match="fan_on"):
            state.fan_on = True  # type: ignore[misc]


class TestCanonicalStates:
    """The canonical-state constants and factory helpers."""

    def test_state_off_is_all_off(self) -> None:
        assert MaxxfanState() == STATE_OFF
        assert STATE_OFF.fan_on is False
        assert STATE_OFF.cover_open is False

    def test_state_vent_open(self) -> None:
        assert STATE_VENT_OPEN.fan_on is False
        assert STATE_VENT_OPEN.cover_open is True

    @pytest.mark.parametrize("speed", [10, 30, 50, 100])
    def test_intake_state(self, speed: int) -> None:
        state = intake_state(speed)
        assert state.fan_on is True
        assert state.fan_speed == speed
        assert state.fan_exhaust is False
        assert state.cover_open is True
        assert state.special is False

    @pytest.mark.parametrize("speed", [10, 50, 100])
    def test_exhaust_state(self, speed: int) -> None:
        state = exhaust_state(speed)
        assert state.fan_on is True
        assert state.fan_speed == speed
        assert state.fan_exhaust is True
        assert state.cover_open is True
        assert state.special is False

    @pytest.mark.parametrize("speed", [10, 50, 100])
    def test_ceiling_state(self, speed: int) -> None:
        state = ceiling_state(speed)
        assert state.fan_on is True
        assert state.fan_speed == speed
        assert state.cover_open is False  # lid closed in ceiling-fan mode
        assert state.special is True

    def test_canonical_states_count(self) -> None:
        # 1 off + 1 vent_open + 10 intake + 10 exhaust + 10 ceiling
        assert len(CANONICAL_STATES) == 32

    def test_canonical_states_all_valid_and_distinct(self) -> None:
        names = list(CANONICAL_STATES)
        assert len(set(names)) == len(names), "duplicate name in CANONICAL_STATES"
        # Every value must be a valid MaxxfanState (already validated via
        # __post_init__ at module import time — this is belt-and-braces).
        for name, state in CANONICAL_STATES.items():
            assert isinstance(state, MaxxfanState), name
