from __future__ import annotations

import threading
import time
from datetime import datetime
from types import SimpleNamespace
import pytest

import src.bot_main as bot_main


def test_first_health_waits_for_current_consumption_without_blocking_main_engine(
    monkeypatch,
):
    import src.utils.logger as logger

    ready = threading.Event()
    visited, heartbeats, logs = [], [], []
    clock = [10.0]

    def check(identity):
        visited.append("check")
        return dict(status="ready" if ready.is_set() else "pending")

    def wait(seconds):
        # The first sweep owns a wait, not Main engine initialization.
        visited.append("engine_started")
        ready.set()
        clock[0] += seconds

    monkeypatch.setattr(logger, "log_info", logs.append)
    result = bot_main._await_startup_consumption(
        dict(process_started_monotonic=0.0),
        check=check,
        monotonic=lambda: clock[0],
        wait=wait,
        heartbeat=lambda: heartbeats.append(clock[0]),
    )
    assert result["status"] == "ready" and visited == [
        "check",
        "engine_started",
        "check",
    ]
    assert len(logs) == 1 and len(heartbeats) == 1


def test_first_health_deadline_uses_original_process_start_and_keeps_heartbeat(
    monkeypatch,
):
    import src.utils.logger as logger

    clock, heartbeats, waits = [140.0], [], []
    monkeypatch.setattr(logger, "log_info", lambda message: None)

    def wait(seconds):
        waits.append(seconds)
        clock[0] += seconds

    result = bot_main._await_startup_consumption(
        dict(process_started_monotonic=0.0),
        check=lambda identity: dict(status="pending"),
        monotonic=lambda: clock[0],
        wait=wait,
        heartbeat=lambda: heartbeats.append(clock[0]),
    )
    assert (
        result["status"] == "failed"
        and result["reason"] == "startup_consumption_deadline_expired"
    )
    assert sum(waits) == 10.0 and heartbeats == [140.0, 145.0, 150.0]
    assert result["waited_seconds"] == 10.0


def test_invalid_startup_receipt_does_not_wait_for_timeout():
    result = bot_main._await_startup_consumption(
        dict(process_started_monotonic=0.0),
        check=lambda identity: dict(status="failed", reason="invalid_receipt"),
        monotonic=lambda: 1.0,
        wait=lambda seconds: pytest.fail("invalid input must surface immediately"),
        heartbeat=lambda: None,
    )
    assert result["reason"] == "invalid_receipt" and result["waited_seconds"] == 0.0


def test_receipt_check_cannot_complete_ready_after_original_startup_deadline():
    clock = [149.9]

    def check(identity):
        clock[0] = 150.01
        return dict(status="ready")

    result = bot_main._await_startup_consumption(
        dict(process_started_monotonic=0.0),
        check=check,
        monotonic=lambda: clock[0],
        heartbeat=lambda: None,
        wait=lambda seconds: pytest.fail("no renewed startup wait"),
    )
    assert (
        result["status"] == "failed"
        and result["reason"] == "startup_consumption_deadline_expired"
    )


def test_startup_failure_runs_real_full_checks_and_recovers_only_on_receipt(
    monkeypatch,
):
    from src.engine.error_detectors.base import DetectionResult
    import src.utils.logger as logger

    reports, full_checks, alerts = [], [], []

    class FakeEngine:
        def __init__(self, **kwargs):
            assert kwargs == dict(dry_run=False, mode="full")

        def run_all(self):
            full_checks.append(True)
            return [
                DetectionResult(
                    "process_health", "system", "pass", "processes healthy"
                ),
                DetectionResult(
                    "artifact_freshness", "artifact", "fail", "real current partial"
                ),
            ]

        def build_report(self, results):
            return dict(
                target_date="2026-10-14", summary_severity="fail", results=results
            )

        def write_report(self, report):
            reports.append(report)

    def stop_after_second(interval):
        if len(reports) == 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(bot_main, "ErrorDetectionEngine", FakeEngine)
    monkeypatch.setattr(
        bot_main,
        "_await_startup_consumption",
        lambda identity: dict(
            status="failed", reason="startup_consumption_deadline_expired"
        ),
    )
    monkeypatch.setattr(
        bot_main, "_startup_consumption_check", lambda identity: dict(status="ready")
    )
    monkeypatch.setattr(bot_main, "write_heartbeat", lambda name: None)
    monkeypatch.setattr(bot_main.time, "sleep", stop_after_second)
    monkeypatch.setattr(logger, "log_error", lambda message: None)
    monkeypatch.setattr(logger, "log_info", lambda message: None)
    with pytest.raises(KeyboardInterrupt):
        bot_main.error_detection_loop(
            60,
            SimpleNamespace(publish=lambda *args: alerts.append(args)),
            startup_identity={"fixture": True},
        )
    assert len(full_checks) == 2
    assert reports[0]["results"][0].severity == "fail"
    assert (
        reports[0]["results"][0].details["startup_consumption"]["reason"]
        == "startup_consumption_deadline_expired"
    )
    assert reports[1]["results"][0].severity == "pass"
    assert all(
        report["results"][1].summary == "real current partial" for report in reports
    )
    assert all(report["results"][1].severity == "fail" for report in reports)
    assert reports[1]["startup_consumption"]["status"] == "ready"
    assert all(
        datetime.fromisoformat(report["health_sweep_started_at_kst"])
        .utcoffset()
        .total_seconds()
        == 9 * 3600
        for report in reports
    )


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
        lambda date: calls.append(("snapshot", date))
        or {"trade_review": "snapshot.json"},
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
        "systemd-run",
        "--user",
        "--scope",
        "--collect",
        "-p",
        "MemoryMax=2G",
        "-p",
        "MemorySwapMax=512M",
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


def test_error_detection_loop_writes_each_health_report_but_logs_one_incident(
    monkeypatch,
):
    from src.engine.error_detectors.base import DetectionResult
    import src.utils.logger as logger

    reports, errors, alerts, heartbeats = [], [], [], []
    failure = DetectionResult("cron_completion", "cron", "fail", "terminal failure")

    class FakeEngine:
        def __init__(self, **kwargs):
            pass

        def run_all(self):
            return [failure]

        def build_report(self, results):
            return {"target_date": "2026-10-02", "severity": results[0].severity}

        def write_report(self, report):
            reports.append(report)

    def stop_after_four(_interval):
        if len(reports) == 4:
            raise KeyboardInterrupt

    monkeypatch.setattr(bot_main, "ErrorDetectionEngine", FakeEngine)
    monkeypatch.setattr(
        bot_main, "write_heartbeat", lambda name: heartbeats.append(name)
    )
    monkeypatch.setattr(bot_main.time, "sleep", stop_after_four)
    monkeypatch.setattr(logger, "log_error", errors.append)
    bus = SimpleNamespace(publish=lambda *args: alerts.append(args))
    import pytest

    with pytest.raises(KeyboardInterrupt):
        bot_main.error_detection_loop(60, bus)
    assert len(reports) == len(heartbeats) == 4
    assert all(r["severity"] == "fail" for r in reports)
    assert errors == ["[ERROR_DETECTION] cron_completion: terminal failure"]
    assert len(alerts) == 1 and alerts[0][0] == "SYSTEM_HEALTH_ALERT"
    assert alerts[0][1]["audience"] == "ADMIN_ONLY"


@pytest.mark.parametrize("producer", [0, 1, 75])
def test_startup_observer_uses_existing_owners_and_no_notification(
    tmp_path, monkeypatch, producer
):
    (tmp_path / "tmp").mkdir()
    calls = []

    class Child:
        def __init__(self, args, **kwargs):
            calls.append((args, kwargs))
            self.returncode = producer if len(calls) == 1 else 0

        def poll(self):
            return self.returncode

    monkeypatch.setattr(bot_main.subprocess, "Popen", Child)
    monkeypatch.setattr(
        bot_main, "_startup_consumption_check", lambda identity: dict(status="ready")
    )
    identity = dict(
        process_started_monotonic=0.0,
        workspace=tmp_path,
        release_root=tmp_path,
        target_date="2026-10-16",
        pid=123,
    )
    result = bot_main._refresh_startup_observer(
        identity, monotonic=lambda: 30.0, heartbeat=lambda: None
    )
    assert result["status"] == "attempted" and result["producer_exit"] == producer
    assert "src.engine.buy_funnel_sentinel" in calls[0][0]
    assert "--submission-monitor-source" in calls[0][0]
    assert "src.engine.monitoring.submission_bottleneck_monitor" in calls[1][0]
    assert ("--source-only" in calls[1][0]) == bool(producer)
    assert all(
        "--notify" not in args and opts["start_new_session"] for args, opts in calls
    )


def test_startup_observer_busy_or_expired_never_starts_unowned_child(
    tmp_path, monkeypatch
):
    import fcntl

    (tmp_path / "tmp").mkdir()
    identity = dict(
        process_started_monotonic=0.0,
        workspace=tmp_path,
        release_root=tmp_path,
        target_date="2026-10-16",
        pid=123,
    )
    monkeypatch.setattr(
        bot_main.subprocess,
        "Popen",
        lambda *a, **k: pytest.fail("no child after deadline"),
    )
    with (tmp_path / "tmp/run_buy_funnel_sentinel.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = bot_main._refresh_startup_observer(
            identity, monotonic=lambda: 130.0, heartbeat=lambda: None
        )
    assert result["reason"] == "startup_observer_owner_busy"


@pytest.mark.parametrize("elapsed", [104.5, 110.0, 125.0])
def test_startup_observer_unstarted_producer_cannot_replace_completed_report(
    tmp_path, monkeypatch, elapsed
):
    (tmp_path / "tmp").mkdir()
    report = (
        tmp_path
        / "data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json"
    )
    report.parent.mkdir(parents=True)
    original = b'{"execution_status":"completed","execution_mode":"full","run_id":"current-pid"}\n'
    report.write_bytes(original)
    identity = dict(
        process_started_monotonic=0.0,
        workspace=tmp_path,
        release_root=tmp_path,
        target_date="2026-10-19",
        pid=123,
    )
    monkeypatch.setattr(
        bot_main, "_startup_consumption_check", lambda identity: dict(status="ready")
    )
    monkeypatch.setattr(
        bot_main.subprocess,
        "Popen",
        lambda *a, **k: pytest.fail("no source-only child for unstarted producer"),
    )
    result = bot_main._refresh_startup_observer(
        identity, monotonic=lambda: elapsed, heartbeat=lambda: None
    )
    assert (
        result["status"] == "failed"
        and result["reason"] == "startup_observer_deadline_expired"
    )
    assert (
        result["producer_started"] is False and result["publication_attempted"] is False
    )
    assert report.read_bytes() == original


@pytest.mark.parametrize(
    "producer_seconds,observer_seconds,producer_exit,observer_exit",
    [
        (50.0, 20.0, 0, 0),
        (999.0, 0.0, 75, 0),
        (50.0, 999.0, 0, 75),
    ],
)
def test_startup_source_and_observer_share_original_deadline_after_attestation(
    tmp_path,
    monkeypatch,
    producer_seconds,
    observer_seconds,
    producer_exit,
    observer_exit,
):
    (tmp_path / "tmp").mkdir()
    clock, calls, children, beats, killed = [61.0], [], {}, [], []

    class Child:
        def __init__(self, args, **kwargs):
            calls.append(args)
            self.pid = len(calls)
            self.duration = producer_seconds if self.pid == 1 else observer_seconds
            self.started = clock[0]
            self.returncode = None
            children[self.pid] = self

        def poll(self):
            if self.returncode is None and clock[0] - self.started >= self.duration:
                self.returncode = 0
            return self.returncode

        def wait(self, timeout):
            assert self.returncode is not None
            return self.returncode

    def kill(pid, sig):
        killed.append(pid)
        children[pid].returncode = -int(sig)

    monkeypatch.setattr(bot_main.subprocess, "Popen", Child)
    monkeypatch.setattr(bot_main.os, "killpg", kill)
    monkeypatch.setattr(
        bot_main, "_startup_consumption_check", lambda identity: dict(status="ready")
    )
    identity = dict(
        process_started_monotonic=0.0,
        workspace=tmp_path,
        release_root=tmp_path,
        target_date="2026-10-20",
        pid=123,
    )
    result = bot_main._refresh_startup_observer(
        identity,
        monotonic=lambda: clock[0],
        wait=lambda seconds: clock.__setitem__(0, clock[0] + seconds),
        heartbeat=lambda: beats.append(clock[0]),
    )
    assert result["producer_exit"] == producer_exit
    assert result["observer_exit"] == observer_exit
    assert ("--source-only" in calls[1]) == bool(producer_exit)
    assert (
        clock[0] <= 150.0
        and beats
        and all(b - a <= 5.0 for a, b in zip(beats, beats[1:]))
    )
    assert len(killed) == int(producer_exit == 75) + int(observer_exit == 75)
