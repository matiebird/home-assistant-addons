#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -euo pipefail

CONFIG_PATH="/data/config.ini"
BINARY="/usr/local/bin/spf5000es-server"

require_mqtt_service() {
  if ! bashio::services.available 'mqtt'; then
    bashio::exit.nok "Home Assistant Mosquitto broker add-on is required but not running."
  fi
}

log_mqtt_target() {
  local host port user
  host="$(bashio::services 'mqtt' 'host')"
  port="$(bashio::services 'mqtt' 'port')"
  user="$(bashio::services 'mqtt' 'username')"
  if [[ -n "${user}" ]]; then
    bashio::log.info "MQTT broker: ${user}@${host}:${port}"
  else
    bashio::log.info "MQTT broker: ${host}:${port}"
  fi
}

write_config_ini() {
  if ! MQTT_HOST="$(bashio::services 'mqtt' 'host')" \
    MQTT_PORT="$(bashio::services 'mqtt' 'port')" \
    MQTT_USER="$(bashio::services 'mqtt' 'username')" \
    MQTT_PASSWORD="$(bashio::services 'mqtt' 'password')" \
    python3 - <<'PY' | python3 /render_config.py >"${CONFIG_PATH}.tmp"
import json
import os
import subprocess
import sys

def cfg(name: str):
    result = subprocess.run(
        ["bashio", "config", name],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip("\n")

options = {
    "serial_port": cfg("serial_port"),
    "modbus_timeout_sec": float(cfg("modbus_timeout_sec")),
    "log_level": cfg("log_level"),
    "mqtt_client_id": cfg("mqtt_client_id"),
    "mqtt_keepalive_sec": int(cfg("mqtt_keepalive_sec")),
    "mqtt_will_delay_sec": int(cfg("mqtt_will_delay_sec")),
    "mqtt_operation_timeout_sec": float(cfg("mqtt_operation_timeout_sec")),
    "mqtt_disconnect_timeout_sec": float(cfg("mqtt_disconnect_timeout_sec")),
    "mqtt_topic_prefix": cfg("mqtt_topic_prefix"),
    "mqtt_ha_discovery_prefix": cfg("mqtt_ha_discovery_prefix"),
    "mqtt_ha_device_id": cfg("mqtt_ha_device_id"),
    "mqtt_ha_device_name": cfg("mqtt_ha_device_name"),
    "polling_config_interval_sec": int(cfg("polling_config_interval_sec")),
    "polling_status_interval_sec": int(cfg("polling_status_interval_sec")),
    "recovery_reconnect_attempts": int(cfg("recovery_reconnect_attempts")),
    "recovery_initial_backoff_sec": int(cfg("recovery_initial_backoff_sec")),
    "recovery_max_backoff_sec": int(cfg("recovery_max_backoff_sec")),
    "recovery_reset_cooldown_sec": int(cfg("recovery_reset_cooldown_sec")),
}

mqtt = {
    "host": os.environ["MQTT_HOST"],
    "port": int(os.environ["MQTT_PORT"]),
    "username": os.environ.get("MQTT_USER", ""),
    "password": os.environ.get("MQTT_PASSWORD", ""),
}

json.dump({"options": options, "mqtt": mqtt}, sys.stdout)
PY
  then
    bashio::exit.nok "Failed to render config.ini from add-on options."
  fi

  chmod 600 "${CONFIG_PATH}.tmp"
  mv -f "${CONFIG_PATH}.tmp" "${CONFIG_PATH}"
}

main() {
  require_mqtt_service
  log_mqtt_target
  write_config_ini
  cd /data
  exec "${BINARY}"
}

main "$@"
