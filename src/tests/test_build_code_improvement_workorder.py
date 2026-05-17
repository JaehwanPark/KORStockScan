import json

from src.engine import build_code_improvement_workorder as mod


def test_build_code_improvement_workorder_classifies_and_renders(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    ev_dir.mkdir()
    payload = {
        "date": "2026-05-08",
        "ev_report_summary": {"gemini_fresh": True, "claude_fresh": True},
        "consensus_findings": [
            {
                "finding_id": "latency_guard_miss_ev_recovery",
                "title": "latency guard miss EV recovery",
                "confidence": "consensus",
                "route": "instrumentation_order",
                "mapped_family": None,
                "target_subsystem": "runtime_instrumentation",
            },
            {
                "finding_id": "ai_threshold_miss_ev_recovery",
                "title": "AI threshold miss EV recovery",
                "confidence": "consensus",
                "route": "existing_family",
                "mapped_family": "score65_74_recovery_probe",
                "target_subsystem": "entry_funnel",
            },
            {
                "finding_id": "liquidity_gate_miss_ev_recovery",
                "title": "liquidity gate miss EV recovery",
                "confidence": "consensus",
                "route": "auto_family_candidate",
                "mapped_family": None,
                "target_subsystem": "entry_filter_quality",
            },
        ],
        "solo_findings": [
            {
                "finding_id": "cache_signature_noise",
                "title": "cache signature noise",
                "confidence": "solo",
                "route": "instrumentation_order",
                "target_subsystem": "runtime_instrumentation",
            }
        ],
        "auto_family_candidates": [
            {
                "family_id": "pattern_lab_liquidity_gate_miss_ev_recovery",
                "implementation_order_id": "order_pattern_lab_liquidity_gate_miss_ev_recovery",
                "allowed_runtime_apply": False,
            }
        ],
        "code_improvement_orders": [
            {
                "order_id": "order_ai_threshold_miss_ev_recovery",
                "title": "AI threshold miss EV recovery",
                "target_subsystem": "entry_funnel",
                "priority": 2,
                "files_likely_touched": ["src/engine/daily_threshold_cycle_report.py"],
                "acceptance_tests": ["pytest threshold tests"],
                "runtime_effect": False,
            },
            {
                "order_id": "order_latency_guard_miss_ev_recovery",
                "title": "latency guard miss EV recovery",
                "target_subsystem": "runtime_instrumentation",
                "priority": 1,
                "files_likely_touched": ["src/engine/sniper_performance_tuning_report.py"],
                "acceptance_tests": ["pytest instrumentation tests"],
                "runtime_effect": False,
            },
            {
                "order_id": "order_liquidity_gate_miss_ev_recovery",
                "title": "liquidity gate miss EV recovery",
                "target_subsystem": "entry_filter_quality",
                "priority": 3,
                "files_likely_touched": ["src/engine/daily_threshold_cycle_report.py"],
                "acceptance_tests": ["pytest report tests"],
                "runtime_effect": False,
            },
            {
                "order_id": "order_cache_signature_noise",
                "title": "cache signature noise",
                "target_subsystem": "runtime_instrumentation",
                "priority": 4,
                "files_likely_touched": ["src/engine/ai_engine.py"],
                "acceptance_tests": ["pytest cache tests"],
                "runtime_effect": False,
            },
            {
                "order_id": "order_partial_fallback_shadow",
                "title": "partial fallback shadow",
                "target_subsystem": "holding_exit",
                "priority": 5,
                "files_likely_touched": ["src/engine/sniper_state_handlers.py"],
                "acceptance_tests": ["pytest holding tests"],
                "runtime_effect": False,
            },
        ],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-08.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=5)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert decisions["order_latency_guard_miss_ev_recovery"] == "implement_now"
    assert decisions["order_ai_threshold_miss_ev_recovery"] == "attach_existing_family"
    assert decisions["order_liquidity_gate_miss_ev_recovery"] == "design_family_candidate"
    assert decisions["order_cache_signature_noise"] == "defer_evidence"
    assert decisions["order_partial_fallback_shadow"] == "reject"
    assert report["generation_id"].startswith("2026-05-08-")
    assert report["source_hash"]
    assert report["lineage"]["previous_exists"] is False
    assert (doc_dir / "code_improvement_workorder_2026-05-08.md").exists()
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(encoding="utf-8")
    assert "Codex 실행 지시" in markdown
    assert "2-Pass 실행 기준" in markdown
    assert "Snapshot Lineage" in markdown
    assert "order_latency_guard_miss_ev_recovery" in markdown
    assert "auto_bounded_live" in markdown


def test_build_code_improvement_workorder_limits_selected_orders(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    automation_dir.mkdir()
    payload = {
        "date": "2026-05-08",
        "consensus_findings": [],
        "solo_findings": [],
        "auto_family_candidates": [],
        "code_improvement_orders": [
            {"order_id": f"order_{idx}", "title": f"order {idx}", "priority": idx, "runtime_effect": False}
            for idx in range(5)
        ],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", tmp_path / "docs")

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=2)

    assert report["summary"]["source_order_count"] == 5
    assert report["summary"]["selected_order_count"] == 2
    assert report["deferred_or_rejected_count"] == 3


def test_build_code_improvement_workorder_consumes_pattern_lab_currentness_audit(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    currentness_dir = tmp_path / "currentness"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    currentness_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-15.json").write_text(
        json.dumps({"date": "2026-05-15", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (currentness_dir / "pattern_lab_currentness_audit_2026-05-15.json").write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {"fail_count": 1},
                "code_improvement_orders": [
                    {
                        "order_id": "order_pattern_lab_currentness_audit_metric_contract",
                        "title": "pattern lab metric contract",
                        "target_subsystem": "pattern_lab",
                        "priority": 1,
                        "route": "implement_now",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity")
    monkeypatch.setattr(mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", tmp_path / "missing-observation-audit")
    monkeypatch.setattr(mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance")
    monkeypatch.setattr(mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", currentness_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=2)

    order = report["orders"][0]
    assert order["source_report_type"] == "pattern_lab_currentness_audit"
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert report["summary"]["pattern_lab_currentness_source_order_count"] == 1
    assert report["source"]["pattern_lab_currentness_audit"] == str(
        currentness_dir / "pattern_lab_currentness_audit_2026-05-15.json"
    )


def test_build_code_improvement_workorder_adds_pipeline_event_verbosity_order(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    verbosity_dir = tmp_path / "verbosity"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for directory in (automation_dir, ev_dir, verbosity_dir):
        directory.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-14.json").write_text(
        json.dumps({"date": "2026-05-14", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-14.json").write_text("{}", encoding="utf-8")
    (verbosity_dir / "pipeline_event_verbosity_2026-05-14.json").write_text(
        json.dumps(
            {
                "state": "v2_shadow_missing",
                "recommended_workorder_state": "open_shadow_order",
                "raw_stream": {
                    "raw_size_bytes": 1000,
                    "high_volume_line_count": 900,
                    "high_volume_byte_share_pct": 70.0,
                },
                "producer_summary": {"exists": False},
                "parity": {
                    "ok": False,
                    "raw_derived_event_count": 900,
                    "producer_event_count": 0,
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENT_VERBOSITY_DIR", verbosity_dir)
    monkeypatch.setattr(mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-14", max_orders=3)

    order = next(item for item in report["orders"] if item["order_id"] == "order_pipeline_event_compaction_v2_shadow")
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert report["summary"]["pipeline_event_verbosity_source_order_count"] == 1
    assert report["source"]["pipeline_event_verbosity"] == str(
        verbosity_dir / "pipeline_event_verbosity_2026-05-14.json"
    )


def test_build_code_improvement_workorder_adds_observation_source_quality_orders(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    audit_dir = tmp_path / "observation-audit"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for directory in (automation_dir, ev_dir, audit_dir):
        directory.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-15.json").write_text(
        json.dumps({"date": "2026-05-15", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-15.json").write_text("{}", encoding="utf-8")
    (audit_dir / "observation_source_quality_audit_2026-05-15.json").write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {
                    "event_count": 100,
                    "warning_stage_count": 1,
                    "high_volume_no_source_field_stage_count": 1,
                },
                "stage_contracts": {
                    "blocked_ai_score": {"status": "warning"},
                    "swing_probe_state_persisted": {
                        "status": "warning",
                        "sample_count": 60,
                        "missing_violations": {
                            "metric_role": 1.0,
                            "decision_authority": 1.0,
                        },
                    },
                    "scale_in_price_p2_observe": {
                        "status": "warning",
                        "sample_count": 12,
                        "missing_violations": {
                            "orderbook_micro_ready": 0.0833,
                        },
                    },
                },
                "high_volume_no_source_fields": [
                    {"stage": "strength_momentum_observed", "event_count": 60},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity")
    monkeypatch.setattr(mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", audit_dir)
    monkeypatch.setattr(mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=5)

    order_ids = {item["order_id"]: item for item in report["orders"]}
    assert order_ids["order_ai_source_quality_not_evaluated_provenance"]["decision"] == "implement_now"
    assert order_ids["order_high_volume_diagnostic_stage_contract_labels"]["runtime_effect"] is False
    swing_order = order_ids["order_swing_source_quality_micro_context_provenance"]
    assert swing_order["runtime_effect"] is False
    assert swing_order["decision"] == "implement_now"
    assert any("swing_warning_stages=swing_probe_state_persisted,scale_in_price_p2_observe" in item for item in swing_order["evidence"])
    assert report["summary"]["observation_source_quality_source_order_count"] == 3
    assert report["source"]["observation_source_quality_audit"] == str(
        audit_dir / "observation_source_quality_audit_2026-05-15.json"
    )


def test_build_code_improvement_workorder_adds_window_policy_audit_order(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    calibration_dir = tmp_path / "calibration"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for directory in (automation_dir, ev_dir, calibration_dir):
        directory.mkdir()
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-14_postclose.json"
    calibration_path.write_text(
        json.dumps(
            {
                "window_policy_audit": {
                    "issue_counts": {"rolling_source_snapshot_mismatch": 2},
                    "items": [
                        {
                            "family": "score65_74_recovery_probe",
                            "primary": "rolling_5d",
                            "candidate_state": "hold",
                            "primary_sample_count": 177,
                            "primary_snapshot_sample_count": 0,
                            "primary_source_sample_count": 177,
                            "issues": ["rolling_source_snapshot_mismatch"],
                        }
                    ],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (automation_dir / "scalping_pattern_lab_automation_2026-05-14.json").write_text(
        json.dumps({"date": "2026-05-14", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-14.json").write_text(
        json.dumps({"sources": {"calibration": str(calibration_path)}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity")
    monkeypatch.setattr(mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-14", max_orders=3)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_threshold_window_policy_source_snapshot_alignment"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert "rolling_source_snapshot_mismatch" in "\n".join(order["evidence"])


def test_build_code_improvement_workorder_adds_codebase_performance_orders(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    perf_dir = tmp_path / "perf"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for directory in (automation_dir, ev_dir, perf_dir):
        directory.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-14.json").write_text(
        json.dumps({"date": "2026-05-14", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-14.json").write_text("{}", encoding="utf-8")
    perf_path = perf_dir / "codebase_performance_workorder_2026-05-14.json"
    perf_path.write_text(
        json.dumps(
            {
                "source_doc_hash": "abc123",
                "accepted_candidates": [
                    {
                        "item_id": "order_perf_buy_funnel_json_scan",
                        "title": "BUY funnel sentinel field scan without repeated json.dumps",
                        "risk_tier": "low",
                        "target_subsystem": "buy_funnel_sentinel",
                        "priority": 1,
                        "runtime_effect": False,
                        "strategy_effect": False,
                        "data_quality_effect": False,
                        "tuning_axis_effect": False,
                        "files_likely_touched": ["src/engine/buy_funnel_sentinel.py"],
                        "acceptance_tests": ["pytest src/tests/test_buy_funnel_sentinel.py"],
                        "parity_contract": "classification parity",
                        "forbidden_uses": ["runtime_threshold_mutation"],
                    }
                ],
                "deferred_candidates": [
                    {
                        "item_id": "order_perf_kiwoom_orders_http_session_review",
                        "title": "Kiwoom orders HTTP session reuse manual review",
                        "risk_tier": "high",
                        "target_subsystem": "broker_transport",
                        "priority": 20,
                        "runtime_effect": False,
                        "strategy_effect": False,
                        "data_quality_effect": False,
                        "tuning_axis_effect": False,
                        "files_likely_touched": ["src/engine/kiwoom_orders.py"],
                        "acceptance_tests": ["pytest src/tests/test_kiwoom_orders.py"],
                        "parity_contract": "broker request parity",
                        "defer_reason": "manual broker lifecycle review required",
                    }
                ],
                "rejected_candidates": [
                    {
                        "item_id": "order_perf_raw_event_suppression_out_of_scope",
                        "title": "Raw pipeline event suppression out of scope",
                        "risk_tier": "high",
                        "target_subsystem": "pipeline_event_storage",
                        "priority": 30,
                        "runtime_effect": False,
                        "strategy_effect": False,
                        "data_quality_effect": False,
                        "tuning_axis_effect": False,
                        "files_likely_touched": ["src/utils/pipeline_event_logger.py"],
                        "acceptance_tests": ["pytest pipeline tests"],
                        "parity_contract": "out of scope",
                        "defer_reason": "raw suppression excluded",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", perf_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-14", max_orders=10)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert decisions["order_perf_buy_funnel_json_scan"] == "implement_now"
    assert decisions["order_perf_kiwoom_orders_http_session_review"] == "defer_evidence"
    assert decisions["order_perf_raw_event_suppression_out_of_scope"] == "reject"
    accepted = next(item for item in report["orders"] if item["order_id"] == "order_perf_buy_funnel_json_scan")
    assert accepted["runtime_effect"] is False
    assert accepted["strategy_effect"] is False
    assert accepted["data_quality_effect"] is False
    assert accepted["tuning_axis_effect"] is False
    assert accepted["parity_contract"] == "classification parity"
    assert report["summary"]["codebase_performance_source_order_count"] == 3
    assert report["source"]["codebase_performance_workorder"] == str(perf_path)


def test_build_code_improvement_workorder_adds_panic_lifecycle_orders(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    calibration_dir = tmp_path / "calibration"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for directory in (automation_dir, ev_dir, calibration_dir):
        directory.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-13.json").write_text(
        json.dumps({"date": "2026-05-13", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-13.json"
    calibration_path.write_text(
        json.dumps(
            {
                "calibration_source_bundle": {
                    "source_metrics": {
                        "panic_sell_defense": {
                            "panic_state": "PANIC_SELL",
                            "panic_regime_mode": "PANIC_DETECTED",
                            "runtime_effect": "report_only_no_mutation",
                            "stop_loss_exit_count": 3,
                            "confirmation_eligible_exit_count": 2,
                            "active_sim_probe_positions": 1,
                            "microstructure_market_risk_state": "NEUTRAL",
                            "microstructure_confirmed_risk_off_advisory": False,
                            "microstructure_portfolio_local_risk_off_only": True,
                            "market_breadth_followup_candidate": True,
                            "source_quality_blockers": ["market_regime_not_risk_off"],
                            "candidate_status": {"panic_stop_confirmation": "report_only_candidate"},
                        },
                        "panic_buying": {
                            "panic_buy_state": "PANIC_BUY",
                            "panic_buy_regime_mode": "PANIC_BUY_CONTINUATION",
                            "runtime_effect": "report_only_no_mutation",
                            "panic_buy_active_count": 1,
                            "tp_counterfactual_count": 4,
                            "trailing_winner_count": 2,
                            "market_wide_panic_buy_confirmed": True,
                            "market_breadth_risk_on_advisory": True,
                            "candidate_status": {"panic_buy_runner_tp_canary": "report_only_candidate"},
                        },
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-13.json").write_text(
        json.dumps({"sources": {"calibration": str(calibration_path)}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-13", max_orders=5)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert decisions["order_panic_sell_defense_lifecycle_transition_pack"] == "design_family_candidate"
    assert decisions["order_panic_buy_runner_tp_canary_lifecycle_pack"] == "design_family_candidate"
    assert report["summary"]["panic_lifecycle_source_order_count"] == 2
    assert report["source"]["threshold_cycle_calibration"] == str(calibration_path)
    panic_order = next(
        item for item in report["orders"] if item["order_id"] == "order_panic_sell_defense_lifecycle_transition_pack"
    )
    assert any("market_breadth_followup_candidate=True" in item for item in panic_order["evidence"])
    assert any("source_quality_blockers=['market_regime_not_risk_off']" in item for item in panic_order["evidence"])
    panic_buy_order = next(
        item for item in report["orders"] if item["order_id"] == "order_panic_buy_runner_tp_canary_lifecycle_pack"
    )
    assert any("panic_buy_regime_mode=PANIC_BUY_CONTINUATION" in item for item in panic_buy_order["evidence"])
    assert any("market_wide_panic_buy_confirmed=True" in item for item in panic_buy_order["evidence"])
    markdown = (doc_dir / "code_improvement_workorder_2026-05-13.md").read_text(encoding="utf-8")
    assert "panic_buy_runner_tp_canary" in markdown
    assert "threshold_cycle_calibration" in markdown


def test_build_code_improvement_workorder_routes_panic_buy_source_quality_only(tmp_path, monkeypatch):
    automation_dir = tmp_path / "scalping_pattern_lab_automation"
    ev_dir = tmp_path / "threshold_cycle_ev"
    calibration_dir = tmp_path / "threshold_cycle_calibration"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    calibration_dir.mkdir(parents=True)
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-13.json"
    calibration_path.write_text(
        json.dumps(
            {
                "calibration_source_bundle": {
                    "source_metrics": {
                        "panic_buying": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_buy_state": "NORMAL",
                            "panic_buy_regime_mode": "NORMAL",
                            "panic_buy_active_count": 0,
                            "tp_counterfactual_count": 0,
                            "trailing_winner_count": 0,
                            "market_wide_panic_buy_confirmed": False,
                            "market_breadth_risk_on_advisory": False,
                            "missing_orderbook_count": 15,
                            "missing_trade_aggressor_count": 13,
                            "source_quality_blockers": ["panic_buy_orderbook_collector_coverage_gap"],
                            "candidate_status": {},
                        }
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    ev_dir.mkdir(parents=True)
    (ev_dir / "threshold_cycle_ev_2026-05-13.json").write_text(
        json.dumps({"sources": {"calibration": str(calibration_path)}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-13", max_orders=5)

    order = next(
        item for item in report["orders"] if item["order_id"] == "order_panic_buying_source_quality_market_breadth_micro_coverage"
    )
    assert order["route"] == "source_quality_blocker"
    assert order["runtime_effect"] is False
    assert order["threshold_family"] is None
    assert any("source_quality_blockers=['panic_buy_orderbook_collector_coverage_gap']" in item for item in order["evidence"])


def test_build_code_improvement_workorder_merges_swing_automation(tmp_path, monkeypatch):
    scalping_dir = tmp_path / "scalping"
    swing_dir = tmp_path / "swing"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    scalping_dir.mkdir()
    swing_dir.mkdir()
    (scalping_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_scalping_instrumentation",
                        "title": "scalping instrumentation",
                        "target_subsystem": "runtime_instrumentation",
                        "priority": 1,
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_improvement_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "ev_report_summary": {"threshold_ai_status": "parsed"},
                "consensus_findings": [
                    {
                        "finding_id": "swing_gatekeeper_reject_threshold_review",
                        "title": "swing gatekeeper reject threshold review",
                        "confidence": "consensus",
                        "route": "existing_family",
                        "mapped_family": "swing_gatekeeper_accept_reject",
                        "target_subsystem": "swing_entry",
                    }
                ],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_gatekeeper_reject_threshold_review",
                        "title": "swing gatekeeper reject threshold review",
                        "lifecycle_stage": "entry",
                        "target_subsystem": "swing_entry",
                        "threshold_family": "swing_gatekeeper_accept_reject",
                        "priority": 2,
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", scalping_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", swing_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=5)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert report["summary"]["source_order_count"] == 2
    assert report["summary"]["scalping_source_order_count"] == 1
    assert report["summary"]["swing_source_order_count"] == 1
    assert report["summary"]["swing_threshold_ai_status"] == "parsed"
    assert decisions["order_swing_gatekeeper_reject_threshold_review"] == "attach_existing_family"
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(encoding="utf-8")
    assert "swing_improvement_automation" in markdown
    assert "lifecycle_stage" in markdown


def test_build_code_improvement_workorder_dedupes_duplicate_orders(tmp_path, monkeypatch):
    scalping_dir = tmp_path / "scalping"
    swing_dir = tmp_path / "swing"
    swing_lab_dir = tmp_path / "swing_lab"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for d in (scalping_dir, swing_dir, swing_lab_dir):
        d.mkdir()
    (scalping_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_shared_instrumentation",
                        "title": "shared instrumentation",
                        "lifecycle_stage": "both",
                        "target_subsystem": "runtime_instrumentation",
                        "priority": 1,
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_improvement_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_only",
                        "title": "swing only",
                        "lifecycle_stage": "entry",
                        "target_subsystem": "swing_entry",
                        "priority": 2,
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (swing_lab_dir / "swing_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "ev_report_summary": {"deepseek_lab_available": True},
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_only",
                        "title": "swing only",
                        "lifecycle_stage": "entry",
                        "target_subsystem": "swing_entry",
                        "priority": 3,
                        "runtime_effect": False,
                    },
                    {
                        "order_id": "order_swing_only",
                        "title": "swing only duplicate",
                        "lifecycle_stage": "entry",
                        "target_subsystem": "swing_entry",
                        "priority": 4,
                        "runtime_effect": False,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", scalping_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", swing_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", swing_lab_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=5)

    assert report["summary"]["source_order_count"] == 3
    assert report["summary"]["scalping_source_order_count"] == 1
    assert report["summary"]["swing_source_order_count"] == 1
    assert report["summary"]["swing_lab_source_order_count"] == 2
    dup_warnings = report["summary"].get("duplicate_order_warnings") or []
    assert len(dup_warnings) == 1
    assert "order_swing_only" in dup_warnings[0]
    assert "swing_pattern_lab_automation" in dup_warnings[0]
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(encoding="utf-8")
    assert "Duplicate Order Collisions" in markdown


def test_build_code_improvement_workorder_adds_threshold_ev_hold_no_edge_followup(tmp_path, monkeypatch):
    scalping_dir = tmp_path / "scalping"
    ev_dir = tmp_path / "ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    scalping_dir.mkdir()
    ev_dir.mkdir()
    (scalping_dir / "scalping_pattern_lab_automation_2026-05-11.json").write_text(
        json.dumps(
            {
                "date": "2026-05-11",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [],
            }
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-11.json").write_text(
        json.dumps(
            {
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "holding_exit_decision_matrix_advisory",
                            "calibration_state": "hold_no_edge",
                            "sample_count": 42,
                            "sample_floor": 20,
                            "source_metrics": {
                                "counterfactual_gap_count": 42,
                                "eligible_but_not_chosen_sample_snapshots": 0,
                                "eligible_but_not_chosen_post_sell_joined_candidates": 0,
                                "counterfactual_proxy_missing_actions": ["hold_defer", "avg_down_wait"],
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", scalping_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-11", max_orders=5)

    assert report["summary"]["threshold_ev_source_order_count"] == 1
    order = report["orders"][0]
    assert order["order_id"] == "order_holding_exit_decision_matrix_edge_counterfactual"
    assert order["decision"] == "implement_now"
    assert order["mapped_family"] == "holding_exit_decision_matrix_advisory"
    assert "counterfactual_gap_count=42" in order["evidence"]
    markdown = (doc_dir / "code_improvement_workorder_2026-05-11.md").read_text(encoding="utf-8")
    assert "hold_no_edge" in markdown
    assert "counterfactual" in markdown


def test_build_code_improvement_workorder_skips_adm_followup_when_instrumentation_gap_closed(tmp_path, monkeypatch):
    scalping_dir = tmp_path / "scalping"
    ev_dir = tmp_path / "ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    scalping_dir.mkdir()
    ev_dir.mkdir()
    (scalping_dir / "scalping_pattern_lab_automation_2026-05-11.json").write_text(
        json.dumps(
            {
                "date": "2026-05-11",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [],
            }
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-11.json").write_text(
        json.dumps(
            {
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "holding_exit_decision_matrix_advisory",
                            "calibration_state": "hold_no_edge",
                            "sample_count": 14,
                            "sample_floor": 1,
                            "source_metrics": {
                                "instrumentation_status": "implemented",
                                "counterfactual_gap_count": 0,
                                "eligible_but_not_chosen_sample_snapshots": 12,
                                "eligible_but_not_chosen_post_sell_joined_candidates": 8,
                                "counterfactual_proxy_missing_actions": [],
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", scalping_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-11", max_orders=5)

    assert report["summary"]["threshold_ev_source_order_count"] == 0
    assert all(item["order_id"] != "order_holding_exit_decision_matrix_edge_counterfactual" for item in report["orders"])


def test_build_code_improvement_workorder_moves_closed_latency_instrumentation_to_existing_family(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    ev_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-11.json").write_text(
        json.dumps(
            {
                "date": "2026-05-11",
                "consensus_findings": [
                    {
                        "finding_id": "latency_guard_miss_ev_recovery",
                        "title": "latency guard miss EV recovery",
                        "confidence": "consensus",
                        "route": "instrumentation_order",
                        "target_subsystem": "runtime_instrumentation",
                    }
                ],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_latency_guard_miss_ev_recovery",
                        "title": "latency guard miss EV recovery",
                        "target_subsystem": "runtime_instrumentation",
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-11.json").write_text(
        json.dumps(
            {
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "pre_submit_price_guard",
                            "calibration_state": "hold_sample",
                            "source_metrics": {
                                "instrumentation_status": "implemented",
                                "provenance_contract": [
                                    "latency_block_events",
                                    "latency_guard_miss_unique_stocks",
                                    "quote_fresh_latency_pass_rate",
                                    "latency_reason_breakdown",
                                ],
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-11", max_orders=5)

    order = report["orders"][0]
    assert order["order_id"] == "order_latency_guard_miss_ev_recovery"
    assert order["decision"] == "attach_existing_family"
    assert order["mapped_family"] == "pre_submit_price_guard"


def test_build_code_improvement_workorder_reports_previous_generation_diff(tmp_path, monkeypatch):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    previous = {
        "generation_id": "2026-05-08-oldhash",
        "source_hash": "oldhash",
        "generated_at": "2026-05-08T17:00:00+09:00",
        "orders": [
            {"order_id": "order_old", "decision": "implement_now"},
            {"order_id": "order_keep", "decision": "defer_evidence"},
        ],
    }
    (report_dir / "code_improvement_workorder_2026-05-08.json").write_text(
        json.dumps(previous, ensure_ascii=False),
        encoding="utf-8",
    )
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_keep",
                        "title": "keep now instrumentation",
                        "target_subsystem": "runtime_instrumentation",
                        "priority": 1,
                        "runtime_effect": False,
                    },
                    {
                        "order_id": "order_new",
                        "title": "new instrumentation",
                        "target_subsystem": "runtime_instrumentation",
                        "priority": 2,
                        "runtime_effect": False,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing")
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab")
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=5)

    assert report["lineage"]["previous_exists"] is True
    assert report["lineage"]["previous_generation_id"] == "2026-05-08-oldhash"
    assert report["lineage"]["new_order_ids"] == ["order_new"]
    assert report["lineage"]["removed_order_ids"] == ["order_old"]
    assert report["lineage"]["decision_changed_order_ids"] == ["order_keep"]
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(encoding="utf-8")
    assert "order_new" in markdown
    assert "order_old" in markdown
