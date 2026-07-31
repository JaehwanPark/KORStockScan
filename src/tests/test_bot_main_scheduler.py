from __future__ import annotations

import threading
import time
from datetime import datetime
from types import SimpleNamespace

import src.bot_main as bot_main


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


def test_monitor_snapshot_runs_in_resource_isolated_wrapper(monkeypatch, tmp_path):
    project_root = tmp_path
    manifest_path = (
        project_root
        / "data"
        / "report"
        / "monitor_snapshots"
        / "manifests"
        / "monitor_snapshot_manifest_2026-07-28_full.json"
    )
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(
            (
                '{"target_date":"2026-07-28","profile":"full",'
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
        str(project_root / "deploy" / "run_monitor_snapshot_safe.sh"),
        "2026-07-28",
    ]
    assert captured["cwd"] == project_root
    assert captured["capture_output"] is True
    assert captured["text"] is True
    assert captured["env"]["MONITOR_SNAPSHOT_ASYNC"] == "0"
    assert captured["env"]["MONITOR_SNAPSHOT_FORCE"] == "1"
    assert captured["env"]["MONITOR_SNAPSHOT_PROFILE"] == "full"
    assert captured["env"]["MONITOR_SNAPSHOT_IO_DELAY_SEC"] == "1.0"
    assert captured["env"]["ALLOW_EXISTING_FULL_BUILD_WITH_BOT"] == "1"


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
        / "monitor_snapshot_manifest_2026-07-28_full.json"
    )
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        (
            '{"target_date":"2026-07-28","profile":"full",'
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
