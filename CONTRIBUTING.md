# Contributing

Thanks for considering a contribution! This integration is meant to stay small
and focused on the MaxxFan Deluxe over a Tuya-class Zigbee IR-blaster. Bug
fixes, new IR-blaster transports, and broader device coverage are all welcome.

## Development setup

This repo targets **Python 3.13** and **Home Assistant 2025.1+**.

```bash
git clone https://github.com/netlob/hass-maxxfan-zigbee-ir.git
cd hass-maxxfan-zigbee-ir
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pre-commit install
```

## Running checks locally

The same checks the CI runs:

```bash
ruff format --check .
ruff check .
mypy custom_components/maxxfan
pytest --cov
```

`pre-commit run --all-files` runs the lint/format hooks against every file —
useful as a final sanity check before opening a PR.

## Project layout

- `custom_components/maxxfan/protocol/` — pure-Python protocol layer (MaxxFan
  packet encoder + Tuya base64 codec + state dataclass). No HA imports.
  Strict-typed via mypy. Aim for ≥ 95 % coverage.
- `custom_components/maxxfan/{__init__,climate,coordinator,config_flow}.py` —
  the Home Assistant integration surface.
- `tests/` — pytest, using `pytest-homeassistant-custom-component` for HA-side
  fixtures.

## Commit / PR guidelines

- One logical change per PR. Bundle ruff/mypy fixes with the code they belong
  to, not as a separate PR.
- Reference any related issue with `Fixes #N` or `Refs #N`.
- Tests are required for protocol-layer changes and for new HA behaviour.
- CHANGELOG entries land in the `[Unreleased]` section; the release commit
  promotes them to a versioned heading.

## Adding a new IR-blaster transport

Subclass `MaxxfanTransport` (from `protocol/transport.py`), implement
`async def send_state(state: MaxxfanState) -> None`, and wire it into the
config flow as a transport choice. Keep the encoder + climate code untouched —
that's the whole point of the abstraction.

## Reverse-engineering questions

Protocol-level questions (timing, encoding, undocumented bits) are usually
better filed upstream at
[brown-studios/esphome-maxxfan-protocol](https://github.com/brown-studios/esphome-maxxfan-protocol),
which is where the decode lives. Open an issue here only if it's specific to
how this integration handles a particular packet.
