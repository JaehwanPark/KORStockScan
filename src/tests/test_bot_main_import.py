import importlib
import inspect
import os
import runpy
import sys

import pytest


def test_bot_main_import_does_not_install_runtime_side_effects():
    sys.modules.pop("src.bot_main", None)
    preloaded = set(sys.modules)
    before_stdout = sys.stdout
    before_stderr = sys.stderr

    module = importlib.import_module("src.bot_main")

    loaded_by_import = set(sys.modules) - preloaded
    assert sys.stdout is before_stdout
    assert sys.stderr is before_stderr
    assert "src.notify.telegram_manager" not in loaded_by_import
    assert "src.engine.kiwoom_sniper_v2" not in loaded_by_import
    assert callable(module.install_dual_logger)


def test_bot_main_import_clears_retired_inherited_runtime_authority(monkeypatch):
    monkeypatch.setenv("KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE",
        "2026-08-28",
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC", "2"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC", "5"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS",
        "10",
    )
    sys.modules.pop("src.bot_main", None)

    module = importlib.import_module("src.bot_main")

    assert "KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED" not in os.environ
    assert (
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED" not in os.environ
    )
    assert (
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE"
        not in os.environ
    )
    assert (
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC"
        not in os.environ
    )
    assert (
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC"
        not in os.environ
    )
    assert (
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS"
        not in os.environ
    )
    assert module._RETIRED_RUNTIME_ENV_CLEARED_AT_STARTUP == (
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ACTIVE_DATE",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_ENABLED",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_MIN_WAIT_SEC",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_SPREAD_WORSEN_BPS",
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_DIRECT_CANARY_RECHECK_TTL_SEC",
        "KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED",
    )
    source = inspect.getsource(module)
    assert (
        'if __name__ == "__main__" and _RETIRED_RUNTIME_ENV_CLEARED_AT_STARTUP'
        in source
    )
    assert "os.execve(" in source


def test_bot_main_script_reexecs_with_sanitized_runtime_env(monkeypatch):
    captured = {}

    def fake_execve(executable, argv, environ):
        captured.update(
            {
                "executable": executable,
                "argv": tuple(argv),
                "environ": dict(environ),
            }
        )
        raise SystemExit(0)

    monkeypatch.setenv("KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED", "true")
    monkeypatch.setattr(os, "execve", fake_execve)

    with pytest.raises(SystemExit, match="0"):
        runpy.run_path("src/bot_main.py", run_name="__main__")

    assert captured["executable"] == sys.executable
    assert captured["argv"][0] == sys.executable
    assert "KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED" not in captured["environ"]


def test_morning_recommendation_broadcast_scheduler_is_removed():
    module = importlib.import_module("src.bot_main")
    source = inspect.getsource(module)

    assert not hasattr(module, "broadcast_today_picks_job")
    assert "morning_report_sent" not in source
    assert "now.hour == 8 and now.minute == 50" not in source
    assert "AI KOSPI 종목추천 리포트" not in source
    assert "초단타(SCALP) 포착 대기열" not in source
