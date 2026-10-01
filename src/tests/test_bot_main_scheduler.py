from __future__ import annotations

import threading
import time
from datetime import datetime
from types import SimpleNamespace

import src.bot_main as bot_main


def test_monitor_archive_defers_live_fact_sync_to_postclose(monkeypatch, tmp_path):
    from src.engine import strategy_position_performance_report as performance_report

    monkeypatch.setattr(bot_main, "PROJECT_ROOT", tmp_path)
    forbidden_sync = lambda _date: (_ for _ in ()).throw(
        AssertionError("premature_fact_sync")
    )
    monkeypatch.setattr(
        bot_main, "sync_trade_performance_for_date", forbidden_sync, raising=False
    )
    monkeypatch.setattr(
        performance_report,
        "sync_trade_performance_for_date",
        forbidden_sync,
    )
    calls = []
    monkeypatch.setattr(
        bot_main,
        "run_monitor_snapshot_isolated",
        lambda date: calls.append(("snapshot", date)) or {"trade_review": "snapshot.json"},
    )
    monkeypatch.setattr(
        bot_main,
        "archive_target_date_logs",
        lambda date, paths: calls.append(("archive", date)) or [{"path": "log.gz"}],
    )

    result = bot_main.generate_monitor_archive_job("2026-09-28")

    assert calls == [("snapshot", "2026-09-28"), ("archive", "2026-09-28")]
    assert result["performance_sync"] == {
        "status": "deferred_to_postclose",
        "owner": "threshold_cycle_postclose",
        "reason": "live_pipeline_source_unsealed",
    }
    assert result["snapshots"] == {"trade_review": "snapshot.json"}
    assert result["archived_logs"] == [{"path": "log.gz"}]


def test_daily_report_dispatch_is_nonblocking_and_keeps_heartbeat_progress(
    monkeypatch,
):
    started = threading.Event()
    release = threading.Event()
    heartbeat_writes: list[str] = []

    def slow_report():
        started.set()
        assert release.wait(timeout=2)

    monkeypatch.setattr(bot_main, "generate_daily_report_job", slow_report)
    monkeypatch.setattr(
        bot_main,
        "write_heartbeat",
        lambda name: heartbeat_writes.append(name),
    )

    before = time.monotonic()
    sent = bot_main.dispatch_daily_report_if_due(
        datetime(2026, 7, 28, 8, 45, 0),
        False,
    )
    elapsed = time.monotonic() - before
    for _ in range(3):
        bot_main.write_heartbeat("main_loop")

    assert sent is True
    assert elapsed < 0.25
    assert started.wait(timeout=1)
    assert heartbeat_writes == ["main_loop", "main_loop", "main_loop"]

    release.set()
    thread = bot_main._SCHEDULER_JOB_THREADS.get("daily_report")
    if thread is not None:
        thread.join(timeout=2)


def test_named_scheduler_job_deduplicates_inflight_work(monkeypatch):
    started = threading.Event()
    release = threading.Event()
    call_count = 0

    def slow_job():
        nonlocal call_count
        call_count += 1
        started.set()
        assert release.wait(timeout=2)

    first = bot_main.run_scheduler_job_async("dedupe-test", slow_job)
    assert started.wait(timeout=1)
    second = bot_main.run_scheduler_job_async("dedupe-test", slow_job)

    assert second is first
    assert call_count == 1

    release.set()
    first.join(timeout=2)
    assert not first.is_alive()
    assert "dedupe-test" not in bot_main._SCHEDULER_JOB_THREADS


def test_daily_report_dispatch_runs_only_in_due_minute(monkeypatch):
    dispatched: list[str] = []
    monkeypatch.setattr(
        bot_main,
        "run_scheduler_job_async",
        lambda name, func: dispatched.append(name),
    )

    assert (
        bot_main.dispatch_daily_report_if_due(
            datetime(2026, 7, 28, 8, 44, 59),
            False,
        )
        is False
    )
    assert (
        bot_main.dispatch_daily_report_if_due(
            datetime(2026, 7, 28, 8, 45, 0),
            False,
        )
        is True
    )
    assert (
        bot_main.dispatch_daily_report_if_due(
            datetime(2026, 7, 28, 8, 45, 30),
            True,
        )
        is True
    )
    assert dispatched == ["daily_report"]


def test_monitor_snapshot_runs_in_memory_isolated_light_scope(monkeypatch, tmp_path):
    project_root = tmp_path
    manifest_path = (
        project_root
        / "data"
        / "report"
        / "monitor_snapshots"
        / "manifests"
        / "monitor_snapshot_manifest_2026-07-28_intraday_light.json"
    )
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(
            (
                '{"target_date":"2026-07-28","profile":"intraday_light",'
                '"snapshot_paths":{"trade_review":"/tmp/trade_review.json"}}'
            ),
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(bot_main, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(bot_main.subprocess, "run", fake_run)

    result = bot_main.run_monitor_snapshot_isolated("2026-07-28")

    assert result == {"trade_review": "/tmp/trade_review.json"}
    assert captured["command"] == [
        "systemd-run", "--user", "--scope", "--collect",
        "-p", "MemoryMax=2G", "-p", "MemorySwapMax=512M",
        str(project_root / "deploy" / "run_monitor_snapshot_safe.sh"),
        "2026-07-28",
    ]
    assert captured["cwd"] == project_root
    assert captured["capture_output"] is True
    assert captured["text"] is True
    assert captured["env"]["MONITOR_SNAPSHOT_ASYNC"] == "0"
    assert captured["env"]["MONITOR_SNAPSHOT_FORCE"] == "1"
    assert captured["env"]["MONITOR_SNAPSHOT_PROFILE"] == "intraday_light"
    assert captured["env"]["MONITOR_SNAPSHOT_IO_DELAY_SEC"] == "1.0"
    assert "ALLOW_EXISTING_FULL_BUILD_WITH_BOT" not in captured["env"]


def test_monitor_snapshot_isolated_wrapper_failure_is_not_silent(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(bot_main, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        bot_main.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=9,
            stdout="",
            stderr="worker failed",
        ),
    )

    try:
        bot_main.run_monitor_snapshot_isolated("2026-07-28")
    except RuntimeError as exc:
        assert "exit=9" in str(exc)
        assert "worker failed" in str(exc)
    else:
        raise AssertionError("isolated wrapper failure must be surfaced")


def test_monitor_snapshot_isolated_wrapper_rejects_stale_manifest(
    monkeypatch,
    tmp_path,
):
    manifest_path = (
        tmp_path
        / "data"
        / "report"
        / "monitor_snapshots"
        / "manifests"
        / "monitor_snapshot_manifest_2026-07-28_intraday_light.json"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        (
            '{"target_date":"2026-07-28","profile":"intraday_light",'
            '"snapshot_paths":{"trade_review":"/tmp/stale.json"}}'
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(bot_main, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        bot_main.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="skipped",
            stderr="",
        ),
    )
    monkeypatch.setattr(bot_main.time, "time_ns", lambda: 10**20)

    try:
        bot_main.run_monitor_snapshot_isolated("2026-07-28")
    except RuntimeError as exc:
        assert "manifest is not fresh" in str(exc)
    else:
        raise AssertionError("stale manifest must not close the scheduler job")


def test_error_detection_loop_writes_each_health_report_but_logs_one_incident(monkeypatch):
    from src.engine.error_detectors.base import DetectionResult
    import src.utils.logger as logger
    reports, errors, alerts, heartbeats = [], [], [], []
    failure = DetectionResult('cron_completion', 'cron', 'fail', 'terminal failure')
    class FakeEngine:
        def __init__(self, **kwargs): pass
        def run_all(self): return [failure]
        def build_report(self, results): return {'target_date': '2026-10-02', 'severity': results[0].severity}
        def write_report(self, report): reports.append(report)
    def stop_after_four(_interval):
        if len(reports) == 4: raise KeyboardInterrupt
    monkeypatch.setattr(bot_main, 'ErrorDetectionEngine', FakeEngine)
    monkeypatch.setattr(bot_main, 'write_heartbeat', lambda name: heartbeats.append(name))
    monkeypatch.setattr(bot_main.time, 'sleep', stop_after_four)
    monkeypatch.setattr(logger, 'log_error', errors.append)
    bus = SimpleNamespace(publish=lambda *args: alerts.append(args))
    import pytest
    with pytest.raises(KeyboardInterrupt):
        bot_main.error_detection_loop(60, bus)
    assert len(reports) == len(heartbeats) == 4
    assert all(r['severity'] == 'fail' for r in reports)
    assert errors == ['[ERROR_DETECTION] cron_completion: terminal failure']
    assert len(alerts) == 1 and alerts[0][0] == 'SYSTEM_HEALTH_ALERT'
    assert alerts[0][1]['audience'] == 'ADMIN_ONLY'
