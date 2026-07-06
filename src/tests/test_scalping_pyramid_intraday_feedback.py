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
        _event(101, "095500", "future", "stat_action_decision_snapshot", {"profit_rate": "+2.80"}),
        _event(101, "095500", "future", "sell_completed", {"profit_rate": "+2.35"}),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")
    item = report["pyramid_feedback_rows"][0]

    assert item["pyramid_feedback_label"] == "pyramid_would_have_helped"
    assert item["actual_order_submitted"] is False
    assert item["broker_order_forbidden"] is True
    assert item["runtime_effect"] is False
    assert item["decision_authority"] == "source_only_pyramid_intraday_feedback_no_runtime_mutation"
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
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")
    item = report["pyramid_feedback_rows"][0]

    assert item["current_ai_score"] == 50
    assert item["pyramid_feedback_label"] == "pyramid_overheat_or_reversal_risk"
    assert item["pyramid_feedback_label"] != "pyramid_would_have_helped"


def test_pyramid_intraday_feedback_blocks_source_quality_when_pressure_provenance_missing(tmp_path):
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
        _event(205, "111222", "missing-pressure-source", "sell_completed", {"profit_rate": "+2.40"}),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["source_quality"]["status"] == "pressure_provenance_missing"
    assert report["source_quality"]["pressure_provenance_missing_count"] == 1


def test_pyramid_intraday_feedback_blocks_source_quality_when_pressure_provenance_unusable(tmp_path):
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
        _event(206, "111333", "unusable-pressure-source", "sell_completed", {"profit_rate": "+2.40"}),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["source_quality"]["status"] == "pressure_provenance_unusable"
    assert report["source_quality"]["pressure_provenance_unusable_count"] == 1


def test_pyramid_intraday_feedback_blocks_source_quality_when_micro_vwap_provenance_missing(tmp_path):
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
        _event(207, "111444", "missing-micro-source", "sell_completed", {"profit_rate": "+2.40"}),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["source_quality"]["status"] == "micro_vwap_provenance_missing"
    assert report["source_quality"]["micro_vwap_provenance_missing_count"] == 1


def test_pyramid_intraday_feedback_blocks_source_quality_when_micro_vwap_provenance_unusable(tmp_path):
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
        _event(208, "111555", "stale-micro-source", "sell_completed", {"profit_rate": "+2.40"}),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

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
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")
    item = report["pyramid_feedback_rows"][0]

    assert item["actual_order_submitted"] is True
    assert item["broker_order_forbidden"] is False
    assert item["scale_in_blocker_reason"] == "pyramid_submitted"
    assert report["blocker_metrics"][0]["submitted_then_profit_rate"] == 1.0


def test_pyramid_intraday_feedback_backtests_all_one_share_events(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            401,
            "095500",
            "future",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry", "forced_entry_qty": 5},
        ),
        _event(401, "095500", "future", "stat_action_decision_snapshot", {"profit_rate": "+1.60"}),
        _event(401, "095500", "future", "stat_action_decision_snapshot", {"profit_rate": "+2.30"}),
        _event(401, "095500", "future", "sell_completed", {"profit_rate": "+1.90"}),
        _event(
            402,
            "222222",
            "flat",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry", "forced_entry_qty": 1},
        ),
        _event(402, "222222", "flat", "stat_action_decision_snapshot", {"profit_rate": "+0.40"}),
        _event(402, "222222", "flat", "sell_completed", {"profit_rate": "-0.10"}),
        _event(
            403,
            "333333",
            "runner",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry", "forced_entry_qty": 1},
        ),
        _event(403, "333333", "runner", "stat_action_decision_snapshot", {"profit_rate": "+1.70"}),
        _event(403, "333333", "runner", "stat_action_decision_snapshot", {"profit_rate": "+3.10"}),
        _event(403, "333333", "runner", "sell_completed", {"profit_rate": "+2.80"}),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")
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
    assert "intraday_threshold_mutation" in report["one_share_metric_contract"]["forbidden_uses"]


def test_pyramid_intraday_feedback_uses_runtime_min_profit_for_one_share_opportunity(tmp_path, monkeypatch):
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
            {"forced_entry_reason": "rising_missed_one_share_entry", "forced_entry_qty": 1},
        ),
        _event(501, "444444", "lower", "stat_action_decision_snapshot", {"profit_rate": "+1.30"}),
        _event(501, "444444", "lower", "sell_completed", {"profit_rate": "+1.80"}),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")
    item = report["one_share_pyramid_opportunity_rows"][0]

    assert item["pyramid_opportunity_seen"] is True
    assert item["pyramid_opportunity_min_profit_pct"] == 1.2
    assert item["pyramid_opportunity_profit_rate"] == 1.3
