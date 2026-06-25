import json
import gzip
from datetime import datetime

from src.engine.monitoring.intraday_entry_blocker_diagnostics import (
    build_report,
    _default_pipeline_path,
    _loop_should_stop,
    _parse_hhmm,
    _within_time_window,
)


def _event(code, name, stage, fields, emitted_at="2026-06-23T08:00:00"):
    return {
        "pipeline": "ENTRY_PIPELINE",
        "stock_code": code,
        "stock_name": name,
        "stage": stage,
        "fields": fields,
        "emitted_at": emitted_at,
    }


def test_build_report_surfaces_rising_promoted_without_real_submit(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "010690",
            "화신",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "7.80"},
        ),
        _event(
            "010690",
            "화신",
            "ai_confirmed",
            {"price_delta_since_first_seen_pct": "7.80", "action": "WAIT", "ai_score": "60", "entry_score_threshold": "75"},
        ),
        _event(
            "010690",
            "화신",
            "blocked_strength_momentum",
            {"price_delta_since_first_seen_pct": "7.80", "reason": "below_buy_ratio", "ai_score": "60"},
        ),
        _event(
            "010690",
            "화신",
            "ai_confirmed_terminal_no_budget",
            {"price_delta_since_first_seen_pct": "7.80", "terminal_reason": "ai_wait"},
        ),
        _event(
            "010690",
            "화신",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "7.80",
                "skip_reason": "scanner_full_eval_loop_budget_deferred",
                "rising_entry_relief_eligible": True,
                "scanner_positive_delta_pct": "7.80",
                "scanner_full_eval_budget_source": "deferred_no_relief",
                "scanner_full_eval_limit": "12",
                "scanner_full_eval_count": "12",
                "scanner_rising_full_eval_extra_limit": "4",
                "scanner_rising_full_eval_relief_count": "4",
            },
        ),
        _event("010690", "화신", "scalp_sim_buy_order_assumed_filled", {"simulated_order": "True"}),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 1
    item = report["rising_missed_buy"][0]
    assert item["stock_code"] == "010690"
    assert item["real_submit_count"] == 0
    assert "sim_submit_observation_count" not in item
    assert item["dominant_blocker"]["stage"] == "blocked_strength_momentum"
    assert item["latest_blocker"]["reason"] == "scanner_full_eval_loop_budget_deferred"
    assert item["latest_ai_action"] == "WAIT"
    assert report["blocker_rollup"][0] == {"stage": "blocked_strength_momentum", "reason": "below_buy_ratio", "count": 1}
    assert report["relief_blocker_split_rollup"]["rising_missed_buy"][0] == {
        "stage": "scalping_scanner_watching_runtime_skip",
        "reason": "scanner_full_eval_loop_budget_deferred",
        "count": 1,
    }
    assert item["recent_blockers"][-1]["scanner_full_eval_budget_source"] == "deferred_no_relief"
    assert item["scanner_full_eval_budget_deferred"]["count"] == 1
    assert report["summary"]["rising_missed_full_eval_budget_deferred_count"] == 1
    assert report["scanner_full_eval_budget_diagnostics"]["top_symbols"][0]["stock_code"] == "010690"
    budget_priority = next(
        item for item in report["root_cause_priorities"] if item["issue"] == "scanner_full_eval_budget_deferred"
    )
    assert budget_priority["decision"] == "treat_as_evaluation_throughput_bottleneck_not_buy_threshold_signal"
    assert "threshold_relaxation" in budget_priority["forbidden_uses"]


def test_build_report_splits_relief_blockers_for_non_rising(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.20"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "0.20", "skip_reason": "entry_cooldown_active"},
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["rising_missed_buy_count"] == 0
    assert report["relief_blocker_split_rollup"]["rising_missed_buy"] == []
    assert report["relief_blocker_split_rollup"]["non_rising_promoted"] == [
        {"stage": "scalping_scanner_watching_runtime_skip", "reason": "entry_cooldown_active", "count": 1}
    ]


def test_build_report_splits_low_ai_pressure_by_eval_freshness(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "quote_age_ms": "1200",
                "tick_latest_age_ms": "900",
                "reason": "below_strength_base",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "50",
                "quote_age_ms": "18000",
                "reason": "stale_quote_or_context",
            },
        ),
        _event(
            "000001",
            "A",
            "scalp_entry_action_decision_snapshot",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "buy_pressure_10t": "-12.5",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    expected = {"fresh_eval": 1, "stale_or_delayed_eval": 1, "unknown_eval_quality": 1}
    assert report["summary"]["rising_missed_low_ai_or_negative_pressure_eval_quality"] == expected
    assert report["rising_missed_buy"][0]["low_ai_or_negative_pressure_eval_quality"] == expected


def test_build_report_excludes_recovery_observations_from_blockers(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "scanner_fast_precheck_subscription_recheck_snapshot_applied",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "before_strategy_start",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "reason": "below_strength_base",
                "ws_strength_history_count": "12",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    item = report["rising_missed_buy"][0]
    assert item["blocker_count"] == 1
    assert item["dominant_blocker"] == {
        "stage": "blocked_strength_momentum",
        "reason": "below_strength_base",
        "count": 1,
    }
    assert item["latest_blocker"]["reason"] == "below_strength_base"
    assert report["summary"]["repeated_zero_strength_history_workorder_count"] == 0
    assert report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"] == []


def test_build_report_treats_recovered_stale_ws_as_recovered_not_stale_eval(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "ai_score": "60",
                "quote_age_ms": "1200",
                "skip_reason": "scanner_fast_precheck_stale_ws_recovered",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "scanner_fast_precheck_stale_ws_recovered",
                "ws_strength_history_count": "0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    expected = {"fresh_eval": 1, "stale_or_delayed_eval": 0, "unknown_eval_quality": 0}
    assert report["summary"]["rising_missed_low_ai_or_negative_pressure_eval_quality"] == expected
    assert report["summary"]["rising_missed_repeated_zero_strength_history_workorder_count"] == 0
    assert report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"] == []


def test_build_report_surfaces_repeated_zero_strength_history_workorder(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "insufficient_history",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "ws_strength_history_count": "0",
            },
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.30"}),
        _event(
            "000002",
            "B",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "1.30",
                "skip_reason": "insufficient_history",
                "ws_strength_history_count": "0",
            },
        ),
        _event("000003", "C", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "0.20"}),
        _event(
            "000003",
            "C",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "0.20",
                "skip_reason": "insufficient_history",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000003",
            "C",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "0.20",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "ws_strength_history_count": "0",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["repeated_zero_strength_history_workorder_count"] == 2
    assert report["summary"]["rising_missed_repeated_zero_strength_history_workorder_count"] == 1
    rising_workorders = report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"]
    assert [item["stock_code"] for item in rising_workorders] == ["000001"]
    assert rising_workorders[0]["decision_authority"] == "source_quality_only"
    assert rising_workorders[0]["runtime_effect"] is False
    assert "strength_threshold_relaxation" in rising_workorders[0]["forbidden_uses"]
    single_zero_history = next(item for item in report["rising_missed_buy"] if item["stock_code"] == "000002")
    assert single_zero_history["zero_strength_history_source_quality"]["source_quality_route"] == (
        "observe_until_repeated"
    )


def test_build_report_suppresses_transient_zero_history_after_downstream_progress(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.40"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "fast_precheck_result": "stability_pending",
                "fast_precheck_reason": "stale_ws_snapshot",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "fast_precheck_result": "stability_pending",
                "fast_precheck_reason": "stale_ws_snapshot",
                "ws_strength_history_count": "0",
            },
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_fast_precheck",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "fast_precheck_pass",
                "ws_strength_history_count": "3",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_strength_momentum",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "reason": "below_strength_base",
                "ai_score": "62",
                "ws_strength_history_count": "3",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    quality = report["rising_missed_buy"][0]["zero_strength_history_source_quality"]
    assert quality["event_count"] == 0
    assert quality["raw_event_count"] == 2
    assert quality["recovered_by_downstream_progress"] is True
    assert quality["source_quality_route"] == "transient_stale_recovered_to_downstream_blocker"
    assert report["summary"]["rising_missed_repeated_zero_strength_history_workorder_count"] == 0
    assert report["source_quality_workorders"]["rising_missed_repeated_zero_strength_history"] == []
    assert all(
        item["issue"] != "scanner_strength_history_or_stale_eval"
        for item in report["root_cause_priorities"]
    )


def test_build_report_excludes_sim_and_keeps_falling_real_submit(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "-0.20"}),
        _event(
            "000001",
            "A",
            "broker_buy_submit",
            {"price_delta_since_first_seen_pct": "-0.20", "actual_order_submitted": "True"},
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "-0.30"}),
        _event(
            "000002",
            "B",
            "scalp_sim_buy_order_assumed_filled",
            {
                "price_delta_since_first_seen_pct": "-0.30",
                "simulated_order": "True",
                "actual_order_submitted": "False",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert [item["stock_code"] for item in report["falling_real_submitted"]] == ["000001"]
    assert "falling_sim_submitted" not in report
    assert report["summary"]["falling_real_submitted_count"] == 1
    assert report["summary"]["excluded_analysis_scope"] == "sim_and_swing_events"


def test_build_report_excludes_sim_price_rows_from_real_entry_price_diagnostics(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.00"}),
        _event(
            "000001",
            "A",
            "scalp_entry_action_decision_snapshot",
            {
                "reason": "scalp_live_simulator",
                "submitted_order_price": "0",
                "best_bid_at_submit": "10000",
                "entry_submit_revalidation_warning": "stale_context_or_quote",
            },
        ),
        _event(
            "000001",
            "A",
            "scalp_entry_action_decision_snapshot",
            {
                "simulation_book": "scalp_ai_buy_all",
                "submitted_order_price": "0",
                "best_bid_at_submit": "10000",
                "entry_submit_revalidation_warning": "stale_context_or_quote",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["entry_price_execution"]["event_count"] == 0
    assert report["entry_price_execution"]["candidate_failure_count"] == 0
    assert not any(item["issue"] == "entry_price_or_submit_price_guard_block" for item in report["root_cause_priorities"])


def test_build_report_prioritizes_real_entry_price_candidate_failures(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.00"}),
        _event(
            "000001",
            "A",
            "entry_ai_price_canary_fallback",
            {"reason": "invalid_price", "action": "IMPROVE_LIMIT"},
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    assert report["entry_price_execution"]["candidate_failure_count"] == 1
    assert report["entry_price_execution"]["candidate_failure_reason_counts"] == [
        {"reason": "invalid_price", "count": 1}
    ]
    priority = next(item for item in report["root_cause_priorities"] if item["issue"] == "entry_price_or_submit_price_guard_block")
    assert priority["evidence"]["candidate_failure_count"] == 1
    assert "stale_submit_bypass" in priority["forbidden_uses"]


def test_build_report_since_filters_out_older_real_submit(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.00"}, "2026-06-23T14:00:00"),
        _event(
            "000001",
            "A",
            "broker_buy_submit",
            {"price_delta_since_first_seen_pct": "1.00", "actual_order_submitted": "True"},
            "2026-06-23T14:05:00",
        ),
        _event("000002", "B", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}, "2026-06-23T14:16:00"),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-23",
        pipeline_path=path,
        generated_at="fixed",
        since="2026-06-23T14:15:00",
    )

    assert report["event_window"]["since"] == "2026-06-23T14:15:00"
    assert report["summary"]["real_submit_symbol_count"] == 0
    assert report["summary"]["rising_missed_buy_count"] == 1
    assert report["rising_missed_buy"][0]["stock_code"] == "000002"


def test_build_report_since_keeps_previously_promoted_active_rising_candidate(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event(
            "000001",
            "A",
            "scalping_scanner_candidate_promoted",
            {"price_delta_since_first_seen_pct": "0.00"},
            "2026-06-23T15:55:00",
        ),
        _event(
            "000001",
            "A",
            "scalping_scanner_fast_precheck",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "fast_precheck_pass",
            },
            "2026-06-23T16:00:30",
        ),
        _event(
            "000001",
            "A",
            "ai_confirmed_terminal_no_budget",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "terminal_reason": "blocked_ai_score_below_buy_score_threshold",
                "ai_score": "68",
            },
            "2026-06-23T16:01:00",
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(
        target_date="2026-06-23",
        pipeline_path=path,
        generated_at="fixed",
        since="2026-06-23T16:00:00",
    )

    assert report["summary"]["promoted_symbol_count"] == 1
    assert report["summary"]["promoted_before_window_symbol_count"] == 1
    assert report["summary"]["rising_missed_buy_count"] == 1
    item = report["rising_missed_buy"][0]
    assert item["stock_code"] == "000001"
    assert item["promoted_in_event_window"] is False
    assert item["first_promoted_at"] == "2026-06-23T15:55:00"
    assert item["latest_blocker"]["reason"] == "blocked_ai_score_below_buy_score_threshold"


def test_build_report_reads_gzip_pipeline_events(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-22.jsonl.gz"
    row = _event("000003", "C", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"})
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = build_report(target_date="2026-06-22", pipeline_path=path, generated_at="fixed")

    assert report["summary"]["promoted_symbol_count"] == 1
    assert report["rising_missed_buy"][0]["stock_code"] == "000003"


def test_default_pipeline_path_prefers_gzip_when_plain_missing(monkeypatch, tmp_path):
    base = tmp_path / "data" / "pipeline_events"
    base.mkdir(parents=True)
    gz_path = base / "pipeline_events_2026-06-22.jsonl.gz"
    gz_path.write_bytes(b"")
    monkeypatch.setattr(
        "src.engine.monitoring.intraday_entry_blocker_diagnostics.PROJECT_ROOT",
        tmp_path,
    )

    assert _default_pipeline_path("2026-06-22") == gz_path


def test_build_report_adds_entry_price_scale_in_and_post_sell_diagnostics(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "1.20"}),
        _event(
            "000001",
            "A",
            "pre_submit_price_guard_block",
            {
                "price_delta_since_first_seen_pct": "1.20",
                "entry_price_guard": "defensive_order_price",
                "resolution_reason": "defensive_order_price",
                "price_below_bid_bps": "95",
                "submitted_order_price": "9900",
                "best_bid_at_submit": "10000",
                "quote_age_at_submit_ms": "450",
                "pre_submit_liquidity_guard_action": "PASS",
            },
        ),
        {
            "pipeline": "HOLDING_PIPELINE",
            "stock_code": "000002",
            "stock_name": "B",
            "stage": "stat_action_decision_snapshot",
            "fields": {
                "profit_rate": "-1.2",
                "peak_profit": "0.2",
                "current_ai_score": "73",
                "scale_in_gate_allowed": "False",
                "scale_in_gate_reason": "scalping_buy_window_blocked",
                "scale_in_blocker_reason": "scalping_buy_window_blocked",
                "scale_in_action_type": "AVG_DOWN",
                "distance_to_buy_bps": "-120",
            },
            "emitted_at": "2026-06-23T09:10:00",
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stock_code": "000002",
            "stock_name": "B",
            "stage": "stat_action_decision_snapshot",
            "fields": {
                "profit_rate": "1.8",
                "peak_profit": "2.1",
                "current_ai_score": "78",
                "scale_in_gate_allowed": "True",
                "scale_in_gate_reason": "ok",
                "scale_in_blocker_reason": "scalping_pyramid_ok",
                "scale_in_action_type": "PYRAMID",
                "distance_to_buy_bps": "140",
            },
            "emitted_at": "2026-06-23T09:11:00",
        },
        {
            "pipeline": "HOLDING_PIPELINE",
            "stock_code": "000005",
            "stock_name": "E",
            "stage": "stat_action_decision_snapshot",
            "fields": {
                "profit_rate": "0.1",
                "peak_profit": "0.8",
                "current_ai_score": "72",
                "scale_in_gate_allowed": "False",
                "scale_in_gate_reason": "-",
                "scale_in_blocker_reason": "MFE protect exit",
                "scale_in_action_type": "-",
                "distance_to_buy_bps": "30",
            },
            "emitted_at": "2026-06-23T09:12:00",
        },
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    (post_sell_dir / "post_sell_candidates_2026-06-23.jsonl").write_text(
        json.dumps({"post_sell_id": "p1"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (post_sell_dir / "post_sell_evaluations_2026-06-23.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "post_sell_id": "p1",
                        "stock_code": "000003",
                        "stock_name": "C",
                        "sell_time": "09:20:00",
                        "profit_rate": "1.5",
                        "exit_rule": "scalp_trailing_take_profit",
                        "outcome": "MISSED_UPSIDE",
                        "metrics_10m": {"mfe_pct": "3.2", "mfe_vs_buy_pct": "4.4"},
                        "ai_score_at_exit": "71",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "post_sell_id": "p2",
                        "stock_code": "000004",
                        "stock_name": "D",
                        "sell_time": "09:25:00",
                        "profit_rate": "-2.1",
                        "exit_rule": "scalp_soft_stop_pct",
                        "outcome": "GOOD_EXIT",
                        "metrics_10m": {"mfe_pct": "0.1", "mfe_vs_buy_pct": "-1.0"},
                        "ai_score_at_exit": "55",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = build_report(
        target_date="2026-06-23",
        pipeline_path=path,
        post_sell_dir=post_sell_dir,
        generated_at="fixed",
    )

    assert report["entry_price_execution"]["block_or_unfilled_count"] == 1
    assert report["entry_price_execution"]["candidate_failure_count"] == 0
    assert report["entry_price_execution"]["recent_issues"][0]["price_below_bid_bps"] == 95.0
    assert report["scale_in_diagnostics"]["blocked_count"] == 1
    assert report["scale_in_diagnostics"]["blocker_reason_counts"][0] == {
        "reason": "scalping_buy_window_blocked",
        "count": 1,
    }
    post_sell = report["post_sell_flow_diagnostics"]
    assert post_sell["candidate_count"] == 1
    assert post_sell["evaluated_count"] == 2
    assert post_sell["missed_upside_count"] == 1
    assert post_sell["bad_entry_after_sell_count"] == 1
    assert post_sell["top_missed_upside"][0]["flow"] == "take_profit_flow"
    assert post_sell["bad_entry_examples"][0]["stock_code"] == "000004"
    priorities = report["root_cause_priorities"]
    assert [item["issue"] for item in priorities] == [
        "entry_price_or_submit_price_guard_block",
        "scale_in_blocked",
        "post_sell_missed_upside_or_bad_entry",
    ]
    assert priorities[0]["runtime_effect"] is False
    assert "stale_submit_bypass" in priorities[0]["forbidden_uses"]


def test_build_report_prioritizes_stale_observation_before_ai_threshold(tmp_path):
    path = tmp_path / "pipeline_events_2026-06-23.jsonl"
    rows = [
        _event("000001", "A", "scalping_scanner_candidate_promoted", {"price_delta_since_first_seen_pct": "2.40"}),
        _event(
            "000001",
            "A",
            "scalping_scanner_watching_runtime_skip",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "skip_reason": "scanner_fast_precheck_stability_pending",
                "ws_strength_history_count": "0",
                "quote_age_ms": "9000",
            },
        ),
        _event(
            "000001",
            "A",
            "blocked_ai_score",
            {
                "price_delta_since_first_seen_pct": "2.40",
                "reason": "score_62.0",
                "ai_score": "62",
                "quote_age_ms": "9000",
            },
        ),
    ]
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")

    report = build_report(target_date="2026-06-23", pipeline_path=path, generated_at="fixed")

    priorities = report["root_cause_priorities"]
    assert priorities[0]["issue"] == "scanner_strength_history_or_stale_eval"
    assert priorities[0]["decision"] == "fix_observation_freshness_before_threshold_tuning"
    assert priorities[1]["issue"] == "ai_wait_or_baseline_prior_score_block"
    assert "broad_buy_score_relaxation" in priorities[1]["forbidden_uses"]


def test_loop_window_helpers():
    buy_start = _parse_hhmm("09:00")
    buy_end = _parse_hhmm("15:20")

    assert _within_time_window(datetime(2026, 6, 25, 9, 0), start=buy_start, end=buy_end)
    assert _within_time_window(datetime(2026, 6, 25, 15, 20), start=buy_start, end=buy_end)
    assert not _within_time_window(datetime(2026, 6, 25, 15, 21), start=buy_start, end=buy_end)
    assert not _loop_should_stop(datetime(2026, 6, 25, 19, 0), until=_parse_hhmm("19:00"))
    assert _loop_should_stop(datetime(2026, 6, 25, 19, 0, 1), until=_parse_hhmm("19:00"))
