import gzip
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
                "rising_missed_selection_prior_key": "prior_positive",
                "rising_missed_selection_recommendation": "positive_prior",
                "rising_missed_selection_confidence": "high",
                "rising_missed_selection_score_delta": "20",
                "rising_missed_selection_rank_reason": "positive_prior_test",
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
                "rising_missed_selection_prior_key": "prior_loss",
                "rising_missed_selection_recommendation": "loss_filter",
                "rising_missed_selection_confidence": "medium",
                "rising_missed_selection_score_delta": "-20",
                "rising_missed_selection_rank_reason": "loss_prior_test",
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
                        "recent_blockers": [
                            {
                                "stage": "blocked_strength_momentum",
                                "reason": "insufficient_history",
                                "rising_missed_selection_prior_key": "prior_blocked",
                                "rising_missed_selection_recommendation": "source_quality_blocked",
                                "rising_missed_selection_score_delta": -30,
                            }
                        ],
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
    assert report["summary"]["forced_scout_selection_prior_winner_counts"] == [
        {"recommendation": "positive_prior", "count": 1}
    ]
    assert report["summary"]["forced_scout_selection_prior_loser_counts"] == [
        {"recommendation": "loss_filter", "count": 1}
    ]
    assert report["summary"]["shared_source_signature_count"] == 1
    assert report["summary"]["take_profit_runner_review_candidate_count"] == 1
    assert report["entry_quality_split_summary"]["loser_peak_profit"]["avg_peak_profit"] == 0.0
    assert (
        report["take_profit_capture_summary"]["runner_review_candidates"][0]["stock_code"]
        == "000001"
    )
    assert (
        "take_profit_policy_change_without_approval"
        in report["take_profit_capture_summary"]["forbidden_uses"]
    )
    assert report["summary"]["current_missed_count"] == 1
    assert report["summary"]["current_missed_selection_prior_recommendation_counts"] == [
        {"recommendation": "source_quality_blocked", "count": 1}
    ]
    assert report["current_missed_summary"]["top_rows"][0]["rising_missed_selection_prior_key"] == "prior_blocked"
    assert report["summary"]["scale_in_price_guard_block_record_count"] == 1
    assert report["summary"]["scale_in_qty_block_record_count"] == 1
    assert report["summary"]["code_improvement_order_count"] == 5
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
        "rising_missed_scout_take_profit_capture_review",
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
    assert "take_profit_runner_review_candidate_count" in markdown


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


def test_build_report_reads_gzip_pipeline_fallback(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "data" / "pipeline_events"
    post_sell_dir = tmp_path / "data" / "post_sell"
    diagnostic_dir = tmp_path / "data" / "report" / "intraday_entry_blocker_diagnostics"
    feedback_dir = tmp_path / "data" / "report" / "rising_missed_intraday_feedback"
    prior_dir = tmp_path / "data" / "report" / "rising_missed_classifier_prior"
    for path in [pipeline_dir, post_sell_dir, diagnostic_dir, feedback_dir, prior_dir]:
        path.mkdir(parents=True, exist_ok=True)
    with gzip.open(pipeline_dir / "pipeline_events_2026-07-02.jsonl.gz", "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                _event(
                    1,
                    "000001",
                    "gzip",
                    "rising_missed_one_share_entry",
                    {"forced_entry_reason": "rising_missed_one_share_entry"},
                )
            )
            + "\n"
        )
    (post_sell_dir / "post_sell_candidates_2026-07-02.jsonl").write_text("", encoding="utf-8")
    (diagnostic_dir / "intraday_entry_blocker_diagnostics_2026-07-02.json").write_text(
        json.dumps({"rising_missed_buy": []}),
        encoding="utf-8",
    )
    (feedback_dir / "rising_missed_intraday_feedback_2026-07-02.json").write_text(
        json.dumps({"summary": {}}),
        encoding="utf-8",
    )
    (prior_dir / "rising_missed_classifier_prior_2026-07-02.json").write_text(
        json.dumps({"summary": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)

    report = mod.build_report("2026-07-02", generated_at="fixed")

    assert report["summary"]["forced_scout_record_count"] == 1
    assert report["source_paths"]["pipeline_events"].endswith("pipeline_events_2026-07-02.jsonl.gz")


def test_build_report_ingests_intraday_feedback_order(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    post_sell_path = tmp_path / "post_sell.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    intraday_feedback_path = tmp_path / "feedback.json"
    classifier_prior_path = tmp_path / "missing_prior.json"
    pipeline_path.write_text(
        json.dumps(
            _event(
                1,
                "000001",
                "feedback",
                "rising_missed_one_share_entry",
                {"forced_entry_reason": "rising_missed_one_share_entry"},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    post_sell_path.write_text("", encoding="utf-8")
    diagnostic_path.write_text(json.dumps({"rising_missed_buy": []}), encoding="utf-8")
    intraday_feedback_path.write_text(
        json.dumps(
            {
                "summary": {
                    "rising_missed_avg_down_ge2_count": 2,
                    "initial_quality_fail_count": 1,
                    "feedback_label_counts": [
                        {"feedback_label": "rising_missed_initial_quality_fail", "count": 1},
                        {"feedback_label": "rising_missed_initial_quality_review", "count": 1},
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-02",
        pipeline_path=pipeline_path,
        post_sell_path=post_sell_path,
        diagnostic_path=diagnostic_path,
        intraday_feedback_path=intraday_feedback_path,
        classifier_prior_path=classifier_prior_path,
        generated_at="fixed",
    )

    assert report["summary"]["intraday_feedback_avg_down_ge2_count"] == 2
    assert report["summary"]["intraday_feedback_initial_quality_fail_count"] == 1
    order = report["code_improvement_orders"][0]
    assert order["mapped_family"] == "rising_missed_initial_quality_feedback_loop"
    assert order["runtime_effect"] is False
    assert "scale_in_guard_bypass" in order["forbidden_uses"]


def test_build_report_ingests_classifier_prior_source_only_order(tmp_path):
    pipeline_path = tmp_path / "pipeline.jsonl"
    post_sell_path = tmp_path / "post_sell.jsonl"
    diagnostic_path = tmp_path / "diag.json"
    intraday_feedback_path = tmp_path / "feedback.json"
    classifier_prior_path = tmp_path / "prior.json"
    pipeline_path.write_text("", encoding="utf-8")
    post_sell_path.write_text("", encoding="utf-8")
    diagnostic_path.write_text(json.dumps({"rising_missed_buy": []}), encoding="utf-8")
    intraday_feedback_path.write_text(json.dumps({"summary": {}}), encoding="utf-8")
    classifier_prior_path.write_text(
        json.dumps(
            {
                "summary": {
                    "prior_count": 2,
                    "recommendation_counts": {"positive_prior": 1, "quality_risk": 1},
                }
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_report(
        "2026-07-02",
        pipeline_path=pipeline_path,
        post_sell_path=post_sell_path,
        diagnostic_path=diagnostic_path,
        intraday_feedback_path=intraday_feedback_path,
        classifier_prior_path=classifier_prior_path,
        generated_at="fixed",
    )

    assert report["summary"]["classifier_prior_available"] is True
    assert report["summary"]["classifier_prior_count"] == 2
    assert report["summary"]["code_improvement_order_count"] == 1
    order = report["code_improvement_orders"][0]
    assert order["mapped_family"] == "rising_missed_classifier_prior_feedback_bridge"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert "forced_one_share_success_counting" in order["forbidden_uses"]
