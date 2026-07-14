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


def test_tp1_first_hit_label_prefers_gross_target_and_requires_actual_costs_for_net(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            701,
            "000701",
            "tp1",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "rising_missed_tp1_candidate_lane": "low_rebound",
                "current_price_observed": 10000,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            701,
            "000701",
            "tp1",
            "holding_observation",
            {"current_price_observed": 10140},
            emitted_at="2026-07-14T09:05:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-14", pipeline_path=pipeline_path, generated_at="fixed")

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == "gross_target_first"
    assert label["first_hit_move_pct"] == 1.4
    assert label["net_label"] == "unavailable_fee_tax_missing"
    assert report["summary"]["rising_missed_tp1_net_confirmed_count"] == 0


def test_tp1_first_hit_label_marks_adverse_first_and_can_confirm_net_with_costs(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            702,
            "000702",
            "adverse",
            "rising_missed_tp1_candidate_blocked",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "current_price_observed": 10000,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            702,
            "000702",
            "adverse",
            "holding_observation",
            {"current_price_observed": 9920},
            emitted_at="2026-07-14T09:02:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            703,
            "000703",
            "net",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "current_price_observed": 10000,
                "actual_fee_krw": 10,
                "actual_tax_krw": 10,
            },
            emitted_at="2026-07-14T09:10:00+09:00",
        ),
        _event(
            703,
            "000703",
            "net",
            "holding_observation",
            {"current_price_observed": 10130},
            emitted_at="2026-07-14T09:15:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-14", pipeline_path=pipeline_path, generated_at="fixed")
    labels = {row["stock_code"]: row for row in report["rising_missed_tp1_first_hit_label_rows"]}

    assert labels["000702"]["gross_first_hit_label"] == "adverse_stop_first"
    assert labels["000702"]["net_label"] == "unavailable_fee_tax_missing"
    assert labels["000703"]["gross_first_hit_label"] == "gross_target_first"
    assert labels["000703"]["actual_cost_pct"] == 0.2
    assert labels["000703"]["net_label"] == "net_target_confirmed"


def test_tp1_first_hit_label_accepts_explicit_zero_costs_without_closing_pending_horizon(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            704,
            "000704",
            "pending",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "current_price_observed": 10000,
                "actual_fee_krw": 0,
                "actual_tax_krw": 0,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            704,
            "000704",
            "pending",
            "holding_observation",
            {"current_price_observed": 10020},
            emitted_at="2026-07-14T09:05:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-14", pipeline_path=pipeline_path, generated_at="fixed")

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["gross_first_hit_label"] == "pending_horizon"
    assert label["actual_cost_pct"] == 0.0
    assert label["net_label"] == "pending_horizon"


def test_tp1_first_hit_label_uses_effective_price_and_later_cost_only_event(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            705,
            "000705",
            "bridge",
            "rising_missed_normal_buy_bridge_unlocked",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "rising_missed_tp1_effective_price": 10000,
                "current_price_observed": 9000,
                "quantity": 1,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            705,
            "000705",
            "bridge",
            "holding_observation",
            {
                "current_price_observed": 10130,
                "rising_missed_tp1_effective_price": 10000,
            },
            emitted_at="2026-07-14T09:05:00+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            705,
            "000705",
            "bridge",
            "execution_cost_observation",
            {"actual_fee_krw": 10, "actual_tax_krw": 10},
            emitted_at="2026-07-14T09:08:00+09:00",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-14", pipeline_path=pipeline_path, generated_at="fixed")

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["entry_price"] == 10000.0
    assert label["entry_price_source"] == "rising_missed_tp1_effective_price"
    assert label["gross_first_hit_label"] == "gross_target_first"
    assert label["actual_cost_pct"] == 0.2
    assert label["net_label"] == "net_target_confirmed"


def test_tp1_labels_prefer_effective_candidate_and_fresh_submit_mark_over_stale_scanner_price(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            706,
            "000706",
            "pass",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "rising_missed_tp1_evaluation_id": "pass-eval",
                "rising_missed_tp1_effective_price": 10000,
                "current_price_observed": 9000,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            706,
            "000706",
            "pass",
            "real_weak_ai_micro_entry_block",
            {"current_price_observed": 9000, "mark_price_at_submit": 10140},
            emitted_at="2026-07-14T09:01:00+09:00",
        ),
        _event(
            806,
            "000806",
            "counterfactual",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "selector_reason": "rising_missed_tp1_lane_not_eligible",
                "selector_deferred": False,
                "rising_missed_tp1_candidate_allowed": False,
                "rising_missed_tp1_evaluation_id": "counterfactual-eval",
                "rising_missed_tp1_effective_price": 20000,
                "current_price_observed": 18000,
                "rising_missed_tp1_counterfactual_submit_safety_action": "RECHECK_REQUIRED",
                "rising_missed_tp1_counterfactual_submit_safety_risks": "momentum_support_weak",
            },
            emitted_at="2026-07-14T09:02:00+09:00",
        ),
        _event(
            806,
            "000806",
            "counterfactual",
            "scalping_scanner_promotion_latency_trace",
            {"current_price_observed": 20300, "ws_last_0d_age_ms": 100},
            emitted_at="2026-07-14T09:03:00+09:00",
        ),
        _event(
            806,
            "000806",
            "counterfactual",
            "scalping_scanner_watching_runtime_skip",
            {"current_price_observed": 20280, "ws_last_0b_age_ms": 100},
            emitted_at="2026-07-14T09:04:00+09:00",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-14", pipeline_path=pipeline_path, generated_at="fixed")

    pass_label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert pass_label["entry_price"] == 10000.0
    assert pass_label["entry_price_source"] == "rising_missed_tp1_effective_price"
    assert pass_label["gross_first_hit_label"] == "gross_target_first"
    counterfactual_label = report[
        "rising_missed_tp1_counterfactual_first_hit_label_rows"
    ][0]
    assert counterfactual_label["entry_price"] == 20000.0
    assert counterfactual_label["entry_price_source"] == "rising_missed_tp1_effective_price"
    assert counterfactual_label["gross_first_hit_label"] == "gross_target_first"
    assert counterfactual_label["first_hit_ts"] == "2026-07-14T09:04:00+09:00"
    assert report["summary"]["rising_missed_tp1_counterfactual_gross_target_first_count"] == 1
    assert counterfactual_label["actual_order_submitted"] is False
    assert counterfactual_label["broker_order_forbidden"] is True


def test_tp1_label_ignores_unfresh_decision_stage_current_price_before_submit_mark(
    tmp_path,
):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            707,
            "000707",
            "stale-decision-price",
            "rising_missed_one_share_entry",
            {
                "rising_missed_tp1_selector_active": True,
                "rising_missed_tp1_candidate_allowed": True,
                "rising_missed_tp1_candidate_reason": "rising_missed_tp1_candidate_pass",
                "rising_missed_tp1_evaluation_id": "stale-decision-price-eval",
                "rising_missed_tp1_effective_price": 10000,
                "current_price_observed": 11000,
            },
            emitted_at="2026-07-14T09:00:00+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "budget_pass",
            {"current_price_observed": 11000},
            emitted_at="2026-07-14T09:00:01+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "orderbook_stability_observed",
            {"current_price_observed": 11000},
            emitted_at="2026-07-14T09:00:02+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "latency_block",
            {
                "current_price_observed": 11000,
                "pre_submit_ws_snapshot_refresh_latest_price": 10050,
                "rising_missed_submit_safety_backoff_lineage": True,
                "reason": "latency_state_danger",
            },
            emitted_at="2026-07-14T09:00:03+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "budget_pass",
            {"current_price_observed": 11000},
            emitted_at="2026-07-14T09:00:04+09:00",
        ),
        _event(
            707,
            "000707",
            "stale-decision-price",
            "holding_observation",
            {"current_price_observed": 10040},
            emitted_at="2026-07-14T09:00:05+09:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-14", pipeline_path=pipeline_path, generated_at="fixed")

    label = report["rising_missed_tp1_first_hit_label_rows"][0]
    assert label["entry_price"] == 10000.0
    assert label["gross_first_hit_label"] == "pending_horizon"
    assert label["max_move_pct_within_20m"] == 0.5
    assert label["observed_price_event_count"] == 3
    blocker = report["submit_safety_blocker_rows"][0]
    assert blocker["block_price"] == 10050.0
    assert blocker["mfe_after_block_pct"] == -0.0995
    assert blocker["mae_after_block_pct"] == -0.0995
    assert blocker["post_block_price_event_count"] == 1


def test_tp1_counterfactual_submit_safety_is_aggregated_without_label_duplication(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-14.jsonl"
    rows = [
        _event(
            801,
            "000801",
            "recheck",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "selector_reason": "rising_missed_tp1_insufficient_positive_support",
                "selector_deferred": False,
                "rising_missed_tp1_candidate_allowed": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": "RECHECK_REQUIRED",
                "rising_missed_tp1_counterfactual_submit_safety_risks": (
                    "spread_above_candidate_caution,momentum_support_weak"
                ),
                "rising_missed_tp1_positive_support_count": 1,
                "rising_missed_tp1_positive_support_families": "depth",
            },
        ),
        _event(
            802,
            "000802",
            "defer",
            "rising_missed_tp1_counterfactual_submit_safety",
            {
                "selector_reason": "tp1_effective_quote_stale",
                "selector_deferred": True,
                "rising_missed_tp1_candidate_allowed": False,
                "rising_missed_tp1_counterfactual_submit_safety_action": (
                    "INPUT_DEFER_EXPECTED"
                ),
                "rising_missed_tp1_counterfactual_submit_safety_risks": "-",
                "rising_missed_tp1_positive_support_count": 0,
                "rising_missed_tp1_positive_support_families": "-",
            },
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-14", pipeline_path=pipeline_path, generated_at="fixed")
    summary = report["summary"]

    assert summary["rising_missed_tp1_counterfactual_submit_safety_count"] == 2
    assert summary["rising_missed_tp1_counterfactual_unique_symbol_count"] == 2
    assert summary["rising_missed_tp1_counterfactual_action_counts"] == [
        {"action": "RECHECK_REQUIRED", "count": 1},
        {"action": "INPUT_DEFER_EXPECTED", "count": 1},
    ]
    assert summary["rising_missed_tp1_counterfactual_risk_counts"] == [
        {"risk": "spread_above_candidate_caution", "count": 1},
        {"risk": "momentum_support_weak", "count": 1},
    ]
    assert report["rising_missed_tp1_first_hit_label_rows"] == []
    assert all(
        row["actual_order_submitted"] is False
        and row["broker_order_forbidden"] is True
        and row["runtime_effect"] is False
        for row in report["rising_missed_tp1_counterfactual_submit_safety_rows"]
    )


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
            "first_touch_entry_submitted_count": 1,
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
                "entry_order_submitted": True,
                "entry_order_submitted_count": 1,
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
    assert "entry_submitted=True" in markdown
    assert "entry_submit_count=1" in markdown
    assert "avgdown_submitted_count=2" in markdown
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
    assert report["summary"]["first_touch_entry_submitted_count"] == 0
    assert report["summary"]["first_touch_avg_down_submitted_count"] == 2
    assert report["summary"]["first_touch_avgdown_decision_blocked_count"] == 1
    assert report["summary"]["first_touch_closed_count"] == 2
    assert report["summary"]["first_touch_profitable_count"] == 1
    assert report["summary"]["first_touch_loss_or_flat_count"] == 1
    rows_by_record = {row["record_id"]: row for row in report["first_touch_regression_rows"]}
    assert rows_by_record["401"]["first_touch_regression_label"] == "first_touch_recovered_profit"
    assert rows_by_record["401"]["entry_order_submitted"] is False
    assert rows_by_record["401"]["entry_order_submitted_count"] == 0
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


def test_build_report_captures_real_entry_submit_separately_from_first_touch_avgdown_submit(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-08.jsonl"
    rows = [
        _event(
            601,
            "000601",
            "real-entry-only",
            "rising_missed_one_share_entry",
            {"forced_entry_reason": "rising_missed_one_share_entry"},
            emitted_at="2026-07-08T10:00:00",
        ),
        _event(
            601,
            "000601",
            "real-entry-only",
            "order_bundle_submitted",
            {"actual_order_submitted": True, "broker_order_forbidden": False},
            emitted_at="2026-07-08T10:00:05",
        ),
        _event(
            601,
            "000601",
            "real-entry-only",
            "holding_started",
            {"actual_order_submitted": True, "buy_price": "1000", "buy_qty": "1"},
            emitted_at="2026-07-08T10:00:10",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            601,
            "000601",
            "real-entry-only",
            "stop_line_touch_first_touch_avgdown_decision_blocked",
            {
                "profit_rate": "-3.10",
                "peak_profit": "0.10",
                "current_ai_score": "57",
                "first_touch_avgdown_decision_allowed": False,
                "first_touch_avgdown_decision_reason": "ai_score_no_submit_authority",
                "first_touch_avgdown_ai_score_usable": False,
                "first_touch_avgdown_ai_score_source": "live",
                "first_touch_avgdown_ai_score_data_quality": "partial",
                "first_touch_reversal_feature_source_quality": "usable",
                "first_touch_reversal_feature_stale": False,
            },
            emitted_at="2026-07-08T10:05:00",
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            601,
            "000601",
            "real-entry-only",
            "sell_completed",
            {"profit_rate": "-3.14"},
            emitted_at="2026-07-08T10:06:00",
            pipeline="HOLDING_PIPELINE",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-08", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["summary"]["first_touch_entry_submitted_count"] == 1
    row = report["first_touch_regression_rows"][0]
    assert row["entry_order_submitted"] is True
    assert row["entry_order_submitted_count"] == 1
    assert row["entry_fill_seen"] is True
    assert row["entry_fill_seen_count"] == 1
    assert row["first_touch_avg_down_submitted"] is False
    assert row["avg_down_submitted_event_count"] == 0
    assert report["summary"]["rising_missed_submit_lineage_record_count"] == 1
    assert report["summary"]["rising_missed_entry_submitted_count"] == 1
    assert report["summary"]["rising_missed_order_bundle_submitted_count"] == 1
    submit_row = report["rising_missed_submit_lineage_rows"][0]
    assert submit_row["entry_order_submitted"] is True
    assert submit_row["order_bundle_submitted_count"] == 1
    assert submit_row["submit_lineage_join_method"] == "record_id"


def test_build_report_joins_forced_plan_to_submit_by_code_time_when_lineage_fields_missing(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-10.jsonl"
    rows = [
        _event(
            701,
            "000701",
            "lineage-missing",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            },
            emitted_at="2026-07-10T10:00:00",
        ),
        _event(
            701,
            "000701",
            "lineage-missing",
            "rising_missed_one_share_entry_order_plan_forced",
            {
                "planned_order_price": "170100",
                "forced_entry_qty": "1",
            },
            emitted_at="2026-07-10T10:00:02",
        ),
        _event(
            999,
            "000701",
            "lineage-missing",
            "order_leg_sent",
            {
                "order_no": "0027316",
                "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            },
            emitted_at="2026-07-10T10:00:05",
        ),
        _event(
            999,
            "000701",
            "lineage-missing",
            "order_bundle_submitted",
            {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "0027316",
                "order_price": "170100",
                "source_signature": "OPEN_TOP,REALTIME_RANK_START,VALUE_TOP",
            },
            emitted_at="2026-07-10T10:00:08",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-10", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["summary"]["rising_missed_submit_lineage_record_count"] == 1
    assert report["summary"]["rising_missed_order_plan_forced_count"] == 1
    assert report["summary"]["rising_missed_entry_submitted_count"] == 1
    assert report["summary"]["rising_missed_order_leg_sent_count"] == 1
    row = report["rising_missed_submit_lineage_rows"][0]
    assert row["record_id"] == "701"
    assert row["submit_lineage_join_method"] == "code_time_window"
    assert row["primary_order_no"] == "0027316"
    assert row["submitted_order_price"] == "170100"
    assert row["actual_order_submitted"] is False
    assert row["broker_order_forbidden"] is True
    assert row["decision_authority"] == "source_only_rising_missed_submit_lineage"


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


def test_submit_safety_breakdown_and_backoff_opportunity_audit_are_source_only(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-10.jsonl"
    rows = [
        _event(
            701,
            "000701",
            "stale-ai-wait",
            "rising_missed_scout_quality_guard_blocked",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "block_reason": "stale_quote_with_weak_ai_or_strength",
                "current_price": "1000",
                "price_delta_since_first_seen_pct": "1.20",
                "rising_missed_scout_quality_guard_quote_age_ms": "4500",
                "rising_missed_scout_quality_guard_max_quote_age_ms": "3000",
                "rising_missed_scout_quality_guard_quote_stale": True,
                "rising_missed_scout_quality_guard_weak_evidence": True,
                "rising_missed_scout_quality_guard_ai_action": "WAIT",
                "rising_missed_scout_quality_guard_ai_score": "58",
                "pre_submit_rest_orderbook_refresh_enabled": True,
                "pre_submit_rest_orderbook_refresh_applied": True,
                "pre_submit_rest_orderbook_refresh_reason": "rest_orderbook_fresh",
                "rising_missed_rest_quote_ai_recheck_attempted": True,
                "rising_missed_rest_quote_ai_recheck_success": True,
            },
            emitted_at="2026-07-10T09:00:00",
        ),
        _event(
            701,
            "000701",
            "stale-ai-wait",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "1030",
                "price_delta_since_first_seen_pct": "2.00",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:01:00",
        ),
        _event(
            706,
            "000706",
            "stale-ai-missing",
            "rising_missed_scout_quality_guard_blocked",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "block_reason": "stale_quote_with_missing_ai_provenance",
                "current_price": "1500",
                "price_delta_since_first_seen_pct": "1.50",
                "rising_missed_scout_quality_guard_quote_age_ms": "6000",
                "rising_missed_scout_quality_guard_max_quote_age_ms": "3000",
                "rising_missed_scout_quality_guard_quote_stale": True,
                "rising_missed_scout_quality_guard_weak_evidence": False,
                "rising_missed_scout_quality_guard_weak_ai": False,
                "rising_missed_scout_quality_guard_ai_action": "-",
                "rising_missed_scout_quality_guard_ai_score": "50.0",
                "rising_missed_scout_quality_guard_ai_provenance_missing": True,
                "rising_missed_scout_quality_guard_ai_score_defaulted_without_action": True,
            },
            emitted_at="2026-07-10T09:01:30",
        ),
        _event(
            706,
            "000706",
            "stale-ai-missing",
            "scalping_scanner_candidate_observed",
            {
                "current_price": "1530",
                "price_delta_since_first_seen_pct": "2.10",
                "ws_last_0b_age_ms": "100",
            },
            emitted_at="2026-07-10T09:01:45",
        ),
        _event(
            702,
            "000702",
            "true-ofi-block",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "2000",
                "price_delta_since_first_seen_pct": "2.50",
                "ws_age_ms": "40",
                "spread_ratio": "0.007",
                "latency_danger_detail_reason": "spread_above_caution_below_guard_cap",
                "latency_spread_block_spread_bps": "70.0",
                "latency_spread_relief_micro_estimator_reason": "true_ofi_below_floor",
                "latency_spread_relief_micro_estimator_true_ofi_ewma": "-0.12",
                "latency_spread_relief_micro_estimator_true_ofi_sample_count": "120",
            },
            emitted_at="2026-07-10T09:02:00",
        ),
        _event(
            703,
            "000703",
            "ignored-normal",
            "latency_block",
            {"reason": "latency_state_danger", "current_price": "3000"},
            emitted_at="2026-07-10T09:02:30",
        ),
        _event(
            704,
            "000704",
            "recovered",
            "scalping_scanner_fast_precheck",
            {
                "fast_precheck_result": "budget_reallocated",
                "fast_precheck_reason": "scanner_ws_stale_backoff_active",
                "scanner_budget_reallocation_source": "ws_stale_feedback",
                "price_delta_since_first_seen_pct": "1.00",
                "scanner_rising_missed_source_marker_present": True,
            },
            emitted_at="2026-07-10T09:03:00",
        ),
        _event(
            704,
            "000704",
            "recovered",
            "scalping_scanner_fast_precheck",
            {
                "fast_precheck_result": "eligible_for_heavy_entry_eval",
                "fast_precheck_reason": "fast_precheck_pass",
                "price_delta_since_first_seen_pct": "1.40",
            },
            emitted_at="2026-07-10T09:04:00",
        ),
        _event(
            705,
            "000705",
            "not-recovered",
            "scalping_scanner_fast_precheck",
            {
                "fast_precheck_result": "budget_reallocated",
                "fast_precheck_reason": "submit_safety_backoff_active",
                "rising_missed_budget_reallocation_source": "submit_safety_feedback",
                "price_delta_since_first_seen_pct": "1.10",
                "scanner_rising_missed_source_marker_present": True,
            },
            emitted_at="2026-07-10T09:05:00",
        ),
        _event(
            705,
            "000705",
            "not-recovered",
            "scalping_scanner_watching_runtime_skip",
            {"price_delta_since_first_seen_pct": "2.20"},
            emitted_at="2026-07-10T09:06:00",
        ),
        _event(
            799,
            "000799",
            "clock-anchor",
            "scalping_scanner_runtime_target_attach",
            {"price_delta_since_first_seen_pct": "0.00"},
            emitted_at="2026-07-10T09:09:00",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-10", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["summary"]["submit_safety_block_count"] == 3
    assert report["summary"]["potential_backoff_opportunity_loss_count"] == 1
    bucket_counts = {
        item["blocker_bucket"]: item["count"] for item in report["summary"]["submit_safety_bucket_counts"]
    }
    assert bucket_counts == {
        "ai_wait_after_refresh": 1,
        "latency_true_ofi_below_floor": 1,
        "missing_ai_or_fresh_input": 1,
    }
    stale_row = report["submit_safety_blocker_rows"][0]
    assert stale_row["reason"] == "stale_quote_with_weak_ai_or_strength"
    assert stale_row["quote_age_sec"] == 4.5
    assert stale_row["mfe_after_block_pct"] == 3.0
    assert stale_row["runtime_effect"] is False
    missing_ai_row = report["submit_safety_blocker_rows"][1]
    assert missing_ai_row["reason"] == "stale_quote_with_missing_ai_provenance"
    assert missing_ai_row["blocker_bucket"] == "missing_ai_or_fresh_input"
    assert "ai_provenance_missing" in missing_ai_row["components"]
    assert "weak_ai_score" not in missing_ai_row["components"]
    latency_row = report["submit_safety_blocker_rows"][2]
    assert latency_row["true_ofi_reason"] == "true_ofi_below_floor"
    assert latency_row["spread_bps"] == 70.0
    backoff_rows = {item["stock_code"]: item for item in report["backoff_opportunity_audit_rows"]}
    assert backoff_rows["000704"]["recovered_eval_after_last_backoff"] is True
    assert backoff_rows["000705"]["potential_backoff_opportunity_loss"] is True
    assert backoff_rows["000705"]["backoff_observation_state"] == "mature_unrecovered"
    assert report["summary"]["backoff_active_positive_delta_symbol_count"] == 0
    assert (
        report["metric_contracts"]["rising_missed_submit_safety_blocker_breakdown"]["decision_authority"]
        == "source_only_submit_safety_blocker_attribution"
    )


def test_latency_false_negative_review_selects_only_high_mfe_low_mae_latency_blocks(tmp_path):
    pipeline_path = tmp_path / "pipeline_events_2026-07-10.jsonl"
    rows = [
        _event(
            801,
            "000801",
            "true-ofi-candidate",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "1000",
                "ws_age_ms": "80",
                "latency_danger_detail_reason": "spread_above_caution_below_guard_cap",
                "latency_spread_block_spread_bps": "62.0",
                "latency_spread_relief_micro_estimator_reason": "true_ofi_below_floor",
                "latency_spread_relief_micro_estimator_true_ofi_ewma": "-0.04",
                "latency_spread_relief_micro_estimator_true_ofi_sample_count": "120",
            },
            emitted_at="2026-07-10T09:10:00",
        ),
        _event(
            801,
            "000801",
            "true-ofi-candidate",
            "scalping_scanner_candidate_observed",
            {"current_price": "990", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:10:20",
        ),
        _event(
            801,
            "000801",
            "true-ofi-candidate",
            "scalping_scanner_candidate_observed",
            {"current_price": "1045", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:10:40",
        ),
        _event(
            802,
            "000802",
            "spread-candidate",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "2000",
                "ws_age_ms": "70",
                "latency_danger_detail_reason": "spread_above_caution",
                "latency_spread_block_spread_bps": "55.0",
            },
            emitted_at="2026-07-10T09:11:00",
        ),
        _event(
            802,
            "000802",
            "spread-candidate",
            "scalping_scanner_candidate_observed",
            {"current_price": "1980", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:11:20",
        ),
        _event(
            802,
            "000802",
            "spread-candidate",
            "scalping_scanner_candidate_observed",
            {"current_price": "2070", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:11:40",
        ),
        _event(
            803,
            "000803",
            "wide-mae",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "3000",
                "latency_danger_detail_reason": "spread_above_caution",
                "latency_spread_block_spread_bps": "58.0",
            },
            emitted_at="2026-07-10T09:12:00",
        ),
        _event(
            803,
            "000803",
            "wide-mae",
            "scalping_scanner_candidate_observed",
            {"current_price": "2910", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:12:20",
        ),
        _event(
            803,
            "000803",
            "wide-mae",
            "scalping_scanner_candidate_observed",
            {"current_price": "3120", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:12:40",
        ),
        _event(
            804,
            "000804",
            "stale-not-latency",
            "rising_missed_scout_quality_guard_blocked",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "block_reason": "stale_quote_with_weak_ai_or_strength",
                "current_price": "1000",
                "rising_missed_scout_quality_guard_quote_age_ms": "5000",
                "rising_missed_scout_quality_guard_ai_action": "WAIT",
            },
            emitted_at="2026-07-10T09:13:00",
        ),
        _event(
            804,
            "000804",
            "stale-not-latency",
            "scalping_scanner_candidate_observed",
            {"current_price": "1100", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:13:20",
        ),
        _event(
            805,
            "000805",
            "wide-spread-observe",
            "latency_block",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "reason": "latency_state_danger",
                "current_price": "4000",
                "ws_age_ms": "80",
                "latency_danger_detail_reason": "spread_above_caution",
                "latency_spread_block_spread_bps": "130.0",
            },
            emitted_at="2026-07-10T09:14:00",
        ),
        _event(
            805,
            "000805",
            "wide-spread-observe",
            "scalping_scanner_candidate_observed",
            {"current_price": "4000", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:14:10",
        ),
        _event(
            805,
            "000805",
            "wide-spread-observe",
            "scalping_scanner_candidate_observed",
            {"current_price": "4160", "ws_last_0b_age_ms": "100"},
            emitted_at="2026-07-10T09:14:20",
        ),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    report = mod.build_report("2026-07-10", pipeline_path=pipeline_path, generated_at="fixed")

    assert report["summary"]["latency_false_negative_review_count"] == 3
    assert report["summary"]["latency_false_negative_true_ofi_count"] == 1
    assert report["summary"]["latency_false_negative_spread_only_count"] == 2
    rows_by_code = {item["stock_code"]: item for item in report["latency_false_negative_review_rows"]}
    assert set(rows_by_code) == {"000801", "000802", "000805"}
    assert rows_by_code["000801"]["review_bucket"] == "true_ofi_false_negative_candidate"
    assert rows_by_code["000801"]["mfe_after_block_pct"] == 4.5
    assert rows_by_code["000801"]["mae_after_block_pct"] == -1.0
    assert rows_by_code["000802"]["review_bucket"] == "spread_caution_false_negative_candidate"
    assert rows_by_code["000802"]["mfe_after_block_pct"] == 3.5
    assert rows_by_code["000802"]["mae_after_block_pct"] == -1.0
    assert rows_by_code["000801"]["runtime_effect"] is False
    assert rows_by_code["000801"]["allowed_runtime_apply"] is False
    assert (
        report["metric_contracts"]["rising_missed_latency_false_negative_review"]["decision_authority"]
        == "source_only_latency_false_negative_review"
    )
    canary_rows_by_code = {
        item["stock_code"]: item for item in report["latency_false_negative_canary_candidate_rows"]
    }
    assert canary_rows_by_code["000801"]["canary_cohort"] == "true_ofi_near_zero_false_negative"
    assert canary_rows_by_code["000801"]["canary_grade"] == "ready_for_recheck"
    assert canary_rows_by_code["000801"]["canary_primary_review_score_pct"] == 3.5
    assert canary_rows_by_code["000802"]["canary_cohort"] == "spread_only_false_negative"
    assert canary_rows_by_code["000802"]["canary_grade"] == "ready_for_recheck"
    assert canary_rows_by_code["000805"]["canary_grade"] == "observe_wide_spread"
    assert report["summary"]["latency_false_negative_canary_candidate_count"] == 3
    assert report["summary"]["latency_false_negative_canary_ready_count"] == 2
    assert report["summary"]["latency_false_negative_canary_observe_wide_spread_count"] == 1
    assert (
        report["metric_contracts"]["rising_missed_latency_false_negative_canary_candidate"]["decision_authority"]
        == "source_only_latency_false_negative_canary_candidate"
    )
