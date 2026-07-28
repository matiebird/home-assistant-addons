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
  if ! \
    MQTT_HOST="$(bashio::services 'mqtt' 'host')" \
    MQTT_PORT="$(bashio::services 'mqtt' 'port')" \
    MQTT_USER="$(bashio::services 'mqtt' 'username')" \
    MQTT_PASSWORD="$(bashio::services 'mqtt' 'password')" \
    OPTION_SERIAL_PORT="$(bashio::config 'serial_port')" \
    OPTION_MODBUS_TIMEOUT_SEC="$(bashio::config 'modbus_timeout_sec')" \
    OPTION_LOG_LEVEL="$(bashio::config 'log_level')" \
    OPTION_MQTT_CLIENT_ID="$(bashio::config 'mqtt_client_id')" \
    OPTION_MQTT_KEEPALIVE_SEC="$(bashio::config 'mqtt_keepalive_sec')" \
    OPTION_MQTT_WILL_DELAY_SEC="$(bashio::config 'mqtt_will_delay_sec')" \
    OPTION_MQTT_OPERATION_TIMEOUT_SEC="$(bashio::config 'mqtt_operation_timeout_sec')" \
    OPTION_MQTT_DISCONNECT_TIMEOUT_SEC="$(bashio::config 'mqtt_disconnect_timeout_sec')" \
    OPTION_MQTT_TOPIC_PREFIX="$(bashio::config 'mqtt_topic_prefix')" \
    OPTION_MQTT_HA_DISCOVERY_PREFIX="$(bashio::config 'mqtt_ha_discovery_prefix')" \
    OPTION_MQTT_HA_DEVICE_ID="$(bashio::config 'mqtt_ha_device_id')" \
    OPTION_MQTT_HA_DEVICE_NAME="$(bashio::config 'mqtt_ha_device_name')" \
    OPTION_POLLING_CONFIG_INTERVAL_SEC="$(bashio::config 'polling_config_interval_sec')" \
    OPTION_POLLING_STATUS_INTERVAL_SEC="$(bashio::config 'polling_status_interval_sec')" \
    OPTION_RECOVERY_RECONNECT_ATTEMPTS="$(bashio::config 'recovery_reconnect_attempts')" \
    OPTION_RECOVERY_INITIAL_BACKOFF_SEC="$(bashio::config 'recovery_initial_backoff_sec')" \
    OPTION_RECOVERY_MAX_BACKOFF_SEC="$(bashio::config 'recovery_max_backoff_sec')" \
    OPTION_RECOVERY_RESET_COOLDOWN_SEC="$(bashio::config 'recovery_reset_cooldown_sec')" \
    python3 /build_render_payload.py | python3 /render_config.py >"${CONFIG_PATH}.tmp"
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
