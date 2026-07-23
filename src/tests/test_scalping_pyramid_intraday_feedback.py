import json
from types import SimpleNamespace

from src.engine.monitoring import scalping_pyramid_intraday_feedback as mod


def _event(
    record_id,
    code,
    name,
    stage,
    fields=None,
    emitted_at="2026-07-03T09:00:00",
    pipeline="HOLDING_PIPELINE",
):
    return {
        "pipeline": pipeline,
        "record_id": record_id,
        "stock_code": code,
        "stock_name": name,
        "stage": stage,
        "fields": fields or {},
        "emitted_at": emitted_at,
    }


def test_pyramid_intraday_feedback_labels_future_recovery_candidate(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            101,
            "095500",
            "future",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "tick_accel_below_min",
                "profit_rate": "+1.80",
                "peak_profit": "+1.80",
                "current_ai_score": 75,
                "buy_pressure_10t": 71,
                "tick_aggressor_trusted_count": 3,
                "tick_aggressor_pressure_usable": True,
                "tick_acceleration_ratio": 0.31,
                "curr_vs_micro_vwap_bp": 66,
                "micro_vwap_available": True,
                "minute_candle_window_fresh": True,
                "min_ai_score": 70,
                "min_tick_accel": 0.5,
                "max_micro_vwap_bps": 60,
            },
        ),
        _event(
            101,
            "095500",
            "future",
            "stat_action_decision_snapshot",
            {"profit_rate": "+2.80"},
        ),
        _event(101, "095500", "future", "sell_completed", {"profit_rate": "+2.35"}),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["pyramid_feedback_rows"][0]

    assert item["pyramid_feedback_label"] == "pyramid_would_have_helped"
    assert item["actual_order_submitted"] is False
    assert item["broker_order_forbidden"] is True
    assert item["runtime_effect"] is False
    assert (
        item["decision_authority"]
        == "source_only_pyramid_intraday_feedback_no_runtime_mutation"
    )
    assert "intraday_threshold_mutation" in item["forbidden_uses"]
    assert item["tick_aggressor_trusted_count"] == 3
    assert item["tick_aggressor_pressure_usable"] is True
    assert report["blocker_metrics"][0]["recovered_or_extended_rate"] == 1.0


def test_pyramid_intraday_feedback_keeps_ai50_as_risk_or_neutral(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            202,
            "111111",
            "weak",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "ai_score_below_min",
                "profit_rate": "+1.60",
                "current_ai_score": 50,
                "tick_acceleration_ratio": 0.52,
                "curr_vs_micro_vwap_bp": 20,
                "micro_vwap_available": True,
                "minute_candle_window_fresh": True,
            },
        ),
        _event(202, "111111", "weak", "sell_completed", {"profit_rate": "-0.20"}),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["pyramid_feedback_rows"][0]

    assert item["current_ai_score"] == 50
    assert item["pyramid_feedback_label"] == "pyramid_overheat_or_reversal_risk"
    assert item["pyramid_feedback_label"] != "pyramid_would_have_helped"


def test_pyramid_intraday_feedback_blocks_source_quality_when_pressure_provenance_missing(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            205,
            "111222",
            "missing-pressure-source",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "buy_pressure_below_min",
                "profit_rate": "+1.60",
                "current_ai_score": 72,
                "buy_pressure_10t": 81,
                "tick_acceleration_ratio": 0.52,
                "curr_vs_micro_vwap_bp": 20,
                "micro_vwap_available": True,
                "minute_candle_window_fresh": True,
            },
        ),
        _event(
            205,
            "111222",
            "missing-pressure-source",
            "sell_completed",
            {"profit_rate": "+2.40"},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["source_quality"]["status"] == "pressure_provenance_missing"
    assert report["source_quality"]["pressure_provenance_missing_count"] == 1


def test_pyramid_intraday_feedback_blocks_source_quality_when_pressure_provenance_unusable(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            206,
            "111333",
            "unusable-pressure-source",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "buy_pressure_below_min",
                "profit_rate": "+1.60",
                "current_ai_score": 72,
                "buy_pressure_10t": 81,
                "tick_aggressor_trusted_count": 0,
                "tick_aggressor_pressure_usable": False,
                "tick_acceleration_ratio": 0.52,
                "curr_vs_micro_vwap_bp": 20,
                "micro_vwap_available": True,
                "minute_candle_window_fresh": True,
            },
        ),
        _event(
            206,
            "111333",
            "unusable-pressure-source",
            "sell_completed",
            {"profit_rate": "+2.40"},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["source_quality"]["status"] == "pressure_provenance_unusable"
    assert report["source_quality"]["pressure_provenance_unusable_count"] == 1


def test_pyramid_intraday_feedback_blocks_source_quality_when_micro_vwap_provenance_missing(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            207,
            "111444",
            "missing-micro-source",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "micro_vwap_overheated",
                "profit_rate": "+1.60",
                "current_ai_score": 72,
                "tick_acceleration_ratio": 0.52,
                "curr_vs_micro_vwap_bp": 70,
            },
        ),
        _event(
            207,
            "111444",
            "missing-micro-source",
            "sell_completed",
            {"profit_rate": "+2.40"},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["source_quality"]["status"] == "micro_vwap_provenance_missing"
    assert report["source_quality"]["micro_vwap_provenance_missing_count"] == 1


def test_pyramid_intraday_feedback_blocks_source_quality_when_micro_vwap_provenance_unusable(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            208,
            "111555",
            "stale-micro-source",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "micro_vwap_overheated",
                "profit_rate": "+1.60",
                "current_ai_score": 72,
                "tick_acceleration_ratio": 0.52,
                "curr_vs_micro_vwap_bp": 70,
                "micro_vwap_available": True,
                "minute_candle_window_fresh": False,
            },
        ),
        _event(
            208,
            "111555",
            "stale-micro-source",
            "sell_completed",
            {"profit_rate": "+2.40"},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert report["source_quality"]["status"] == "micro_vwap_provenance_unusable"
    assert report["source_quality"]["micro_vwap_provenance_unusable_count"] == 1


def test_pyramid_intraday_feedback_counts_submitted_then_profit_rows(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            303,
            "222222",
            "submitted",
            "scale_in_order_submitted",
            {"add_type": "PYRAMID", "profit_rate": "+1.70", "current_ai_score": 76},
        ),
        _event(303, "222222", "submitted", "sell_completed", {"profit_rate": "+2.10"}),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["pyramid_feedback_rows"][0]

    assert item["actual_order_submitted"] is True
    assert item["broker_order_forbidden"] is False
    assert item["scale_in_blocker_reason"] == "pyramid_submitted"
    assert report["blocker_metrics"][0]["submitted_then_profit_rate"] == 1.0


def test_normal_winner_expansion_tracks_post_candidate_incremental_ev_and_probe_confirmation(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-23.jsonl"
    rows = [
        _event(
            350,
            "350350",
            "normal-winner",
            "rising_missed_one_share_entry",
            {
                "actual_order_submitted": True,
                "forced_entry_qty": 10,
                "rising_missed_effective_venue": "KRX",
                "rising_missed_market_session_bucket": "krx_regular",
            },
            emitted_at="2026-07-23T10:00:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            350,
            "350350",
            "normal-winner",
            "probe_filled",
            {
                "probe_bundle_id": "350350-probe",
                "fill_qty": 1,
                "fill_price": 10000,
            },
            emitted_at="2026-07-23T10:00:01",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            350,
            "350350",
            "normal-winner",
            "probe_continuation_deferred",
            {
                "post_probe_direction_state": "STRONG",
                "post_probe_continuation_action": "DEFER",
                "post_probe_direction_reason": (
                    "post_probe_second_strong_confirmation_required"
                ),
                "post_probe_direction_positive_groups": "price_tick,orderbook",
                "post_probe_direction_negative_groups": "-",
                "probe_confirmation_count": 1,
            },
            emitted_at="2026-07-23T10:00:02.000000",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            350,
            "350350",
            "normal-winner",
            "residual_planned",
            {
                "post_probe_direction_state": "STRONG",
                "post_probe_continuation_action": "ALLOW_NARROW",
                "post_probe_direction_reason": "post_probe_wait_two_group_positive",
                "post_probe_direction_positive_groups": "price_tick,orderbook",
                "post_probe_direction_negative_groups": "-",
                "probe_confirmation_count": 2,
            },
            emitted_at="2026-07-23T10:00:02.300000",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            350,
            "350350",
            "normal-winner",
            "residual_blocked",
            {
                "probe_bundle_id": "350350-probe",
                "reason": "residual_revalidation_timeout",
                "forced_entry_qty": 10,
                "actual_order_submitted": False,
            },
            emitted_at="2026-07-23T10:00:04",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            350,
            "350350",
            "normal-winner",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "profit_not_enough",
                "profit_rate": 0.5,
                "peak_profit": 0.5,
                "current_ai_score": 72,
                "buy_pressure_10t": 70,
                "tick_aggressor_trusted_count": 5,
                "tick_aggressor_pressure_usable": True,
                "tick_acceleration_ratio": 1.2,
                "curr_vs_micro_vwap_bp": 20,
                "micro_vwap_available": True,
                "minute_candle_window_fresh": True,
                "min_profit_pct": 1.1,
            },
            emitted_at="2026-07-23T10:01:00",
        ),
        _event(
            350,
            "350350",
            "normal-winner",
            "stat_action_decision_snapshot",
            {"profit_rate": 1.2, "peak_profit": 1.2},
            emitted_at="2026-07-23T10:02:00",
        ),
        _event(
            350,
            "350350",
            "normal-winner",
            "sell_completed",
            {"profit_rate": 1.0},
            emitted_at="2026-07-23T10:03:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-23", pipeline_path=pipeline_path, generated_at="fixed"
    )
    summary = report["summary"]["normal_winner_expansion"]
    item = report["normal_winner_expansion_rows"][0]

    assert report["schema_version"] == 3
    assert summary["candidate_count"] == 1
    assert summary["source_quality_valid_candidate_count"] == 1
    assert summary["realized_incremental_winner_count"] == 1
    assert summary["equal_weight_avg_profit_pct"] > 0
    assert summary["notional_weighted_ev_pct"] > 0
    assert item["normal_winner_expansion_label"] == "realized_incremental_winner"
    assert item["normal_winner_expansion_incremental_mfe_pct"] > 0.4
    assert item["normal_winner_expansion_incremental_final_profit_pct"] > 0.2
    assert item["normal_winner_expansion_assumed_trade_cost_pct"] == 0.23
    assert item["normal_winner_expansion_candidate_notional_krw"] > 0
    assert item["effective_venue"] == "KRX"
    assert item["market_session_bucket"] == "krx_regular"
    assert item["venue_source_quality_valid"] is True
    assert item["actual_order_submitted"] is False
    assert item["broker_order_forbidden"] is True
    assert item["runtime_effect"] is False
    assert item["allowed_runtime_apply"] is False
    assert summary["by_effective_venue"][0]["effective_venue"] == "KRX"
    assert item["probe_direction_max_consecutive_strong_count"] == 2
    assert item["probe_confirmation_max_count"] == 2
    assert item["probe_direction_negative_seen"] is False
    assert (
        item["normal_winner_expansion_probe_confirmation_signature"]
        == "two_consecutive_strong_no_negative"
    )
    contract = report["normal_winner_expansion_metric_contract"]
    assert contract["primary_decision_metric"] == "notional_weighted_ev_pct"
    assert (
        contract["decision_authority"]
        == "source_only_normal_winner_expansion_attribution_no_runtime_mutation"
    )


def test_normal_winner_expansion_venue_provenance_keeps_premarket_cohort_separate():
    item = {}
    premarket = _event(
        351,
        "351351",
        "premarket",
        "rising_missed_one_share_entry",
        {
            "rising_missed_effective_venue": "PREMARKET_KRX_LIKE",
            "rising_missed_market_session_bucket": "krx_like_premarket",
        },
    )
    mod._update_venue_provenance(item, premarket)

    assert item["effective_venue"] == "PREMARKET_KRX_LIKE"
    assert item["market_session_bucket"] == "krx_like_premarket"
    assert item["venue_source_quality_valid"] is True

    conflicting_nxt = _event(
        351,
        "351351",
        "premarket",
        "probe_filled",
        {"effective_venue": "NXT"},
    )
    mod._update_venue_provenance(item, conflicting_nxt)

    assert item["effective_venue"] == "UNKNOWN"
    assert item["venue_source_quality_valid"] is False
    assert item["effective_venue_resolution"] == "conflicting_explicit_effective_venue"


def test_pyramid_intraday_feedback_backtests_all_one_share_events(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            401,
            "095500",
            "future",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "actual_order_submitted": True,
                "forced_entry_qty": 5,
            },
        ),
        _event(
            401,
            "095500",
            "future",
            "stat_action_decision_snapshot",
            {"profit_rate": "+1.60"},
        ),
        _event(
            401,
            "095500",
            "future",
            "stat_action_decision_snapshot",
            {"profit_rate": "+2.30"},
        ),
        _event(401, "095500", "future", "sell_completed", {"profit_rate": "+1.90"}),
        _event(
            402,
            "222222",
            "flat",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "actual_order_submitted": True,
                "forced_entry_qty": 1,
            },
        ),
        _event(
            402,
            "222222",
            "flat",
            "stat_action_decision_snapshot",
            {"profit_rate": "+0.40"},
        ),
        _event(402, "222222", "flat", "sell_completed", {"profit_rate": "-0.10"}),
        _event(
            403,
            "333333",
            "runner",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "actual_order_submitted": True,
                "forced_entry_qty": 1,
            },
        ),
        _event(
            403,
            "333333",
            "runner",
            "stat_action_decision_snapshot",
            {"profit_rate": "+1.70"},
        ),
        _event(
            403,
            "333333",
            "runner",
            "stat_action_decision_snapshot",
            {"profit_rate": "+3.10"},
        ),
        _event(403, "333333", "runner", "sell_completed", {"profit_rate": "+2.80"}),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    one_share_rows = report["one_share_pyramid_opportunity_rows"]
    by_code = {item["stock_code"]: item for item in one_share_rows}

    assert report["summary"]["one_share_event_count"] == 3
    assert report["summary"]["one_share_closed_count"] == 3
    assert report["summary"]["one_share_pyramid_opportunity_count"] == 2
    assert report["summary"]["one_share_pyramid_missed_upside_count"] == 2
    assert set(by_code) == {"095500", "222222", "333333"}
    assert by_code["095500"]["forced_entry_qty"] == 5
    assert by_code["095500"]["pyramid_feedback_label"] == "pyramid_would_have_helped"
    assert by_code["222222"]["pyramid_feedback_label"] == "pyramid_correctly_blocked"
    assert by_code["333333"]["pyramid_opportunity_cost_pct"] == 1.4
    assert by_code["333333"]["decision_authority"] == (
        "source_only_one_share_pyramid_opportunity_backtest_no_runtime_mutation"
    )
    assert (
        "intraday_threshold_mutation"
        in report["one_share_metric_contract"]["forbidden_uses"]
    )


def test_pyramid_intraday_feedback_uses_runtime_min_profit_for_one_share_opportunity(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        mod,
        "TRADING_RULES",
        SimpleNamespace(SCALPING_PYRAMID_MIN_PROFIT_PCT=1.2),
    )
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            501,
            "444444",
            "lower",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "actual_order_submitted": True,
                "forced_entry_qty": 1,
            },
        ),
        _event(
            501,
            "444444",
            "lower",
            "stat_action_decision_snapshot",
            {"profit_rate": "+1.30"},
        ),
        _event(501, "444444", "lower", "sell_completed", {"profit_rate": "+1.80"}),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["pyramid_opportunity_seen"] is True
    assert item["pyramid_opportunity_min_profit_pct"] == 1.2
    assert item["pyramid_opportunity_profit_rate"] == 1.3


def test_one_share_peak_crossing_is_not_labeled_as_correctly_blocked(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            601,
            "555555",
            "peak-only",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "actual_order_submitted": True,
                "forced_entry_qty": 5,
            },
        ),
        _event(
            601,
            "555555",
            "peak-only",
            "stat_action_decision_snapshot",
            {"profit_rate": "+0.40", "peak_profit": "+1.40"},
        ),
        _event(
            601,
            "555555",
            "peak-only",
            "sell_completed",
            {"profit_rate": "0.00", "peak_profit": "+1.40"},
        ),
        _event(
            699,
            "555599",
            "runtime-threshold-source",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "profit_not_enough",
                "profit_rate": "+0.50",
                "peak_profit": "+0.50",
                "min_profit_pct": "+1.10",
            },
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["max_profit_seen"] == 1.4
    assert item["pyramid_opportunity_seen"] is True
    assert item["pyramid_opportunity_min_profit_pct"] == 1.1
    assert item["pyramid_opportunity_threshold_source"] == (
        "same_day_unique_runtime_pyramid_evaluation"
    )
    assert item["pyramid_opportunity_source"] == (
        "holding_peak_runtime_threshold_crossed_postscan"
    )
    assert item["pyramid_feedback_label"] != "pyramid_correctly_blocked"


def test_pyramid_blocked_event_below_min_does_not_invent_opportunity(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            602,
            "555556",
            "below-min",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "actual_order_submitted": True,
                "forced_entry_qty": 5,
            },
        ),
        _event(
            602,
            "555556",
            "below-min",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "tick_accel_below_min",
                "profit_rate": "+0.40",
                "peak_profit": "+0.50",
            },
        ),
        _event(
            602,
            "555556",
            "below-min",
            "sell_completed",
            {"profit_rate": "+0.30", "peak_profit": "+0.50"},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item.get("pyramid_opportunity_seen") is not True
    assert report["summary"]["one_share_pyramid_opportunity_count"] == 0


def test_probe_residual_soft_abort_and_pyramid_recheck_provenance(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            603,
            "555557",
            "soft-abort",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "actual_order_submitted": False,
                "forced_entry_qty": 5,
            },
        ),
        _event(
            603,
            "555557",
            "soft-abort",
            "probe_filled",
            {"probe_bundle_id": "bundle-603", "fill_qty": 1, "fill_price": 10000},
        ),
        _event(
            603,
            "555557",
            "soft-abort",
            "residual_blocked",
            {
                "probe_bundle_id": "bundle-603",
                "reason": "residual_revalidation_timeout",
                "entry_split_probe_scale_in_recheck_allowed": True,
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            603,
            "555557",
            "soft-abort",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "tick_accel_below_min",
                "profit_rate": "+1.20",
                "peak_profit": "+1.70",
            },
        ),
        _event(
            603,
            "555557",
            "soft-abort",
            "sell_completed",
            {"profit_rate": "+1.20", "peak_profit": "+1.70"},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["residual_expected_qty"] == 4
    assert item["forced_entry_qty"] == 5
    assert item["one_share_actual_stage"] == "probe_filled"
    assert item["residual_filled_qty"] == 0
    assert item["residual_zero_fill"] is True
    assert item["residual_soft_abort"] is True
    assert item["residual_scale_in_recheck_allowed"] is True
    assert item["pyramid_evaluation_seen"] is True
    assert item["residual_missed_upside_candidate"] is True
    assert report["summary"]["probe_residual_zero_fill_count"] == 1
    assert report["summary"]["probe_residual_soft_abort_count"] == 1
    assert report["summary"]["probe_residual_missed_upside_candidate_count"] == 1
    assert report["summary"]["probe_residual_pyramid_evaluation_seen_count"] == 1


def test_partial_submitted_direction_defer_is_not_soft_abort():
    item = {}
    row = _event(
        604,
        "555558",
        "partial-submitted",
        "residual_blocked",
        {
            "reason": "residual_leg_direction_deferred",
            "actual_order_submitted": True,
            "residual_submitted_qty": 3,
            "residual_submitted_leg_count": 1,
        },
        pipeline="ENTRY_PIPELINE",
    )

    mod._update_probe_residual_observation(item, row)

    assert item["residual_soft_abort"] is False
    assert item["residual_hard_or_capacity_abort"] is True
    assert item["residual_partial_submitted_before_block"] is True
    assert item["residual_scale_in_recheck_allowed"] is False


def test_probe_residual_fill_uses_exact_bundle_terminal_not_later_buy_qty(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            605,
            "117730",
            "exact-bundle",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "forced_entry_qty": 80,
                "actual_order_submitted": False,
            },
        ),
        _event(
            605,
            "117730",
            "exact-bundle",
            "probe_filled",
            {
                "probe_bundle_id": "bundle-605",
                "fill_qty": 1,
                "fill_price": 14100,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
        ),
        _event(
            605,
            "117730",
            "exact-bundle",
            "residual_submitted",
            {
                "probe_bundle_id": "bundle-605",
                "order_no": "R605",
                "qty": 79,
                "price": 14050,
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            605,
            "117730",
            "exact-bundle",
            "holding_snapshot_after_later_scale_in",
            {"buy_qty": 153, "entry_filled_qty": 153, "profit_rate": "+0.30"},
        ),
        _event(
            605,
            "117730",
            "exact-bundle",
            "bundle_completed",
            {
                "probe_bundle_id": "bundle-605",
                "requested_qty": 80,
                "filled_qty": 80,
            },
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["residual_submitted_qty"] == 79
    assert item["residual_filled_qty"] == 79
    assert item["residual_unfilled_qty"] == 0
    assert item["residual_fill_attribution_valid"] is True
    assert item["residual_fill_attribution_state"] == "full_fill"
    assert item["effective_venue"] == "KRX"
    assert item["market_session_bucket"] == "krx_regular"


def test_probe_residual_without_terminal_receipt_is_open_unresolved(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            606,
            "117731",
            "open-bundle",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "forced_entry_qty": 5,
                "actual_order_submitted": False,
            },
        ),
        _event(
            606,
            "117731",
            "open-bundle",
            "probe_filled",
            {
                "probe_bundle_id": "bundle-606",
                "fill_qty": 1,
                "fill_price": 10000,
            },
        ),
        _event(
            606,
            "117731",
            "open-bundle",
            "residual_submitted",
            {
                "probe_bundle_id": "bundle-606",
                "order_no": "R606",
                "qty": 4,
                "price": 9990,
            },
            pipeline="ENTRY_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["residual_fill_attribution_valid"] is None
    assert item["residual_fill_attribution_state"] == "open_unresolved"
    assert item["residual_filled_qty"] is None
    assert item["residual_unfilled_qty"] is None
    assert item["residual_zero_fill"] is None


def test_invalid_probe_fill_attribution_is_excluded_from_expansion_ev(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            607,
            "117732",
            "invalid-bundle",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "forced_entry_qty": 80,
                "actual_order_submitted": False,
            },
        ),
        _event(
            607,
            "117732",
            "invalid-bundle",
            "probe_filled",
            {
                "probe_bundle_id": "bundle-607",
                "fill_qty": 1,
                "fill_price": 10000,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
        ),
        _event(
            607,
            "117732",
            "invalid-bundle",
            "residual_submitted",
            {
                "probe_bundle_id": "bundle-607",
                "order_no": "R607",
                "qty": 79,
                "price": 9990,
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            607,
            "117732",
            "invalid-bundle",
            "bundle_completed",
            {
                "probe_bundle_id": "bundle-607",
                "requested_qty": 80,
                "filled_qty": 153,
            },
        ),
        _event(
            607,
            "117732",
            "invalid-bundle",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "profit_not_enough",
                "profit_rate": "+1.20",
                "current_ai_score": 70,
                "buy_pressure_10t": 80,
                "tick_aggressor_trusted_count": 10,
                "tick_aggressor_pressure_usable": True,
                "tick_acceleration_ratio": 1.2,
                "curr_vs_micro_vwap_bp": 10,
                "micro_vwap_available": True,
                "minute_candle_window_fresh": True,
            },
        ),
        _event(
            607,
            "117732",
            "invalid-bundle",
            "sell_completed",
            {"profit_rate": "+1.50"},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["residual_fill_attribution_valid"] is False
    assert item["residual_fill_attribution_state"] == (
        "filled_qty_exceeds_submitted_or_expected"
    )
    assert item["normal_winner_expansion_label"] == "source_quality_blocked"
    assert report["source_quality"]["residual_fill_attribution_invalid_count"] == 1
    assert report["source_quality"]["status"] == "pass"
    assert report["summary"]["probe_residual_fill_attribution_invalid_count"] == 1
    assert (
        report["summary"]["normal_winner_expansion"][
            "source_quality_blocked_candidate_count"
        ]
        == 1
    )
    assert report["summary"]["normal_winner_expansion"]["closed_candidate_count"] == 0
