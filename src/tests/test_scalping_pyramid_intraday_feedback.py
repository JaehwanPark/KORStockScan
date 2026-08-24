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

    assert report["schema_version"] == 4
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
    assert item["residual_missed_upside_candidate"] is False
    assert item["residual_pyramid_threshold_missed_upside_candidate"] is True
    assert report["summary"]["probe_residual_zero_fill_count"] == 1
    assert report["summary"]["probe_residual_soft_abort_count"] == 1
    assert report["summary"]["probe_residual_missed_upside_candidate_count"] == 0
    assert (
        report["summary"][
            "probe_residual_pyramid_threshold_missed_upside_candidate_count"
        ]
        == 1
    )
    assert report["summary"]["probe_residual_pyramid_evaluation_seen_count"] == 1


def test_post_probe_real_outcome_separates_profitable_and_loss_zero_fill_rows(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-29.jsonl"
    rows = []
    outcomes = [
        (701, "270660", "loss-a", 7, 12770, -3.67),
        (702, "475040", "loss-b", 43, 2990, -0.23),
        (703, "073240", "winner", 21, 6040, 0.27),
    ]
    for record_id, code, name, requested_qty, fill_price, final_profit in outcomes:
        rows.extend(
            [
                _event(
                    record_id,
                    code,
                    name,
                    "entry_split_order_plan_applied",
                    {
                        "rising_missed_one_share_scout": True,
                        "entry_split_order_probe_first_applied": True,
                        "effective_qty": requested_qty,
                        "forced_entry_qty": requested_qty,
                        "entry_split_order_probe_qty": 1,
                        "entry_split_order_leg_count": 4,
                        "entry_split_order_qty_weight_min": 0.4,
                        "entry_split_order_policy_version": "fixture-v1",
                        "entry_split_order_variant_id": "fixture-40-30-30",
                        "effective_venue": "NXT",
                        "market_session_bucket": "nxt",
                    },
                    emitted_at=f"2026-07-29T16:35:{record_id - 660}.000000+09:00",
                    pipeline="ENTRY_PIPELINE",
                ),
                _event(
                    record_id,
                    code,
                    name,
                    "probe_filled",
                    {
                        "probe_bundle_id": f"bundle-{record_id}",
                        "fill_qty": 1,
                        "fill_price": fill_price,
                        "effective_venue": "NXT",
                        "market_session_bucket": "nxt",
                    },
                    emitted_at=f"2026-07-29T16:35:{record_id - 660}.100000+09:00",
                    pipeline="ENTRY_PIPELINE",
                ),
            ]
        )
        if final_profit > 0:
            for suffix, signature in (("200000", "source-a"), ("500000", "source-b")):
                rows.append(
                    _event(
                        record_id,
                        code,
                        name,
                        "probe_continuation_deferred",
                        {
                            "probe_bundle_id": f"bundle-{record_id}",
                            "post_probe_direction_state": "UNKNOWN",
                            "post_probe_continuation_action": "DEFER",
                            "post_probe_direction_reason": (
                                "post_probe_nxt_wait_fast_tape_required"
                            ),
                            "post_probe_direction_positive_groups": (
                                "orderbook,signed_pressure"
                            ),
                            "post_probe_direction_negative_groups": "-",
                            "post_probe_direction_mark_price": fill_price,
                            "post_probe_direction_probe_fill_price": fill_price,
                            "post_probe_direction_ai_action": "WAIT",
                            "post_probe_hard_veto": False,
                            "post_probe_confirmation_evidence_version_proven": True,
                            "post_probe_confirmation_source_version_signature": (
                                signature
                            ),
                            "post_probe_direction_tick_context_fresh": True,
                        },
                        emitted_at=(
                            f"2026-07-29T16:35:{record_id - 660}.{suffix}+09:00"
                        ),
                        pipeline="ENTRY_PIPELINE",
                    )
                )
        rows.extend(
            [
                _event(
                    record_id,
                    code,
                    name,
                    "residual_blocked",
                    {
                        "probe_bundle_id": f"bundle-{record_id}",
                        "reason": "residual_revalidation_timeout",
                        "entry_split_probe_scale_in_recheck_allowed": False,
                    },
                    emitted_at=f"2026-07-29T16:35:{record_id - 660}.900000+09:00",
                    pipeline="ENTRY_PIPELINE",
                ),
                _event(
                    record_id,
                    code,
                    name,
                    "sell_completed",
                    {
                        "profit_rate": final_profit,
                        "peak_profit": 0.76 if final_profit > 0 else final_profit,
                    },
                    emitted_at=f"2026-07-29T16:37:{record_id - 660}.000000+09:00",
                ),
            ]
        )
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-29", pipeline_path=pipeline_path, generated_at="fixed"
    )
    by_code = {
        item["stock_code"]: item
        for item in report["one_share_pyramid_opportunity_rows"]
    }
    winner = by_code["073240"]

    assert report["schema_version"] == 4
    assert (
        winner["post_probe_real_outcome_label"]
        == "profitable_zero_fill_confirmation_ready"
    )
    assert winner["post_probe_real_confirmation_max_count"] == 2
    assert winner["post_probe_real_confirmation_ready"] is True
    assert winner["post_probe_counterfactual_first_leg_qty"] == 8
    assert winner["post_probe_counterfactual_first_leg_notional_krw"] == 48_320
    assert winner["post_probe_counterfactual_first_leg_profit_proxy_krw"] == 130.46
    assert winner["residual_missed_upside_candidate"] is True
    assert (
        winner["canonical_expansion_outcome_label"]
        == "expansion_missed_upside_confirmation_ready"
    )
    assert winner["post_probe_legacy_label_conflict"] is True
    assert winner["residual_pyramid_threshold_missed_upside_candidate"] is False
    assert (
        by_code["270660"]["post_probe_real_outcome_label"]
        == "loss_or_flat_zero_fill_no_confirmation"
    )
    assert (
        by_code["475040"]["post_probe_real_outcome_label"]
        == "loss_or_flat_zero_fill_no_confirmation"
    )

    summary = report["summary"]
    assert summary["probe_residual_real_outcome_closed_count"] == 3
    assert summary["probe_residual_realized_winner_zero_fill_count"] == 1
    assert summary["probe_residual_realized_loss_or_flat_zero_fill_count"] == 2
    assert summary["probe_residual_realized_winner_confirmation_ready_count"] == 1
    assert summary["probe_residual_realized_loss_or_flat_confirmation_ready_count"] == 0
    assert summary["probe_residual_missed_upside_candidate_count"] == 1
    assert summary["canonical_expansion_missed_upside_count"] == 1
    assert summary["post_probe_legacy_label_conflict_count"] == 1
    assert summary["post_probe_confirmation_false_positive_loss_or_flat_count"] == 0
    assert (
        summary["probe_residual_pyramid_threshold_missed_upside_candidate_count"] == 0
    )
    assert summary["probe_residual_confirmation_ready_notional_weighted_ev_pct"] == 0.27
    assert (
        summary["probe_residual_confirmation_ready_simple_sum_profit_proxy_krw"]
        == 130.46
    )
    contract = report["post_probe_real_outcome_metric_contract"]
    assert contract["metric_role"] == "multi_leg_post_probe_real_outcome_attribution"
    assert contract["decision_authority"].startswith("source_only_")
    assert "bot_restart" in contract["forbidden_uses"]


def test_whole_day_real_entry_lifecycle_reconciles_all_venues_and_entry_states(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-29.jsonl"
    rows = [
        _event(
            801,
            "801801",
            "premarket-winner",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "requested_qty": 1,
                "order_no": "P801",
                "order_price": 10000,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_session_bucket": "krx_like_premarket",
            },
            emitted_at="2026-07-29T08:10:00+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            801,
            "801801",
            "premarket-winner",
            "holding_started",
            {
                "actual_order_submitted": True,
                "buy_qty": 1,
                "buy_price": 10000,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_session_bucket": "krx_like_premarket",
            },
            emitted_at="2026-07-29T08:10:01+09:00",
        ),
        _event(
            801,
            "801801",
            "premarket-winner",
            "sell_completed",
            {
                "profit_rate": 0.4,
                "realized_pnl_krw": 40,
                "sell_price": 10050,
            },
            emitted_at="2026-07-29T08:12:00+09:00",
        ),
        _event(
            802,
            "802802",
            "premarket-cancel",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "requested_qty": 1,
                "order_no": "P802",
                "order_price": 20000,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_session_bucket": "krx_like_premarket",
            },
            emitted_at="2026-07-29T08:20:00+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            802,
            "802802",
            "premarket-cancel",
            "entry_order_cancel_confirmed",
            {
                "filled_qty": 0,
                "unfilled_qty": 1,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "market_session_bucket": "krx_like_premarket",
            },
            emitted_at="2026-07-29T08:21:30+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            803,
            "803803",
            "krx-loss",
            "probe_submitted",
            {
                "actual_order_submitted": True,
                "forced_entry_qty": 5,
                "qty": 1,
                "order_no": "K803",
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
            emitted_at="2026-07-29T10:00:00+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            803,
            "803803",
            "krx-loss",
            "holding_started",
            {
                "actual_order_submitted": True,
                "buy_qty": 1,
                "buy_price": 3000,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
            emitted_at="2026-07-29T10:00:01+09:00",
        ),
        _event(
            803,
            "803803",
            "krx-loss",
            "sell_completed",
            {"profit_rate": -0.2, "realized_pnl_krw": -6, "sell_price": 3000},
            emitted_at="2026-07-29T10:01:00+09:00",
        ),
        _event(
            804,
            "804804",
            "nxt-open",
            "probe_submitted",
            {
                "actual_order_submitted": True,
                "forced_entry_qty": 2,
                "qty": 1,
                "order_no": "N804",
                "probe_bundle_id": "bundle-804",
                "effective_venue": "NXT",
                "market_session_bucket": "nxt",
            },
            emitted_at="2026-07-29T17:00:00+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            804,
            "804804",
            "nxt-open",
            "probe_filled",
            {
                "probe_bundle_id": "bundle-804",
                "forced_entry_qty": 2,
                "fill_qty": 1,
                "fill_price": 60000,
                "effective_venue": "NXT",
                "market_session_bucket": "nxt",
            },
            emitted_at="2026-07-29T17:00:00.500000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            804,
            "804804",
            "nxt-open",
            "holding_started",
            {
                "actual_order_submitted": True,
                "buy_qty": 1,
                "buy_price": 60000,
                "effective_venue": "NXT",
                "market_session_bucket": "nxt",
            },
            emitted_at="2026-07-29T17:00:01+09:00",
        ),
        _event(
            804,
            "804804",
            "nxt-open",
            "residual_submitted",
            {
                "probe_bundle_id": "bundle-804",
                "forced_entry_qty": 2,
                "qty": 1,
                "order_no": "N804-R1",
                "price": 60000,
                "effective_venue": "NXT",
                "market_session_bucket": "nxt",
            },
            emitted_at="2026-07-29T17:00:01.250000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-29", pipeline_path=pipeline_path, generated_at="fixed"
    )
    summary = report["summary"]["whole_day_real_entry_lifecycle"]
    lifecycle_rows = {
        item["stock_code"]: item
        for item in report["whole_day_real_entry_lifecycle_rows"]
    }

    assert summary["submitted_cycle_count"] == 4
    assert summary["filled_cycle_count"] == 3
    assert summary["canceled_unfilled_cycle_count"] == 1
    assert summary["closed_cycle_count"] == 2
    assert summary["holding_cycle_count"] == 1
    assert summary["winner_count"] == 1
    assert summary["loss_count"] == 1
    assert summary["realized_pnl_krw_known_sum"] == 34
    assert summary["realized_pnl_source_quality_state"] == "complete"
    assert summary["single_share_plan_closed_winner_count"] == 1
    assert summary["multi_leg_probe_cycle_count"] == 2
    assert {item["effective_venue"] for item in summary["by_effective_venue"]} == {
        "KRX",
        "NXT",
        "PREMARKET_KRX_LIKE",
    }
    assert lifecycle_rows["803803"]["planned_qty"] == 5
    assert lifecycle_rows["803803"]["broker_submitted_qty"] == 1
    assert lifecycle_rows["804804"]["broker_submitted_qty"] == 2
    assert lifecycle_rows["804804"]["filled_qty"] == 1
    assert lifecycle_rows["804804"]["lifecycle_state"] == "holding"
    assert report["whole_day_real_entry_lifecycle_metric_contract"][
        "decision_authority"
    ].startswith("source_only_")
    assert report["whole_day_real_entry_lifecycle_rows"][0]["runtime_effect"] is False

    output_json = tmp_path / "feedback.json"
    output_md = tmp_path / "feedback.md"
    mod.write_outputs(report, output_json=output_json, output_md=output_md)
    markdown = output_md.read_text(encoding="utf-8")
    assert "- canonical_expansion_missed_upside_count: 0" in markdown
    assert "## Whole-Day Real Entry Lifecycle Rows" in markdown
    assert "venue=PREMARKET_KRX_LIKE" in markdown
    assert "state=holding" in markdown


def test_real_entry_lifecycle_separates_reused_record_id_by_scanner_attempt(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-24.jsonl"
    first_attempt = "SCANPROM-003350-1787544456554"
    second_attempt = "SCANPROM-003350-1787546124680"
    rows = [
        _event(
            34702,
            "003350",
            "한국화장품제조",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "requested_qty": 1,
                "order_no": "0043176",
                "scanner_promotion_id": first_attempt,
                "main_lifecycle_attempt_id": first_attempt,
                "main_lifecycle_id": "mlc-first",
                "effective_venue": "KRX",
            },
            emitted_at="2026-08-24T13:10:24+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            34702,
            "003350",
            "한국화장품제조",
            "entry_order_cancel_confirmed",
            {
                "filled_qty": 0,
                "unfilled_qty": 1,
                "scanner_promotion_id": first_attempt,
                "effective_venue": "KRX",
            },
            emitted_at="2026-08-24T13:11:52+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        # Runtime fill can be journaled before the order bundle receipt.
        _event(
            34702,
            "003350",
            "한국화장품제조",
            "holding_started",
            {
                "actual_order_submitted": True,
                "buy_qty": 1,
                "buy_price": 11750,
                "main_lifecycle_attempt_id": second_attempt,
                "main_lifecycle_id": "mlc-second",
                "effective_venue": "KRX",
            },
            emitted_at="2026-08-24T13:36:06+09:00",
        ),
        _event(
            34702,
            "003350",
            "한국화장품제조",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "requested_qty": 1,
                "order_no": "0045294",
                "main_lifecycle_attempt_id": second_attempt,
                "main_lifecycle_id": "mlc-second",
                "effective_venue": "KRX",
            },
            emitted_at="2026-08-24T13:36:09+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-24", pipeline_path=pipeline_path, generated_at="fixed"
    )
    summary = report["summary"]["whole_day_real_entry_lifecycle"]
    lifecycle_rows = report["whole_day_real_entry_lifecycle_rows"]

    assert summary["submitted_cycle_count"] == 2
    assert summary["filled_cycle_count"] == 1
    assert summary["canceled_unfilled_cycle_count"] == 1
    assert summary["holding_cycle_count"] == 1
    assert {item["attempt_id"] for item in lifecycle_rows} == {
        first_attempt,
        second_attempt,
    }
    assert {tuple(item["entry_submit_order_nos"]) for item in lifecycle_rows} == {
        ("0043176",),
        ("0045294",),
    }


def test_real_entry_lifecycle_reconstructs_legacy_full_close_realized_pnl(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-29.jsonl"
    rows = [
        _event(
            811,
            "811811",
            "legacy-revive",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "requested_qty": 2,
                "order_no": "K811",
                "effective_venue": "KRX",
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            811,
            "811811",
            "legacy-revive",
            "holding_started",
            {"buy_qty": 2, "buy_price": 10_000, "effective_venue": "KRX"},
        ),
        _event(
            811,
            "811811",
            "legacy-revive",
            "sell_completed",
            {"sell_qty": 2, "sell_price": 10_100, "profit_rate": 0.77},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-29", pipeline_path=pipeline_path, generated_at="fixed"
    )
    lifecycle = report["whole_day_real_entry_lifecycle_rows"][0]
    summary = report["summary"]["whole_day_real_entry_lifecycle"]

    assert lifecycle["realized_pnl_krw"] == 154
    assert lifecycle["realized_pnl_krw_source"] == (
        "reconstructed_same_cycle_full_close_fee_aware"
    )
    assert summary["realized_pnl_krw_known_count"] == 1
    assert summary["realized_pnl_krw_missing_count"] == 0
    assert summary["realized_pnl_krw_source_counts"] == [
        {
            "source": "reconstructed_same_cycle_full_close_fee_aware",
            "count": 1,
        }
    ]


def test_real_entry_lifecycle_reconciles_stale_sell_buy_price_to_holding_fill(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-24.jsonl"
    rows = [
        _event(
            34620,
            "003530",
            "한화투자증권",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "requested_qty": 1,
                "order_no": "0020775",
                "effective_venue": "KRX",
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            34620,
            "003530",
            "한화투자증권",
            "holding_started",
            {"buy_qty": 1, "buy_price": 5_040, "effective_venue": "KRX"},
        ),
        _event(
            34620,
            "003530",
            "한화투자증권",
            "sell_completed",
            {
                "buy_price": 5_110,
                "sell_qty": 1,
                "sell_price": 5_070,
                "profit_rate": -1.02,
                "realized_pnl_krw": -52,
                "realized_pnl_krw_source": "broker_fill_prices_fee_aware",
            },
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-24", pipeline_path=pipeline_path, generated_at="fixed"
    )
    lifecycle = report["whole_day_real_entry_lifecycle_rows"][0]
    summary = report["summary"]["whole_day_real_entry_lifecycle"]

    assert lifecycle["final_profit_rate"] == 0.36
    assert lifecycle["realized_pnl_krw"] == 18
    assert lifecycle["realized_pnl_krw_source"] == (
        "reconciled_same_cycle_broker_fill_prices_fee_aware"
    )
    assert lifecycle["lifecycle_economics_reconciled"] is True
    assert lifecycle["raw_sell_completed_buy_price"] == 5_110
    assert lifecycle["raw_sell_completed_profit_rate"] == -1.02
    assert lifecycle["raw_sell_completed_realized_pnl_krw"] == -52
    assert summary["winner_count"] == 1
    assert summary["loss_count"] == 0
    assert summary["realized_pnl_krw_known_sum"] == 18


def test_real_entry_lifecycle_does_not_reconcile_multi_share_average_change(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-24.jsonl"
    rows = [
        _event(
            900,
            "900900",
            "multi-share",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "requested_qty": 2,
                "order_no": "K900",
                "effective_venue": "KRX",
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            900,
            "900900",
            "multi-share",
            "holding_started",
            {"buy_qty": 2, "buy_price": 5_040, "effective_venue": "KRX"},
        ),
        _event(
            900,
            "900900",
            "multi-share",
            "sell_completed",
            {
                "buy_price": 5_110,
                "sell_qty": 2,
                "sell_price": 5_070,
                "profit_rate": -1.02,
                "realized_pnl_krw": -104,
            },
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-24", pipeline_path=pipeline_path, generated_at="fixed"
    )
    lifecycle = report["whole_day_real_entry_lifecycle_rows"][0]

    assert lifecycle["final_profit_rate"] == -1.02
    assert lifecycle["realized_pnl_krw"] == -104
    assert "lifecycle_economics_reconciled" not in lifecycle


def test_real_entry_lifecycle_does_not_reconcile_code_only_fallback_cycle(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-08-24.jsonl"
    rows = [
        _event(
            "",
            "003530",
            "code-only",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "requested_qty": 1,
                "order_no": "0020775",
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            "",
            "003530",
            "code-only",
            "holding_started",
            {"buy_qty": 1, "buy_price": 5_040},
        ),
        _event(
            "",
            "003530",
            "code-only",
            "sell_completed",
            {
                "buy_price": 5_110,
                "sell_qty": 1,
                "sell_price": 5_070,
                "profit_rate": -1.02,
                "realized_pnl_krw": -52,
            },
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-24", pipeline_path=pipeline_path, generated_at="fixed"
    )
    lifecycle = report["whole_day_real_entry_lifecycle_rows"][0]

    assert lifecycle["final_profit_rate"] == -1.02
    assert lifecycle["realized_pnl_krw"] == -52
    assert "lifecycle_economics_reconciled" not in lifecycle


def test_real_entry_lifecycle_does_not_reconstruct_partial_sell_pnl(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-29.jsonl"
    rows = [
        _event(
            812,
            "812812",
            "partial-close",
            "order_bundle_submitted",
            {"actual_order_submitted": True, "requested_qty": 2, "order_no": "K812"},
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            812,
            "812812",
            "partial-close",
            "holding_started",
            {"buy_qty": 2, "buy_price": 10_000},
        ),
        _event(
            812,
            "812812",
            "partial-close",
            "sell_completed",
            {"sell_qty": 1, "sell_price": 10_100, "profit_rate": 0.77},
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-29", pipeline_path=pipeline_path, generated_at="fixed"
    )

    assert (
        report["whole_day_real_entry_lifecycle_rows"][0].get("realized_pnl_krw") is None
    )
    assert (
        report["summary"]["whole_day_real_entry_lifecycle"][
            "realized_pnl_krw_missing_count"
        ]
        == 1
    )


def test_post_probe_confirmation_reconstructs_event_time_and_excludes_after_terminal(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-29.jsonl"

    def direction_event(emitted_at, signature):
        return _event(
            704,
            "704704",
            "event-order",
            "probe_continuation_deferred",
            {
                "probe_bundle_id": "bundle-704",
                "post_probe_direction_state": "UNKNOWN",
                "post_probe_continuation_action": "DEFER",
                "post_probe_direction_positive_groups": "orderbook,signed_pressure",
                "post_probe_direction_negative_groups": "-",
                "post_probe_direction_mark_price": 10000,
                "post_probe_direction_probe_fill_price": 10000,
                "post_probe_direction_ai_action": "WAIT",
                "post_probe_hard_veto": False,
                "post_probe_confirmation_evidence_version_proven": True,
                "post_probe_confirmation_source_version_signature": signature,
                "post_probe_direction_tick_context_fresh": True,
            },
            emitted_at=emitted_at,
            pipeline="ENTRY_PIPELINE",
        )

    rows = [
        _event(
            704,
            "704704",
            "event-order",
            "entry_split_order_plan_applied",
            {
                "rising_missed_one_share_scout": True,
                "entry_split_order_probe_first_applied": True,
                "effective_qty": 11,
                "forced_entry_qty": 11,
                "entry_split_order_probe_qty": 1,
                "entry_split_order_leg_count": 4,
                "entry_split_order_qty_weight_min": 0.4,
                "effective_venue": "KRX",
            },
            emitted_at="2026-07-29T10:00:00.000000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            704,
            "704704",
            "event-order",
            "probe_filled",
            {
                "probe_bundle_id": "bundle-704",
                "fill_qty": 1,
                "fill_price": 10000,
                "effective_venue": "KRX",
            },
            emitted_at="2026-07-29T10:00:00.100000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            704,
            "704704",
            "event-order",
            "residual_blocked",
            {
                "probe_bundle_id": "bundle-704",
                "reason": "residual_revalidation_timeout",
                "entry_split_probe_scale_in_recheck_allowed": False,
            },
            emitted_at="2026-07-29T10:00:03.000000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        # Independent writers may append earlier event-time rows after terminal rows.
        direction_event("2026-07-29T10:00:00.500000+09:00", "source-a"),
        direction_event("2026-07-29T10:00:00.800000+09:00", "source-b"),
        direction_event("2026-07-29T10:00:03.100000+09:00", "after-terminal"),
        _event(
            704,
            "704704",
            "event-order",
            "sell_completed",
            {"profit_rate": 0.2},
            emitted_at="2026-07-29T10:01:00.000000+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-29", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["post_probe_real_confirmation_max_count"] == 2
    assert item["post_probe_real_confirmation_ready"] is True
    assert item["post_probe_real_confirmation_excluded_observation_count"] == 1
    assert item["post_probe_real_outcome_label"] == (
        "profitable_zero_fill_confirmation_ready"
    )


def test_runtime_two_of_two_confirmation_is_not_hidden_when_strict_tick_quality_rejects(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-31.jsonl"
    rows = [
        _event(
            25678,
            "000250",
            "삼천당제약",
            "entry_split_order_plan_applied",
            {
                "rising_missed_one_share_scout": True,
                "entry_split_order_probe_first_applied": True,
                "effective_qty": 3,
                "forced_entry_qty": 3,
                "entry_split_order_probe_qty": 1,
                "entry_split_order_leg_count": 3,
                "entry_split_order_qty_weight_min": 0.5,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
            emitted_at="2026-07-31T10:12:34.499000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            25678,
            "000250",
            "삼천당제약",
            "probe_filled",
            {
                "probe_bundle_id": "000250-probe-83b1f1fb0dee",
                "fill_qty": 1,
                "fill_price": 146600,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
            },
            emitted_at="2026-07-31T10:12:34.655000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            25678,
            "000250",
            "삼천당제약",
            "probe_continuation_deferred",
            {
                "probe_bundle_id": "000250-probe-83b1f1fb0dee",
                "probe_confirmation_count": 1,
                "post_probe_direction_state": "STRONG",
                "post_probe_continuation_action": "DEFER",
                "post_probe_direction_positive_groups": "price_tick,orderbook",
                "post_probe_direction_negative_groups": "-",
                "post_probe_direction_mark_price": 146700,
                "post_probe_direction_probe_fill_price": 146600,
                "post_probe_direction_ai_action": "WAIT",
                "post_probe_hard_veto": False,
                "post_probe_confirmation_evidence_version_proven": True,
                "post_probe_confirmation_source_version_signature": "source-a",
                "post_probe_direction_tick_context_fresh": False,
            },
            emitted_at="2026-07-31T10:12:35.687000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            25678,
            "000250",
            "삼천당제약",
            "residual_planned",
            {
                "probe_bundle_id": "000250-probe-83b1f1fb0dee",
                "probe_confirmation_count": 2,
                "post_probe_confirmation_grant_active": True,
                "post_probe_direction_state": "STRONG",
                "post_probe_continuation_action": "ALLOW_RECOVERED_WIDE",
                "post_probe_direction_positive_groups": "price_tick,orderbook",
                "post_probe_direction_negative_groups": "-",
                "post_probe_direction_mark_price": 146700,
                "post_probe_direction_probe_fill_price": 146600,
                "post_probe_direction_ai_action": "WAIT",
                "post_probe_hard_veto": False,
                "post_probe_confirmation_evidence_version_proven": True,
                "post_probe_confirmation_source_version_signature": "source-b",
                "post_probe_direction_tick_context_fresh": False,
            },
            emitted_at="2026-07-31T10:12:36.198000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            25678,
            "000250",
            "삼천당제약",
            "residual_blocked",
            {
                "probe_bundle_id": "000250-probe-83b1f1fb0dee",
                "reason": "residual_leg_direction_deferred",
                "probe_confirmation_count": 2,
                "entry_split_probe_scale_in_recheck_allowed": False,
            },
            emitted_at="2026-07-31T10:12:36.282000+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            25678,
            "000250",
            "삼천당제약",
            "sell_completed",
            {"profit_rate": 0.38, "peak_profit": 1.06},
            emitted_at="2026-07-31T10:14:11.539000+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-31", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]
    summary = report["summary"]

    assert item["post_probe_runtime_confirmation_max_count"] == 2
    assert item["post_probe_runtime_confirmation_ready"] is True
    assert item["post_probe_real_confirmation_max_count"] == 0
    assert item["post_probe_real_confirmation_ready"] is False
    assert item["post_probe_confirmation_contract_alignment"] == (
        "runtime_confirmed_source_quality_disputed"
    )
    assert item["post_probe_real_confirmation_source_quality_blockers"] == [
        "tick_context_not_fresh"
    ]
    assert item["post_probe_real_outcome_label"] == (
        "profitable_zero_fill_no_confirmation"
    )
    assert item["post_probe_runtime_outcome_label"] == (
        "profitable_zero_fill_runtime_confirmation_ready"
    )
    assert item["canonical_expansion_outcome_label"] == (
        "expansion_missed_upside_runtime_confirmed_source_quality_disputed"
    )
    assert item["canonical_expansion_missed_upside_candidate"] is True
    assert summary["canonical_expansion_missed_upside_count"] == 1
    assert summary["canonical_expansion_source_quality_valid_missed_upside_count"] == 0
    assert summary["post_probe_runtime_confirmation_source_quality_disputed_count"] == 1
    assert (
        summary["probe_residual_confirmation_ready_counterfactual_ev_eligible_count"]
        == 0
    )


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


def test_hard_abort_recovery_confirmation_becomes_source_only_normal_winner_candidate(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-03.jsonl"
    recovery_contract = {
        "probe_bundle_id": "bundle-recovery",
        "recovery_evaluation_seen": True,
        "recovery_state": "STRONG",
        "recovery_reason": "post_hard_abort_recovery_confirmed",
        "recovery_eligible": True,
        "recovery_source_quality_blockers": "-",
        "recovery_positive_groups": "price,signed_tape,tick_impulse,micro_vwap",
        "recovery_negative_groups": "-",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": (
            "source_only_post_hard_abort_recovery_observation_no_runtime_mutation"
        ),
        "profit_rate": 1.2,
        "peak_profit": 1.2,
        "current_ai_score": 72,
        "buy_pressure_10t": 50,
        "tick_aggressor_trusted_count": 0,
        "tick_aggressor_pressure_usable": False,
        "tick_acceleration_ratio": 1.3,
        "curr_vs_micro_vwap_bp": 20,
        "micro_vwap_available": True,
        "minute_candle_window_fresh": True,
        "recovery_ai_thesis_state": "supportive",
        "recovery_ai_tape_substitution_applied": True,
        "recovery_ai_parent_prompt_version": "decision_quality_v2_14",
        "recovery_holding_ai_action": "HOLD",
        "recovery_holding_ai_data_quality": "fresh",
    }
    rows = [
        _event(
            701,
            "123456",
            "recovery-winner",
            "rising_missed_one_share_entry",
            {
                "forced_entry_qty": 12,
                "actual_order_submitted": False,
                "effective_venue": "PREMARKET_KRX_LIKE",
                "entry_split_order_leg_count": 3,
                "entry_split_order_qty_weight_min": 0.4,
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            701,
            "123456",
            "recovery-winner",
            "probe_filled",
            {
                "probe_bundle_id": "bundle-recovery",
                "fill_qty": 1,
                "fill_price": 10000,
                "effective_venue": "PREMARKET_KRX_LIKE",
            },
            emitted_at="2026-08-03T09:00:00+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            701,
            "123456",
            "recovery-winner",
            "residual_blocked",
            {
                "probe_bundle_id": "bundle-recovery",
                "reason": "fresh_ai_drop_veto",
                "entry_split_probe_scale_in_recheck_allowed": False,
            },
            emitted_at="2026-08-03T09:00:01+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            701,
            "123456",
            "recovery-winner",
            "post_probe_hard_abort_recovery_observed",
            {
                **recovery_contract,
                "recovery_evidence_signature": "recovery-a",
                "recovery_confirmation_count": 1,
                "recovery_confirmation_ready": False,
            },
            emitted_at="2026-08-03T09:00:02+09:00",
        ),
        _event(
            701,
            "123456",
            "recovery-winner",
            "post_probe_terminal_abort_recovery_observed",
            {
                **recovery_contract,
                "decision_authority": (
                    "source_only_post_terminal_abort_recovery_observation_"
                    "no_runtime_mutation"
                ),
                "recovery_abort_class": "soft",
                "recovery_state": "SOURCE_BLOCKED",
                "recovery_reason": "source_quality_blocked:quote_stale",
                "recovery_eligible": False,
                "recovery_source_quality_blockers": "quote_stale",
                "recovery_confirmation_preserved": True,
                "recovery_evidence_signature": "recovery-gap",
                "recovery_confirmation_count": 1,
                "recovery_confirmation_ready": False,
                "recovery_ai_thesis_state": "neutral_or_unproven",
                "recovery_ai_tape_substitution_applied": False,
            },
            emitted_at="2026-08-03T09:00:02.150000+09:00",
        ),
        _event(
            701,
            "123456",
            "recovery-winner",
            "post_probe_terminal_abort_recovery_observed",
            {
                **recovery_contract,
                "decision_authority": (
                    "source_only_post_terminal_abort_recovery_observation_"
                    "no_runtime_mutation"
                ),
                "recovery_abort_class": "soft",
                "recovery_evidence_signature": "recovery-b",
                "recovery_confirmation_count": 2,
                "recovery_confirmation_ready": True,
            },
            emitted_at="2026-08-03T09:00:02.300000+09:00",
        ),
        _event(
            701,
            "123456",
            "recovery-winner",
            "stat_action_decision_snapshot",
            {"profit_rate": 3.0, "peak_profit": 3.0},
            emitted_at="2026-08-03T09:00:05+09:00",
        ),
        _event(
            701,
            "123456",
            "recovery-winner",
            "sell_completed",
            {"profit_rate": 2.5, "peak_profit": 3.0},
            emitted_at="2026-08-03T09:01:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["post_probe_real_confirmation_ready"] is False
    assert item["post_probe_hard_abort_recovery_confirmation_ready"] is True
    assert item["post_probe_real_outcome_label"] == (
        "profitable_zero_fill_recovery_confirmation_ready"
    )
    assert item["canonical_expansion_outcome_label"] == (
        "expansion_recovery_missed_upside_confirmation_ready"
    )
    assert item["normal_winner_expansion_candidate_seen"] is True
    assert item["normal_winner_expansion_blocker_reason"] == (
        "post_terminal_abort_recovery_source_only"
    )
    assert item["normal_winner_expansion_blocker_namespace"] == (
        "POST_PROBE_TERMINAL_ABORT_RECOVERY"
    )
    assert item["post_probe_terminal_abort_recovery_latest_class"] == "soft"
    assert report["summary"]["post_terminal_abort_recovery_soft_count"] == 1
    assert report["summary"]["post_terminal_abort_recovery_hard_count"] == 0
    assert item["normal_winner_expansion_label"] == "realized_incremental_winner"
    assert item["runtime_effect"] is False
    assert item["actual_order_submitted"] is False
    assert report["summary"]["post_hard_abort_recovery_confirmation_ready_count"] == 1
    assert (
        item["post_probe_hard_abort_recovery_confirmation_preserved_gap_count"] == 1
    )
    assert item["post_probe_hard_abort_recovery_ai_thesis_state_counts"] == {
        "neutral_or_unproven": 1,
        "supportive": 2,
    }
    assert item["post_probe_hard_abort_recovery_ai_tape_substitution_count"] == 2
    assert (
        report["summary"][
            "post_terminal_abort_recovery_confirmation_preserved_gap_count"
        ]
        == 1
    )
    assert (
        report["summary"][
            "post_terminal_abort_recovery_ai_supportive_evaluation_count"
        ]
        == 2
    )
    assert (
        report["summary"][
            "post_terminal_abort_recovery_ai_tape_substitution_count"
        ]
        == 2
    )
    ai_axis = report["summary"]["normal_winner_expansion"][
        "feature_axis_metrics"
    ]["recovery_ai_thesis_state"]
    assert len(ai_axis) == 1
    assert ai_axis[0]["bucket"] == "supportive"
    assert ai_axis[0]["sample_count"] == 1
    assert ai_axis[0]["realized_incremental_winner_count"] == 1
    persisted = report["normal_winner_expansion_rows"][0]
    assert persisted["normal_winner_expansion_recovery_ai_thesis_state"] == (
        "supportive"
    )
    assert (
        persisted[
            "normal_winner_expansion_recovery_ai_tape_substitution_applied"
        ]
        is True
    )
    assert persisted["normal_winner_expansion_recovery_ai_parent_prompt_version"] == (
        "decision_quality_v2_14"
    )
    assert report["summary"]["canonical_expansion_missed_upside_count"] == 1


def test_profitable_hard_abort_without_recovery_is_not_labeled_correct_block(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-03.jsonl"
    rows = [
        _event(
            702,
            "654321",
            "unevaluated-winner",
            "rising_missed_one_share_entry",
            {
                "forced_entry_qty": 10,
                "actual_order_submitted": False,
                "effective_venue": "KRX",
            },
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            702,
            "654321",
            "unevaluated-winner",
            "probe_filled",
            {
                "probe_bundle_id": "bundle-unevaluated",
                "fill_qty": 1,
                "fill_price": 10000,
                "effective_venue": "KRX",
            },
            emitted_at="2026-08-03T09:00:00+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            702,
            "654321",
            "unevaluated-winner",
            "residual_blocked",
            {
                "probe_bundle_id": "bundle-unevaluated",
                "reason": "fresh_ai_drop_veto",
                "entry_split_probe_scale_in_recheck_allowed": False,
            },
            emitted_at="2026-08-03T09:00:01+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            702,
            "654321",
            "unevaluated-winner",
            "sell_completed",
            {"profit_rate": 2.0, "peak_profit": 3.0},
            emitted_at="2026-08-03T09:01:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-03", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["post_probe_real_outcome_label"] == (
        "profitable_zero_fill_recovery_evaluation_not_run"
    )
    assert item["canonical_expansion_outcome_label"] == (
        "expansion_recovery_evaluation_not_run"
    )
    assert item["canonical_expansion_outcome_label"] != (
        "expansion_correctly_not_expanded_no_confirmation"
    )
    assert (
        report["summary"][
            "post_hard_abort_recovery_evaluation_not_run_profitable_count"
        ]
        == 1
    )


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
                "entry_price_resolver_offset_profile": "normal",
                "entry_price_resolver_action": "passive_reprice",
                "entry_price_resolver_previous_price": 14100,
                "entry_price_resolver_resolved_price": 14050,
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
    assert item["post_probe_reprice_observed"] is True
    assert item["post_probe_reprice_provenance_complete"] is True
    assert item["post_probe_reprice_provenance_rejected_leg_count"] == 0
    assert item["post_probe_reprice_outcome_source_quality_valid"] is False
    assert item["post_probe_reprice_outcome_source_quality_reasons"] == [
        "real_sell_completed_profit_missing"
    ]
    assert item["post_probe_reprice_avg_passive_improvement_bps"] == 35.461


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


def test_post_sell_pyramid_candidate_is_temporal_source_quality_blocked(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-28.jsonl"
    rows = [
        _event(
            608,
            "285800",
            "temporal",
            "rising_missed_one_share_entry",
            {
                "actual_order_submitted": True,
                "forced_entry_qty": 9,
                "rising_missed_effective_venue": "NXT",
                "rising_missed_market_session_bucket": "nxt_entry_window",
            },
            emitted_at="2026-07-28T19:38:40+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            608,
            "285800",
            "temporal",
            "probe_filled",
            {
                "probe_bundle_id": "bundle-608",
                "fill_qty": 1,
                "fill_price": 14080,
                "effective_venue": "NXT",
                "market_session_bucket": "nxt_entry_window",
            },
            emitted_at="2026-07-28T19:38:41+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            608,
            "285800",
            "temporal",
            "residual_blocked",
            {
                "probe_bundle_id": "bundle-608",
                "reason": "residual_revalidation_timeout",
                "forced_entry_qty": 9,
            },
            emitted_at="2026-07-28T19:38:44+09:00",
            pipeline="ENTRY_PIPELINE",
        ),
        _event(
            608,
            "285800",
            "temporal",
            "sell_completed",
            {"profit_rate": "+0.62", "peak_profit": "+1.20"},
            emitted_at="2026-07-28T19:38:49+09:00",
        ),
        _event(
            608,
            "285800",
            "temporal",
            "pyramid_blocked_reason",
            {
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_reason": "probe_expand_forbidden",
                "profit_rate": "+1.05",
                "current_ai_score": 70,
                "buy_pressure_10t": 80,
                "tick_aggressor_trusted_count": 10,
                "tick_aggressor_pressure_usable": True,
                "tick_acceleration_ratio": 1.2,
                "curr_vs_micro_vwap_bp": 10,
                "micro_vwap_available": True,
                "minute_candle_window_fresh": True,
            },
            emitted_at="2026-07-28T19:39:33+09:00",
        ),
    ]
    # Independent writers may flush in a different order than event time.
    rows[-2], rows[-1] = rows[-1], rows[-2]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-07-28", pipeline_path=pipeline_path, generated_at="fixed"
    )
    item = report["normal_winner_expansion_rows"][0]
    summary = report["summary"]["normal_winner_expansion"]

    assert report["pyramid_feedback_rows"] == []
    assert item["normal_winner_expansion_temporal_inversion"] is True
    assert item["normal_winner_expansion_candidate_at"] is None
    assert item["final_profit_rate"] == 0.62
    assert item["normal_winner_expansion_label"] == "source_quality_blocked"
    assert (
        "temporal_inversion:candidate_after_final_ts"
        in item["normal_winner_expansion_source_quality_reasons"]
    )
    assert summary["temporal_inversion_candidate_count"] == 1
    assert summary["source_quality_valid_candidate_count"] == 0
    assert summary["closed_candidate_count"] == 0
    assert report["source_quality"]["status"] == "pass"
    assert report["source_quality"]["temporal_inversion_candidate_count"] == 1


def test_real_scale_in_performance_separates_winner_recovery_and_avg_down(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-04.jsonl"
    rows = [
        _event(
            701,
            "111111",
            "avg-down-open",
            "scale_in_executed",
            {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "A1",
                "fill_price": 9900,
                "fill_qty": 1,
                "add_type": "AVG_DOWN",
                "add_reason": "late_loss_avg_down_retry",
                "new_avg_price": 10000,
                "new_buy_qty": 2,
            },
            emitted_at="2026-08-04T10:00:00+09:00",
        ),
        _event(
            701,
            "111111",
            "avg-down-open",
            "ai_holding_review",
            {"profit_rate": "-1.25"},
            emitted_at="2026-08-04T10:01:00+09:00",
        ),
        _event(
            702,
            "222222",
            "winner-recovery",
            "scale_in_executed",
            {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "P1",
                "fill_price": 10000,
                "fill_qty": 1,
                "add_type": "PYRAMID",
                "add_reason": "post_probe_winner_recovery_first_leg",
                "new_avg_price": 9950,
                "new_buy_qty": 2,
                "post_probe_winner_recovery_ai_thesis_state": "supportive",
                "post_probe_winner_recovery_ai_parent_action": "WAIT",
                "post_probe_winner_recovery_ai_parent_prompt_version": "entry-v9",
                "post_probe_winner_recovery_ai_parent_trace_id": "entry-trace-v9",
                "post_probe_winner_recovery_ai_parent_snapshot_id": (
                    "entry-snapshot-v9"
                ),
                "post_probe_winner_recovery_holding_ai_action": "HOLD",
                "post_probe_winner_recovery_holding_ai_data_quality": "fresh",
                "post_probe_winner_recovery_holding_ai_input_schema": (
                    "holding_decision_context_v1"
                ),
                "post_probe_winner_recovery_ai_tape_substitution_applied": True,
            },
            emitted_at="2026-08-04T10:02:00+09:00",
        ),
        _event(
            702,
            "222222",
            "winner-recovery",
            "scale_in_executed",
            {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "P1",
                "fill_price": 10100,
                "fill_qty": 1,
                "add_type": "PYRAMID",
                "add_reason": "post_probe_winner_recovery_first_leg",
                "new_avg_price": 10000,
                "new_buy_qty": 3,
            },
            emitted_at="2026-08-04T10:02:01+09:00",
        ),
        _event(
            702,
            "222222",
            "winner-recovery",
            "sell_completed",
            {"profit_rate": "+1.20", "sell_price": 10150},
            emitted_at="2026-08-04T10:05:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-04", pipeline_path=pipeline_path, generated_at="fixed"
    )
    summary = report["summary"]["real_scale_in_performance"]
    items = {
        item["scale_in_outcome_cohort"]: item
        for item in report["real_scale_in_performance_rows"]
    }

    assert summary["execution_count"] == 2
    assert summary["closed_count"] == 1
    assert summary["active_unrealized_count"] == 1
    assert summary["avg_down_execution_count"] == 1
    assert summary["winner_recovery_execution_count"] == 1
    assert summary["winner_expansion_vs_avg_down_asymmetry_observed"] is False
    assert items["avg_down"]["closed"] is not True
    assert items["avg_down"]["latest_position_profit_pct"] == -1.25
    assert items["winner_recovery"]["final_position_profit_pct"] == 1.2
    assert items["winner_recovery"]["fill_qty"] == 2
    assert items["winner_recovery"]["fill_price"] == 10050
    assert items["winner_recovery"]["scale_in_leg_gross_return_proxy_pct"] == 0.995
    assert items["winner_recovery"]["winner_recovery_qty_cap_valid"] is False
    assert items["winner_recovery"]["recovery_ai_thesis_state"] == "supportive"
    assert items["winner_recovery"]["recovery_ai_parent_prompt_version"] == "entry-v9"
    assert items["winner_recovery"]["recovery_ai_parent_trace_id"] == (
        "entry-trace-v9"
    )
    assert items["winner_recovery"]["recovery_ai_parent_snapshot_id"] == (
        "entry-snapshot-v9"
    )
    assert items["winner_recovery"]["recovery_holding_ai_action"] == "HOLD"
    assert items["winner_recovery"]["recovery_ai_tape_substitution_applied"] is True
    assert items["winner_recovery"]["recovery_holding_ai_input_schema"] == (
        "holding_decision_context_v1"
    )
    assert summary["winner_recovery_qty_cap_invalid_count"] == 1
    assert report["source_quality"]["status"] == "winner_recovery_qty_cap_invalid"
    assert summary["winner_recovery_by_ai_thesis_state"] == [
        {
            "recovery_ai_thesis_state": "supportive",
            "execution_count": 1,
            "closed_count": 1,
            "closed_winner_count": 1,
            "equal_weight_avg_final_position_profit_pct": 1.2,
            "source_quality_valid_closed_count": 0,
            "source_quality_adjusted_ev_pct": None,
            "runtime_apply_authority": False,
        }
    ]
    assert summary["source_quality_adjusted_ev_available"] is False
    assert (
        report["real_scale_in_performance_metric_contract"]["metric_role"]
        == "real_scale_in_execution_outcome_attribution"
    )


def test_real_scale_in_performance_calculates_fee_aware_ev_from_complete_receipts(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-04.jsonl"
    rows = [
        _event(
            703,
            "333333",
            "winner-recovery-valid",
            "scale_in_executed",
            {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "P2",
                "fill_price": 10000,
                "fill_qty": 1,
                "add_type": "PYRAMID",
                "add_reason": "post_probe_winner_recovery_first_leg",
                "new_avg_price": 9950,
                "new_buy_qty": 2,
                "receipt_economics_complete": True,
                "receipt_quantity_contract_complete": True,
                "receipt_unit_fill_consistent": True,
                "broker_execution_provenance_complete": True,
                "effective_venue": "KRX",
                "market_session_bucket": "krx_regular",
                "broker_actual_execution_venue": "KRX",
                "broker_actual_execution_venue_source": "official_fid_919",
            },
            emitted_at="2026-08-04T10:02:00+09:00",
        ),
        _event(
            703,
            "333333",
            "winner-recovery-valid",
            "sell_completed",
            {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "profit_rate": "+0.70",
                "sell_price": 10100,
                "realized_pnl_krw": 139,
                "no_scale_in_counterfactual_profit_pct": 0.65,
                "scale_in_incremental_realized_delta_pct": 0.05,
                "sell_execution_receipt_economics_complete": True,
                "sell_execution_receipt_quantity_contract_complete": True,
                "sell_execution_receipt_unit_fill_consistent": True,
                "broker_execution_provenance_complete": True,
                "broker_actual_execution_venue": "NXT",
                "broker_actual_execution_venue_source": "official_fid_919",
            },
            emitted_at="2026-08-04T10:05:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-04", pipeline_path=pipeline_path, generated_at="fixed"
    )
    summary = report["summary"]["real_scale_in_performance"]
    row = report["real_scale_in_performance_rows"][0]
    expected_net_pnl = mod.calculate_net_realized_pnl(10000, 10100, 1)
    expected_ev = round(expected_net_pnl / 10000 * 100.0, 4)

    assert row["source_quality_valid"] is True
    assert row["source_quality_blockers"] == []
    assert row["scale_in_leg_net_pnl_proxy_krw"] == expected_net_pnl
    assert row["scale_in_leg_net_return_proxy_pct"] == expected_ev
    assert row["entry_effective_venue"] == "KRX"
    assert row["market_session_bucket"] == "krx_regular"
    assert row["scale_in_broker_actual_execution_venue"] == "KRX"
    assert row["sell_broker_actual_execution_venue"] == "NXT"
    assert row["scale_in_incremental_realized_delta_pct"] == 0.05
    assert summary["source_quality_adjusted_ev_available"] is True
    assert summary["source_quality_valid_closed_count"] == 1
    assert summary["source_quality_blocked_closed_count"] == 0
    assert summary["source_quality_adjusted_ev_pct"] == expected_ev
    assert summary["scale_in_leg_net_pnl_proxy_krw_sum"] == expected_net_pnl
    assert summary["scale_in_leg_diagnostic_win_rate"] == 1.0
    assert (
        summary["by_outcome_cohort"]["winner_recovery"][
            "source_quality_adjusted_ev_pct"
        ]
        == expected_ev
    )


def test_incomplete_real_scale_in_receipt_isolated_without_poisoning_report(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-08-20.jsonl"
    rows = [
        _event(
            704,
            "444444",
            "normal-pyramid-incomplete-receipt",
            "scale_in_executed",
            {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "P3",
                "fill_price": 10000,
                "fill_qty": 1,
                "add_type": "PYRAMID",
                "add_reason": "profit_pyramid",
                "new_avg_price": 9950,
                "new_buy_qty": 2,
            },
            emitted_at="2026-08-20T10:02:00+09:00",
        ),
        _event(
            704,
            "444444",
            "normal-pyramid-incomplete-receipt",
            "sell_completed",
            {"profit_rate": "+1.00", "sell_price": 10100},
            emitted_at="2026-08-20T10:05:00+09:00",
        ),
    ]
    pipeline_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )

    report = mod.build_report(
        "2026-08-20", pipeline_path=pipeline_path, generated_at="fixed"
    )
    row = report["real_scale_in_performance_rows"][0]

    assert row["closed"] is True
    assert row["source_quality_valid"] is False
    assert report["source_quality"]["status"] == "pass_with_row_exclusions"
    assert report["source_quality"]["source_quality_excluded_row_count"] == 1
    assert report["source_quality"]["source_quality_exclusion_reasons"] == {
        "real_scale_in_receipt_source_quality_incomplete": 1
    }
