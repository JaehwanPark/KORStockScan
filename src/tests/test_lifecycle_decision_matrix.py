import gzip
import json

from src.engine import lifecycle_decision_matrix as mod


def test_scale_in_bucket_v2_sample_floor_excludes_legacy_rows():
    rows = [
        {
            "runtime_features": {
                "scale_in_applicability": "applied",
                "scale_in_decision_id": f"decision-{idx}",
            },
            "labels": {
                "scale_in_ev_label_version": mod.SCALE_IN_EV_LABEL_VERSION,
                "incremental_notional_ev_pct": 1.2,
                "runtime_authority_ready": False,
            } if idx == 0 else {"profit_rate": 0.5},
            "stage_ev_composite_pct": 0.5,
        }
        for idx in range(mod.SCALE_IN_BUCKET_SAMPLE_FLOOR + 5)
    ]

    bucket = mod._scale_in_bucket_row("arm", "PYRAMID", rows)

    assert bucket["counterfactual_eligible_sample"] == len(rows)
    assert bucket["counterfactual_joined_sample"] == 1
    assert bucket["filled_sample"] == 1
    assert bucket["runtime_authority_ready_sample"] == 0
    assert bucket["counterfactual_method"] == "treatment_path_added_tranche_return"
    assert bucket["runtime_authority_method_required"] == "paired_add_no_add_lifecycle_replay"
    assert bucket["scale_in_ev_coverage_state"] == "v2_partial"
    assert bucket["source_quality_gate"] == "hold_sample"
    assert bucket["recommended_route"] == "hold_sample"
    assert bucket["runtime_authority_ready"] is False


def test_scale_in_rolling_aggregation_uses_only_v2_joined_ev_and_authority_samples():
    legacy = {
        "bucket_key": "PYRAMID",
        "sample": 100,
        "joined_sample": 100,
        "source_quality_adjusted_ev_pct": -5.0,
        "runtime_authority_ready": False,
    }
    v2 = {
        "bucket_key": "PYRAMID",
        "sample": mod.SCALE_IN_BUCKET_SAMPLE_FLOOR,
        "joined_sample": mod.SCALE_IN_BUCKET_SAMPLE_FLOOR,
        "source_quality_adjusted_ev_pct": 1.5,
        "counterfactual_eligible_sample": mod.SCALE_IN_BUCKET_SAMPLE_FLOOR,
        "counterfactual_joined_sample": mod.SCALE_IN_BUCKET_SAMPLE_FLOOR,
        "filled_sample": mod.SCALE_IN_BUCKET_SAMPLE_FLOOR,
        "runtime_authority_ready": True,
        "runtime_authority_ready_sample": mod.SCALE_IN_BUCKET_SAMPLE_FLOOR,
    }

    bucket = mod._aggregate_bucket_rows([legacy, v2], scale_in=True)[0]

    assert bucket["source_quality_adjusted_ev_pct"] == 1.5
    assert bucket["counterfactual_joined_sample"] == mod.SCALE_IN_BUCKET_SAMPLE_FLOOR
    assert bucket["filled_sample"] == mod.SCALE_IN_BUCKET_SAMPLE_FLOOR
    assert bucket["counterfactual_method"] == "treatment_path_added_tranche_return"
    assert bucket["runtime_authority_method_required"] == "paired_add_no_add_lifecycle_replay"
    assert bucket["scale_in_ev_coverage_state"] == "v2_ready"
    assert bucket["runtime_authority_ready"] is True


def test_scale_in_v2_edge_without_runtime_authority_stays_source_only():
    rows = [
        {
            "stage": "scale_in",
            "runtime_features": {
                "scale_in_applicability": "applied",
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_namespace": "PYRAMID",
                "scale_in_execution_arm": "MARKETABLE_OBSERVATION",
            },
            "labels": {
                "scale_in_ev_label_version": mod.SCALE_IN_EV_LABEL_VERSION,
                "incremental_notional_ev_pct": 1.2,
                "runtime_authority_ready": False,
                "profit_rate": 0.5,
            },
            "stage_ev_composite_pct": 0.5,
        }
        for _ in range(mod.SCALE_IN_BUCKET_SAMPLE_FLOOR)
    ]

    attribution = mod._scale_in_bucket_attribution(rows)

    assert attribution["summary"]["edge_bucket_count"] > 0
    assert attribution["summary"]["actionable_bucket_count"] == 0
    assert (
        attribution["summary"]["runtime_authority_blocked_count"]
        == attribution["summary"]["edge_bucket_count"]
    )
    assert attribution["summary"]["runtime_candidate_count"] == 0
    assert attribution["summary"]["workorder_count"] == 0
    blocked = next(
        item
        for item in attribution["runtime_authority_blocked_buckets"]
        if item["bucket_type"] == "arm"
    )
    assert blocked["bucket_type"] == "arm"
    assert blocked["bucket_key"] == "PYRAMID"
    assert blocked["next_route"] == "source_only_keep_collecting_until_paired_add_lifecycle_replay"
    assert blocked["allowed_runtime_apply"] is False


def test_bucket_aggregation_keeps_same_key_separate_by_bucket_type():
    rows = [
        {
            "bucket_type": "arm",
            "bucket_key": "SAME",
            "sample": 3,
            "joined_sample": 3,
            "source_quality_adjusted_ev_pct": 1.0,
        },
        {
            "bucket_type": "blocker_namespace",
            "bucket_key": "SAME",
            "sample": 4,
            "joined_sample": 4,
            "source_quality_adjusted_ev_pct": -1.0,
        },
    ]

    buckets = mod._aggregate_bucket_rows(rows)

    assert len(buckets) == 2
    assert {(item["bucket_type"], item["sample"]) for item in buckets} == {
        ("arm", 3),
        ("blocker_namespace", 4),
    }


def test_rolling_aggregation_excludes_source_quality_blocked_daily_report(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "MATRIX_DIR", tmp_path)
    monkeypatch.setattr(
        mod,
        "load_source_quality_preflight",
        lambda target_date: {
            "status": "pass",
            "tuning_input_allowed": True,
            "allowed_runtime_apply": True,
            "hard_blocking_contract_gap_count": 0,
        },
    )
    sections = {
        name: {"buckets": []}
        for name in (
            "entry_bucket_attribution",
            "submit_bucket_attribution",
            "holding_bucket_attribution",
            "exit_bucket_attribution",
            "scale_in_bucket_attribution",
            "overnight_bucket_attribution",
            "lifecycle_flow_bucket_attribution",
        )
    }
    for source_date, blocked in (("2026-06-11", False), ("2026-06-12", True)):
        payload = {
            "date": source_date,
            "summary": {"total_rows": 1, "source_rows_total": 1, "retained_rows": 1},
            "policy_entries": [],
            "source_quality_preflight_gate": {
                "status": "fail" if blocked else "pass",
                "tuning_input_allowed": not blocked,
                "allowed_runtime_apply": not blocked,
                "hard_blocking_contract_gap_count": int(blocked),
            },
            **sections,
        }
        (tmp_path / f"lifecycle_decision_matrix_{source_date}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    report = mod._aggregate_existing_daily_lifecycle_reports(
        "2026-06-12",
        ["2026-06-11", "2026-06-12"],
        window_policy="rolling5d",
        output_suffix="rolling5d",
    )

    assert report is not None
    assert report["summary"]["source_dates"] == ["2026-06-11"]
    assert report["summary"]["excluded_daily_report_dates"] == {
        "2026-06-12": "daily_lifecycle_source_quality_preflight_blocked"
    }
    assert report["summary"]["unavailable_daily_report_dates"] == []


def test_scale_in_counterfactual_enrichment_requires_exact_decision_id():
    rows = [
        {
            "stage": "scale_in",
            "candidate_id": "candidate-1",
            "runtime_features": {
                "sim_record_id": "sim-1",
                "scale_in_arm": "PYRAMID",
                "scale_in_decision_id": "decision-exact",
                "scale_in_execution_arm": "MARKETABLE_OBSERVATION",
            },
            "labels": {},
        },
        {
            "stage": "scale_in",
            "candidate_id": "candidate-2",
            "runtime_features": {
                "sim_record_id": "sim-1",
                "scale_in_arm": "PYRAMID",
                "scale_in_decision_id": "",
            },
            "labels": {},
        },
    ]
    labels = {
        "decision-exact": {
            "scale_in_ev_label_version": mod.SCALE_IN_EV_LABEL_VERSION,
            "incremental_notional_ev_pct": 1.0,
        }
    }

    assert mod._enrich_scale_in_rows_with_counterfactual_ev(rows, labels) == 1
    assert rows[0]["labels"]["incremental_notional_ev_pct"] == 1.0
    assert "incremental_notional_ev_pct" not in rows[1]["labels"]


def test_scale_in_counterfactual_enrichment_rejects_passive_arm():
    rows = [
        {
            "stage": "scale_in",
            "runtime_features": {
                "scale_in_decision_id": "decision-1",
                "scale_in_execution_arm": "PASSIVE_BASELINE",
            },
            "labels": {},
        },
        {
            "stage": "scale_in",
            "runtime_features": {
                "scale_in_decision_id": "decision-1",
                "scale_in_execution_arm": "MARKETABLE_OBSERVATION",
            },
            "labels": {},
        },
    ]
    labels = {
        "decision-1": {
            "scale_in_ev_label_version": mod.SCALE_IN_EV_LABEL_VERSION,
            "incremental_notional_ev_pct": 1.0,
        }
    }

    assert mod._enrich_scale_in_rows_with_counterfactual_ev(rows, labels) == 1
    assert rows[0]["labels"] == {}
    assert rows[1]["labels"]["incremental_notional_ev_pct"] == 1.0


def test_scale_in_label_report_authority_does_not_upgrade_row(monkeypatch):
    monkeypatch.setattr(
        mod,
        "_load_json",
        lambda path: {
            "scale_in_ev_label_version": mod.SCALE_IN_EV_LABEL_VERSION,
            "runtime_authority_ready": True,
            "rows": [
                {
                    "scale_in_decision_id": "decision-treatment-only",
                    "runtime_ev_eligible": True,
                    "runtime_authority_ready": False,
                    "horizons": {"final": {"incremental_notional_ev_pct": 1.2}},
                }
            ],
        },
    )

    labels = mod._load_scale_in_counterfactual_labels("2026-06-12")

    assert labels["decision-treatment-only"]["runtime_authority_ready"] is False


def test_complete_lifecycle_without_scale_in_is_not_applicable_and_keeps_ev():
    rows = [
        {"stage": "entry", "candidate_id": "c1", "runtime_features": {}, "labels": {}},
        {"stage": "submit", "candidate_id": "c1", "runtime_features": {}, "labels": {}},
        {
            "stage": "holding",
            "candidate_id": "c1",
            "runtime_features": {},
            "labels": {"profit_rate": 1.4},
            "stage_ev_composite_pct": 1.4,
        },
        {
            "stage": "exit",
            "candidate_id": "c1",
            "runtime_features": {},
            "labels": {"profit_rate": 1.4},
            "stage_ev_composite_pct": 1.4,
        },
    ]

    flow = mod._flow_record("c1", "exact_sim_record_id", rows)

    assert flow["stage_completion_state"] == "complete"
    assert flow["source_quality_gate"] == "pass"
    assert flow["scale_in_applicability"] == "not_applicable"
    assert flow["scale_in_incremental_label_required"] is False
    assert flow["source_quality_adjusted_ev_pct"] is not None


def test_complete_lifecycle_with_unfilled_scale_in_is_considered_not_applied():
    rows = [
        {"stage": "entry", "runtime_features": {}, "labels": {}},
        {"stage": "submit", "runtime_features": {}, "labels": {}},
        {"stage": "holding", "runtime_features": {}, "labels": {"profit_rate": 0.5}, "stage_ev_composite_pct": 0.5},
        {
            "stage": "scale_in",
            "runtime_features": {"scale_in_applicability": "considered_not_applied"},
            "labels": {"profit_rate": 0.5},
            "stage_ev_composite_pct": 0.5,
        },
        {"stage": "exit", "runtime_features": {}, "labels": {"profit_rate": 0.5}, "stage_ev_composite_pct": 0.5},
    ]

    flow = mod._flow_record("c2", "exact_sim_record_id", rows)

    assert flow["stage_completion_state"] == "complete"
    assert flow["scale_in_applicability"] == "considered_not_applied"
    assert flow["scale_in_incremental_label_required"] is False


def test_lifecycle_bucket_rows_explain_unknown_source_field_causes():
    rows = [
        {
            "runtime_features": {"ai_score": 67},
            "labels": {"profit_rate": 0.4},
            "stage_ev_composite_pct": 0.4,
        }
        for _ in range(3)
    ]

    entry = mod._entry_bucket_row("liquidity_bucket", "liquidity_unknown", rows)
    scale = mod._scale_in_bucket_row("blocker_reason", "blocker_reason_unknown", rows)

    assert entry["unknown_reason_counts"]["missing_source_field"] == 1
    assert entry["source_field_coverage"]["liquidity_bucket"]["source_fields"] == [
        "runtime_features.liquidity_bucket",
        "runtime_features.liquidity_guard_action",
        "runtime_features.liquidity_guard_reason",
        "runtime_features.sim_pre_submit_liquidity_guard_action",
        "runtime_features.sim_pre_submit_liquidity_reason",
        "runtime_features.sim_liquidity_value",
        "runtime_features.sim_min_liquidity",
    ]
    assert scale["unknown_reason_counts"]["missing_source_field"] == 1
    assert scale["recommended_resolution"] == "emit_or_backfill_source_field"


def test_lifecycle_entry_unknown_bucket_is_source_quality_blocker_not_edge_candidate():
    rows = [
        {
            "stage": "entry",
            "source_stage": "scalp_entry_action_decision_snapshot",
            "runtime_features": {
                "ai_score": None,
                "chosen_action": "NO_BUY_AI",
                "stale_bucket": "stale_unknown",
                "liquidity_bucket": "liquidity_high",
                "overbought_bucket": "overbought_unknown",
            },
            "labels": {"profit_rate": 1.2},
            "stage_ev_composite_pct": 1.2,
        }
        for _ in range(mod.ENTRY_BUCKET_SAMPLE_FLOOR)
    ]

    row = mod._entry_bucket_row("stale_bucket", "stale_unknown", rows)
    attribution = mod._entry_bucket_attribution(rows)

    assert row["source_quality_gate"] == "source_quality_blocker"
    assert row["recommended_route"] == "source_quality_workorder"
    assert attribution["summary"]["actionable_bucket_count"] == 0
    assert attribution["summary"]["runtime_candidate_count"] == 0
    assert attribution["summary"]["source_quality_blocked_bucket_count"] > 0
    assert any(
        item["reason"] == "unknown_bucket_source_quality_blocker"
        for item in attribution["code_improvement_workorders"]
    )


def test_lifecycle_entry_exit_rule_unknown_is_label_not_applicable():
    rows = [
        {
            "stage": "entry",
            "runtime_features": {"ai_score": 67, "chosen_action": "WAIT_REQUOTE"},
            "labels": {"profit_rate": 0.4},
            "stage_ev_composite_pct": 0.4,
        }
        for _ in range(12)
    ]

    entry = mod._entry_bucket_row("exit_rule", "exit_unknown", rows)

    assert entry["unknown_reason_counts"] == {"entry_label_not_applicable": 1}
    assert entry["recommended_resolution"] == "entry_label_not_applicable"


def test_lifecycle_holding_started_marks_action_and_held_not_applicable():
    row = {
        "stage": "holding",
        "source_stage": "scalp_sim_holding_started",
        "runtime_features": {"profit_rate_live": 0.4},
        "labels": {"profit_rate": 0.4},
        "stage_ev_composite_pct": 0.4,
    }

    features = mod._holding_bucket_features(row)
    bucket_id = mod._holding_combo_bucket_id(row)
    attribution = mod._holding_bucket_attribution([row for _ in range(5)])

    assert features["holding_action"] == "holding_action_not_applicable_at_start"
    assert features["held_bucket"] == "held_not_applicable_at_start"
    assert "holding_action_unknown" not in bucket_id
    assert "held_unknown" not in bucket_id
    assert all(
        item["recommended_route"] != "source_quality_workorder"
        for item in attribution["code_improvement_workorders"]
    )


def test_lifecycle_holding_started_missing_profit_is_not_applicable_not_workorder():
    row = {
        "stage": "holding",
        "source_stage": "scalp_sim_holding_started",
        "runtime_features": {},
        "labels": {},
        "stage_ev_composite_pct": None,
    }

    features = mod._holding_bucket_features(row)
    attribution = mod._holding_bucket_attribution([row])

    assert features["holding_action"] == "holding_action_not_applicable_at_start"
    assert features["profit_band"] == "profit_not_applicable_at_start"
    assert features["held_bucket"] == "held_not_applicable_at_start"
    assert "profit_profit_unk" not in mod._holding_combo_bucket_id(row)
    assert all(
        item["recommended_route"] != "source_quality_workorder"
        for item in attribution["code_improvement_workorders"]
    )


def test_lifecycle_entry_bucket_uses_pre_submit_guard_fields_when_explicit_unknown():
    row = {
        "stage": "entry",
        "source_stage": "scalp_entry_action_decision_snapshot",
        "runtime_features": {
            "ai_score": 67,
            "chosen_action": "WAIT_REQUOTE",
            "liquidity_bucket": "liquidity_unknown",
            "sim_pre_submit_liquidity_guard_action": "WOULD_PASS",
            "sim_pre_submit_liquidity_reason": "liquidity_ok",
            "overbought_bucket": "overbought_unknown",
            "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
            "sim_pre_submit_overbought_reason": "overbought_ok",
        },
        "labels": {"profit_rate": 0.4},
        "stage_ev_composite_pct": 0.4,
    }

    features = mod._entry_bucket_features(row)

    assert features["liquidity_bucket"] == "liquidity_ok"
    assert features["overbought_bucket"] == "overbought_ok"


def test_lifecycle_flow_entry_bucket_uses_submit_guard_dimensions_as_fallback():
    rows = [
        {
            "candidate_id": "FLOW-1",
            "stock_code": "000001",
            "event_time": "2026-05-20T09:10:00+09:00",
            "stage": "entry",
            "source_stage": "entry",
            "runtime_features": {
                "ai_score": 67,
                "chosen_action": "WAIT_REQUOTE",
                "liquidity_bucket": "liquidity_unknown",
                "overbought_bucket": "overbought_unknown",
            },
            "labels": {"profit_rate": 0.4},
            "stage_ev_composite_pct": 0.4,
        },
        {
            "candidate_id": "FLOW-1",
            "stock_code": "000001",
            "event_time": "2026-05-20T09:10:01+09:00",
            "stage": "submit",
            "source_stage": "scalp_sim_pre_submit_liquidity_guard_would_pass",
            "runtime_features": {
                "sim_pre_submit_liquidity_guard_action": "WOULD_PASS",
                "sim_pre_submit_liquidity_reason": "liquidity_ok",
                "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
                "sim_pre_submit_overbought_reason": "overbought_ok",
            },
            "labels": {"profit_rate": 0.4},
            "stage_ev_composite_pct": 0.4,
        },
        {
            "candidate_id": "FLOW-1",
            "stock_code": "000001",
            "event_time": "2026-05-20T09:10:02+09:00",
            "stage": "holding",
            "source_stage": "scalp_sim_holding_snapshot",
            "runtime_features": {"chosen_action": "HOLD", "profit_rate_live": 0.4, "held_sec": 60},
            "labels": {"profit_rate": 0.4},
            "stage_ev_composite_pct": 0.4,
        },
        {
            "candidate_id": "FLOW-1",
            "stock_code": "000001",
            "event_time": "2026-05-20T09:10:03+09:00",
            "stage": "exit",
            "source_stage": "scalp_sim_sell_order_assumed_filled",
            "runtime_features": {"chosen_action": "SELL"},
            "labels": {"profit_rate": 0.4, "exit_rule": "trailing_take_profit"},
            "stage_ev_composite_pct": 0.4,
        },
    ]

    attribution = mod._lifecycle_flow_bucket_attribution(rows)
    flow = attribution["flows"][0]

    assert "liquidity_liquidity_ok" in flow["entry_bucket_id"]
    assert "overbought_overbo" in flow["entry_bucket_id"]
    assert "liquidity_unknown" not in flow["entry_bucket_id"]
    assert "overbought_unknown" not in flow["entry_bucket_id"]


def test_lifecycle_partial_exit_marks_outcome_not_applicable():
    row = {
        "stage": "exit",
        "source_stage": "scalp_sim_partial_sell_order_assumed_filled",
        "runtime_features": {},
        "labels": {
            "exit_rule": "scalp_sim_panic_lifecycle_partial_exit",
            "profit_rate": -0.4,
        },
        "stage_ev_composite_pct": -0.4,
    }

    features = mod._exit_bucket_features(row)
    bucket_id = mod._exit_combo_bucket_id(row)
    attribution = mod._exit_bucket_attribution([row for _ in range(5)])

    assert features["exit_outcome"] == "outcome_not_applicable_partial_exit"
    assert "outcome_unknown" not in bucket_id
    assert all(
        item["recommended_route"] != "source_quality_workorder"
        for item in attribution["code_improvement_workorders"]
    )


def test_lifecycle_overnight_decision_marks_missing_action_not_applicable():
    row = {
        "stage": "holding",
        "source_stage": "scalp_sim_overnight_decision",
        "runtime_features": {
            "chosen_action": "holding_action_unknown",
            "profit_rate_live": -1.0,
            "held_sec": 2400,
        },
        "labels": {"profit_rate": -1.0},
        "stage_ev_composite_pct": -1.0,
    }

    features = mod._holding_bucket_features(row)
    bucket_id = mod._holding_combo_bucket_id(row)

    assert features["holding_action"] == "holding_action_not_applicable_overnight_decision"
    assert "holding_action_unknown" not in bucket_id


def test_lifecycle_overnight_decision_uses_overnight_action_when_ai_action_none():
    row = {
        "stage": "holding",
        "source_stage": "scalp_sim_overnight_decision",
        "runtime_features": {
            "ai_action": "None",
            "overnight_action": "SELL_TODAY",
            "profit_rate_live": -1.0,
            "held_sec": 2400,
        },
        "labels": {"profit_rate": -1.0},
        "stage_ev_composite_pct": -1.0,
    }

    assert mod._holding_bucket_features(row)["holding_action"] == "SELL_TODAY"


def test_lifecycle_partial_exit_treats_string_none_outcome_as_missing():
    row = {
        "stage": "exit",
        "source_stage": "scalp_sim_partial_sell_order_assumed_filled",
        "runtime_features": {},
        "labels": {
            "exit_rule": "scalp_sim_panic_lifecycle_partial_exit",
            "sim_post_sell_outcome": "None",
            "profit_rate": 0.4,
        },
        "stage_ev_composite_pct": 0.4,
    }

    assert mod._exit_bucket_features(row)["exit_outcome"] == "outcome_not_applicable_partial_exit"


def test_lifecycle_entry_score_bands_keep_score60_floor_granular():
    assert mod._entry_score_band(59) == "score_lt60"
    assert mod._entry_score_band(61) == "score_60_62"
    assert mod._entry_score_band(64) == "score_63_65"
    assert mod._entry_score_band(67) == "score_66_69"
    assert mod._entry_score_band(70) == "score_70p"


def test_lifecycle_decision_matrix_reads_gzip_pipeline_events(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", tmp_path / "post_sell")
    pipeline_dir.mkdir(parents=True)
    with gzip.open(pipeline_dir / "pipeline_events_2026-05-20.jsonl.gz", "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "stage": "scalp_sim_holding_started",
                    "fields": {
                        "simulation_book": "scalp_ai_buy_all",
                        "sim_record_id": "SIM-1",
                        "actual_order_submitted": "False",
                        "broker_order_forbidden": "True",
                        "ai_action": "HOLD",
                        "ai_score": "72",
                    },
                }
            )
            + "\n"
        )

    rows, meta = mod._load_scalp_sim_holding_rows("2026-05-20")

    assert len(rows) == 1
    assert meta["stage_counts"]["scalp_sim_holding_started"] == 1


def test_lifecycle_decision_matrix_excludes_synthetic_scalp_sim_events_from_authority_rows(
    tmp_path, monkeypatch
):
    pipeline_dir = tmp_path / "pipeline_events"
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    pipeline_dir.mkdir(parents=True)
    rows = [
        {
            "stage": "scalp_sim_buy_order_assumed_filled",
            "stock_code": "123456",
            "stock_name": "TEST",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-SYNTH",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            "emitted_at": "2026-06-15T10:00:00+09:00",
        },
        {
            "stage": "scalp_sim_buy_order_assumed_filled",
            "stock_code": "011070",
            "stock_name": "LG이노텍",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-REAL",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            "emitted_at": "2026-06-15T10:01:00+09:00",
        },
        {
            "stage": "scalp_sim_scale_in_order_assumed_filled",
            "stock_code": "123456",
            "stock_name": "TEST",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-SYNTH-SCALE",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            "emitted_at": "2026-06-15T10:02:00+09:00",
        },
        {
            "stage": "scalp_sim_scale_in_order_assumed_filled",
            "stock_code": "011070",
            "stock_name": "LG이노텍",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-REAL-SCALE",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
            "emitted_at": "2026-06-15T10:03:00+09:00",
        },
    ]
    with (pipeline_dir / "pipeline_events_2026-06-15.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    submit_rows, submit_meta = mod._load_scalp_sim_submit_rows("2026-06-15")

    assert [row["stock_code"] for row in submit_rows] == ["011070"]
    assert submit_meta["stage_counts"] == {"scalp_sim_buy_order_assumed_filled": 1}
    assert submit_meta["synthetic_excluded_count"] == 2
    scale_rows, scale_meta = mod._load_scalp_sim_scale_in_rows("2026-06-15")
    assert [row["stock_code"] for row in scale_rows] == ["011070"]
    assert scale_meta["filled_events"] == 1
    assert scale_meta["synthetic_excluded_count"] == 2


def test_lifecycle_submit_bucket_attribution_is_source_only_and_surfaces_gaps():
    rows = [
        {
            "stage": "submit",
            "source_stage": "scalp_sim_buy_order_virtual_pending",
            "runtime_features": {
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "quote_age_ms": 1200,
                "would_limit_fill": True,
                "price_resolution_bucket": "passive_limit",
            },
            "labels": {"profit_rate": 0.2},
            "stage_ev_composite_pct": 0.2,
        },
        {
            "stage": "submit",
            "source_stage": "scalp_sim_entry_submit_revalidation_block",
            "runtime_features": {
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "entry_submit_revalidation_block": "stale_context_or_quote",
                "quote_age_ms": 12000,
                "would_limit_fill": False,
                "price_resolution_bucket": "stale_block",
            },
            "labels": {"profit_rate": -0.4},
            "stage_ev_composite_pct": -0.4,
        },
        {
            "stage": "submit",
            "source_stage": "scalp_sim_buy_order_assumed_filled",
            "runtime_features": {
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "quote_age_ms": 500,
                "would_limit_fill": True,
                "price_resolution_bucket": "assumed_fill",
            },
            "labels": {"profit_rate": 0.1},
            "stage_ev_composite_pct": 0.1,
        },
    ]

    attribution = mod._submit_bucket_attribution(rows)

    assert attribution["decision_authority"] == "adm_ldm_submit_bucket_attribution_source_only"
    assert attribution["runtime_effect"] is False
    assert attribution["allowed_runtime_apply"] is False
    assert "broker_order_submit" in attribution["forbidden_uses"]
    assert attribution["summary"]["submit_rows"] == 3
    assert attribution["summary"]["bucket_count"] > 0
    assert attribution["runtime_approval_candidates"] == []


def test_lifecycle_submit_bucket_attribution_creates_contract_gap_workorders():
    rows = [
        {
            "stage": "submit",
            "source_stage": "scalp_sim_buy_order_virtual_pending",
            "runtime_features": {},
            "labels": {},
            "stage_ev_composite_pct": None,
        }
    ]

    attribution = mod._submit_bucket_attribution(rows)

    assert attribution["summary"]["contract_gap_count"] >= 1
    assert {
        item["workorder_id"]
        for item in attribution["code_improvement_workorders"]
    } >= {
        "order_entry_post_submit_contract_gap_review",
        "order_entry_broker_receipt_contract_gap_review",
        "order_entry_fill_quality_contract_gap_review",
        "order_entry_telegram_post_submit_contract_gap_review",
        "order_entry_sim_submit_path_bucket_instrumentation",
    }


def test_lifecycle_submit_bucket_attribution_surfaces_post_submit_join_gap():
    rows = [
        {
            "stage": "submit",
            "source_stage": "order_bundle_submitted",
            "runtime_features": {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "stock_code": "011070",
                "order_price": 10049,
            },
            "labels": {"profit_rate": None},
            "stage_ev_composite_pct": None,
        }
    ]

    attribution = mod._submit_bucket_attribution(rows)

    assert attribution["summary"]["real_submitted_row_count"] == 1
    assert attribution["summary"]["missing_broker_order_key_count"] == 1
    assert attribution["summary"]["missing_broker_order_key_rate"] == 1.0
    assert attribution["summary"]["post_submit_provenance_join_gap"] is True
    assert attribution["summary"]["post_submit_provenance_join_gap_raw"] is True
    assert {
        item["workorder_id"]
        for item in attribution["code_improvement_workorders"]
    } >= {"order_entry_post_submit_provenance_join_gap"}


def test_lifecycle_submit_bucket_attribution_surfaces_bot_history_backfill_candidates(tmp_path, monkeypatch):
    bot_history = tmp_path / "bot_history.log"
    bot_history.write_text(
        "\n".join(
            [
                "[2026-06-11 12:34:55] 📩 [WS 주문상태] 131970 | 주문번호: '0049916' | 상태: '접수' | 구분: '+매수'",
                "[2026-06-11 12:35:31] 📩 [WS 주문상태] 131970 | 주문번호: '0049962' | 상태: '접수' | 구분: '매수취소'",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "BOT_HISTORY_LOG", bot_history)
    rows = [
        {
            "stage": "submit",
            "source_stage": "order_bundle_submitted",
            "stock_code": "131970",
            "event_time": "2026-06-11T12:34:54",
            "runtime_features": {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
            },
            "labels": {"profit_rate": None},
            "stage_ev_composite_pct": None,
        }
    ]

    attribution = mod._submit_bucket_attribution(rows)
    summary = attribution["summary"]

    assert summary["post_submit_provenance_join_gap_raw"] is True
    assert summary["post_submit_provenance_join_gap"] is False
    assert summary["bot_history_broker_order_key_backfill_candidate_count"] == 1
    assert summary["bot_history_broker_order_key_backfill_full_coverage"] is True
    assert summary["bot_history_broker_order_key_exact_mapping_count"] == 1
    assert summary["bot_history_broker_order_key_exact_mapping_full_coverage"] is True
    assert summary["post_submit_provenance_join_resolution"] == "resolved_by_exact_bot_history_submit_time_mapping"
    candidate = summary["bot_history_broker_order_key_backfill_candidates"][0]
    assert candidate["best_candidate"]["broker_order_no"] == "0049916"
    assert candidate["best_candidate"]["delta_sec"] == 1
    assert candidate["exact_submit_time_mapping"] is True


def test_lifecycle_submit_bucket_attribution_keeps_ambiguous_bot_history_backfill_open(tmp_path, monkeypatch):
    bot_history = tmp_path / "bot_history.log"
    bot_history.write_text(
        "\n".join(
            [
                "[2026-06-11 12:34:55] 📩 [WS 주문상태] 131970 | 주문번호: '0049916' | 상태: '접수' | 구분: '+매수'",
                "[2026-06-11 12:35:12] 📩 [WS 주문상태] 131970 | 주문번호: '0049917' | 상태: '접수' | 구분: '+매수'",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "BOT_HISTORY_LOG", bot_history)
    rows = [
        {
            "stage": "submit",
            "source_stage": "order_bundle_submitted",
            "stock_code": "131970",
            "event_time": "2026-06-11T12:34:54",
            "runtime_features": {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
            },
            "labels": {"profit_rate": None},
            "stage_ev_composite_pct": None,
        }
    ]

    summary = mod._submit_bucket_attribution(rows)["summary"]

    assert summary["bot_history_broker_order_key_backfill_candidate_count"] == 1
    assert summary["bot_history_broker_order_key_backfill_full_coverage"] is True
    assert summary["bot_history_broker_order_key_exact_mapping_count"] == 0
    assert summary["bot_history_broker_order_key_exact_mapping_full_coverage"] is False
    assert summary["post_submit_provenance_join_resolution"] == "candidate_backfill_available_but_exact_mapping_required"
    candidate = summary["bot_history_broker_order_key_backfill_candidates"][0]
    assert candidate["candidate_count"] == 2
    assert candidate["exact_submit_time_mapping"] is False


def test_lifecycle_submit_bucket_attribution_does_not_gap_when_broker_key_present():
    rows = [
        {
            "stage": "submit",
            "source_stage": "order_bundle_submitted",
            "runtime_features": {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "broker_order_no": "0046858",
                "order_response_ord_no": "0046858",
                "submit_attempt_id": "011070:1781160000000:0046858",
            },
            "labels": {"profit_rate": None},
            "stage_ev_composite_pct": None,
        }
    ]

    attribution = mod._submit_bucket_attribution(rows)

    assert attribution["summary"]["real_submitted_row_count"] == 1
    assert attribution["summary"]["missing_broker_order_key_count"] == 0
    assert attribution["summary"]["missing_broker_order_key_rate"] == 0.0
    assert attribution["summary"]["post_submit_provenance_join_gap_raw"] is False
    assert attribution["summary"]["post_submit_provenance_join_gap"] is False
    assert "order_entry_post_submit_provenance_join_gap" not in {
        item["workorder_id"]
        for item in attribution["code_improvement_workorders"]
    }


def test_lifecycle_submit_bucket_attribution_accepts_top_level_order_keys():
    rows = [
        {
            "stage": "submit",
            "source_stage": "order_bundle_submitted",
            "ord_no": "0046858",
            "order_response_ord_no": "0046858",
            "runtime_features": {},
            "labels": {"profit_rate": None},
            "stage_ev_composite_pct": None,
        }
    ]

    attribution = mod._submit_bucket_attribution(rows)

    assert attribution["summary"]["real_submitted_row_count"] == 1
    assert attribution["summary"]["missing_broker_order_key_count"] == 0
    assert attribution["summary"]["post_submit_provenance_join_gap_raw"] is False
    assert attribution["summary"]["post_submit_provenance_join_gap"] is False


def test_lifecycle_submit_bucket_attribution_normalizes_post_submit_contract_fields():
    rows = [
        {
            "stage": "submit",
            "source_stage": "order_bundle_submitted",
            "actual_order_submitted": True,
            "ord_no": "0046858",
            "qty": 3,
            "submitted_order_price": 11200,
            "strategy": "scalping",
            "runtime_features": {
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "resolved_order_price": 11200,
                "limit_price": 11200,
            },
            "labels": {"profit_rate": None},
            "stage_ev_composite_pct": None,
        }
    ]

    attribution = mod._submit_bucket_attribution(rows)
    gaps = {
        item["gap_type"]
        for item in attribution["post_submit_contract_gaps"]
    }

    assert attribution["summary"]["contract_gap_count"] == 0
    assert "broker_receipt_contract_gap" not in gaps
    assert "fill_quality_contract_gap" not in gaps
    assert "post_submit_contract_gap" not in gaps
    assert "telegram_post_submit_contract_gap" not in gaps
    assert "source_taxonomy_contract_gap" not in gaps


def test_lifecycle_submit_unknown_bucket_is_source_quality_blocker():
    rows = [
        {
            "stage": "submit",
            "source_stage": "scalp_sim_buy_order_virtual_pending",
            "runtime_features": {
                "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
                "sim_pre_submit_overbought_reason": "overbought_unknown",
            },
            "labels": {"profit_rate": 0.5},
            "stage_ev_composite_pct": 0.5,
        }
        for _ in range(mod.SUBMIT_BUCKET_SAMPLE_FLOOR)
    ]

    bucket = mod._submit_bucket_row("overbought_bucket", "overbought_unknown", rows)

    assert bucket["source_quality_gate"] == "source_quality_blocker"
    assert bucket["recommended_route"] == "source_quality_workorder"
    assert bucket["allowed_runtime_apply"] is False


def test_lifecycle_submit_bucket_attribution_buckets_sim_pre_submit_guards():
    rows = [
        {
            "stage": "submit",
            "source_stage": "scalp_sim_pre_submit_liquidity_guard_would_block",
            "runtime_features": {
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "sim_submit_path_observation_only",
                "sim_pre_submit_liquidity_guard_action": "WOULD_BLOCK",
                "sim_pre_submit_liquidity_reason": "below_min_liquidity",
                "sim_liquidity_value": 100_000_000,
                "sim_min_liquidity": 500_000_000,
                "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
                "sim_pre_submit_overbought_reason": "overbought_ok",
                "latency_state": "DANGER",
                "latency_reason": "scalp_live_simulator",
                "quote_age_ms": 200,
                "would_limit_fill": True,
                "limit_price": 10_000,
                "price_below_bid_bps": 4,
                "sim_record_id": "SIM-1",
            },
            "labels": {"profit_rate": 0.2},
            "stage_ev_composite_pct": 0.2,
        },
        {
            "stage": "submit",
            "source_stage": "scalp_sim_pre_submit_liquidity_guard_would_pass",
            "runtime_features": {
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "sim_pre_submit_liquidity_guard_action": "WOULD_PASS",
                "sim_pre_submit_liquidity_reason": "liquidity_ok",
                "sim_liquidity_value": 800_000_000,
                "sim_min_liquidity": 500_000_000,
                "sim_pre_submit_overbought_guard_action": "WOULD_PASS",
                "sim_pre_submit_overbought_reason": "overbought_ok",
                "latency_state": "SAFE",
                "latency_reason": "scalp_live_simulator",
                "quote_age_ms": 200,
                "would_limit_fill": True,
                "limit_price": 10_000,
                "price_below_bid_bps": 0,
                "sim_record_id": "SIM-2",
            },
            "labels": {"profit_rate": 0.1},
            "stage_ev_composite_pct": 0.1,
        },
        {
            "stage": "submit",
            "source_stage": "pre_submit_liquidity_guard_block",
            "runtime_features": {
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "liquidity_guard_action": "BLOCK",
                "liquidity_guard_reason": "below_min_liquidity",
                "liquidity_value": 100_000_000,
                "min_liquidity": 500_000_000,
                "overbought_guard_action": "PASS",
                "overbought_guard_reason": "overbought_ok",
                "latency_state": "SAFE",
            },
            "labels": {"profit_rate": 0.0},
            "stage_ev_composite_pct": 0.0,
        },
    ]

    attribution = mod._submit_bucket_attribution(rows)
    bucket_keys = {(item["bucket_type"], item["bucket_key"]) for item in attribution["buckets"]}

    assert ("liquidity_guard_action", "would_block") in bucket_keys
    assert ("overbought_guard_action", "would_pass") in bucket_keys
    assert ("liquidity_bucket", "below_min_liquidity") in bucket_keys
    assert ("liquidity_bucket", "liquidity_ok") in bucket_keys
    assert ("latency_state", "danger") in bucket_keys
    assert (
        "order_entry_sim_submit_path_bucket_instrumentation"
        not in {item["workorder_id"] for item in attribution["code_improvement_workorders"]}
    )


def test_lifecycle_matrix_builder_separates_runtime_features_and_labels(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    entry_dir.mkdir(parents=True)
    post_sell_dir.mkdir(parents=True)
    monitor_dir.mkdir(parents=True)
    pipeline_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    examples = [
        {
            "candidate_id": f"cand-{idx}",
            "stock_code": f"000{idx:03d}",
            "event_time": "2026-05-18T09:01:00+09:00",
            "stage": "scalp_entry_action_decision_snapshot",
            "chosen_action": "WAIT_REQUOTE",
            "ai_score": 67 + (idx % 3),
            "ai_action": "WAIT",
            "mfe_10m_pct": 1.2,
            "mae_10m_pct": -0.3,
            "close_10m_pct": 0.8,
            "outcome_joined": True,
        }
        for idx in range(25)
    ]
    (entry_dir / "scalp_entry_action_decision_matrix_2026-05-18.json").write_text(
        json.dumps({"examples": examples}, ensure_ascii=False),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-18")

    assert report["summary"]["total_rows"] == 25
    assert report["summary"]["joined_rows"] == 25
    assert "ai_score" in report["runtime_feature_keys"]
    assert "mfe_10m_pct" not in report["runtime_feature_keys"]
    assert "mfe_10m_pct" in report["label_keys"]
    assert report["examples"][0]["runtime_features"]["ai_score"] >= 67
    assert "mfe_10m_pct" not in report["examples"][0]["runtime_features"]
    assert "mfe_10m_pct" in report["examples"][0]["labels"]
    assert report["fixed_threshold_contract"]["roles"]["baseline_prior"]
    assert any(item["stage"] == "entry" and item["source_quality_gate"] == "pass" for item in report["policy_entries"])
    assert (matrix_dir / "lifecycle_decision_matrix_2026-05-18.json").exists()
    assert (matrix_dir / "lifecycle_decision_matrix_2026-05-18.md").exists()


def test_lifecycle_matrix_excludes_pre_clean_baseline_source_dates(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (matrix_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "clean_baseline_policy",
        lambda: {
            "enabled": True,
            "clean_tuning_baseline_date": "2026-06-04",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
    )

    report = mod.build_lifecycle_decision_matrix_report(
        "2026-06-04",
        start_date="2026-06-02",
        end_date="2026-06-04",
    )

    assert report["summary"]["source_dates"] == ["2026-06-04"]
    assert report["summary"]["clean_baseline_excluded_source_dates"] == ["2026-06-02", "2026-06-03"]
    assert "clean_tuning_baseline_excluded_source_dates" in report["warnings"]
    assert report["runtime_effect"] is False


def test_lifecycle_matrix_prefers_entry_adm_rows_and_has_no_policy_cap(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    rows = [
        {
            "candidate_id": f"cand-{idx}",
            "stock_code": f"{idx:06d}",
            "event_time": "2026-05-20T09:01:00+09:00",
            "stage": "scalp_entry_action_decision_snapshot",
            "chosen_action": "BUY_NOW",
            "ai_score": 80,
            "profit_rate": 0.3,
            "mfe_10m_pct": 0.5,
            "mae_10m_pct": -0.1,
            "close_10m_pct": 0.2,
            "outcome_joined": True,
        }
        for idx in range(2101)
    ]
    (entry_dir / "scalp_entry_action_decision_matrix_2026-05-20.json").write_text(
        json.dumps({"rows": rows, "examples": rows[:1]}, ensure_ascii=False),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-20")

    assert report["sources"]["entry"]["source_field"] == "rows"
    assert report["sources"]["entry"]["source_rows"] == 2101
    assert report["summary"]["source_rows_total"] == 2101
    assert report["summary"]["retained_rows"] == 2101
    assert report["summary"]["dropped_rows_by_source"] == {}
    assert report["policy_entries"][0]["stage"] == "entry"
    assert report["policy_entries"][0]["sample"] == 2101


def test_lifecycle_matrix_ingests_scalp_sim_submit_and_holding_rows(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    common_fields = {
        "simulation_book": "scalp_ai_buy_all",
        "simulated_order": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "sim_observation_only",
        "runtime_effect": False,
        "sim_record_id": "SIM-1",
        "entry_adm_candidate_id": "ADM-1",
        "bucket_directed_sim_probe": True,
        "lifecycle_bucket_match_status": "matched",
        "lifecycle_bucket_source_bucket_id": "lifecycle_flow:combo_lifecycle_flow:test:abc123",
        "lifecycle_bucket_bucket_id": "lifecycle_flow:combo_lifecycle_flow:test",
        "lifecycle_bucket_classification_state": "lifecycle_flow_sim_probe_candidate",
        "lifecycle_bucket_source_bucket_kind": "lifecycle_flow_sim_probe_policy",
    }
    events = [
        {
            "stage": "scalp_sim_buy_order_virtual_pending",
            "stock_code": "000001",
            "emitted_at": "2026-05-20T09:10:00+09:00",
            "fields": {**common_fields, "best_ask": "1000", "would_limit_fill": False},
        },
        {
            "stage": "scalp_sim_buy_order_assumed_filled",
            "stock_code": "000001",
            "emitted_at": "2026-05-20T09:10:05+09:00",
            "fields": {**common_fields, "best_ask": "1000", "would_limit_fill": True, "qty": "1"},
        },
        {
            "stage": "scalp_sim_holding_started",
            "stock_code": "000001",
            "emitted_at": "2026-05-20T09:10:06+09:00",
            "fields": {**common_fields, "assumed_fill_price": "1000", "requested_qty": "1"},
        },
        {
            "stage": "scalp_sim_sell_order_assumed_filled",
            "stock_code": "000001",
            "emitted_at": "2026-05-20T09:20:00+09:00",
            "fields": {**common_fields, "profit_rate": "0.8", "exit_rule": "tp"},
        },
    ]
    (pipeline_dir / "pipeline_events_2026-05-20.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events),
        encoding="utf-8",
    )
    (post_sell_dir / "sim_post_sell_evaluations_2026-05-20.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "sim_record_id": "SIM-1",
                        "entry_adm_candidate_id": "ADM-1",
                        "profit_rate": 0.8,
                        "exit_rule": "scalp_hard_stop_pct",
                        "outcome": "GOOD_ENTRY",
                        "current_ai_score": 76,
                        "ai_score_raw": 79,
                        "ai_model": "bedrock-nova-lite-v2",
                        "ai_result_source": "bedrock",
                        "high_ai_hard_stop_conflict": True,
                        "hard_stop_conflict_dimension": "high_ai_hard_stop_conflict",
                        "hard_stop_conflict_ai_score_band": "ai_score_75_79",
                        "hard_stop_conflict_runtime_effect": False,
                        "hard_stop_conflict_allowed_runtime_apply": False,
                        "hard_stop_conflict_hard_gate": False,
                        "metrics_10m": {"mfe_pct": 1.2, "mae_pct": -0.2, "close_ret_pct": 0.8},
                    },
                    ensure_ascii=False,
                )
            ]
        ),
        encoding="utf-8",
    )
    (entry_dir / "scalp_entry_action_decision_matrix_2026-05-20.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "candidate_id": "ADM-1",
                        "sim_record_id": "SIM-1",
                        "stock_code": "000001",
                        "event_time": "2026-05-20T09:09:59+09:00",
                        "stage": "scalp_entry_action_decision_snapshot",
                        "chosen_action": "BUY_NOW",
                        "ai_score": 76,
                        "profit_rate": 0.8,
                        "mfe_10m_pct": 1.2,
                        "mae_10m_pct": -0.2,
                        "close_10m_pct": 0.8,
                        "outcome_joined": True,
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-20")

    submit_entry = next(item for item in report["policy_entries"] if item["stage"] == "submit")
    holding_entry = next(item for item in report["policy_entries"] if item["stage"] == "holding")
    assert submit_entry["sample"] == 1
    assert submit_entry["joined_sample"] == 1
    assert holding_entry["sample"] == 1
    assert holding_entry["joined_sample"] == 1
    assert report["sources"]["scalp_sim_submit"]["rows"] == 1
    assert report["sources"]["scalp_sim_submit"]["joined_rows"] == 1
    assert report["sources"]["scalp_sim_holding"]["rows"] == 1
    assert report["sources"]["scalp_sim_holding"]["joined_rows"] == 1
    submit_row = next(row for row in report["examples"] if row["source"] == "scalp_sim_entry_submit_pipeline_events")
    assert submit_row["source_stage"] == "scalp_sim_buy_order_assumed_filled"
    assert submit_row["runtime_features"]["actual_order_submitted"] is False
    assert submit_row["runtime_features"]["broker_order_forbidden"] is True
    assert submit_row["runtime_features"]["decision_authority"] == "sim_observation_only"
    assert submit_row["runtime_features"]["bucket_directed_sim_probe"] is True
    assert submit_row["runtime_features"]["lifecycle_bucket_match_status"] == "matched"
    assert report["summary"]["bucket_directed_sim_probe"]["matched_row_count"] >= 2
    assert (
        report["summary"]["bucket_directed_sim_probe"]["matched_unique_source_bucket_count"]
        == 1
    )
    post_sell_row = next(row for row in report["examples"] if row["source"] == "sim_post_sell_evaluations")
    assert post_sell_row["runtime_features"]["high_ai_hard_stop_conflict"] is True
    assert post_sell_row["runtime_features"]["hard_stop_conflict_dimension"] == "high_ai_hard_stop_conflict"
    assert post_sell_row["runtime_features"]["ai_model"] == "bedrock-nova-lite-v2"
    assert post_sell_row["labels"]["hard_stop_conflict_dimension"] == "high_ai_hard_stop_conflict"
    assert "hard_stop_conflict_dimension" not in mod._entry_bucket_features(post_sell_row)
    flow_attr = report["lifecycle_flow_bucket_attribution"]
    assert flow_attr["metric_scope"] == "lifecycle_bundle_ev"
    assert flow_attr["summary"]["complete_flow_count"] == 1
    assert flow_attr["summary"]["direct_sim_record_complete_flow_count"] == 1
    assert flow_attr["summary"]["adm_bridge_complete_flow_count"] == 0
    flow = flow_attr["flows"][0]
    assert flow["identity_quality"] == "exact_sim_record_id"
    assert flow["identity_closure_type"] == "direct_sim_record"
    assert flow["direct_sim_record_closed"] is True
    assert flow["reconstructed_flow_closed"] is False
    assert flow["source_sim_record_ids"] == ["SIM-1"]
    assert flow["source_candidate_ids"] == ["ADM-1"]
    assert flow["source_entry_adm_candidate_ids"] == ["ADM-1"]
    assert flow["source_quality_gate"] == "pass"
    assert flow["ai_inference_proposal"]["model"] == "gpt-5.4-mini"
    assert flow["entry_bucket_id"].startswith("entry:combo_entry_spot:")
    assert flow["submit_bucket_id"].startswith("submit:combo_submit_quality:")
    assert flow["holding_bucket_id"].startswith("holding:combo_holding_flow:")
    assert flow["exit_bucket_id"].startswith("exit:combo_exit_result:")
    assert report["summary"]["identity_join_rate"] == 1.0
    assert report["summary"]["complete_flow_rate"] == 1.0
    holding_attr = report["holding_bucket_attribution"]
    exit_attr = report["exit_bucket_attribution"]
    assert holding_attr["summary"]["bucket_count"] > 0
    assert exit_attr["summary"]["bucket_count"] > 0
    assert holding_attr["runtime_approval_candidates"] == []
    assert exit_attr["runtime_approval_candidates"] == []
    assert holding_attr["buckets"][0]["ai_inference_proposal"]["reasoning_effort"] == "medium"
    assert exit_attr["buckets"][0]["allowed_runtime_apply"] is False


def test_lifecycle_flow_bucket_fallback_identity_is_not_live_quality():
    rows = [
        {
            "stock_code": "000001",
            "event_time": f"2026-05-20T09:10:0{idx}+09:00",
            "stage": stage,
            "source_stage": stage,
            "runtime_features": {"ai_score": 70},
            "labels": {"profit_rate": 0.5, "mfe_10m_pct": 0.7, "mae_10m_pct": -0.1, "close_10m_pct": 0.5},
            "stage_ev_composite_pct": 0.5,
        }
        for idx, stage in enumerate(("entry", "submit", "holding", "exit"))
    ]

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    assert attribution["summary"]["fallback_identity_count"] == 4
    assert attribution["summary"]["identity_missing_count"] == 4
    assert attribution["summary"]["identity_join_rate"] == 0.0
    assert attribution["summary"]["complete_flow_rate"] == 0.0
    assert attribution["summary"]["incomplete_flow_reason_counts"]["fallback_identity_incomplete"] == 4
    assert all(flow["source_quality_gate"] == "fallback_identity_incomplete" for flow in attribution["flows"])
    assert attribution["runtime_approval_candidates"] == []


def test_lifecycle_flow_identity_prefers_entry_adm_candidate_id_before_row_candidate_id():
    row = {
        "candidate_id": "ROW-1",
        "runtime_features": {"entry_adm_candidate_id": "ADM-1"},
        "stock_code": "000001",
        "event_time": "2026-05-20T09:10:00+09:00",
    }

    assert mod._row_flow_identity(row) == ("entry_adm_candidate_id:ADM-1", "entry_adm_candidate_id")


def test_lifecycle_flow_adm_bridge_joins_entry_candidate_to_downstream_sim_rows():
    rows = [
        {
            "candidate_id": "8403",
            "stock_code": "011500",
            "event_time": "2026-05-28T09:05:54+09:00",
            "stage": "entry",
            "source_stage": "entry",
            "runtime_features": {"ai_score": 70},
            "labels": {"profit_rate": 0.4},
            "stage_ev_composite_pct": 0.4,
            "source": "scalp_entry_action_decision_matrix",
        },
        *[
            {
                "candidate_id": "ADM-011500-8403-1779926754334-bea5a3",
                "stock_code": "011500",
                "event_time": f"2026-05-28T09:0{idx}:55+09:00",
                "stage": stage,
                "source_stage": stage,
                "runtime_features": {
                    "sim_record_id": "SCALPSIM-011500-1779926754335-f7e730",
                    "entry_adm_candidate_id": "ADM-011500-8403-1779926754334-bea5a3",
                    "broker_order_forbidden": True,
                },
                "labels": {"profit_rate": 0.4},
                "stage_ev_composite_pct": 0.4,
            }
            for idx, stage in enumerate(("submit", "holding", "exit"), start=6)
        ],
    ]

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    assert attribution["summary"]["complete_flow_count"] == 1
    assert attribution["summary"]["direct_sim_record_complete_flow_count"] == 0
    assert attribution["summary"]["adm_bridge_complete_flow_count"] == 1
    assert attribution["summary"]["join_contract_blocked"] is False
    assert attribution["summary"]["stage_identity"]["entry"]["identity_quality_counts"] == {"entry_adm_bridge_key": 1}
    assert attribution["flows"][0]["identity_quality"] == "entry_adm_bridge_key"
    assert attribution["flows"][0]["identity_closure_type"] == "adm_bridge_reconstructed"
    assert attribution["flows"][0]["reconstructed_flow_closed"] is True
    assert attribution["flows"][0]["source_sim_record_ids"] == ["SCALPSIM-011500-1779926754335-f7e730"]
    assert attribution["flows"][0]["source_entry_adm_candidate_ids"] == ["ADM-011500-8403-1779926754334-bea5a3"]
    assert attribution["flows"][0]["stage_completion_state"] == "complete"


def test_lifecycle_flow_adm_bridge_does_not_rekey_non_adm_numeric_entry_sources():
    rows = [
        {
            "candidate_id": "8403",
            "stock_code": "011500",
            "event_time": "2026-05-28T09:05:54+09:00",
            "stage": "entry",
            "source_stage": "wait6579_ev_cohort",
            "runtime_features": {"ai_score": 70},
            "labels": {"profit_rate": 0.4},
            "stage_ev_composite_pct": 0.4,
            "source": "wait6579_ev_cohort",
        },
        {
            "candidate_id": "ADM-011500-8403-1779926754334-bea5a3",
            "stock_code": "011500",
            "event_time": "2026-05-28T09:06:55+09:00",
            "stage": "submit",
            "source_stage": "submit",
            "runtime_features": {
                "entry_adm_candidate_id": "ADM-011500-8403-1779926754334-bea5a3",
                "broker_order_forbidden": True,
            },
            "labels": {"profit_rate": 0.4},
            "stage_ev_composite_pct": 0.4,
        },
    ]

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    assert attribution["summary"]["complete_flow_count"] == 0
    assert attribution["summary"]["stage_identity"]["entry"]["identity_quality_counts"] == {"candidate_id": 1}
    assert attribution["summary"]["stage_identity"]["submit"]["identity_quality_counts"] == {"entry_adm_bridge_key": 1}


def test_lifecycle_flow_workorders_sample_incomplete_flows_after_complete_flows():
    rows = []
    for flow_idx in range(3):
        for stage_idx, stage in enumerate(("entry", "submit", "holding", "exit")):
            rows.append(
                {
                    "candidate_id": f"ADM-00000{flow_idx}-{flow_idx}-x",
                    "stock_code": f"00000{flow_idx}",
                    "event_time": f"2026-05-28T09:0{flow_idx}:0{stage_idx}+09:00",
                    "stage": stage,
                    "source_stage": stage,
                    "runtime_features": {
                        "entry_adm_candidate_id": f"ADM-00000{flow_idx}-{flow_idx}-x",
                        "broker_order_forbidden": True,
                    },
                    "labels": {"profit_rate": 0.4},
                    "stage_ev_composite_pct": 0.4,
                }
            )
    for flow_idx in range(25):
        rows.append(
            {
                "candidate_id": f"ENTRY-{flow_idx}",
                "stock_code": f"100{flow_idx:03d}",
                "event_time": f"2026-05-28T10:{flow_idx:02d}:00+09:00",
                "stage": "entry",
                "source_stage": "entry",
                "runtime_features": {"ai_score": 70},
                "labels": {"profit_rate": 0.1},
                "stage_ev_composite_pct": 0.1,
            }
        )

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    assert attribution["summary"]["complete_flow_count"] == 3
    assert attribution["summary"]["workorder_count"] == 20
    assert len(attribution["code_improvement_workorders"]) == 20
    assert all(
        item["reason"] != "pass"
        for item in attribution["code_improvement_workorders"]
    )


def test_lifecycle_flow_surfaces_identity_namespace_mismatch_when_required_stages_exist():
    rows = [
        {
            "candidate_id": "ENTRY-1",
            "stock_code": "000001",
            "event_time": "2026-05-20T09:10:00+09:00",
            "stage": "entry",
            "source_stage": "entry",
            "runtime_features": {"ai_score": 70},
            "labels": {},
            "stage_ev_composite_pct": 0.1,
        },
        *[
            {
                "stock_code": "000001",
                "event_time": f"2026-05-20T09:1{idx}:00+09:00",
                "stage": stage,
                "source_stage": stage,
                "runtime_features": {"sim_record_id": "SIM-1", "broker_order_forbidden": True},
                "labels": {"profit_rate": 0.4},
                "stage_ev_composite_pct": 0.4,
            }
            for idx, stage in enumerate(("submit", "holding", "exit"), start=1)
        ],
    ]

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    summary = attribution["summary"]
    assert summary["complete_flow_count"] == 0
    assert summary["join_contract_blocked"] is True
    assert summary["bundle_ev_tuning_state"] == "blocked_join_gap"
    assert summary["incomplete_flow_reason_counts"]["identity_namespace_mismatch"] == 1
    assert summary["incomplete_flow_reason_counts"]["entry_candidate_id_to_sim_record_id_bridge_missing"] == 1
    assert attribution["runtime_approval_candidates"] == []


def test_lifecycle_flow_bridge_key_can_complete_cross_namespace_flow():
    rows = [
        {
            "candidate_id": "ENTRY-1",
            "stock_code": "000001",
            "event_time": "2026-05-20T09:10:00+09:00",
            "stage": "entry",
            "source_stage": "entry",
            "runtime_features": {"lifecycle_flow_bridge_key": "FLOW-1", "ai_score": 70},
            "labels": {},
            "stage_ev_composite_pct": 0.1,
        },
        *[
            {
                "stock_code": "000001",
                "event_time": f"2026-05-20T09:1{idx}:00+09:00",
                "stage": stage,
                "source_stage": stage,
                "runtime_features": {
                    "lifecycle_flow_bridge_key": "FLOW-1",
                    "sim_record_id": "SIM-1",
                    "broker_order_forbidden": True,
                },
                "labels": {"profit_rate": 0.4},
                "stage_ev_composite_pct": 0.4,
            }
            for idx, stage in enumerate(("submit", "holding", "exit"), start=1)
        ],
    ]

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    assert attribution["summary"]["complete_flow_count"] == 1
    assert attribution["summary"]["adm_bridge_complete_flow_count"] == 1
    assert attribution["summary"]["join_contract_blocked"] is False
    assert attribution["flows"][0]["identity_quality"] == "lifecycle_flow_bridge_key"
    assert attribution["flows"][0]["identity_closure_type"] == "adm_bridge_reconstructed"
    assert attribution["flows"][0]["stage_completion_state"] == "complete"


def test_lifecycle_matrix_ingests_scalp_sim_scale_in_rows(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    entry_dir.mkdir(parents=True)
    post_sell_dir.mkdir(parents=True)
    monitor_dir.mkdir(parents=True)
    pipeline_dir.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    events = [
        {
            "stage": "scalp_sim_scale_in_order_assumed_filled",
            "stock_code": "000001",
            "emitted_at": "2026-05-19T10:00:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-1",
                "ord_no": "SIMADD-1",
                "add_type": "PYRAMID",
                "qty": "2",
                "limit_price": "1000",
                "curr_price": "1000",
                "best_bid": "990",
                "best_ask": "1000",
                "actual_order_submitted": "False",
                "broker_order_forbidden": "True",
            },
        },
        {
            "stage": "scalp_sim_holding_snapshot",
            "stock_code": "000001",
            "emitted_at": "2026-05-19T10:01:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-1",
                "profit_rate": "1.2",
            },
        },
        {
            "stage": "scalp_sim_holding_snapshot",
            "stock_code": "000001",
            "emitted_at": "2026-05-19T10:02:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-1",
                "profit_rate": "-0.4",
            },
        },
        {
            "stage": "scalp_sim_sell_order_assumed_filled",
            "stock_code": "000001",
            "emitted_at": "2026-05-19T10:03:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": "SIM-1",
                "profit_rate": "0.7",
                "exit_rule": "trailing_take_profit",
                "actual_order_submitted": "False",
            },
        },
    ]
    (pipeline_dir / "pipeline_events_2026-05-19.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-19")

    scale_rows = [row for row in report["examples"] if row.get("stage") == "scale_in"]
    assert len(scale_rows) == 1
    assert scale_rows[0]["source"] == "scalp_sim_scale_in_pipeline_events"
    assert scale_rows[0]["runtime_features"]["add_type"] == "PYRAMID"
    assert scale_rows[0]["runtime_features"]["actual_order_submitted"] == "False"
    assert "mfe_10m_pct" not in scale_rows[0]["runtime_features"]
    assert scale_rows[0]["labels"]["profit_rate"] == 0.7
    assert scale_rows[0]["labels"]["mfe_10m_pct"] == 1.2
    assert scale_rows[0]["labels"]["mae_10m_pct"] == -0.4
    assert report["sources"]["scalp_sim_scale_in"]["filled_events"] == 1
    assert any(item["stage"] == "scale_in" and item["sample"] == 1 for item in report["policy_entries"])


def test_lifecycle_matrix_joins_institutional_flow_features(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    flow_dir = tmp_path / "institutional_flow_context"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, flow_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )
    monkeypatch.setattr(
        mod,
        "institutional_flow_report_paths",
        lambda target_date: (
            flow_dir / f"institutional_flow_context_{target_date}.json",
            flow_dir / f"institutional_flow_context_{target_date}.md",
        ),
    )
    (entry_dir / "scalp_entry_action_decision_matrix_2026-05-20.json").write_text(
        json.dumps(
            {
                "examples": [
                    {
                        "candidate_id": "cand-1",
                        "stock_code": "005930",
                        "event_time": "2026-05-20T09:01:00+09:00",
                        "stage": "scalp_entry_action_decision_snapshot",
                        "chosen_action": "WAIT_REQUOTE",
                        "ai_score": 66,
                        "mfe_10m_pct": 1.2,
                        "mae_10m_pct": -0.3,
                        "close_10m_pct": 0.8,
                        "outcome_joined": True,
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (flow_dir / "institutional_flow_context_2026-05-20.json").write_text(
        json.dumps(
            {
                "summary": {"row_count": 1},
                "rows": [
                    {
                        "stock_code": "005930",
                        "foreign_net_roll5": 100,
                        "inst_net_roll5": 200,
                        "dual_net_buy": True,
                        "institutional_flow_status": "OK",
                        "institutional_flow_regime": "DUAL_ACCUMULATION",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-20")

    features = report["examples"][0]["runtime_features"]
    assert features["foreign_net_roll5"] == 100
    assert features["inst_net_roll5"] == 200
    assert features["institutional_flow_status"] == "OK"
    assert report["sources"]["institutional_flow_context"]["joined_rows"] == 1


def test_lifecycle_matrix_keeps_panic_lifecycle_source_contract_and_euphoria_split(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )
    events = [
        {
            "stage": "scalp_sim_euphoria_partial_profit_assumed_filled",
            "stock_code": "000001",
            "emitted_at": "2026-05-20T10:00:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "source_family": "panic_lifecycle_actuator",
                "family_type": "sim_lifecycle_source",
                "live_selectable": False,
                "preopen_apply_allowed": False,
                "env_apply_allowed": False,
                "threshold_env_mutation_allowed": False,
                "real_order_allowed": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "decision_authority": "sim_observation_only",
                "risk_context_owner": "euphoria",
                "risk_direction": "risk_on_euphoria",
                "action_namespace": "euphoria_lifecycle",
                "euphoria_action_type": "TAKE_PARTIAL_PROFIT_RUNNER",
                "euphoria_risk_level": 2,
                "euphoria_epoch_id": "euphoria-1",
                "realized_profit_rate": "0.8",
                "exit_rule": "scalp_sim_euphoria_runner_partial_profit",
            },
        },
        {
            "stage": "scalp_sim_euphoria_context_noop",
            "stock_code": "000002",
            "emitted_at": "2026-05-20T10:01:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "source_family": "panic_lifecycle_actuator",
                "family_type": "sim_lifecycle_source",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "risk_context_owner": "euphoria",
                "risk_direction": "risk_on_euphoria",
                "action_namespace": "euphoria_lifecycle",
                "runtime_effect": "SIM_NOOP_CONTEXT_NOT_OK",
                "exclude_from_ev": True,
                "euphoria_context_status": "SOURCE_QUALITY_BLOCKED",
            },
        },
    ]
    (pipeline_dir / "pipeline_events_2026-05-20.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-20")

    rows = [row for row in report["examples"] if row["source"] == "scalp_sim_panic_pipeline_events"]
    assert len(rows) == 2
    euphoria_row = next(row for row in rows if row["runtime_features"].get("euphoria_action_type"))
    features = euphoria_row["runtime_features"]
    assert features["source_family"] == "panic_lifecycle_actuator"
    assert features["family_type"] == "sim_lifecycle_source"
    assert features["live_selectable"] is False
    assert features["risk_context_owner"] == "euphoria"
    assert features["action_namespace"] == "euphoria_lifecycle"
    assert features["euphoria_action_type"] == "TAKE_PARTIAL_PROFIT_RUNNER"
    noop_row = next(row for row in rows if row["runtime_features"].get("exclude_from_ev"))
    assert noop_row["stage_ev_composite_pct"] is None
    assert noop_row["outcome_joined"] is False


def test_lifecycle_matrix_emits_entry_bucket_attribution_workorders(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    rows = [
        {
            "candidate_id": f"bad-{idx}",
            "stock_code": f"100{idx:03d}",
            "event_time": "2026-05-21T09:01:00+09:00",
            "stage": "scalp_entry_action_decision_snapshot",
            "source_stage": "scalp_sim_entry_armed",
            "chosen_action": "WAIT_REQUOTE",
            "ai_score": 58,
            "stale_bucket": "fresh",
            "entry_submit_revalidation_warning": "stale_context_or_quote",
            "liquidity_bucket": "below_min_liquidity",
            "risk_context_bucket": "weak_momentum_context",
            "overbought_bucket": "overbought_normal",
            "time_bucket": "time_1200_1400",
            "profit_rate": -1.2,
            "mfe_10m_pct": 0.1,
            "mae_10m_pct": -1.5,
            "close_10m_pct": -1.0,
            "outcome_joined": True,
        }
        for idx in range(22)
    ]
    rows.extend(
        {
            "candidate_id": f"good-{idx}",
            "stock_code": f"200{idx:03d}",
            "event_time": "2026-05-21T10:01:00+09:00",
            "stage": "scalp_entry_action_decision_snapshot",
            "source_stage": "scalp_sim_entry_armed",
            "chosen_action": "WAIT_REQUOTE",
            "ai_score": 64,
            "stale_bucket": "fresh",
            "liquidity_bucket": "liquidity_ok",
            "risk_context_bucket": "neutral_strength_momentum",
            "overbought_bucket": "pullback_observed",
            "time_bucket": "time_1000_1200",
            "profit_rate": 0.8,
            "mfe_10m_pct": 1.5,
            "mae_10m_pct": -0.2,
            "close_10m_pct": 0.9,
            "outcome_joined": True,
        }
        for idx in range(21)
    )
    (entry_dir / "scalp_entry_action_decision_matrix_2026-05-21.json").write_text(
        json.dumps({"rows": rows}, ensure_ascii=False),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-21")

    attribution = report["entry_bucket_attribution"]
    assert attribution["decision_authority"] == "adm_ldm_entry_bucket_attribution_source_only"
    assert attribution["summary"]["runtime_candidate_count"] >= 1
    assert attribution["summary"]["workorder_count"] >= 1
    stale_bucket = next(
        item
        for item in attribution["buckets"]
        if item["bucket_type"] == "stale_bucket" and item["bucket_key"] == "stale_context_or_quote"
    )
    assert stale_bucket["recommended_route"] == "candidate_tighten_or_exclude"
    assert stale_bucket["source_quality_adjusted_ev_pct"] < 0
    assert any(
        item["bucket_type"] == "overbought_bucket"
        and item["bucket_key"] == "pullback_observed"
        and item["recommended_route"] == "candidate_recovery_or_relax"
        for item in attribution["buckets"]
    )
    assert report["summary"]["entry_bucket_runtime_candidate_count"] >= 1


def test_lifecycle_matrix_emits_scale_in_bucket_attribution_workorders(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    events = [
        {
            "stage": "stat_action_decision_snapshot",
            "stock_code": f"9{idx:05d}",
            "record_id": idx,
            "emitted_at": f"2026-05-21T13:{idx:02d}:00+09:00",
            "fields": {
                "chosen_action": "pyramid_wait",
                "scale_in_action_type": "PYRAMID",
                "scale_in_action_reason": "scalping_pyramid_ok",
                "scale_in_arm": "PYRAMID",
                "scale_in_blocker_namespace": "PYRAMID",
                "scale_in_blocker_reason": "scalping_pyramid_ok",
                "profit_rate": "+1.20",
                "peak_profit": "+1.80",
                "held_sec": "240",
                "current_ai_score": "76",
                "ai_score_source": "model",
                "supply_pass_count": "3",
            },
        }
        for idx in range(11)
    ]
    (pipeline_dir / "pipeline_events_2026-05-21.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-21")

    attribution = report["scale_in_bucket_attribution"]
    assert attribution["decision_authority"] == "adm_ldm_scale_in_bucket_attribution_source_only"
    assert attribution["summary"]["arm_counts"]["PYRAMID"] == 11
    assert attribution["summary"]["runtime_candidate_count"] == 0
    assert attribution["summary"]["workorder_count"] == 0
    arm_bucket = next(item for item in attribution["buckets"] if item["bucket_type"] == "arm")
    assert arm_bucket["bucket_key"] == "PYRAMID"
    assert arm_bucket["scale_in_ev_coverage_state"] == "legacy_only"
    assert arm_bucket["recommended_route"] == "hold_sample"
    assert report["summary"]["scale_in_bucket_runtime_candidate_count"] == 0


def test_lifecycle_matrix_wait6579_rows_carry_runtime_bucket_fields(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )
    (monitor_dir / "wait6579_ev_cohort_2026-05-21.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "candidate_id": f"wait-{idx}",
                        "stock_code": f"3{idx:05d}",
                        "signal_time": "10:15:00",
                        "ai_score": 67,
                        "action": "WAIT",
                        "buy_pressure": 72.0,
                        "tick_accel": 1.3,
                        "micro_vwap_bp": 10.0,
                        "liquidity_bucket": "liquidity_proxy_strong",
                        "liquidity_bucket_provenance": "deterministic_proxy",
                        "overbought_bucket": "overbought_proxy_normal",
                        "overbought_bucket_provenance": "deterministic_proxy",
                        "time_bucket": "time_1000_1200",
                        "expected_ev_pct": 1.2,
                        "mfe_10m_pct": 2.0,
                        "mae_10m_pct": -0.3,
                        "close_10m_pct": 1.0,
                    }
                    for idx in range(12)
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-21")

    combo = next(
        item
        for item in report["entry_bucket_attribution"]["buckets"]
        if item["bucket_type"] == "combo_entry_spot"
        and "source=wait6579_ev_cohort" in item["bucket_key"]
    )
    assert "liquidity=liquidity_proxy_strong" in combo["bucket_key"]
    assert "overbought=overbought_proxy_normal" in combo["bucket_key"]
    assert "time=time_1000_1200" in combo["bucket_key"]
    assert combo["recommended_resolution"] == "none"


def test_lifecycle_matrix_backfills_scale_in_observation_fields(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )
    events = [
        {
            "stage": "scale_in_arm_blocked",
            "stock_code": f"4{idx:05d}",
            "record_id": idx,
            "emitted_at": f"2026-05-21T13:{idx:02d}:00+09:00",
            "fields": {
                "chosen_action": "pyramid_wait",
                "reason": "profit_not_enough",
                "profit_rate": "0.7",
                "peak_profit": "1.1",
                "current_ai_score": "74",
            },
        }
        for idx in range(6)
    ]
    (pipeline_dir / "pipeline_events_2026-05-21.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-21")

    scale_rows = [row for row in report["examples"] if row["stage"] == "scale_in"]
    assert scale_rows
    for row in scale_rows:
        features = row["runtime_features"]
        assert features["scale_in_arm"] == "PYRAMID"
        assert features["scale_in_blocker_namespace"] == "PYRAMID"
        assert features["ai_score_source"] == "score_field_backfilled"
        assert features["scale_in_field_provenance"]["arm"] == "backfilled_from_stage_or_action"


def test_lifecycle_matrix_emits_overnight_bucket_attribution_workorders(tmp_path, monkeypatch):
    matrix_dir = tmp_path / "matrix"
    entry_dir = tmp_path / "entry_adm"
    post_sell_dir = tmp_path / "post_sell"
    monitor_dir = tmp_path / "monitor"
    pipeline_dir = tmp_path / "pipeline_events"
    for directory in (entry_dir, post_sell_dir, monitor_dir, pipeline_dir):
        directory.mkdir(parents=True)
    monkeypatch.setattr(mod, "MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    monkeypatch.setattr(mod, "MONITOR_SNAPSHOT_DIR", monitor_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(
        mod,
        "entry_adm_report_paths",
        lambda target_date: (
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.json",
            entry_dir / f"scalp_entry_action_decision_matrix_{target_date}.md",
        ),
    )

    events = [
        {
            "stage": "scalp_sim_overnight_sell_today",
            "stock_code": f"8{idx:05d}",
            "record_id": idx,
            "emitted_at": f"2026-05-21T15:2{idx % 10}:00+09:00",
            "fields": {
                "simulation_book": "scalp_ai_buy_all",
                "sim_record_id": f"SIM-ON-{idx}",
                "ai_action": "SELL_TODAY",
                "ai_confidence": "0.82",
                "profit_rate": "+1.10",
                "profit_rate_live": "+1.10",
                "peak_profit": "+1.70",
                "held_sec": "900",
                "current_price_source": "best_bid",
                "source_quality_gate": "overnight_decision_coverage",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            },
        }
        for idx in range(11)
    ]
    (pipeline_dir / "pipeline_events_2026-05-21.jsonl").write_text(
        "\n".join(json.dumps(event, ensure_ascii=False) for event in events),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_decision_matrix_report("2026-05-21")

    attribution = report["overnight_bucket_attribution"]
    assert attribution["decision_authority"] == "adm_ldm_overnight_bucket_attribution_source_only"
    assert attribution["implementation_status"] == "implemented"
    assert attribution["implementation_provenance"]["runtime_effect"] is False
    assert attribution["summary"]["status_counts"]["SELL_TODAY"] == 11
    assert attribution["summary"]["runtime_candidate_count"] >= 1
    assert attribution["summary"]["workorder_count"] >= 1
    assert attribution["code_improvement_workorders"][0]["implementation_status"] == "implemented"
    assert attribution["code_improvement_workorders"][0]["implementation_provenance"]["source_field_coverage"] == {}
    action_bucket = next(item for item in attribution["buckets"] if item["bucket_type"] == "overnight_action")
    assert action_bucket["bucket_key"] == "SELL_TODAY"
    assert action_bucket["recommended_route"] == "candidate_recovery_or_relax"
    assert report["summary"]["overnight_bucket_runtime_candidate_count"] >= 1


def test_lifecycle_flow_denominator_excludes_scale_in_noise_and_incomplete_seeds():
    rows = []
    for idx in range(5):
        rows.append(
            {
                "candidate_id": f"ADM-00000{idx}-{idx}-x",
                "stock_code": f"00000{idx}",
                "event_time": f"2026-05-28T09:0{idx}:00+09:00",
                "stage": "entry",
                "source_stage": "entry",
                "runtime_features": {
                    "entry_adm_candidate_id": f"ADM-00000{idx}-{idx}-x",
                    "broker_order_forbidden": True,
                },
                "labels": {"profit_rate": 0.4},
                "stage_ev_composite_pct": 0.4,
            }
        )
    for idx in range(3):
        base_id = "SIM-ORPHAN"
        rows.append(
            {
                "candidate_id": f"{base_id}-{idx}",
                "stock_code": f"20000{idx}",
                "event_time": f"2026-05-28T10:0{idx}:00+09:00",
                "stage": "scale_in",
                "source_stage": "scale_in",
                "runtime_features": {
                    "sim_record_id": f"{base_id}-{idx}",
                    "add_type": "PYRAMID",
                    "scale_in_arm": "PYRAMID",
                    "broker_order_forbidden": True,
                },
                "labels": {"profit_rate": 0.2},
                "stage_ev_composite_pct": 0.2,
            }
        )

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    summary = attribution["summary"]
    assert summary["complete_flow_count"] == 0
    assert summary["scale_in_followup_event_count"] == 3
    assert 0 <= summary["scale_in_unique_flow_count"] <= summary["scale_in_followup_event_count"]
    assert summary["scale_in_noise_flow_count"] == 3
    assert summary.get("active_priority_incomplete_seed_count", 0) >= 0
    assert "denominator_exclusion_counts" in summary
    assert summary.get("denominator_exclusion_counts", {}).get("scale_in_noise_flow_excluded", 0) == 3
    assert "conversion_blocker_reason_counts" in summary
    assert "observation_seed_reason_counts" in summary
    assert "scale_in_noise_only" in str(summary.get("observation_seed_reason_counts", {}))
    assert "complete_flow_conversion_denominator" in summary
    assert summary["incomplete_flow_reason_counts"].get("scale_in_noise_only", 0) == 3


def test_lifecycle_flow_denominator_separates_conversion_blockers_from_observation_seeds():
    rows = []
    for idx in range(4):
        rows.append(
            {
                "candidate_id": f"ADM-{idx}",
                "stock_code": f"10000{idx}",
                "event_time": f"2026-05-28T09:0{idx}:00+09:00",
                "stage": "entry",
                "source_stage": "entry",
                "runtime_features": {
                    "entry_adm_candidate_id": f"ADM-{idx}",
                    "broker_order_forbidden": True,
                },
                "labels": {"profit_rate": 0.4},
                "stage_ev_composite_pct": 0.4,
            }
        )

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    summary = attribution["summary"]
    assert summary["complete_flow_count"] == 0
    assert summary["active_priority_incomplete_seed_count"] == 4
    assert summary.get("complete_flow_conversion_denominator", 0) == 0


def test_lifecycle_flow_complete_conversion_denominator_counts_complete_flows():
    rows = []
    for idx in range(2):
        for stage_idx, stage in enumerate(("entry", "submit", "holding", "exit")):
            rows.append(
                {
                    "candidate_id": f"ADM-{idx}-{idx}-x",
                    "stock_code": f"0000{idx}",
                    "event_time": f"2026-05-28T09:0{idx}:0{stage_idx}+09:00",
                    "stage": stage,
                    "source_stage": stage,
                    "runtime_features": {
                        "entry_adm_candidate_id": f"ADM-{idx}-{idx}-x",
                        "broker_order_forbidden": True,
                    },
                    "labels": {"profit_rate": 0.4},
                    "stage_ev_composite_pct": 0.4,
                }
            )

    attribution = mod._lifecycle_flow_bucket_attribution(rows)

    summary = attribution["summary"]
    assert summary["complete_flow_count"] == 2
    assert summary["complete_flow_conversion_denominator"] == 2
    assert summary["active_priority_incomplete_seed_count"] == 0
    assert summary["scale_in_noise_flow_count"] == 0
