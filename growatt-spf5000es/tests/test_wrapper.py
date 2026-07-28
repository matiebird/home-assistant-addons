#!/usr/bin/env python3
"""Deterministic wrapper tests for the Growatt SPF5000ES add-on."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ADDON_ROOT = Path(__file__).resolve().parents[1]
RENDER_SCRIPT = ADDON_ROOT / "render_config.py"
BUILD_PAYLOAD_SCRIPT = ADDON_ROOT / "build_render_payload.py"
CONFIG_YAML = ADDON_ROOT / "config.yaml"
RUN_SH = ADDON_ROOT / "run.sh"
SERVER_REVISION = "8ffebe20262b1acc665139b388261db971713f5f"

DEFAULT_OPTIONS = {
    "serial_port": "/dev/ttyUSB0",
    "modbus_timeout_sec": 1.5,
    "log_level": "INFO",
    "mqtt_client_id": "growatt_spf5000es",
    "mqtt_keepalive_sec": 60,
    "mqtt_will_delay_sec": 300,
    "mqtt_operation_timeout_sec": 10,
    "mqtt_disconnect_timeout_sec": 5,
    "mqtt_topic_prefix": "growatt/spf5000es",
    "mqtt_ha_discovery_prefix": "homeassistant",
    "mqtt_ha_device_id": "growatt_spf5000es",
    "mqtt_ha_device_name": "Growatt SPF 5000 ES",
    "polling_config_interval_sec": 600,
    "polling_status_interval_sec": 2,
    "recovery_reconnect_attempts": 3,
    "recovery_initial_backoff_sec": 1,
    "recovery_max_backoff_sec": 10,
    "recovery_reset_cooldown_sec": 300,
}

DEFAULT_MQTT = {
    "host": "core-mosquitto",
    "port": 1883,
    "username": "addons",
    "password": "s3cret!pass",
}

def option_env(options: dict, mqtt: dict) -> dict[str, str]:
    return {
        "OPTION_SERIAL_PORT": options["serial_port"],
        "OPTION_MODBUS_TIMEOUT_SEC": str(options["modbus_timeout_sec"]),
        "OPTION_LOG_LEVEL": options["log_level"],
        "OPTION_MQTT_CLIENT_ID": options["mqtt_client_id"],
        "OPTION_MQTT_KEEPALIVE_SEC": str(options["mqtt_keepalive_sec"]),
        "OPTION_MQTT_WILL_DELAY_SEC": str(options["mqtt_will_delay_sec"]),
        "OPTION_MQTT_OPERATION_TIMEOUT_SEC": str(options["mqtt_operation_timeout_sec"]),
        "OPTION_MQTT_DISCONNECT_TIMEOUT_SEC": str(
            options["mqtt_disconnect_timeout_sec"]
        ),
        "OPTION_MQTT_TOPIC_PREFIX": options["mqtt_topic_prefix"],
        "OPTION_MQTT_HA_DISCOVERY_PREFIX": options["mqtt_ha_discovery_prefix"],
        "OPTION_MQTT_HA_DEVICE_ID": options["mqtt_ha_device_id"],
        "OPTION_MQTT_HA_DEVICE_NAME": options["mqtt_ha_device_name"],
        "OPTION_POLLING_CONFIG_INTERVAL_SEC": str(
            options["polling_config_interval_sec"]
        ),
        "OPTION_POLLING_STATUS_INTERVAL_SEC": str(
            options["polling_status_interval_sec"]
        ),
        "OPTION_RECOVERY_RECONNECT_ATTEMPTS": str(
            options["recovery_reconnect_attempts"]
        ),
        "OPTION_RECOVERY_INITIAL_BACKOFF_SEC": str(
            options["recovery_initial_backoff_sec"]
        ),
        "OPTION_RECOVERY_MAX_BACKOFF_SEC": str(options["recovery_max_backoff_sec"]),
        "OPTION_RECOVERY_RESET_COOLDOWN_SEC": str(
            options["recovery_reset_cooldown_sec"]
        ),
        "MQTT_HOST": mqtt["host"],
        "MQTT_PORT": str(mqtt["port"]),
        "MQTT_USER": mqtt["username"],
        "MQTT_PASSWORD": mqtt["password"],
    }


def render_ini_from_option_env(options: dict, mqtt: dict) -> str:
    env = {**option_env(options, mqtt)}
    payload = subprocess.run(
        [sys.executable, str(BUILD_PAYLOAD_SCRIPT)],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if payload.returncode != 0:
        raise AssertionError(payload.stderr.strip() or payload.stdout)
    completed = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT)],
        input=payload.stdout,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or completed.stdout)
    return completed.stdout


class WrapperMetadataTests(unittest.TestCase):
    def test_config_yaml_contains_required_ha_metadata(self) -> None:
        text = CONFIG_YAML.read_text(encoding="utf-8")
        self.assertIn('name: Growatt SPF5000ES', text)
        self.assertIn("slug: growatt_spf5000es", text)
        self.assertIn('version: "0.1.2"', text)
        self.assertIn("init: false", text)
        self.assertIn("uart: true", text)
        self.assertIn("startup: services", text)
        self.assertIn("- mqtt:need", text)
        self.assertIn("- mqtt", text)
        self.assertIn("serial_port: /dev/ttyUSB0", text)
        self.assertIn("polling_status_interval_sec: 2", text)
        self.assertIn("polling_config_interval_sec: 600", text)
        self.assertIn("modbus_timeout_sec: 1.5", text)
        self.assertIn("- aarch64", text)
        self.assertIn("- amd64", text)

    def test_dockerfile_pins_upstream_revision(self) -> None:
        dockerfile = (ADDON_ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn(SERVER_REVISION, dockerfile)
        self.assertIn("go test ./...", dockerfile)

    def test_dockerfile_installs_runtime_python(self) -> None:
        dockerfile = (ADDON_ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("apk add --no-cache python3", dockerfile)

    def test_run_sh_does_not_log_password(self) -> None:
        script = RUN_SH.read_text(encoding="utf-8")
        log_section = script.split("log_mqtt_target()", 1)[1].split("write_config_ini()", 1)[0]
        self.assertNotIn("MQTT_PASSWORD", log_section)
        self.assertNotIn("password", log_section.lower())

    def test_run_sh_uses_bashio_config_without_subprocess(self) -> None:
        script = RUN_SH.read_text(encoding="utf-8")
        self.assertIn("bashio::config", script)
        self.assertNotIn('["bashio", "config"', script)
        self.assertNotIn("subprocess", script)
        self.assertNotIn("import subprocess", script)
        self.assertIn("build_render_payload.py", script)


class RenderConfigTests(unittest.TestCase):
    def test_option_env_render_path_matches_direct_payload(self) -> None:
        rendered = render_ini_from_option_env(DEFAULT_OPTIONS, DEFAULT_MQTT)
        self.assertIn("PORT = /dev/ttyUSB0", rendered)
        self.assertIn("HOST = core-mosquitto", rendered)
        self.assertIn("PASSWORD = s3cret!pass", rendered)

    def test_renders_stock_sections_and_defaults(self) -> None:
        rendered = render_ini_from_option_env(DEFAULT_OPTIONS, DEFAULT_MQTT)
        self.assertIn("[MODBUS]", rendered)
        self.assertIn("PORT = /dev/ttyUSB0", rendered)
        self.assertIn("TIMEOUT_SEC = 1.5", rendered)
        self.assertIn("[MQTT]", rendered)
        self.assertIn("HOST = core-mosquitto", rendered)
        self.assertIn("PORT = 1883", rendered)
        self.assertIn("USER = addons", rendered)
        self.assertIn("PASSWORD = s3cret!pass", rendered)
        self.assertIn("TOPIC_PREFIX = growatt/spf5000es", rendered)
        self.assertIn('HA_DEVICE_NAME = "Growatt SPF 5000 ES"', rendered)
        self.assertIn("CONFIG_INTERVAL_SEC = 600", rendered)
        self.assertIn("STATUS_INTERVAL_SEC = 2", rendered)
        self.assertIn("RECONNECT_ATTEMPTS = 3", rendered)
        self.assertIn("LEVEL = INFO", rendered)

    def test_password_is_present_in_ini_but_not_in_log_helper_output(self) -> None:
        rendered = render_ini_from_option_env(DEFAULT_OPTIONS, DEFAULT_MQTT)
        self.assertIn("s3cret!pass", rendered)
        log_line = f"MQTT broker: {DEFAULT_MQTT['username']}@{DEFAULT_MQTT['host']}:{DEFAULT_MQTT['port']}"
        self.assertNotIn(DEFAULT_MQTT["password"], log_line)

    def test_rejects_newline_injection_in_serial_port(self) -> None:
        options = dict(DEFAULT_OPTIONS)
        options["serial_port"] = "/dev/ttyUSB0\n[EVIL]"
        with self.assertRaises(AssertionError):
            render_ini_from_option_env(options, DEFAULT_MQTT)

    def test_rejects_control_characters_in_device_name(self) -> None:
        options = dict(DEFAULT_OPTIONS)
        options["mqtt_ha_device_name"] = "bad\x01name"
        with self.assertRaises(AssertionError):
            render_ini_from_option_env(options, DEFAULT_MQTT)

    def test_quotes_values_with_spaces(self) -> None:
        options = dict(DEFAULT_OPTIONS)
        options["mqtt_ha_device_name"] = "Growatt SPF 5000 ES"
        rendered = render_ini_from_option_env(options, DEFAULT_MQTT)
        self.assertRegex(rendered, r'HA_DEVICE_NAME = "Growatt SPF 5000 ES"')


if __name__ == "__main__":
    unittest.main()
