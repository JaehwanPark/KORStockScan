from pathlib import Path

from src.engine.collect_remote_latency_baseline import _default_output_paths, _render_markdown


def test_default_output_paths_group_by_date_and_window(tmp_path: Path) -> None:
    json_path, md_path = _default_output_paths(tmp_path, "2026-04-13", "preopen", "20260413_082000")
    assert json_path == tmp_path / "2026-04-13" / "2026-04-13_preopen_20260413_082000.json"
    assert md_path == tmp_path / "2026-04-13" / "2026-04-13_preopen_20260413_082000.md"


def test_render_markdown_contains_key_fields() -> None:
    payload = {
        "collected_at": "2026-04-13T08:20:00+09:00",
        "hostname": "korstock-test-server",
        "bot_running": True,
        "bot_pid": "1234",
        "tmux_bot_session": True,
        "latency_env": {
            "KORSTOCKSCAN_LATENCY_CANARY_PROFILE": "remote_v2",
            "KORSTOCKSCAN_SCALP_LATENCY_GUARD_CANARY_MAX_WS_JITTER_MS": "400",
        },
        "shadow_env": {"AI_WATCHING_75_PROMPT_SHADOW_ENABLED": "true"},
        "pipeline": {
            "exists": True,
            "line_count": 11,
            "entry_pipeline_rows": 3,
            "latency_block_rows": 1,
            "latest_event_at": "2026-04-13 08:21:01",
        },
        "thread_snapshot": ["hdr", "row"],
        "top_snapshot": ["top hdr"],
    }
    text = _render_markdown("preopen", payload)
    assert "Remote Latency Baseline / preopen" in text
    assert "remote_v2" in text
    assert "pipeline_line_count: `11`" in text
    assert "thread_snapshot" not in text.lower()
