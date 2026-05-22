# MaxxFan (Zigbee IR) for Home Assistant

[![hassfest](https://github.com/netlob/hass-maxxfan-zigbee-ir/actions/workflows/validate.yml/badge.svg)](https://github.com/netlob/hass-maxxfan-zigbee-ir/actions/workflows/validate.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Tests](https://github.com/netlob/hass-maxxfan-zigbee-ir/actions/workflows/tests.yml/badge.svg)](https://github.com/netlob/hass-maxxfan-zigbee-ir/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/netlob/hass-maxxfan-zigbee-ir)](https://github.com/netlob/hass-maxxfan-zigbee-ir/releases)

> Native Home Assistant control of a MAXXAIR MaxxFan Deluxe roof fan, via a
> Tuya-class Zigbee IR-blaster paired in Zigbee2MQTT. No WiFi, no learn-mode,
> no cloud — every command is a fully-formed IR packet generated from the
> reverse-engineered MaxxFan protocol.

> [!NOTE]
> **🚧 This README is the v0.1 scaffold.** Screenshots, full setup walk-through,
> and the device matrix arrive in the polish commit. Code lands incrementally in
> the meantime — track the [CHANGELOG](CHANGELOG.md).

## What you get (planned)

- A real `climate.maxxfan` entity registered as a Device in HA (vendor, model,
  software version).
- HVAC modes `off / cool / fan_only / heat` (where `heat` is MaxxFan's
  ceiling-fan mode — lid closed, fan running for in-cabin air circulation).
- Fan modes `off / low / medium / high / max`, mappable to the underlying
  10 % speed steps.
- Optional built-in cooling thermostat: pick an indoor temperature sensor in
  options and the integration drives the fan toward your setpoint with
  configurable hysteresis.
- A `maxxfan.send_state` service for arbitrary fine-grained control from
  scripts (direction, speed in 10 % steps, lid open/close, ceiling-fan mode,
  beep).
- No learn-mode — every code is generated programmatically. Add new states
  or fan-mode mappings via config; no need to fish out the original remote.

## Why this exists

Most "smart IR" integrations replay codes they were taught with the original
remote — fragile (timing tolerances) and limited (one code per state you
bothered to record). The MaxxFan IR protocol has been fully reverse-engineered
by the [brown-studios/esphome-maxxfan-protocol](https://github.com/brown-studios/esphome-maxxfan-protocol)
team. Combining that with a Tuya-base64 codec means we can synthesise **any**
state on demand — without ever needing the remote in our hand.

## Hardware required

- A **MAXXAIR MaxxFan Deluxe** (any of 5100K / 6200K / 7000K / 7500K — they all
  share the protocol).
- A **Tuya-class Zigbee IR-blaster** paired in Zigbee2MQTT, e.g.
  Moes UFO-R11, HSENO, ZS06. Anything that exposes `ir_code_to_send` in Z2M.
- A working **Zigbee2MQTT** + Mosquitto setup talking to your Home Assistant.

## Installation

_Detailed steps + screenshots land in the polish commit. Quick summary for
early adopters:_

1. In HACS → Integrations → ⋮ → **Custom repositories**, add
   `https://github.com/netlob/hass-maxxfan-zigbee-ir` as **Integration**.
2. Install and restart Home Assistant.
3. Settings → Devices & Services → **Add Integration** → search "MaxxFan".

## Acknowledgements

This integration stands entirely on the shoulders of two upstream
reverse-engineering efforts:

- **[brown-studios/esphome-maxxfan-protocol](https://github.com/brown-studios/esphome-maxxfan-protocol)**
  — full reverse-engineering of the MaxxFan IR remote protocol (16-byte
  packet, 38 kHz carrier, 800 µs RS-232-style framing). The encoder in this
  repo is a faithful Python port of their C++ implementation. Without them
  this integration simply would not exist.
- **[burkminipup/irdb-to-tuya](https://github.com/burkminipup/irdb-to-tuya)**
  — Tuya base64 IR codec (LZSS-style compression). Vendored verbatim under
  their MIT license; see [`custom_components/maxxfan/protocol/tuya_ir.py`](custom_components/maxxfan/protocol/tuya_ir.py).
- **[skypeachblue](https://github.com/skypeachblue)** &
  **[wingspinner](https://github.com/wingspinner)** — the original MaxxFan
  protocol reversing work that fed into the brown-studios component.

## Roadmap

- Broadlink transport (use a Broadlink hub instead of Zigbee).
- ESPHome `remote_transmitter` transport (DIY ESP32 + IR LED).
- WiFi Tuya IR-blaster transport (same codec, different delivery).
- Optional IR receiver support for closed-loop state when the original remote
  is used.

Explicitly **not** planned: companion-heater coupling (e.g. mutex with a
diesel/propane heater). That's a personal-setup concern — wire it up via a
regular HA automation, this integration stays MaxxFan-focused.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
