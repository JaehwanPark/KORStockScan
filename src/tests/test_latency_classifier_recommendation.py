import json

from src.engine import latency_classifier_recommendation as mod


def _event(code, *, name="REAL", age=100, jitter=0, spread=0.001, quote_stale=False):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "stage": "latency_block",
        "stock_name": name,
        "stock_code": code,
        "record_id": 1,
        "fields": {
            "ws_age_ms": str(age),
            "ws_jitter_ms": str(jitter),
            "spread_ratio": str(spread),
            "quote_stale": str(quote_stale),
            "decision": "REJECT_DANGER",
            "latency": "DANGER",
        },
    }


def test_latency_classifier_recommendation_builds_apply_candidate(tmp_path, monkeypatch):
    event_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report"
    event_dir.mkdir()
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    rows = []
    for idx in range(24):
        rows.append(_event(f"10{idx:04d}", age=800, jitter=900, spread=0.008))
    rows.append(_event("123456", name="TEST", age=800, jitter=900, spread=0.008))
    (event_dir / "pipeline_events_2026-05-18.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    payload = mod.write_report("2026-05-18")

    assert payload["latency_block_count"] == 24
    assert payload["selected_profile_id"] == "balanced_1200_1500_0100"
    candidate = payload["calibration_candidate"]
    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["target_env_keys"] == mod.TARGET_ENV_KEYS
    assert candidate["recommended_values"] == {
        "max_ws_age_ms_for_caution": 1200,
        "max_ws_jitter_ms_for_caution": 1500,
        "max_spread_ratio_for_caution": 0.01,
    }
    assert (report_dir / "latency_classifier_recommendation_2026-05-18.json").exists()
    assert (report_dir / "latency_classifier_recommendation_2026-05-18.md").exists()


def test_latency_classifier_recommendation_holds_when_sample_short(tmp_path, monkeypatch):
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir()
    monkeypatch.setattr(mod, "PIPELINE_EVENT_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    rows = [_event("005950", age=800, jitter=900, spread=0.008) for _ in range(3)]
    (event_dir / "pipeline_events_2026-05-18.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    payload = mod.build_report("2026-05-18")

    assert payload["latency_block_count"] == 3
    assert payload["calibration_candidate"]["calibration_state"] == "hold_sample"
    assert payload["calibration_candidate"]["allowed_runtime_apply"] is False
