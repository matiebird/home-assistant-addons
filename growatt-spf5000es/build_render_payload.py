#!/usr/bin/env python3
"""Build render_config.py JSON payload from add-on option environment variables."""

from __future__ import annotations

import json
import os
import sys


def _require(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise KeyError(name)
    return value


def build_payload() -> dict:
    options = {
        "serial_port": _require("OPTION_SERIAL_PORT"),
        "modbus_timeout_sec": float(_require("OPTION_MODBUS_TIMEOUT_SEC")),
        "log_level": _require("OPTION_LOG_LEVEL"),
        "mqtt_client_id": _require("OPTION_MQTT_CLIENT_ID"),
        "mqtt_keepalive_sec": int(_require("OPTION_MQTT_KEEPALIVE_SEC")),
        "mqtt_will_delay_sec": int(_require("OPTION_MQTT_WILL_DELAY_SEC")),
        "mqtt_operation_timeout_sec": float(
            _require("OPTION_MQTT_OPERATION_TIMEOUT_SEC")
        ),
        "mqtt_disconnect_timeout_sec": float(
            _require("OPTION_MQTT_DISCONNECT_TIMEOUT_SEC")
        ),
        "mqtt_topic_prefix": _require("OPTION_MQTT_TOPIC_PREFIX"),
        "mqtt_ha_discovery_prefix": _require("OPTION_MQTT_HA_DISCOVERY_PREFIX"),
        "mqtt_ha_device_id": _require("OPTION_MQTT_HA_DEVICE_ID"),
        "mqtt_ha_device_name": _require("OPTION_MQTT_HA_DEVICE_NAME"),
        "polling_config_interval_sec": int(
            _require("OPTION_POLLING_CONFIG_INTERVAL_SEC")
        ),
        "polling_status_interval_sec": int(
            _require("OPTION_POLLING_STATUS_INTERVAL_SEC")
        ),
        "recovery_reconnect_attempts": int(
            _require("OPTION_RECOVERY_RECONNECT_ATTEMPTS")
        ),
        "recovery_initial_backoff_sec": int(
            _require("OPTION_RECOVERY_INITIAL_BACKOFF_SEC")
        ),
        "recovery_max_backoff_sec": int(_require("OPTION_RECOVERY_MAX_BACKOFF_SEC")),
        "recovery_reset_cooldown_sec": int(
            _require("OPTION_RECOVERY_RESET_COOLDOWN_SEC")
        ),
    }
    mqtt = {
        "host": _require("MQTT_HOST"),
        "port": int(_require("MQTT_PORT")),
        "username": os.environ.get("MQTT_USER", ""),
        "password": os.environ.get("MQTT_PASSWORD", ""),
    }
    return {"options": options, "mqtt": mqtt}


def main() -> int:
    try:
        json.dump(build_payload(), sys.stdout)
    except (KeyError, TypeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
