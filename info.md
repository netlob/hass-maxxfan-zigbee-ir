# MaxxFan (Zigbee IR)

Drive a MAXXAIR MaxxFan Deluxe roof fan from Home Assistant via a Tuya-class
Zigbee IR-blaster paired in Zigbee2MQTT.

## Highlights

- Native `climate.maxxfan` entity (registered as a Device with vendor / model /
  software version)
- HVAC modes: `off / cool / fan_only / heat` (heat = MaxxFan ceiling-fan mode)
- Fan modes: `off / low / medium / high / max`
- Optional built-in cooling thermostat — pick an indoor temperature sensor
  and the integration drives the fan toward your setpoint
- `maxxfan.send_state` service for fine-grained programmatic control
- **No learn-mode required** — every IR packet is synthesised on demand from
  the reverse-engineered MaxxFan protocol

## Hardware

- MAXXAIR MaxxFan Deluxe (5100K / 6200K / 7000K / 7500K)
- Tuya-class Zigbee IR-blaster (Moes UFO-R11, HSENO, ZS06 — anything Z2M
  exposes as `ir_code_to_send`)
- Zigbee2MQTT

## Credits

Built on the reverse-engineering of
[brown-studios/esphome-maxxfan-protocol](https://github.com/brown-studios/esphome-maxxfan-protocol)
(MaxxFan IR protocol) and
[burkminipup/irdb-to-tuya](https://github.com/burkminipup/irdb-to-tuya)
(Tuya base64 IR codec). See the [README](https://github.com/netlob/hass-maxxfan-zigbee-ir#acknowledgements)
for the full list.
