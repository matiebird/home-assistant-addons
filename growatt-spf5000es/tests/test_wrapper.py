#!/usr/bin/env python3
"""Deterministic wrapper tests for the Growatt SPF5000ES add-on."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ADDON_ROOT = Path(__file__).resolve().parents[1]
RENDER_SCRIPT = ADDON_ROOT / "render_config.py"
CONFIG_YAML = ADDON_ROOT / "config.yaml"
RUN_SH = ADDON_ROOT / "run.sh"
SERVER_REVISION = "48d262c847c5e35ebe824fed08dd6fc0b483c6bd"

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


def render_ini(options: dict, mqtt: dict) -> str:
    payload = json.dumps({"options": options, "mqtt": mqtt})
    completed = subprocess.run(
        [sys.executable, str(RENDER_SCRIPT)],
        input=payload,
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
        self.assertIn('version: "0.1.0"', text)
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


class RenderConfigTests(unittest.TestCase):
    def test_renders_stock_sections_and_defaults(self) -> None:
        rendered = render_ini(DEFAULT_OPTIONS, DEFAULT_MQTT)
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
        rendered = render_ini(DEFAULT_OPTIONS, DEFAULT_MQTT)
        self.assertIn("s3cret!pass", rendered)
        log_line = f"MQTT broker: {DEFAULT_MQTT['username']}@{DEFAULT_MQTT['host']}:{DEFAULT_MQTT['port']}"
        self.assertNotIn(DEFAULT_MQTT["password"], log_line)

    def test_rejects_newline_injection_in_serial_port(self) -> None:
        options = dict(DEFAULT_OPTIONS)
        options["serial_port"] = "/dev/ttyUSB0\n[EVIL]"
        with self.assertRaises(AssertionError):
            render_ini(options, DEFAULT_MQTT)

    def test_rejects_control_characters_in_device_name(self) -> None:
        options = dict(DEFAULT_OPTIONS)
        options["mqtt_ha_device_name"] = "bad\x01name"
        with self.assertRaises(AssertionError):
            render_ini(options, DEFAULT_MQTT)

    def test_quotes_values_with_spaces(self) -> None:
        options = dict(DEFAULT_OPTIONS)
        options["mqtt_ha_device_name"] = "Growatt SPF 5000 ES"
        rendered = render_ini(options, DEFAULT_MQTT)
        self.assertRegex(rendered, r'HA_DEVICE_NAME = "Growatt SPF 5000 ES"')


if __name__ == "__main__":
    unittest.main()
