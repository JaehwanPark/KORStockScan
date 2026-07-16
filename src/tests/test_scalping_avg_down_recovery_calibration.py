import json
from pathlib import Path

from src.engine.monitoring import scalping_avg_down_recovery_calibration as mod


def _write_event(path: Path, *, stage: str, emitted_at: str, **fields):
    payload = {"stage": stage, "emitted_at": emitted_at, "fields": fields}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _write_good_samples(path: Path, date: str, *, shallow_count: int, deep_count: int):
    for idx in range(shallow_count):
        sim_id = f"{date}-sim-{idx}"
        base_minute = 9 * 60 + idx
        base_time = f"{date}T{base_minute // 60:02d}:{base_minute % 60:02d}:00+09:00"
        future_time = f"{date}T{(base_minute + 10) // 60:02d}:{(base_minute + 10) % 60:02d}:00+09:00"
        common = {"sim_record_id": sim_id, "profit_rate": -0.50}
        _write_event(
            path,
            stage="scalp_sim_pre_submit_liquidity_guard_would_pass",
            emitted_at=base_time,
            **common,
        )
        _write_event(
            path,
            stage="scalp_sim_pre_submit_overbought_guard_would_pass",
            emitted_at=base_time,
            **common,
        )
        _write_event(
            path,
            stage="scalp_sim_buy_order_assumed_filled",
            emitted_at=base_time,
            would_submit_stage="order_leg_sent",
            **common,
        )
        _write_event(
            path,
            stage="scalp_sim_scale_in_candidate_funnel",
            emitted_at=base_time,
            add_type="AVG_DOWN",
            scale_in_candidate_funnel_state="eligible",
            held_sec=90,
            **common,
        )
        _write_event(
            path,
            stage="scalp_sim_holding_mark",
            emitted_at=future_time,
            sim_record_id=sim_id,
            profit_rate=1.00,
        )

    for idx in range(deep_count):
        record_id = f"{date}-real-{idx}"
        base_minute = 10 * 60 + idx
        base_time = f"{date}T{base_minute // 60:02d}:{base_minute % 60:02d}:00+09:00"
        future_time = f"{date}T{(base_minute + 10) // 60:02d}:{(base_minute + 10) % 60:02d}:00+09:00"
        _write_event(
            path,
            stage="stop_line_touch_mandatory_avg_down_submitted",
            emitted_at=base_time,
            record_id=record_id,
            add_type="AVG_DOWN",
            actual_order_submitted=True,
            profit_rate=-3.65,
            held_sec=180,
            current_ai_score=70,
        )
        _write_event(
            path,
            stage="holding_mark",
            emitted_at=future_time,
            record_id=record_id,
            profit_rate=0.50,
        )


def test_scalping_avg_down_recovery_calibration_builds_post_add_candidate(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    events_path = events_dir / "pipeline_events_2026-07-10.jsonl"

    _write_good_samples(events_path, "2026-07-10", shallow_count=10, deep_count=5)

    report = mod.build_report("2026-07-10", generated_at="2026-07-10T20:10:00+09:00")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["allowed_runtime_apply"] is True
    assert (
        candidate["metric_contract"]["window_policy"]
        == "rolling_clean_baseline_pipeline_events"
    )
    assert (
        candidate["sample_floor"]
        == "rolling_shallow_primary>=10 and rolling_deep_primary>=5"
    )
    assert candidate["source_metrics"]["shallow_primary"]["sample_count"] == 10
    assert candidate["source_metrics"]["deep_primary"]["sample_count"] == 5
    assert candidate["source_metrics"]["daily_shallow_primary"]["sample_count"] == 10
    assert candidate["source_metrics"]["daily_deep_primary"]["sample_count"] == 5
    assert report["source_quality"]["clean_baseline_date"] == "2026-06-04"
    assert (
        "SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION" in candidate["target_env_keys"]
    )
    assert "DEEP_RECOVERY_AVG_DOWN_PNL_MIN" in candidate["target_env_keys"]
    assert candidate["recommended_values"]["shallow_max_per_position"] == 2
    assert candidate["recommended_values"]["deep_pnl_min"] == -4.0


def test_scalping_avg_down_recovery_calibration_uses_rolling_window_for_apply(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    _write_good_samples(
        events_dir / "pipeline_events_2026-07-09.jsonl",
        "2026-07-09",
        shallow_count=5,
        deep_count=3,
    )
    _write_good_samples(
        events_dir / "pipeline_events_2026-07-10.jsonl",
        "2026-07-10",
        shallow_count=5,
        deep_count=2,
    )

    report = mod.build_report("2026-07-10", generated_at="2026-07-10T20:10:00+09:00")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["source_metrics"]["rolling_shallow_primary"]["sample_count"] == 10
    assert candidate["source_metrics"]["rolling_deep_primary"]["sample_count"] == 5
    assert candidate["source_metrics"]["daily_shallow_primary"]["sample_count"] == 5
    assert candidate["source_metrics"]["daily_deep_primary"]["sample_count"] == 2
    assert candidate["source_event_dates"] == ["2026-07-09", "2026-07-10"]


def test_scalping_avg_down_recovery_calibration_blocks_missing_source(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)

    report = mod.build_report("2026-07-10", generated_at="2026-07-10T20:10:00+09:00")
    candidate = report["calibration_candidates"][0]

    assert report["source_quality"]["status"] == "missing_input"
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["calibration_reason"] == "source_pipeline_events_missing"
    assert candidate["source_quality_gate"] == "source_quality_blocked"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["target_env_keys"] == []
