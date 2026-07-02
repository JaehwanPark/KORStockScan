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
    }
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"

    mod.write_outputs(report, output_json=output_json, output_md=output_md)

    assert json.loads(output_json.read_text(encoding="utf-8"))["target_date"] == "2026-07-02"
    markdown = output_md.read_text(encoding="utf-8")
    assert "rising_missed_avg_down_ge2_count: 1" in markdown
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
