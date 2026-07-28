# Changelog

## 0.1.4

- Rebuild against upstream spf5000es-server `e7d096172977b0b9e23669c4c68cc218ac2c6a17`,
  which fixes Home Assistant writable-settings display with runtime state-aware
  fail-closed number ranges, FloatChargeVolt/LiProtocolType corrections, and
  server-side numeric command range validation.

## 0.1.3

- Rebuild against upstream spf5000es-server `ac42f7b88c5782eb55f14e23e022eacb0cc6a9d1`,
  which adds secret-safe DEBUG pipeline diagnostics.

## 0.1.2

- Rebuild against upstream spf5000es-server `8ffebe20262b1acc665139b388261db971713f5f`,
  which fixes the MQTT stranded-update race between polling and publish.

## 0.1.1

- Fix add-on startup: read options with shell `bashio::config` instead of invoking
  an external `bashio config` subprocess from Python, which fails under the HA
  `with-contenv bashio` runtime.

## 0.1.0

- Initial Home Assistant OS add-on wrapper for upstream
  [spf5000es-server](https://github.com/rany2/spf5000es-server) at revision
  `48d262c847c5e35ebe824fed08dd6fc0b483c6bd`.
- Maps the inverter USB/serial port and stock polling, logging, and recovery
  settings into `config.ini`.
- Obtains MQTT broker credentials from the Supervisor Mosquitto service.
- Publishes full telemetry, MQTT discovery entities, writable configuration
  controls, and the time-sync button provided by the upstream service.
