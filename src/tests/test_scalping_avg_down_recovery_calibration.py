import json
from pathlib import Path

import pytest

from src.engine.monitoring import scalping_avg_down_recovery_calibration as mod


@pytest.fixture(autouse=True)
def _source_quality_preflight_pass(monkeypatch):
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "source_quality_gate": "pass",
        },
    )


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

    assert candidate["calibration_state"] == "hold_no_change"
    assert candidate["calibration_reason"] == "recommended_values_unchanged"
    assert candidate["allowed_runtime_apply"] is False
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
    assert report["source_quality"]["clean_baseline_date"] == "2026-06-05"
    assert candidate["target_env_keys"] == []
    assert candidate["recommended_values"]["shallow_max_per_position"] == 2
    assert candidate["recommended_values"]["deep_pnl_min"] == -4.0
    assert candidate["source_metrics"]["decision_guards"] == {
        "target_hit_edge_ok": True,
        "final_ev_edge_ok": True,
        "downside_edge_ok": True,
        "recommended_values_changed": False,
        "minimum_mfe_to_adverse_ratio": 1.0,
        "minimum_equal_weight_avg_profit_pct": 0.0,
    }


def test_avg_down_calibration_excludes_blocked_source_date(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    allowed = events_dir / "pipeline_events_2026-07-09.jsonl"
    blocked = events_dir / "pipeline_events_2026-07-10.jsonl"
    _write_good_samples(allowed, "2026-07-09", shallow_count=1, deep_count=0)
    _write_good_samples(blocked, "2026-07-10", shallow_count=1, deep_count=0)
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda source_date: {
            "status": "pass" if source_date == "2026-07-09" else "missing",
            "tuning_input_allowed": source_date == "2026-07-09",
            "allowed_runtime_apply": source_date == "2026-07-09",
            "source_quality_gate": (
                "pass" if source_date == "2026-07-09" else "blocked_contract_gap"
            ),
            "blocked_reason": (
                None
                if source_date == "2026-07-09"
                else "source_quality_preflight_missing"
            ),
        },
    )

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]

    assert candidate["cumulative_quality_window"]["source_dates"] == ["2026-07-09"]
    assert candidate["source_metrics"]["shallow_raw_submit_pass_avg_down_count"] == 1
    assert report["source_quality"]["input"] == [str(allowed)]
    assert (
        report["source_quality"]["source_quality_excluded_dates"][0]["source_date"]
        == "2026-07-10"
    )
    assert candidate["runtime_update_mode"] == "single_cumulative_quality_update"
    assert candidate["max_runtime_apply_count"] == 1
    assert candidate["post_apply_attribution_required"] is True
    assert (
        report["runtime_update_contract"]["quality_update_id"]
        == candidate["quality_update_id"]
    )
    assert report["runtime_update_contract"]["allowed_runtime_apply_count"] == 0


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

    assert candidate["calibration_state"] == "hold_no_change"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["source_metrics"]["rolling_shallow_primary"]["sample_count"] == 10
    assert candidate["source_metrics"]["rolling_deep_primary"]["sample_count"] == 5
    assert candidate["source_metrics"]["daily_shallow_primary"]["sample_count"] == 5
    assert candidate["source_metrics"]["daily_deep_primary"]["sample_count"] == 2
    assert candidate["source_event_dates"] == ["2026-07-09", "2026-07-10"]


def test_scalping_avg_down_recovery_calibration_updates_cumulative_learning_from_one_row(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    _write_good_samples(
        events_dir / "pipeline_events_2026-07-10.jsonl",
        "2026-07-10",
        shallow_count=1,
        deep_count=0,
    )

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]
    quality = candidate["source_metrics"]["cumulative_judgment_quality"]

    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["learning_sample_floor"] == 1
    assert candidate["learning_sample_floor_passed"] is True
    assert candidate["cumulative_learning_includes_target_date"] is True
    assert quality == {
        "status": "includes_target_date_primary_rows",
        "learning_sample_floor": 1,
        "learning_sample_floor_passed": True,
        "target_date_primary_contribution_count": 1,
        "cumulative_primary_sample_count": 1,
        "applied_to_calibration_decision": True,
        "runtime_promotion_authority": False,
        "runtime_promotion_sample_floor_passed": False,
    }
    assert candidate["metric_contract"]["runtime_promotion_sample_floor"] == {
        "rolling_shallow_primary": 10,
        "rolling_deep_primary": 5,
    }


def test_scalping_avg_down_recovery_calibration_requires_positive_final_ev(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    events_path = events_dir / "pipeline_events_2026-07-10.jsonl"
    _write_good_samples(events_path, "2026-07-10", shallow_count=10, deep_count=5)
    for idx in range(10):
        _write_event(
            events_path,
            stage="scalp_sim_holding_mark",
            emitted_at=f"2026-07-10T{(9 * 60 + idx + 20) // 60:02d}:{(9 * 60 + idx + 20) % 60:02d}:00+09:00",
            sim_record_id=f"2026-07-10-sim-{idx}",
            profit_rate=-1.00,
        )
    for idx in range(5):
        _write_event(
            events_path,
            stage="holding_mark",
            emitted_at=f"2026-07-10T{(10 * 60 + idx + 20) // 60:02d}:{(10 * 60 + idx + 20) % 60:02d}:00+09:00",
            record_id=f"2026-07-10-real-{idx}",
            profit_rate=-1.00,
        )

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "hold_no_edge"
    assert candidate["calibration_reason"] == "post_add_final_ev_not_positive"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["source_metrics"]["decision_guards"]["target_hit_edge_ok"] is True
    assert candidate["source_metrics"]["decision_guards"]["final_ev_edge_ok"] is False


def test_scalping_avg_down_recovery_calibration_adjusts_only_changed_values(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    events_dir = tmp_path / "pipeline_events"
    events_dir.mkdir(parents=True)
    events_path = events_dir / "pipeline_events_2026-07-10.jsonl"
    _write_good_samples(events_path, "2026-07-10", shallow_count=10, deep_count=5)
    current = mod._current_values()
    current["shallow_max_per_position"] = 1
    monkeypatch.setattr(mod, "_current_values", lambda: current)

    report = mod.build_report("2026-07-10")
    candidate = report["calibration_candidates"][0]

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["calibration_reason"] == "post_add_ev_downside_edge_ok"
    assert candidate["allowed_runtime_apply"] is True
    assert candidate["recommended_values_changed"] is True
    assert (
        "SHALLOW_VOLATILITY_AVG_DOWN_MAX_PER_POSITION" in candidate["target_env_keys"]
    )
    assert report["runtime_update_contract"]["allowed_runtime_apply_count"] == 1


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
