import json
from pathlib import Path

from src.engine.monitoring import rising_missed_scout_workorder as mod


def _event(
    record_id,
    code,
    name,
    stage,
    fields=None,
    emitted_at="2026-07-01T09:00:00",
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


def test_build_report_joins_forced_scout_post_sell_and_creates_workorders(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    post_sell_path = tmp_path / "post_sell.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    pipeline_rows = [
        _event(
            1,
            "000001",
            "winner",
            "rising_missed_one_share_entry",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "scanner_promotion_reason": "price_jump_start_acceleration",
                "source_signature": "OPEN_TOP,PRICE_JUMP_START,VALUE_TOP",
                "price_delta_since_first_seen_pct": "2.5",
                "rising_missed_one_share_entry_price": "10000",
            },
        ),
        _event(1, "000001", "winner", "latency_pass"),
        _event(1, "000001", "winner", "order_bundle_submitted"),
        _event(
            1,
            "000001",
            "winner",
            "stat_action_decision_snapshot",
            {
                "profit_rate": "+1.80",
                "peak_profit": "+2.10",
                "current_ai_score": "72",
                "scale_in_action_type": "PYRAMID",
                "scale_in_gate_allowed": "True",
                "scale_in_blocker_reason": "scalping_pyramid_ok",
                "distance_to_buy_bps": "210.0",
            },
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            1,
            "000001",
            "winner",
            "scale_in_price_guard_block",
            {"scale_in_action_type": "PYRAMID", "reason": "quote_stale"},
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            1,
            "000001",
            "winner",
            "scale_in_qty_block",
            {"scale_in_action_type": "PYRAMID", "reason": "pyramid_exposure_cap"},
            pipeline="HOLDING_PIPELINE",
        ),
        _event(
            2,
            "000002",
            "loser",
            "budget_pass",
            {
                "forced_entry_reason": "rising_missed_one_share_entry",
                "rising_missed_one_share_entry_forced": "True",
                "scanner_promotion_reason": "price_jump_start_acceleration",
                "source_signature": "OPEN_TOP,PRICE_JUMP_START,VALUE_TOP",
                "price_delta_since_first_seen_pct": "4.0",
            },
        ),
        _event(2, "000002", "loser", "latency_pass"),
        _event(2, "000002", "loser", "order_bundle_submitted"),
    ]
    pipeline_path.write_text("\n".join(json.dumps(row) for row in pipeline_rows), encoding="utf-8")
    post_sell_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "recommendation_id": 1,
                        "stock_code": "000001",
                        "stock_name": "winner",
                        "sell_time": "09:10:00",
                        "profit_rate": 1.2,
                        "peak_profit": 1.5,
                        "held_sec": 600,
                        "exit_rule": "scalp_trailing_take_profit",
                    }
                ),
                json.dumps(
                    {
                        "recommendation_id": 2,
                        "stock_code": "000002",
                        "stock_name": "loser",
                        "sell_time": "09:05:00",
                        "profit_rate": -0.8,
                        "peak_profit": 0.0,
                        "held_sec": 120,
                        "exit_rule": "scalp_hard_stop_pct",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    diagnostic_path.write_text(
        json.dumps(
            {
                "rising_missed_buy": [
                    {
                        "stock_code": "000003",
                        "stock_name": "missed",
                        "rising_missed_class": "source_quality_excluded",
                        "rising_missed_one_share_eligible": False,
                        "max_price_delta_since_first_seen_pct": 3.0,
                        "latest_blocker": {"stage": "blocked_strength_momentum", "reason": "insufficient_history"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-01",
        pipeline_path=pipeline_path,
        post_sell_path=post_sell_path,
        diagnostic_path=diagnostic_path,
        generated_at="fixed",
    )

    assert report["summary"]["forced_scout_record_count"] == 2
    assert report["summary"]["profitable_forced_scout_count"] == 1
    assert report["summary"]["loss_or_flat_forced_scout_count"] == 1
    assert report["summary"]["current_missed_count"] == 1
    assert report["summary"]["scale_in_price_guard_block_record_count"] == 1
    assert report["summary"]["scale_in_qty_block_record_count"] == 1
    assert report["summary"]["code_improvement_order_count"] == 4
    assert report["scale_in_bottleneck_summary"]["pyramid_ok_record_count"] == 1
    assert report["scale_in_bottleneck_summary"]["price_guard_reason_counts"] == [
        {"reason": "quote_stale", "count": 1}
    ]
    assert report["scale_in_bottleneck_summary"]["qty_block_reason_counts"] == [
        {"reason": "pyramid_exposure_cap", "count": 1}
    ]
    assert (
        report["metric_contracts"]["scale_in_bottleneck_summary"]["decision_authority"]
        == "source_only_scale_in_bottleneck_analysis"
    )
    assert (
        "scale_in_guard_bypass"
        in report["metric_contracts"]["scale_in_bottleneck_summary"]["forbidden_uses"]
    )
    assert {order["mapped_family"] for order in report["code_improvement_orders"]} == {
        "rising_missed_scout_loss_filter",
        "rising_missed_scout_post_sell_bridge",
        "rising_missed_scout_scale_in_price_guard_split",
        "rising_missed_scout_scale_in_qty_evidence_split",
    }
    assert {order["implementation_status"] for order in report["code_improvement_orders"]} == {
        "implemented"
    }
    assert {
        order["implementation_provenance"]["runtime_effect"]
        for order in report["code_improvement_orders"]
    } == {False}
    assert {order["runtime_effect"] for order in report["code_improvement_orders"]} == {False}
    assert {order["allowed_runtime_apply"] for order in report["code_improvement_orders"]} == {False}
    assert all("forced_one_share_success_counting" in order["forbidden_uses"] for order in report["code_improvement_orders"])
    scale_orders = [
        order
        for order in report["code_improvement_orders"]
        if str(order["mapped_family"]).startswith("rising_missed_scout_scale_in")
    ]
    assert all("scale_in_guard_bypass" in order["forbidden_uses"] for order in scale_orders)
    assert all("position_cap_release" in order["forbidden_uses"] for order in scale_orders)


def test_write_outputs_renders_json_and_markdown(tmp_path):
    report = {
        "target_date": "2026-07-01",
        "generated_at": "fixed",
        "summary": {
            "forced_scout_record_count": 1,
            "forced_scout_with_post_sell_count": 1,
            "profitable_forced_scout_count": 1,
            "loss_or_flat_forced_scout_count": 0,
            "winner_profit": {"avg_profit_rate": 1.2},
            "loser_profit": {"avg_profit_rate": None},
            "current_missed_count": 0,
            "scale_in_price_guard_block_record_count": 1,
            "scale_in_qty_block_record_count": 1,
            "scale_in_executed_record_count": 0,
            "code_improvement_order_count": 1,
        },
        "code_improvement_orders": [
            {
                "order_id": "order_rising_missed_scout_post_sell_bridge",
                "title": "bridge",
                "mapped_family": "rising_missed_scout_post_sell_bridge",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "evidence": ["winner_count=1"],
            }
        ],
    }
    output_json = tmp_path / "report.json"
    output_md = tmp_path / "report.md"

    mod.write_outputs(report, output_json=output_json, output_md=output_md)

    assert json.loads(output_json.read_text(encoding="utf-8"))["target_date"] == "2026-07-01"
    markdown = output_md.read_text(encoding="utf-8")
    assert "order_rising_missed_scout_post_sell_bridge" in markdown
    assert "runtime_effect: false" in markdown


def test_build_report_streams_pipeline_jsonl_without_full_text_read(tmp_path, monkeypatch):
    pipeline_path = tmp_path / "pipeline.jsonl"
    post_sell_path = tmp_path / "post_sell.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    pipeline_path.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                _event(
                    1,
                    "000001",
                    "winner",
                    "rising_missed_one_share_entry",
                    {"forced_entry_reason": "rising_missed_one_share_entry"},
                ),
                _event(1, "000001", "winner", "latency_pass"),
                _event(
                    1,
                    "000001",
                    "winner",
                    "scale_in_executed",
                    {"scale_in_action_type": "PYRAMID"},
                    pipeline="HOLDING_PIPELINE",
                ),
            ]
        ),
        encoding="utf-8",
    )
    post_sell_path.write_text(
        json.dumps({"recommendation_id": 1, "profit_rate": 1.1, "peak_profit": 1.3}) + "\n",
        encoding="utf-8",
    )
    diagnostic_path.write_text(json.dumps({"rising_missed_buy": []}), encoding="utf-8")

    original_read_text = Path.read_text

    def guarded_read_text(self, *args, **kwargs):
        if self == pipeline_path:
            raise AssertionError("pipeline JSONL must be streamed, not read as one string")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_read_text)

    report = mod.build_report(
        "2026-07-01",
        pipeline_path=pipeline_path,
        post_sell_path=post_sell_path,
        diagnostic_path=diagnostic_path,
        generated_at="fixed",
    )

    assert report["summary"]["forced_scout_record_count"] == 1
    assert report["summary"]["scale_in_executed_record_count"] == 1
