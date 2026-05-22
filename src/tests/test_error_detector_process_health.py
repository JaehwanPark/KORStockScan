from __future__ import annotations

import json
import os
import time
from pathlib import Path
from datetime import datetime

import pytest

from src.engine.error_detectors import process_health as process_health_module
from src.engine.error_detectors.process_health import (
    ProcessHealthDetector,
    reset_heartbeat,
    write_heartbeat,
    HEARTBEAT_PATH,
    POSTCLOSE_BOT_ISOLATION_PATH,
)


@pytest.fixture(autouse=True)
def _force_trading_day(monkeypatch):
    monkeypatch.setattr(process_health_module, "is_krx_trading_day", lambda target: True)


class TestProcessHealthDetector:
    def setup_method(self):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        if POSTCLOSE_BOT_ISOLATION_PATH.exists():
            POSTCLOSE_BOT_ISOLATION_PATH.unlink()

    def teardown_method(self):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        if POSTCLOSE_BOT_ISOLATION_PATH.exists():
            POSTCLOSE_BOT_ISOLATION_PATH.unlink()

    def test_heartbeat_write_main_loop(self):
        write_heartbeat("main_loop")
        assert HEARTBEAT_PATH.exists()
        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        assert "main_loop" in data
        assert "last_beat" in data["main_loop"]
        assert data["main_loop"]["pid"] == os.getpid()

    def test_heartbeat_write_thread(self):
        write_heartbeat("telegram")
        assert HEARTBEAT_PATH.exists()
        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        assert "threads" in data
        assert "telegram" in data["threads"]
        assert data["threads"]["telegram"]["alive"] is True

    def test_heartbeat_append_thread(self):
        write_heartbeat("main_loop")
        write_heartbeat("crisis_monitor")
        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        assert "main_loop" in data
        assert "crisis_monitor" in data["threads"]

    def test_reset_heartbeat_discards_stale_threads(self):
        write_heartbeat("main_loop")
        write_heartbeat("scalping_scanner")
        reset_heartbeat()
        write_heartbeat("main_loop")
        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        assert "main_loop" in data
        assert "scalping_scanner" not in data.get("threads", {})

    def test_detector_pass_when_heartbeat_fresh(self):
        write_heartbeat("main_loop")
        write_heartbeat("telegram")
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "pass"

    def test_detector_fail_when_no_heartbeat(self):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "fail"
        assert "not found" in result.summary.lower()

    def test_detector_fail_when_main_loop_stale(self):
        write_heartbeat("main_loop")
        stale_data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": os.getpid(),
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(stale_data), encoding="utf-8")
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "fail"
        assert "stale" in result.summary.lower()

    def test_detector_warning_when_no_threads(self):
        data = {
            "main_loop": {
                "last_beat": datetime.now().astimezone().isoformat(timespec="seconds"),
                "pid": os.getpid(),
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "warning"

    def test_detector_pass_when_no_heartbeat_outside_expected_runtime(self, monkeypatch):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        monkeypatch.setattr(process_health_module, "_is_bot_expected_running", lambda: False)

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["main_loop_status"] == "expected_stopped"

    def test_detector_pass_when_pid_dead_outside_expected_runtime(self, monkeypatch):
        monkeypatch.setattr(process_health_module, "_is_bot_expected_running", lambda: False)
        data = {
            "main_loop": {
                "last_beat": datetime.now().astimezone().isoformat(timespec="seconds"),
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["main_loop_status"] == "pid_dead"

    def test_detector_fail_when_pid_dead_inside_expected_runtime(self, monkeypatch):
        monkeypatch.setattr(process_health_module, "_is_bot_expected_running", lambda: True)
        monkeypatch.setattr(process_health_module, "_seconds_since_expected_start", lambda: 600.0)
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert "no longer alive" in result.summary

    def test_detector_warns_when_pid_dead_during_postclose_bot_isolation(self, monkeypatch):
        monkeypatch.setattr(process_health_module, "_is_bot_expected_running", lambda: True)
        monkeypatch.setattr(process_health_module, "_seconds_since_expected_start", lambda: 600.0)
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")
        POSTCLOSE_BOT_ISOLATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        POSTCLOSE_BOT_ISOLATION_PATH.write_text(
            json.dumps(
                {
                    "active": True,
                    "target_date": "2026-05-22",
                    "session": "bot",
                    "action": "restart",
                    "reason": "threshold_cycle_postclose_resource_isolation",
                    "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                }
            ),
            encoding="utf-8",
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "warning"
        assert result.details["main_loop_status"] == "postclose_isolation_pid_dead"
        assert result.details["postclose_bot_isolation"]["reason"] == (
            "threshold_cycle_postclose_resource_isolation"
        )
        assert "No immediate restart" in result.recommended_action

    def test_detector_fail_when_postclose_bot_isolation_marker_is_stale(self, monkeypatch):
        monkeypatch.setattr(process_health_module, "_is_bot_expected_running", lambda: True)
        monkeypatch.setattr(process_health_module, "_seconds_since_expected_start", lambda: 600.0)
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")
        POSTCLOSE_BOT_ISOLATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        POSTCLOSE_BOT_ISOLATION_PATH.write_text(
            json.dumps(
                {
                    "active": True,
                    "target_date": "2026-05-22",
                    "session": "bot",
                    "action": "restart",
                    "reason": "threshold_cycle_postclose_resource_isolation",
                    "started_at": "2000-01-01T00:00:00+00:00",
                }
            ),
            encoding="utf-8",
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert "postclose_bot_isolation" not in result.details

    def test_detector_warns_for_dead_pid_during_restart_grace(self, monkeypatch):
        monkeypatch.setattr(process_health_module, "_is_bot_expected_running", lambda: True)
        monkeypatch.setattr(process_health_module, "_seconds_since_expected_start", lambda: 600.0)
        data = {
            "main_loop": {
                "last_beat": datetime.now().astimezone().isoformat(timespec="seconds"),
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "warning"
        assert result.details["main_loop_status"] == "restart_grace_pid_handoff"
        assert "restart grace" in result.summary

    def test_detector_warns_for_dead_startup_pid_during_grace(self, monkeypatch):
        monkeypatch.setattr(process_health_module, "_is_bot_expected_running", lambda: True)
        monkeypatch.setattr(process_health_module, "_seconds_since_expected_start", lambda: 1.0)
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "warning"
        assert result.details["main_loop_status"] == "pid_dead"
        assert "startup grace" in result.summary

    def test_detector_warns_for_missing_heartbeat_during_startup_grace(self, monkeypatch):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        monkeypatch.setattr(process_health_module, "_is_bot_expected_running", lambda: True)
        monkeypatch.setattr(process_health_module, "_seconds_since_expected_start", lambda: 30.0)

        result = ProcessHealthDetector().check()

        assert result.severity == "warning"
        assert result.details["main_loop_status"] == "startup_grace_waiting"
