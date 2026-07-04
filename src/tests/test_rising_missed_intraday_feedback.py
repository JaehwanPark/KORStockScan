import json

from src.engine.monitoring import rising_missed_intraday_feedback as mod


def _event(
    record_id,
    code,
    name,
    stage,
    fields=None,
    emitted_at="2026-07-02T09:00:00",
    pipeline="ENTRY_PIPELINE",
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


def test_build_report_flags_rising_missed_avg_down_ge2_initial_quality_fail(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-02.jsonl"
    rows = [
        _event(
            101,
            "000101",
            "failer",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "scanner_promotion_reason": "price_jump_start_acceleration",
                "source_signature": "OPEN_TOP,PRICE_JUMP_START",
                "price_delta_since_first_seen_pct": "4.20",
            },
            emitted_at="2026-07-02T09:01:00",
        ),
        _event(
            101,
            "000101",
            "failer",
            "stat_action_decision_snapshot",
            {
                "avg_down_count": "1",
                "profit_rate": "-1.20",
                "peak_profit": "-0.20",
                "scale_in_gate_reason": "avg_down_candidate",
            },
            emitted_at="2026-07-02T09:05:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            101,
            "000101",
            "failer",
            "stat_action_decision_snapshot",
            {
                "avg_down_count": "2",
                "profit_rate": "-2.10",
                "peak_profit": "-0.20",
                "exit_rule_candidate": "scalp_soft_stop_pct",
                "sell_reason_type": "LOSS",
                "scale_in_gate_reason": "scale_in_cooldown",
            },
            emitted_at="2026-07-02T09:08:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            202,
            "000202",
            "normal",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
        ),
        _event(
            202,
            "000202",
            "normal",
            "stat_action_decision_snapshot",
            {"avg_down_count": "1", "profit_rate": "+0.40"},
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-02", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["summary"]["forced_rising_missed_record_count"] == 2
    assert report["summary"]["rising_missed_avg_down_ge2_count"] == 1
    assert report["summary"]["initial_quality_fail_count"] == 1
    record = report["records"][0]
    assert record["record_id"] == "101"
    assert record["feedback_label"] == "rising_missed_initial_quality_fail"
    assert record["max_avg_down_count"] == 2
    assert record["min_profit_seen"] == -2.1
    order = report["code_improvement_orders"][0]
    assert order["mapped_family"] == "rising_missed_initial_quality_feedback_loop"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert "intraday_runtime_apply" in order["forbidden_uses"]


def test_write_outputs_renders_json_and_markdown(tmp_path):
    report = {
        "target_date": "2026-07-02",
        "generated_at": "fixed",
        "summary": {
            "forced_rising_missed_record_count": 1,
            "holding_record_count": 1,
            "rising_missed_avg_down_ge2_count": 1,
            "initial_quality_fail_count": 1,
            "scale_in_rescue_warning_count": 0,
            "code_improvement_order_count": 1,
        },
        "records": [
            {
                "record_id": "101",
                "stock_code": "000101",
                "stock_name": "failer",
                "feedback_label": "rising_missed_initial_quality_fail",
                "max_avg_down_count": 2,
                "latest_profit_rate": -2.1,
                "min_profit_seen": -2.1,
                "max_profit_seen": -1.2,
                "latest_gate_reason": "scale_in_cooldown",
            }
        ],
        "first_touch_regression_rows": [
            {
                "record_id": "101",
                "stock_code": "000101",
                "stock_name": "failer",
                "first_touch_regression_label": "first_touch_loss_or_flat",
                "first_touch_avg_down_submitted": True,
                "first_touch_profit_rate": -3.1,
                "first_touch_peak_profit": -0.2,
                "first_touch_ai_score": 66.0,
                "final_profit_rate": -2.1,
                "avg_down_submitted_event_count": 2,
                "max_avg_down_count": 2,
                "blocker_counts_before_first_touch": {"blocked_strength_momentum": 1},
            }
        ],
    }
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"

    mod.write_outputs(report, output_json=output_json, output_md=output_md)

    assert json.loads(output_json.read_text(encoding="utf-8"))["target_date"] == "2026-07-02"
    markdown = output_md.read_text(encoding="utf-8")
    assert "rising_missed_avg_down_ge2_count: 1" in markdown
    assert "## First Touch Regression" in markdown
    assert "submitted_count=2" in markdown
    assert "shadow_cap1=-" in markdown
    assert "rising_missed_initial_quality_fail" in markdown


def test_profit_recovered_sell_order_is_rescue_warning_not_initial_fail(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-02.jsonl"
    rows = [
        _event(
            303,
            "000303",
            "recovered",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
        ),
        _event(
            303,
            "000303",
            "recovered",
            "stat_action_decision_snapshot",
            {"avg_down_count": "2", "profit_rate": "+0.80", "peak_profit": "+1.30"},
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            303,
            "000303",
            "recovered",
            "sell_order_sent",
            {
                "avg_down_count": "2",
                "profit_rate": "+1.10",
                "peak_profit": "+1.30",
                "exit_rule_candidate": "scalp_trailing_take_profit",
                "sell_reason_type": "PROFIT",
            },
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-02", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["summary"]["initial_quality_fail_count"] == 0
    assert report["summary"]["scale_in_rescue_warning_count"] == 1
    assert report["records"][0]["feedback_label"] == "rising_missed_scale_in_rescue_warning"


def test_build_report_adds_continuously_updated_first_touch_regression_rows(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            401,
            "000401",
            "winner",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "source_signature": "OPEN_TOP,PRICE_JUMP_START",
            },
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            401,
            "000401",
            "winner",
            "blocked_strength_momentum",
            {"block_reason": "below_strength_base"},
            emitted_at="2026-07-03T08:04:00",
        ),
        _event(
            401,
            "000401",
            "winner",
            "stop_line_touch_mandatory_avg_down_candidate",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "gate_reason": "ok",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            401,
            "000401",
            "winner",
            "stop_line_touch_mandatory_avg_down_submitted",
            {"profit_rate": "-3.42", "peak_profit": "-0.23", "current_ai_score": "65", "gate_reason": "ok"},
            emitted_at="2026-07-03T08:06:01",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            401,
            "000401",
            "winner",
            "sell_completed",
            {"profit_rate": "+1.09"},
            emitted_at="2026-07-03T08:07:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            402,
            "000402",
            "loser",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:10",
        ),
        _event(
            402,
            "000402",
            "loser",
            "blocked_strength_momentum",
            {"block_reason": "insufficient_history"},
            emitted_at="2026-07-03T08:04:10",
        ),
        _event(
            402,
            "000402",
            "loser",
            "stop_line_touch_mandatory_avg_down_candidate",
            {
                "profit_rate": "-3.33",
                "peak_profit": "-0.23",
                "current_ai_score": "67",
                "gate_reason": "ok",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
            },
            emitted_at="2026-07-03T08:17:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            402,
            "000402",
            "loser",
            "stop_line_touch_mandatory_avg_down_submitted",
            {"profit_rate": "-3.33", "peak_profit": "-0.23", "current_ai_score": "67", "gate_reason": "ok"},
            emitted_at="2026-07-03T08:17:01",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            402,
            "000402",
            "loser",
            "stop_line_touch_mandatory_avg_down_submitted",
            {"profit_rate": "-3.05", "peak_profit": "-0.23", "current_ai_score": "67", "gate_reason": "ok"},
            emitted_at="2026-07-03T08:31:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            402,
            "000402",
            "loser",
            "sell_completed",
            {"profit_rate": "-4.64"},
            emitted_at="2026-07-03T08:34:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            403,
            "000403",
            "blocked",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:20",
        ),
        _event(
            403,
            "000403",
            "blocked",
            "blocked_strength_momentum",
            {"block_reason": "below_strength_base"},
            emitted_at="2026-07-03T08:04:20",
        ),
        _event(
            403,
            "000403",
            "blocked",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.89",
                "peak_profit": "-0.10",
                "current_ai_score": "66",
                "gate_reason": "repeated_blockers_without_recovery",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "repeated_blockers_without_recovery",
                "first_touch_avgdown_support_signals": "quote_spread_present",
                "first_touch_avgdown_risk_signals": "repeated_blockers_without_support",
                "first_touch_avgdown_repeated_blocker_count": 11,
                "first_touch_avgdown_decision_authority": "real_scalping_first_touch_avgdown_decision_gate",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
            },
            emitted_at="2026-07-03T08:20:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["summary"]["first_touch_regression_record_count"] == 3
    assert report["summary"]["first_touch_avg_down_submitted_count"] == 2
    assert report["summary"]["first_touch_avgdown_decision_blocked_count"] == 1
    assert report["summary"]["first_touch_closed_count"] == 2
    assert report["summary"]["first_touch_profitable_count"] == 1
    assert report["summary"]["first_touch_loss_or_flat_count"] == 1
    rows_by_record = {row["record_id"]: row for row in report["first_touch_regression_rows"]}
    assert rows_by_record["401"]["first_touch_regression_label"] == "first_touch_recovered_profit"
    assert rows_by_record["401"]["blocker_counts_before_first_touch"] == {"blocked_strength_momentum": 1}
    assert rows_by_record["401"]["first_touch_shadow_cap1_decision"] == "cap1_first_avg_down_allowed"
    assert rows_by_record["402"]["first_touch_regression_label"] == "first_touch_loss_or_flat"
    assert rows_by_record["402"]["avg_down_submitted_event_count"] == 2
    assert rows_by_record["402"]["first_touch_shadow_cap1_decision"] == "cap1_extra_avg_down_would_block"
    assert "cap1_extra_avg_down_would_block" in rows_by_record["402"]["first_touch_shadow_risk_signals"]
    assert rows_by_record["403"]["first_touch_regression_label"] == "first_touch_open_unresolved"
    assert rows_by_record["403"]["first_touch_avgdown_decision_blocked"] is True
    assert rows_by_record["403"]["first_touch_avgdown_decision_allowed"] is False
    assert rows_by_record["403"]["actual_order_submitted"] is False
    assert rows_by_record["403"]["broker_order_forbidden"] is True
    assert rows_by_record["403"]["first_touch_avgdown_decision_reason"] == "repeated_blockers_without_recovery"
    assert rows_by_record["403"]["first_touch_avgdown_decision_authority"] == (
        "real_scalping_first_touch_avgdown_decision_gate"
    )
    assert (
        report["metric_contracts"]["rising_missed_first_touch_regression"]["decision_authority"]
        == "source_only_first_touch_regression_table"
    )
    assert report["source_quality"]["status"] == "pass"


def test_first_touch_regression_blocks_source_quality_when_ai_provenance_missing(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            501,
            "000501",
            "missing-ai-provenance",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            501,
            "000501",
            "missing-ai-provenance",
            "stop_line_touch_mandatory_avg_down_candidate",
            {"profit_rate": "-3.42", "peak_profit": "-0.23", "current_ai_score": "65", "gate_reason": "ok"},
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["source_quality"]["status"] == "first_touch_ai_provenance_missing"
    assert report["summary"]["first_touch_ai_provenance_missing_count"] == 1


def test_first_touch_regression_accepts_runtime_usable_holding_ai_not_called_score(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            505,
            "000505",
            "usable-prior-score",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            505,
            "000505",
            "usable-prior-score",
            "stop_line_touch_mandatory_avg_down_candidate",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "gate_reason": "ok",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "holding_ai_not_called",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["source_quality"]["status"] == "pass"
    assert report["summary"]["first_touch_ai_provenance_unusable_count"] == 0


def test_first_touch_regression_blocks_source_quality_when_micro_provenance_unusable(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            502,
            "000502",
            "stale-micro",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            502,
            "000502",
            "stale-micro",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "gate_reason": "micro_context_stale_ignored",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "insufficient_first_touch_recovery_confirmation",
                "first_touch_avgdown_support_signals": "buy_pressure_support",
                "first_touch_avgdown_risk_signals": "micro_context_stale_ignored",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
                "first_touch_reversal_feature_source_quality": "stale",
                "first_touch_reversal_feature_stale": True,
                "first_touch_reversal_feature_stale_reason": "micro_vwap_unavailable",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["source_quality"]["status"] == "first_touch_micro_provenance_unusable"
    assert report["summary"]["first_touch_micro_provenance_unusable_count"] == 1


def test_first_touch_regression_blocks_source_quality_when_pressure_provenance_missing(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            503,
            "000503",
            "missing-pressure",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            503,
            "000503",
            "missing-pressure",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "insufficient_first_touch_recovery_confirmation",
                "first_touch_avgdown_support_signals": "buy_pressure_support|tick_accel_support",
                "first_touch_avgdown_risk_signals": "",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
                "first_touch_reversal_feature_source_quality": "usable",
                "first_touch_reversal_feature_stale": False,
                "buy_pressure_10t": "78.0",
                "tick_acceleration_ratio": "1.25",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["source_quality"]["status"] == "first_touch_pressure_provenance_missing"
    assert report["summary"]["first_touch_pressure_provenance_missing_count"] == 1


def test_first_touch_regression_blocks_source_quality_when_micro_vwap_provenance_missing(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-03.jsonl"
    rows = [
        _event(
            504,
            "000504",
            "missing-minute",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-03T08:03:00",
        ),
        _event(
            504,
            "000504",
            "missing-minute",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.42",
                "peak_profit": "-0.23",
                "current_ai_score": "65",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "insufficient_first_touch_recovery_confirmation",
                "first_touch_avgdown_support_signals": "micro_vwap_non_negative",
                "first_touch_avgdown_risk_signals": "",
                "first_touch_avgdown_ai_score_usable": True,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "fresh",
                "first_touch_reversal_feature_source_quality": "usable",
                "first_touch_reversal_feature_stale": False,
                "curr_vs_micro_vwap_bp": "12.0",
            },
            emitted_at="2026-07-03T08:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-03", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["source_quality"]["status"] == "first_touch_micro_provenance_missing"
    assert report["summary"]["first_touch_micro_provenance_missing_count"] == 1
