from __future__ import annotations

import threading
import time
from datetime import datetime

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
