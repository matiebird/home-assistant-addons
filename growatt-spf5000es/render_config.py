#!/usr/bin/env python3
"""Render spf5000es-server config.ini from add-on options and MQTT credentials."""

from __future__ import annotations

import json
import sys
from typing import Any, Mapping


class ConfigRenderError(ValueError):
    """Raised when option values cannot be rendered safely."""


def _contains_control_characters(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def validate_string_field(name: str, value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ConfigRenderError(f"{name} must be a string")
    if _contains_control_characters(value):
        raise ConfigRenderError(f"{name} contains invalid control characters")
    return value


def format_ini_value(value: str) -> str:
    if value == "":
        return ""
    if any(character in value for character in ' \t#=;"\n\r'):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def render_config_ini(options: Mapping[str, Any], mqtt: Mapping[str, Any]) -> str:
    serial_port = validate_string_field("serial_port", options["serial_port"])
    modbus_timeout_sec = options["modbus_timeout_sec"]
    log_level = validate_string_field("log_level", options["log_level"])

    mqtt_host = validate_string_field("mqtt.host", mqtt["host"])
    mqtt_user = validate_string_field("mqtt.username", mqtt.get("username", ""))
    mqtt_password = validate_string_field("mqtt.password", mqtt.get("password", ""))

    fields = {
        "MODBUS": {
            "PORT": serial_port,
            "TIMEOUT_SEC": str(modbus_timeout_sec),
        },
        "LOGGING": {
            "LEVEL": log_level,
        },
        "MQTT": {
            "HOST": mqtt_host,
            "PORT": str(int(mqtt["port"])),
            "USER": mqtt_user,
            "PASSWORD": mqtt_password,
            "TLS_ENABLED": "false",
            "TLS_CA_FILE": "",
            "TLS_CERT_FILE": "",
            "TLS_KEY_FILE": "",
            "TLS_SERVER_NAME": "",
            "CLIENT_ID": validate_string_field(
                "mqtt_client_id", options["mqtt_client_id"]
            ),
            "KEEPALIVE_SEC": str(int(options["mqtt_keepalive_sec"])),
            "WILL_DELAY_SEC": str(int(options["mqtt_will_delay_sec"])),
            "OPERATION_TIMEOUT_SEC": str(options["mqtt_operation_timeout_sec"]),
            "DISCONNECT_TIMEOUT_SEC": str(options["mqtt_disconnect_timeout_sec"]),
            "TOPIC_PREFIX": validate_string_field(
                "mqtt_topic_prefix", options["mqtt_topic_prefix"]
            ),
            "HA_DISCOVERY_PREFIX": validate_string_field(
                "mqtt_ha_discovery_prefix", options["mqtt_ha_discovery_prefix"]
            ),
            "HA_DEVICE_ID": validate_string_field(
                "mqtt_ha_device_id", options["mqtt_ha_device_id"]
            ),
            "HA_DEVICE_NAME": validate_string_field(
                "mqtt_ha_device_name", options["mqtt_ha_device_name"]
            ),
        },
        "POLLING": {
            "CONFIG_INTERVAL_SEC": str(int(options["polling_config_interval_sec"])),
            "STATUS_INTERVAL_SEC": str(int(options["polling_status_interval_sec"])),
        },
        "RECOVERY": {
            "RECONNECT_ATTEMPTS": str(int(options["recovery_reconnect_attempts"])),
            "INITIAL_BACKOFF_SEC": str(int(options["recovery_initial_backoff_sec"])),
            "MAX_BACKOFF_SEC": str(int(options["recovery_max_backoff_sec"])),
            "RESET_COOLDOWN_SEC": str(int(options["recovery_reset_cooldown_sec"])),
        },
    }

    lines: list[str] = []
    for section, keys in fields.items():
        lines.append(f"[{section}]")
        for key, value in keys.items():
            lines.append(f"{key} = {format_ini_value(value)}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    payload = json.load(sys.stdin)
    try:
        rendered = render_config_ini(payload["options"], payload["mqtt"])
    except (ConfigRenderError, KeyError, TypeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
