from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import pytest

from src.engine.error_detectors import process_health as process_health_module
from src.engine.error_detectors.process_health import (
    ProcessHealthDetector,
    reset_heartbeat,
    write_heartbeat,
    HEARTBEAT_PATH,
    POSTCLOSE_BOT_ISOLATION_PATH,
)

_ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT = (
    process_health_module._samsung_morning_runtime_contract
)


@pytest.fixture(autouse=True)
def _force_trading_day(monkeypatch, tmp_path):
    monkeypatch.setattr(
        process_health_module, "is_krx_trading_day", lambda target: True
    )
    heartbeat_path = tmp_path / "error_detector_heartbeat.json"
    isolation_path = tmp_path / "postclose_bot_isolation.json"
    monkeypatch.setattr(process_health_module, "HEARTBEAT_PATH", heartbeat_path)
    monkeypatch.setattr(
        process_health_module, "POSTCLOSE_BOT_ISOLATION_PATH", isolation_path
    )
    monkeypatch.setitem(globals(), "HEARTBEAT_PATH", heartbeat_path)
    monkeypatch.setitem(globals(), "POSTCLOSE_BOT_ISOLATION_PATH", isolation_path)
    monkeypatch.setattr(
        process_health_module,
        "_samsung_morning_runtime_contract",
        lambda now: {
            "severity": "pass",
            "status": "not_applicable_test_default",
            "target_date": now.date().isoformat(),
        },
    )
    monkeypatch.setattr(
        process_health_module,
        "_pid_cmdline_contains_bot_main",
        lambda pid: True,
    )


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

    def test_detector_fails_when_samsung_expected_runtime_fails(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module,
            "_samsung_morning_runtime_contract",
            lambda now: {
                "severity": "fail",
                "status": "expected_process_not_healthy",
                "reason": "exact_date_authority_missing_or_stale",
            },
        )
        write_heartbeat("main_loop")
        write_heartbeat("telegram")

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert "Samsung morning" in result.summary
        assert result.details["samsung_morning_runtime"]["reason"] == (
            "exact_date_authority_missing_or_stale"
        )

    def test_detector_preserves_concurrent_main_and_samsung_failures(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module,
            "_samsung_morning_runtime_contract",
            lambda now: {
                "severity": "fail",
                "status": "expected_process_not_healthy",
                "reason": "exact_date_authority_missing_or_stale",
            },
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert "Heartbeat file not found" in result.summary
        assert "Samsung morning expected runtime" in result.summary

    def test_detector_fails_immediately_when_thread_reports_stopped(self):
        write_heartbeat("main_loop")
        write_heartbeat("sniper_engine", alive=False)

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["stopped_threads"] == ["sniper_engine"]
        assert result.details["thread_status"] == "stale"
        assert "sniper_engine" in result.summary

    def test_detector_passes_for_sniper_normal_market_close(self, monkeypatch):
        now = (
            datetime.now()
            .astimezone()
            .replace(hour=20, minute=0, second=3, microsecond=0)
        )
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        write_heartbeat("main_loop")
        write_heartbeat(
            "sniper_engine",
            alive=False,
            terminal_reason="market_close",
        )
        # The finalizer writes alive=False once more without knowing the
        # branch reason. The explicit normal terminal marker must survive.
        write_heartbeat("sniper_engine", alive=False)
        state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        state["main_loop"]["last_beat"] = now.isoformat(timespec="seconds")
        state["threads"]["sniper_engine"]["last_beat"] = now.isoformat(
            timespec="seconds"
        )
        HEARTBEAT_PATH.write_text(json.dumps(state), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["thread_status"] == "expected_terminal"
        assert result.details["expected_stopped_threads"] == ["sniper_engine"]
        assert result.details["thread_terminal_reason"]["sniper_engine"] == (
            "market_close"
        )
        assert "sniper_engine" in result.summary

    def test_detector_rejects_market_close_reason_before_cutoff(self, monkeypatch):
        now = (
            datetime.now()
            .astimezone()
            .replace(hour=19, minute=59, second=59, microsecond=0)
        )
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        write_heartbeat("main_loop")
        write_heartbeat(
            "sniper_engine",
            alive=False,
            terminal_reason="market_close",
        )
        state = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))
        state["main_loop"]["last_beat"] = now.isoformat(timespec="seconds")
        state["threads"]["sniper_engine"]["last_beat"] = now.isoformat(
            timespec="seconds"
        )
        HEARTBEAT_PATH.write_text(json.dumps(state), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["stopped_threads"] == ["sniper_engine"]

    def test_detector_rejects_prior_date_market_close_terminal(self, monkeypatch):
        now = (
            datetime.now()
            .astimezone()
            .replace(hour=20, minute=1, second=0, microsecond=0)
        )
        prior = now - timedelta(days=1)
        monkeypatch.setattr(process_health_module.time, "time", now.timestamp)
        HEARTBEAT_PATH.write_text(
            json.dumps(
                {
                    "main_loop": {
                        "last_beat": now.isoformat(timespec="seconds"),
                        "pid": os.getpid(),
                    },
                    "threads": {
                        "sniper_engine": {
                            "last_beat": prior.isoformat(timespec="seconds"),
                            "alive": False,
                            "terminal_reason": "market_close",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["stopped_threads"] == ["sniper_engine"]

    def test_live_heartbeat_clears_prior_terminal_reason(self):
        write_heartbeat(
            "sniper_engine",
            alive=False,
            terminal_reason="market_close",
        )
        write_heartbeat("sniper_engine")

        data = json.loads(HEARTBEAT_PATH.read_text(encoding="utf-8"))

        assert data["threads"]["sniper_engine"]["alive"] is True
        assert "terminal_reason" not in data["threads"]["sniper_engine"]

    def test_detector_fail_when_no_heartbeat(self, monkeypatch):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        detector = ProcessHealthDetector()
        result = detector.check()
        assert result.severity == "fail"
        assert "not found" in result.summary.lower()

    def test_detector_fail_when_main_loop_stale(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
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

    def test_detector_pass_when_no_heartbeat_outside_expected_runtime(
        self, monkeypatch
    ):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: False
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["main_loop_status"] == "expected_stopped"

    def test_detector_pass_when_pid_dead_outside_expected_runtime(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: False
        )
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
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["main_loop_status"] == "startup_not_observed"
        assert "prior-run PID" in result.summary
        assert "PREOPEN handoff" in result.recommended_action

    def test_detector_keeps_dead_current_run_pid_classification(self, monkeypatch):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
        data = {
            "main_loop": {
                "last_beat": datetime.now().astimezone().isoformat(timespec="seconds"),
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")
        monkeypatch.setattr(
            process_health_module.ProcessHealthDetector,
            "restart_grace_sec",
            property(lambda self: 0),
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "fail"
        assert result.details["main_loop_status"] == "pid_dead"
        assert "no longer alive" in result.summary

    def test_detector_passes_when_pid_dead_during_postclose_bot_isolation(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
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
                    "started_at": datetime.now()
                    .astimezone()
                    .isoformat(timespec="seconds"),
                }
            ),
            encoding="utf-8",
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "pass"
        assert result.details["main_loop_status"] == "postclose_isolation_pid_dead"
        assert result.details["postclose_bot_isolation"]["reason"] == (
            "threshold_cycle_postclose_resource_isolation"
        )
        assert "No immediate restart" in result.recommended_action
        assert "stop/isolation" in result.recommended_action

    def test_detector_fail_when_postclose_bot_isolation_marker_is_stale(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
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
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 600.0
        )
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
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 1.0
        )
        data = {
            "main_loop": {
                "last_beat": "2000-01-01T00:00:00+00:00",
                "pid": 99999999,
            }
        }
        HEARTBEAT_PATH.write_text(json.dumps(data), encoding="utf-8")

        result = ProcessHealthDetector().check()

        assert result.severity == "warning"
        assert result.details["main_loop_status"] == "startup_grace_prior_run_heartbeat"
        assert "prior-run PID" in result.summary

    def test_detector_warns_for_missing_heartbeat_during_startup_grace(
        self, monkeypatch
    ):
        if HEARTBEAT_PATH.exists():
            HEARTBEAT_PATH.unlink()
        monkeypatch.setattr(
            process_health_module, "_is_bot_expected_running", lambda: True
        )
        monkeypatch.setattr(
            process_health_module, "_seconds_since_expected_start", lambda: 30.0
        )

        result = ProcessHealthDetector().check()

        assert result.severity == "warning"
        assert result.details["main_loop_status"] == "startup_grace_waiting"


def _mock_samsung_systemd_states(
    monkeypatch, *, live: dict, preflight: dict | None = None
):
    states = {
        process_health_module._SAMSUNG_MORNING_TIMER_UNIT: {
            "LoadState": "loaded",
            "UnitFileState": "enabled",
            "ActiveState": "active",
            "SubState": "waiting",
            "Result": "success",
            "Triggers": process_health_module._SAMSUNG_MORNING_LIVE_UNIT,
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
        process_health_module._SAMSUNG_MORNING_PREFLIGHT_UNIT: preflight
        or {
            "LoadState": "loaded",
            "User": "ubuntu",
            "Group": "ubuntu",
            "ActiveState": "activating",
            "SubState": "start",
            "Result": "success",
            "MainPID": 15132,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:00 KST",
        },
        process_health_module._SAMSUNG_MORNING_LIVE_UNIT: live,
    }
    states[process_health_module._SAMSUNG_MORNING_PREFLIGHT_UNIT].setdefault(
        "User", "ubuntu"
    )
    states[process_health_module._SAMSUNG_MORNING_PREFLIGHT_UNIT].setdefault(
        "Group", "ubuntu"
    )
    states[process_health_module._SAMSUNG_MORNING_LIVE_UNIT].setdefault(
        "User", "ubuntu"
    )
    states[process_health_module._SAMSUNG_MORNING_LIVE_UNIT].setdefault(
        "Group", "ubuntu"
    )
    monkeypatch.setattr(
        process_health_module,
        "_systemd_unit_state",
        lambda unit: {"unit": unit, **states[unit]},
    )


def _write_samsung_authority(path, *, target_date: str, ready: bool):
    path.write_text(
        json.dumps(
            {
                "schema": process_health_module._SAMSUNG_MORNING_AUTHORITY_SCHEMA,
                "target_date": target_date,
                "status": "ready" if ready else "blocked",
                "observed_at_kst": f"{target_date}T07:57:00+09:00",
                "valid_until_kst": f"{target_date}T23:59:59+09:00",
                "decision_authority": (
                    "explicit_user_directed_morning_two_episode_live_start"
                ),
                "source_quality_gate": "PASS",
                "runtime_effect": True,
                "actual_order_submitted": False,
                "broker_order_forbidden": False,
                "policy": {
                    "symbol": "005930",
                    "quantity": 20,
                    "allocation": (
                        "ten_shares_base_limit_and_ten_shares_base_plus_1tick"
                    ),
                    "maximum_episodes_per_day": 2,
                    "unfilled_target": "hold_position_without_forced_exit",
                },
                "rollback": {
                    "action": (
                        "fail_closed_and_disable_only_morning_two_leg_timer_and_services"
                    ),
                    "widget_service_effect": "none",
                },
                "decision": {
                    "ready": ready,
                    "target_date": target_date,
                    "main_bot_active": ready,
                    "main_bot_runtime_env_verified": ready,
                    "main_bot_pid": 14307 if ready else 0,
                    "shared_token_available": ready,
                    "operator_exclusion_source": "manual_operator" if ready else "",
                    "prior_reentry_state_clear": ready,
                    "parallel_widget_trading_allowed": True,
                    "independent_order_ledger_required": True,
                    "blockers": [] if ready else ["blocked"],
                },
            }
        ),
        encoding="utf-8",
    )


def test_samsung_runtime_warns_before_acceptance_deadline(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-01", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:04:59+09:00")
    )

    assert result["severity"] == "warning"
    assert result["status"] == "bounded_wait"
    assert result["reason"] == "exact_date_authority_missing_or_stale"


def test_samsung_runtime_fails_at_acceptance_deadline(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-01", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["status"] == "expected_process_not_healthy"
    assert result["reason"] == "exact_date_authority_missing_or_stale"


def test_samsung_runtime_passes_with_exact_authority_and_live_pid(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
        preflight={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:00 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "pass"
    assert result["status"] == "healthy_active"


def test_samsung_runtime_rejects_corrupt_authority_schema(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    payload = json.loads(authority_path.read_text(encoding="utf-8"))
    payload["schema"] = "stale_schema"
    authority_path.write_text(json.dumps(payload), encoding="utf-8")
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "exact_date_authority_schema_invalid"


def test_samsung_runtime_rejects_authority_policy_drift(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    payload = json.loads(authority_path.read_text(encoding="utf-8"))
    payload["policy"]["quantity"] = 21
    authority_path.write_text(json.dumps(payload), encoding="utf-8")
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "exact_date_authority_policy_invalid"


def test_samsung_runtime_rejects_prior_date_terminal_result(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Tue 2026-09-01 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "morning_live_service_not_started"


def test_samsung_runtime_rejects_dead_bound_main_bot_pid(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    monkeypatch.setattr(
        process_health_module,
        "_pid_cmdline_contains_bot_main",
        lambda pid: False,
    )
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "exact_date_authority_main_bot_pid_inactive"


def test_samsung_terminal_success_survives_planned_main_bot_shutdown(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    monkeypatch.setattr(
        process_health_module,
        "_pid_cmdline_contains_bot_main",
        lambda pid: False,
    )
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
        preflight={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:00 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T21:55:00+09:00")
    )

    assert result["severity"] == "pass"
    assert result["status"] == "one_shot_completed"


def test_samsung_runtime_fails_immediately_for_explicit_preflight_failure(
    monkeypatch, tmp_path
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=False)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "inactive",
            "SubState": "dead",
            "Result": "success",
            "MainPID": 0,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "",
        },
        preflight={
            "LoadState": "loaded",
            "ActiveState": "failed",
            "SubState": "failed",
            "Result": "failed",
            "MainPID": 0,
            "ExecMainStatus": 3,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:00 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:00:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "morning_preflight_failed"


def test_samsung_runtime_rejects_installed_credential_drift(monkeypatch, tmp_path):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "User": "ubuntu",
            "Group": "www-data",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == "morning_service_credential_contract_mismatch"


@pytest.mark.parametrize(
    ("timer_change", "expected_reason"),
    [
        ({"UnitFileState": "disabled"}, "morning_timer_not_enabled"),
        (
            {"Triggers": "wrong-owner.service"},
            "morning_timer_trigger_contract_mismatch",
        ),
    ],
)
def test_samsung_runtime_rejects_timer_install_contract_drift(
    monkeypatch, tmp_path, timer_change, expected_reason
):
    authority_path = tmp_path / "authority.json"
    monkeypatch.setattr(
        process_health_module, "SAMSUNG_MORNING_AUTHORITY_PATH", authority_path
    )
    _write_samsung_authority(authority_path, target_date="2026-09-02", ready=True)
    _mock_samsung_systemd_states(
        monkeypatch,
        live={
            "LoadState": "loaded",
            "ActiveState": "active",
            "SubState": "running",
            "Result": "success",
            "MainPID": 15555,
            "ExecMainStatus": 0,
            "ExecMainStartTimestamp": "Wed 2026-09-02 07:57:01 KST",
        },
    )
    original_state = process_health_module._systemd_unit_state

    def changed_state(unit):
        state = original_state(unit)
        if unit == process_health_module._SAMSUNG_MORNING_TIMER_UNIT:
            state.update(timer_change)
        return state

    monkeypatch.setattr(process_health_module, "_systemd_unit_state", changed_state)

    result = _ORIGINAL_SAMSUNG_MORNING_RUNTIME_CONTRACT(
        datetime.fromisoformat("2026-09-02T08:05:00+09:00")
    )

    assert result["severity"] == "fail"
    assert result["reason"] == expected_reason
