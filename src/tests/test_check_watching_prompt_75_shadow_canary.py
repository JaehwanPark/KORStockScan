from pathlib import Path

from src.engine.check_watching_prompt_75_shadow_canary import _evaluate_status


def test_evaluate_status_fails_when_bot_or_env_missing():
    status, failures, warnings = _evaluate_status(
        {
            "bot_running": False,
            "tmux_bot_session": False,
            "shadow_env": {"enabled": False},
            "pipeline": {"exists": False},
        },
        {
            "require_bot": True,
            "require_shadow_env": True,
            "require_pipeline_file": True,
            "max_pipeline_stale_min": 20,
        },
    )

    assert status == "fail"
    assert "bot_main.py not running" in failures
    assert "shadow env not enabled in bot runtime" in failures
    assert "pipeline_events file missing" in failures
    assert "tmux bot session not detected" in warnings


def test_evaluate_status_warns_when_collection_not_started_yet():
    status, failures, warnings = _evaluate_status(
        {
            "bot_running": True,
            "tmux_bot_session": True,
            "shadow_env": {"enabled": True},
            "pipeline": {
                "exists": True,
                "stale_minutes": 5,
                "entry_events": 12,
                "ai_confirmed": 4,
                "shadow_rows": 0,
            },
        },
        {
            "require_bot": True,
            "require_shadow_env": True,
            "require_pipeline_file": True,
            "max_pipeline_stale_min": 20,
        },
    )

    assert status == "warning"
    assert failures == []
    assert "ai_confirmed exists but shadow_rows still 0" in warnings


def test_evaluate_status_ok_when_runtime_and_collection_are_fresh():
    status, failures, warnings = _evaluate_status(
        {
            "bot_running": True,
            "tmux_bot_session": True,
            "shadow_env": {"enabled": True},
            "pipeline": {
                "exists": True,
                "stale_minutes": 3,
                "entry_events": 30,
                "ai_confirmed": 7,
                "shadow_rows": 2,
            },
        },
        {
            "require_bot": True,
            "require_shadow_env": True,
            "require_pipeline_file": True,
            "max_pipeline_stale_min": 20,
        },
    )

    assert status == "ok"
    assert failures == []
    assert warnings == []
