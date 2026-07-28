# Growatt SPF5000ES

Home Assistant OS add-on that runs the upstream
[spf5000es-server](https://github.com/rany2/spf5000es-server) service against a
Growatt SPF 5000 ES inverter connected over USB/RS485. The add-on preserves the
stock Modbus polling, MQTT telemetry, Home Assistant discovery, writable
configuration controls, and inverter time-sync button from upstream.

## Prerequisites

- Home Assistant OS on a Farmassistant Pi 5 (or another supported `aarch64` /
  `amd64` host).
- The official **Mosquitto broker** add-on installed, started, and configured.
  This add-on declares `mqtt:need`; MQTT host, port, username, and password are
  supplied automatically by the Supervisor. You do not enter MQTT credentials in
  this add-on.
- Physical USB/serial access to the SPF 5000 ES. Only one host may own the
  inverter serial link at a time.

## Installation and cutover

1. Add this repository in **Settings → Add-ons → Add-on store → ⋮ → Repositories**
   if it is not already present:
   `https://github.com/matiebird/home-assistant-addons`
2. Install the **Growatt SPF5000ES** add-on.
3. **Stop SolarAssistant** (or any other software currently using the inverter
   USB cable) on the machine that owns the SPF5000ES today.
4. Move the SPF5000ES USB cable from the SolarAssistant host to the Farmassistant
   Pi 5.
5. On the Pi, open the add-on **Configuration** tab and set **Serial port**:
   - Prefer a stable path such as `/dev/serial/by-id/usb-...` if it appears
     after the move.
   - Otherwise use `/dev/ttyUSB0` (the default).
6. Leave the other options at their stock defaults unless you have a specific
   reason to tune polling, logging, or recovery behaviour.
7. Start the add-on and open **Log**. You should see the MQTT broker target
   (username and host, never the password) and upstream service startup messages.
8. In Home Assistant, verify MQTT discovery entities for **Growatt SPF 5000 ES**
   appear under **Settings → Devices & services → MQTT**.
9. Confirm live telemetry updates and that configuration entities respond. The
   time-sync control is exposed through the upstream MQTT interface.

## Rollback

To return the inverter to SolarAssistant:

1. Stop the **Growatt SPF5000ES** add-on.
2. Move the USB cable back to the SolarAssistant host.
3. Start SolarAssistant and confirm it regains the inverter.

## Configuration notes

- Serial port paths are validated for safe INI rendering; embedded newlines and
  control characters are rejected.
- `config.ini` is regenerated on each start with mode `600` and is read from
  `/data` by the upstream binary.
- Advanced recovery and polling values match the upstream defaults and map
  directly to the stock `config.ini` keys.

## Development

Wrapper tests (no serial device or network required):

```sh
python3 -m unittest discover -s growatt-spf5000es/tests -v
```

The Docker image builds the pinned upstream submodule, runs `go test ./...`, and
injects build revision `ac42f7b88c5782eb55f14e23e022eacb0cc6a9d1`.
