import json
from datetime import datetime, timedelta

from src.engine.scalping import microstructure_reaction_context as mod


def _v3_observation(identity="a", **extra):
    return {
        "stock_code": "005930",
        "record_id": "123",
        "stage": "ai_confirmed",
        "event_time": "2026-09-04T09:00:00",
        "microstructure_reaction_context_version": mod.CONTEXT_VERSION,
        "microstructure_reaction_context_id": identity,
        "microstructure_reaction_evaluation_id": identity,
        "microstructure_reaction_delivery_telemetry_version": "v3",
        "microstructure_reaction_context_computed": True,
        "microstructure_reaction_context_status": "ok",
        "microstructure_reaction_reference_time": "2026-09-04T09:00:00",
        "microstructure_reaction_reference_price": 10000,
        "microstructure_reaction_venue": "KRX",
        **extra,
    }


def test_v3_coverage_deduplicates_and_ignores_scanner_volume(tmp_path):
    rows = [_v3_observation() for _ in range(3)]
    baseline = mod._delivery_observation_summary(rows)
    more = mod._delivery_observation_summary(
        rows + [{"stage": "scanner", "v_pw_now": 100} for _ in range(1000)]
    )
    assert baseline["context_computed_count"] == more["context_computed_count"] == 1
    assert baseline["usable_coverage_pct"] == more["usable_coverage_pct"] == 100
    assert more["provider_delivery_coverage_pct"] is None
    assert (
        mod._microstructure_code_improvement_orders(more, tmp_path / "report.json")
        == []
    )
    bad = [
        _v3_observation(
            microstructure_reaction_source_quality="missing_quote_time",
            microstructure_reaction_context_status="source_quality_missing",
        )
        for _ in range(3)
    ]
    summary = mod._delivery_observation_summary(bad)
    orders = mod._microstructure_code_improvement_orders(
        summary, tmp_path / "report.json"
    )
    assert len(orders) == 1 and orders[0]["unique_affected_count"] == 1
    assert orders[0]["runtime_effect"] is False
    assert (
        mod._microstructure_code_improvement_orders(
            {"row_count": 1, "rest_signed_trade_ticks_row_count": 1},
            tmp_path / "report.json",
        )
        == []
    )


def test_v3_cache_is_not_a_new_computation_requirement():
    summary = mod._delivery_observation_summary(
        [
            _v3_observation(),
            _v3_observation(
                "cache",
                ai_trace_endpoint_name="analyze_target",
                microstructure_reaction_context_computed=False,
                microstructure_reaction_context_reused=True,
            ),
        ]
    )
    assert summary["context_applicable_count"] == 1
    assert summary["context_computed_count"] == 1
    assert summary["computed_coverage_pct"] == 100
    assert summary["context_reused_count"] == 1
    assert summary["diagnostic_contract_violation_counts"] == {}


def test_v3_missing_required_payload_remains_in_delivery_denominator():
    summary = mod._delivery_observation_summary(
        [
            _v3_observation(
                ai_trace_endpoint_name="holding_score",
                microstructure_reaction_context_consumed=True,
                microstructure_reaction_context_consumer="holding_source_quality",
                microstructure_reaction_context_payload_included=False,
                microstructure_reaction_provider_delivery_status="response_received",
                microstructure_reaction_context_sent=False,
            ),
            _v3_observation(
                "sent",
                microstructure_reaction_context_payload_included=True,
                microstructure_reaction_provider_delivery_status="response_received",
                microstructure_reaction_context_sent=True,
            ),
        ]
    )
    assert summary["context_payload_included_count"] == 1
    assert summary["provider_delivery_required_count"] == 2
    assert summary["context_sent_count"] == 1
    assert summary["provider_delivery_coverage_pct"] == 50
    assert summary["diagnostic_contract_violation_counts"] == {
        "required_holding_payload_missing": 1
    }


def test_defect_provenance_preserves_exact_owner_and_bounded_unique_receipts(tmp_path):
    rows = [
        _v3_observation(str(i), microstructure_reaction_venue=None) for i in range(25)
    ]
    result = mod._delivery_observation_summary(rows + rows)
    cause = "evaluation_venue_missing_or_conflicting"
    detail = result["diagnostic_contract_provenance"][cause]
    assert detail["unique_evaluation_count"] == 25
    assert detail["stage_counts"] == {"ai_confirmed": 25}
    assert len(detail["receipts"]) == 20 and detail["truncated"] is True
    assert detail["historical_source_repaired"] is False
    example = detail["receipts"][0]
    assert example["record_id"] == "123" and example["stock_code"] == "005930"
    assert example["microstructure_reaction_venue"] is None
    orders = mod._microstructure_code_improvement_orders(
        result, tmp_path / "source.json"
    )
    assert orders[0]["diagnostic_provenance"] == detail
    assert result["diagnostic_contract_violation_counts"][cause] == 25


def test_finite_outcome_floor_and_version_separation(monkeypatch, tmp_path):
    monkeypatch.setattr(
        mod,
        "_source_quality_preflight",
        lambda _: {
            "signature": {},
            "status": "pass",
            "tuning_input_allowed": True,
            "blocked_reason": None,
        },
    )
    outcomes = [
        {
            "opportunity_id": str(i),
            "feature_version": mod.CONTEXT_VERSION,
            "outcome_join_status": "time_exact",
            "outcome_source_quality_pass": True,
            "cost_adjusted_counterfactual_return_pct": value,
        }
        for i, value in enumerate(
            [0.2] + [None] * 16 + [float("nan"), float("inf"), float("-inf")]
        )
    ]
    outcomes += [
        {
            **outcomes[0],
            "opportunity_id": "old",
            "feature_version": "microstructure_reaction_context_v1",
            "cost_adjusted_counterfactual_return_pct": 99,
        }
    ]
    rollup = mod._daily_opportunity_rollup(
        "2026-09-04", {"opportunities": outcomes}, tmp_path / "events"
    )
    assert rollup["outcome_source_quality_pass_count"] == 20
    assert rollup["source_quality_adjusted_ev_evaluable_count"] == 1
    assert rollup["source_quality_adjusted_return_sum_pct"] == 0.2
    assert rollup["historical_diagnostic_opportunity_count"] == 1
    rollup["tuning_input_allowed"] = True
    monkeypatch.setattr(mod, "_available_pipeline_dates", lambda _: ["2026-09-04"])
    monkeypatch.setattr(mod, "_load_daily_opportunity_rollup", lambda _: rollup)
    cumulative = mod._clean_baseline_cumulative_opportunity_exploration("2026-09-04")
    assert cumulative["diagnostic_sample_floor_met"] is False
    assert cumulative["source_quality_adjusted_ev_pct"] == 0.2
    assert cumulative["candidate_review_required"] is False


def test_two_same_cycle_micro_anchors_join_their_own_outcomes(monkeypatch, tmp_path):
    from src.engine.sniper_missed_entry_counterfactual import (
        EntryEvent,
        _build_microstructure_attempt_outcomes,
    )

    start = datetime(2026, 9, 4, 9)
    rows = [
        _v3_observation("a"),
        _v3_observation(
            "b",
            microstructure_reaction_reference_time="2026-09-04T09:01:00",
            microstructure_reaction_reference_price=10100,
        ),
    ]
    events = [
        EntryEvent(
            row["event_time"],
            "2026-09-04",
            "Samsung",
            "005930",
            "ai_confirmed",
            "123",
            row,
        )
        for row in rows
    ]
    points = {
        ("005930", "KRX"): [
            (start + timedelta(minutes=i), 10000 + i * 10) for i in range(1, 22)
        ],
        ("005930", "NXT"): [(start + timedelta(minutes=20), 20000)],
    }
    report = _build_microstructure_attempt_outcomes(
        events, points, now=start + timedelta(hours=1)
    )
    assert len(report["rows"]) == 2
    assert (
        report["rows"][0]["cost_adjusted_counterfactual_return_pct"]
        != report["rows"][1]["cost_adjusted_counterfactual_return_pct"]
    )
    monkeypatch.setattr(
        mod,
        "_load_watch_cycle_outcomes",
        lambda _: (report["rows"], tmp_path / "outcome.json", "loaded"),
    )
    opportunities = mod._unique_entry_opportunities(rows + rows)
    assert len(opportunities) == 2
    mod._attach_time_exact_outcomes(opportunities, "2026-09-04")
    assert all(row["outcome_join_status"] == "time_exact" for row in opportunities)
    assert all(row["outcome_reference_delta_ms"] == 0 for row in opportunities)
    pending = _build_microstructure_attempt_outcomes(
        events, points, now=start + timedelta(minutes=10)
    )
    assert all(
        row["outcome_status"] == "pending_outcome"
        and row["cost_adjusted_counterfactual_return_pct"] is None
        for row in pending["rows"]
    )


def test_diagnostic_handoff_reports_missing_workorder_without_live_gate():
    from src.engine.verify_threshold_cycle_postclose_chain import (
        _microstructure_diagnostic_handoff_status,
    )

    source = {"schema_version": 5, "code_improvement_orders": [{"order_id": "order_a"}]}
    summary = {"code_improvement_order_ids": ["order_a"], "runtime_effect": False}
    report = {"microstructure_reaction_context": summary}
    daily = {"calibration_source_bundle": {"source_metrics": report}}
    missing = _microstructure_diagnostic_handoff_status(
        source, report, report, {}, daily
    )
    assert missing["status"] == "automation_handoff_gap"
    assert missing["issues"] == ["workorder_missing:order_a"]
    assert missing["runtime_effect"] is False
    closed = _microstructure_diagnostic_handoff_status(
        source, report, report, {"orders": [{"order_id": "order_a"}]}, daily
    )
    assert closed["status"] == "pass"


def test_v3_wire_report_preserves_identity_and_emits_one_real_defect(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "reports")
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", tmp_path)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", tmp_path / "snapshots")
    monkeypatch.setattr(mod, "SOURCE_QUALITY_AUDIT_DIR", tmp_path / "quality")
    monkeypatch.setattr(mod, "_available_pipeline_dates", lambda _: [])
    fields = _v3_observation(
        microstructure_reaction_context_status="source_quality_missing",
        microstructure_reaction_source_quality="missing_quote_time",
    )
    events = [
        {
            "stage": stage,
            "record_id": 123,
            "stock_code": "005930",
            "emitted_at": "2026-09-04T09:00:00",
            "fields": {key: str(value) for key, value in fields.items()},
        }
        for stage in ("ai_confirmed", "blocked_ai_score", "watching_analyze_target")
    ]
    (tmp_path / "pipeline_events_2026-09-04.jsonl").write_text(
        "\n".join(json.dumps(event) for event in events) + "\n"
    )
    report = mod.build_microstructure_reaction_context_report("2026-09-04")
    assert report["summary"]["context_computed_count"] == 1
    assert report["summary"]["delivery_telemetry_legacy_unverifiable_count"] == 0
    assert report["rows"][0]["microstructure_reaction_evaluation_id"] == "a"
    assert len(report["code_improvement_orders"]) == 1
    assert report["code_improvement_orders"][0]["unique_affected_count"] == 1


def test_verifier_catches_producer_not_emitting_required_diagnostic_order():
    from src.engine.verify_threshold_cycle_postclose_chain import (
        _microstructure_diagnostic_handoff_status,
    )

    source = {
        "schema_version": 5,
        "summary": {"diagnostic_contract_violation_counts": {"missing_quote_time": 1}},
    }
    result = _microstructure_diagnostic_handoff_status(source, {}, {}, {}, {})
    assert result["status"] == "automation_handoff_gap"
    assert "producer_workorder_missing:missing_quote_time" in result["issues"]


def test_microstructure_reaction_context_report_preserves_contract_and_keys(
    tmp_path, monkeypatch
):
    event_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "microstructure_reaction_context"
    event_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(
        mod, "MONITOR_SNAPSHOT_DIR", tmp_path / "report" / "monitor_snapshots"
    )

    event_path = event_dir / "pipeline_events_2026-05-31.jsonl"
    event_path.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "ai_confirmed",
                        "stock_code": "A005930",
                        "stock_name": "Samsung",
                        "record_id": "real-1",
                        "emitted_at": "2026-05-31T09:01:00+09:00",
                        "fields": {
                            "source_event_stage": "ai_confirmed",
                            "actual_order_submitted": True,
                            "broker_order_forbidden": False,
                            "microstructure_reaction_context_version": "microstructure_reaction_context_v1",
                            "microstructure_reaction_context_status": "ok",
                            "microstructure_reaction_ask_sweep_score": 72,
                            "microstructure_reaction_post_sweep_hold_score": 68,
                            "microstructure_reaction_bid_replenishment_score": 61,
                            "microstructure_reaction_wall_replenishment_risk_score": 35,
                            "microstructure_reaction_vi_proximity_risk": 10,
                            "microstructure_reaction_entry_reaction_quality": "favorable_reaction",
                            "microstructure_reaction_source_quality": "fresh_short_window",
                            "microstructure_reaction_context_hash": "abc123",
                            "tick_aggressor_source_counts": "{'kiwoom_0b_signed_trade_volume': 5}",
                            "tick_trade_value_source_counts": "{'1313': 3, 'calc_price_x_1030_1031_sum': 2}",
                            "tick_trade_value_1313_count": 3,
                            "tick_trade_value_1313_missing_count": 2,
                            "trade_volume_source_counts": "{'1030_1031_sum': 5}",
                            "trade_volume_1030_1031_vs_15_evaluable_count": 5,
                            "trade_volume_1030_1031_vs_15_mismatch_count": 1,
                            "kiwoom_0b_aux_observed_count": 10,
                            "kiwoom_0b_1313_present_count": 6,
                            "kiwoom_0b_1313_missing_count": 4,
                            "kiwoom_0b_trade_value_source_counts": "{'1313': 6, 'calc_price_x_1030_1031_sum': 4}",
                            "kiwoom_0b_trade_volume_source_counts": "{'1030_1031_sum': 10}",
                            "kiwoom_0b_1030_1031_vs_15_evaluable_count": 10,
                            "kiwoom_0b_1030_1031_vs_15_mismatch_count": 2,
                            "ka10003_buy_dominance_observation": {
                                "source_counts": {
                                    "1030_1031_split": 2,
                                    "signed_volume": 1,
                                },
                                "trade_value_source_counts": {
                                    "1313": 2,
                                    "calc_price_x_volume": 1,
                                },
                                "inside_spread_count": 1,
                                "split_vs_15_evaluable_count": 2,
                                "split_vs_15_mismatch_count": 1,
                            },
                            "v_pw_now": 131.0,
                            "v_pw_source": "ws_0b",
                            "v_pw_runtime_support_usable": True,
                            "v_pw_ws_value": 131.0,
                            "v_pw_rest_value": 109.0,
                            "ka10046_strength_source": "ka10046_rest_strength_trend",
                            "ka10046_strength_decision_authority": "strength_trend_rest_fallback_source_only",
                            "ka10046_strength_runtime_effect": False,
                            "ka10046_strength_rest_received_ts_ms": 1780000000000,
                            "market_data_signed_tape_state": "sell_dominated",
                            "market_data_signed_tape_sample_count": 3,
                            "market_data_signed_tape_buy_count": 1,
                            "market_data_signed_tape_sell_count": 2,
                            "market_data_signed_tape_buy_volume": 100,
                            "market_data_signed_tape_sell_volume": 350,
                            "market_data_signed_tape_buy_ratio_pct": 22.222,
                            "market_data_rest_signed_tape_pressure_usable": False,
                            "rest_signed_trade_ticks": [
                                {
                                    "signed_trade_volume": "-200",
                                    "rest_signed_tape_source": "ka10084",
                                },
                                {
                                    "signed_trade_volume": "+100",
                                    "rest_signed_tape_source": "ka10084",
                                },
                            ],
                            "latency_true_ofi_direct_canary_signed_tape_sample_count": 3,
                            "latency_true_ofi_direct_canary_signed_tape_buy_count": 1,
                            "latency_true_ofi_direct_canary_signed_tape_sell_count": 2,
                            "latency_true_ofi_direct_canary_signed_tape_buy_volume": 100,
                            "latency_true_ofi_direct_canary_signed_tape_sell_volume": 350,
                            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume": -250,
                            "latency_true_ofi_direct_canary_signed_tape_buy_ratio": 22.222,
                            "latency_true_ofi_direct_canary_signed_tape_latest_side": "SELL",
                            "latency_true_ofi_direct_canary_signed_tape_sell_dominated": True,
                            "latency_true_ofi_direct_canary_signed_tape_latest_buy_single": 0,
                            "latency_true_ofi_direct_canary_signed_tape_latest_sell_single": 200,
                            "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated": True,
                            "latency_true_ofi_direct_canary_tape_block_reason": "signed_tape_sell_dominated",
                            "latency_true_ofi_direct_canary_tape_support_ok": False,
                            "quote_stale": False,
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "blocked_liquidity",
                        "stock_code": "A000660",
                        "record_id": "probe-1",
                        "emitted_at": "2026-05-31T09:02:00+09:00",
                        "fields": {
                            "source_event_stage": "blocked_liquidity",
                            "sim_record_id": "sim-1",
                            "sim_parent_record_id": "parent-1",
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "microstructure_reaction_context_version": "microstructure_reaction_context_v1",
                            "microstructure_reaction_context_status": "stale",
                            "microstructure_reaction_ask_sweep_score": 50,
                            "microstructure_reaction_post_sweep_hold_score": 50,
                            "microstructure_reaction_bid_replenishment_score": 50,
                            "microstructure_reaction_wall_replenishment_risk_score": 50,
                            "microstructure_reaction_vi_proximity_risk": 0,
                            "microstructure_reaction_entry_reaction_quality": "neutral_unusable",
                            "microstructure_reaction_source_quality": "stale_tick_or_quote",
                            "microstructure_reaction_context_hash": "def456",
                            "tick_aggressor_source_counts": "{'missing_best_quote': 5}",
                            "tick_trade_value_source_counts": "{'calc_price_x_15_abs': 5}",
                            "tick_trade_value_1313_count": 0,
                            "tick_trade_value_1313_missing_count": 5,
                            "trade_volume_source_counts": "{'15_abs': 5}",
                            "trade_volume_1030_1031_vs_15_evaluable_count": 0,
                            "trade_volume_1030_1031_vs_15_mismatch_count": 0,
                            "kiwoom_0b_aux_observed_count": 3,
                            "kiwoom_0b_1313_present_count": 0,
                            "kiwoom_0b_1313_missing_count": 3,
                            "kiwoom_0b_trade_value_source_counts": "{'calc_price_x_15_abs': 3}",
                            "kiwoom_0b_trade_volume_source_counts": "{'15_abs': 3}",
                            "kiwoom_0b_1030_1031_vs_15_evaluable_count": 0,
                            "kiwoom_0b_1030_1031_vs_15_mismatch_count": 0,
                            "ka10003_buy_dominance_observation_source_counts": "{'inside_excluded': 3}",
                            "ka10003_buy_dominance_observation_trade_value_source_counts": "{'calc_price_x_volume': 3}",
                            "ka10003_buy_dominance_observation_inside_spread_count": 3,
                            "ka10003_buy_dominance_observation_split_vs_15_evaluable_count": 0,
                            "ka10003_buy_dominance_observation_split_vs_15_mismatch_count": 0,
                            "v_pw_now": 120.0,
                            "v_pw_source": "ka10046_rest_fallback",
                            "v_pw_runtime_support_usable": False,
                            "v_pw_ws_value": 0.0,
                            "v_pw_rest_value": 120.0,
                            "ka10046_strength_source": "ka10046_rest_strength_trend",
                            "ka10046_strength_decision_authority": "strength_trend_rest_fallback_source_only",
                            "ka10046_strength_runtime_effect": False,
                            "ka10046_strength_rest_received_ts_ms": 1780000001000,
                            "market_data_signed_tape_state": "mixed",
                            "market_data_signed_tape_sample_count": 2,
                            "market_data_signed_tape_buy_count": 1,
                            "market_data_signed_tape_sell_count": 1,
                            "market_data_signed_tape_buy_volume": 90,
                            "market_data_signed_tape_sell_volume": 80,
                            "market_data_signed_tape_buy_ratio_pct": 52.941,
                            "market_data_rest_signed_tape_pressure_usable": False,
                            "rest_signed_trade_ticks": "[{'signed_trade_volume': '-80', 'rest_signed_tape_source': 'ka10084'}]",
                            "latency_true_ofi_direct_canary_signed_tape_sample_count": 2,
                            "latency_true_ofi_direct_canary_signed_tape_buy_count": 1,
                            "latency_true_ofi_direct_canary_signed_tape_sell_count": 1,
                            "latency_true_ofi_direct_canary_signed_tape_buy_volume": 90,
                            "latency_true_ofi_direct_canary_signed_tape_sell_volume": 80,
                            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume": 10,
                            "latency_true_ofi_direct_canary_signed_tape_buy_ratio": 52.941,
                            "latency_true_ofi_direct_canary_signed_tape_latest_side": "BUY",
                            "latency_true_ofi_direct_canary_signed_tape_sell_dominated": False,
                            "latency_true_ofi_direct_canary_signed_tape_latest_buy_single": 90,
                            "latency_true_ofi_direct_canary_signed_tape_latest_sell_single": 0,
                            "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated": False,
                            "latency_true_ofi_direct_canary_tape_support_ok": True,
                            "quote_stale": True,
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "latency_block",
                        "stock_code": "A111111",
                        "record_id": "quote-only",
                        "emitted_at": "2026-05-31T09:03:00+09:00",
                        "fields": {
                            "quote_stale": True,
                            "ws_age_ms": 5000,
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_microstructure_reaction_context_report("2026-05-31")

    assert report["report_type"] == "microstructure_reaction_context"
    assert report["runtime_effect"] is False
    assert report["decision_authority"] == (
        "diagnostic_source_only_with_fail_closed_holding_quality_consumer"
    )
    assert report["metric_role"] == "source_quality_and_counterfactual_diagnostic"
    assert report["primary_decision_metric"] == "source_quality_adjusted_ev_pct"
    assert "standalone_buy" in report["forbidden_uses"]
    assert "broker_guard_bypass" in report["forbidden_uses"]
    assert report["summary"]["row_count"] == 2
    assert report["summary"]["ok_count"] == 1
    assert report["summary"]["real_submitted_count"] == 1
    assert report["schema_version"] == 5
    assert report["source_row_count"] == 2
    assert report["stored_row_count"] == 2
    assert report["summary"]["delivery_telemetry_v2_count"] == 0
    assert report["summary"]["delivery_telemetry_legacy_unverifiable_count"] == 2
    assert "rest_signed_trade_ticks" not in report["rows"][0]
    funnel = report["summary"]["opportunity_exploration_funnel"]
    assert funnel["favorable_reaction_usable_count"] == 1
    assert funnel["favorable_reaction_submitted_count"] == 1
    assert funnel["favorable_reaction_unsubmitted_count"] == 0
    assert funnel["favorable_reaction_unsubmitted_observation_stage_counts"] == {}
    assert funnel["favorable_reaction_unsubmitted_unique_stock_count"] == 0
    assert funnel["unique_entry_opportunity_count"] == 1
    assert funnel["unique_entry_submitted_opportunity_count"] == 1
    assert funnel["causal_blocker_attribution_complete"] is True
    assert funnel["runtime_effect"] is False
    assert report["summary"]["v_pw_source_counts"] == {
        "ka10046_rest_fallback": 1,
        "ws_0b": 1,
    }
    assert report["summary"]["v_pw_rest_fallback_count"] == 1
    assert report["summary"]["v_pw_ws_0b_count"] == 1
    assert report["summary"]["v_pw_rest_fallback_rate_pct"] == 50.0
    assert report["summary"]["v_pw_runtime_support_unusable_count"] == 1
    assert report["summary"]["ka10046_rest_fallback_quote_freshness_counts"] == {
        "stale": 1
    }
    assert report["summary"]["ka10046_rest_fallback_with_stale_quote_count"] == 1
    assert report["summary"]["ka10046_strength_runtime_effect_true_count"] == 0
    assert report["summary"]["ka10046_strength_missing_received_ts_count"] == 0
    assert report["summary"]["ka10046_0b_strength_compare_evaluable_count"] == 1
    assert report["summary"]["ka10046_0b_strength_abs_diff_avg"] == 22.0
    assert report["summary"]["ka10046_0b_strength_divergence20_count"] == 1
    assert report["summary"]["ka10046_0b_strength_divergence20_rate_pct"] == 100.0
    assert report["summary"]["market_data_signed_tape_state_counts"] == {
        "mixed": 1,
        "sell_dominated": 1,
    }
    assert report["summary"]["market_data_signed_tape_sample_count_total"] == 5
    assert report["summary"]["market_data_signed_tape_buy_count_total"] == 2
    assert report["summary"]["market_data_signed_tape_sell_count_total"] == 3
    assert report["summary"]["market_data_signed_tape_buy_volume_total"] == 190
    assert report["summary"]["market_data_signed_tape_sell_volume_total"] == 430
    assert (
        report["summary"]["market_data_rest_signed_tape_pressure_usable_true_count"]
        == 0
    )
    assert report["summary"]["rest_signed_trade_ticks_row_count"] == 3
    assert report["summary"]["rest_signed_trade_ticks_source_counts"] == {"ka10084": 3}
    assert (
        report["summary"][
            "latency_true_ofi_direct_canary_signed_tape_sample_count_total"
        ]
        == 5
    )
    assert (
        report["summary"]["latency_true_ofi_direct_canary_signed_tape_buy_count_total"]
        == 2
    )
    assert (
        report["summary"]["latency_true_ofi_direct_canary_signed_tape_sell_count_total"]
        == 3
    )
    assert (
        report["summary"][
            "latency_true_ofi_direct_canary_signed_tape_net_buy_volume_sum"
        ]
        == -240
    )
    assert report["summary"][
        "latency_true_ofi_direct_canary_signed_tape_latest_side_counts"
    ] == {
        "BUY": 1,
        "SELL": 1,
    }
    assert (
        report["summary"][
            "latency_true_ofi_direct_canary_signed_tape_sell_dominated_count"
        ]
        == 1
    )
    assert (
        report["summary"][
            "latency_true_ofi_direct_canary_signed_tape_latest_single_sell_dominated_count"
        ]
        == 1
    )
    assert report["summary"][
        "latency_true_ofi_direct_canary_tape_block_reason_counts"
    ] == {
        "missing": 1,
        "signed_tape_sell_dominated": 1,
    }
    assert report["rows"][0]["stock_code"] == "005930"
    assert report["rows"][1]["sim_record_id"] == "sim-1"
    assert report["rows"][1]["sim_parent_record_id"] == "parent-1"
    assert report["rows"][1]["broker_order_forbidden"] is True
    assert report["summary"]["tick_aggressor_source_counts"] == {
        "kiwoom_0b_signed_trade_volume": 5,
        "missing_best_quote": 5,
    }
    assert report["summary"]["tick_trade_value_1313_missing_count"] == 7
    assert report["summary"]["tick_trade_value_1313_missing_rate_pct"] == 70.0
    assert report["summary"]["trade_volume_1030_1031_vs_15_mismatch_count"] == 1
    assert report["summary"]["trade_volume_1030_1031_vs_15_mismatch_rate_pct"] == 20.0
    assert report["summary"]["trade_volume_1030_1031_vs_15_noncomparable_count"] == 5
    assert (
        report["summary"]["trade_volume_1030_1031_vs_15_contract_violation_count"] == 0
    )
    assert report["summary"]["v_pw_expected_count"] == 2
    assert report["summary"]["v_pw_missing_count"] == 0
    assert report["summary"]["kiwoom_0b_aux_observed_count"] == 13
    assert report["summary"]["kiwoom_0b_1313_missing_count"] == 7
    assert report["summary"]["kiwoom_0b_1313_missing_rate_pct"] == 53.846
    assert report["summary"]["kiwoom_0b_trade_value_source_counts"] == {
        "1313": 6,
        "calc_price_x_1030_1031_sum": 4,
        "calc_price_x_15_abs": 3,
    }
    assert report["summary"]["kiwoom_0b_1030_1031_vs_15_mismatch_rate_pct"] == 20.0
    assert report["summary"]["ka10003_buy_dominance_observation_source_counts"] == {
        "1030_1031_split": 2,
        "inside_excluded": 3,
        "signed_volume": 1,
    }
    assert report["summary"][
        "ka10003_buy_dominance_observation_trade_value_source_counts"
    ] == {
        "1313": 2,
        "calc_price_x_volume": 4,
    }
    assert (
        report["summary"]["ka10003_buy_dominance_observation_inside_spread_count"] == 4
    )
    assert (
        report["summary"][
            "ka10003_buy_dominance_observation_split_vs_15_mismatch_count"
        ]
        == 1
    )
    assert (
        report["summary"][
            "ka10003_buy_dominance_observation_split_vs_15_mismatch_rate_pct"
        ]
        == 50.0
    )
    assert report["summary"]["code_improvement_order_count"] == 0
    assert report["summary"]["top_code_improvement_orders"] == []
    assert report["code_improvement_orders"] == []
    markdown = (report_dir / "microstructure_reaction_context_2026-05-31.md").read_text(
        encoding="utf-8"
    )
    assert "code_improvement_order_count" in markdown
    assert "order_microstructure_signed_tape_runtime_candidate_review" not in markdown
    assert (report_dir / "microstructure_reaction_context_2026-05-31.json").exists()
    assert (report_dir / "microstructure_reaction_context_2026-05-31.md").exists()


def test_opportunity_funnel_deduplicates_entry_attempts_and_time_matches_outcomes(
    tmp_path, monkeypatch
):
    target_date = "2026-07-20"
    event_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "microstructure_reaction_context"
    snapshot_dir = tmp_path / "report" / "monitor_snapshots"
    source_quality_dir = tmp_path / "report" / "observation_source_quality_audit"
    event_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)
    source_quality_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", snapshot_dir)
    monkeypatch.setattr(mod, "SOURCE_QUALITY_AUDIT_DIR", source_quality_dir)

    def favorable_event(stage, emitted_at, *, record_id="entry-1", extra=None):
        fields = {
            "effective_venue": "KRX",
            "source_event_stage": stage,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "microstructure_reaction_context_status": "ok",
            "microstructure_reaction_entry_reaction_quality": "favorable_reaction",
            "microstructure_reaction_source_quality": "fresh_short_window",
        }
        fields.update(extra or {})
        return {
            "stage": stage,
            "stock_code": "A123456",
            "stock_name": "Example",
            "record_id": record_id,
            "emitted_at": emitted_at,
            "fields": fields,
        }

    events = [
        favorable_event(
            "ai_confirmed",
            f"{target_date}T09:00:00.500000+09:00",
            extra={"action": "DROP"},
        ),
        favorable_event(
            "scalp_entry_action_decision_snapshot",
            f"{target_date}T09:00:01+09:00",
            extra={"chosen_action": "NO_BUY_AI", "ai_action": "DROP"},
        ),
        favorable_event(
            "ai_holding_review",
            f"{target_date}T09:00:02+09:00",
            record_id="holding-1",
        ),
        favorable_event(
            "ai_confirmed",
            f"{target_date}T10:00:00+09:00",
            extra={"action": "DROP"},
        ),
    ]
    (event_dir / f"pipeline_events_{target_date}.jsonl").write_text(
        "\n".join(json.dumps(event) for event in events) + "\n",
        encoding="utf-8",
    )
    prior_date = "2026-07-19"
    for source_date in (prior_date, target_date):
        (
            source_quality_dir / f"observation_source_quality_audit_{source_date}.json"
        ).write_text(
            json.dumps(
                {
                    "status": "pass",
                    "tuning_input_allowed": True,
                }
            ),
            encoding="utf-8",
        )
    (event_dir / f"pipeline_events_{prior_date}.jsonl").write_text(
        json.dumps(
            favorable_event(
                "ai_confirmed",
                f"{prior_date}T09:30:00+09:00",
                record_id="prior-entry",
                extra={"action": "DROP"},
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (snapshot_dir / f"missed_entry_counterfactual_{prior_date}.json").write_text(
        json.dumps(
            {
                "watch_cycle_participation_ledger": {
                    "rows": [
                        {
                            "stock_code": "123456",
                            "runtime_record_id": "prior-entry",
                            "effective_venue": "KRX",
                            "reference_time": f"{prior_date}T09:30:00+09:00",
                            "primary_source_quality_state": "pass",
                            "opportunity_label": "gross_target_first",
                            "primary_horizon_min": 20,
                            "cost_adjusted_counterfactual_return_pct": 1.0,
                            "forward_horizon_metrics": {
                                "20": {"mfe_pct": 1.5, "mae_pct": -0.2}
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    outcome_path = snapshot_dir / f"missed_entry_counterfactual_{target_date}.json"
    outcome_path.write_text(
        json.dumps(
            {
                "watch_cycle_participation_ledger": {
                    "rows": [
                        {
                            "stock_code": "123456",
                            "runtime_record_id": "entry-1",
                            "reference_time": f"{target_date}T09:00:00+09:00",
                            "primary_source_quality_state": "pass",
                            "effective_venue": "KRX",
                            "market_session_bucket": "krx_regular",
                            "opportunity_label": "gross_target_first",
                            "primary_horizon_min": 20,
                            "cost_adjusted_counterfactual_return_pct": 2.0,
                            "forward_horizon_metrics": {
                                "1": {"mfe_pct": 0.8, "mae_pct": -0.1},
                                "20": {"mfe_pct": 2.2, "mae_pct": -0.3},
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    backfill = mod.backfill_clean_baseline_opportunity_rollups(target_date)
    assert backfill["generated_dates"] == [prior_date, target_date]
    assert backfill["failed_dates"] == []
    assert backfill["failure_details"] == []
    report = mod.build_microstructure_reaction_context_report(target_date)
    funnel = report["summary"]["opportunity_exploration_funnel"]

    assert funnel["raw_favorable_event_count"] == 4
    assert funnel["entry_favorable_event_count"] == 3
    assert funnel["holding_or_non_entry_favorable_event_count"] == 1
    assert funnel["unique_entry_opportunity_count"] == 2
    assert funnel["unique_entry_unsubmitted_opportunity_count"] == 2
    assert funnel["first_blocker_counts"] == {"ai_confirmed": 2}
    assert funnel["causal_blocker_attribution_complete"] is True
    assert funnel["outcome_time_exact_join_count"] == 1
    assert funnel["outcome_source_quality_pass_count"] == 1
    assert funnel["outcome_join_status_counts"] == {
        "reference_time_mismatch": 1,
        "time_exact": 1,
    }
    assert funnel["post_observation_outcome_join_complete"] is False
    assert funnel["outcome_source_status"] == "loaded"
    first, second = funnel["opportunities"]
    assert first["observation_event_count"] == 2
    assert first["outcome_join_status"] == "time_exact"
    assert first["forward_horizon_metrics"]["20"]["mfe_pct"] == 2.2
    assert second["outcome_join_status"] == "reference_time_mismatch"
    assert "forward_horizon_metrics" not in second
    assert report["sources"]["missed_entry_counterfactual"] == str(outcome_path)
    cumulative = report["summary"]["clean_baseline_cumulative_opportunity_exploration"]
    assert cumulative["available_source_date_count"] == 2
    assert cumulative["included_date_count"] == 2
    assert cumulative["missing_or_stale_rollup_dates"] == []
    assert cumulative["unique_entry_opportunity_count"] == 3
    # Legacy raw observations remain diagnostics, never current-version EV.
    assert cumulative["outcome_source_quality_pass_count"] == 0
    assert cumulative["outcome_time_exact_join_coverage_pct"] == 66.667
    assert cumulative["outcome_source_quality_pass_coverage_pct"] == 0
    assert cumulative["source_quality_adjusted_ev_pct"] is None
    assert cumulative["sample_floor_met"] is False
    assert cumulative["analysis_status"] == "sample_floor_not_met"
    assert cumulative["runtime_reflection_status"] == "not_applicable_diagnostic"
    assert cumulative["diagnostic_limitations"] == [
        "source_quality_pass_outcome_sample_below_20",
    ]
    assert cumulative["source_quality_exclusion_warnings"] == [
        "exact_attempt_time_outcome_coverage_incomplete",
    ]
    assert cumulative["runtime_apply_required"] is False
    assert (
        report_dir
        / f"microstructure_reaction_context_{target_date}_clean_baseline_cumulative.json"
    ).exists()


def test_cumulative_excludes_missing_rollup_date_without_blocking_valid_window(
    monkeypatch,
):
    valid_date = "2026-07-20"
    missing_date = "2026-07-21"
    valid_rollup = {
        "date": valid_date,
        "tuning_input_allowed": True,
        "outcome_source_quality_pass_count": 20,
        "source_quality_adjusted_ev_evaluable_count": 20,
        "source_quality_adjusted_return_sum_pct": 10.0,
        "primary_horizon_evaluable_count": 20,
        "primary_mfe_sum_pct": 20.0,
        "primary_mae_sum_pct": -4.0,
        "unique_entry_opportunity_count": 20,
        "unique_entry_unsubmitted_opportunity_count": 20,
        "first_blocker_attributed_count": 20,
        "outcome_time_exact_join_count": 20,
        "outcome_source_status": "loaded",
    }
    monkeypatch.setattr(
        mod, "_available_pipeline_dates", lambda target_date: [valid_date, missing_date]
    )
    monkeypatch.setattr(
        mod,
        "_load_daily_opportunity_rollup",
        lambda source_date: valid_rollup if source_date == valid_date else {},
    )

    cumulative = mod._clean_baseline_cumulative_opportunity_exploration(missing_date)

    assert cumulative["loaded_rollup_date_coverage_pct"] == 50.0
    assert cumulative["missing_or_stale_rollup_dates"] == [missing_date]
    assert cumulative["analysis_status"] == "positive_diagnostic_evidence"
    assert cumulative["runtime_reflection_status"] == "not_applicable_diagnostic"
    assert cumulative["runtime_reflection_blockers"] == []
    assert cumulative["source_quality_exclusion_warnings"] == [
        "daily_rollup_missing_or_stale_dates_excluded"
    ]


def test_microstructure_report_emits_full_gap_source_quality_orders(
    tmp_path, monkeypatch
):
    event_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "microstructure_reaction_context"
    event_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    event_path = event_dir / "pipeline_events_2026-07-16.jsonl"
    event_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "stage": "scalp_sim_entry_armed",
                    "stock_code": f"{index:06d}",
                    "fields": {
                        "microstructure_reaction_context_status": "missing",
                        "v_pw_source": "missing",
                        "latest_strength": "-",
                        "trade_volume_1030_1031_vs_15_evaluable_count": 1,
                        "trade_volume_1030_1031_vs_15_mismatch_count": 1,
                        "trade_volume_1030_1031_vs_15_comparison_contract": (
                            "same_tick_comparable"
                        ),
                    },
                }
            )
            for index in range(1, 21)
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_microstructure_reaction_context_report("2026-07-16")

    orders = {item["order_id"]: item for item in report["code_improvement_orders"]}
    assert "order_microstructure_v_pw_full_source_gap" in orders
    assert "order_microstructure_trade_volume_split_contract_mismatch" in orders
    assert all(item["route"] == "instrumentation_order" for item in orders.values())
    assert all(item["runtime_effect"] is False for item in orders.values())
    assert all(item["allowed_runtime_apply"] is False for item in orders.values())


def test_microstructure_report_backfills_vpw_and_classifies_legacy_volume_scope(
    tmp_path, monkeypatch
):
    event_dir = tmp_path / "pipeline_events"
    report_dir = tmp_path / "report" / "microstructure_reaction_context"
    event_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", event_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    event_path = event_dir / "pipeline_events_2026-07-16.jsonl"
    event_path.write_text(
        "\n".join(
            json.dumps(
                {
                    "stage": "scalp_entry_action_decision_snapshot",
                    "stock_code": f"{index:06d}",
                    "fields": {
                        "microstructure_reaction_context_status": "ok",
                        "v_pw_source": "missing",
                        "latest_strength": "88.3",
                        "trade_volume_source_counts": {"1030_1031_sum": 1},
                        "trade_volume_1030_1031_vs_15_evaluable_count": 1,
                        "trade_volume_1030_1031_vs_15_mismatch_count": 1,
                    },
                }
            )
            for index in range(1, 21)
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_microstructure_reaction_context_report("2026-07-16")
    summary = report["summary"]

    assert summary["v_pw_expected_count"] == 20
    assert summary["v_pw_ws_0b_count"] == 20
    assert summary["v_pw_report_provenance_backfilled_count"] == 20
    assert summary["v_pw_missing_count"] == 0
    assert summary["trade_volume_1030_1031_vs_15_mismatch_rate_pct"] == 100.0
    assert summary["trade_volume_1030_1031_vs_15_noncomparable_count"] == 20
    assert summary["trade_volume_1030_1031_vs_15_contract_violation_count"] == 0
    assert report["code_improvement_orders"] == []
