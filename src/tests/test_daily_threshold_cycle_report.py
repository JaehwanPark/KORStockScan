import gzip
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from src.engine import daily_threshold_cycle_report as report_mod


def test_build_daily_threshold_cycle_report_generates_candidates_from_samples():
    pipeline_rows = {
        "2026-04-28": [],
        "2026-04-29": [],
        "2026-04-30": [
            {"stage": "budget_pass", "fields": {"signal_score": "72", "latest_strength": "111", "buy_pressure_10t": "53", "ws_age_ms": "900", "ws_jitter_ms": "410", "spread_ratio": "0.0078"}},
            {"stage": "budget_pass", "fields": {"signal_score": "74", "latest_strength": "114", "buy_pressure_10t": "56", "ws_age_ms": "980", "ws_jitter_ms": "430", "spread_ratio": "0.0080"}},
            {"stage": "budget_pass", "fields": {"signal_score": "76", "latest_strength": "118", "buy_pressure_10t": "58", "ws_age_ms": "1030", "ws_jitter_ms": "450", "spread_ratio": "0.0081"}},
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "71", "late_fill": "false"}},
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "77"}},
            {"stage": "bad_entry_block_observed", "fields": {"held_sec": "65", "profit_rate": "-0.88", "peak_profit": "0.12", "ai_score": "41"}},
            {"stage": "bad_entry_block_observed", "fields": {"held_sec": "72", "profit_rate": "-0.94", "peak_profit": "0.18", "ai_score": "43"}},
            {"stage": "bad_entry_refined_candidate", "fields": {"exclusion_reason": "soft_stop_zone", "should_exit": "False"}},
            {"stage": "bad_entry_refined_candidate", "fields": {"exclusion_reason": "loss_too_shallow", "should_exit": "False"}},
            {"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.62", "held_sec": "88", "ai_score": "63", "ai_recovery_delta": "17"}},
            {"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.55", "held_sec": "94", "ai_score": "66", "ai_recovery_delta": "18"}},
            {
                "stage": "reversal_add_blocked_reason",
                "fields": {
                    "blocked_reason": "hold_sec_out_of_range",
                    "profit_rate": "-0.48",
                    "held_sec": "210",
                    "ai_score": "62",
                    "ai_recovery_delta": "14",
                    "pnl_ok": "True",
                    "hold_ok": "False",
                    "low_floor_ok": "True",
                    "ai_score_ok": "True",
                    "ai_recover_ok": "True",
                    "supply_ok": "True",
                    "buy_pressure_ok": "True",
                    "tick_accel_ok": "True",
                    "large_sell_absent_ok": "True",
                    "micro_vwap_ok": "True",
                },
            },
            {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.74", "held_sec": "37"}},
            {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.95", "held_sec": "42"}},
            {
                "stage": "stat_action_decision_snapshot",
                "record_id": 1001,
                "fields": {"chosen_action": "pyramid_wait", "scale_in_action_type": "PYRAMID"},
            },
            {
                "stage": "exit_signal",
                "record_id": 1001,
                "stock_code": "456040",
                "stock_name": "OCI",
                "emitted_at": "2026-04-30T09:47:37",
                "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "0.59", "peak_profit": "1.00", "current_ai_score": "62"},
            },
            {"stage": "sell_completed", "record_id": 1001, "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "0.59"}},
            {
                "stage": "stat_action_decision_snapshot",
                "record_id": 1002,
                "fields": {"chosen_action": "pyramid_wait", "scale_in_action_type": "PYRAMID"},
            },
            {
                "stage": "exit_signal",
                "record_id": 1002,
                "stock_code": "042370",
                "stock_name": "비츠로테크",
                "emitted_at": "2026-04-30T09:56:09",
                "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "2.79", "peak_profit": "3.48", "current_ai_score": "74"},
            },
            {"stage": "sell_completed", "record_id": 1002, "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "3.58"}},
        ]
        + [
            {"stage": "budget_pass", "fields": {"signal_score": "73", "latest_strength": "116", "buy_pressure_10t": "57", "ws_age_ms": "970", "ws_jitter_ms": "420", "spread_ratio": "0.0079"}}
            for _ in range(600)
        ]
        + [{"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}} for _ in range(25)]
        + [{"stage": "bad_entry_block_observed", "fields": {"held_sec": "70", "profit_rate": "-0.90", "peak_profit": "0.15", "ai_score": "42"}} for _ in range(30)]
        + [{"stage": "reversal_add_candidate", "fields": {"profit_rate": "-0.58", "held_sec": "92", "ai_score": "65", "ai_recovery_delta": "16"}} for _ in range(22)]
        + [{"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.82", "held_sec": "40"}} for _ in range(30)]
        + [
            {
                "stage": "protect_trailing_smooth_hold",
                "fields": {
                    "sample_span_sec": "10",
                    "sample_count": "4",
                    "below_ratio": "0.50",
                    "buffer_pct": "1.00",
                    "emergency_pct": "-2.00",
                },
            }
            for _ in range(12)
        ]
        + [
            {
                "stage": "protect_trailing_smooth_confirmed",
                "fields": {
                    "sample_span_sec": "12",
                    "sample_count": "4",
                    "below_ratio": "0.75",
                    "buffer_pct": "1.00",
                    "emergency_pct": "-2.00",
                },
            }
            for _ in range(10)
        ]
        + [
            {
                "stage": "sell_completed",
                "fields": {"exit_rule": "protect_trailing_stop", "profit_rate": "-0.20"},
            }
            for _ in range(2)
        ],
    }

    completed_rows = [
        {"profit_rate": -0.5, "buy_price": 8500, "buy_time": "2026-04-30 09:10:00", "daily_volume": 1_200_000},
        {"profit_rate": 0.3, "buy_price": 22000, "buy_time": "2026-04-30 10:05:00", "daily_volume": 3_000_000, "pyramid_count": 1},
        {"profit_rate": -1.1, "buy_price": 76000, "buy_time": "2026-04-30 14:20:00", "daily_volume": 8_000_000, "avg_down_count": 1},
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: pipeline_rows.get(target_date, []),
        completed_rows_loader=lambda start_date, end_date: completed_rows,
    )

    assert report["summary"]["completed_valid_rolling_7d"] == 3
    assert report["summary"]["loss_count_rolling_7d"] == 2
    assert "threshold_snapshot" in report
    assert "threshold_diff_report" in report
    assert "apply_candidate_list" in report
    assert "calibration_candidates" in report
    assert "post_apply_attribution" in report
    assert "safety_guard_pack" in report
    assert "calibration_trigger_pack" in report
    assert "rollback_guard_pack" in report

    bad_entry = report["threshold_snapshot"]["bad_entry_block"]
    assert bad_entry["apply_ready"] is True
    assert bad_entry["sample"]["soft_stop_zone_candidate"] == 1

    reversal_add = report["threshold_snapshot"]["reversal_add"]
    assert reversal_add["sample"]["blocker_top"]["hold_sec_out_of_range"] == 1
    assert reversal_add["sample"]["near_miss_all_but_hold"] == 1

    pre_submit = report["threshold_snapshot"]["pre_submit_price_guard"]
    assert pre_submit["apply_ready"] is False
    assert 60 <= pre_submit["recommended"]["max_below_bid_bps"] <= 120
    dynamic_entry = report["threshold_snapshot"]["dynamic_entry_price_resolver"]
    assert dynamic_entry["sample"]["candidate_labels"] == [
        "bid-1",
        "bid-2",
        "bid-3",
        "best_bid",
        "AI_candidate",
        "reference_target",
        "timeout_15s",
        "timeout_30s",
    ]
    assert dynamic_entry["sample"]["candidate_metrics"]["real"]["fill_rate"] is None
    assert dynamic_entry["sample"]["candidate_metrics"]["real"]["late_fill_rate"] == 0.0
    assert dynamic_entry["sample"]["candidate_metrics_ready"] is False
    execution_quality = report["threshold_snapshot"]["entry_price_execution_quality"]
    assert execution_quality["sample"]["fill_join_events"] == 0
    assert execution_quality["sample"]["fill_join_available"] is False

    soft_stop = report["threshold_snapshot"]["soft_stop_micro_grace"]
    assert soft_stop["apply_ready"] is True
    whipsaw = report["threshold_snapshot"]["soft_stop_whipsaw_confirmation"]
    assert whipsaw["apply_ready"] is True
    whipsaw_candidate = next(
        item for item in report["calibration_candidates"] if item["family"] == "soft_stop_whipsaw_confirmation"
    )
    assert whipsaw_candidate["apply_mode"] == "calibrated_apply_candidate"
    assert whipsaw_candidate["calibration_state"] in {"adjust_up", "adjust_down", "hold"}
    assert whipsaw_candidate["safety_revert_required"] is False
    assert whipsaw_candidate["target_env_keys"]
    assert whipsaw_candidate["max_step_per_day"] is not None
    assert whipsaw_candidate["sample_window"] == "rolling_10d_with_daily_guard"
    assert whipsaw_candidate["window_policy"]["daily_only_allowed"] is False
    protect_trailing = report["threshold_snapshot"]["protect_trailing_smoothing"]
    assert protect_trailing["apply_ready"] is True
    assert protect_trailing["recommended"]["min_samples"] >= 3
    assert protect_trailing["recommended"]["buffer_pct"] == 1.0
    scalp_trailing = report["threshold_snapshot"]["scalp_trailing_take_profit"]
    assert scalp_trailing["sample"]["weak_borderline"] == 1
    assert scalp_trailing["sample"]["would_hold_if_weak_limit_plus_10bp"] == 1
    assert scalp_trailing["sample"]["would_hold_if_strong_ai_score_relaxed_5pt"] == 1
    assert scalp_trailing["sample"]["pyramid_signaled_not_executed"] == 2
    assert scalp_trailing["sample"]["borderline_examples"][0]["pyramid_state"] == "pyramid_signaled_not_executed"
    assert scalp_trailing["sample"]["strong_ai_boundary_examples"][0]["stock_code"] == "042370"
    action_weight = report["threshold_snapshot"]["statistical_action_weight"]
    assert action_weight["apply_ready"] is False
    assert action_weight["recommended"]["data_completeness"]["price_known"] == 3

    apply_families = {item["family"] for item in report["apply_candidate_list"]}
    assert "pre_submit_price_guard" not in apply_families
    assert "dynamic_entry_price_resolver" not in apply_families
    assert "entry_mechanical_momentum" in apply_families


def test_threshold_cycle_report_marks_calibration_sample_and_live_risk_states():
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [],
        report_source_loader=lambda target_date: {"sources": {}, "source_metrics": {}, "new_observation_axis_created": False},
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    assert candidates["soft_stop_whipsaw_confirmation"]["calibration_state"] == "hold_sample"
    assert candidates["soft_stop_whipsaw_confirmation"]["sample_floor_status"] == "hold_sample"
    assert candidates["soft_stop_whipsaw_confirmation"]["safety_revert_required"] is False
    assert candidates["trailing_continuation"]["calibration_state"] == "freeze"
    assert candidates["trailing_continuation"]["allowed_runtime_apply"] is False
    assert candidates["scale_in_price_guard"]["calibration_state"] == "hold_sample"
    assert candidates["scale_in_price_guard"]["allowed_runtime_apply"] is False
    assert candidates["scale_in_price_guard"]["apply_mode"] == "report_only_calibration"
    assert candidates["scale_in_price_guard"]["sample_window"] == "rolling_10d_or_cumulative_sparse"
    assert candidates["pre_submit_price_guard"]["calibration_state"] == "hold"
    assert candidates["pre_submit_price_guard"]["allowed_runtime_apply"] is False
    assert candidates["dynamic_entry_price_resolver"]["calibration_state"] == "hold_sample"
    assert candidates["dynamic_entry_price_resolver"]["allowed_runtime_apply"] is True
    assert candidates["entry_price_execution_quality"]["allowed_runtime_apply"] is False
    assert "liquidity_gate_refined_candidate" not in candidates
    assert "overbought_gate_refined_candidate" not in candidates
    assert candidates["liquidity_pre_submit_guard_p1"]["allowed_runtime_apply"] is False
    assert candidates["liquidity_pre_submit_guard_p1"]["apply_mode"] == "report_only_calibration"
    assert candidates["liquidity_pre_submit_guard_p1"]["supersedes"] == ["liquidity_gate_refined_candidate"]
    assert candidates["overbought_pullback_guard_p1"]["allowed_runtime_apply"] is False
    assert candidates["overbought_pullback_guard_p1"]["supersedes"] == ["overbought_gate_refined_candidate"]
    assert candidates["holding_flow_ofi_smoothing"]["sample_window"] == "daily_intraday"
    assert candidates["market_regime_continuous_thresholds"]["allowed_runtime_apply"] is False
    assert candidates["market_regime_continuous_thresholds"]["runtime_change"] is False
    assert candidates["market_regime_continuous_thresholds"]["calibration_state"] == "hold_sample"
    assert candidates["market_regime_continuous_thresholds"]["apply_mode"] == "manifest_only"
    assert candidates["market_regime_continuous_thresholds"]["sample_window"] == "rolling_10d_with_valid_market_cache_and_daily_report"
    assert report["post_apply_attribution"]["soft_stop_balanced_policy"]["perfect_win_rate_required"] is False


def test_score65_74_recovery_probe_reports_effective_score60_aliases():
    family = report_mod._build_score65_74_recovery_probe_family(
        [
            {"stage": "wait65_79_ev_candidate", "fields": {"ai_score": "61"}},
            {"stage": "blocked_ai_score", "fields": {"ai_score": "62"}},
            {"stage": "blocked_ai_score", "fields": {"ai_score": "59"}},
        ]
    )

    assert family["current"]["min_score"] == 60
    assert family["current"]["effective_score_range"] == "60-74"
    assert family["current"]["configured_min_micro_vwap_bp"] == 0.0
    assert family["current"]["effective_min_micro_vwap_bp"] == 10.0
    assert family["current"]["min_micro_vwap_bp"] == 10.0
    assert family["sample"]["wait65_79_score60_74_candidate"] == 1
    assert family["sample"]["blocked_score60_74"] == 1
    assert family["sample"]["wait65_79_score65_74_candidate"] == 1
    assert family["sample"]["effective_score_range"] == "60-74"


def test_score65_74_recovery_probe_excludes_early_accel_recheck_retry_rows():
    family = report_mod._build_score65_74_recovery_probe_family(
        [
            {
                "stage": "wait65_79_ev_candidate",
                "fields": {
                    "ai_score": "61",
                    "ai_call_trigger_reason": "early_accel_recheck",
                    "tuning_authority_excluded_reason": "early_accel_recheck_operator_retry",
                },
            },
            {
                "stage": "blocked_ai_score",
                "fields": {
                    "ai_score": "62",
                    "ai_call_trigger_reason": "early_accel_recheck",
                },
            },
            {"stage": "wait65_79_ev_candidate", "fields": {"ai_score": "63"}},
            {"stage": "blocked_ai_score", "fields": {"ai_score": "64"}},
        ]
    )

    assert family["sample"]["wait65_79_score60_74_candidate"] == 1
    assert family["sample"]["blocked_score60_74"] == 1


def test_scalp_simulator_summary_excludes_synthetic_and_tracks_duplicate_dominance():
    events = [
        {
            "stage": "scalp_sim_duplicate_buy_signal",
            "stock_code": "123456",
            "stock_name": "TEST",
            "fields": {"simulation_book": "scalp_ai_buy_all"},
        },
        *[
            {
                "stage": "scalp_sim_duplicate_buy_signal",
                "stock_code": "011070",
                "stock_name": "LG이노텍",
                "emitted_at": "2026-06-12T13:48:00+09:00",
                "fields": {"simulation_book": "scalp_ai_buy_all"},
            }
            for _ in range(10)
        ],
        {
            "stage": "scalp_sim_entry_armed",
            "stock_code": "000660",
            "stock_name": "SK하이닉스",
            "fields": {"simulation_book": "scalp_ai_buy_all"},
        },
    ]
    summary = report_mod._scalp_simulator_event_summary(
        events,
        sim_completed_rows=[
            {"stock_code": "123456", "stock_name": "TEST", "profit_rate": 1.0},
            {"stock_code": "000660", "stock_name": "SK하이닉스", "profit_rate": 1.0},
        ],
    )

    assert summary["synthetic_excluded_count"] == 1
    assert summary["duplicate_buy_signal"] == 10
    assert summary["duplicate_buy_signal_by_symbol_top"] == {"011070": 10}
    assert summary["duplicate_dominance_symbol_count"] == 1
    assert summary["duplicate_buy_signal_by_symbol_time_bucket_top"] == {"011070|time_1030_1400": 10}
    assert summary["duplicate_dominance_symbol_time_bucket_count"] == 1
    assert summary["completed_profit_summary"]["sample"] == 1


def test_market_regime_continuous_threshold_family_metadata_and_source_bundle(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    report_dir.mkdir(parents=True)
    monkeypatch.setattr(report_mod, "REPORT_DIR", report_dir)

    for day in range(1, 11):
        label = "RISK_ON" if day >= 7 else ("NEUTRAL" if day >= 4 else "RISK_OFF")
        score = 35.0 + day * 4.0
        (report_dir / f"report_2026-05-{day:02d}.json").write_text(
            json.dumps(
                {
                    "date": f"2026-05-{day:02d}",
                    "stats": {
                        "market_regime_continuous_score": score,
                        "market_regime_continuous_label": label,
                        "market_regime_component_scores": {
                            "vix_level": 15.0,
                            "fear_greed_level": 8.0,
                            "domestic_breadth": 10.0,
                            "oil_relief": 7.0,
                            "local_model": 4.0,
                        },
                        "market_regime_score_version": "market_regime_continuous_v1",
                        "market_regime_source_quality": "valid",
                        "swing_entry_recovery_gate_score": 0,
                        "allow_swing_entry": day >= 7,
                    },
                    "performance": {
                        "summary": {
                            "total_records": 5,
                            "filled_records": 2,
                            "completed_records": 1,
                            "win_rate": 50.0,
                            "avg_profit_rate": 0.1 * day,
                        }
                    },
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    metrics = report_mod._summarize_market_regime_continuous_sources("2026-05-10")
    metadata = report_mod.CALIBRATION_FAMILY_METADATA["market_regime_continuous_thresholds"]

    assert metadata["allowed_runtime_apply"] is False
    assert metadata["runtime_effect"] is False
    assert metadata["bounds"]["risk_on_min_score"]["max_step_per_day"] == 5
    assert metrics["latest"]["score"] == 75.0
    assert metrics["rolling_10d"]["valid_market_regime_days"] == 10
    assert metrics["source_quality"]["status"] == "pass"
    assert "RISK_ON" in metrics["label_ev_breakdown"]


def test_threshold_cycle_report_counts_scalp_sim_entry_price_and_revalidation_scope():
    events = [
        {
            "stage": "scalp_sim_entry_ai_price_applied",
            "fields": {
                "threshold_family": "dynamic_entry_price_resolver",
                "actual_order_submitted": "false",
            },
        },
        {
            "stage": "scalp_sim_entry_ai_price_skip_order",
            "fields": {
                "threshold_family": "dynamic_entry_price_resolver",
                "actual_order_submitted": "false",
            },
        },
        {
            "stage": "scalp_sim_entry_submit_revalidation_warning",
            "fields": {
                "threshold_family": "dynamic_entry_price_resolver",
                "entry_submit_revalidation_warning": "stale_quote",
                "price_below_bid_bps": "15",
                "actual_order_submitted": "false",
            },
        },
        {
            "stage": "scalp_sim_entry_submit_revalidation_block",
            "fields": {
                "threshold_family": "dynamic_entry_price_resolver",
                "block_reason": "stale_context_or_quote",
                "actual_order_submitted": "false",
            },
        },
        {
            "stage": "scalp_sim_buy_order_virtual_pending",
            "fields": {
                "threshold_family": "dynamic_entry_price_resolver",
                "price_below_bid_bps": "12",
                "actual_order_submitted": "false",
            },
        },
        {
            "stage": "scalp_sim_scale_in_order_assumed_filled",
            "fields": {
                "threshold_family": "scale_in_price_guard",
                "virtual_budget_override": "true",
                "actual_order_submitted": "false",
            },
        },
    ]
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-15",
        pipeline_loader=lambda target_date: events if target_date == "2026-05-15" else [],
        report_source_loader=lambda target_date: {
            "sources": {},
            "source_metrics": {},
            "new_observation_axis_created": False,
        },
        completed_rows_loader=lambda start_date, end_date: [],
    )

    dynamic_entry = report["threshold_snapshot"]["dynamic_entry_price_resolver"]["sample"]
    assert dynamic_entry["sim_entry_ai_price_applied"] == 1
    assert dynamic_entry["sim_entry_ai_price_skip_order"] == 1
    assert dynamic_entry["sim_submit_revalidation_block"] == 1
    assert dynamic_entry["sim_price_below_bid_bps"] == 1
    assert dynamic_entry["price_below_bid_bps"] == 0
    assert dynamic_entry["sim_actual_order_submitted"] is False
    assert dynamic_entry["sim_broker_order_forbidden"] is True
    assert dynamic_entry["candidate_metrics"]["real"]["fill_rate"] is None
    assert dynamic_entry["candidate_metrics"]["real"]["late_fill_rate"] == 0.0
    assert dynamic_entry["candidate_metrics_ready"] is False

    scalp_sim = report["scalp_simulator"]
    assert scalp_sim["entry_ai_price_applied"] == 1
    assert scalp_sim["entry_ai_price_skip_order"] == 1
    assert scalp_sim["entry_submit_revalidation_warning"] == 1
    assert scalp_sim["entry_submit_revalidation_block"] == 1
    assert scalp_sim["scale_in_filled"] == 1


def test_threshold_cycle_report_routes_entry_filter_ev_sources_to_calibration_families():
    report_sources = {
        "sources": {
            "missed_entry_counterfactual": {
                "path": "data/report/monitor_snapshots/missed_entry_counterfactual_2026-05-08.json",
                "exists": True,
            },
            "performance_tuning": {
                "path": "data/report/monitor_snapshots/performance_tuning_2026-05-08.json",
                "exists": True,
            },
        },
        "source_metrics": {
            "latency_guard_miss_ev_recovery": {
                "evaluated_candidates": 25,
                "missed_winner_rate": 70.0,
                "avoided_loser_rate": 20.0,
                "quote_fresh_latency_pass_rate": 90.0,
                "performance_latency_block_events": 25,
            },
            "buy_score65_74": {
                "score65_74_candidates": 3,
                "wait6579_total_candidates": 3,
                "blocked_ai_score_evaluated": 22,
                "blocked_ai_score_missed_winner_rate": 60.0,
                "blocked_ai_score_avoided_loser_rate": 20.0,
            },
            "liquidity_gate_refined_candidate": {
                "evaluated_candidates": 21,
                "missed_winner_rate": 45.0,
                "avoided_loser_rate": 35.0,
                "performance_blocked_liquidity_events": 21,
            },
            "overbought_gate_refined_candidate": {
                "evaluated_candidates": 21,
                "missed_winner_rate": 15.0,
                "avoided_loser_rate": 45.0,
                "performance_blocked_overbought_events": 21,
            },
        },
    }
    pipeline_rows = (
        [{"stage": "pre_submit_price_guard_block", "fields": {"price_below_bid_bps": "85"}} for _ in range(5)]
        + [{"stage": "blocked_liquidity", "fields": {}} for _ in range(5)]
        + [{"stage": "blocked_overbought", "fields": {}} for _ in range(5)]
        + [{"stage": "blocked_ai_score", "fields": {"ai_score": "70"}} for _ in range(5)]
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: pipeline_rows,
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    assert candidates["pre_submit_price_guard"]["calibration_state"] == "hold"
    assert candidates["pre_submit_price_guard"]["allowed_runtime_apply"] is False
    assert candidates["dynamic_entry_price_resolver"]["calibration_state"] == "hold_sample"
    assert candidates["dynamic_entry_price_resolver"]["source_metrics"]["missed_winner_rate"] == 70.0
    assert candidates["score65_74_recovery_probe"]["source_metrics"]["blocked_ai_score_evaluated"] == 22
    assert "liquidity_gate_refined_candidate" not in candidates
    assert "overbought_gate_refined_candidate" not in candidates
    assert candidates["liquidity_pre_submit_guard_p1"]["calibration_state"] == "hold"
    assert candidates["liquidity_pre_submit_guard_p1"]["allowed_runtime_apply"] is False
    assert candidates["liquidity_pre_submit_guard_p1"]["source_metrics"]["missed_winner_rate"] == 45.0
    assert candidates["liquidity_pre_submit_guard_p1"]["sample_count"] == 21
    assert candidates["overbought_pullback_guard_p1"]["calibration_state"] == "hold"
    assert candidates["overbought_pullback_guard_p1"]["source_metrics"]["avoided_loser_rate"] == 45.0
    assert candidates["overbought_pullback_guard_p1"]["sample_count"] == 21


def test_dynamic_entry_price_resolver_opens_when_source_candidate_metrics_are_complete():
    complete_metrics = {
        "fill_rate": 62.0,
        "full_fill_rate": 51.0,
        "partial_fill_rate": 11.0,
        "cancel_rate": 18.0,
        "late_fill_rate": 3.0,
        "missed_upside": 0.21,
        "source_quality_adjusted_ev_pct": 0.42,
    }
    report_sources = {
        "sources": {
            "entry_price_candidate_quality": {
                "path": "data/report/entry_price_candidate_quality/entry_price_candidate_quality_2026-05-08.json",
                "exists": True,
            },
        },
        "source_metrics": {
            "dynamic_entry_price_resolver": {
                "candidate_observations": 25,
                "sim_candidate_observations": 25,
                "real_candidate_observations": 0,
                "source_quality_adjusted_ev_pct": 0.37,
                "candidate_metrics": {
                    "sim": dict(complete_metrics),
                    "real": dict(complete_metrics),
                },
                "recommended_values_decision_scope": "sim_probe_ev",
                "recommended_values": {
                    "enabled": True,
                    "normal_defensive_ticks": "2",
                    "max_below_bid_bps": "70",
                    "conditional_1tick_real_enabled": False,
                },
            },
        },
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}}
            for _ in range(7)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    dynamic = candidates["dynamic_entry_price_resolver"]
    assert dynamic["calibration_state"] == "adjust_up"
    assert dynamic["apply_mode"] == "calibrated_apply_candidate"
    assert dynamic["sample_floor_status"] == "ready"
    assert dynamic["recommended_values"]["normal_defensive_ticks"] == 2
    assert dynamic["recommended_values"]["max_below_bid_bps"] == 70
    assert dynamic["recommended_values"]["conditional_1tick_real_enabled"] is False
    assert dynamic["source_metrics"]["recommended_values_audit"]["accepted"]["normal_defensive_ticks"] == 2
    assert dynamic["source_metrics"]["recommended_values_audit"]["accepted"]["max_below_bid_bps"] == 70
    assert dynamic["source_metrics"]["recommended_values_audit"]["clamped"] == {}
    assert dynamic["source_metrics"]["candidate_metrics_ready"] is True
    assert dynamic["source_metrics"]["candidate_metrics_missing"] == {}


def test_dynamic_entry_price_resolver_uses_sim_metrics_for_readiness_and_keeps_real_diagnostic():
    complete_sim_metrics = {
        "fill_rate": 62.0,
        "full_fill_rate": 51.0,
        "partial_fill_rate": 11.0,
        "cancel_rate": 18.0,
        "late_fill_rate": 3.0,
        "missed_upside": 0.21,
        "source_quality_adjusted_ev_pct": 0.42,
    }
    real_diagnostic_metrics = {
        "cancel_rate": 0.0,
        "late_fill_rate": 0.0,
        "fill_rate": None,
        "full_fill_rate": None,
        "partial_fill_rate": None,
        "missed_upside": None,
        "source_quality_adjusted_ev_pct": -9.5,
    }
    report_sources = {
        "sources": {
            "entry_price_candidate_quality": {
                "path": "data/report/entry_price_candidate_quality/entry_price_candidate_quality_2026-05-08.json",
                "exists": True,
            },
        },
        "source_metrics": {
            "dynamic_entry_price_resolver": {
                "candidate_observations": 25,
                "sim_candidate_observations": 25,
                "real_candidate_observations": 7,
                "source_quality_adjusted_ev_pct": -9.5,
                "candidate_metrics": {
                    "sim": dict(complete_sim_metrics),
                    "real": dict(real_diagnostic_metrics),
                },
                "recommended_values_decision_scope": "sim",
                "recommended_values": {
                    "enabled": True,
                    "normal_defensive_ticks": "2",
                    "max_below_bid_bps": "70",
                    "conditional_1tick_real_enabled": False,
                },
            },
        },
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}}
            for _ in range(7)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    dynamic = candidates["dynamic_entry_price_resolver"]
    assert dynamic["calibration_state"] == "adjust_up"
    assert dynamic["apply_mode"] == "calibrated_apply_candidate"
    assert dynamic["source_metrics"]["candidate_metrics_ready"] is True
    assert dynamic["source_metrics"]["candidate_metrics_missing"] == {}
    assert "candidate_metrics_diagnostic_missing" not in dynamic["source_metrics"]


def test_dynamic_entry_price_resolver_does_not_use_real_observations_for_sample_floor():
    complete_sim_metrics = {
        "fill_rate": 62.0,
        "full_fill_rate": 51.0,
        "partial_fill_rate": 11.0,
        "cancel_rate": 18.0,
        "late_fill_rate": 3.0,
        "missed_upside": 0.21,
        "source_quality_adjusted_ev_pct": 0.42,
    }
    report_sources = {
        "sources": {},
        "source_metrics": {
            "dynamic_entry_price_resolver": {
                "candidate_observations": 25,
                "sim_candidate_observations": 5,
                "real_candidate_observations": 20,
                "candidate_metrics": {
                    "sim": dict(complete_sim_metrics),
                },
                "recommended_values_decision_scope": "sim",
                "recommended_values": {
                    "enabled": True,
                    "normal_defensive_ticks": "2",
                    "max_below_bid_bps": "70",
                    "conditional_1tick_real_enabled": False,
                },
            },
        },
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}}
            for _ in range(20)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    dynamic = {item["family"]: item for item in report["calibration_candidates"]}[
        "dynamic_entry_price_resolver"
    ]
    assert dynamic["calibration_state"] == "hold_real_outcome_pending"
    assert dynamic["sample_count"] == 20
    assert dynamic["sample_floor_status"] == "hold_real_outcome_pending"
    assert "outcome join" in dynamic["calibration_reason"]


def test_dynamic_entry_price_resolver_separates_sim_unpriced_stale_and_ai_candidate_failures():
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {
                "stage": "scalp_sim_buy_order_virtual_pending",
                "fields": {
                    "submitted_order_price": "0",
                    "entry_submit_revalidation_warning": "stale_context_or_quote",
                    "quote_stale_at_submit": "true",
                    "actual_order_submitted": "false",
                    "broker_order_forbidden": "true",
                },
            },
            {
                "stage": "scalp_sim_buy_order_assumed_filled",
                "fields": {
                    "submitted_order_price": "0",
                    "quote_stale_at_submit": "true",
                    "actual_order_submitted": "false",
                    "broker_order_forbidden": "true",
                },
            },
            {
                "stage": "scalp_sim_buy_order_virtual_pending",
                "fields": {
                    "submitted_order_price": "10000",
                    "actual_order_submitted": "false",
                    "broker_order_forbidden": "true",
                },
            },
            {
                "stage": "scalp_sim_buy_order_assumed_filled",
                "fields": {
                    "submitted_order_price": "10000",
                    "actual_order_submitted": "false",
                    "broker_order_forbidden": "true",
                    "fill_type": "full_fill",
                },
            },
            {
                "stage": "entry_ai_price_canary_fallback",
                "fields": {
                    "reason": "invalid_price",
                    "orderbook_micro_reason": "missing_snapshot",
                    "orderbook_micro_state": "insufficient",
                    "orderbook_micro_observer_missing_reason": "missing_snapshot",
                },
            },
            {"stage": "entry_ai_price_canary_applied", "fields": {"submitted_order_price": "10000"}},
        ],
        completed_rows_loader=lambda start_date, end_date: [],
    )

    dynamic = report["threshold_snapshot"]["dynamic_entry_price_resolver"]["sample"]
    sim_metrics = dynamic["candidate_metrics"]["sim"]
    assert dynamic["real_candidate_observations"] == 0
    assert sim_metrics["priced_sample_count"] == 2
    assert sim_metrics["unpriced_sample_count"] == 2
    assert sim_metrics["stale_warning_count"] == 2
    assert sim_metrics["excluded_from_fill_ev_count"] == 2
    assert sim_metrics["excluded_from_fill_ev_reasons"] == {
        "quote_stale_at_submit": 1,
        "stale_context_or_quote": 1,
    }
    assert sim_metrics["fill_rate"] == 100.0
    assert sim_metrics["forbidden_zero_price_observation_count"] == 0
    assert sim_metrics["limit_fill_price_missing_but_assumed_present_count"] == 0
    assert sim_metrics["real_execution_quality_sample_count"] == 0
    assert dynamic["unpriced_or_stale_warning_count"] == 2
    assert dynamic["sim_submit_path_quality"]["scalp_sim_buy_order_virtual_pending"] == {
        "sample_count": 2,
        "priced_sample_count": 1,
        "unpriced_sample_count": 1,
        "stale_warning_count": 1,
        "excluded_from_fill_ev_count": 1,
        "actual_order_submitted_violation_count": 0,
        "broker_order_forbidden_violation_count": 0,
        "canonical_sim_fill_price_defect_breakdown": {"priced_valid": 1},
        "forbidden_zero_price_observation_count": 0,
        "limit_fill_price_missing_but_assumed_present_count": 0,
        "classification": "sim_unpriced_stale_warning",
    }
    ai_quality = dynamic["candidate_quality"]["AI_candidate"]
    assert ai_quality["candidate_event_count"] == 2
    assert ai_quality["candidate_failure_count"] == 1
    assert ai_quality["candidate_failure_rate"] == 50.0
    assert ai_quality["failure_reasons"] == {"invalid_price": 1, "missing_snapshot": 1}


def test_dynamic_entry_price_resolver_clamps_invalid_source_recommended_values():
    complete_metrics = {
        "fill_rate": 62.0,
        "full_fill_rate": 51.0,
        "partial_fill_rate": 11.0,
        "cancel_rate": 18.0,
        "late_fill_rate": 3.0,
        "missed_upside": 0.21,
        "source_quality_adjusted_ev_pct": 0.42,
    }
    report_sources = {
        "sources": {},
        "source_metrics": {
            "dynamic_entry_price_resolver": {
                "candidate_observations": 25,
                "sim_candidate_observations": 18,
                "real_candidate_observations": 7,
                "source_quality_adjusted_ev_pct": 0.37,
                "candidate_metrics": {
                    "sim": dict(complete_metrics),
                    "real": dict(complete_metrics),
                },
                "recommended_values_decision_scope": "sim",
                "recommended_values": {
                    "enabled": "true",
                    "normal_defensive_ticks": 10,
                    "max_below_bid_bps": 200,
                    "conditional_1tick_real_enabled": "false",
                },
            },
        },
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}}
            for _ in range(25)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    dynamic = {item["family"]: item for item in report["calibration_candidates"]}["dynamic_entry_price_resolver"]
    assert dynamic["recommended_values"]["normal_defensive_ticks"] == 2
    assert dynamic["recommended_values"]["max_below_bid_bps"] == 90
    assert dynamic["recommended_values"]["conditional_1tick_real_enabled"] is True
    audit = dynamic["source_metrics"]["recommended_values_audit"]
    assert audit["clamped"]["normal_defensive_ticks"] == {"requested": 10, "applied": 2}
    assert audit["clamped"]["max_below_bid_bps"] == {"requested": 200, "applied": 90}
    assert audit["rejected"]["enabled"]["reason"] == "invalid_bool"
    assert audit["rejected"]["conditional_1tick_real_enabled"]["reason"] == "invalid_bool"


def test_dynamic_entry_price_resolver_holds_without_runtime_recommendation_change():
    complete_metrics = {
        "fill_rate": 62.0,
        "full_fill_rate": 51.0,
        "partial_fill_rate": 11.0,
        "cancel_rate": 18.0,
        "late_fill_rate": 3.0,
        "missed_upside": 0.21,
        "source_quality_adjusted_ev_pct": 0.42,
    }
    report_sources = {
        "sources": {},
        "source_metrics": {
            "dynamic_entry_price_resolver": {
                "candidate_observations": 25,
                "sim_candidate_observations": 18,
                "real_candidate_observations": 7,
                "source_quality_adjusted_ev_pct": 0.37,
                "candidate_metrics": {
                    "sim": dict(complete_metrics),
                    "real": dict(complete_metrics),
                },
            },
        },
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}}
            for _ in range(25)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    dynamic = {item["family"]: item for item in report["calibration_candidates"]}["dynamic_entry_price_resolver"]
    assert dynamic["calibration_state"] == "hold_sample"
    assert dynamic["apply_mode"] == "report_only_calibration"
    assert dynamic["source_metrics"]["candidate_metrics_ready"] is True
    assert dynamic["source_metrics"]["recommended_values_valid"] is False
    assert dynamic["source_metrics"]["recommended_values_runtime_change_ready"] is False
    assert "recommended_values_audit" not in dynamic["source_metrics"]


def test_dynamic_entry_price_resolver_holds_when_conditional_1tick_recommendation_matches_current(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "TRADING_RULES",
        SimpleNamespace(
            SCALPING_ENTRY_PRICE_RESOLVER_ENABLED=True,
            SCALPING_NORMAL_DEFENSIVE_TICKS=1,
            SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS=80,
            SCALPING_CONDITIONAL_1TICK_REAL_ENABLED=False,
        ),
    )
    complete_metrics = {
        "fill_rate": 62.0,
        "full_fill_rate": 51.0,
        "partial_fill_rate": 11.0,
        "cancel_rate": 18.0,
        "late_fill_rate": 3.0,
        "missed_upside": 0.21,
        "source_quality_adjusted_ev_pct": 0.42,
    }
    report_sources = {
        "sources": {},
        "source_metrics": {
            "dynamic_entry_price_resolver": {
                "candidate_observations": 25,
                "sim_candidate_observations": 18,
                "real_candidate_observations": 7,
                "source_quality_adjusted_ev_pct": 0.37,
                "candidate_metrics": {
                    "sim": dict(complete_metrics),
                    "real": dict(complete_metrics),
                },
                "recommended_values_decision_scope": "sim",
                "recommended_values": {
                    "conditional_1tick_real_enabled": False,
                },
            },
        },
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "75"}}
            for _ in range(25)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    dynamic = {item["family"]: item for item in report["calibration_candidates"]}["dynamic_entry_price_resolver"]
    assert dynamic["current_values"]["conditional_1tick_real_enabled"] is False
    assert dynamic["recommended_values"]["conditional_1tick_real_enabled"] is False
    assert dynamic["calibration_state"] == "hold_sample"
    assert dynamic["source_metrics"]["recommended_values_valid"] is True
    assert dynamic["source_metrics"]["recommended_values_runtime_change_ready"] is False


def test_dynamic_entry_price_resolver_rejects_recommendation_without_sim_scope():
    complete_metrics = {
        "fill_rate": 62.0,
        "full_fill_rate": 51.0,
        "partial_fill_rate": 11.0,
        "cancel_rate": 18.0,
        "late_fill_rate": 3.0,
        "missed_upside": 0.21,
        "source_quality_adjusted_ev_pct": 0.42,
    }
    report_sources = {
        "sources": {},
        "source_metrics": {
            "dynamic_entry_price_resolver": {
                "candidate_observations": 25,
                "sim_candidate_observations": 25,
                "real_candidate_observations": 25,
                "candidate_metrics": {
                    "sim": dict(complete_metrics),
                },
                "recommended_values": {
                    "normal_defensive_ticks": "2",
                    "max_below_bid_bps": "70",
                },
            },
        },
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "120"}}
            for _ in range(25)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    dynamic = {item["family"]: item for item in report["calibration_candidates"]}[
        "dynamic_entry_price_resolver"
    ]
    assert dynamic["calibration_state"] == "hold_sample"
    assert dynamic["recommended_values"]["normal_defensive_ticks"] == dynamic["current_values"]["normal_defensive_ticks"]
    assert dynamic["recommended_values"]["max_below_bid_bps"] == dynamic["current_values"]["max_below_bid_bps"]
    assert dynamic["source_metrics"]["recommended_values_valid"] is False
    assert dynamic["source_metrics"]["recommended_values_runtime_change_ready"] is False
    audit = dynamic["source_metrics"]["recommended_values_audit"]
    assert audit["rejected"]["recommended_values_decision_scope"] == {
        "value": None,
        "reason": "required_sim_scope",
    }


def test_dynamic_entry_price_resolver_partial_sim_recommendation_keeps_unspecified_keys_current():
    complete_metrics = {
        "fill_rate": 62.0,
        "full_fill_rate": 51.0,
        "partial_fill_rate": 11.0,
        "cancel_rate": 18.0,
        "late_fill_rate": 3.0,
        "missed_upside": 0.21,
        "source_quality_adjusted_ev_pct": 0.42,
    }
    report_sources = {
        "sources": {},
        "source_metrics": {
            "dynamic_entry_price_resolver": {
                "candidate_observations": 25,
                "sim_candidate_observations": 25,
                "real_candidate_observations": 25,
                "candidate_metrics": {
                    "sim": dict(complete_metrics),
                },
                "recommended_values_decision_scope": "sim",
                "recommended_values": {
                    "normal_defensive_ticks": "2",
                },
            },
        },
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "order_bundle_submitted", "fields": {"price_below_bid_bps": "120"}}
            for _ in range(25)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    dynamic = {item["family"]: item for item in report["calibration_candidates"]}[
        "dynamic_entry_price_resolver"
    ]
    assert dynamic["calibration_state"] == "adjust_up"
    assert dynamic["recommended_values"]["normal_defensive_ticks"] == 2
    assert dynamic["recommended_values"]["max_below_bid_bps"] == dynamic["current_values"]["max_below_bid_bps"]
    assert dynamic["recommended_values"]["conditional_1tick_real_enabled"] == dynamic["current_values"][
        "conditional_1tick_real_enabled"
    ]
    assert dynamic["source_metrics"]["recommended_values_valid"] is True
    assert dynamic["source_metrics"]["recommended_values_runtime_change_ready"] is True


def test_window_policy_registry_demotes_score65_daily_trigger_without_rolling_denominator():
    report = {
        "calibration_candidates": [
            {
                "family": "score65_74_recovery_probe",
                "source_family": "score65_74_recovery_probe",
                "threshold_version": "score65_74_recovery_probe:observe_only:ready",
                "stage": "entry",
                "priority": 10,
                "current_value": False,
                "recommended_value": True,
                "current_values": {"enabled": False},
                "recommended_values": {"enabled": True},
                "sample_count": 191,
                "source_sample_count": 191,
                "sample_floor": 20,
                "sample_floor_status": "ready",
                "window_policy": {
                    "primary": "rolling_5d",
                    "secondary": ["daily_intraday", "cumulative_since_2026-04-21"],
                    "daily_only_allowed": False,
                },
                "calibration_state": "adjust_up",
                "calibration_reason": "daily BUY drought trigger",
                "apply_mode": "efficient_tradeoff_canary_candidate",
                "allowed_runtime_apply": True,
            }
        ]
    }
    cumulative = {
        "threshold_snapshot_by_window": {
            "rolling_5d": {
                "score65_74_recovery_probe": {
                    "sample": {
                        "wait65_79_score65_74_candidate": 0,
                        "blocked_score65_74": 0,
                        "budget_pass": 999,
                    },
                    "sample_ready": False,
                }
            }
        }
    }

    report_mod.apply_window_policy_registry_to_report(report, cumulative)

    candidate = report["calibration_candidates"][0]
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["runtime_apply_blocker"] == "window_policy_primary_not_ready"
    assert candidate["window_policy_resolution"]["primary"] == "rolling_5d"
    assert candidate["window_policy_resolution"]["primary_sample_count"] == 0
    assert candidate["apply_mode"] == "report_only_calibration"
    assert report["window_policy_audit"]["issue_counts"] == {"daily_only_leak_blocked": 1}


def test_threshold_cycle_calibration_uses_holding_exit_report_sources():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-04-30",
        "sources": {
            "holding_exit_observation": {"path": "data/report/monitor_snapshots/holding_exit_observation_2026-04-30.json", "exists": True},
            "holding_exit_sentinel": {"path": "data/report/holding_exit_sentinel/holding_exit_sentinel_2026-04-30.json", "exists": True},
        },
        "source_metrics": {
            "soft_stop": {
                "holding_exit_observation_total": 20,
                "holding_exit_observation_rebound_above_sell_10m_rate": 90.0,
                "holding_exit_observation_whipsaw_signal": True,
            },
            "holding_flow": {
                "sentinel_primary": "HOLD_DEFER_DANGER",
                "holding_flow_override_defer_exit": 67,
                "max_defer_worsen_pct": 0.8,
            },
            "trailing": {
                "evaluated_trailing": 17,
                "missed_upside_rate": 29.4,
                "good_exit_rate": 41.2,
            },
        },
        "new_observation_axis_created": False,
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
        calibration_run_phase="intraday",
    )

    assert report["meta"]["calibration_run_phase"] == "intraday"
    assert report["meta"]["calibration_cadence"] == "scheduled_postclose_manual_intraday"
    assert report["calibration_source_bundle"]["new_observation_axis_created"] is False
    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    assert candidates["soft_stop_whipsaw_confirmation"]["source_sample_count"] == 20
    assert candidates["soft_stop_whipsaw_confirmation"]["sample_floor_status"] == "ready"
    assert candidates["soft_stop_whipsaw_confirmation"]["window_policy"]["primary"] == "rolling_10d"
    assert candidates["soft_stop_whipsaw_confirmation"]["source_metrics"]["holding_exit_observation_whipsaw_signal"] is True
    assert candidates["holding_flow_ofi_smoothing"]["source_sample_count"] == 67
    assert candidates["holding_flow_ofi_smoothing"]["source_metrics"]["sentinel_primary"] == "HOLD_DEFER_DANGER"


def test_calibration_source_bundle_includes_panic_sell_defense(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "REPORT_DIR", tmp_path / "report")
    panic_path = tmp_path / "report" / "panic_sell_defense" / "panic_sell_defense_2026-05-12.json"
    panic_path.parent.mkdir(parents=True, exist_ok=True)
    panic_path.write_text(
        json.dumps(
            {
                "report_type": "panic_sell_defense",
                "panic_state": "RECOVERY_WATCH",
                "panic_regime_mode": "STABILIZING",
                "panic_regime_contract": {
                    "decision_authority": "source_quality_only",
                    "runtime_effect": "report_only_no_mutation",
                    "allowed_actions": ["sim_probe_only_recovery_candidate"],
                    "forbidden_uses": ["auto_sell"],
                },
                "policy": {"runtime_effect": "report_only_no_mutation"},
                "panic_metrics": {
                    "real_exit_count": 28,
                    "non_real_exit_count": 28,
                    "stop_loss_exit_count": 22,
                    "max_rolling_30m_stop_loss_exit_count": 17,
                    "stop_loss_exit_ratio_pct": 78.6,
                    "avg_exit_profit_rate_pct": -1.3621,
                    "confirmation_eligible_exit_count": 6,
                    "never_delay_exit_count": 0,
                },
                "recovery_metrics": {
                    "active_sim_probe": {
                        "active_positions": 8,
                        "avg_unrealized_profit_rate_pct": 0.7995,
                        "win_rate_pct": 62.5,
                        "provenance_check": {"passed": True},
                    },
                    "post_sell_feedback": {
                        "rebound_above_sell_10_20m_pct": 0.0,
                        "rebound_above_buy_10_20m_pct": 0.0,
                    },
                },
                "canary_candidates": [
                    {"family": "panic_entry_freeze_guard", "status": "report_only_candidate"},
                    {"family": "panic_rebound_probe", "status": "hold_until_recovery_confirmed"},
                ],
                "microstructure_detector": {
                    "evaluated_symbol_count": 3,
                    "risk_off_advisory_count": 1,
                    "allow_new_long_false_count": 1,
                    "missing_orderbook_count": 1,
                    "degraded_orderbook_count": 1,
                    "metrics": {
                        "max_panic_score": 0.84,
                        "max_recovery_score": 0.41,
                    },
                },
                "microstructure_market_context": {
                    "market_risk_state": "NEUTRAL",
                    "market_confirms_risk_off": False,
                    "breadth_confirms_risk_off": False,
                    "confirmed_risk_off_advisory": False,
                    "portfolio_local_risk_off_only": True,
                    "risk_off_advisory_ratio_pct": 33.3,
                    "breadth_symbol_floor": 20,
                    "reasons": [
                        "micro_risk_off_unconfirmed_by_market_or_breadth",
                        "micro_evaluated_symbol_count_below_breadth_floor",
                        "market_regime_not_risk_off",
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    bundle = report_mod._summarize_calibration_report_sources("2026-05-12")
    metrics = bundle["source_metrics"]["panic_sell_defense"]

    assert bundle["sources"]["panic_sell_defense"]["exists"] is True
    assert metrics["panic_state"] == "RECOVERY_WATCH"
    assert metrics["panic_regime_mode"] == "STABILIZING"
    assert metrics["panic_regime_decision_authority"] == "source_quality_only"
    assert metrics["panic_regime_runtime_effect"] == "report_only_no_mutation"
    assert "sim_probe_only_recovery_candidate" in metrics["panic_regime_allowed_actions"]
    assert "auto_sell" in metrics["panic_regime_forbidden_uses"]
    assert metrics["runtime_effect"] == "report_only_no_mutation"
    assert metrics["max_rolling_30m_stop_loss_exit_count"] == 17
    assert metrics["active_sim_probe_provenance_passed"] is True
    assert metrics["candidate_status"]["panic_entry_freeze_guard"] == "report_only_candidate"
    assert metrics["microstructure_evaluated_symbol_count"] == 3
    assert metrics["microstructure_risk_off_advisory_count"] == 1
    assert metrics["microstructure_degraded_orderbook_count"] == 1
    assert metrics["microstructure_max_panic_score"] == 0.84
    assert metrics["microstructure_market_risk_state"] == "NEUTRAL"
    assert metrics["microstructure_confirmed_risk_off_advisory"] is False
    assert metrics["microstructure_portfolio_local_risk_off_only"] is True
    assert metrics["market_breadth_followup_candidate"] is True
    assert metrics["market_breadth_next_action"] == "review_index_breadth_before_panic_runtime_candidate"
    assert "market_regime_not_risk_off" in metrics["source_quality_blockers"]
    assert metrics["allowed_runtime_apply"] is False


def test_calibration_source_bundle_includes_panic_buying_read_only(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "REPORT_DIR", tmp_path / "report")
    panic_path = tmp_path / "report" / "panic_buying" / "panic_buying_2026-05-13.json"
    panic_path.parent.mkdir(parents=True, exist_ok=True)
    panic_path.write_text(
        json.dumps(
            {
                "report_type": "panic_buying",
                "panic_buy_state": "PANIC_BUY",
                "panic_buy_regime_mode": "PANIC_BUY_CONTINUATION",
                "panic_buy_regime_contract": {
                    "decision_authority": "source_quality_only",
                    "runtime_effect": "report_only_no_mutation",
                    "allowed_actions": ["report_runner_hold_candidate"],
                    "forbidden_uses": ["auto_buy", "full_market_sell"],
                },
                "risk_regime_gate_state": "watch",
                "risk_regime_gate_authority": "source_quality_only",
                "risk_regime_threshold_mode": "dynamic_quantile",
                "risk_regime_gate": {
                    "confirmed_evidence_count": 2,
                    "source_quality_blockers": ["panic_buy_local_unconfirmed_by_market_breadth"],
                },
                "policy": {"runtime_effect": "report_only_no_mutation"},
                "panic_buy_metrics": {
                    "panic_buy_active_count": 2,
                    "panic_buy_watch_count": 1,
                    "max_panic_buy_score": 0.88,
                    "avg_confidence": 0.72,
                },
                "exhaustion_metrics": {
                    "exhaustion_candidate_count": 1,
                    "exhaustion_confirmed_count": 0,
                    "max_exhaustion_score": 0.67,
                },
                "tp_counterfactual_summary": {
                    "candidate_context_count": 3,
                    "tp_like_exit_count": 2,
                    "trailing_winner_count": 1,
                },
                "microstructure_detector": {
                    "panic_buy_signal_count": 3,
                    "missing_orderbook_count": 2,
                    "missing_trade_aggressor_count": 1,
                    "carried_orderbook_snapshot_count": 4,
                    "carried_trade_aggressor_snapshot_count": 5,
                },
                "market_breadth_context": {
                    "market_panic_breadth_source_quality_status": "ok",
                    "market_panic_breadth_risk_on_advisory": False,
                    "market_panic_breadth_risk_off_advisory": True,
                    "market_wide_panic_buy_confirmed": False,
                },
                "canary_candidates": [
                    {"family": "panic_buy_runner_tp_canary", "status": "report_only_candidate"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    bundle = report_mod._summarize_calibration_report_sources("2026-05-13")
    metrics = bundle["source_metrics"]["panic_buying"]

    assert bundle["sources"]["panic_buying"]["exists"] is True
    assert metrics["panic_buy_state"] == "PANIC_BUY"
    assert metrics["panic_buy_regime_mode"] == "PANIC_BUY_CONTINUATION"
    assert metrics["panic_buy_regime_decision_authority"] == "source_quality_only"
    assert metrics["panic_buy_regime_runtime_effect"] == "report_only_no_mutation"
    assert metrics["risk_regime_gate_state"] == "watch"
    assert metrics["risk_regime_gate_authority"] == "source_quality_only"
    assert metrics["risk_regime_threshold_mode"] == "dynamic_quantile"
    assert metrics["confirmed_evidence_count"] == 2
    assert "report_runner_hold_candidate" in metrics["panic_buy_regime_allowed_actions"]
    assert "full_market_sell" in metrics["panic_buy_regime_forbidden_uses"]
    assert metrics["runtime_effect"] == "report_only_no_mutation"
    assert metrics["panic_buy_active_count"] == 2
    assert metrics["max_panic_buy_score"] == 0.88
    assert metrics["tp_counterfactual_count"] == 3
    assert metrics["candidate_status"]["panic_buy_runner_tp_canary"] == "report_only_candidate"
    assert metrics["allowed_runtime_apply"] is False
    assert metrics["market_breadth_risk_on_advisory"] is False
    assert metrics["market_breadth_risk_off_advisory"] is True
    assert metrics["market_wide_panic_buy_confirmed"] is False
    assert metrics["missing_orderbook_count"] == 2
    assert "panic_buy_local_unconfirmed_by_market_breadth" in metrics["source_quality_blockers"]
    assert "panic_buy_orderbook_collector_coverage_gap" in metrics["source_quality_blockers"]


def test_calibration_source_bundle_audits_report_only_cleanup_candidates(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "REPORT_DIR", tmp_path / "report")
    sentinel_path = tmp_path / "report" / "sentinel_followup_2026-05-13.md"
    add_blocked_path = tmp_path / "report" / "monitor_snapshots" / "add_blocked_lock_2026-05-13.json"
    add_blocked_path.parent.mkdir(parents=True, exist_ok=True)
    sentinel_path.write_text("# legacy follow-up\n", encoding="utf-8")
    add_blocked_path.write_text(json.dumps({"total_blocked_events": 3}), encoding="utf-8")

    bundle = report_mod._summarize_calibration_report_sources("2026-05-13")
    audit = bundle["report_only_cleanup_audit"]
    candidates = {item["id"]: item for item in audit["cleanup_candidates"]}

    assert audit["metric_role"] == "source_quality_gate"
    assert audit["decision_authority"] == "source_quality_only"
    assert audit["primary_decision_metric"] == "cleanup_candidate_count"
    assert audit["source_quality_gate"] == "cleanup_candidate_count == 0"
    assert "runtime_threshold_apply" in audit["forbidden_uses"]
    assert "sentinel_followup" in candidates
    assert candidates["sentinel_followup"]["runtime_effect"] is False
    assert candidates["sentinel_followup"]["in_current_source_bundle"] is False
    assert candidates["add_blocked_lock"]["current_owner"] == "monitor_snapshot_reference_only"
    assert any("report-only cleanup candidate: sentinel_followup" in warning for warning in bundle["warnings"])


def test_calibration_source_bundle_reads_gzip_monitor_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "REPORT_DIR", tmp_path / "report")
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    with gzip.open(snapshot_dir / "post_sell_feedback_2026-05-13.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(
            {
                "soft_stop": {
                    "post_sell_soft_stop_total": 2,
                    "post_sell_rebound_above_sell_10m_rate": 50.0,
                }
            },
            handle,
        )

    bundle = report_mod._summarize_calibration_report_sources("2026-05-13")

    assert bundle["sources"]["post_sell_feedback"]["exists"] is True
    assert bundle["sources"]["post_sell_feedback"]["path"].endswith(".json.gz")
    assert bundle["sources"]["post_sell_feedback"]["loaded"] is True
    assert "soft_stop" in bundle["sources"]["post_sell_feedback"]["top_keys"]


def test_calibration_source_bundle_surfaces_rising_missed_refinement_action_plan(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "REPORT_DIR", tmp_path / "report")
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "missed_entry_counterfactual_2026-07-02.json").write_text(
        json.dumps(
            {
                "metrics": {
                    "rising_missed_refinement": {
                        "metric_role": "source_quality_gate",
                        "decision_authority": "postclose_source_only_refinement_no_runtime_apply",
                        "window_policy": "same_day_missed_entry_counterfactual_rows",
                        "sample_floor": 1,
                        "primary_decision_metric": "diagnostic_win_rate",
                        "source_quality_gate": "pipeline_stage_flow_and_counterfactual_outcome_present",
                        "rising_missed_candidate_count": 6,
                        "rising_missed_missed_winner_count": 5,
                        "rising_missed_avoided_loser_count": 1,
                        "rising_missed_missed_winner_rate": 83.33,
                        "rising_missed_avoided_loser_rate": 16.67,
                    },
                    "rising_missed_refinement_action_plan": {
                        "metric_role": "source_quality_gate",
                        "plan_type": "rising_missed_classifier_refinement_source_only",
                        "decision": "source_only_positive_prior_candidates_ready",
                        "operator_manual_query_required": "false",
                        "window_policy": "same_day_missed_entry_counterfactual_rows",
                        "sample_floor": 3,
                        "primary_decision_metric": "diagnostic_win_rate",
                        "source_quality_gate": "pipeline_stage_flow_and_counterfactual_outcome_present",
                        "runtime_effect": "false",
                        "allowed_runtime_apply": "false",
                        "decision_authority": "postclose_source_only_refinement_no_runtime_apply",
                        "positive_prior_candidates": [
                            {
                                "axis": "source_signature",
                                "key": "OPEN_TOP,PRICE_JUMP_START",
                                "evaluated_candidates": 6,
                                "missed_winner_rate": 83.33,
                                "avoided_loser_rate": 16.67,
                            }
                        ],
                        "exclusion_or_confirmation_candidates": [],
                        "hold_sample_candidates": [],
                        "next_actions": [
                            "surface_positive_prior_candidates_in_daily_calibration_source_bundle"
                        ],
                        "forbidden_uses": ["intraday_threshold_mutation", "broker_order_submit"],
                    },
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    bundle = report_mod._summarize_calibration_report_sources("2026-07-02")

    plan = bundle["source_metrics"]["rising_missed_refinement_action_plan"]
    assert plan["metric_role"] == "source_quality_gate"
    assert plan["decision"] == "source_only_positive_prior_candidates_ready"
    assert plan["operator_manual_query_required"] is False
    assert plan["window_policy"] == "same_day_missed_entry_counterfactual_rows"
    assert plan["sample_floor"] == 3
    assert plan["primary_decision_metric"] == "diagnostic_win_rate"
    assert plan["source_quality_gate"] == "pipeline_stage_flow_and_counterfactual_outcome_present"
    assert plan["runtime_effect"] is False
    assert plan["allowed_runtime_apply"] is False
    assert plan["rising_missed_candidate_count"] == 6
    assert plan["positive_prior_candidates"][0]["key"] == "OPEN_TOP,PRICE_JUMP_START"
    assert plan["next_actions"] == ["surface_positive_prior_candidates_in_daily_calibration_source_bundle"]


def test_soft_stop_calibration_holds_on_single_post_sell_source_sample():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-08",
        "sources": {
            "post_sell_feedback": {"path": "data/report/monitor_snapshots/post_sell_feedback_2026-05-08.json", "exists": True},
        },
        "source_metrics": {
            "soft_stop": {
                "post_sell_soft_stop_total": 1,
                "post_sell_rebound_above_sell_10m_rate": 100.0,
                "post_sell_rebound_above_buy_10m_rate": 100.0,
                "post_sell_rebound_above_sell_30m_rate": 100.0,
                "post_sell_rebound_above_buy_30m_rate": 100.0,
                "post_sell_rebound_above_sell_60m_rate": 100.0,
                "post_sell_rebound_above_buy_60m_rate": 100.0,
            },
        },
        "new_observation_axis_created": False,
    }
    pipeline_rows = [
        {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.82", "held_sec": "40"}}
        for _ in range(13)
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: pipeline_rows,
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
        calibration_run_phase="intraday",
    )

    candidate = next(
        item for item in report["calibration_candidates"] if item["family"] == "soft_stop_whipsaw_confirmation"
    )
    assert candidate["source_sample_count"] == 1
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["sample_floor_status"] == "hold_sample"
    assert candidate["runtime_change"] is False
    assert candidate["source_metrics"]["post_sell_rebound_above_buy_30m_rate"] == 100.0


def test_ai_correction_clamps_out_of_bounds_value_without_runtime_change():
    calibration_report = {
        "date": "2026-05-08",
        "meta": {"calibration_run_phase": "intraday"},
        "calibration_candidates": [
            {
                "family": "holding_flow_ofi_smoothing",
                "threshold_version": "holding_flow_ofi_smoothing:manifest_only:ready",
                "current_value": 90,
                "recommended_value": 90,
                "min_value": 30,
                "max_value": 120,
                "max_step_per_day": 15,
                "sample_floor": 20,
                "sample_count": 30,
                "source_sample_count": 30,
                "calibration_state": "hold",
                "window_policy": {"primary": "daily_intraday", "secondary": ["rolling_5d"], "daily_only_allowed": True},
                "allowed_runtime_apply": True,
            }
        ],
    }
    ai_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "holding_flow_ofi_smoothing",
                "anomaly_type": "defer_cost_spike",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "adjust_up",
                    "proposed_value": 200,
                    "anomaly_route": "threshold_candidate",
                    "sample_window": "daily_intraday",
                },
                "correction_reason": "defer cost deteriorated intraday",
                "required_evidence": ["holding_exit_sentinel"],
                "risk_flags": ["defer_cost"],
            }
        ],
    }

    review = report_mod.build_threshold_cycle_ai_correction_report(calibration_report, ai_raw_response=ai_response)

    item = review["items"][0]
    assert review["ai_status"] == "parsed"
    assert item["guard_accepted"] is True
    assert item["guard_decision"]["effective_value"] == 105
    assert item["guard_decision"]["clamped"] is True
    assert item["runtime_change"] is False
    assert item["final_source_of_truth"] == "deterministic_calibration_guard"


def test_ai_correction_keeps_soft_stop_single_sample_as_hold_sample():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-08",
        "sources": {"post_sell_feedback": {"path": "post_sell_feedback_2026-05-08.json", "exists": True}},
        "source_metrics": {
            "soft_stop": {
                "post_sell_soft_stop_total": 1,
                "post_sell_rebound_above_sell_30m_rate": 100.0,
                "post_sell_rebound_above_buy_30m_rate": 100.0,
            },
        },
        "new_observation_axis_created": False,
    }
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {"stage": "soft_stop_micro_grace", "fields": {"profit_rate": "-1.82", "held_sec": "40"}}
            for _ in range(13)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
        calibration_run_phase="intraday",
    )
    ai_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "soft_stop_whipsaw_confirmation",
                "anomaly_type": "late_rebound",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "adjust_up",
                    "proposed_value": 80,
                    "anomaly_route": "threshold_candidate",
                    "sample_window": "rolling_10d",
                },
                "correction_reason": "single late rebound case",
                "required_evidence": ["rolling soft-stop tail"],
                "risk_flags": ["single_case"],
            }
        ],
    }

    review = report_mod.build_threshold_cycle_ai_correction_report(report, ai_raw_response=ai_response)
    item = next(item for item in review["items"] if item["family"] == "soft_stop_whipsaw_confirmation")

    assert item["guard_accepted"] is False
    assert item["guard_decision"]["effective_state"] == "hold_sample"
    assert "window_policy_blocks_single_case_live_candidate" in item["guard_reject_reason"]
    deterministic = next(
        candidate for candidate in report["calibration_candidates"] if candidate["family"] == "soft_stop_whipsaw_confirmation"
    )
    assert deterministic["calibration_state"] == "hold_sample"


def test_ai_correction_instrumentation_gap_excludes_threshold_candidate_review():
    calibration_report = {
        "date": "2026-05-08",
        "run_phase": "postclose",
        "calibration_candidates": [
            {
                "family": "score65_74_recovery_probe",
                "threshold_version": "score65_74_recovery_probe:ready",
                "current_value": False,
                "recommended_value": True,
                "min_value": None,
                "max_value": None,
                "max_step_per_day": None,
                "sample_floor": 20,
                "sample_count": 50,
                "source_sample_count": 50,
                "calibration_state": "adjust_up",
                "window_policy": {"primary": "daily_intraday", "secondary": ["rolling_5d"], "daily_only_allowed": True},
                "allowed_runtime_apply": True,
            }
        ],
    }
    ai_response = {
        "schema_version": 1,
        "corrections": [
            {
                "family": "score65_74_recovery_probe",
                "anomaly_type": "partial_sample_zero",
                "ai_review_state": "correction_proposed",
                "correction_proposal": {
                    "proposed_state": "hold_sample",
                    "anomaly_route": "instrumentation_gap",
                    "sample_window": "daily_intraday",
                },
                "correction_reason": "partial fill provenance missing",
                "required_evidence": ["full/partial split"],
                "risk_flags": ["instrumentation_gap"],
            }
        ],
    }

    review = report_mod.build_threshold_cycle_ai_correction_report(calibration_report, ai_raw_response=ai_response)
    decision = review["items"][0]["guard_decision"]

    assert decision["guard_accepted"] is True
    assert decision["route_action"] == "exclude_from_threshold_candidate_review"
    assert decision["runtime_change"] is False


def test_ai_correction_parse_failure_keeps_deterministic_report_available():
    calibration_report = {
        "date": "2026-05-08",
        "run_phase": "intraday",
        "calibration_candidates": [
            {
                "family": "holding_flow_ofi_smoothing",
                "threshold_version": "holding_flow_ofi_smoothing:ready",
                "current_value": 90,
                "recommended_value": 90,
                "calibration_state": "hold",
                "allowed_runtime_apply": True,
            }
        ],
    }

    review = report_mod.build_threshold_cycle_ai_correction_report(
        calibration_report,
        ai_raw_response={"schema_version": 1, "corrections": [], "apply_now": True},
    )

    assert review["ai_status"] == "parse_rejected"
    assert review["items"][0]["ai_review_state"] == "unavailable"
    assert review["items"][0]["deterministic_state"] == "hold"
    assert review["items"][0]["runtime_change"] is False


def test_openai_threshold_ai_correction_uses_strict_schema_and_deep_model(monkeypatch):
    captured = {}

    class _FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                output_text=json.dumps({"schema_version": 1, "corrections": []}),
                usage=SimpleNamespace(input_tokens=123, output_tokens=45, total_tokens=168),
            )

    class _FakeOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key
            self.responses = _FakeResponses()

    monkeypatch.setattr(report_mod, "_load_threshold_ai_openai_keys", lambda: [("OPENAI_API_KEY", "test-key")])
    monkeypatch.setattr("openai.OpenAI", _FakeOpenAI)

    raw_response, status = report_mod._call_openai_threshold_ai_correction(
        {"calibration_candidates": [], "calibration_source_bundle": {}},
        run_phase="postclose",
    )

    assert json.loads(raw_response) == {"schema_version": 1, "corrections": []}
    assert status["provider"] == "openai"
    assert status["model"] == "gpt-5.5"
    assert status["reasoning_effort"] == "high"
    assert status["new_provider_call"] is True
    assert status["attempted_key_count"] == 1
    assert status["configured_key_count"] == 1
    assert status["attempted_model_count"] == 1
    assert status["input_context_hash"]
    assert status["prompt_chars"] >= status["input_context_chars"]
    assert status["output_chars"] == len(raw_response)
    assert status["input_tokens"] == 123
    assert status["output_tokens"] == 45
    assert status["total_tokens"] == 168
    assert status["cost_estimate_status"] == "missing_price_contract"
    assert captured["model"] == "gpt-5.5"
    assert captured["reasoning"]["effort"] == "high"
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["text"]["format"]["name"] == "threshold_ai_correction_v1"
    assert captured["text"]["format"]["strict"] is True
    assert captured["text"]["format"]["schema"]["additionalProperties"] is False
    assert "Domain glossary" in captured["instructions"]
    assert not any("\uac00" <= char <= "\ud7a3" for char in captured["instructions"])
    assert not any("\uac00" <= char <= "\ud7a3" for char in captured["input"])
    assert "Return only JSON" in captured["instructions"]


def test_threshold_ai_correction_fallback_prompt_is_english_ascii():
    prompt = report_mod._build_ai_correction_prompt({"note": "수급 확인"})

    assert "You are the threshold-cycle calibration AI reviewer" in prompt
    assert "\\uc218\\uae09" in prompt
    assert not any("\uac00" <= char <= "\ud7a3" for char in prompt)


def test_ai_correction_input_context_is_compact_and_hash_referenced():
    huge_metrics = {f"metric_{idx:03d}": {"values": list(range(100)), "note": "x" * 200} for idx in range(80)}
    calibration_report = {
        "date": "2026-05-20",
        "generated_at": "2026-05-21 08:00:00",
        "run_phase": "postclose",
        "calibration_candidates": [
            {
                "family": "soft_stop_whipsaw_confirmation",
                "threshold_version": "v1",
                "current_value": 60,
                "recommended_value": 70,
                "calibration_state": "adjust_up",
                "source_metrics": huge_metrics,
            }
        ],
        "calibration_source_bundle": {
            "sources": {f"source_{idx}": {"exists": True, "path": f"artifact_{idx}.json"} for idx in range(50)},
            "source_metrics": huge_metrics,
            "warnings": ["warn"] * 30,
        },
        "trade_lifecycle_attribution": {
            "status": "ok",
            "records": [{"id": idx, "payload": "y" * 300} for idx in range(200)],
            "examples": [{"id": idx, "payload": "z" * 300} for idx in range(30)],
        },
    }
    cumulative_report = {
        "date": "2026-05-20",
        "generated_at": "2026-05-21 08:00:00",
        "summary": {"completed_valid_cumulative": 10},
        "threshold_snapshot_by_window": {
            "rolling_10d": {
                "soft_stop_whipsaw_confirmation": {"sample": huge_metrics, "recommended": {"confirm_sec": 70}},
            }
        },
        "calibration_source_bundle_by_window": {
            "rolling_10d": {"sources": {}, "source_metrics": huge_metrics, "warnings": []},
        },
        "completed_by_source": huge_metrics,
        "source_flags": huge_metrics,
    }

    context = report_mod._build_ai_correction_input_context(
        calibration_report,
        cumulative_report,
        source_calibration_report_path="data/report/threshold_cycle_calibration/example.json",
    )

    assert report_mod._json_chars(context) <= report_mod.AI_CORRECTION_CONTEXT_TOTAL_CHAR_LIMIT
    assert context["_context_budget"]["full_blob_policy"] == "hash_and_path_reference_only"
    candidate = context["calibration_candidates"][0]
    assert "source_metrics_summary" in candidate
    assert "source_metrics_full_hash" in candidate
    assert "source_metrics" not in candidate
    assert context["source_artifact_references"]["calibration_report"]["full_hash"]
    calibration_report["generated_at"] = "2026-05-21 08:30:00"
    cumulative_report["generated_at"] = "2026-05-21 08:30:00"
    rerun_context = report_mod._build_ai_correction_input_context(
        calibration_report,
        cumulative_report,
        source_calibration_report_path="data/report/threshold_cycle_calibration/example.json",
    )
    assert report_mod._json_sha256(context) == report_mod._json_sha256(rerun_context)


def test_reuse_ai_review_requires_matching_input_hash(tmp_path):
    input_hash = "abc123"
    path = tmp_path / "threshold_cycle_ai_review_2026-05-20_postclose.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": report_mod.THRESHOLD_AI_CORRECTION_SCHEMA_VERSION,
                "ai_status": "parsed",
                "input_context_hash": input_hash,
                "ai_provider_status": {"provider": "openai", "status": "success"},
                "items": [],
            }
        ),
        encoding="utf-8",
    )

    reused = report_mod._load_reusable_threshold_ai_review(path, input_context_hash=input_hash)
    assert reused is not None
    assert reused["ai_provider_status"]["status"] == "reused_valid_artifact"
    assert reused["ai_provider_status"]["new_provider_call"] is False
    assert reused["reuse_guard"]["status"] == "reused"
    assert report_mod._load_reusable_threshold_ai_review(path, input_context_hash="different") is None


def test_calibration_report_sources_preserve_buy_funnel_latency_microstructure_counts(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    buy_dir = report_dir / "buy_funnel_sentinel"
    buy_dir.mkdir(parents=True)
    target_date = "2099-01-05"
    (buy_dir / f"buy_funnel_sentinel_{target_date}.json").write_text(
        json.dumps(
            {
                "classification": {
                    "primary": "PRICE_GUARD_DROUGHT",
                    "matches": ["PRICE_GUARD_DROUGHT", "LATENCY_DROUGHT"],
                    "secondary": ["LATENCY_DROUGHT"],
                    "submit_drought_root_cause": {
                        "latency_root_cause_counts": {
                            "spread_microstructure_guard": 17,
                            "spread_or_slippage_guard": 5,
                            "quote_stale": 3,
                        }
                    },
                },
                "current": {"session": {"stage_events": {}, "ratios": {}}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(report_mod, "REPORT_DIR", report_dir)

    bundle = report_mod._summarize_calibration_report_sources(target_date)
    metrics = bundle["source_metrics"]["buy_score65_74"]

    assert metrics["sentinel_matches"] == ["PRICE_GUARD_DROUGHT", "LATENCY_DROUGHT"]
    assert metrics["latency_root_cause_counts"]["spread_microstructure_guard"] == 17
    assert metrics["latency_spread_microstructure_guard_count"] == 17
    assert metrics["latency_spread_or_slippage_guard_count"] == 5
    assert metrics["latency_quote_stale_count"] == 3


def test_efficient_tradeoff_calibration_adds_entry_bad_entry_and_adm_candidates():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-07",
        "sources": {
            "buy_funnel_sentinel": {"path": "data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-07.json", "exists": True},
            "wait6579_ev_cohort": {"path": "data/report/monitor_snapshots/wait6579_ev_cohort_2026-05-07.json", "exists": True},
            "holding_exit_decision_matrix": {"path": "data/report/holding_exit_decision_matrix/holding_exit_decision_matrix_2026-05-07.json", "exists": True},
            "statistical_action_weight": {"path": "data/report/statistical_action_weight/statistical_action_weight_2026-05-07.json", "exists": True},
        },
        "source_metrics": {
            "buy_score65_74": {
                "sentinel_primary": "UPSTREAM_AI_THRESHOLD",
                "sentinel_secondary": ["LATENCY_DROUGHT"],
                "score65_74_candidates": 191,
                "score65_74_avg_expected_ev_pct": 4.7,
                "score65_74_avg_close_10m_pct": 5.5,
                "full_samples": 181,
                "partial_samples": 0,
                "threshold_relaxation_approved": False,
                "partial_sample_zero_is_calibration_target": True,
                "budget_pass": 30,
                "order_bundle_submitted": 10,
            },
            "latency_guard_miss_ev_recovery": {
                "evaluated_candidates": 10,
                "avg_close_10m_pct": 1.2,
                "performance_latency_block_events": 10,
                "events_without_counterfactual": 0,
                "next_action": "use_latency_block_ev_for_refined_guard_review",
            },
            "bad_entry": {
                "refined_candidate": 441,
                "soft_stop_tail_sample": 20,
                "holding_flow_override_defer_exit": 67,
                "sell_order_sent": 9,
                "sell_completed": 9,
            },
            "decision_support": {
                "matrix_version": "holding_exit_decision_matrix_v1_2026-05-07",
                "matrix_entries": 14,
                "matrix_non_clear_edge": 0,
                "matrix_no_clear_edge": 14,
                "saw_candidate_weight_source": 7,
                "saw_defensive_only_high_loss_rate": 4,
                "saw_insufficient_sample": 3,
            },
        },
        "new_observation_axis_created": False,
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-07",
        pipeline_loader=lambda target_date: [
            {"stage": "bad_entry_refined_candidate", "fields": {"would_exit": "True"}}
            for _ in range(12)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidates = {item["family"]: item for item in report["calibration_candidates"]}
    assert candidates["score65_74_recovery_probe"]["apply_mode"] == "efficient_tradeoff_canary_candidate"
    assert candidates["score65_74_recovery_probe"]["calibration_state"] == "adjust_up"
    assert candidates["score65_74_recovery_probe"]["source_metrics"]["partial_samples"] == 0
    assert candidates["dynamic_entry_price_resolver"]["source_metrics"]["events_without_counterfactual"] == 0
    assert (
        candidates["dynamic_entry_price_resolver"]["source_metrics"]["next_action"]
        == "use_latency_block_ev_for_refined_guard_review"
    )
    assert candidates["bad_entry_refined_canary"]["apply_mode"] == "efficient_tradeoff_canary_candidate"
    assert candidates["bad_entry_refined_canary"]["source_metrics"]["holding_flow_override_defer_exit"] == 67
    assert candidates["holding_exit_decision_matrix_advisory"]["calibration_state"] == "hold_no_edge"
    assert candidates["holding_exit_decision_matrix_advisory"]["apply_mode"] == "report_only_calibration"
    assert candidates["holding_exit_decision_matrix_advisory"]["sample_floor_status"] == "minimum_edge_missing"


def test_score65_74_recovery_probe_does_not_use_raw_panic_adjusted_floor():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-12",
        "sources": {
            "buy_funnel_sentinel": {"path": "data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-12.json", "exists": True},
            "wait6579_ev_cohort": {"path": "data/report/monitor_snapshots/wait6579_ev_cohort_2026-05-12.json", "exists": True},
            "panic_sell_defense": {"path": "data/report/panic_sell_defense/panic_sell_defense_2026-05-12.json", "exists": True},
        },
        "source_metrics": {
            "buy_score65_74": {
                "sentinel_primary": "UPSTREAM_AI_THRESHOLD",
                "sentinel_secondary": [],
                "panic_state": "RECOVERY_WATCH",
                "panic_detected": True,
                "panic_by_stop_loss_count": True,
                "risk_regime_gate_state": "watch",
                "score65_74_candidates": 14,
                "wait6579_total_candidates": 14,
                "score65_74_avg_expected_ev_pct": 2.2277,
                "score65_74_avg_close_10m_pct": 2.5788,
                "score65_74_avg_mfe_10m_pct": 3.886,
                "full_samples": 14,
                "partial_samples": 0,
                "threshold_relaxation_approved": False,
                "budget_pass": 0,
                "latency_pass": 0,
                "order_bundle_submitted": 0,
                "submitted_to_budget_unique_pct": 0.0,
            }
        },
        "new_observation_axis_created": False,
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-12",
        pipeline_loader=lambda target_date: [],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidate = {item["family"]: item for item in report["calibration_candidates"]}["score65_74_recovery_probe"]
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["sample_count"] == 14
    assert candidate["sample_floor"] == 20
    assert candidate["sample_floor_status"] == "hold_sample"
    assert candidate["recommended_values"]["enabled"] is False
    assert "sample floor" in candidate["calibration_reason"]


def test_score65_74_recovery_probe_opens_existing_entry_unlock_when_rolling_primary_ready():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-18",
        "sources": {
            "buy_funnel_sentinel": {"path": "data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-05-18.json", "exists": True},
            "wait6579_ev_cohort": {"path": "data/report/monitor_snapshots/wait6579_ev_cohort_2026-05-18.json", "exists": True},
            "panic_sell_defense": {"path": "data/report/panic_sell_defense/panic_sell_defense_2026-05-18.json", "exists": True},
        },
        "source_metrics": {
            "buy_score65_74": {
                "sentinel_primary": "UPSTREAM_AI_THRESHOLD",
                "sentinel_secondary": [],
                "panic_state": "NORMAL",
                "panic_regime_mode": "NORMAL",
                "panic_detected": False,
                "panic_by_stop_loss_count": False,
                "score65_74_candidates": 50,
                "wait6579_total_candidates": 50,
                "score65_74_avg_expected_ev_pct": 4.5216,
                "score65_74_avg_close_10m_pct": 5.243,
                "score65_74_avg_mfe_10m_pct": 7.7935,
                "full_samples": 50,
                "partial_samples": 0,
                "threshold_relaxation_approved": False,
                "budget_pass": 11,
                "latency_pass": 0,
                "order_bundle_submitted": 0,
                "submitted_to_budget_unique_pct": 0.0,
            }
        },
        "new_observation_axis_created": False,
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-18",
        pipeline_loader=lambda target_date: [],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidate = {item["family"]: item for item in report["calibration_candidates"]}["score65_74_recovery_probe"]
    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["sample_count"] == 50
    assert candidate["sample_floor_status"] == "ready"
    assert candidate["recommended_values"]["enabled"] is True
    assert candidate["source_metrics"]["entry_unlock_probe_ready"] is True
    assert "bounded entry probe" in candidate["calibration_reason"]


def test_score65_74_recovery_probe_reads_score60_74_alias_metrics():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-18",
        "sources": {
            "buy_funnel_sentinel": {"path": "sentinel.json", "exists": True},
            "wait6579_ev_cohort": {"path": "cohort.json", "exists": True},
        },
        "source_metrics": {
            "buy_score60_74": {
                "sentinel_primary": "UPSTREAM_AI_THRESHOLD",
                "sentinel_secondary": [],
                "panic_state": "NORMAL",
                "panic_regime_mode": "NORMAL",
                "panic_detected": False,
                "panic_by_stop_loss_count": False,
                "score60_74_candidates": 41,
                "wait6579_total_candidates": 41,
                "score60_74_avg_expected_ev_pct": 3.2,
                "score60_74_avg_close_10m_pct": 1.8,
                "score60_74_avg_mfe_10m_pct": 4.4,
                "full_samples": 41,
                "partial_samples": 0,
                "threshold_relaxation_approved": False,
                "budget_pass": 4,
                "latency_pass": 0,
                "order_bundle_submitted": 0,
            }
        },
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-18",
        pipeline_loader=lambda target_date: [],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidate = {item["family"]: item for item in report["calibration_candidates"]}["score65_74_recovery_probe"]
    assert candidate["sample_count"] == 41
    assert candidate["sample_floor_status"] == "ready"
    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["source_metrics"]["entry_unlock_probe_ready"] is True
    assert candidate["source_metrics"]["score60_74_avg_expected_ev_pct"] == 3.2


def test_scale_in_split_order_plan_counterfactual_candidates_are_apply_ready(tmp_path, monkeypatch):
    target_date = "2026-07-07"
    report_dir = tmp_path / "scale_in_split_order_plan"
    policy_file = tmp_path / "scale_in_split_order_policy_2026-07-07.json"
    report_dir.mkdir(parents=True)
    policy_file.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(report_mod, "SCALE_IN_SPLIT_ORDER_PLAN_DIR", report_dir)
    (report_dir / f"scale_in_split_order_plan_{target_date}.json").write_text(
        json.dumps(
            {
                "schema_version": "scale_in_split_order_plan_v1",
                "source_quality": {"status": "pass", "tuning_input_allowed": True},
                "input_summary": {
                    "avg_down_observation_count": 2,
                    "counterfactual_selected_count": 2,
                    "baseline_fallback_count": 0,
                    "price_observation_join_gap_count": 0,
                    "base_price_reconstruction_gap_count": 0,
                    "market_qty_split_only_count": 0,
                },
                "candidate_grid": [
                    {
                        "context_bucket": "unknown_strategy:late_loss_retry:normal",
                        "real_sample_count": 1,
                        "sim_sample_count": 0,
                        "policy_mode": "counterfactual_tick_band_selector",
                    }
                ],
                "recommended_policy": {
                    "policy_file": str(policy_file),
                    "policy_version": "scale_in_split_order_plan:test-counterfactual",
                    "candidates": [
                        {
                            "context_bucket": "unknown_strategy:late_loss_retry:normal",
                            "policy_mode": "counterfactual_tick_band_selector",
                            "runtime_apply_allowed": True,
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    family = report_mod._build_scale_in_split_order_plan_family(target_date=target_date)
    candidate = next(
        item
        for item in report_mod._build_calibration_candidates([family], {})
        if item["family"] == "scale_in_split_order_plan"
    )

    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["recommended_values"]["enabled"] is True
    assert candidate["recommended_values"]["policy_version"] == "scale_in_split_order_plan:test-counterfactual"
    assert candidate["source_metrics"]["counterfactual_selected_count"] == 2
    assert "counterfactual" in candidate["calibration_reason"]


def test_bad_entry_refined_candidate_waits_for_postclose_lifecycle_attribution(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "POST_SELL_DIR", tmp_path)
    (tmp_path / "post_sell_evaluations_2026-05-08.jsonl").write_text(
        json.dumps(
            {
                "recommendation_id": 5645,
                "outcome": "GOOD_EXIT",
                "exit_rule": "scalp_soft_stop_pct",
                "profit_rate": -1.75,
                "metrics_10m": {"mfe_pct": 0.713, "mae_pct": -11.058},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {
                "stage": "bad_entry_refined_candidate",
                "record_id": 5645,
                "fields": {
                    "exclusion_reason": "soft_stop_zone",
                    "would_exit": "False",
                    "should_exit": "False",
                },
            }
            for _ in range(10)
        ],
        report_source_loader=lambda target_date: {"sources": {}, "source_metrics": {}, "new_observation_axis_created": False},
        completed_rows_loader=lambda start_date, end_date: [],
    )

    family = report["threshold_snapshot"]["bad_entry_refined_canary"]
    lifecycle = family["sample"]["lifecycle_attribution"]
    assert lifecycle["post_sell_joined_records"] == 1
    assert lifecycle["final_type_counts"]["late_detected_soft_stop_zone"] == 1

    candidate = next(item for item in report["calibration_candidates"] if item["family"] == "bad_entry_refined_canary")
    assert candidate["calibration_state"] == "hold"
    assert candidate["source_metrics"]["post_sell_joined_candidate_records"] == 1
    assert candidate["source_metrics"]["late_detected_soft_stop_zone_records"] == 1
    assert candidate["runtime_change"] is False


def test_trade_lifecycle_attribution_splits_entry_holding_exit_and_post_sell_types(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "POST_SELL_DIR", tmp_path)
    (tmp_path / "post_sell_candidates_2026-05-08.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recommendation_id": 5645,
                        "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
                        "exit_rule": "scalp_soft_stop_pct",
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "recommendation_id": 6001,
                        "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
                        "exit_rule": "scalp_trailing_take_profit",
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (tmp_path / "post_sell_evaluations_2026-05-08.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recommendation_id": 5645,
                        "outcome": "GOOD_EXIT",
                        "exit_rule": "scalp_soft_stop_pct",
                        "profit_rate": -1.75,
                        "metrics_10m": {"mfe_pct": 0.7, "mae_pct": -11.0},
                    },
                    ensure_ascii=False,
                ),
                json.dumps(
                    {
                        "recommendation_id": 6001,
                        "outcome": "MISSED_UPSIDE",
                        "exit_rule": "scalp_trailing_take_profit",
                        "profit_rate": 0.5,
                        "metrics_10m": {"mfe_pct": 2.2, "mae_pct": -0.3},
                    },
                    ensure_ascii=False,
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-08",
        pipeline_loader=lambda target_date: [
            {
                "stage": "order_bundle_submitted",
                "record_id": 5645,
                "stock_code": "298830",
                "stock_name": "슈어소프트테크",
                "emitted_at": "2026-05-08T12:53:39",
                "fields": {"entry_order_lifecycle": "normal", "entry_price_guard": "latency_danger_override_defensive"},
            },
            {
                "stage": "bad_entry_refined_candidate",
                "record_id": 5645,
                "emitted_at": "2026-05-08T12:59:40",
                "fields": {"exclusion_reason": "soft_stop_zone", "would_exit": "False"},
            },
            {
                "stage": "exit_signal",
                "record_id": 5645,
                "stock_code": "298830",
                "stock_name": "슈어소프트테크",
                "emitted_at": "2026-05-08T12:59:53",
                "fields": {
                    "exit_rule": "scalp_soft_stop_pct",
                    "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
                    "profit_rate": "-1.87",
                },
            },
            {
                "stage": "sell_completed",
                "record_id": 5645,
                "emitted_at": "2026-05-08T12:59:54",
                "fields": {"exit_rule": "scalp_soft_stop_pct", "profit_rate": "-1.75"},
            },
            {
                "stage": "order_bundle_submitted",
                "record_id": 6001,
                "stock_code": "000001",
                "stock_name": "트레일링",
                "emitted_at": "2026-05-08T10:00:00",
                "fields": {"entry_order_lifecycle": "normal"},
            },
            {
                "stage": "exit_signal",
                "record_id": 6001,
                "stock_code": "000001",
                "stock_name": "트레일링",
                "emitted_at": "2026-05-08T10:05:00",
                "fields": {
                    "exit_rule": "scalp_trailing_take_profit",
                    "exit_decision_source": "HOLDING_FLOW_OVERRIDE",
                },
            },
            {
                "stage": "sell_completed",
                "record_id": 6001,
                "emitted_at": "2026-05-08T10:05:01",
                "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "0.5"},
            },
            {
                "stage": "order_bundle_submitted",
                "record_id": 7001,
                "stock_code": "000002",
                "stock_name": "미체결",
                "emitted_at": "2026-05-08T11:00:00",
                "fields": {"entry_order_lifecycle": "passive_probe"},
            },
            {
                "stage": "entry_order_cancel_confirmed",
                "record_id": 7001,
                "emitted_at": "2026-05-08T11:00:30",
                "fields": {"entry_order_lifecycle": "passive_probe"},
            },
        ],
        report_source_loader=lambda target_date: {"sources": {}, "source_metrics": {}, "new_observation_axis_created": False},
        completed_rows_loader=lambda start_date, end_date: [],
    )

    lifecycle = report["trade_lifecycle_attribution"]
    assert lifecycle["primary_type_counts"]["soft_stop_good_exit"] == 1
    assert lifecycle["primary_type_counts"]["trailing_early_exit"] == 1
    assert lifecycle["primary_type_counts"]["entry_unfilled_cancelled"] == 1
    assert lifecycle["family_views"]["bad_entry_refined"]["late_detected_soft_stop_zone"] == 1
    assert lifecycle["family_views"]["entry_price"]["entry_unfilled_cancelled"] == 1
    assert lifecycle["family_views"]["trailing"]["early_exit"] == 1


def test_scale_in_price_guard_calibration_uses_existing_sources_without_live_apply():
    report_sources = {
        "schema_version": 1,
        "target_date": "2026-05-07",
        "sources": {
            "holding_exit_sentinel": {
                "path": "data/report/holding_exit_sentinel/holding_exit_sentinel_2026-05-07.json",
                "exists": True,
            },
            "statistical_action_weight": {
                "path": "data/report/statistical_action_weight/statistical_action_weight_2026-05-07.json",
                "exists": True,
            },
        },
        "source_metrics": {
            "scale_in_price_guard": {
                "scale_in_price_resolved": 0,
                "scale_in_price_guard_block": 4,
                "scale_in_price_p2_observe": 0,
                "compact_scale_in_executed": 0,
                "avg_down_wait": 1,
                "pyramid_wait": 6,
            }
        },
        "new_observation_axis_created": False,
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-07",
        pipeline_loader=lambda target_date: [
            {
                "stage": "scale_in_price_guard_block",
                "fields": {
                    "add_type": "PYRAMID",
                    "reason": "micro_vwap_bp>60.0",
                    "spread_bps": "27.1",
                    "micro_vwap_bps": "70.0",
                },
            }
            for _ in range(4)
        ],
        report_source_loader=lambda target_date: report_sources,
        completed_rows_loader=lambda start_date, end_date: [],
    )

    candidate = next(item for item in report["calibration_candidates"] if item["family"] == "scale_in_price_guard")
    assert candidate["apply_mode"] == "report_only_calibration"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["runtime_change"] is False
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["sample_count"] == 7
    assert candidate["source_sample_count"] == 7
    assert candidate["source_metrics"]["compact_scale_in_executed"] == 0


def test_statistical_action_weight_report_buckets_completed_rows():
    completed_rows = [
        {
            "profit_rate": 0.8,
            "buy_price": 9000,
            "buy_time": "2026-04-30 09:10:00",
            "daily_volume": 1_000_000,
            "pyramid_count": 1,
        },
        {
            "profit_rate": 0.6,
            "buy_price": 9500,
            "buy_time": "2026-04-30 09:12:00",
            "daily_volume": 1_500_000,
            "pyramid_count": 1,
        },
        {
            "profit_rate": -0.7,
            "buy_price": 9500,
            "buy_time": "2026-04-30 09:16:00",
            "daily_volume": 1_200_000,
            "avg_down_count": 1,
        },
        {
            "profit_rate": 0.2,
            "buy_price": 22_000,
            "buy_time": "2026-04-30 10:05:00",
            "daily_volume": 6_000_000,
        },
        {
            "profit_rate": -0.3,
            "buy_price": 22_000,
            "buy_time": "2026-04-30 10:08:00",
            "daily_volume": 6_500_000,
        },
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [
            {"stage": "scale_in_executed", "fields": {"add_type": "PYRAMID"}},
            {"stage": "stat_action_decision_snapshot", "fields": {"chosen_action": "pyramid_wait"}},
            {"stage": "sell_completed", "fields": {"profit_rate": "0.8"}},
        ],
        completed_rows_loader=lambda start_date, end_date: completed_rows,
    )

    family = report["threshold_snapshot"]["statistical_action_weight"]
    assert family["sample"]["completed_valid"] == 5
    assert family["sample"]["pyramid_wait"] == 2
    assert family["sample"]["avg_down_wait"] == 1
    assert family["sample"]["compact_scale_in_executed"] == 1
    assert family["sample"]["compact_decision_snapshot"] == 1
    assert family["recommended"]["action_summary"]["pyramid_wait"]["avg_profit_rate"] == 0.7
    assert family["current"]["score_method"] == "empirical_bayes_lower_confidence_bound"
    first_price_bucket = family["recommended"]["by_price_bucket"][0]
    assert "best_confidence_adjusted_score" in first_price_bucket
    assert "policy_hint" in first_price_bucket
    assert family["recommended"]["data_completeness"]["volume_known"] == 5


def test_daily_threshold_cycle_keeps_sim_completed_out_of_family_candidate_input():
    real_rows = [
        {
            "profit_rate": -0.4,
            "strategy": "SCALPING",
            "buy_price": 12_000,
            "buy_time": "2026-05-14 09:10:00",
            "daily_volume": 1_000_000,
        }
    ]
    sim_event = {
        "event_type": "pipeline_event",
        "pipeline": "HOLDING_PIPELINE",
        "stage": "scalp_sim_sell_order_assumed_filled",
        "stock_name": "SIM",
        "stock_code": "000001",
        "emitted_date": "2026-05-14",
        "emitted_at": "2026-05-14T10:00:00",
        "fields": {
            "simulation_book": "scalp_ai_buy_all",
            "simulated_order": "True",
            "actual_order_submitted": "False",
            "sim_record_id": "SIM-1",
            "profit_rate": "5.0",
            "buy_price": "10000",
            "assumed_fill_price": "10500",
            "qty": "1",
        },
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-14",
        pipeline_loader=lambda target_date: [sim_event] if target_date == "2026-05-14" else [],
        completed_rows_loader=lambda start_date, end_date: real_rows,
    )

    assert report["summary"]["completed_valid_rolling_7d"] == 1
    assert report["summary"]["real_completed_valid_rolling_7d"] == 1
    assert report["summary"]["sim_completed_valid_rolling_7d"] == 1
    assert report["completed_by_source"]["real"]["sample"] == 1
    assert report["completed_by_source"]["sim"]["sample"] == 1
    assert report["completed_by_source"]["combined"]["sample"] == 2

    action_weight = report["threshold_snapshot"]["statistical_action_weight"]
    assert action_weight["sample"]["completed_valid"] == 1
    assert action_weight["recommended"]["data_completeness"]["price_known"] == 1

    sizing = report["threshold_snapshot"]["position_sizing_dynamic_formula"]
    assert sizing["sample"]["real_completed_valid"] == 1
    assert sizing["sample"]["real_completed_summary"]["avg_profit_rate"] == -0.4


def test_daily_threshold_cycle_joins_sim_post_sell_mfe_mae(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "POST_SELL_DIR", tmp_path)
    (tmp_path / "sim_post_sell_evaluations_2026-05-18.jsonl").write_text(
        json.dumps(
            {
                "post_sell_id": "SIMPOST1",
                "sim_record_id": "SIM-005950-1",
                "sim_parent_record_id": "PARENT-1",
                "stock_code": "005950",
                "stock_name": "이수화학",
                "outcome": "MISSED_UPSIDE",
                "profit_rate": -2.54,
                "runtime_effect": False,
                "actual_order_submitted": False,
                "metrics_10m": {"mfe_pct": 4.45, "mae_pct": -0.47, "close_ret_pct": 3.9},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    sim_event = {
        "event_type": "pipeline_event",
        "pipeline": "HOLDING_PIPELINE",
        "stage": "scalp_sim_sell_order_assumed_filled",
        "stock_name": "이수화학",
        "stock_code": "005950",
        "emitted_date": "2026-05-18",
        "emitted_at": "2026-05-18T10:00:00",
        "fields": {
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": "False",
            "sim_record_id": "SIM-005950-1",
            "sim_parent_record_id": "PARENT-1",
            "profit_rate": "-2.54",
            "buy_price": "10000",
            "assumed_fill_price": "9746",
            "qty": "1",
        },
    }

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-18",
        pipeline_loader=lambda target_date: [sim_event] if target_date == "2026-05-18" else [],
        completed_rows_loader=lambda start_date, end_date: [],
    )

    join = report["scalp_simulator"]["post_sell_join"]
    assert join["joined_completed"] == 1
    assert join["pending_completed"] == 0
    assert join["outcome_counts"]["MISSED_UPSIDE"] == 1
    assert join["avg_mfe_10m_pct"] == 4.45
    assert join["runtime_effect"] is False
    assert join["decision_authority"] == "sim_equal_weight_observation_only"


def test_statistical_action_weight_reports_eligible_but_not_chosen(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "POST_SELL_DIR", tmp_path)
    (tmp_path / "post_sell_evaluations_2026-04-30.jsonl").write_text(
        json.dumps(
            {
                "recommendation_id": 1001,
                "outcome": "MISSED_UPSIDE",
                "exit_rule": "scalp_soft_stop_pct",
                "profit_rate": -1.2,
                "metrics_10m": {"mfe_pct": 1.4, "mae_pct": -0.8},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [
            {
                "stage": "stat_action_decision_snapshot",
                "record_id": 1001,
                "stock_code": "000100",
                "fields": {
                    "chosen_action": "hold_wait",
                    "eligible_actions": "hold_wait|exit_now|pyramid_wait",
                    "rejected_actions": "exit_now:no_sell_signal",
                    "profit_rate": "-0.4",
                    "peak_profit": "0.2",
                    "drawdown_from_peak": "0.6",
                    "current_ai_score": "62",
                },
            }
        ],
        completed_rows_loader=lambda start_date, end_date: [],
    )

    eligible = report["threshold_snapshot"]["statistical_action_weight"]["recommended"]["eligible_but_not_chosen"]
    assert eligible["status"] == "report_only"
    assert eligible["sample_snapshots"] == 1
    assert eligible["sample_candidates"] == 2
    assert eligible["post_sell_joined_candidates"] == 2
    chosen_row = next(row for row in eligible["chosen_action_summary"] if row["chosen_action"] == "hold_defer")
    assert chosen_row["sample"] == 1
    exit_row = next(row for row in eligible["action_summary"] if row["candidate_action"] == "exit_only")
    assert exit_row["avg_post_decision_mfe_10m_proxy"] == 1.4

    artifact = report_mod.build_statistical_action_weight_artifact(report)
    markdown = report_mod.render_statistical_action_weight_markdown(artifact)
    assert "Eligible But Not Chosen" in markdown
    assert "Chosen Action Proxy" in markdown
    assert "post_decision_*_proxy" in markdown

    matrix = report_mod.build_holding_exit_decision_matrix(report)
    proxy_summary = matrix["counterfactual_proxy_summary"]
    assert proxy_summary["sample_snapshots"] == 1
    assert proxy_summary["per_action_samples"]["hold_defer"] == 1
    assert proxy_summary["per_action_samples"]["exit_only"] == 1
    assert proxy_summary["per_action_samples"]["pyramid_wait"] == 1
    assert proxy_summary["missing_actions"] == ["avg_down_wait"]


def test_ofi_ai_smoothing_families_generate_manifest_only_candidates():
    pipeline_rows = []
    for record_id in range(1, 7):
        pipeline_rows.append(
            {
                "stage": "entry_ai_price_ofi_skip_demoted",
                "record_id": record_id,
                "fields": {
                    "orderbook_micro_state": "neutral",
                    "entry_ai_price_ofi_regime": "neutral",
                    "orderbook_micro_snapshot_age_ms": "120",
                },
            }
        )
        pipeline_rows.append({"stage": "order_bundle_submitted", "record_id": record_id, "fields": {}})
        pipeline_rows.append({"stage": "sell_completed", "record_id": record_id, "fields": {"profit_rate": "0.20"}})
    pipeline_rows.extend(
        {
            "stage": "entry_ai_price_canary_skip_order",
            "fields": {
                "orderbook_micro_state": "bearish",
                "orderbook_micro_snapshot_age_ms": "130",
            },
        }
        for _ in range(15)
    )
    pipeline_rows.extend(
        {
            "stage": "entry_ai_price_canary_skip_followup",
            "fields": {"mfe_bps": "20", "mae_bps": "-10"},
        }
        for _ in range(3)
    )
    for record_id in range(101, 107):
        pipeline_rows.append(
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "record_id": record_id,
                "fields": {
                    "smoothing_action": "DEBOUNCE_EXIT",
                    "holding_flow_ofi_regime": "stable_bullish",
                    "orderbook_micro_state": "bullish",
                    "worsen_from_candidate": "0.10",
                },
            }
        )
        pipeline_rows.append({"stage": "sell_completed", "record_id": record_id, "fields": {"profit_rate": "0.30"}})
    for record_id in range(201, 216):
        pipeline_rows.append(
            {
                "stage": "holding_flow_ofi_smoothing_applied",
                "record_id": record_id,
                "fields": {
                    "smoothing_action": "CONFIRM_EXIT",
                    "holding_flow_ofi_regime": "stable_bearish",
                    "orderbook_micro_state": "bearish",
                    "worsen_from_candidate": "0.34",
                },
            }
        )
    pipeline_rows.append(
        {
            "stage": "holding_flow_ofi_smoothing_applied",
            "record_id": 301,
            "fields": {
                "smoothing_action": "NO_CHANGE",
                "holding_flow_ofi_regime": "neutral",
                "orderbook_micro_state": "neutral",
                "worsen_from_candidate": "0.05",
            },
        }
    )
    pipeline_rows.append({"stage": "holding_flow_override_force_exit", "fields": {"force_reason": "worsen_floor"}})
    pipeline_rows.append(
        {
            "stage": "holding_flow_override_force_exit",
            "fields": {
                "force_reason": "max_defer_sec",
                "ofi_force_exit_phase": "post_debounce_guard",
                "ofi_force_exit_terminal_reason": "max_defer_sec",
                "ofi_debounce_profit_delta": "-0.25",
            },
        }
    )
    pipeline_rows.append(
        {
            "stage": "holding_flow_override_force_exit",
            "fields": {
                "force_reason": "ws_stale",
                "ofi_force_exit_phase": "source_quality_guard",
                "ofi_force_exit_terminal_reason": "ws_stale",
            },
        }
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: pipeline_rows,
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=True,
    )

    entry_family = report["threshold_snapshot"]["entry_ofi_ai_smoothing"]
    assert entry_family["apply_ready"] is True
    assert entry_family["apply_mode"] == "manifest_only"
    assert entry_family["sample"]["demoted"] == 6
    assert entry_family["sample"]["demoted_submitted"] == 6
    assert entry_family["sample"]["demoted_completed"] == 6
    assert entry_family["recommended"]["entry_skip_demotion_confidence_upper"] == 90

    holding_family = report["threshold_snapshot"]["holding_flow_ofi_smoothing"]
    assert holding_family["apply_ready"] is True
    assert holding_family["apply_mode"] == "manifest_only"
    assert holding_family["sample"]["exit_debounce"] == 6
    assert holding_family["sample"]["bearish_confirm"] == 15
    assert holding_family["sample"]["no_change"] == 1
    assert holding_family["sample"]["effective_action_count"] == 21
    assert holding_family["sample"]["force_exit_priority"] == 3
    assert holding_family["sample"]["force_exit_before_smoothing"] == 1
    assert holding_family["sample"]["force_exit_after_debounce"] == 1
    assert holding_family["sample"]["force_exit_source_quality_guard"] == 1
    assert holding_family["sample"]["force_exit_phase"] == {
        "pre_smoothing_guard": 1,
        "post_debounce_guard": 1,
        "source_quality_guard": 1,
    }
    assert holding_family["sample"]["debounce_terminal_reason"] == {"max_defer_sec": 1}
    assert holding_family["sample"]["debounce_profit_delta_avg"] == -0.25
    assert holding_family["recommended"]["holding_bearish_confirm_worsen_pct"] == 0.3

    manifest_families = {
        item["family"]
        for item in report["apply_candidate_list"]
        if item["owner_rule"] == "manifest_only_no_runtime_mutation"
    }
    assert {"entry_ofi_ai_smoothing", "holding_flow_ofi_smoothing"} <= manifest_families


def test_scale_in_price_guard_family_generates_manifest_only_candidate():
    pipeline_rows = []
    for record_id in range(1, 13):
        pipeline_rows.append(
            {
                "stage": "scale_in_price_resolved",
                "record_id": record_id,
                "fields": {
                    "add_type": "PYRAMID",
                    "spread_bps": "42.5",
                    "micro_vwap_bps": "18.0",
                    "resolved_vs_curr_bps": "-12.0",
                    "effective_qty": "1",
                    "qty_reason": "pyramid_momentum_confirmed",
                },
            }
        )
        pipeline_rows.append({"stage": "scale_in_executed", "record_id": record_id, "fields": {"add_type": "PYRAMID"}})
    for record_id in range(101, 111):
        pipeline_rows.append(
            {
                "stage": "scale_in_price_guard_block",
                "record_id": record_id,
                "fields": {
                    "add_type": "PYRAMID",
                    "reason": "spread_too_wide",
                    "spread_bps": "91.0",
                    "micro_vwap_bps": "70.0",
                },
            }
        )
    for record_id in range(1, 4):
        pipeline_rows.append(
            {
                "stage": "scale_in_price_p2_observe",
                "record_id": record_id,
                "fields": {"add_type": "PYRAMID", "action": "SKIP"},
            }
        )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-05-06",
        pipeline_loader=lambda target_date: pipeline_rows,
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=True,
    )

    family = report["threshold_snapshot"]["scale_in_price_guard"]
    assert family["apply_ready"] is True
    assert family["apply_mode"] == "manifest_only"
    assert family["sample"]["resolved"] == 12
    assert family["sample"]["guard_block"] == 10
    assert family["sample"]["p2_observe"] == 3
    assert family["sample"]["block_reason"]["spread_too_wide"] == 10
    assert family["current"]["max_spread_bps"] == 80.0

    manifest_families = {
        item["family"]
        for item in report["apply_candidate_list"]
        if item["owner_rule"] == "manifest_only_no_runtime_mutation"
    }
    assert "scale_in_price_guard" in manifest_families
    candidate = next(item for item in report["calibration_candidates"] if item["family"] == "scale_in_price_guard")
    assert candidate["apply_mode"] == "report_only_calibration"
    assert candidate["calibration_state"] == "hold"
    assert candidate["allowed_runtime_apply"] is False


def test_position_sizing_dynamic_formula_generates_candidate_grid():
    pipeline_rows = []
    for record_id in range(1, 36):
        event = {
            "stage": "budget_pass",
            "record_id": record_id,
            "stock_code": f"{100000 + record_id:06d}",
            "fields": {
                "score": "82",
                "strategy": "SCALPING",
                "volatility_bucket": "mid",
                "liquidity_value": "850000000",
                "liquidity_bucket": "high",
                "spread_bps": "18.5",
                "price_band": "10000_30000",
                "recent_loss_bucket": "none",
                "portfolio_exposure_bucket": "low",
                "target_budget": "500000.0",
                "resolved_price": "10000.0",
                "actual_order_submitted": "true",
            },
        }
        pipeline_rows.append(event)

    completed_rows = [{"profit_rate": 0.5, "strategy": "SCALPING", "stock_code": f"{100000 + i:06d}", "buy_price": 10000, "buy_qty": 5} for i in range(1, 21)] + [
        {"profit_rate": -0.2, "strategy": "SCALPING", "stock_code": f"{100000 + (i + 20):06d}", "buy_price": 8000, "buy_qty": 4} for i in range(1, 16)
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-06-10",
        pipeline_loader=lambda target_date: pipeline_rows,
        completed_rows_loader=lambda start_date, end_date: completed_rows,
        skip_completed_rows=False,
    )

    family = report["threshold_snapshot"]["position_sizing_dynamic_formula"]
    assert family["apply_ready"] is True
    assert family["apply_mode"] == "candidate_grid_comparison"
    assert family["current"]["runtime_apply_allowed"] is False
    assert family["current"]["formula_version"] == "linear_10_30_current"
    candidate_grid = family["candidate_grid"]
    assert isinstance(candidate_grid, list)
    assert len(candidate_grid) == 7
    baseline = candidate_grid[0]
    assert baseline["formula_candidate_id"] == "linear_10_30_current"
    assert baseline["formula_type"] == "baseline"
    assert baseline["real_sample_count"] > 0
    assert baseline["real_completed_overall_ev_pct"] is not None
    assert baseline["source_quality_blocked"] is False
    assert baseline["real_actual_order_submitted_count"] > 0

    candidate = next(item for item in report["calibration_candidates"] if item["family"] == "position_sizing_dynamic_formula")
    assert candidate["calibration_state"] == "hold"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["human_approval_required"] is False


def test_position_sizing_dynamic_formula_enters_candidate_grid_chain():
    pipeline_rows = []
    for record_id in range(1, 36):
        pipeline_rows.append(
            {
                "stage": "budget_pass",
                "record_id": record_id,
                "fields": {
                    "score": "82",
                    "strategy": "SCALPING",
                    "volatility_bucket": "mid",
                    "liquidity_value": "850000000",
                    "liquidity_bucket": "high",
                    "spread_bps": "18.5",
                    "price_band": "10000_30000",
                    "recent_loss_bucket": "none",
                    "portfolio_exposure_bucket": "low",
                    "target_budget": "500000.0",
                    "resolved_price": "10000.0",
                    "actual_order_submitted": "true",
                },
            }
        )
    pipeline_rows.append(
        {
            "stage": "scalp_sim_buy_order_assumed_filled",
            "record_id": "SIM-1",
            "fields": {
                "qty_source": "sim_virtual_budget_dynamic_formula",
                "actual_order_submitted": "false",
                "budget_authority": "sim_virtual_not_real_orderable_amount",
            },
        }
    )
    completed_rows = [
        {"profit_rate": 0.4, "strategy": "SCALPING", "buy_price": 10000, "buy_qty": 2}
        for _ in range(20)
    ] + [
        {"profit_rate": -0.2, "strategy": "SCALPING", "buy_price": 20000, "buy_qty": 1}
        for _ in range(15)
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-06-10",
        pipeline_loader=lambda target_date: pipeline_rows,
        completed_rows_loader=lambda start_date, end_date: completed_rows,
        skip_completed_rows=False,
    )

    family = report["threshold_snapshot"]["position_sizing_dynamic_formula"]
    assert family["apply_mode"] == "candidate_grid_comparison"
    assert family["apply_ready"] is True
    assert family["sample"]["real_completed_valid"] == 35
    assert family["sample"]["source_quality_passed"] is True
    assert family["sample"]["notional_weighted_ev_pct"] is not None
    assert len(family["candidate_grid"]) == 7
    baseline = family["candidate_grid"][0]
    assert baseline["formula_candidate_id"] == "linear_10_30_current"
    assert baseline["real_sample_count"] > 0
    assert baseline["source_quality_blocked"] is False

    candidate = next(
        item for item in report["calibration_candidates"] if item["family"] == "position_sizing_dynamic_formula"
    )
    assert candidate["calibration_state"] == "hold"
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["human_approval_required"] is False


def test_position_sizing_dynamic_formula_does_not_use_sim_as_real_floor():
    pipeline_rows = [
        {
            "stage": "scalp_sim_buy_order_assumed_filled",
            "record_id": f"SIM-{idx}",
            "fields": {
                "score": "88",
                "strategy": "SCALPING",
                "volatility_bucket": "mid",
                "liquidity_value": "850000000",
                "spread_bps": "18.5",
                "price_band": "10000_30000",
                "recent_loss_bucket": "none",
                "portfolio_exposure_bucket": "low",
                "qty_source": "sim_virtual_budget_dynamic_formula",
                "actual_order_submitted": "false",
                "budget_authority": "sim_virtual_not_real_orderable_amount",
            },
        }
        for idx in range(40)
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-06-10",
        pipeline_loader=lambda target_date: pipeline_rows,
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=False,
    )

    family = report["threshold_snapshot"]["position_sizing_dynamic_formula"]
    assert family["sample"]["real_completed_valid"] == 0
    assert family["sample"]["sim_probe_sizing_event_count"] == 40
    assert family["apply_ready"] is False
    assert len(family["candidate_grid"]) == 7
    for candidate_entry in family["candidate_grid"]:
        assert candidate_entry["real_sample_count"] == 0
        assert candidate_entry["sim_probe_sample_count"] >= 0
        assert candidate_entry["sim_probe_actual_order_submitted_false_count"] >= 0

    candidate = next(
        item for item in report["calibration_candidates"] if item["family"] == "position_sizing_dynamic_formula"
    )
    assert candidate["calibration_state"] == "hold_sample"
    assert candidate["allowed_runtime_apply"] is False


def test_position_sizing_dynamic_formula_candidate_grid_excludes_source_quality_blocked():
    pipeline_rows = []
    for record_id in range(1, 36):
        pipeline_rows.append(
            {
                "stage": "budget_pass",
                "record_id": record_id,
                "fields": {
                    "score": "75",
                    "strategy": "SCALPING",
                    "volatility_bucket": "mid",
                    "liquidity_value": "500000000",
                    "spread_bps": "25.0",
                    "price_band": "5000_15000",
                    "recent_loss_bucket": "none",
                    "portfolio_exposure_bucket": "low",
                    "target_budget": "300000.0",
                    "resolved_price": "8000.0",
                    "actual_order_submitted": "true",
                },
            }
        )

    completed_rows = [{"profit_rate": 0.7, "strategy": "SCALPING", "buy_price": 8000, "buy_qty": 5} for _ in range(16)] + [
        {"profit_rate": -0.1, "strategy": "SCALPING", "buy_price": 8000, "buy_qty": 4} for _ in range(16)
    ]

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-06-10",
        pipeline_loader=lambda target_date: pipeline_rows,
        completed_rows_loader=lambda start_date, end_date: completed_rows,
        skip_completed_rows=False,
    )

    family = report["threshold_snapshot"]["position_sizing_dynamic_formula"]
    assert family["apply_ready"] is True
    candidate_grid = family["candidate_grid"]
    assert len(candidate_grid) == 7
    for candidate_entry in candidate_grid:
        assert "formula_candidate_id" in candidate_entry
        assert "real_sample_count" in candidate_entry
        assert "sim_probe_sample_count" in candidate_entry
        assert candidate_entry["sim_probe_actual_order_submitted_false_count"] >= 0
    blocked = [c for c in candidate_grid if c.get("source_quality_blocked")]
    assert len(blocked) == 0


def test_build_daily_threshold_cycle_report_keeps_unready_family_observe_only():
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [],
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=True,
    )

    reversal_add = report["threshold_snapshot"]["reversal_add"]
    assert reversal_add["apply_ready"] is False
    assert reversal_add["recommended"]["max_hold_sec"] >= 120

    assert report["apply_candidate_list"] == []
    assert any("skip-db" in warning for warning in report["warnings"])


def test_default_pipeline_loader_prefers_compact_threshold_file(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(report_mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    report_mod.THRESHOLD_CYCLE_DIR.mkdir(parents=True, exist_ok=True)

    compact_path = report_mod.THRESHOLD_CYCLE_DIR / "threshold_events_2026-04-30.jsonl"
    compact_path.write_text(
        json.dumps(
            {
                "event_type": "threshold_cycle_event",
                "stage": "bad_entry_block_observed",
                "fields": {"held_sec": "70", "profit_rate": "-0.8", "peak_profit": "0.1", "ai_score": "40"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    rows = report_mod._default_pipeline_loader("2026-04-30")
    assert len(rows) == 1
    assert rows[0]["stage"] == "bad_entry_block_observed"


def test_default_pipeline_loader_prefers_partitioned_compact_over_legacy(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(report_mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    partition_dir = report_mod.THRESHOLD_CYCLE_DIR / "date=2026-04-30" / "family=bad_entry_block"
    partition_dir.mkdir(parents=True, exist_ok=True)
    (partition_dir / "part-000001.jsonl").write_text(
        json.dumps(
            {
                "event_type": "threshold_cycle_event",
                "stage": "bad_entry_block_observed",
                "fields": {"held_sec": "70"},
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    report_mod.THRESHOLD_CYCLE_DIR.mkdir(parents=True, exist_ok=True)
    (report_mod.THRESHOLD_CYCLE_DIR / "threshold_events_2026-04-30.jsonl").write_text(
        json.dumps({"event_type": "threshold_cycle_event", "stage": "budget_pass", "fields": {}}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    checkpoint_dir = report_mod.THRESHOLD_CYCLE_DIR / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    (checkpoint_dir / "2026-04-30.json").write_text(
        json.dumps({"completed": True, "paused_reason": None}, ensure_ascii=False),
        encoding="utf-8",
    )

    load_result = report_mod._default_pipeline_load_result("2026-04-30")
    assert [row["stage"] for row in load_result.rows] == ["bad_entry_block_observed"]
    assert load_result.meta["data_source"] == "partitioned_compact"
    assert load_result.meta["partition_count"] == 1
    assert load_result.meta["checkpoint_completed"] is True


def test_daily_threshold_cycle_report_does_not_reload_same_day_for_rolling_sim_rows():
    calls: Counter[str] = Counter()

    def pipeline_loader(target_date: str) -> list[dict]:
        calls[target_date] += 1
        if target_date == "2026-04-30":
            return [
                {"stage": "budget_pass", "fields": {"signal_score": "72"}},
                {
                    "stage": "scalp_sim_sell_order_assumed_filled",
                    "emitted_date": "2026-04-30",
                    "stock_code": "005930",
                    "fields": {
                        "profit_rate": "0.3",
                        "sim_record_id": "same-day-sim",
                        "assumed_fill_price": "70100",
                    },
                },
            ]
        if target_date == "2026-04-29":
            return [
                {
                    "stage": "scalp_sim_sell_order_assumed_filled",
                    "emitted_date": "2026-04-29",
                    "stock_code": "000660",
                    "fields": {
                        "profit_rate": "-0.2",
                        "sim_record_id": "prev-day-sim",
                        "assumed_fill_price": "180000",
                    },
                }
            ]
        if target_date == "2026-04-28":
            return [
                {
                    "stage": "scalp_sim_sell_order_assumed_filled",
                    "emitted_date": "2026-04-28",
                    "stock_code": "000660",
                    "fields": {
                        "profit_rate": "0.9",
                        "sim_record_id": "prev-day-sim",
                        "assumed_fill_price": "181000",
                    },
                }
            ]
        return []

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=pipeline_loader,
        report_source_loader=lambda target_date: {},
        completed_rows_loader=lambda start_date, end_date: [],
    )

    assert calls["2026-04-30"] == 1
    assert calls["2026-04-29"] == 1
    assert calls["2026-04-28"] == 1
    assert report["summary"]["event_count_same_day"] == 2
    assert report["summary"]["sim_completed_valid_rolling_7d"] == 2
    assert report["scalp_simulator"]["completed_profit_summary"]["sample"] == 1


def test_daily_threshold_cycle_report_includes_pipeline_load_meta(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(report_mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    partition_dir = report_mod.THRESHOLD_CYCLE_DIR / "date=2026-04-30" / "family=bad_entry_block"
    partition_dir.mkdir(parents=True, exist_ok=True)
    (partition_dir / "part-000001.jsonl").write_text(
        json.dumps({"event_type": "threshold_cycle_event", "stage": "bad_entry_block_observed", "fields": {}}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        completed_rows_loader=lambda start_date, end_date: [],
        skip_completed_rows=True,
    )

    assert report["meta"]["pipeline_load"]["2026-04-30"]["data_source"] == "partitioned_compact"
    assert report["summary"]["event_count_same_day"] == 1


def test_default_pipeline_load_result_reads_legacy_compact_gzip(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(report_mod, "THRESHOLD_CYCLE_DIR", tmp_path / "threshold_cycle")
    report_mod.THRESHOLD_CYCLE_DIR.mkdir(parents=True, exist_ok=True)
    compact_path = report_mod.THRESHOLD_CYCLE_DIR / "threshold_events_2026-04-30.jsonl.gz"
    with gzip.open(compact_path, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "event_type": "threshold_cycle_event",
                    "stage": "bad_entry_block_observed",
                    "fields": {},
                },
                ensure_ascii=False,
            )
            + "\n"
        )

    load_result = report_mod._default_pipeline_load_result("2026-04-30")

    assert [row["stage"] for row in load_result.rows] == ["bad_entry_block_observed"]
    assert load_result.meta["data_source"] == "legacy_compact"
    assert load_result.meta["read_bytes_estimate"] == compact_path.stat().st_size


def test_statistical_action_weight_artifacts_render_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "STAT_ACTION_REPORT_DIR", tmp_path / "statistical_action_weight")
    monkeypatch.setattr(report_mod, "AI_DECISION_MATRIX_DIR", tmp_path / "holding_exit_decision_matrix")
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [
            {"stage": "stat_action_decision_snapshot", "fields": {"chosen_action": "exit_now"}},
            {"stage": "sell_completed", "fields": {"profit_rate": "0.4"}},
        ],
        completed_rows_loader=lambda start_date, end_date: [
            {
                "profit_rate": 0.8,
                "buy_price": 9000,
                "buy_time": "2026-04-30 09:10:00",
                "daily_volume": 1_000_000,
            },
            {
                "profit_rate": 0.6,
                "buy_price": 9000,
                "buy_time": "2026-04-30 09:12:00",
                "daily_volume": 1_000_000,
                "pyramid_count": 1,
            },
        ],
    )

    json_path, md_path = report_mod.save_statistical_action_weight_artifact(report)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["family"] == "statistical_action_weight"
    assert payload["runtime_change"] is False
    assert "Statistical Action Weight Report" in markdown
    assert "Price Bucket" in markdown
    assert "compact_decision_snapshot" in markdown


def test_holding_exit_decision_matrix_artifact_contains_prompt_hints(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "AI_DECISION_MATRIX_DIR", tmp_path / "holding_exit_decision_matrix")
    report = report_mod.build_daily_threshold_cycle_report(
        "2026-04-30",
        pipeline_loader=lambda target_date: [],
        completed_rows_loader=lambda start_date, end_date: [
            {
                "profit_rate": 0.7,
                "buy_price": 9000,
                "buy_time": "2026-04-30 09:10:00",
                "daily_volume": 1_000_000,
            }
            for _ in range(8)
        ],
    )

    json_path, md_path = report_mod.save_holding_exit_decision_matrix(report)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["matrix_version"] == "holding_exit_decision_matrix_v1_2026-04-30"
    assert payload["runtime_change"] is False
    assert payload["hard_veto"]
    assert payload["entries"]
    assert payload["summary"]["entry_count"] == len(payload["entries"])
    assert payload["summary"]["non_no_clear_edge_count"] == 0
    assert payload["summary"]["no_clear_edge_count"] == len(payload["entries"])
    assert payload["summary"]["per_action_edge_buckets"] == {
        "prefer_exit": 0,
        "prefer_avg_down_wait": 0,
        "prefer_pyramid_wait": 0,
    }
    assert "prompt_hint" in payload["entries"][0]
    assert payload["instrumentation_status"] == "implemented"
    assert payload["instrumentation_contract_version"] == 1
    assert "counterfactual_proxy_summary.per_action_samples" in payload["provenance_contract"]
    assert "counterfactual_coverage" in payload["entries"][0]
    assert payload["counterfactual_coverage_summary"]["entry_count"] == len(payload["entries"])
    assert "exit_only" in payload["counterfactual_coverage_summary"]["per_action_samples"]
    assert payload["counterfactual_proxy_summary"]["required_actions"][0] == "hold_defer"
    assert "Holding/Exit Decision Matrix" in markdown
    assert "Counterfactual Coverage" in markdown
    assert "non_no_clear_edge_count" in markdown
    assert "per_action_edge_buckets" in markdown
    assert "proxy_per_action_samples" in markdown
    assert "Prompt Hints" in markdown


def test_cumulative_threshold_cycle_report_splits_windows_and_cohorts():
    pipeline_rows = {
        "2026-04-29": [{"stage": "budget_pass", "fields": {"signal_score": "72"}}],
        "2026-04-30": [
            {"stage": "bad_entry_block_observed", "fields": {"held_sec": "70", "profit_rate": "-0.8"}},
            {"stage": "exit_signal", "fields": {"exit_rule": "scalp_trailing_take_profit", "profit_rate": "0.6", "peak_profit": "1.0", "current_ai_score": "62"}},
        ],
    }
    completed_rows = [
        {"rec_date": "2026-04-28", "profit_rate": 0.4, "strategy": "SCALPING", "buy_price": 9000},
        {"rec_date": "2026-04-29", "profit_rate": -0.6, "strategy": "fallback_single", "buy_price": 9000},
        {"rec_date": "2026-04-30", "profit_rate": 1.2, "strategy": "SCALPING", "pyramid_count": 1, "last_add_type": "PYRAMID"},
        {"rec_date": "2026-04-30", "profit_rate": -0.9, "strategy": "SCALPING", "avg_down_count": 1, "last_add_type": "REVERSAL_ADD"},
        {"rec_date": "2026-04-30", "profit_rate": None, "strategy": "SCALPING"},
    ]

    report = report_mod.build_cumulative_threshold_cycle_report(
        "2026-04-30",
        start_date="2026-04-28",
        rolling_days=(2,),
        pipeline_loader=lambda target_date: pipeline_rows.get(target_date, []),
        completed_rows_loader=lambda start_date, end_date: completed_rows,
    )

    assert report["operator_decision"] == "report_only_review"
    assert report["source_flags"]["runtime_change"] is False
    assert report["summary"]["completed_valid_cumulative"] == 4
    assert report["completed_cohorts"]["cumulative"]["normal_only"]["sample"] == 3
    assert report["completed_cohorts"]["cumulative"]["pyramid_activated"]["sample"] == 1
    assert report["completed_cohorts"]["cumulative"]["reversal_add_activated"]["sample"] == 1
    assert report["completed_cohorts"]["rolling_2d"]["all_completed_valid"]["sample"] == 3
    assert report["summary"]["event_count_by_window"]["cumulative"] == 3
    assert "scalp_trailing_take_profit" in report["threshold_snapshot_by_window"]["rolling_2d"]
    assert report["apply_candidate_list_by_window"]["cumulative"] == []
    assert report["threshold_snapshot_by_window"]["cumulative"]["bad_entry_block"]["apply_mode"] == "report_only_reference"


def test_cumulative_threshold_cycle_report_artifacts_render_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(report_mod, "CUMULATIVE_THRESHOLD_REPORT_DIR", tmp_path / "threshold_cycle_cumulative")
    report = report_mod.build_cumulative_threshold_cycle_report(
        "2026-04-30",
        start_date="2026-04-30",
        rolling_days=(1,),
        pipeline_loader=lambda target_date: [{"stage": "budget_pass", "fields": {"signal_score": "72"}}],
        completed_rows_loader=lambda start_date, end_date: [
            {"rec_date": "2026-04-30", "profit_rate": 0.5, "strategy": "SCALPING", "buy_price": 9000},
        ],
    )

    json_path, md_path = report_mod.save_cumulative_threshold_cycle_report(report)
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    markdown = md_path.read_text(encoding="utf-8")

    assert payload["source_flags"]["application_mode"] == "report_only_cumulative_threshold_input"
    assert payload["source_flags"]["live_threshold_mutation"] is False
    assert "Cumulative Threshold Cycle Report" in markdown
    assert "Cohort Summary" in markdown
    assert "runtime_change: `False`" in markdown


def test_cumulative_threshold_cycle_report_renders_family_specific_denominator():
    report = report_mod.build_cumulative_threshold_cycle_report(
        "2026-04-30",
        start_date="2026-04-30",
        rolling_days=(1,),
        pipeline_loader=lambda target_date: [{"stage": "budget_pass", "fields": {"signal_score": "72"}}],
        completed_rows_loader=lambda start_date, end_date: [],
    )

    markdown = report_mod.render_cumulative_threshold_cycle_markdown(report)

    assert "| cumulative | score65_74_recovery_probe | entry | 0 | False | report_only_reference |" in markdown


def test_window_policy_audit_uses_registered_denominators_for_position_sizing():
    report = {
        "calibration_candidates": [
            {
                "family": "position_sizing_dynamic_formula",
                "sample_count": 4,
                "source_sample_count": 0,
                "sample_floor": 30,
                "calibration_state": "hold_sample",
                "apply_mode": "candidate_grid_comparison",
                "window_policy": {
                    "primary": "rolling_10d",
                    "secondary": ["daily", "cumulative_since_2026-04-21"],
                    "daily_only_allowed": False,
                },
            }
        ]
    }
    cumulative = {
        "threshold_snapshot_by_window": {
            "rolling_10d": {
                "position_sizing_dynamic_formula": {
                    "sample": {
                        "real_completed_valid": 16,
                        "sizing_event_count": 4280,
                    },
                    "sample_ready": False,
                }
            }
        }
    }

    report_mod.apply_window_policy_registry_to_report(report, cumulative)

    item = report["window_policy_audit"]["items"][0]
    assert item["sample_denominator_keys"] == ["real_completed_valid"]
    assert item["primary_sample_count"] == 16


def test_window_policy_registry_recomputes_candidate_from_ready_rolling_snapshot():
    report = {
        "calibration_candidates": [
            {
                "family": "protect_trailing_smoothing",
                "sample_count": 0,
                "source_sample_count": 0,
                "sample_floor": 20,
                "calibration_state": "hold_sample",
                "apply_mode": "report_only_calibration",
                "allowed_runtime_apply": True,
                "window_policy": {
                    "primary": "rolling_10d",
                    "secondary": ["daily"],
                    "daily_only_allowed": False,
                },
            }
        ]
    }
    cumulative = {
        "threshold_snapshot_by_window": {
            "rolling_10d": {
                "protect_trailing_smoothing": {
                    "sample": {"smooth_hold": 10, "smooth_confirmed": 10},
                    "sample_ready": True,
                    "current": {"window_sec": 20},
                    "recommended": {"window_sec": 30},
                }
            }
        }
    }

    report_mod.apply_window_policy_registry_to_report(report, cumulative)

    candidate = report["calibration_candidates"][0]
    assert candidate["calibration_state"] == "adjust_up"
    assert candidate["sample_count"] == 20
    assert candidate["decision_sample_window"] == "rolling_10d"
    assert candidate["apply_mode"] == "calibrated_apply_candidate"
    assert report["window_policy_audit"]["issue_counts"] == {}


def test_window_policy_registry_consumes_rolling_source_metrics_when_snapshot_sample_is_empty():
    report = {
        "calibration_candidates": [
            {
                "family": "liquidity_pre_submit_guard_p1",
                "sample_count": 0,
                "source_sample_count": 0,
                "sample_floor": 20,
                "calibration_state": "hold_sample",
                "apply_mode": "report_only_calibration",
                "allowed_runtime_apply": False,
                "supersedes": ["liquidity_gate_refined_candidate"],
                "window_policy": {
                    "primary": "rolling_5d",
                    "secondary": ["daily_intraday"],
                    "daily_only_allowed": False,
                },
            }
        ]
    }
    cumulative = {
        "threshold_snapshot_by_window": {
            "rolling_5d": {
                "liquidity_pre_submit_guard_p1": {
                    "sample": {"blocked_events": 0},
                    "sample_ready": False,
                    "current": {"enabled": False},
                    "recommended": {"enabled": False},
                }
            }
        },
        "calibration_source_bundle_by_window": {
            "rolling_5d": {
                "source_metrics": {
                    "liquidity_gate_refined_candidate": {
                        "evaluated_candidates": 30,
                        "missed_winner_rate": 35.0,
                        "avoided_loser_rate": 15.0,
                    }
                }
            }
        },
    }

    report_mod.apply_window_policy_registry_to_report(report, cumulative)

    candidate = report["calibration_candidates"][0]
    assert candidate["calibration_state"] == "hold"
    assert candidate["sample_count"] == 30
    assert candidate["source_metrics"]["evaluated_candidates"] == 30
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["supersedes"] == ["liquidity_gate_refined_candidate"]
    assert report["window_policy_audit"]["issue_counts"] == {}
    audit_item = report["window_policy_audit"]["items"][0]
    assert audit_item["snapshot_alignment_status"] == "source_denominator_used"
    assert "rendering-only" in audit_item["snapshot_alignment_reason"]


def test_window_policy_audit_keeps_ready_rolling_daily_source_split_as_lineage():
    candidates = [
        {
            "family": "soft_stop_whipsaw_confirmation",
            "source_sample_count": 3,
            "sample_floor": 10,
            "calibration_state": "hold_sample",
            "window_policy_resolution": {
                "primary": "rolling_10d",
                "daily_only_allowed": False,
                "primary_sample_ready": True,
                "primary_snapshot_available": True,
                "primary_source_available": True,
                "primary_sample_count": 7417,
                "primary_snapshot_sample_count": 7417,
                "primary_source_sample_count": 7417,
            },
        }
    ]

    audit = report_mod._build_window_policy_audit(candidates)

    assert audit["status"] == "pass"
    assert audit["issue_counts"] == {}
    assert audit["lineage_warning_counts"] == {"rolling_ready_daily_source_split": 1}
    item = audit["items"][0]
    assert item["source_sample_split_status"] == "documented_daily_source_split"
    assert "lineage evidence" in item["source_sample_split_reason"]


def test_classify_fill_price_defect_limit_missing_not_unpriced():
    from src.engine import daily_threshold_cycle_report as target

    fields = {
        "assumed_fill_price": "10000",
        "limit_fill_price": "0",
        "submitted_order_price": "9990",
    }
    classification = target._classify_sim_fill_price_defect(fields, "scalp_sim_buy_order_assumed_filled")
    assert classification == "limit_fill_price_missing_but_assumed_present"

    canonical = target._canonical_sim_fill_price(fields)
    assert canonical == 10000.0


def test_classify_fill_price_defect_unpriced_no_canonical():
    from src.engine import daily_threshold_cycle_report as target

    fields = {
        "submitted_order_price": "0",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
    }
    classification = target._classify_sim_fill_price_defect(fields, "scalp_sim_buy_order_virtual_pending")
    assert classification == "unpriced_no_canonical"


def test_classify_fill_price_defect_forbidden_zero_price():
    from src.engine import daily_threshold_cycle_report as target

    fields = {
        "submitted_order_price": "0",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    classification = target._classify_sim_fill_price_defect(fields, "scalp_sim_buy_order_virtual_pending")
    assert classification == "forbidden_zero_price_observation"


def test_dynamic_entry_price_counterfactual_join_diagnostics_breaks_down_reasons(monkeypatch, tmp_path):
    from src.engine import daily_threshold_cycle_report as target

    report_dir = tmp_path / "report"
    source_dir = report_dir / "monitor_snapshots"
    source_dir.mkdir(parents=True)
    monkeypatch.setattr(target, "REPORT_DIR", report_dir)
    (source_dir / "missed_entry_counterfactual_2026-05-20.json").write_text(
        json.dumps({"rows": [{"candidate_id": "C1"}]}),
        encoding="utf-8",
    )

    diagnostics = target._dynamic_entry_price_counterfactual_join_diagnostics(
        [
            {"stage": "latency_block", "fields": {"candidate_id": "C1"}},
            {"stage": "order_bundle_submitted", "fields": {"candidate_id": "C1"}},
            {"stage": "latency_block", "fields": {}},
            {"stage": "order_bundle_submitted", "fields": {"candidate_id": "C2"}},
            {"stage": "holding_observation", "fields": {"candidate_id": "C3"}},
        ],
        target_date="2026-05-20",
    )

    assert diagnostics["joined_sample"] == 1
    assert diagnostics["matched_event_count"] == 2
    assert diagnostics["events_without_counterfactual"] == 2
    assert diagnostics["events_without_counterfactual_event_count"] == 2
    assert diagnostics["counterfactual_unmatched_row_count"] == 0
    assert diagnostics["reason_counts"]["missing_attempt_key"] == 1
    assert diagnostics["reason_counts"]["candidate_id_mismatch"] == 1
    assert diagnostics["reason_counts"]["not_join_eligible"] == 1
    assert diagnostics["runtime_effect"] is False


def test_active_seed_matched_string_boolean_separation():
    from src.engine import daily_threshold_cycle_report as target

    events = [
        {"stage": "scalp_sim_entry_armed", "fields": {"active_seed_matched": False, "ldm_hypothesis_matched": True, "lifecycle_bucket_match_status": "no_match"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"active_seed_matched": "false", "ldm_hypothesis_matched": True, "lifecycle_bucket_match_status": "no_match"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"active_seed_matched": "0", "ldm_hypothesis_matched": True, "lifecycle_bucket_match_status": "no_match"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"active_seed_matched": "no", "ldm_hypothesis_matched": True, "lifecycle_bucket_match_status": "no_match"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"ldm_hypothesis_matched": True, "lifecycle_bucket_match_status": "no_match"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"active_seed_matched": True, "lifecycle_bucket_match_status": "matched"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"active_seed_matched": "true", "lifecycle_bucket_match_status": "matched"}},
    ]

    result = target._sim_lifecycle_bucket_match_aggregation(events)

    assert result["active_seed_matched_false_count"] == 4
    assert result["active_seed_matched_none_count"] == 1
    assert result["active_seed_matched_true_count"] == 2
    assert result["hypothesis_matched_but_parent_bucket_no_match_count"] == 5
    assert result["no_match_count"] == 5
    assert result["natural_no_match_count"] == 5
    assert result["matched_count"] == 2
    assert result["matched_entry_child_bridge_count"] == 0
    assert result["panic_scale_in_stage_excluded_count"] == 0
    assert result["contract_missing_count"] == 0
    assert result["active_seed_match_source_alias_used_count"] == 0


def test_panic_scale_in_not_counted_in_lifecycle_match():
    from src.engine import daily_threshold_cycle_report as target

    events = [
        {"stage": "scalp_sim_panic_scale_in_blocked", "fields": {"lifecycle_bucket_match_status": "no_match", "active_seed_matched": True}},
        {"stage": "scalp_sim_panic_scale_in_blocked", "fields": {"lifecycle_bucket_match_status": "no_match", "active_seed_matched": False}},
        {"stage": "scalp_sim_entry_armed", "fields": {"lifecycle_bucket_match_status": "no_match", "active_seed_matched": False}},
    ]

    result = target._sim_lifecycle_bucket_match_aggregation(events)

    assert result["panic_scale_in_stage_excluded_count"] == 2
    assert result["natural_no_match_count"] == 1
    assert result["no_match_count"] == 3
    assert result["hypothesis_matched_but_parent_bucket_no_match_count"] == 0


def test_active_seed_alias_from_priority_field():
    from src.engine import daily_threshold_cycle_report as target

    events = [
        {"stage": "scalp_sim_entry_armed", "fields": {"scalp_sim_active_priority_seed_matched": True, "lifecycle_bucket_match_status": "matched"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"scalp_sim_active_priority_seed_matched": False, "lifecycle_bucket_match_status": "no_match"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"scalp_sim_active_priority_seed_matched": "true", "lifecycle_bucket_match_status": "matched"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"scalp_sim_active_priority_seed_matched": "false", "lifecycle_bucket_match_status": "no_match"}},
        {"stage": "scalp_sim_entry_armed", "fields": {"lifecycle_bucket_match_status": "no_match"}},
    ]

    result = target._sim_lifecycle_bucket_match_aggregation(events)

    assert result["active_seed_matched_true_count"] == 2
    assert result["active_seed_matched_false_count"] == 2
    assert result["active_seed_matched_none_count"] == 1
    assert result["active_seed_match_source_alias_used_count"] == 4
    assert result["matched_count"] == 2
    assert result["natural_no_match_count"] == 3


def test_reclassify_entry_child_bridge_from_bucket_id():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="no_match",
        fields={
            "lifecycle_bucket_match_status": "no_match",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score66-69:stale_low",
            "lifecycle_bucket_source_bucket_id": "parent_bucket_abc123",
            "lifecycle_bucket_entry_bucket_key": "score=66-69|source=buy_signal",
        },
        stage="scalp_sim_entry_armed",
        active_seed_state="false",
    )
    assert result == "matched_entry_child_bridge"


def test_reclassify_prefix_true_not_bridge_without_source():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="no_match",
        fields={
            "lifecycle_bucket_match_status": "no_match",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score66-69:stale_low",
        },
        stage="scalp_sim_entry_armed",
        active_seed_state="true",
    )
    assert result == "active_seed_prefix_matched_parent_missing"


def test_reclassify_false_prefix_alone_natural_no_match():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="no_match",
        fields={
            "lifecycle_bucket_match_status": "no_match",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score66-69:stale_low",
        },
        stage="scalp_sim_entry_armed",
        active_seed_state="false",
    )
    assert result == "natural_no_match"


def test_reclassify_diagnostic_stage_missing_not_instrumented():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="missing",
        fields={},
        stage="scalp_sim_ai_holding_live_call",
        active_seed_state="none",
    )
    assert result == "not_instrumented"


def test_reclassify_lifecycle_stage_missing_contract_missing():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="missing",
        fields={},
        stage="scalp_sim_entry_armed",
        active_seed_state="none",
    )
    assert result == "contract_missing"


def test_hypothesis_count_includes_prefix_matched_parent_missing():
    from src.engine import daily_threshold_cycle_report as target

    events = [
        {"stage": "scalp_sim_entry_armed", "fields": {"lifecycle_bucket_match_status": "no_match", "active_seed_matched": True, "ldm_hypothesis_matched": True}},
        {"stage": "scalp_sim_entry_armed", "fields": {"lifecycle_bucket_match_status": "no_match", "active_seed_matched": False, "ldm_hypothesis_matched": True}},
        {"stage": "scalp_sim_entry_armed", "fields": {"lifecycle_bucket_match_status": "no_match", "active_seed_matched": False}},
    ]

    result = target._sim_lifecycle_bucket_match_aggregation(events)

    assert result["active_seed_prefix_matched_parent_missing_count"] == 1
    assert result["natural_no_match_count"] == 2
    assert result["hypothesis_matched_but_parent_bucket_no_match_count"] == 2


def test_not_instrumented_separated_from_contract_missing():
    from src.engine import daily_threshold_cycle_report as target

    events = [
        {"stage": "scalp_sim_entry_armed", "fields": {}},
        {"stage": "scalp_sim_entry_armed", "fields": {}},
        {"stage": "scalp_sim_ai_holding_live_call", "fields": {}},
        {"stage": "scalp_sim_ai_holding_deferred", "fields": {}},
        {"stage": "scalp_sim_ai_holding_reuse", "fields": {}},
    ]

    result = target._sim_lifecycle_bucket_match_aggregation(events)

    assert result["contract_missing_count"] == 2
    assert result["not_instrumented_count"] == 3


def test_duplicate_buy_signal_is_not_instrumented():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="missing",
        fields={},
        stage="scalp_sim_duplicate_buy_signal",
        active_seed_state="none",
    )
    assert result == "not_instrumented"


def test_lifecycle_entry_armed_remains_contract_missing():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="missing",
        fields={},
        stage="scalp_sim_entry_armed",
        active_seed_state="none",
    )
    assert result == "contract_missing"


def test_sim_only_lifecycle_context_missing_status_backfilled_as_context_only():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="missing",
        fields={
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "decision_authority": "sim_observation_only",
        },
        stage="scalp_sim_overnight_decision",
        active_seed_state="none",
    )
    assert result == "candidate_context_only"


def test_sim_submit_path_lifecycle_context_missing_status_backfilled_as_context_only():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="missing",
        fields={
            "simulation_book": "scalp_ai_buy_all",
            "actual_order_submitted": "False",
            "broker_order_forbidden": "True",
            "decision_authority": "sim_submit_path_observation_only",
        },
        stage="scalp_sim_pre_submit_liquidity_guard_would_pass",
        active_seed_state="none",
    )
    assert result == "candidate_context_only"


def test_duplicate_not_in_lifecycle_eligible_stages():
    from src.engine import daily_threshold_cycle_report as target

    assert not target._is_lifecycle_match_eligible_stage("scalp_sim_duplicate_buy_signal")
    assert target._is_lifecycle_match_eligible_stage("scalp_sim_entry_armed")
    assert target._is_lifecycle_match_eligible_stage("scalp_sim_buy_order_assumed_filled")
    assert target._is_lifecycle_match_eligible_stage("scalp_sim_holding_started")


def test_lifecycle_match_aggregation_separates_raw_missing_from_decision_gap():
    from src.engine import daily_threshold_cycle_report as target

    events = [
        {
            "stage": "scalp_sim_duplicate_buy_signal",
            "fields": {"simulation_book": "scalp_ai_buy_all"},
        },
        {
            "stage": "scalp_sim_entry_armed",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "lifecycle_bucket_match_status": "matched",
                "active_seed_matched": True,
            },
        },
        {
            "stage": "scalp_sim_holding_started",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "active_seed_matched": False,
            },
        },
        {
            "stage": "scalp_sim_pre_submit_liquidity_guard_would_pass",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
                "decision_authority": "sim_submit_path_observation_only",
            },
        },
    ]

    result = target._sim_lifecycle_bucket_match_aggregation(events)

    assert result["missing_count"] == 3
    assert result["raw_missing_count_scope"] == "all_scalp_sim_events_compatibility_counter"
    assert result["eligible_lifecycle_match_event_count"] == 3
    assert result["eligible_lifecycle_match_observed_count"] == 1
    assert result["eligible_lifecycle_match_gap_count"] == 1
    assert result["decision_missing_count"] == 1
    assert result["decision_missing_count_scope"] == "eligible_lifecycle_match_events_only"
    assert result["candidate_context_only_count"] == 1
    assert result["not_instrumented_count"] == 1
    assert result["eligible_active_seed_matched_none_count"] == 1


def test_producer_parent_catalog_missing_reason_flow():
    from src.engine import daily_threshold_cycle_report as target

    events = [
        {"stage": "scalp_sim_entry_armed", "fields": {
            "lifecycle_bucket_match_status": "no_match",
            "lifecycle_bucket_match_reason": "parent_catalog_missing",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score66-69:stale_low",
            "active_seed_matched": True,
        }},
        {"stage": "scalp_sim_entry_armed", "fields": {
            "lifecycle_bucket_match_status": "no_match",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score60-65",
            "active_seed_matched": False,
        }},
        {"stage": "scalp_sim_entry_armed", "fields": {
            "lifecycle_bucket_match_status": "matched",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score60-65",
            "lifecycle_bucket_source_bucket_id": "parent_bucket_abc123",
            "active_seed_matched": True,
        }},
    ]

    result = target._sim_lifecycle_bucket_match_aggregation(events)

    assert result["active_seed_prefix_matched_parent_missing_count"] == 1
    assert result["natural_no_match_count"] == 1
    assert result["matched_count"] == 1
    assert result["matched_entry_child_bridge_count"] == 0


def test_parent_catalog_missing_blocks_bridge():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="no_match",
        fields={
            "lifecycle_bucket_match_status": "no_match",
            "lifecycle_bucket_match_reason": "parent_catalog_missing",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score66-69:stale_low",
            "lifecycle_bucket_source_bucket_id": "parent_bucket_abc123",
        },
        stage="scalp_sim_entry_armed",
        active_seed_state="false",
    )
    assert result != "matched_entry_child_bridge"
    assert result == "natural_no_match"


def test_parent_catalog_missing_none_also_blocks_bridge():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="no_match",
        fields={
            "lifecycle_bucket_match_status": "no_match",
            "lifecycle_bucket_match_reason": "parent_catalog_missing",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score66-69",
            "lifecycle_bucket_source_bucket_id": "parent_bucket_xyz",
        },
        stage="scalp_sim_entry_armed",
        active_seed_state="none",
    )
    assert result != "matched_entry_child_bridge"
    assert result == "natural_no_match"


def test_bridge_still_works_without_parent_catalog_missing():
    from src.engine import daily_threshold_cycle_report as target

    result = target._reclassify_match_status(
        raw_match_status="no_match",
        fields={
            "lifecycle_bucket_match_status": "no_match",
            "lifecycle_bucket_match_reason": "",
            "lifecycle_bucket_bucket_id": "entry:combo_entry_spot:score66-69:stale_low",
            "lifecycle_bucket_source_bucket_id": "parent_bucket_abc123",
        },
        stage="scalp_sim_entry_armed",
        active_seed_state="false",
    )
    assert result == "matched_entry_child_bridge"


def test_enrich_entry_price_sim_metrics_with_post_sell_joins_and_populates_metrics(tmp_path, monkeypatch):
    from src.engine import daily_threshold_cycle_report as mod

    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    eval_path = post_sell_dir / "sim_post_sell_evaluations_2026-06-11.jsonl"

    evaluations = [
        {
            "sim_record_id": "sim-1",
            "sim_parent_record_id": "",
            "profit_rate": 0.85,
            "outcome": "MISSED_UPSIDE",
            "metrics_10m": {"mfe_pct": 1.2, "mae_pct": -0.5, "close_ret_pct": 0.3},
        },
        {
            "sim_record_id": "sim-2",
            "sim_parent_record_id": "",
            "profit_rate": -0.42,
            "outcome": "GOOD_EXIT",
            "metrics_10m": {"mfe_pct": 0.3, "mae_pct": -1.1, "close_ret_pct": -0.5},
        },
        {
            "sim_record_id": "sim-3",
            "sim_parent_record_id": "",
            "profit_rate": 0.10,
            "outcome": "NEUTRAL",
            "metrics_10m": {"mfe_pct": 0.1, "mae_pct": -0.1, "close_ret_pct": 0.0},
        },
    ]
    eval_path.write_text("\n".join(json.dumps(row) for row in evaluations), encoding="utf-8")

    sim_events = [
        {"stage": "scalp_sim_buy_order_virtual_pending", "fields": {"sim_record_id": "sim-1", "submitted_order_price": "10000"}},
        {"stage": "scalp_sim_buy_order_assumed_filled", "fields": {"sim_record_id": "sim-1"}},
        {"stage": "scalp_sim_buy_order_virtual_pending", "fields": {"sim_record_id": "sim-2", "submitted_order_price": "10000"}},
        {"stage": "scalp_sim_buy_order_assumed_filled", "fields": {"sim_record_id": "sim-2"}},
        {"stage": "scalp_sim_buy_order_virtual_pending", "fields": {"sim_record_id": "sim-3", "submitted_order_price": "10000"}},
        {"stage": "scalp_sim_buy_order_virtual_pending", "fields": {"sim_record_id": "sim-noeval", "submitted_order_price": "10000"}},
    ]

    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    sim_metrics = mod._candidate_metric_pack(
        sim_events,
        submitted_stages={"scalp_sim_buy_order_virtual_pending"},
        fill_stages={"scalp_sim_buy_order_assumed_filled"},
        cancel_stages={"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"},
    )

    enriched = mod._enrich_entry_price_sim_metrics_with_post_sell(
        sim_metrics,
        sim_events,
        target_date="2026-06-11",
    )

    assert enriched["post_sell_joined_count"] == 3
    assert enriched["post_sell_join_pending_count"] == 1
    assert enriched["post_sell_join_status"] == "evaluated"
    assert enriched["missed_upside"] == round(1 / 3 * 100, 2)
    assert enriched["missed_upside_source"] == "sim_post_sell_evaluations_10m"
    assert enriched["source_quality_adjusted_ev_pct"] == round((0.85 - 0.42 + 0.10) / 3, 4)
    assert enriched["ev_source"] == "joined_sim_post_sell_profit_rate"
    assert enriched["post_sell_outcome_counts"] == {"MISSED_UPSIDE": 1, "GOOD_EXIT": 1, "NEUTRAL": 1}
    assert enriched["fill_rate"] is not None


def test_enrich_entry_price_sim_metrics_without_post_sell_artifact_keeps_metrics_none(monkeypatch):
    from src.engine import daily_threshold_cycle_report as mod
    import tempfile

    empty_dir = Path(tempfile.mkdtemp()) / "post_sell"
    empty_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "POST_SELL_DIR", empty_dir)

    sim_events = [
        {"stage": "scalp_sim_buy_order_virtual_pending", "fields": {"submitted_order_price": "10000"}},
    ]
    sim_metrics = mod._candidate_metric_pack(
        sim_events,
        submitted_stages={"scalp_sim_buy_order_virtual_pending"},
        fill_stages={"scalp_sim_buy_order_assumed_filled"},
        cancel_stages={"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"},
    )

    enriched = mod._enrich_entry_price_sim_metrics_with_post_sell(
        sim_metrics, sim_events, target_date="2026-06-11",
    )

    assert enriched["post_sell_join_status"] == "missing_or_empty_artifact"
    assert enriched["post_sell_joined_count"] == 0
    assert enriched["post_sell_join_pending_count"] == 1
    assert enriched["missed_upside"] is None
    assert enriched["source_quality_adjusted_ev_pct"] is None


def test_enrich_sim_parent_record_id_fallback_joins(tmp_path, monkeypatch):
    from src.engine import daily_threshold_cycle_report as mod

    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    eval_path = post_sell_dir / "sim_post_sell_evaluations_2026-06-11.jsonl"
    eval_path.write_text(
        json.dumps({"sim_parent_record_id": "parent-1", "post_sell_id": "ps-1", "profit_rate": 0.55, "outcome": "GOOD_EXIT"})
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    sim_events = [
        {"stage": "scalp_sim_buy_order_virtual_pending",
         "fields": {"sim_parent_record_id": "parent-1", "submitted_order_price": "10000"}},
    ]
    sim_metrics = mod._candidate_metric_pack(
        sim_events,
        submitted_stages={"scalp_sim_buy_order_virtual_pending"},
        fill_stages={"scalp_sim_buy_order_assumed_filled"},
        cancel_stages={"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"},
    )
    enriched = mod._enrich_entry_price_sim_metrics_with_post_sell(
        sim_metrics, sim_events, target_date="2026-06-11",
    )
    assert enriched["post_sell_join_status"] == "evaluated"
    assert enriched["post_sell_joined_count"] == 1
    assert enriched["post_sell_join_pending_count"] == 0


def test_enrich_sim_candidate_id_fallback_joins(tmp_path, monkeypatch):
    from src.engine import daily_threshold_cycle_report as mod

    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    eval_path = post_sell_dir / "sim_post_sell_evaluations_2026-06-11.jsonl"
    eval_path.write_text(
        json.dumps({"candidate_id": "cid-99", "post_sell_id": "ps-2", "profit_rate": -0.33, "outcome": "NEUTRAL"})
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    sim_events = [
        {"stage": "scalp_sim_buy_order_virtual_pending",
         "fields": {"candidate_id": "cid-99", "submitted_order_price": "10000"}},
    ]
    sim_metrics = mod._candidate_metric_pack(
        sim_events,
        submitted_stages={"scalp_sim_buy_order_virtual_pending"},
        fill_stages={"scalp_sim_buy_order_assumed_filled"},
        cancel_stages={"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"},
    )
    enriched = mod._enrich_entry_price_sim_metrics_with_post_sell(
        sim_metrics, sim_events, target_date="2026-06-11",
    )
    assert enriched["post_sell_join_status"] == "evaluated"
    assert enriched["post_sell_joined_count"] == 1
    assert enriched["post_sell_join_pending_count"] == 0


def test_enrich_sim_parent_priority_over_candidate_when_both_exist(tmp_path, monkeypatch):
    from src.engine import daily_threshold_cycle_report as mod

    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    eval_path = post_sell_dir / "sim_post_sell_evaluations_2026-06-11.jsonl"
    eval_path.write_text(
        "\n".join([
            json.dumps({"sim_parent_record_id": "parent-x", "post_sell_id": "ps-parent", "profit_rate": 0.60, "outcome": "GOOD_EXIT"}),
            json.dumps({"candidate_id": "cid-x", "post_sell_id": "ps-cid", "profit_rate": 0.30, "outcome": "GOOD_EXIT"}),
        ]),
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    sim_events = [
        {"stage": "scalp_sim_buy_order_virtual_pending",
         "fields": {"sim_parent_record_id": "parent-x", "candidate_id": "cid-x", "submitted_order_price": "10000"}},
    ]
    sim_metrics = mod._candidate_metric_pack(
        sim_events,
        submitted_stages={"scalp_sim_buy_order_virtual_pending"},
        fill_stages={"scalp_sim_buy_order_assumed_filled"},
        cancel_stages={"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"},
    )
    enriched = mod._enrich_entry_price_sim_metrics_with_post_sell(
        sim_metrics, sim_events, target_date="2026-06-11",
    )
    assert enriched["post_sell_joined_count"] == 1
    assert enriched["post_sell_join_pending_count"] == 0
    assert enriched["source_quality_adjusted_ev_pct"] == 0.60


def test_enrich_sim_separate_events_same_eval_via_different_keys_pending_zero(tmp_path, monkeypatch):
    from src.engine import daily_threshold_cycle_report as mod

    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    eval_path = post_sell_dir / "sim_post_sell_evaluations_2026-06-11.jsonl"
    eval_path.write_text(
        json.dumps({"sim_record_id": "sim-x", "candidate_id": "cid-x", "post_sell_id": "ps-x", "profit_rate": 0.77, "outcome": "MISSED_UPSIDE"})
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    sim_events = [
        {"stage": "scalp_sim_buy_order_virtual_pending",
         "fields": {"sim_record_id": "sim-x", "submitted_order_price": "10000"}},
        {"stage": "scalp_sim_buy_order_assumed_filled",
         "fields": {"candidate_id": "cid-x"}},
    ]
    sim_metrics = mod._candidate_metric_pack(
        sim_events,
        submitted_stages={"scalp_sim_buy_order_virtual_pending"},
        fill_stages={"scalp_sim_buy_order_assumed_filled"},
        cancel_stages={"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"},
    )
    enriched = mod._enrich_entry_price_sim_metrics_with_post_sell(
        sim_metrics, sim_events, target_date="2026-06-11",
    )
    assert enriched["post_sell_joined_count"] == 1
    assert enriched["post_sell_join_pending_count"] == 0
    assert enriched["missed_upside"] == 100.0


def test_enrich_sim_same_eval_via_both_record_id_and_candidate_id_not_duplicated(tmp_path, monkeypatch):
    from src.engine import daily_threshold_cycle_report as mod

    post_sell_dir = tmp_path / "post_sell"
    post_sell_dir.mkdir()
    eval_path = post_sell_dir / "sim_post_sell_evaluations_2026-06-11.jsonl"
    eval_path.write_text(
        json.dumps({"sim_record_id": "sim-x", "candidate_id": "cid-x", "post_sell_id": "ps-x", "profit_rate": 0.77, "outcome": "MISSED_UPSIDE"})
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    sim_events = [
        {"stage": "scalp_sim_buy_order_virtual_pending",
         "fields": {"sim_record_id": "sim-x", "candidate_id": "cid-x", "submitted_order_price": "10000"}},
    ]
    sim_metrics = mod._candidate_metric_pack(
        sim_events,
        submitted_stages={"scalp_sim_buy_order_virtual_pending"},
        fill_stages={"scalp_sim_buy_order_assumed_filled"},
        cancel_stages={"scalp_sim_entry_expired", "scalp_sim_entry_unpriced"},
    )
    enriched = mod._enrich_entry_price_sim_metrics_with_post_sell(
        sim_metrics, sim_events, target_date="2026-06-11",
    )
    assert enriched["post_sell_joined_count"] == 1
    assert enriched["post_sell_join_pending_count"] == 0
    assert enriched["missed_upside"] == 100.0
