import json

from src.engine.automation import codex_workorder_runner
from src.engine import build_code_improvement_workorder as mod
from src.engine import lifecycle_decision_matrix as ldm_mod


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
                "files_likely_touched": [
                    "src/engine/sniper_performance_tuning_report.py"
                ],
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
                "files_likely_touched": ["src/engine/ai_engine_openai.py"],
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=5)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert decisions["order_latency_guard_miss_ev_recovery"] == "implement_now"
    assert decisions["order_ai_threshold_miss_ev_recovery"] == "attach_existing_family"
    assert (
        decisions["order_liquidity_gate_miss_ev_recovery"] == "design_family_candidate"
    )
    assert decisions["order_cache_signature_noise"] == "defer_evidence"
    assert decisions["order_partial_fallback_shadow"] == "reject"
    assert report["generation_id"].startswith("2026-05-08-")
    assert report["source_hash"]
    assert report["lineage"]["previous_exists"] is False
    assert (doc_dir / "code_improvement_workorder_2026-05-08.md").exists()
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(
        encoding="utf-8"
    )
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
            {
                "order_id": f"order_{idx}",
                "title": f"order {idx}",
                "priority": idx,
                "runtime_effect": False,
            }
            for idx in range(5)
        ],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", tmp_path / "report"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", tmp_path / "docs")

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=2)

    assert report["summary"]["source_order_count"] == 5
    assert report["summary"]["selected_order_count"] == 2
    assert report["summary"]["source_decision_counts"] == {"defer_evidence": 5}
    assert report["summary"]["selected_decision_counts"] == {"defer_evidence": 2}
    assert report["summary"]["selected_route_counts"] == {"defer_evidence": 2}
    assert report["summary"]["selected_implement_now_route_count"] == 0
    assert report["summary"]["selected_unimplemented_runtime_effect_false_count"] == 2
    assert report["summary"]["selected_unimplemented_route_counts"] == {
        "defer_evidence": 2
    }
    assert report["deferred_or_rejected_count"] == 3


def test_build_code_improvement_workorder_adds_intraday_entry_blocker_source_quality_orders(
    tmp_path, monkeypatch
):
    intraday_dir = tmp_path / "intraday_entry_blocker_diagnostics"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    intraday_dir.mkdir()
    payload = {
        "source_pipeline_events": "data/pipeline_events/pipeline_events_2026-07-01.jsonl",
        "source_quality_workorders": {
            "rising_missed_runtime_attach_identity_mismatch": [
                {
                    "workorder_type": "scanner_runtime_attach_identity_mismatch",
                    "stock_code": "000390",
                    "stock_name": "매드업",
                    "event_count": 5,
                    "latest_reason": "scanner_identity_name_mismatch",
                    "payload_name": "매드업",
                    "db_name": "SP삼화",
                    "mismatch_expired": "True",
                    "implementation_status": "implemented_source_quality_contract_available",
                    "implementation_provenance": {
                        "implementation_type": "scanner_runtime_attach_identity_source_quality_provenance",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "root_cause_closure_status_hint": "implementation_done",
                    },
                    "forbidden_uses": ["stale_submit_bypass", "broker_guard_bypass"],
                }
            ],
            "rising_missed_freshness_recovery": [
                {
                    "workorder_type": "bounded_rising_candidate_freshness_recheck",
                    "stock_code": "336260",
                    "stock_name": "두산퓨얼셀",
                    "event_count": 15,
                    "diagnostic_quote_age_stale": 9,
                    "pre_ai_stale_or_history_gap": 6,
                    "latest_stage": "blocked_strength_momentum",
                    "latest_reason": "below_strength_base",
                    "implementation_status": "implemented_source_quality_contract_available",
                    "implementation_provenance": {
                        "implementation_type": "bounded_rising_freshness_recheck_source_provenance",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "root_cause_closure_status_hint": "implementation_done",
                    },
                    "forbidden_uses": ["stale_submit_bypass", "broker_guard_bypass"],
                }
            ],
            "repeated_zero_strength_history": [
                {
                    "workorder_type": "scanner_strength_momentum_history_missing",
                    "stock_code": "389470",
                    "stock_name": "인벤티지랩",
                    "event_count": 6,
                    "latest_stage": "scalping_scanner_fast_precheck",
                    "implementation_status": "implemented_source_quality_contract_available",
                    "implementation_provenance": {
                        "implementation_type": "scanner_strength_history_source_quality_provenance",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "root_cause_closure_status_hint": "implementation_done",
                    },
                    "forbidden_uses": ["stale_submit_bypass", "broker_guard_bypass"],
                }
            ],
        },
    }
    (intraday_dir / "intraday_entry_blocker_diagnostics_2026-07-01.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-automation"
    )
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "INTRADAY_ENTRY_BLOCKER_DIAGNOSTICS_DIR", intraday_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-07-01", max_orders=10)

    intraday_orders = [
        item
        for item in report["orders"]
        if item["source_report_type"] == "intraday_entry_blocker_diagnostics"
    ]
    assert report["summary"]["intraday_entry_blocker_source_order_count"] == 3
    assert len(intraday_orders) == 3
    assert {item["decision"] for item in intraday_orders} == {"attach_existing_family"}
    assert {item["runtime_effect"] for item in intraday_orders} == {False}
    assert {item["allowed_runtime_apply"] for item in intraday_orders} == {False}
    assert {item["mapped_family"] for item in intraday_orders} == {
        "bounded_freshness_recheck",
        "scanner_runtime_attach_identity_mismatch",
        "scanner_strength_history_missing",
    }
    strength_order = next(
        item
        for item in intraday_orders
        if item["mapped_family"] == "scanner_strength_history_missing"
    )
    assert (
        strength_order["implementation_status"]
        == "implemented_source_quality_contract_available"
    )
    assert (
        strength_order["implementation_provenance"]["implementation_type"]
        == "scanner_strength_history_source_quality_provenance"
    )
    assert all(
        item["implementation_status"] == "implemented_source_quality_contract_available"
        for item in intraday_orders
    )
    assert all(
        "stale_submit_bypass" in item["forbidden_uses"] for item in intraday_orders
    )
    assert report["source"]["intraday_entry_blocker_diagnostics"] == str(
        intraday_dir / "intraday_entry_blocker_diagnostics_2026-07-01.json"
    )


def test_build_code_improvement_workorder_adds_rising_missed_scout_orders(
    tmp_path, monkeypatch
):
    scout_dir = tmp_path / "rising_missed_scout_workorder"
    prior_dir = tmp_path / "rising_missed_classifier_prior"
    bridge_dir = tmp_path / "rising_missed_normal_buy_bridge_candidate_discovery"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    scout_dir.mkdir()
    prior_dir.mkdir()
    bridge_dir.mkdir()
    payload = {
        "report_type": "rising_missed_scout_workorder",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "code_improvement_orders": [
            {
                "order_id": "order_rising_missed_scout_post_sell_bridge",
                "title": "rising missed scout post-sell bridge for normal-entry recheck",
                "target_subsystem": "entry_freshness",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_scout_post_sell_bridge",
                "threshold_family": "rising_missed_scout_post_sell_bridge",
                "priority": 2,
                "runtime_effect": True,
                "allowed_runtime_apply": True,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "forced_scout_post_sell_source_bridge",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "evidence": ["winner_count=3", "forced scout remains source-only"],
                "forbidden_uses": [
                    "forced_one_share_success_counting",
                    "stale_submit_bypass",
                ],
            }
        ],
    }
    (scout_dir / "rising_missed_scout_workorder_2026-07-01.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    prior_payload = {
        "report_type": "rising_missed_classifier_prior",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "code_improvement_orders": [
            {
                "order_id": "order_rising_missed_classifier_prior_bridge",
                "title": "rising missed cumulative classifier prior bridge",
                "target_subsystem": "rising_missed_entry_classifier",
                "route": "instrumentation_order",
                "mapped_family": "rising_missed_classifier_prior_bridge",
                "threshold_family": "rising_missed_classifier_prior_bridge",
                "priority": 3,
                "runtime_effect": True,
                "allowed_runtime_apply": True,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "rising_missed_classifier_prior_source_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "root_cause_closure_status_hint": "implementation_done",
                },
                "evidence": ["prior_count=2", "runtime_effect=false"],
                "forbidden_uses": ["forced_one_share_success_counting"],
            }
        ],
    }
    (prior_dir / "rising_missed_classifier_prior_2026-07-01.json").write_text(
        json.dumps(prior_payload, ensure_ascii=False),
        encoding="utf-8",
    )
    bridge_payload = {
        "report_type": "rising_missed_normal_buy_bridge_candidate_discovery",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "code_improvement_orders": [
            {
                "order_id": "order_rising_missed_normal_buy_bridge_preopen_env_review",
                "title": "rising missed normal BUY bridge PREOPEN env review",
                "target_subsystem": "normal_buy_score_prior_bridge",
                "route": "preopen_env_candidate_review",
                "mapped_family": "rising_missed_normal_buy_bridge",
                "threshold_family": "rising_missed_normal_buy_bridge",
                "priority": 1,
                "runtime_effect": True,
                "allowed_runtime_apply": True,
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "implementation_status": "implemented_but_waiting_sample",
                "implementation_provenance": {
                    "implementation_type": "rising_missed_normal_buy_runtime_bridge_hook",
                    "runtime_env_key": "KORSTOCKSCAN_RISING_MISSED_NORMAL_BUY_BRIDGE_ENABLED",
                    "runtime_effect": True,
                    "allowed_runtime_apply": True,
                },
                "forbidden_uses": ["forced_one_share_qty_or_tag_reuse"],
            }
        ],
    }
    (
        bridge_dir
        / "rising_missed_normal_buy_bridge_candidate_discovery_2026-07-01.json"
    ).write_text(json.dumps(bridge_payload, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-automation"
    )
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "RISING_MISSED_SCOUT_WORKORDER_DIR", scout_dir)
    monkeypatch.setattr(mod, "RISING_MISSED_CLASSIFIER_PRIOR_DIR", prior_dir)
    monkeypatch.setattr(
        mod, "RISING_MISSED_NORMAL_BUY_BRIDGE_CANDIDATE_DIR", bridge_dir
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-07-01", max_orders=5)

    scout_orders = [
        item
        for item in report["orders"]
        if item["source_report_type"] == "rising_missed_scout_workorder"
    ]
    prior_orders = [
        item
        for item in report["orders"]
        if item["source_report_type"] == "rising_missed_classifier_prior"
    ]
    bridge_orders = [
        item
        for item in report["orders"]
        if item["source_report_type"]
        == "rising_missed_normal_buy_bridge_candidate_discovery"
    ]
    assert report["summary"]["rising_missed_scout_source_order_count"] == 1
    assert report["summary"]["rising_missed_classifier_prior_source_order_count"] == 1
    assert report["summary"]["rising_missed_normal_buy_bridge_source_order_count"] == 1
    assert len(scout_orders) == 1
    assert len(prior_orders) == 1
    assert len(bridge_orders) == 1
    assert scout_orders[0]["decision"] == "attach_existing_family"
    assert scout_orders[0]["runtime_effect"] is False
    assert scout_orders[0]["allowed_runtime_apply"] is False
    assert scout_orders[0]["implementation_status"] == "implemented"
    assert scout_orders[0]["implementation_provenance"]["runtime_effect"] is False
    assert "forced_one_share_success_counting" in scout_orders[0]["forbidden_uses"]
    assert "runtime_threshold_mutation" in scout_orders[0]["forbidden_uses"]
    assert "broker_guard_bypass" in scout_orders[0]["forbidden_uses"]
    assert prior_orders[0]["decision"] == "attach_existing_family"
    assert prior_orders[0]["runtime_effect"] is False
    assert prior_orders[0]["allowed_runtime_apply"] is False
    assert prior_orders[0]["broker_order_forbidden"] is True
    assert "cap_release" in prior_orders[0]["forbidden_uses"]
    assert bridge_orders[0]["runtime_effect"] is False
    assert bridge_orders[0]["allowed_runtime_apply"] is False
    assert bridge_orders[0]["actual_order_submitted"] is False
    assert bridge_orders[0]["broker_order_forbidden"] is True
    assert (
        bridge_orders[0]["implementation_provenance"]["requires_preopen_env_selection"]
        is True
    )
    assert "buy_score_threshold_change" in bridge_orders[0]["forbidden_uses"]
    assert "forced_one_share_qty_or_tag_reuse" in bridge_orders[0]["forbidden_uses"]
    assert report["source"]["rising_missed_scout_workorder"] == str(
        scout_dir / "rising_missed_scout_workorder_2026-07-01.json"
    )
    assert report["source"]["rising_missed_classifier_prior"] == str(
        prior_dir / "rising_missed_classifier_prior_2026-07-01.json"
    )
    assert report["source"][
        "rising_missed_normal_buy_bridge_candidate_discovery"
    ] == str(
        bridge_dir
        / "rising_missed_normal_buy_bridge_candidate_discovery_2026-07-01.json"
    )


def test_build_code_improvement_workorder_adds_one_share_threshold_opportunity_orders(
    tmp_path, monkeypatch
):
    source_dir = tmp_path / "one_share_threshold_opportunity"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    source_dir.mkdir()
    payload = {
        "report_type": "one_share_threshold_opportunity",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "code_improvement_orders": [
            {
                "order_id": "order_one_share_threshold_ai_score_near_buy_entry_hook_review",
                "title": "one-share threshold opportunity entry hook review: ai_score_near_buy",
                "target_subsystem": "scalping_entry_ai_score_recheck",
                "route": "instrumentation_order",
                "mapped_family": "entry_opportunity_recheck_runtime",
                "threshold_family": "entry_opportunity_recheck_runtime",
                "priority": 1,
                "runtime_effect": True,
                "allowed_runtime_apply": True,
                "implementation_status": "implemented",
                "implementation_provenance": {
                    "implementation_type": "one_share_threshold_opportunity_audit",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                },
                "evidence": ["sample=12", "equal_weight_avg_profit_pct=0.42"],
                "forbidden_uses": ["forced_one_share_success_counting"],
            }
        ],
    }
    (source_dir / "one_share_threshold_opportunity_2026-07-01.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-automation"
    )
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "ONE_SHARE_THRESHOLD_OPPORTUNITY_DIR", source_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-07-01", max_orders=5)

    orders = [
        item
        for item in report["orders"]
        if item["source_report_type"] == "one_share_threshold_opportunity"
    ]
    assert report["summary"]["one_share_threshold_opportunity_source_order_count"] == 1
    assert len(orders) == 1
    assert orders[0]["runtime_effect"] is False
    assert orders[0]["allowed_runtime_apply"] is False
    assert orders[0]["actual_order_submitted"] is False
    assert orders[0]["broker_order_forbidden"] is True
    assert orders[0]["implementation_status"] == "implemented"
    assert "broker_guard_bypass" in orders[0]["forbidden_uses"]
    assert report["source"]["one_share_threshold_opportunity"] == str(
        source_dir / "one_share_threshold_opportunity_2026-07-01.json"
    )


def test_build_code_improvement_workorder_adds_entry_hurdle_backtest_orders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    source_dir = tmp_path / "entry_hurdle_backtest"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    source_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-07-01.json").write_text(
        json.dumps(
            {
                "date": "2026-07-01",
                "code_improvement_orders": [
                    {
                        "order_id": "order_overbought_gate_miss_ev_recovery",
                        "title": "overbought gate miss EV recovery",
                        "target_subsystem": "entry_funnel",
                        "route": "auto_family_candidate",
                        "priority": 2,
                        "runtime_effect": False,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    payload = {
        "report_type": "entry_hurdle_backtest",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "source_paths": ["/tmp/missed_entry_counterfactual_2026-07-01.json"],
        "code_improvement_orders": [
            {
                "order_id": "order_overbought_gate_miss_ev_recovery",
                "title": "overbought gate miss EV recovery",
                "target_subsystem": "entry_funnel",
                "route": "existing_family",
                "mapped_family": "overbought_gate_miss_ev_recovery",
                "threshold_family": "overbought_gate_miss_ev_recovery",
                "priority": 2,
                "runtime_effect": True,
                "allowed_runtime_apply": True,
                "implementation_status": "implemented_source_quality_contract_available",
                "implementation_provenance": {
                    "implementation_type": "overbought_gate_counterfactual_report_provenance",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                },
                "evidence": ["missed_winner_rate=83.33", "avoided_loser_rate=0.0"],
                "forbidden_uses": ["threshold mutation"],
            }
        ],
    }
    (source_dir / "entry_hurdle_backtest_2026-07-01.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "ENTRY_HURDLE_BACKTEST_DIR", source_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-07-01", max_orders=5)

    orders = [
        item
        for item in report["orders"]
        if item["source_report_type"] == "entry_hurdle_backtest"
    ]
    pattern_orders = [
        item
        for item in report["orders"]
        if item["source_report_type"] == "scalping_pattern_lab_automation"
        and item["order_id"] == "order_overbought_gate_miss_ev_recovery"
    ]
    assert report["summary"]["entry_hurdle_backtest_source_order_count"] == 1
    assert len(orders) == 1
    assert len(pattern_orders) == 1
    assert orders[0]["decision"] == "attach_existing_family"
    assert pattern_orders[0]["decision"] == "attach_existing_family"
    assert pattern_orders[0]["route"] == "existing_family"
    assert pattern_orders[0]["mapped_family"] == "overbought_gate_miss_ev_recovery"
    assert (
        pattern_orders[0]["implementation_status"]
        == "implemented_source_quality_contract_available"
    )
    assert (
        pattern_orders[0]["implementation_provenance"]["closed_by_source_report_type"]
        == "entry_hurdle_backtest"
    )
    assert orders[0]["runtime_effect"] is False
    assert orders[0]["allowed_runtime_apply"] is False
    assert orders[0]["actual_order_submitted"] is False
    assert orders[0]["broker_order_forbidden"] is True
    assert (
        orders[0]["implementation_status"]
        == "implemented_source_quality_contract_available"
    )
    assert (
        orders[0]["implementation_provenance"][
            "requires_separate_runtime_apply_candidate"
        ]
        is True
    )
    assert "broker_guard_bypass" in orders[0]["forbidden_uses"]
    assert report["source"]["entry_hurdle_backtest"] == str(
        source_dir / "entry_hurdle_backtest_2026-07-01.json"
    )


def test_build_code_improvement_workorder_adds_conversion_lane_orders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    conversion_dir = tmp_path / "conversion_lane"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    conversion_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (conversion_dir / "conversion_lane_2026-05-08.json").write_text(
        json.dumps(
            {
                "conversion_blocker_rank": [
                    {
                        "conversion_candidate_id": "active_seed_x",
                        "blocker_class": "key_lineage",
                        "conversion_impact_rank": 1,
                        "remaining_gap_count": 2,
                        "next_repair_action": "runtime_observed_seed_not_in_catalog",
                        "acceptance_test": "same key is continuous",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CONVERSION_LANE_DIR", conversion_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["source_report_type"] == "conversion_lane"
    assert order["decision"] == "implement_now"
    assert order["conversion_candidate_id"] == "active_seed_x"
    assert order["blocks_bounded_real_canary"] is True
    assert report["summary"]["conversion_lane_source_order_count"] == 1
    assert report["summary"]["selected_implement_now_route_count"] == 1


def test_conversion_lane_orders_are_required_handoff_beyond_max_orders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    conversion_dir = tmp_path / "conversion_lane"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    conversion_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (conversion_dir / "conversion_lane_2026-05-08.json").write_text(
        json.dumps(
            {
                "conversion_blocker_rank": [
                    {
                        "conversion_candidate_id": "hyp_1",
                        "blocker_class": "key_lineage",
                        "conversion_impact_rank": 1,
                        "remaining_gap_count": 2,
                        "next_repair_action": "hypothesis_catalog_missing",
                        "acceptance_test": "same key is continuous",
                    },
                    {
                        "conversion_candidate_id": "submit_drought:LATENCY_PRE_SUBMIT",
                        "blocker_class": "submit_drought",
                        "conversion_impact_rank": 2,
                        "remaining_gap_count": 2,
                        "next_repair_action": "close_submit_drought_latency_pre_submit",
                        "acceptance_test": "submit drought ledger splits weak contracts",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CONVERSION_LANE_DIR", conversion_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    selected_ids = {order["order_id"] for order in report["orders"]}
    assert "order_conversion_lane_key_lineage_hyp_1" in selected_ids
    assert (
        "order_conversion_lane_submit_drought_submit_drought_latency_pre_submit"
        in selected_ids
    )
    assert report["summary"]["selected_implement_now_route_count"] == 2


def test_conversion_lane_axis_instrumentation_marks_order_as_existing_implementation(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    conversion_dir = tmp_path / "conversion_lane"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    conversion_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps({"date": "2026-05-08", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (conversion_dir / "conversion_lane_2026-05-08.json").write_text(
        json.dumps(
            {
                "conversion_blocker_rank": [
                    {
                        "conversion_candidate_id": "submit_drought:LATENCY_PRE_SUBMIT",
                        "blocker_class": "submit_drought",
                        "blocker_axis": "LATENCY_PRE_SUBMIT",
                        "blocker_resolution_status": "open",
                        "blocker_runtime_effect": False,
                        "blocker_allowed_runtime_apply": False,
                        "conversion_impact_rank": 1,
                        "remaining_gap_count": 2,
                        "next_repair_action": "close_submit_drought_latency_pre_submit",
                        "acceptance_test": "submit drought ledger splits weak contracts",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CONVERSION_LANE_DIR", conversion_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["implementation_status"] == "implemented"
    assert order["implementation_provenance"]["implemented_scope"] == (
        "conversion_lane_blocker_axis_report_provenance"
    )
    assert order["decision"] == "attach_existing_family"
    assert (
        report["summary"]["selected_implement_now_new_runtime_effect_false_count"] == 0
    )


def test_build_code_improvement_workorder_escalates_repeated_unresolved_attach(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    repeated_order = {
        "order_id": "order_repeated_source_quality_gap",
        "title": "Repeated source quality gap",
        "target_subsystem": "entry_funnel",
        "route": "existing_family",
        "mapped_family": "lifecycle_decision_matrix_runtime",
        "improvement_type": "source_quality_gap",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    payload = {
        "date": "2026-05-08",
        "consensus_findings": [],
        "solo_findings": [],
        "auto_family_candidates": [],
        "code_improvement_orders": [repeated_order],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {
                            **repeated_order,
                            "decision": "attach_existing_family",
                        }
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["order_id"] == "order_repeated_source_quality_gap"
    assert order["decision"] == "implement_now"
    assert order["route"] == "repeat_unresolved_escalation"
    assert order["repeat_unresolved_escalation"]["repeat_count"] == 2
    assert report["summary"]["repeat_unresolved_escalation_count"] == 1
    assert report["summary"]["repeat_unresolved_escalated_order_ids"] == [
        "order_repeated_source_quality_gap"
    ]
    assert (
        report["summary"]["selected_implement_now_existing_implementation_count"] == 0
    )
    assert (
        report["summary"]["selected_implement_now_existing_implementation_order_ids"]
        == []
    )
    assert (
        report["summary"]["selected_implement_now_new_runtime_effect_false_count"] == 1
    )
    assert report["summary"][
        "selected_implement_now_new_runtime_effect_false_order_ids"
    ] == ["order_repeated_source_quality_gap"]
    assert report["summary"]["selected_unimplemented_runtime_effect_false_count"] == 1


def test_build_code_improvement_workorder_escalates_repeated_unresolved_signature(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    current_order = {
        "order_id": "order_source_gap_current_hash",
        "title": "Repeated hashed source gap",
        "source_report_type": "scalping_pattern_lab_automation",
        "target_subsystem": "entry_funnel",
        "lifecycle_stage": "entry",
        "improvement_type": "source_quality_gap",
        "route": "existing_family",
        "mapped_family": "lifecycle_decision_matrix_runtime",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for idx, previous_date in enumerate(("2026-05-07", "2026-05-06"), start=1):
        previous_order = {
            **current_order,
            "order_id": f"order_source_gap_previous_hash_{idx}",
            "decision": "attach_existing_family",
        }
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [previous_order],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["order_id"] == "order_source_gap_current_hash"
    assert order["decision"] == "implement_now"
    assert order["route"] == "repeat_unresolved_escalation"
    assert order["repeat_unresolved_escalation"]["repeat_key"].startswith("sig:")
    assert order["repeat_unresolved_escalation"]["repeat_count"] == 2
    assert (
        report["summary"]["selected_implement_now_existing_implementation_count"] == 0
    )
    assert (
        report["summary"]["selected_implement_now_new_runtime_effect_false_count"] == 1
    )
    assert report["summary"]["selected_unimplemented_runtime_effect_false_count"] == 1


def test_build_code_improvement_workorder_does_not_escalate_history_implemented_waiting_sample(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    repeated_order = {
        "order_id": "order_source_gap_history_waiting_sample",
        "title": "Repeated source quality gap with waiting sample history",
        "source_report_type": "scalping_pattern_lab_automation",
        "target_subsystem": "entry_funnel",
        "lifecycle_stage": "entry",
        "route": "existing_family",
        "mapped_family": "lifecycle_decision_matrix_runtime",
        "improvement_type": "source_quality_gap",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [repeated_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {
                            **repeated_order,
                            "decision": "attach_existing_family",
                            "implementation_status": "implemented_but_waiting_sample",
                        }
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["order_id"] == "order_source_gap_history_waiting_sample"
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "existing_family"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0
    assert (
        report["summary"]["selected_implement_now_new_runtime_effect_false_count"] == 0
    )


def test_build_code_improvement_workorder_does_not_escalate_existing_family_only_repeat(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    repeated_order = {
        "order_id": "order_existing_family_repeat",
        "title": "Existing family repeat",
        "target_subsystem": "entry_funnel",
        "route": "existing_family",
        "mapped_family": "score65_74_recovery_probe",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [repeated_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {**repeated_order, "decision": "attach_existing_family"}
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "existing_family"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0


def test_build_code_improvement_workorder_keeps_rollup_non_implement_but_marks_longstanding(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    current_order = {
        "order_id": "order_lifecycle_quiet_gap_positive_source_only_rollup",
        "title": "Lifecycle quiet gap positive source-only review",
        "source_report_type": "lifecycle_bucket_discovery_quiet_gap_rollup",
        "target_subsystem": "lifecycle_bucket_discovery_taxonomy_provenance",
        "lifecycle_stage": "multi_stage",
        "improvement_type": "quiet_gap_rollup_evidence",
        "route": "positive_source_only_review",
        "mapped_family": "lifecycle_bucket_discovery",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [{**current_order, "decision": "attach_existing_family"}],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "positive_source_only_review"
    assert (
        order["longstanding_non_implement_review"]["review_disposition"]
        == "keep_visible_by_design"
    )
    assert report["summary"]["repeat_unresolved_structural_blocker_count"] == 0
    assert report["summary"]["selected_terminal_non_implement_longstanding_count"] == 1
    assert report["summary"][
        "selected_terminal_non_implement_longstanding_order_ids"
    ] == ["order_lifecycle_quiet_gap_positive_source_only_rollup"]


def test_build_code_improvement_workorder_escalates_repeated_implemented_submit_drought_as_structural_blocker(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    current_order = {
        "order_id": "order_entry_submit_drought_auto_resolution",
        "title": "Entry submit drought automatic resolution handoff",
        "source_report_type": "buy_funnel_sentinel",
        "target_subsystem": "runtime_instrumentation",
        "lifecycle_stage": "entry_submit",
        "improvement_type": "source_only_report_provenance_handoff",
        "route": "existing_family",
        "mapped_family": "lifecycle_decision_matrix_runtime",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_status": "implemented",
        "next_postclose_metric": (
            "SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose "
            "LDM/runtime summary must show submit blocker attribution."
        ),
        "evidence": ["submitted_to_ai_pct=1.5"],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [{**current_order, "decision": "attach_existing_family"}],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "implement_now"
    assert order["route"] == "repeat_unresolved_structural_blocker"
    assert order["implementation_status"] == "repeat_unresolved_structural_blocker"
    assert order["structural_blocker_escalation"]["repeat_count"] == 3
    assert (
        order["structural_blocker_escalation"]["required_next_route"] == "implement_now"
    )
    assert report["summary"]["repeat_unresolved_structural_blocker_count"] == 1
    assert report["summary"]["repeat_unresolved_structural_blocker_order_ids"] == [
        "order_entry_submit_drought_auto_resolution"
    ]


def test_build_code_improvement_workorder_does_not_reescalate_closed_submit_drought_root_cause(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    current_order = {
        "order_id": "order_entry_submit_drought_auto_resolution",
        "title": "Entry submit drought automatic resolution handoff",
        "source_report_type": "buy_funnel_sentinel",
        "target_subsystem": "runtime_instrumentation",
        "lifecycle_stage": "entry_submit",
        "improvement_type": "source_only_report_provenance_handoff",
        "route": "existing_family",
        "mapped_family": "lifecycle_decision_matrix_runtime",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_status": "implemented",
        "implementation_provenance": {
            "root_cause_closure_status_hint": "root_cause_closed",
        },
        "next_postclose_metric": (
            "SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose "
            "LDM/runtime summary must show submit blocker attribution."
        ),
        "evidence": ["submitted_to_ai_pct=1.5"],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [{**current_order, "decision": "attach_existing_family"}],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["implementation_status"] == "implemented"
    assert order["route"] == "existing_family"
    assert order["root_cause_closure_status"] == "root_cause_closed"
    assert report["summary"]["repeat_unresolved_structural_blocker_count"] == 0


def test_build_code_improvement_workorder_does_not_escalate_repeated_explicit_not_applicable_bucket(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    current_order = {
        "order_id": "order_not_applicable_terminal",
        "title": "Not applicable terminal bucket",
        "source_report_type": "lifecycle_decision_matrix_exit_bucket_attribution",
        "target_subsystem": "lifecycle_decision_matrix",
        "lifecycle_stage": "exit",
        "improvement_type": "exit_bucket_source_quality_child_evidence",
        "route": "existing_family",
        "mapped_family": "lifecycle_decision_matrix_runtime",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_status": "terminal_not_applicable_evidence",
        "implementation_provenance": {
            "recommended_resolution": "mark_not_applicable_explicitly"
        },
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [{**current_order, "decision": "attach_existing_family"}],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "attach_existing_family"
    assert order["structural_blocker_escalation"] is None
    assert (
        order["longstanding_non_implement_review"]["review_disposition"]
        == "keep_visible_by_design"
    )
    assert report["summary"]["repeat_unresolved_structural_blocker_count"] == 0


def test_build_code_improvement_workorder_does_not_double_escalate_summary_contract_gap_when_specific_gap_exists(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    summary_order = {
        "order_id": "order_swing_holding_exit_contract_gap_review",
        "title": "swing holding/exit contract gap review",
        "source_report_type": "swing_improvement_automation",
        "target_subsystem": "swing_holding_exit",
        "lifecycle_stage": "holding_exit",
        "threshold_family": "swing_exit_ofi_qi_smoothing",
        "improvement_type": "lifecycle_contract_gap",
        "route": "existing_family",
        "mapped_family": "swing_exit_ofi_qi_smoothing",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_status": "implemented",
        "next_postclose_metric": "holding/exit source-quality and structured contract gaps are visible without changing sell logic.",
        "evidence": ["evidence={'stale_missing_ratio': 0.1407}"],
    }
    specific_order = {
        "order_id": "order_swing_ofi_qi_stale_or_missing_context",
        "title": "swing OFI/QI stale or missing context",
        "source_report_type": "swing_improvement_automation",
        "target_subsystem": "swing_orderbook_micro_context",
        "lifecycle_stage": "entry",
        "threshold_family": "swing_exit_ofi_qi_smoothing",
        "improvement_type": "instrumentation",
        "route": "existing_family",
        "mapped_family": "swing_exit_ofi_qi_smoothing",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_status": "terminal_existing_family_evidence",
        "next_postclose_metric": "stale_missing_ratio decreases while submitted/simulated entry quality remains attributable.",
    }
    payload = {
        "date": "2026-05-08",
        "consensus_findings": [],
        "solo_findings": [],
        "auto_family_candidates": [],
        "code_improvement_orders": [summary_order, specific_order],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {**summary_order, "decision": "attach_existing_family"},
                        {**specific_order, "decision": "attach_existing_family"},
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=2)

    by_id = {item["order_id"]: item for item in report["orders"]}
    assert (
        by_id["order_swing_ofi_qi_stale_or_missing_context"]["decision"]
        == "implement_now"
    )
    assert (
        by_id["order_swing_ofi_qi_stale_or_missing_context"]["route"]
        == "repeat_unresolved_structural_blocker"
    )
    assert (
        by_id["order_swing_holding_exit_contract_gap_review"]["decision"]
        == "attach_existing_family"
    )
    assert (
        by_id["order_swing_holding_exit_contract_gap_review"][
            "structural_blocker_escalation"
        ]
        is None
    )
    assert (
        by_id["order_swing_holding_exit_contract_gap_review"][
            "longstanding_non_implement_review"
        ]["review_disposition"]
        == "keep_visible_by_design"
    )


def test_build_code_improvement_workorder_does_not_escalate_current_implemented_hold_sample_repeat(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    repeated_order = {
        "order_id": "order_implemented_hold_sample_repeat",
        "title": "Implemented hold sample repeat",
        "source_report_type": "producer_gap_discovery",
        "target_subsystem": "postclose_source_producer",
        "route": "existing_family",
        "mapped_family": "producer_gap_source_bundle",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_status": "implemented_but_hold_sample",
        "implementation_provenance": {
            "source_report_type": "producer_gap_source_bundle",
            "source_quality_status": "implemented_but_hold_sample",
        },
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [repeated_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {**repeated_order, "decision": "attach_existing_family"}
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "existing_family"
    assert order["implementation_status"] == "implemented_but_hold_sample"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0


def test_build_code_improvement_workorder_does_not_escalate_pattern_lab_design_only_repeat(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    repeated_order = {
        "order_id": "order_pattern_lab_design_repeat",
        "title": "All selected candidates failed to reach order submission",
        "source_report_type": "swing_pattern_lab_automation",
        "target_subsystem": "swing_entry_funnel",
        "lifecycle_stage": "entry",
        "improvement_type": "pattern_lab_observation",
        "route": "design_family_candidate",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [repeated_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {**repeated_order, "decision": "design_family_candidate"}
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "design_family_candidate"
    assert order["route"] == "design_family_candidate"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0


def test_build_code_improvement_workorder_does_not_close_swing_ai_contract_without_report_contract(
    tmp_path, monkeypatch
):
    swing_dir = tmp_path / "swing"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    swing_dir.mkdir()
    report_dir.mkdir()
    repeated_order = {
        "order_id": "order_swing_ai_contract_structured_output_eval",
        "title": "swing AI contract structured output eval",
        "source_report_type": "swing_improvement_automation",
        "target_subsystem": "swing_ai_contract",
        "lifecycle_stage": "ai_contract",
        "improvement_type": "ai_contract_eval",
        "route": "auto_family_candidate",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (swing_dir / "swing_improvement_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [repeated_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {**repeated_order, "decision": "design_family_candidate"}
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-scalping"
    )
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", swing_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "design_family_candidate"
    assert order["route"] == "auto_family_candidate"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0


def test_build_code_improvement_workorder_does_not_escalate_deferred_performance_repeat(
    tmp_path, monkeypatch
):
    perf_dir = tmp_path / "perf"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    perf_dir.mkdir()
    report_dir.mkdir()
    repeated_order = {
        "order_id": "order_perf_config_cache_scope_review",
        "title": "Config cache scope review",
        "source_report_type": "codebase_performance_workorder",
        "target_subsystem": "config_loading",
        "lifecycle_stage": "ops_performance",
        "route": "performance_optimization_order",
        "priority": 21,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "performance_candidate_state": "deferred",
    }
    (perf_dir / "codebase_performance_workorder_2026-05-08.json").write_text(
        json.dumps(
            {
                "summary": {"deferred_count": 1},
                "deferred_candidates": [
                    {**repeated_order, "item_id": repeated_order["order_id"]}
                ],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [{**repeated_order, "decision": "defer_evidence"}],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-scalping"
    )
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", perf_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "defer_evidence"
    assert order["route"] == "performance_optimization_order"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0


def test_build_code_improvement_workorder_does_not_escalate_solo_pattern_lab_existing_family_repeat(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    repeated_order = {
        "order_id": "order_solo_existing_family_repeat",
        "title": "solo existing family repeat",
        "source_report_type": "scalping_pattern_lab_automation",
        "target_subsystem": "entry_funnel",
        "route": "existing_family",
        "mapped_family": "score65_74_recovery_probe",
        "improvement_type": "threshold_family_input",
        "confidence": "solo",
        "priority": 7,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [repeated_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-05-07", "2026-05-06"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [{**repeated_order, "decision": "defer_evidence"}],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "defer_evidence"
    assert order["route"] == "existing_family"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0


def test_build_code_improvement_workorder_does_not_signature_escalate_sparse_orders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    current_order = {
        "order_id": "order_sparse_current",
        "target_subsystem": "entry_funnel",
        "route": "existing_family",
        "mapped_family": "lifecycle_decision_matrix_runtime",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-05-08.json").write_text(
        json.dumps(
            {
                "date": "2026-05-08",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for idx, previous_date in enumerate(("2026-05-07", "2026-05-06"), start=1):
        previous_order = {
            **current_order,
            "order_id": f"order_sparse_previous_{idx}",
            "decision": "attach_existing_family",
            "implementation_status": "implemented_but_waiting_sample",
        }
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [previous_order],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=1)

    order = report["orders"][0]
    assert order["order_id"] == "order_sparse_current"
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "existing_family"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0


def test_build_code_improvement_workorder_does_not_escalate_rejudged_not_applicable(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    current_order = {
        "order_id": "order_not_applicable_repeat",
        "title": "Not applicable explicit repeat",
        "source_report_type": "scalping_pattern_lab_automation",
        "target_subsystem": "entry_funnel",
        "lifecycle_stage": "entry",
        "improvement_type": "source_quality_gap",
        "route": "existing_family",
        "mapped_family": "lifecycle_decision_matrix_runtime",
        "priority": 5,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_provenance": {
            "recommended_resolution": "mark_not_applicable_explicitly",
        },
        "files_likely_touched": [],
        "acceptance_tests": [],
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-06-09", "2026-06-08"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [{**current_order, "decision": "attach_existing_family"}],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-06-10", max_orders=1)

    order = report["orders"][0]
    assert order["order_id"] == "order_not_applicable_repeat"
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "existing_family"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0
    assert (
        report["summary"]["selected_implement_now_new_runtime_effect_false_count"] == 0
    )


def test_build_code_improvement_workorder_marks_terminal_non_implement_items(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    orders = [
        {
            "order_id": "order_design_only",
            "title": "Design-only report candidate",
            "source_report_type": "scalping_pattern_lab_automation",
            "target_subsystem": "entry_funnel",
            "route": "auto_family_candidate",
            "priority": 1,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        {
            "order_id": "order_defer_only",
            "title": "Defer evidence only",
            "source_report_type": "scalping_pattern_lab_automation",
            "target_subsystem": "entry_funnel",
            "improvement_type": "pattern_lab_observation",
            "route": "attach_existing_family",
            "mapped_family": "existing_family",
            "priority": 2,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        {
            "order_id": "order_not_applicable_terminal",
            "title": "Not applicable explicit terminal",
            "source_report_type": "scalping_pattern_lab_automation",
            "target_subsystem": "entry_funnel",
            "route": "existing_family",
            "mapped_family": "lifecycle_decision_matrix_runtime",
            "priority": 3,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "implementation_status": "open",
            "implementation_provenance": {
                "recommended_resolution": "mark_not_applicable_explicitly",
            },
        },
    ]
    (automation_dir / "scalping_pattern_lab_automation_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": orders,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-06-10", max_orders=10)

    by_id = {item["order_id"]: item for item in report["orders"]}
    assert (
        by_id["order_design_only"]["implementation_status"]
        == "terminal_design_family_candidate"
    )
    assert (
        by_id["order_defer_only"]["implementation_status"]
        == "terminal_existing_family_evidence"
    )
    assert (
        by_id["order_not_applicable_terminal"]["implementation_status"]
        == "terminal_not_applicable_evidence"
    )
    assert report["summary"]["selected_unimplemented_runtime_effect_false_count"] == 0
    assert (
        report["summary"]["selected_terminal_non_implement_runtime_effect_false_count"]
        == 3
    )


def test_build_code_improvement_workorder_does_not_escalate_terminal_non_implement_history(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    current_order = {
        "order_id": "order_terminal_history",
        "title": "Terminal history should not re-escalate",
        "source_report_type": "scalping_pattern_lab_automation",
        "target_subsystem": "entry_funnel",
        "route": "auto_family_candidate",
        "priority": 1,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-06-09", "2026-06-08"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {
                            **current_order,
                            "decision": "design_family_candidate",
                            "implementation_status": "terminal_design_family_candidate",
                        }
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-06-10", max_orders=10)

    order = report["orders"][0]
    assert order["decision"] == "design_family_candidate"
    assert order["implementation_status"] == "terminal_design_family_candidate"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0
    assert (
        report["summary"]["selected_implement_now_new_runtime_effect_false_count"] == 0
    )


def test_build_code_improvement_workorder_marks_longstanding_actionable_existing_family_recheck(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    current_order = {
        "order_id": "order_swing_existing_family_metric_review",
        "title": "Swing existing family metric review",
        "source_report_type": "swing_improvement_automation",
        "target_subsystem": "swing_entry",
        "lifecycle_stage": "entry",
        "improvement_type": "threshold_family_input",
        "route": "existing_family",
        "mapped_family": "swing_gatekeeper_accept_reject",
        "threshold_family": "swing_gatekeeper_accept_reject",
        "files_likely_touched": ["src/engine/swing_lifecycle_audit.py"],
        "acceptance_tests": ["pytest swing lifecycle audit tests"],
        "priority": 1,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "swing_improvement_automation_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-06-09", "2026-06-08"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {
                            **current_order,
                            "decision": "attach_existing_family",
                            "implementation_status": "terminal_existing_family_evidence",
                        }
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-scalp")
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-06-10", max_orders=10)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_swing_existing_family_metric_review"
    )
    assert order["decision"] == "attach_existing_family"
    assert order["implementation_status"] == "terminal_existing_family_evidence"
    assert order["longstanding_non_implement_review"]["review_disposition"] == (
        "actionable_existing_family_recheck"
    )
    assert order["longstanding_non_implement_action"]["action_required"] is True
    assert report["summary"][
        "selected_longstanding_non_implement_disposition_counts"
    ] == {"actionable_existing_family_recheck": 1}
    assert report["summary"][
        "selected_longstanding_non_implement_action_required_order_ids"
    ] == ["order_swing_existing_family_metric_review"]
    assert (
        report["summary"]["selected_implement_now_new_runtime_effect_false_count"] == 0
    )
    markdown = mod.render_code_improvement_workorder_markdown(report)
    assert "selected_longstanding_non_implement_action_required_order_ids" in markdown
    assert "longstanding_non_implement_action" in markdown
    assert "specific_source_metric_or_provenance_recheck" in markdown


def test_build_code_improvement_workorder_marks_lifecycle_logic_observation_as_actionable_existing_family_recheck(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    current_order = {
        "order_id": "order_swing_scale_in_logic_review",
        "title": "Swing scale-in logic review",
        "source_report_type": "swing_improvement_automation",
        "target_subsystem": "swing_scale_in",
        "lifecycle_stage": "scale_in",
        "improvement_type": "lifecycle_logic_observation",
        "route": "existing_family",
        "mapped_family": "swing_scale_in_ofi_qi_confirmation",
        "threshold_family": "swing_scale_in_ofi_qi_confirmation",
        "files_likely_touched": ["src/engine/swing_lifecycle_audit.py"],
        "acceptance_tests": ["pytest swing lifecycle audit tests"],
        "priority": 1,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "swing_improvement_automation_2026-06-10.json").write_text(
        json.dumps({"date": "2026-06-10", "code_improvement_orders": [current_order]}),
        encoding="utf-8",
    )
    for previous_date in ("2026-06-09", "2026-06-08"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {
                            **current_order,
                            "decision": "attach_existing_family",
                            "implementation_status": "terminal_existing_family_evidence",
                        }
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-scalp")
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-06-10", max_orders=10)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_swing_scale_in_logic_review"
    )
    assert order["longstanding_non_implement_review"]["review_disposition"] == (
        "actionable_existing_family_recheck"
    )
    assert order["longstanding_non_implement_action"]["action_required"] is True


def test_build_code_improvement_workorder_force_selects_longstanding_action_required_orders(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    selected_order = {
        "order_id": "order_selected_existing_family",
        "title": "Selected existing family",
        "source_report_type": "scalping_pattern_lab_automation",
        "target_subsystem": "entry_funnel",
        "improvement_type": "threshold_family_input",
        "route": "existing_family",
        "mapped_family": "buy_score_threshold",
        "threshold_family": "buy_score_threshold",
        "files_likely_touched": ["src/engine/daily_threshold_cycle_report.py"],
        "acceptance_tests": ["pytest threshold tests"],
        "priority": 1,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_status": "implemented",
    }
    current_order = {
        "order_id": "order_non_selected_actionable_recheck",
        "title": "Non-selected actionable recheck",
        "source_report_type": "scalping_pattern_lab_automation",
        "target_subsystem": "entry_funnel",
        "improvement_type": "threshold_family_input",
        "route": "existing_family",
        "mapped_family": "buy_score_threshold",
        "threshold_family": "buy_score_threshold",
        "files_likely_touched": ["src/engine/daily_threshold_cycle_report.py"],
        "acceptance_tests": ["pytest threshold tests"],
        "priority": 99,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (automation_dir / "scalping_pattern_lab_automation_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "code_improvement_orders": [selected_order, current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-06-09", "2026-06-08"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {
                            **selected_order,
                            "decision": "attach_existing_family",
                        },
                        {
                            **current_order,
                            "decision": "defer_evidence",
                            "implementation_status": "terminal_deferred_evidence",
                        },
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-06-10", max_orders=1)

    assert report["summary"][
        "selected_longstanding_non_implement_action_required_order_ids"
    ] == ["order_non_selected_actionable_recheck"]
    assert (
        report["summary"][
            "non_selected_longstanding_non_implement_action_required_order_ids"
        ]
        == []
    )
    markdown = mod.render_code_improvement_workorder_markdown(report)
    assert "selected_longstanding_non_implement_action_required_order_ids" in markdown
    assert "order_non_selected_actionable_recheck" in markdown


def test_build_code_improvement_workorder_does_not_mark_currently_implemented_as_longstanding_non_implement(
    tmp_path,
    monkeypatch,
):
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    current_order = {
        "order_id": "order_swing_existing_family_metric_review",
        "title": "Swing existing family metric review",
        "source_report_type": "swing_improvement_automation",
        "target_subsystem": "swing_entry",
        "lifecycle_stage": "entry",
        "improvement_type": "threshold_family_input",
        "route": "existing_family",
        "mapped_family": "swing_gatekeeper_accept_reject",
        "threshold_family": "swing_gatekeeper_accept_reject",
        "files_likely_touched": ["src/engine/swing_lifecycle_audit.py"],
        "acceptance_tests": ["pytest swing lifecycle audit tests"],
        "priority": 1,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_status": "implemented",
        "implementation_provenance": {
            "source_contract": "swing_gatekeeper_accept_reject_source_metric_v1",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
    }
    (automation_dir / "swing_improvement_automation_2026-06-10.json").write_text(
        json.dumps(
            {
                "date": "2026-06-10",
                "code_improvement_orders": [current_order],
            }
        ),
        encoding="utf-8",
    )
    for previous_date in ("2026-06-09", "2026-06-08"):
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [
                        {
                            **current_order,
                            "implementation_status": "terminal_existing_family_evidence",
                            "implementation_provenance": None,
                        }
                    ],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-scalp")
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-06-10", max_orders=10)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_swing_existing_family_metric_review"
    )
    assert order["implementation_status"] == "implemented"
    review = order.get("longstanding_non_implement_review")
    if review is not None:
        assert review["review_disposition"] == "implemented_with_provenance"
    assert order.get("longstanding_non_implement_action") is None
    assert (
        report["summary"][
            "selected_longstanding_non_implement_action_required_order_ids"
        ]
        == []
    )


def test_build_code_improvement_workorder_does_not_escalate_rejudged_lifecycle_holding_no_files(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "lifecycle_matrix"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    ldm_dir.mkdir()
    report_dir.mkdir()
    ldm_dir.mkdir(parents=True, exist_ok=True)
    lifecycle_report = {
        "holding_bucket_attribution": {
            "parser_version": "1.0.0",
            "code_improvement_workorders": [
                {
                    "bucket_type": "source_quality_gap",
                    "bucket_key": "holding_bucket_001",
                    "reason": "source-quality gap detected in holding bucket",
                    "recommended_route": "instrumentation_order",
                    "workorder_id": "wo_hold_001",
                }
            ],
        },
    }
    (ldm_dir / "lifecycle_decision_matrix_2026-06-10.json").write_text(
        json.dumps(lifecycle_report),
        encoding="utf-8",
    )
    for previous_date in ("2026-06-09", "2026-06-08"):
        previous_order = {
            "order_id": "order_holding_bucket_001_holding_bucket_attribution",
            "title": "LDM holding bucket source-quality follow-up: source_quality_gap=holding_bucket_001",
            "source_report_type": "lifecycle_decision_matrix_holding_bucket_attribution",
            "lifecycle_stage": "holding",
            "target_subsystem": "lifecycle_decision_matrix",
            "route": "instrumentation_order",
            "mapped_family": "lifecycle_decision_matrix_runtime",
            "improvement_type": "holding_bucket_source_quality_child_evidence",
            "priority": 2,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision": "defer_evidence",
            "files_likely_touched": [],
            "acceptance_tests": [],
        }
        (report_dir / f"code_improvement_workorder_{previous_date}.json").write_text(
            json.dumps(
                {
                    "date": previous_date,
                    "orders": [previous_order],
                    "non_selected_orders": [],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-scalping"
    )
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "LIFECYCLE_DECISION_MATRIX_DIR", ldm_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-06-10", max_orders=1)

    order = report["orders"][0]
    assert order["decision"] == "defer_evidence"
    assert report["summary"]["repeat_unresolved_escalation_count"] == 0
    assert (
        report["summary"]["selected_implement_now_new_runtime_effect_false_count"] == 0
    )


def test_lifecycle_bucket_discovery_source_dimension_gap_groups_same_bucket():
    report = {
        "surfaced_candidates": [],
        "source_dimension_gap_summary": {
            "actionable_unknown_gap_count": 2,
            "source_dimension_gap_counts": {"unknown_source_dimensions": 2},
            "actionable_candidates": [
                {
                    "bucket_id": "lifecycle_flow:combo_lifecycle_flow:same",
                    "source_bucket_id": "lifecycle_flow:combo_lifecycle_flow:same:one",
                    "stage": "lifecycle_flow",
                    "bucket_type": "combo_lifecycle_flow",
                    "classification_state": "source_only_keep_collecting",
                    "source_dimension_gap": "unknown_source_dimensions",
                    "recommended_resolution": "resolve_unknown_source_dimensions",
                    "missing_dimension_keys": ["entry"],
                },
                {
                    "bucket_id": "lifecycle_flow:combo_lifecycle_flow:same",
                    "source_bucket_id": "lifecycle_flow:combo_lifecycle_flow:same:two",
                    "stage": "lifecycle_flow",
                    "bucket_type": "combo_lifecycle_flow",
                    "classification_state": "source_only_keep_collecting",
                    "source_dimension_gap": "unknown_source_dimensions",
                    "recommended_resolution": "resolve_unknown_source_dimensions",
                    "missing_dimension_keys": ["entry"],
                },
            ],
        },
    }

    orders = [
        item
        for item in mod._lifecycle_bucket_discovery_followup_orders(report)
        if item["source_report_type"] == "lifecycle_bucket_discovery"
    ]

    assert len(orders) == 1
    assert orders[0]["improvement_type"] == "source_dimension_gap_resolution"


def test_build_code_improvement_workorder_preserves_lifecycle_discovery_handoff_orders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    discovery_dir = tmp_path / "discovery"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    discovery_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-22.json").write_text(
        json.dumps({"date": "2026-05-22", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    bucket_id = "entry:combo_entry_spot:score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_unknown"
    (discovery_dir / "lifecycle_bucket_discovery_2026-05-22.json").write_text(
        json.dumps(
            {
                "metric_role": "source_quality_gate",
                "decision_authority": "postclose_discovery_only",
                "window_policy": "daily_postclose",
                "sample_floor": 1,
                "primary_decision_metric": "source_quality_adjusted_ev_pct",
                "source_quality_gate": "pass",
                "surfaced_candidates": [
                    {
                        "bucket_id": bucket_id,
                        "stage": "entry",
                        "classification_state": "new_bucket_candidate",
                        "bucket_relation": "new",
                        "recommended_action": "code_patch_required",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(
        mod, "SWING_STRATEGY_DISCOVERY_EV_DIR", tmp_path / "missing-swing-discovery"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_DECISION_MATRIX_DIR", tmp_path / "missing-swing-ldm"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR", tmp_path / "missing-swing-bucket"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "LIFECYCLE_DECISION_MATRIX_DIR", tmp_path / "missing-ldm")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(
        mod,
        "_lifecycle_bucket_discovery_report_path",
        lambda target_date: discovery_dir
        / f"lifecycle_bucket_discovery_{target_date}.json",
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-22", max_orders=1)

    order = next(
        item
        for item in report["orders"]
        if item["source_report_type"] == "lifecycle_bucket_discovery"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert order["source_bucket_id"] == bucket_id
    assert order["order_id"].startswith("order_lifecycle_bucket_discovery_entry_")
    assert report["summary"]["lifecycle_bucket_discovery_source_order_count"] == 1


def test_lifecycle_bucket_discovery_greenfield_source_only_exclusion_is_not_active_workorder():
    report = {
        "summary": {
            "greenfield_policy_emit_state": "not_emitted_no_complete_lifecycle_flow"
        },
        "surfaced_candidates": [
            {
                "bucket_id": "lifecycle_flow:combo_lifecycle_flow:blocked",
                "source_bucket_id": "lifecycle_flow:blocked",
                "stage": "lifecycle_flow",
                "classification_state": "runtime_blocked_contract_gap",
                "live_auto_apply_family": "greenfield_real_environment_authority",
                "source_bucket_kind": "live_auto_candidate",
                "source_quality_gate": "pass",
                "source_quality_adjusted_ev_pct": 2.5,
            }
        ],
    }

    assert mod._lifecycle_bucket_discovery_followup_orders(report) == []


def test_lifecycle_bucket_discovery_source_only_new_bucket_is_not_active_workorder():
    report = {
        "surfaced_candidates": [
            {
                "bucket_id": "lifecycle_flow:combo_lifecycle_flow:source-only-new",
                "source_bucket_id": "lifecycle_flow:source-only-new",
                "stage": "lifecycle_flow",
                "classification_state": "new_bucket_candidate",
                "source_bucket_kind": "source_only_observation",
                "recommended_resolution": "instrumentation_gap",
            }
        ],
    }

    assert mod._lifecycle_bucket_discovery_followup_orders(report) == []


def test_lifecycle_bucket_discovery_source_dimension_gap_creates_actionable_workorder():
    report = {
        "surfaced_candidates": [
            {
                "bucket_id": "entry:combo_entry_spot:unknown",
                "source_bucket_id": "entry:combo_entry_spot:unknown",
                "stage": "entry",
                "bucket_type": "combo_entry_spot",
                "classification_state": "source_only_keep_collecting",
                "source_dimension_gap": "unknown_source_dimensions",
                "recommended_resolution": "resolve_unknown_source_dimensions",
                "missing_dimension_keys": ["liquidity_bucket"],
                "unknown_reason_counts": {"missing_source_field": 1},
            }
        ],
    }

    orders = mod._lifecycle_bucket_discovery_followup_orders(report)

    assert len(orders) == 1
    assert orders[0]["order_id"].startswith(
        "order_lifecycle_source_dimension_gap_entry_combo_entry_spot_"
    )
    assert orders[0]["improvement_type"] == "source_dimension_gap_resolution"
    assert orders[0]["priority"] == 1
    assert "source_dimension_gap=unknown_source_dimensions" in orders[0]["evidence"]


def test_lifecycle_bucket_discovery_source_dimension_gap_summary_creates_workorder_when_candidate_truncated():
    report = {
        "surfaced_candidates": [],
        "source_dimension_gap_summary": {
            "actionable_unknown_gap_count": 1,
            "source_dimension_gap_counts": {"unknown_source_dimensions": 1},
            "actionable_candidates": [
                {
                    "bucket_id": "entry:combo_entry_spot:summary-only",
                    "source_bucket_id": "entry:combo_entry_spot:summary-only",
                    "stage": "entry",
                    "bucket_type": "combo_entry_spot",
                    "classification_state": "source_only_keep_collecting",
                    "source_dimension_gap": "unknown_source_dimensions",
                    "recommended_resolution": "resolve_unknown_source_dimensions",
                    "missing_dimension_keys": ["liquidity_bucket"],
                }
            ],
        },
    }

    orders = mod._lifecycle_bucket_discovery_followup_orders(report)

    assert len(orders) == 1
    assert orders[0]["source_bucket_id"] == "entry:combo_entry_spot:summary-only"
    assert orders[0]["improvement_type"] == "source_dimension_gap_resolution"


def test_lifecycle_bucket_discovery_rollup_gap_is_not_implement_now():
    order = {
        "order_id": "order_lifecycle_source_dimension_gap_rollup",
        "source_report_type": "lifecycle_bucket_discovery_source_dimension_rollup",
        "route": "source_dimension_rollup",
        "runtime_effect": False,
    }

    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert classified.decision == "attach_existing_family"
    assert classified.route == "source_dimension_rollup"


def test_lifecycle_bucket_discovery_join_gap_enrichment_creates_source_only_workorder():
    report = {
        "surfaced_candidates": [],
        "source_dimension_gap_summary": {
            "rollup_only_gap_count": 1,
            "source_dimension_gap_counts": {"unknown_source_dimensions": 1},
            "join_gap_enrichment": {
                "candidate_count": 2,
                "stage_counts": {"exit": 2},
                "bucket_type_counts": {"exit_rule": 2},
                "recommended_resolution_counts": {
                    "join_labels_before_bucket_decision": 2
                },
                "missing_dimension_key_counts": {"exit": 2},
                "recommended_next_action": "enrich_bucket_label_or_join_key_before_bucket_decision",
            },
        },
    }

    orders = mod._lifecycle_bucket_discovery_followup_orders(report)
    order = [
        item
        for item in orders
        if item["order_id"] == "order_lifecycle_source_dimension_join_gap_enrichment"
    ][0]

    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert order["improvement_type"] == "source_dimension_join_gap_enrichment"
    assert "join_gap_candidate_count=2" in order["evidence"]
    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "attach_existing_family"
    assert classified.route == "join_gap_enrichment"


def test_lifecycle_bucket_discovery_quiet_gap_rollup_orders_are_attach_existing_family():
    report = {
        "quiet_gap_summary": {
            "quiet_gap_count": 3,
            "rollup_required_count": 3,
            "sim_live_connected_quiet_gap_count": 0,
            "quiet_gap_type_counts": {
                "parent_conflict_child": 1,
                "exclusion_dimension_candidate": 1,
                "positive_source_only_keep_collecting": 1,
                "ai_review_parsed_low_coverage": 1,
            },
            "ai_review_coverage": {
                "status": "parsed",
                "shard_count": 5,
                "parsed_shard_count": 2,
            },
        },
        "surfaced_candidates": [],
    }

    orders = mod._lifecycle_bucket_discovery_followup_orders(report)
    quiet_orders = [
        item
        for item in orders
        if item["source_report_type"] == "lifecycle_bucket_discovery_quiet_gap_rollup"
    ]

    assert {item["order_id"] for item in quiet_orders} == {
        "order_lifecycle_quiet_gap_parent_conflict_rollup",
        "order_lifecycle_quiet_gap_positive_source_only_rollup",
        "order_lifecycle_quiet_gap_ai_review_coverage_rollup",
    }
    classified = mod._classify_order(
        quiet_orders[0],
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "attach_existing_family"
    assert classified.route in {
        "parent_conflict_exclusion_review",
        "positive_source_only_review",
        "ai_review_coverage_review",
    }


def test_observation_source_quality_unknown_warning_creates_rollup_order():
    report = {
        "status": "warning",
        "summary": {
            "event_count": 10,
            "warning_stage_count": 1,
            "high_volume_no_source_field_stage_count": 0,
        },
        "stage_contracts": {
            "unlisted_warning_stage": {
                "status": "warning",
                "sample_count": 10,
                "missing_violations": {"metric_role": 10},
            }
        },
    }

    orders = mod._observation_source_quality_followup_orders(report)

    assert len(orders) == 1
    assert orders[0]["order_id"] == "order_observation_source_quality_warning_rollup"
    assert orders[0]["improvement_type"] == "observation_source_quality_warning_rollup"
    classified = mod._classify_order(
        orders[0],
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "attach_existing_family"


def test_observation_source_quality_unknown_token_findings_create_implement_order():
    report = {
        "status": "warning",
        "summary": {
            "event_count": 100,
            "warning_stage_count": 0,
            "high_volume_no_source_field_stage_count": 0,
            "unknown_token_stage_count": 1,
            "review_warning_count": 1,
            "tuning_input_allowed": True,
        },
        "stage_contracts": {},
        "unknown_token_findings": [
            {
                "stage": "latency_block",
                "event_count": 100,
                "fields": [
                    {
                        "field": "custom_context_state",
                        "count": 95,
                        "rate": 0.95,
                        "examples": ["unknown"],
                    }
                ],
            }
        ],
    }

    orders = mod._observation_source_quality_followup_orders(report)
    order = next(
        item
        for item in orders
        if item["order_id"]
        == "order_observation_source_quality_unknown_token_provenance_gap"
    )

    assert order["improvement_type"] == "source_quality_unknown_token_provenance_gap"
    assert order["runtime_effect"] is False
    assert any("unknown:stage=latency_block" in item for item in order["evidence"])
    assert any(
        "top_unknown_fields=custom_context_state" in item for item in order["evidence"]
    )
    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "implement_now"
    assert classified.route == "source_quality_warning_producer_fix"
    serialized = mod._serialize_classified_order(classified)
    assert serialized["forbidden_uses"]
    assert codex_workorder_runner.is_safe_implement_now(serialized)
    _, unsupported = codex_workorder_runner._acceptance_commands([serialized])
    assert unsupported == []


def test_observation_source_quality_arbitrary_unknown_token_routes_to_workorder():
    report = {
        "status": "warning",
        "summary": {
            "event_count": 100,
            "warning_stage_count": 0,
            "high_volume_no_source_field_stage_count": 0,
            "unknown_token_stage_count": 1,
            "review_warning_count": 1,
            "tuning_input_allowed": True,
        },
        "stage_contracts": {},
        "unknown_token_findings": [
            {
                "stage": "arbitrary_source_stage",
                "event_count": 100,
                "fields": [
                    {
                        "field": "custom_context_state",
                        "count": 1,
                        "rate": 0.01,
                        "examples": ["custom_unknown_placeholder"],
                    }
                ],
            }
        ],
    }

    orders = mod._observation_source_quality_followup_orders(report)
    classified = [
        mod._classify_order(
            order,
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
        for order in orders
    ]
    serialized = [mod._serialize_classified_order(item) for item in classified]
    unknown_orders = [
        item
        for item in serialized
        if item["order_id"]
        == "order_observation_source_quality_unknown_token_provenance_gap"
    ]

    assert len(unknown_orders) == 1
    assert unknown_orders[0]["decision"] == "implement_now"
    assert codex_workorder_runner.is_safe_implement_now(unknown_orders[0])
    assert any(
        "custom_context_state:1:0.01" in item for item in unknown_orders[0]["evidence"]
    )


def test_observation_source_quality_raw_row_exclusion_routes_to_implement_now_workorder():
    report = {
        "status": "warning",
        "summary": {
            "event_count": 100,
            "warning_stage_count": 0,
            "high_volume_no_source_field_stage_count": 0,
            "unknown_token_stage_count": 0,
            "review_warning_count": 0,
            "tuning_input_allowed": True,
        },
        "stage_contracts": {},
        "raw_row_exclusion": {
            "manifest_path": "/tmp/raw_row_exclusion/manifest.json",
            "excluded_row_count": 2,
            "stage_counts": {"custom_runtime_context_stage": 2},
            "field_gap_counts": {"missing_fields:source_record_id": 2},
            "exclusion_reasons": {"required_field_missing": 2, "provenance_missing": 2},
            "first_timestamp": "2026-06-05T09:00:00+09:00",
            "last_timestamp": "2026-06-05T09:05:00+09:00",
            "producer_hint": [
                {
                    "stage": "custom_runtime_context_stage",
                    "count": 2,
                    "pipeline": "ENTRY_PIPELINE",
                    "subsystem": "scalping_entry_or_sim_producer",
                    "top_reasons": ["required_field_missing", "provenance_missing"],
                }
            ],
            "sample_rows": [
                {
                    "line_no": 10,
                    "stage": "custom_runtime_context_stage",
                    "record_id": 1,
                    "reasons": ["required_field_missing"],
                    "gap_fields": {"missing_fields": ["source_record_id"]},
                }
            ],
        },
    }

    orders = mod._observation_source_quality_followup_orders(report)
    classified = [
        mod._classify_order(
            order,
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
        for order in orders
    ]
    serialized = [mod._serialize_classified_order(item) for item in classified]
    raw_orders = [
        item
        for item in serialized
        if item["order_id"]
        == "order_observation_source_quality_raw_row_exclusion_producer_gap"
    ]

    assert len(raw_orders) == 1
    assert raw_orders[0]["decision"] == "implement_now"
    assert raw_orders[0]["route"] == "source_quality_raw_row_exclusion_producer_fix"
    assert raw_orders[0]["runtime_effect"] is False
    assert codex_workorder_runner.is_safe_implement_now(raw_orders[0])
    assert any("excluded_row_count=2" in item for item in raw_orders[0]["evidence"])
    assert any(
        "custom_runtime_context_stage" in item for item in raw_orders[0]["evidence"]
    )


def test_observation_source_quality_raw_row_exclusion_limit_up_context_is_review_only(
    tmp_path,
):
    manifest_path = tmp_path / "manifest.json"
    rows = []
    for idx in range(6):
        rows.append(
            {
                "line_no": idx + 1,
                "payload": {
                    "stage": (
                        "blocked_overbought"
                        if idx % 2 == 0
                        else "blocked_strength_momentum"
                    ),
                    "stock_code": "003220",
                    "record_id": 9276,
                    "fields": {
                        "fluctuation": "29.94" if idx % 2 == 0 else "",
                        "intraday_range_pct": "0.000",
                    },
                },
            }
        )
    manifest_path.write_text(
        json.dumps({"excluded_rows": rows}, ensure_ascii=False), encoding="utf-8"
    )
    report = {
        "status": "warning",
        "summary": {"event_count": 6, "tuning_input_allowed": True},
        "raw_row_exclusion": {
            "manifest_path": str(manifest_path),
            "excluded_row_count": 6,
            "stage_counts": {"blocked_overbought": 3, "blocked_strength_momentum": 3},
            "field_gap_counts": {"zero_fields:intraday_range_pct": 6},
            "exclusion_reasons": {
                "source_quality_blocker": 6,
                "not_evaluated_context": 3,
                "insufficient_history": 3,
            },
        },
    }

    orders = mod._observation_source_quality_followup_orders(report)
    classified = [
        mod._classify_order(
            order,
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
        for order in orders
    ]
    serialized = [mod._serialize_classified_order(item) for item in classified]
    raw_order = next(
        item
        for item in serialized
        if item["order_id"]
        == "order_observation_source_quality_raw_row_exclusion_producer_gap"
    )

    assert raw_order["decision"] == "attach_existing_family"
    assert raw_order["route"] == "review_required_limit_up_locked_context"
    assert (
        raw_order["improvement_type"]
        == "source_quality_raw_row_exclusion_limit_up_locked_context"
    )
    assert (
        raw_order["raw_row_exclusion_context_classification"]
        == "limit_up_locked_context"
    )
    assert (
        raw_order["terminal_disposition"]
        == "no_code_required_pending_policy_classification"
    )
    assert raw_order["implementation_candidate"] is False
    assert not codex_workorder_runner.is_safe_implement_now(raw_order)
    assert any(
        "context_classification=limit_up_locked_context" in item
        for item in raw_order["evidence"]
    )


def test_observation_source_quality_raw_row_exclusion_market_halt_context_is_review_only(
    tmp_path,
):
    report = {
        "status": "warning",
        "summary": {"event_count": 10, "tuning_input_allowed": True},
        "raw_row_exclusion": {
            "excluded_row_count": 10,
            "stage_counts": {"blocked_strength_momentum": 10},
            "field_gap_counts": {"zero_fields:intraday_range_pct": 10},
            "exclusion_reasons": {
                "zero_context_sensitive": 10,
                "insufficient_history": 10,
            },
            "market_halt_or_circuit_window_overlap": True,
            "market_halt_or_circuit_context": {
                "classification": "market_halt_or_circuit_window_overlap",
                "overlap_excluded_row_count": 10,
                "after_normal_flow_excluded_row_count": 0,
                "normal_flow_check_after": "2026-06-08T09:35:00",
            },
        },
    }

    orders = mod._observation_source_quality_followup_orders(report)
    classified = [
        mod._classify_order(
            order,
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
        for order in orders
    ]
    serialized = [mod._serialize_classified_order(item) for item in classified]
    raw_order = next(
        item
        for item in serialized
        if item["order_id"]
        == "order_observation_source_quality_raw_row_exclusion_producer_gap"
    )

    assert raw_order["decision"] == "attach_existing_family"
    assert raw_order["route"] == "review_required_market_halt_context"
    assert (
        raw_order["improvement_type"]
        == "source_quality_raw_row_exclusion_market_halt_context"
    )
    assert (
        raw_order["raw_row_exclusion_context_classification"]
        == "market_halt_or_circuit_window_overlap"
    )
    assert (
        raw_order["terminal_disposition"]
        == "no_code_required_pending_policy_classification"
    )
    assert raw_order["implementation_candidate"] is False
    assert not codex_workorder_runner.is_safe_implement_now(raw_order)
    assert any(
        "context_classification=market_halt_or_circuit_window_overlap" in item
        for item in raw_order["evidence"]
    )


def test_observation_source_quality_raw_row_exclusion_routes_even_when_audit_status_passes():
    report = {
        "status": "pass",
        "summary": {"event_count": 2, "tuning_input_allowed": True},
        "raw_row_exclusion": {
            "excluded_row_count": 1,
            "stage_counts": {"custom_stage": 1},
            "exclusion_reasons": {"required_field_missing": 1},
        },
    }

    orders = mod._observation_source_quality_followup_orders(report)

    assert any(
        item["order_id"]
        == "order_observation_source_quality_raw_row_exclusion_producer_gap"
        for item in orders
    )


def test_observation_source_quality_known_fixed_unknown_tokens_attach_existing_family():
    report = {
        "status": "warning",
        "summary": {
            "event_count": 100,
            "warning_stage_count": 0,
            "high_volume_no_source_field_stage_count": 0,
            "unknown_token_stage_count": 1,
            "review_warning_count": 1,
            "tuning_input_allowed": True,
        },
        "stage_contracts": {},
        "unknown_token_findings": [
            {
                "stage": "latency_block",
                "event_count": 100,
                "fields": [
                    {
                        "field": "swing_micro_ws_quote_stale",
                        "count": 100,
                        "rate": 1.0,
                        "examples": ["unknown"],
                    }
                ],
            }
        ],
    }

    order = next(
        item
        for item in mod._observation_source_quality_followup_orders(report)
        if item["order_id"]
        == "order_observation_source_quality_unknown_token_provenance_gap"
    )
    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert order["implementation_status"] == "implemented_but_waiting_sample"
    assert classified.decision == "attach_existing_family"


def test_lifecycle_source_contract_drift_followup_is_existing_source_only_provenance():
    report = {
        "summary": {
            "source_contract_status": "warning",
            "source_contract_change_count": 1,
        },
        "metric_role": "source_quality_provenance",
        "decision_authority": "lifecycle_bucket_discovery_source_only",
        "window_policy": "same_day_source_bundle_plus_rolling_threshold_cycle_consumer",
        "sample_floor": 0,
        "primary_decision_metric": "source_contract_change",
        "source_quality_gate": "source_contract_drift_warning",
        "forbidden_uses": ["runtime_threshold_apply", "broker_submit"],
        "surfaced_candidates": [
            {
                "bucket_id": "source_contract:source_added:entry:source_key_entry",
                "source_bucket_id": "source_contract:source_added:entry:abc",
                "parent_bucket_id": "source_contract:schema_drift",
                "stage": "source_contract",
                "classification_state": "runtime_blocked_contract_gap",
                "canonical_bucket": "source_contract:source_added:entry",
                "legacy_raw_bucket_key": "entry",
                "bucket_alias_version": "lifecycle_bucket_alias_v1",
                "dimension_set_version": "lifecycle_dimension_set_v1",
                "source_bucket_kind": "source_quality_gap",
                "evidence_grade": "source_only",
                "transition_target": "source_only_keep_collecting",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "full_real_conversion_allowed": False,
                "bounded_live_canary_allowed": False,
                "ai_tier2_taxonomy_decision": "instrumentation_gap",
            }
        ],
    }

    order = mod._lifecycle_bucket_discovery_followup_orders(report)[0]
    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert (
        order["implementation_status"]
        == "implemented_source_quality_contract_available"
    )
    assert (
        order["implementation_provenance"]["decision_authority"]
        == "source_contract_drift_detection"
    )
    assert order["actual_order_submitted"] is False
    assert order["broker_order_forbidden"] is True
    assert classified.decision == "attach_existing_family"


def test_producer_gap_ai_review_followup_pass_is_existing_source_only_provenance():
    order = mod._sanitize_producer_gap_order(
        {
            "order_id": "order_producer_gap_discovery_ai_review_followup_2026_07_06",
            "title": "Producer gap AI review follow-up",
            "improvement_type": "ai_review_followup",
            "route": "review_ai_output",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "evidence": [
                "ai_review_followup_reason=missing_ai_tier2_proposal:1",
                "audit_status=pass",
                "forbidden_use_violations=[]",
            ],
        }
    )
    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert (
        order["implementation_status"]
        == "implemented_source_quality_contract_available"
    )
    assert order["implementation_provenance"]["runtime_effect"] is False
    assert order["implementation_provenance"]["broker_order_forbidden"] is True
    assert classified.decision == "attach_existing_family"


def test_observation_source_quality_unknown_token_workorder_evidence_is_not_truncated():
    fields = [
        {
            "field": f"custom_unknown_field_{idx}",
            "count": 1,
            "rate": 0.01,
            "examples": ["unknown"],
        }
        for idx in range(25)
    ]
    report = {
        "status": "warning",
        "summary": {
            "event_count": 100,
            "warning_stage_count": 0,
            "high_volume_no_source_field_stage_count": 0,
            "unknown_token_stage_count": 1,
            "review_warning_count": 1,
            "tuning_input_allowed": True,
        },
        "stage_contracts": {},
        "unknown_token_findings": [
            {
                "stage": "arbitrary_source_stage",
                "event_count": 100,
                "fields": fields,
            }
        ],
    }

    order = next(
        item
        for item in mod._observation_source_quality_followup_orders(report)
        if item["order_id"]
        == "order_observation_source_quality_unknown_token_provenance_gap"
    )

    unknown_evidence = "\n".join(order["evidence"])
    assert "custom_unknown_field_0:1:0.01" in unknown_evidence
    assert "custom_unknown_field_24:1:0.01" in unknown_evidence


def test_swing_lifecycle_matrix_low_event_coverage_creates_rollup_order():
    report = {
        "summary": {
            "raw_swing_event_count": 1200,
            "ldm_consumed_event_count": 5,
            "ldm_event_coverage_rate": 0.004167,
            "unmapped_swing_stage_counts": {"swing_custom_event": 1195},
        }
    }

    orders = mod._swing_lifecycle_matrix_followup_orders(report)

    assert orders[0]["order_id"] == "order_swing_ldm_event_coverage_rollup"
    assert orders[0]["runtime_effect"] is False
    assert orders[0]["allowed_runtime_apply"] is False


def test_swing_lifecycle_matrix_nan_event_coverage_creates_rollup_order():
    report = {
        "summary": {
            "raw_swing_event_count": 1200,
            "ldm_consumed_event_count": 5,
            "ldm_event_coverage_rate": "nan",
            "unmapped_swing_stage_counts": {"swing_custom_event": 1195},
        }
    }

    orders = mod._swing_lifecycle_matrix_followup_orders(report)

    assert orders[0]["order_id"] == "order_swing_ldm_event_coverage_rollup"
    assert "ldm_event_coverage_rate=0.0" in orders[0]["evidence"]


def test_swing_lifecycle_bucket_discovery_contract_and_ai_review_rollups_are_source_only():
    report = {
        "summary": {
            "sim_auto_review_shard_count": 2,
            "sim_auto_reviewed_candidate_count": 20,
            "sim_auto_unreviewed_candidate_count": 1,
            "sim_auto_downgraded_by_review_count": 1,
            "ai_review_followup_reasons": [
                "sim_policy_review_2:ai_review_response_missing"
            ],
        },
        "surfaced_candidates": [
            {
                "candidate_id": "swing:missing-stage",
                "bucket_id": "swing:missing-stage",
                "classification_state": "source_only_keep_collecting",
            }
        ],
        "code_improvement_workorders": [],
    }

    orders = mod._swing_lifecycle_bucket_discovery_followup_orders(report)
    order_ids = {item["order_id"] for item in orders}

    assert "order_swing_lifecycle_bucket_discovery_contract_rollup" in order_ids
    assert "order_swing_lifecycle_bucket_discovery_ai_review_rollup" in order_ids
    assert all(item["runtime_effect"] is False for item in orders)
    assert all(item["allowed_runtime_apply"] is False for item in orders)


def test_swing_lifecycle_bucket_discovery_provider_unavailable_ai_review_is_hold():
    report = {
        "summary": {
            "ai_review_blocker_state": "provider_unavailable",
            "ai_review_followup_required": False,
            "ai_review_followup_reasons": [],
            "sim_auto_review_shard_count": 1,
            "sim_auto_reviewed_candidate_count": 0,
            "sim_auto_unreviewed_candidate_count": 7,
            "sim_auto_downgraded_by_review_count": 7,
        },
        "surfaced_candidates": [],
        "code_improvement_workorders": [],
    }

    orders = mod._swing_lifecycle_bucket_discovery_followup_orders(report)
    order = next(
        item
        for item in orders
        if item["order_id"] == "order_swing_lifecycle_bucket_discovery_ai_review_rollup"
    )
    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert order["implementation_status"] == "implemented_but_waiting_sample"
    assert classified.decision == "attach_existing_family"
    assert classified.route == "existing_family"


def test_swing_lifecycle_bucket_discovery_ai_review_rollup_order_carries_implemented_provenance():
    report = {
        "summary": {
            "sim_auto_review_shard_count": 2,
            "sim_auto_reviewed_candidate_count": 14,
            "sim_auto_unreviewed_candidate_count": 20,
            "sim_auto_downgraded_by_review_count": 20,
            "ai_review_blocker_state": "sim_policy_followup_required",
            "ai_review_followup_required": True,
            "ai_review_followup_reasons": ["audit_status_missing"],
        },
        "surfaced_candidates": [],
        "code_improvement_workorders": [],
    }

    orders = mod._swing_lifecycle_bucket_discovery_followup_orders(report)
    order = next(
        item
        for item in orders
        if item["order_id"] == "order_swing_lifecycle_bucket_discovery_ai_review_rollup"
    )

    assert order["implementation_status"] == "implemented"
    assert (
        order["implementation_provenance"]["implementation_type"]
        == "swing_bucket_ai_review_shard_rollup"
    )
    assert order["implementation_provenance"]["sim_auto_reviewed_candidate_count"] == 14
    assert (
        order["implementation_provenance"]["root_cause_closure_status_hint"]
        == "root_cause_closed"
    )


def test_build_code_improvement_workorder_consumes_pattern_lab_currentness_audit(
    tmp_path, monkeypatch
):
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
                        "files_likely_touched": ["src/engine/pattern_lab_ai_review.py"],
                        "acceptance_tests": [
                            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py"
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
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


def test_build_code_improvement_workorder_preserves_observability_order_source(
    tmp_path, monkeypatch
):
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
                        "order_id": "order_tuning_observability_performance_tuning_missing_contract_gap",
                        "title": "observability source contract gap",
                        "source_report_type": "tuning_observability_summary",
                        "target_subsystem": "pattern_lab",
                        "priority": 1,
                        "route": "source_contract_gap",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", currentness_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=1)

    order = report["orders"][0]
    assert order["source_report_type"] == "tuning_observability_summary"
    assert order["route"] == "source_contract_gap"
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False


def test_build_code_improvement_workorder_consumes_microstructure_reaction_context_orders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    microstructure_dir = tmp_path / "microstructure_reaction_context"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    microstructure_dir.mkdir()
    target_date = "2026-05-16"
    (automation_dir / f"scalping_pattern_lab_automation_{target_date}.json").write_text(
        json.dumps({"date": target_date, "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (
        microstructure_dir / f"microstructure_reaction_context_{target_date}.json"
    ).write_text(
        json.dumps(
            {
                "date": target_date,
                "report_type": "microstructure_reaction_context",
                "runtime_effect": False,
                "code_improvement_orders": [
                    {
                        "order_id": "order_microstructure_ka10046_received_timestamp_gap",
                        "title": "ka10046 REST strength received timestamp gap",
                        "target_subsystem": "market_data_provenance",
                        "priority": 1,
                        "route": "instrumentation_order",
                        "runtime_effect": True,
                        "allowed_runtime_apply": True,
                        "actual_order_submitted": True,
                        "broker_order_forbidden": False,
                        "files_likely_touched": [
                            "src/engine/scalping/microstructure_reaction_context.py"
                        ],
                        "acceptance_tests": [
                            "PYTHONPATH=. .venv/bin/pytest -q "
                            "src/tests/test_microstructure_reaction_context_report.py"
                        ],
                    },
                    {
                        "order_id": "order_microstructure_signed_tape_runtime_candidate_review",
                        "title": "signed tape runtime candidate review",
                        "target_subsystem": "scalping_entry_source_quality",
                        "priority": 2,
                        "route": "auto_family_candidate",
                        "candidate_family": "microstructure_signed_tape_runtime_candidate",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(mod, "MICROSTRUCTURE_REACTION_CONTEXT_DIR", microstructure_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder(target_date, max_orders=5)

    order_by_id = {order["order_id"]: order for order in report["orders"]}
    timestamp_order = order_by_id["order_microstructure_ka10046_received_timestamp_gap"]
    assert timestamp_order["source_report_type"] == "microstructure_reaction_context"
    assert timestamp_order["decision"] == "implement_now"
    assert timestamp_order["runtime_effect"] is False
    assert timestamp_order["allowed_runtime_apply"] is False
    assert timestamp_order["actual_order_submitted"] is False
    assert timestamp_order["broker_order_forbidden"] is True
    candidate_order = order_by_id[
        "order_microstructure_signed_tape_runtime_candidate_review"
    ]
    assert candidate_order["decision"] == "design_family_candidate"
    assert candidate_order["allowed_runtime_apply"] is False
    assert report["summary"]["microstructure_reaction_context_source_order_count"] == 2
    assert report["source"]["microstructure_reaction_context"] == str(
        microstructure_dir / f"microstructure_reaction_context_{target_date}.json"
    )
    markdown = (doc_dir / f"code_improvement_workorder_{target_date}.md").read_text(
        encoding="utf-8"
    )
    assert "microstructure_reaction_context_source_order_count" in markdown
    assert "order_microstructure_ka10046_received_timestamp_gap" in markdown


def test_build_code_improvement_workorder_consumes_pattern_lab_ai_review(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    ai_review_dir = tmp_path / "ai-review"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    ai_review_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-15.json").write_text(
        json.dumps({"date": "2026-05-15", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (ai_review_dir / "pattern_lab_ai_review_2026-05-15.json").write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {"workorder_count": 1},
                "code_improvement_orders": [
                    {
                        "order_id": "order_pattern_lab_ai_review_currentness_gap",
                        "title": "pattern lab ai reviewed gap",
                        "target_subsystem": "pattern_lab",
                        "priority": 1,
                        "route": "implement_now",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "files_likely_touched": ["src/engine/pattern_lab_ai_review.py"],
                        "acceptance_tests": [
                            "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py"
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AI_REVIEW_DIR", ai_review_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=2)

    order = report["orders"][0]
    assert order["source_report_type"] == "pattern_lab_ai_review"
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert report["summary"]["pattern_lab_ai_review_source_order_count"] == 1
    assert report["source"]["pattern_lab_ai_review"] == str(
        ai_review_dir / "pattern_lab_ai_review_2026-05-15.json"
    )


def test_pattern_lab_ai_review_without_code_contract_is_not_implement_now():
    classified = mod._classify_order(
        {
            "order_id": "order_pattern_lab_ai_review_no_contract",
            "title": "pattern lab ai review no code contract",
            "source_report_type": "pattern_lab_ai_review",
            "target_subsystem": "pattern_lab_ai_review",
            "route": "implement_now",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert classified.decision == "defer_evidence"
    assert "no files_likely_touched" in classified.reason


def test_pattern_lab_ai_review_generic_followup_is_review_evidence_not_implementation():
    classified = mod._classify_order(
        {
            "order_id": "order_pattern_lab_ai_review_ai_review_followup_2026_06_04",
            "title": "Resolve Pattern Lab AI review follow-up",
            "source_report_type": "pattern_lab_ai_review",
            "target_subsystem": "pattern_lab_ai_review",
            "improvement_type": "ai_review_followup",
            "route": "review_ai_output",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "files_likely_touched": ["src/engine/pattern_lab_ai_review.py"],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py"
            ],
        },
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert classified.decision == "defer_evidence"
    assert classified.route == "pattern_lab_ai_review_followup_evidence"


def test_pattern_lab_ai_review_automation_handoff_gap_is_evidence_not_duplicate_implementation():
    order = {
        "order_id": "order_pattern_lab_ai_review_scalping_pattern_lab_automation",
        "title": "Pattern Lab AI review follow-up: scalping_pattern_lab_automation",
        "source_report_type": "pattern_lab_ai_review",
        "target_subsystem": "pattern_lab",
        "improvement_type": "automation_handoff_gap",
        "route": "implement_now",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }

    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert classified.decision == "attach_existing_family"
    assert classified.route == "pattern_lab_ai_review_handoff_evidence"
    assert classified.mapped_family == "pattern_lab_feedback_handoff"


def test_build_code_improvement_workorder_force_selects_producer_gap_orders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    producer_gap_dir = tmp_path / "producer-gap"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    producer_gap_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-26.json").write_text(
        json.dumps(
            {
                "date": "2026-05-26",
                "code_improvement_orders": [
                    {
                        "order_id": "order_low_priority_normal",
                        "title": "low priority normal",
                        "priority": 1,
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (producer_gap_dir / "producer_gap_discovery_2026-05-26.json").write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {"workorder_count": 1},
                "code_improvement_orders": [
                    {
                        "order_id": "order_producer_gap_discovery_time_window_policy_exception",
                        "title": "Implement missing producer: time_window_policy_exception_missing",
                        "target_subsystem": "postclose_source_producer",
                        "priority": 10,
                        "producer_gap_priority": "high",
                        "route": "implement_now",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(mod, "PRODUCER_GAP_DISCOVERY_DIR", producer_gap_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-26", max_orders=1)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert (
        decisions["order_producer_gap_discovery_time_window_policy_exception"]
        == "implement_now"
    )
    order = next(
        item
        for item in report["orders"]
        if item["order_id"]
        == "order_producer_gap_discovery_time_window_policy_exception"
    )
    assert order["actual_order_submitted"] is False
    assert order["broker_order_forbidden"] is True
    assert report["summary"]["producer_gap_discovery_source_order_count"] == 1
    assert report["summary"]["producer_gap_discovery_high_priority_selected"] is True
    assert report["source"]["producer_gap_discovery"] == str(
        producer_gap_dir / "producer_gap_discovery_2026-05-26.json"
    )
    assert (
        "Runtime hook candidate:"
        not in mod.render_code_improvement_workorder_markdown(report)
    )


def test_build_code_improvement_workorder_exposes_non_selected_source_orders(
    tmp_path, monkeypatch
):
    target_date = "2099-01-03"
    automation_dir = tmp_path / "automation"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    (automation_dir / f"scalping_pattern_lab_automation_{target_date}.json").write_text(
        json.dumps(
            {
                "date": target_date,
                "solo_findings": [
                    {
                        "order_id": "order_deferred_solo",
                        "confidence": "solo",
                    }
                ],
                "code_improvement_orders": [
                    {
                        "order_id": "order_runtime_instrumentation",
                        "title": "runtime instrumentation",
                        "target_subsystem": "runtime_instrumentation",
                        "priority": 1,
                        "runtime_effect": False,
                    },
                    {
                        "order_id": "order_deferred_solo",
                        "title": "single lab candidate",
                        "target_subsystem": "entry_funnel",
                        "priority": 9,
                        "runtime_effect": False,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(
        mod, "PRODUCER_GAP_DISCOVERY_DIR", tmp_path / "missing-producer-gap"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder(target_date, max_orders=1)

    assert [item["order_id"] for item in report["orders"]] == [
        "order_runtime_instrumentation"
    ]
    assert report["non_selected_orders"][0]["order_id"] == "order_deferred_solo"
    assert report["non_selected_orders"][0]["decision"] == "defer_evidence"
    assert report["summary"]["non_selected_order_count"] == 1
    assert report["summary"]["non_selected_decision_counts"] == {"defer_evidence": 1}
    assert report["deferred_or_rejected_count"] == 1
    markdown = mod.render_code_improvement_workorder_markdown(report)
    assert "## Non-Selected Source Orders" in markdown
    assert "order_deferred_solo" in markdown


def test_build_code_improvement_workorder_strips_producer_gap_runtime_hook_candidate_contract(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    producer_gap_dir = tmp_path / "producer-gap"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    producer_gap_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-26.json").write_text(
        json.dumps({"date": "2026-05-26", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    hook_contract = {
        "hook_name": "holding_flow_runner_debounce_guard",
        "stage": "holding_exit",
        "initial_authority": "source_only_proposal",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "apply_boundary": "postclose_artifact_to_next_preopen_candidate_only",
        "action_namespace": ["EXIT_CONFIRM", "HOLD_REVIEW", "TRIM"],
        "eligible_after": ["dedicated_source_only_producer_implemented"],
        "safety_vetoes": ["hard_stop", "protect_stop", "emergency_stop"],
        "rollback_guards": ["max_defer_seconds_exceeded"],
        "required_source_artifacts": ["runner_regime_counterfactual_producer"],
        "required_ev_evidence": ["completed_sim_equal_weight_avg_profit_pct_positive"],
        "forbidden_uses": ["hard stop override", "broker guard bypass"],
    }
    (producer_gap_dir / "producer_gap_discovery_2026-05-26.json").write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {"workorder_count": 1},
                "code_improvement_orders": [
                    {
                        "order_id": "order_producer_gap_discovery_runner",
                        "title": "Implement missing producer: sim_holding_runner_gap_missing",
                        "target_subsystem": "runner_regime_counterfactual_producer",
                        "priority": 10,
                        "producer_gap_priority": "high",
                        "route": "implement_now",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "runtime_hook_candidate_contract": hook_contract,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(mod, "PRODUCER_GAP_DISCOVERY_DIR", producer_gap_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-26", max_orders=1)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_producer_gap_discovery_runner"
    )
    assert order["runtime_hook_candidate_contract"] is None
    markdown = mod.render_code_improvement_workorder_markdown(report)
    assert "Runtime hook candidate:" not in markdown


def test_build_code_improvement_workorder_consumes_stage_hook_workorders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    stage_hook_dir = tmp_path / "stage-hook"
    scaffold_dir = tmp_path / "stage-hook-scaffold"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    stage_hook_dir.mkdir()
    scaffold_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-26.json").write_text(
        json.dumps({"date": "2026-05-26", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    contract = {
        "hook_name": "holding_flow_runner_debounce_guard",
        "hook_class": "runtime_arbitration_hook",
        "stage": "holding",
        "initial_authority": "source_only_proposal",
        "readiness_tier": "implementation_workorder_ready",
        "evidence_score": 80.0,
        "action_namespace": ["EXIT_CONFIRM", "HOLD_REVIEW"],
        "required_source_artifacts": ["runner_regime_counterfactual_producer"],
        "required_mapping_tests": ["disabled_initial_runtime_state_test"],
        "rollback_guard_requirements": ["hard_safety_veto_preserved"],
        "forbidden_uses": ["hard stop override", "broker guard bypass"],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    (stage_hook_dir / "stage_hook_workorder_discovery_2026-05-26.json").write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {"workorder_count": 1},
                "code_improvement_orders": [
                    {
                        "order_id": "order_stage_hook_workorder_discovery_runner",
                        "title": "Implement stage hook: holding_flow_runner_debounce_guard",
                        "target_subsystem": "stage_hook.holding_flow_runner_debounce_guard",
                        "priority": 10,
                        "stage_hook_priority": "high",
                        "route": "implement_now",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "initial_runtime_state": "disabled",
                        "requires_separate_runtime_apply_candidate": True,
                        "stage_hook_candidate_contract": contract,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (scaffold_dir / "stage_hook_runtime_scaffold_2026-05-26.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "implemented_hooks": [
                    {
                        "hook_name": "holding_flow_runner_debounce_guard",
                        "implementation_status": "implemented",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "initial_runtime_state": "disabled",
                        "requires_separate_runtime_apply_candidate": True,
                        "implementation_files": [
                            "src/engine/automation/stage_hook_runtime_scaffold.py"
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(
        mod, "PRODUCER_GAP_DISCOVERY_DIR", tmp_path / "missing-producer-gap"
    )
    monkeypatch.setattr(mod, "STAGE_HOOK_WORKORDER_DISCOVERY_DIR", stage_hook_dir)
    monkeypatch.setattr(mod, "STAGE_HOOK_RUNTIME_SCAFFOLD_DIR", scaffold_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-26", max_orders=1)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_stage_hook_workorder_discovery_runner"
    )
    assert order["source_report_type"] == "stage_hook_workorder_discovery"
    assert (
        order["stage_hook_candidate_contract"]["hook_name"]
        == "holding_flow_runner_debounce_guard"
    )
    assert order["initial_runtime_state"] == "disabled"
    assert order["requires_separate_runtime_apply_candidate"] is True
    assert order["implementation_status"] == "implemented"
    assert order["decision"] == "attach_existing_family"
    markdown = mod.render_code_improvement_workorder_markdown(report)
    assert "Stage hook candidate:" in markdown
    assert "holding_flow_runner_debounce_guard" in markdown


def test_build_code_improvement_workorder_auto_selects_buy_funnel_submit_drought(
    tmp_path, monkeypatch
):
    target_date = "2099-01-02"
    automation_dir = tmp_path / "automation"
    sentinel_dir = tmp_path / "buy-funnel"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    sentinel_dir.mkdir()
    (automation_dir / f"scalping_pattern_lab_automation_{target_date}.json").write_text(
        json.dumps({"date": target_date, "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (sentinel_dir / f"buy_funnel_sentinel_{target_date}.json").write_text(
        json.dumps(
            {
                "classification": {"primary": "SUBMIT_DROUGHT_CRITICAL"},
                "current": {
                    "session": {
                        "stage_unique": {
                            "ai_confirmed": 52,
                            "budget_pass": 18,
                            "latency_pass": 7,
                            "order_bundle_submitted": 3,
                        },
                        "ratios": {
                            "submitted_to_ai_unique_pct": 5.77,
                            "submitted_to_budget_unique_pct": 16.67,
                        },
                        "blocker_top": [{"label": "latency_block", "count": 15}],
                        "upstream_blocker_top": [
                            {"label": "blocked_ai_score", "count": 8}
                        ],
                        "latency_blocker_top": [
                            {"label": "spread_too_wide", "count": 11}
                        ],
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(
        mod, "SWING_STRATEGY_DISCOVERY_EV_DIR", tmp_path / "missing-swing-discovery"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_DECISION_MATRIX_DIR", tmp_path / "missing-swing-ldm"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR", tmp_path / "missing-swing-bucket"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "LIFECYCLE_DECISION_MATRIX_DIR", tmp_path / "missing-ldm")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(mod, "BUY_FUNNEL_SENTINEL_DIR", sentinel_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder(target_date, max_orders=1)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_entry_submit_drought_auto_resolution"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert order["source_report_type"] == "buy_funnel_sentinel"
    assert order["mapped_family"] == "lifecycle_decision_matrix_runtime"
    assert "submitted_to_ai_pct=5.77" in order["evidence"]
    assert report["summary"]["buy_funnel_sentinel_source_order_count"] == 6
    assert report["summary"]["buy_funnel_sentinel_primary"] == "SUBMIT_DROUGHT_CRITICAL"
    assert report["summary"]["entry_submit_drought_selected"] is True
    assert report["summary"]["entry_submit_drought_handoff_missing"] is False
    assert report["source"]["buy_funnel_sentinel"] == str(
        sentinel_dir / f"buy_funnel_sentinel_{target_date}.json"
    )


def test_build_code_improvement_workorder_marks_submit_drought_artifact_regeneration_required(
    tmp_path, monkeypatch
):
    target_date = "2099-01-03"
    automation_dir = tmp_path / "automation"
    sentinel_dir = tmp_path / "buy-funnel"
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    sentinel_dir.mkdir()
    ldm_dir.mkdir()
    (automation_dir / f"scalping_pattern_lab_automation_{target_date}.json").write_text(
        json.dumps({"date": target_date, "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (sentinel_dir / f"buy_funnel_sentinel_{target_date}.json").write_text(
        json.dumps(
            {
                "classification": {
                    "primary": "SUBMIT_DROUGHT_CRITICAL",
                    "submit_drought_root_cause": {
                        "latency_root_cause_counts": {"quote_stale": 9},
                        "quote_freshness_attribution": {
                            "refresh_attempted_count": 0,
                            "refresh_applied_count": 0,
                            "latency_pass_recovered_count": 3,
                        },
                    },
                },
                "entry_submit_drought_contract": {
                    "critical": True,
                    "required_downstream": [
                        "code_improvement_workorder",
                        "lifecycle_decision_matrix.submit_bucket_attribution",
                        "threshold_cycle_ev_report",
                        "runtime_approval_summary",
                        "postclose_verifier",
                    ],
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "broker_order_submit_allowed": False,
                    "observation_breakdown": {
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "broker_order_submit_allowed": False,
                        "decision_authority": "submit_drought_attribution_only",
                        "axis_order": [
                            "UPSTREAM_GATE",
                            "BUDGET_PASS_COLLAPSE",
                            "LATENCY_PRE_SUBMIT",
                            "BROKER_RECEIPT",
                            "SIM_REAL_AUTHORITY",
                            "SOURCE_TAXONOMY_LEAKAGE",
                        ],
                        "axes": {
                            "LATENCY_PRE_SUBMIT": {
                                "status": "observed",
                                "observed_count": 9,
                            },
                            "BROKER_RECEIPT": {
                                "status": "observed",
                                "observed_count": 1,
                            },
                        },
                        "forbidden_uses": [
                            "broker_order_submit",
                            "runtime_apply_candidate",
                            "provider_route_change",
                        ],
                    },
                },
                "current": {
                    "session": {
                        "stage_unique": {
                            "ai_confirmed": 12,
                            "budget_pass": 3,
                            "latency_pass": 1,
                            "order_bundle_submitted": 0,
                        },
                        "ratios": {
                            "submitted_to_ai_unique_pct": 8.33,
                            "submitted_to_budget_unique_pct": 33.33,
                        },
                        "blocker_top": [],
                        "upstream_blocker_top": [],
                        "latency_blocker_top": [],
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ldm_dir / f"lifecycle_decision_matrix_{target_date}.json").write_text(
        json.dumps({"submit_bucket_attribution": {"summary": {"submit_rows": 1}}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(
        mod, "SWING_STRATEGY_DISCOVERY_EV_DIR", tmp_path / "missing-swing-discovery"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_DECISION_MATRIX_DIR", tmp_path / "missing-swing-ldm"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR", tmp_path / "missing-swing-bucket"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "LIFECYCLE_DECISION_MATRIX_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(mod, "BUY_FUNNEL_SENTINEL_DIR", sentinel_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder(target_date, max_orders=1)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_entry_submit_drought_auto_resolution"
    )
    assert order["root_cause_closure_status"] == "artifact_regeneration_required"
    assert order["implementation_provenance"]["artifact_regeneration_required"] is True
    assert report["summary"]["artifact_regeneration_required_count"] >= 1


def test_build_code_improvement_workorder_closes_submit_drought_when_root_cause_is_fully_decomposed(
    tmp_path, monkeypatch
):
    target_date = "2099-01-04"
    automation_dir = tmp_path / "automation"
    sentinel_dir = tmp_path / "buy-funnel"
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    sentinel_dir.mkdir()
    ldm_dir.mkdir()
    (automation_dir / f"scalping_pattern_lab_automation_{target_date}.json").write_text(
        json.dumps({"date": target_date, "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (sentinel_dir / f"buy_funnel_sentinel_{target_date}.json").write_text(
        json.dumps(
            {
                "classification": {
                    "primary": "SUBMIT_DROUGHT_CRITICAL",
                    "submit_drought_root_cause": {
                        "latency_root_cause_counts": {
                            "quote_stale": 9,
                            "spread_microstructure_guard": 6,
                            "spread_or_slippage_guard": 4,
                        },
                        "unknown_latency_reason_count": 0,
                        "unknown_latency_workorder_required": False,
                        "quote_freshness_attribution": {
                            "refresh_attempted_count": 5,
                            "refresh_applied_count": 3,
                            "latency_pass_recovered_count": 1,
                        },
                    },
                },
                "entry_submit_drought_contract": {
                    "critical": True,
                    "required_downstream": [
                        "code_improvement_workorder",
                        "lifecycle_decision_matrix.submit_bucket_attribution",
                        "threshold_cycle_ev_report",
                        "runtime_approval_summary",
                        "postclose_verifier",
                    ],
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "broker_order_submit_allowed": False,
                    "observation_breakdown": {
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "broker_order_submit_allowed": False,
                        "decision_authority": "submit_drought_attribution_only",
                        "axis_order": [
                            "UPSTREAM_GATE",
                            "BUDGET_PASS_COLLAPSE",
                            "LATENCY_PRE_SUBMIT",
                            "BROKER_RECEIPT",
                            "SIM_REAL_AUTHORITY",
                            "SOURCE_TAXONOMY_LEAKAGE",
                        ],
                        "axes": {
                            "LATENCY_PRE_SUBMIT": {
                                "status": "observed",
                                "observed_count": 9,
                            },
                            "BROKER_RECEIPT": {
                                "status": "observed",
                                "observed_count": 1,
                            },
                        },
                        "forbidden_uses": [
                            "broker_order_submit",
                            "runtime_apply_candidate",
                            "provider_route_change",
                        ],
                    },
                },
                "current": {
                    "session": {
                        "stage_unique": {
                            "ai_confirmed": 12,
                            "budget_pass": 3,
                            "latency_pass": 1,
                            "order_bundle_submitted": 0,
                        },
                        "ratios": {
                            "submitted_to_ai_unique_pct": 8.33,
                            "submitted_to_budget_unique_pct": 33.33,
                        },
                        "blocker_top": [],
                        "upstream_blocker_top": [],
                        "latency_blocker_top": [],
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ldm_dir / f"lifecycle_decision_matrix_{target_date}.json").write_text(
        json.dumps(
            {
                "submit_bucket_attribution": {
                    "summary": {
                        "submit_rows": 1,
                        "quote_freshness_attribution_present": True,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(
        mod, "SWING_STRATEGY_DISCOVERY_EV_DIR", tmp_path / "missing-swing-discovery"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_DECISION_MATRIX_DIR", tmp_path / "missing-swing-ldm"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR", tmp_path / "missing-swing-bucket"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "LIFECYCLE_DECISION_MATRIX_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(mod, "BUY_FUNNEL_SENTINEL_DIR", sentinel_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder(target_date, max_orders=1)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_entry_submit_drought_auto_resolution"
    )
    assert order["root_cause_closure_status"] == "root_cause_closed"
    assert (
        order["implementation_provenance"]["root_cause_counts"][
            "spread_microstructure_guard"
        ]
        == 6
    )
    assert (
        order["implementation_provenance"]["root_cause_closure_status_hint"]
        == "root_cause_closed"
    )
    assert (
        order["implementation_provenance"]["observation_breakdown"][
            "decision_authority"
        ]
        == "submit_drought_attribution_only"
    )
    assert order["implementation_provenance"]["observation_axis_status"] == {
        "BROKER_RECEIPT": "observed",
        "LATENCY_PRE_SUBMIT": "observed",
    }


def test_buy_funnel_submit_drought_workorder_uses_matches_when_primary_runtime_ops():
    orders = mod._buy_funnel_sentinel_followup_orders(
        {
            "classification": {
                "primary": "RUNTIME_OPS",
                "matches": ["RUNTIME_OPS", "SUBMIT_DROUGHT_CRITICAL"],
            },
            "current": {
                "session": {
                    "stage_unique": {
                        "ai_confirmed": 235,
                        "budget_pass": 3,
                        "latency_pass": 0,
                        "order_bundle_submitted": 0,
                    },
                    "ratios": {
                        "submitted_to_ai_unique_pct": 0.0,
                        "submitted_to_budget_unique_pct": 0.0,
                    },
                    "blocker_top": [{"label": "blocked_ai_score", "count": 180}],
                    "upstream_blocker_top": [{"label": "score_wait", "count": 120}],
                    "latency_blocker_top": [
                        {"label": "stale_context_or_quote", "count": 64}
                    ],
                }
            },
        }
    )

    assert {order["order_id"] for order in orders} >= {
        "order_entry_submit_drought_auto_resolution",
        "order_entry_post_submit_contract_gap_review",
        "order_entry_broker_receipt_contract_gap_review",
        "order_entry_fill_quality_contract_gap_review",
        "order_entry_telegram_post_submit_contract_gap_review",
        "order_entry_source_taxonomy_contract_gap_review",
    }
    assert orders[0]["priority"] == 0
    assert orders[0]["route"] == "instrumentation_order"
    assert "submitted_unique=0" in orders[0]["evidence"]


def test_buy_funnel_submit_drought_creates_source_taxonomy_gap_workorder():
    orders = mod._buy_funnel_sentinel_followup_orders(
        {
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            },
            "entry_submit_drought_contract": {
                "weak_contract_matches": ["SOURCE_TAXONOMY_LEAKAGE"],
                "required_downstream": ["code_improvement_workorder"],
            },
            "current": {
                "session": {
                    "stage_unique": {
                        "ai_confirmed": 235,
                        "budget_pass": 3,
                        "latency_pass": 0,
                        "order_bundle_submitted": 0,
                    },
                    "ratios": {
                        "submitted_to_ai_unique_pct": 0.0,
                        "submitted_to_budget_unique_pct": 0.0,
                    },
                    "blocker_top": [{"label": "blocked_swing_score_vpw", "count": 64}],
                    "upstream_blocker_top": [],
                    "latency_blocker_top": [],
                }
            },
        }
    )

    taxonomy_order = next(
        item
        for item in orders
        if item["order_id"] == "order_entry_source_taxonomy_contract_gap_review"
    )
    assert taxonomy_order["runtime_effect"] is False
    assert taxonomy_order["allowed_runtime_apply"] is False
    assert taxonomy_order["route"] == "instrumentation_order"
    assert "SOURCE_TAXONOMY_LEAKAGE" in taxonomy_order["weak_contract_matches"]


def test_buy_funnel_submit_drought_creates_all_post_submit_weak_contract_workorders():
    orders = mod._buy_funnel_sentinel_followup_orders(
        {
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            },
            "entry_submit_drought_contract": {
                "required_downstream": [
                    "code_improvement_workorder",
                    "lifecycle_decision_matrix.submit_bucket_attribution",
                    "threshold_cycle_ev_report",
                    "runtime_approval_summary",
                    "postclose_verifier",
                ],
                "weak_contract_matches": ["BROKER_RECEIPT_WEAK"],
                "stage_unique": {"order_bundle_submitted": 17},
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            },
            "current": {
                "session": {
                    "stage_unique": {
                        "ai_confirmed": 235,
                        "budget_pass": 3,
                        "latency_pass": 3,
                        "order_bundle_submitted": 0,
                    },
                    "ratios": {
                        "submitted_to_ai_unique_pct": 0.0,
                        "submitted_to_budget_unique_pct": 0.0,
                    },
                    "blocker_top": [],
                    "upstream_blocker_top": [],
                    "latency_blocker_top": [],
                }
            },
        }
    )

    by_id = {item["order_id"]: item for item in orders}
    for order_id in {
        "order_entry_post_submit_contract_gap_review",
        "order_entry_broker_receipt_contract_gap_review",
        "order_entry_fill_quality_contract_gap_review",
        "order_entry_telegram_post_submit_contract_gap_review",
        "order_entry_source_taxonomy_contract_gap_review",
    }:
        assert by_id[order_id]["runtime_effect"] is False
        assert by_id[order_id]["allowed_runtime_apply"] is False
        assert by_id[order_id]["source_report_type"] == "buy_funnel_sentinel"


def test_buy_funnel_submit_drought_marks_post_submit_gap_when_submit_sample_exists():
    orders = mod._buy_funnel_sentinel_followup_orders(
        {
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            },
            "entry_submit_drought_contract": {
                "required_downstream": [
                    "code_improvement_workorder",
                    "lifecycle_decision_matrix.submit_bucket_attribution",
                    "threshold_cycle_ev_report",
                    "runtime_approval_summary",
                    "postclose_verifier",
                ],
                "weak_contract_matches": ["BROKER_RECEIPT_WEAK"],
                "stage_unique": {"order_bundle_submitted": 17},
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            },
            "current": {
                "session": {
                    "stage_unique": {
                        "ai_confirmed": 235,
                        "budget_pass": 3,
                        "latency_pass": 3,
                        "order_bundle_submitted": 17,
                    },
                    "ratios": {
                        "submitted_to_ai_unique_pct": 7.23,
                        "submitted_to_budget_unique_pct": 100.0,
                    },
                    "blocker_top": [],
                    "upstream_blocker_top": [],
                    "latency_blocker_top": [],
                }
            },
        }
    )

    by_id = {item["order_id"]: item for item in orders}
    order = by_id["order_entry_broker_receipt_contract_gap_review"]
    taxonomy_order = by_id["order_entry_source_taxonomy_contract_gap_review"]

    assert order["implementation_status"] == "open_post_submit_provenance_join_gap"
    assert (
        order["implementation_provenance"]["implementation_type"]
        == "post_submit_provenance_join_gap"
    )
    assert order["implementation_provenance"]["submitted_unique"] == 17
    assert (
        order["implementation_provenance"]["sample_status"]
        == "submitted_sample_exists_broker_or_fill_join_missing"
    )
    assert (
        taxonomy_order["implementation_status"] == "open_source_taxonomy_provenance_gap"
    )
    assert (
        taxonomy_order["implementation_provenance"]["implementation_type"]
        == "source_taxonomy_provenance_gap"
    )
    assert taxonomy_order["implementation_provenance"]["sample_status"] == (
        "submitted_sample_exists_source_taxonomy_missing"
    )
    assert taxonomy_order["implementation_provenance"]["submitted_unique"] == 17


def test_buy_funnel_submit_drought_marks_submit_contract_verified_from_ldm_attribution():
    orders = mod._buy_funnel_sentinel_followup_orders(
        {
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            },
            "entry_submit_drought_contract": {
                "required_downstream": [
                    "code_improvement_workorder",
                    "lifecycle_decision_matrix.submit_bucket_attribution",
                    "threshold_cycle_ev_report",
                    "runtime_approval_summary",
                    "postclose_verifier",
                ],
                "weak_contract_matches": [
                    "BROKER_RECEIPT",
                    "FILL_QUALITY",
                    "TELEGRAM_POST_SUBMIT_ONLY",
                    "SOURCE_TAXONOMY_LEAKAGE",
                ],
                "stage_unique": {"order_bundle_submitted": 17},
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            },
            "current": {
                "session": {
                    "stage_unique": {
                        "ai_confirmed": 235,
                        "budget_pass": 3,
                        "latency_pass": 3,
                        "order_bundle_submitted": 17,
                    },
                    "ratios": {
                        "submitted_to_ai_unique_pct": 7.23,
                        "submitted_to_budget_unique_pct": 100.0,
                    },
                    "blocker_top": [],
                    "upstream_blocker_top": [],
                    "latency_blocker_top": [],
                }
            },
        },
        lifecycle_report={
            "submit_bucket_attribution": {
                "summary": {
                    "submit_rows": 41,
                    "contract_gap_count": 0,
                    "workorder_count": 0,
                    "real_submitted_row_count": 17,
                    "missing_broker_order_key_count": 0,
                    "post_submit_provenance_join_gap": False,
                    "post_submit_provenance_join_resolution": (
                        "no_gap_broker_order_key_present_or_no_missing_rows"
                    ),
                },
                "post_submit_contract_gaps": [],
            }
        },
    )

    by_id = {item["order_id"]: item for item in orders}
    for order_id in {
        "order_entry_post_submit_contract_gap_review",
        "order_entry_broker_receipt_contract_gap_review",
        "order_entry_fill_quality_contract_gap_review",
        "order_entry_telegram_post_submit_contract_gap_review",
        "order_entry_source_taxonomy_contract_gap_review",
    }:
        order = by_id[order_id]
        assert order["implementation_status"] == "implemented_submit_contract_verified"
        assert order["implementation_provenance"]["implementation_type"] == (
            "submit_contract_report_provenance_verified"
        )
        assert order["implementation_provenance"]["submit_rows"] == 41
        assert order["implementation_provenance"]["missing_broker_order_key_count"] == 0
        assert order["implementation_provenance"]["runtime_effect"] is False
        assert order["implementation_provenance"]["allowed_runtime_apply"] is False


def test_buy_funnel_submit_drought_keeps_source_taxonomy_gap_open_when_leakage_remains():
    orders = mod._buy_funnel_sentinel_followup_orders(
        {
            "classification": {
                "primary": "SUBMIT_DROUGHT_CRITICAL",
                "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            },
            "entry_submit_drought_contract": {
                "required_downstream": [
                    "code_improvement_workorder",
                    "lifecycle_decision_matrix.submit_bucket_attribution",
                    "threshold_cycle_ev_report",
                    "runtime_approval_summary",
                    "postclose_verifier",
                ],
                "weak_contract_matches": ["SOURCE_TAXONOMY_LEAKAGE"],
                "stage_unique": {"order_bundle_submitted": 17},
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            },
            "current": {
                "session": {
                    "stage_unique": {
                        "ai_confirmed": 235,
                        "budget_pass": 3,
                        "order_bundle_submitted": 17,
                    },
                    "ratios": {
                        "submitted_to_ai_unique_pct": 7.23,
                        "submitted_to_budget_unique_pct": 9.9,
                    },
                    "blocker_top": [{"label": "blocked_swing_gap:-", "count": 12}],
                    "upstream_blocker_top": [],
                    "latency_blocker_top": [],
                }
            },
        },
        lifecycle_report={
            "submit_bucket_attribution": {
                "summary": {
                    "submit_rows": 41,
                    "contract_gap_count": 0,
                    "real_submitted_row_count": 17,
                    "missing_broker_order_key_count": 0,
                    "post_submit_provenance_join_gap": False,
                    "post_submit_provenance_join_resolution": (
                        "no_gap_broker_order_key_present_or_no_missing_rows"
                    ),
                },
                "post_submit_contract_gaps": [],
            }
        },
    )

    by_id = {item["order_id"]: item for item in orders}
    taxonomy_order = by_id["order_entry_source_taxonomy_contract_gap_review"]
    assert (
        taxonomy_order["implementation_status"] == "open_source_taxonomy_provenance_gap"
    )
    assert (
        "taxonomy_leakage_labels=['blocked_swing_gap:-']" in taxonomy_order["evidence"]
    )
    receipt_order = by_id["order_entry_broker_receipt_contract_gap_review"]
    assert (
        receipt_order["implementation_status"] == "implemented_submit_contract_verified"
    )


def test_lifecycle_submit_attribution_marks_no_gap_resolution_when_broker_key_present():
    report = ldm_mod._submit_bucket_attribution(
        [
            {
                "stage": "submit",
                "source_stage": "order_bundle_submitted",
                "event_time": "2026-06-12T09:05:00",
                "stock_code": "005930",
                "actual_order_submitted": True,
                "runtime_features": {
                    "actual_order_submitted": True,
                    "broker_order_no": "12345",
                    "broker_order_submitted": True,
                    "broker_receipt_status": "submitted_receipt_observed",
                    "broker_receipt_reason": "order_bundle_submitted",
                    "requested_qty": 1,
                    "filled_qty": 0,
                    "remaining_qty": 1,
                    "fill_quality": "pending",
                    "would_limit_fill": False,
                    "resolved_order_price": 10000,
                    "limit_price": 10000,
                    "post_submit_state": "submitted",
                    "cancel_requested": False,
                    "cancel_result": "none",
                    "position_rebased_after_fill": False,
                    "entry_submit_revalidation_warning": False,
                    "entry_submit_revalidation_block": False,
                    "quote_age_ms": 100,
                    "telegram_sent_after_broker_submit": True,
                    "telegram_event_type": "BUY_SUBMITTED",
                    "telegram_audience": "VIP_ALL",
                    "strategy_domain": "scalping",
                    "source_namespace": "entry_submit",
                    "blocker_namespace": "none",
                },
            }
        ]
    )

    summary = report["summary"]
    assert summary["contract_gap_count"] == 0
    assert summary["missing_broker_order_key_count"] == 0
    assert summary["post_submit_provenance_join_gap"] is False
    assert summary["post_submit_provenance_join_resolution"] == (
        "no_gap_broker_order_key_present_or_no_missing_rows"
    )


def test_build_code_improvement_workorder_consumes_ldm_submit_bucket_workorders(
    tmp_path, monkeypatch
):
    target_date = "2099-01-03"
    automation_dir = tmp_path / "automation"
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    ldm_dir.mkdir()
    (automation_dir / f"scalping_pattern_lab_automation_{target_date}.json").write_text(
        json.dumps({"date": target_date, "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (ldm_dir / f"lifecycle_decision_matrix_{target_date}.json").write_text(
        json.dumps(
            {
                "submit_bucket_attribution": {
                    "metric_role": "submit_funnel_source_quality_gate",
                    "decision_authority": "adm_ldm_submit_bucket_attribution_source_only",
                    "window_policy": "daily_lifecycle_submit_rows_plus_threshold_cycle_rolling_consumer",
                    "sample_floor": 3,
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_gate": "submit row sample + provenance",
                    "forbidden_uses": ["broker_order_submit"],
                    "code_improvement_workorders": [
                        {
                            "workorder_id": "order_entry_broker_receipt_contract_gap_review",
                            "bucket_type": "broker_receipt_contract_gap",
                            "bucket_key": "broker_receipt_or_real_submit_flag_missing",
                            "reason": "broker_receipt_or_real_submit_flag_missing",
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                        }
                    ],
                },
                "holding_bucket_attribution": {
                    "metric_role": "sim_probe_ev",
                    "decision_authority": "adm_ldm_holding_bucket_attribution_source_only",
                    "window_policy": "daily_lifecycle_holding_rows_plus_threshold_cycle_rolling_consumer",
                    "sample_floor": 3,
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_gate": "holding rows + joined labels",
                    "forbidden_uses": ["stage_only_live_promotion"],
                    "code_improvement_workorders": [
                        {
                            "workorder_id": "holding_bucket_source_quality_1",
                            "bucket_type": "combo_holding_flow",
                            "bucket_key": "source=sim|action=HOLD|profit=profit_unknown|held=held_unknown",
                            "reason": "holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation",
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                        }
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_DECISION_MATRIX_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(
        mod, "SWING_STRATEGY_DISCOVERY_EV_DIR", tmp_path / "missing-swing-discovery"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_DECISION_MATRIX_DIR", tmp_path / "missing-swing-ldm"
    )
    monkeypatch.setattr(
        mod, "SWING_LIFECYCLE_BUCKET_DISCOVERY_DIR", tmp_path / "missing-swing-bucket"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AI_REVIEW_DIR", tmp_path / "missing-ai-review"
    )
    monkeypatch.setattr(mod, "BUY_FUNNEL_SENTINEL_DIR", tmp_path / "missing-buy")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder(target_date, max_orders=1)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_entry_broker_receipt_contract_gap_review"
    )
    assert order["decision"] == "implement_now"
    assert (
        order["source_report_type"]
        == "lifecycle_decision_matrix_submit_bucket_attribution"
    )
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    expected_holding_order_id = mod._lifecycle_stage_bucket_order_id(
        "holding",
        {
            "bucket_type": "combo_holding_flow",
            "bucket_key": "source=sim|action=HOLD|profit=profit_unknown|held=held_unknown",
        },
    )
    holding_order = next(
        item
        for item in report["orders"]
        if item["order_id"] == expected_holding_order_id
    )
    assert (
        holding_order["source_report_type"]
        == "lifecycle_decision_matrix_holding_bucket_attribution"
    )
    assert holding_order["allowed_runtime_apply"] is False
    assert report["summary"]["lifecycle_submit_bucket_source_order_count"] == 1
    assert report["summary"]["lifecycle_holding_exit_bucket_source_order_count"] == 1


def test_lifecycle_child_bucket_not_applicable_evidence_is_existing_family():
    classified = mod._classify_order(
        {
            "order_id": "order_lifecycle_exit_bucket_outcome_unknown",
            "title": "LDM exit bucket source-quality follow-up",
            "source_report_type": "lifecycle_decision_matrix_exit_bucket_attribution",
            "target_subsystem": "lifecycle_decision_matrix",
            "route": "instrumentation_order",
            "threshold_family": "lifecycle_decision_matrix_runtime",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "implementation_status": "open",
            "implementation_provenance": {
                "source_field_coverage": {
                    "outcome": {
                        "present_count": 9,
                        "sample_count": 9,
                        "coverage_rate": 1.0,
                    }
                },
                "recommended_resolution": "mark_not_applicable_explicitly",
            },
        },
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert classified.decision == "attach_existing_family"
    assert classified.route == "existing_family"
    assert "not_applicable" in classified.reason


def test_build_code_improvement_workorder_adds_entry_adm_gap_order(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    adm_dir = tmp_path / "adm"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for directory in (automation_dir, ev_dir, adm_dir):
        directory.mkdir()
    adm_path = adm_dir / "scalp_entry_action_decision_matrix_2026-05-18.json"
    adm_path.write_text(json.dumps({"status": "warning"}), encoding="utf-8")
    (automation_dir / "scalping_pattern_lab_automation_2026-05-18.json").write_text(
        json.dumps({"date": "2026-05-18", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-18.json").write_text(
        json.dumps(
            {
                "sources": {"scalp_entry_action_decision_matrix": str(adm_path)},
                "scalp_entry_action_decision_matrix": {
                    "available": True,
                    "status": "warning",
                    "joined_sample": 2,
                    "sample_floor": 20,
                    "prompt_applied_count": 0,
                    "missing_actions": ["WAIT_REQUOTE"],
                    "artifact": str(adm_path),
                    "outcome_join_diagnostic": {
                        "status": "no_candidate_key_overlap",
                        "zero_join_reason": "entry_adm_candidate_keys_do_not_overlap_post_sell_evaluation_keys",
                        "candidate_post_sell_key_overlap_count": 0,
                        "post_sell_evaluation_rows": 1,
                        "post_sell_evaluation_join_keys": 1,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod,
        "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR",
        tmp_path / "missing-observation-audit",
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-18", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_scalp_entry_adm_daily_tuning_coverage"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert "joined_sample=2" in order["evidence"]
    assert "outcome_join_status=no_candidate_key_overlap" in order["evidence"]
    assert (
        "zero_join_reason=entry_adm_candidate_keys_do_not_overlap_post_sell_evaluation_keys"
        in order["evidence"]
    )
    assert report["source"]["scalp_entry_action_decision_matrix"] == str(adm_path)


def test_entry_adm_sample_wait_only_is_rejudged_non_implement():
    classified = mod._classify_order(
        {
            "order_id": "order_scalp_entry_adm_daily_tuning_coverage",
            "title": "scalp entry ADM daily tuning coverage",
            "source_report_type": "threshold_cycle_ev",
            "target_subsystem": "entry_funnel",
            "route": "instrumentation_order",
            "threshold_family": "scalp_entry_action_decision_matrix_advisory",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "adm_issue_types": [
                "joined_sample_below_sample_floor",
                "prompt_context_not_loaded",
            ],
            "files_likely_touched": [
                "src/engine/scalp_entry_action_decision_matrix.py",
                "src/engine/threshold_cycle_ev_report.py",
            ],
            "acceptance_tests": [
                "PYTHONPATH=. .venv/bin/pytest src/tests/test_scalp_entry_action_decision_matrix.py"
            ],
        },
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )

    assert classified.decision == "defer_evidence"
    assert "waiting on clean sample/runtime observation" in classified.reason


def test_build_code_improvement_workorder_adds_pipeline_event_verbosity_order(
    tmp_path, monkeypatch
):
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "PIPELINE_EVENT_VERBOSITY_DIR", verbosity_dir)
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-14", max_orders=3)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_pipeline_event_compaction_v2_shadow"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert report["summary"]["pipeline_event_verbosity_source_order_count"] == 1
    assert report["source"]["pipeline_event_verbosity"] == str(
        verbosity_dir / "pipeline_event_verbosity_2026-05-14.json"
    )


def test_build_code_improvement_workorder_adds_observation_source_quality_orders(
    tmp_path, monkeypatch
):
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", audit_dir)
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=5)

    order_ids = {item["order_id"]: item for item in report["orders"]}
    assert (
        order_ids["order_ai_source_quality_not_evaluated_provenance"]["decision"]
        == "implement_now"
    )
    assert (
        order_ids["order_high_volume_diagnostic_stage_contract_labels"][
            "runtime_effect"
        ]
        is False
    )
    swing_order = order_ids["order_swing_source_quality_micro_context_provenance"]
    assert swing_order["runtime_effect"] is False
    assert swing_order["decision"] == "implement_now"
    assert any(
        "swing_warning_stages=swing_probe_state_persisted,scale_in_price_p2_observe"
        in item
        for item in swing_order["evidence"]
    )
    assert report["summary"]["observation_source_quality_source_order_count"] == 3
    assert report["source"]["observation_source_quality_audit"] == str(
        audit_dir / "observation_source_quality_audit_2026-05-15.json"
    )


def test_build_code_improvement_workorder_adds_source_quality_hard_block_order(
    tmp_path, monkeypatch
):
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
                    "event_count": 10,
                    "warning_stage_count": 1,
                    "tuning_input_allowed": False,
                    "blocked_reason": "blocked_contract_gap",
                    "hard_blocking_contract_gap_count": 1,
                    "hard_blocking_stages": ["blocked_ai_score"],
                },
                "stage_contracts": {
                    "blocked_ai_score": {
                        "status": "warning",
                        "sample_count": 10,
                        "missing_violations": {"tick_accel_source": 1.0},
                    }
                },
                "hard_blocking_contract_gaps": [
                    {
                        "stage": "blocked_ai_score",
                        "reason": "stage_contract_status_warning_or_fail",
                        "missing_fields": ["tick_accel_source"],
                        "sample_count": 10,
                        "first_timestamp": "2026-05-15T09:00:00+09:00",
                        "last_timestamp": "2026-05-15T09:10:00+09:00",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", audit_dir)
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"]
        == "order_observation_source_quality_hard_block_contract_gap"
    )
    assert order["decision"] == "implement_now"
    assert order["route"] == "source_quality_gap"
    assert order["improvement_type"] == "source_quality_hard_block_contract_gap"
    assert order["runtime_effect"] is False
    assert any(
        "first_timestamp=2026-05-15T09:00:00+09:00" in item
        for item in order["evidence"]
    )


def test_build_code_improvement_workorder_keeps_raw_row_exclusion_order_beyond_max_orders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    audit_dir = tmp_path / "observation-audit"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    audit_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-15.json").write_text(
        json.dumps({"date": "2026-05-15", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (audit_dir / "observation_source_quality_audit_2026-05-15.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "summary": {"event_count": 2, "tuning_input_allowed": True},
                "raw_row_exclusion": {
                    "excluded_row_count": 1,
                    "stage_counts": {"custom_stage": 1},
                    "exclusion_reasons": {"required_field_missing": 1},
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", audit_dir)
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=0)

    selected_ids = {order["order_id"] for order in report["orders"]}
    assert (
        "order_observation_source_quality_raw_row_exclusion_producer_gap"
        in selected_ids
    )
    assert report["summary"][
        "selected_implement_now_new_runtime_effect_false_order_ids"
    ] == ["order_observation_source_quality_raw_row_exclusion_producer_gap"]


def test_build_code_improvement_workorder_treats_implemented_report_order_as_existing_family(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    swing_lab_dir = tmp_path / "swing-lab"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    swing_lab_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-15.json").write_text(
        json.dumps({"date": "2026-05-15", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (swing_lab_dir / "swing_pattern_lab_automation_2026-05-15.json").write_text(
        json.dumps(
            {
                "date": "2026-05-15",
                "swing_ai_structured_output_eval": {
                    "report_contract": "swing_ai_structured_output_eval_report_v1",
                    "source_contract": "swing_ai_structured_output_eval_v1",
                    "decision_authority": "swing_ai_contract_eval_report_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "sample_status": "waiting_replay_sample",
                    "schema_valid_rate": None,
                    "decision_disagreement_rate_pct": None,
                    "p50_latency_ms": None,
                    "estimated_total_cost_krw": None,
                },
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_pattern_lab_deepseek_ofi_qi_stale_missing",
                        "title": "OFI/QI stale/missing quality review",
                        "source_report_type": "swing_pattern_lab_automation",
                        "route": "implement_now",
                        "mapped_family": "swing_entry_ofi_qi_execution_quality",
                        "implementation_status": "implemented",
                        "implementation_checks": [
                            {"name": "contract", "status": "pass"}
                        ],
                        "implementation_provenance": {
                            "owner": "swing_pattern_lab_automation",
                            "decision_authority": "source_quality_only",
                            "runtime_effect": False,
                        },
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", swing_lab_dir)
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", tmp_path / "missing-audit"
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_swing_pattern_lab_deepseek_ofi_qi_stale_missing"
    )
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "existing_family"
    assert order["implementation_candidate"] is False
    assert order["implementation_status"] == "implemented"
    assert order["implementation_checks"] == [{"name": "contract", "status": "pass"}]
    assert (
        order["implementation_provenance"]["decision_authority"]
        == "source_quality_only"
    )


def test_build_code_improvement_workorder_attaches_swing_improvement_implemented_ofi_qi_order(
    tmp_path, monkeypatch
):
    swing_dir = tmp_path / "swing"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    swing_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    (swing_dir / "swing_improvement_automation_2026-05-15.json").write_text(
        json.dumps(
            {
                "date": "2026-05-15",
                "swing_ai_structured_output_eval": {
                    "report_contract": "swing_ai_structured_output_eval_report_v1",
                    "source_contract": "swing_ai_structured_output_eval_v1",
                    "decision_authority": "swing_ai_contract_eval_report_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "sample_status": "waiting_replay_sample",
                    "schema_valid_rate": None,
                    "decision_disagreement_rate_pct": None,
                    "p50_latency_ms": None,
                    "estimated_total_cost_krw": None,
                },
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_ofi_qi_stale_or_missing_context",
                        "title": "swing OFI/QI stale or missing context",
                        "source_report_type": "swing_improvement_automation",
                        "route": "existing_family",
                        "mapped_family": "swing_entry_ofi_qi_execution_quality",
                        "implementation_status": "implemented",
                        "implementation_provenance": {
                            "owner": "swing_improvement_automation",
                            "source_contract": "swing_orderbook_micro_context_v2",
                            "group": "entry",
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                        },
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-pattern")
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", swing_dir)
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", tmp_path / "missing-audit"
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_swing_ofi_qi_stale_or_missing_context"
    )
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "existing_family"
    assert order["implementation_candidate"] is False
    assert order["implementation_status"] == "implemented"
    assert (
        order["implementation_provenance"]["source_contract"]
        == "swing_orderbook_micro_context_v2"
    )
    assert order["root_cause_closure_status"] == "root_cause_closed"


def test_build_code_improvement_workorder_attaches_swing_ai_structured_output_eval_contract(
    tmp_path, monkeypatch
):
    swing_dir = tmp_path / "swing"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    swing_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    (swing_dir / "swing_improvement_automation_2026-05-15.json").write_text(
        json.dumps(
            {
                "date": "2026-05-15",
                "swing_ai_structured_output_eval": {
                    "report_contract": "swing_ai_structured_output_eval_report_v1",
                    "source_contract": "swing_ai_structured_output_eval_v1",
                    "decision_authority": "swing_ai_contract_eval_report_only",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "sample_status": "waiting_replay_sample",
                    "schema_valid_rate": None,
                    "decision_disagreement_rate_pct": None,
                    "p50_latency_ms": None,
                    "estimated_total_cost_krw": None,
                },
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_ai_contract_structured_output_eval",
                        "title": "swing AI contract structured output eval",
                        "target_subsystem": "swing_ai_contract",
                        "source_report_type": "swing_improvement_automation",
                        "lifecycle_stage": "ai_contract",
                        "improvement_type": "ai_contract_eval",
                        "priority": 5,
                        "route": "auto_family_candidate",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "intent": (
                            "Replay Korean prompt vs English-control prompt vs strict schema prompt before "
                            "adopting a swing AI contract."
                        ),
                        "evidence": [
                            "swing_gatekeeper_free_text_label",
                            "swing_holding_flow_scalping_prompt_reuse",
                            "swing_scale_in_ai_contract_missing",
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-pattern")
    monkeypatch.setattr(mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", swing_dir)
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", tmp_path / "missing-audit"
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-15", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_swing_ai_contract_structured_output_eval"
    )
    assert order["decision"] == "attach_existing_family"
    assert order["route"] == "existing_family"
    assert order["mapped_family"] == "swing_ai_contract_structured_output_eval"
    assert order["implementation_candidate"] is False
    assert (
        order["implementation_status"]
        == "implemented_source_quality_contract_waiting_sample"
    )
    assert order["root_cause_closure_status"] == "implementation_done"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert order["actual_order_submitted"] is False
    assert order["broker_order_forbidden"] is True
    assert (
        order["implementation_provenance"]["decision_authority"]
        == "swing_ai_contract_eval_report_only"
    )
    assert (
        order["implementation_provenance"]["source_contract"]
        == "swing_ai_structured_output_eval_v1"
    )
    assert (
        order["implementation_provenance"]["sample_status"] == "waiting_replay_sample"
    )


def test_build_code_improvement_workorder_attaches_lifecycle_ai_context_instrumentation(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    ev_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-20.json").write_text(
        json.dumps({"date": "2026-05-20", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-20.json").write_text(
        json.dumps(
            {
                "sources": {
                    "lifecycle_ai_context": "data/report/lifecycle_ai_context/lifecycle_ai_context_2026-05-20.json",
                    "lifecycle_ai_context_attribution": "data/report/lifecycle_ai_context_attribution/lifecycle_ai_context_attribution_2026-05-20.json",
                },
                "lifecycle_ai_context": {"available": True, "prompt_stage_count": 3},
                "lifecycle_ai_context_attribution": {
                    "available": True,
                    "context_applied_count": 0,
                    "replay_budget": 30,
                    "implementation_status": "implemented",
                    "implementation_checks": [{"name": "contract", "status": "pass"}],
                    "implementation_provenance": {
                        "runtime_effect": False,
                        "decision_authority": "postclose_context_attribution_only",
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", tmp_path / "missing-audit"
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-20", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_lifecycle_ai_context_attribution_feedback"
    )
    assert order["decision"] == "attach_existing_family"
    assert order["implementation_status"] == "implemented"
    assert order["runtime_effect"] is False


def test_build_code_improvement_workorder_attaches_swing_discovery_source_quality_instrumentation(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    swing_ev_dir = tmp_path / "swing-ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    automation_dir.mkdir()
    swing_ev_dir.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-20.json").write_text(
        json.dumps({"date": "2026-05-20", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    (swing_ev_dir / "swing_strategy_discovery_ev_2026-05-20.json").write_text(
        json.dumps(
            {
                "summary": {
                    "labeled_sample_count": 0,
                    "pending_future_quote_count": 10,
                    "avoid_bucket_count": 0,
                },
                "source_quality_summary": {
                    "implementation_status": "implemented",
                    "implementation_checks": [
                        {"name": "label_maturity_provenance", "status": "pass"}
                    ],
                    "implementation_provenance": {
                        "runtime_effect": False,
                        "decision_authority": "swing_sim_exploration_only",
                    },
                    "maturity_status_counts": {"pending_future_quotes": 10},
                },
                "warnings": ["pending_future_quotes", "sample_floor_not_met"],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "SWING_STRATEGY_DISCOVERY_EV_DIR", swing_ev_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", tmp_path / "missing-audit"
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-20", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_swing_strategy_discovery_source_quality_followup"
    )
    assert order["decision"] == "attach_existing_family"
    assert order["implementation_status"] == "implemented"
    assert order["implementation_provenance"]["runtime_effect"] is False


def test_build_code_improvement_workorder_adds_window_policy_audit_order(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    calibration_dir = tmp_path / "calibration"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for directory in (automation_dir, ev_dir, calibration_dir):
        directory.mkdir()
    calibration_path = (
        calibration_dir / "threshold_cycle_calibration_2026-05-14_postclose.json"
    )
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
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


def test_build_code_improvement_workorder_adds_codebase_performance_orders(
    tmp_path, monkeypatch
):
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
                        "acceptance_tests": [
                            "pytest src/tests/test_buy_funnel_sentinel.py"
                        ],
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", perf_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-14", max_orders=10)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert decisions["order_perf_buy_funnel_json_scan"] == "implement_now"
    assert decisions["order_perf_kiwoom_orders_http_session_review"] == "defer_evidence"
    assert decisions["order_perf_raw_event_suppression_out_of_scope"] == "reject"
    accepted = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_perf_buy_funnel_json_scan"
    )
    assert accepted["runtime_effect"] is False
    assert accepted["strategy_effect"] is False
    assert accepted["data_quality_effect"] is False
    assert accepted["tuning_axis_effect"] is False
    assert accepted["parity_contract"] == "classification parity"
    assert report["summary"]["codebase_performance_source_order_count"] == 3
    assert report["source"]["codebase_performance_workorder"] == str(perf_path)


def test_build_code_improvement_workorder_attaches_implemented_codebase_performance_order(
    tmp_path, monkeypatch
):
    perf_dir = tmp_path / "perf"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    ev_dir = tmp_path / "ev"
    perf_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    doc_dir.mkdir(parents=True)
    ev_dir.mkdir(parents=True)
    (ev_dir / "threshold_cycle_ev_2026-05-14.json").write_text("{}", encoding="utf-8")
    perf_path = perf_dir / "codebase_performance_workorder_2026-05-14.json"
    perf_path.write_text(
        json.dumps(
            {
                "source_doc_hash": "abc123",
                "accepted_candidates": [
                    {
                        "item_id": "order_perf_monitor_snapshot_stream_tail",
                        "title": "Monitor snapshot runtime streaming tail read",
                        "risk_tier": "low",
                        "target_subsystem": "monitor_snapshot",
                        "priority": 1,
                        "runtime_effect": False,
                        "implementation_status": "implemented",
                        "implementation_checks": [
                            {"path": "src/engine/monitor_snapshot_runtime.py"}
                        ],
                        "files_likely_touched": [
                            "src/engine/monitor_snapshot_runtime.py"
                        ],
                        "acceptance_tests": [
                            "pytest src/tests/test_log_archive_service.py"
                        ],
                        "parity_contract": "last valid JSON line parity",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-automation"
    )
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", perf_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-14", max_orders=10)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_perf_monitor_snapshot_stream_tail"
    )
    assert order["decision"] == "attach_existing_family"
    assert order["mapped_family"] == "ops_performance_report_only_implemented"
    assert order["implementation_status"] == "implemented"


def test_build_code_improvement_workorder_adds_panic_lifecycle_orders(
    tmp_path, monkeypatch
):
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
                            "candidate_status": {
                                "panic_stop_confirmation": "report_only_candidate"
                            },
                        },
                        "panic_buying": {
                            "panic_buy_state": "PANIC_BUY",
                            "panic_buy_regime_mode": "PANIC_BUY_CONTINUATION",
                            "risk_regime_gate_state": "confirmed_panic_buy",
                            "risk_regime_threshold_mode": "dynamic_quantile",
                            "confirmed_evidence_count": 4,
                            "runtime_effect": "report_only_no_mutation",
                            "panic_buy_active_count": 1,
                            "tp_counterfactual_count": 4,
                            "trailing_winner_count": 2,
                            "market_wide_panic_buy_confirmed": True,
                            "market_breadth_risk_on_advisory": True,
                            "candidate_status": {
                                "panic_buy_runner_tp_canary": "report_only_candidate"
                            },
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-13", max_orders=5)

    decisions = {item["order_id"]: item["decision"] for item in report["orders"]}
    assert (
        decisions["order_panic_sell_defense_lifecycle_transition_pack"]
        == "attach_existing_family"
    )
    assert (
        decisions["order_panic_buy_runner_tp_canary_lifecycle_pack"]
        == "attach_existing_family"
    )
    assert report["summary"]["panic_lifecycle_source_order_count"] == 2
    assert report["source"]["threshold_cycle_calibration"] == str(calibration_path)
    panic_order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_panic_sell_defense_lifecycle_transition_pack"
    )
    assert any(
        "market_breadth_followup_candidate=True" in item
        for item in panic_order["evidence"]
    )
    assert any(
        "source_quality_blockers=['market_regime_not_risk_off']" in item
        for item in panic_order["evidence"]
    )
    assert (
        panic_order["implementation_status"]
        == "implemented_source_quality_contract_waiting_sample"
    )
    panic_buy_order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_panic_buy_runner_tp_canary_lifecycle_pack"
    )
    assert any(
        "panic_buy_regime_mode=PANIC_BUY_CONTINUATION" in item
        for item in panic_buy_order["evidence"]
    )
    assert any(
        "risk_regime_gate_state=confirmed_panic_buy" in item
        for item in panic_buy_order["evidence"]
    )
    assert any(
        "market_wide_panic_buy_confirmed=True" in item
        for item in panic_buy_order["evidence"]
    )
    assert panic_buy_order["implementation_status"] == "implemented_but_waiting_sample"
    markdown = (doc_dir / "code_improvement_workorder_2026-05-13.md").read_text(
        encoding="utf-8"
    )
    assert "panic_buy_runner_tp_canary" in markdown
    assert "threshold_cycle_calibration" in markdown


def test_build_code_improvement_workorder_routes_panic_buy_source_quality_only(
    tmp_path, monkeypatch
):
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
                            "risk_regime_gate_state": "source_quality_blocked",
                            "risk_regime_threshold_mode": "insufficient_sample",
                            "confirmed_evidence_count": 0,
                            "panic_buy_active_count": 0,
                            "tp_counterfactual_count": 0,
                            "trailing_winner_count": 0,
                            "market_wide_panic_buy_confirmed": False,
                            "market_breadth_risk_on_advisory": False,
                            "missing_orderbook_count": 15,
                            "missing_trade_aggressor_count": 13,
                            "source_quality_blockers": [
                                "panic_buy_orderbook_collector_coverage_gap"
                            ],
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-13", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"]
        == "order_panic_buying_source_quality_market_breadth_micro_coverage"
    )
    assert order["route"] == "existing_family"
    assert order["runtime_effect"] is False
    assert order["threshold_family"] is None
    assert (
        order["implementation_status"]
        == "implemented_source_quality_contract_waiting_sample"
    )
    assert any(
        "risk_regime_gate_state=source_quality_blocked" in item
        for item in order["evidence"]
    )
    assert any(
        "source_quality_blockers=['panic_buy_orderbook_collector_coverage_gap']" in item
        for item in order["evidence"]
    )


def test_build_code_improvement_workorder_merges_swing_automation(
    tmp_path, monkeypatch
):
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
    assert (
        decisions["order_swing_gatekeeper_reject_threshold_review"]
        == "attach_existing_family"
    )
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(
        encoding="utf-8"
    )
    assert "swing_improvement_automation" in markdown
    assert "lifecycle_stage" in markdown


def test_build_code_improvement_workorder_forces_swing_entry_bottleneck_selected(
    tmp_path, monkeypatch
):
    scalping_dir = tmp_path / "scalping"
    swing_dir = tmp_path / "swing"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    scalping_dir.mkdir()
    swing_dir.mkdir()
    (scalping_dir / "scalping_pattern_lab_automation_2026-05-22.json").write_text(
        json.dumps(
            {
                "date": "2026-05-22",
                "consensus_findings": [],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_alpha_pipeline_event_compaction",
                        "title": "alpha pipeline event compaction",
                        "lifecycle_stage": "ops",
                        "target_subsystem": "runtime_instrumentation",
                        "priority": 0,
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_improvement_automation_2026-05-22.json").write_text(
        json.dumps(
            {
                "date": "2026-05-22",
                "swing_entry_bottleneck": {
                    "primary": "SWING_ENTRY_DROUGHT_CRITICAL",
                    "matches": ["GATEKEEPER_PULLBACK_WAIT", "SUBMIT_ZERO"],
                },
                "consensus_findings": [
                    {
                        "finding_id": "swing_entry_bottleneck_auto_resolution",
                        "title": "swing entry bottleneck automatic resolution handoff",
                        "confidence": "consensus",
                        "route": "instrumentation_order",
                        "mapped_family": "swing_gatekeeper_accept_reject",
                        "target_subsystem": "swing_entry",
                    }
                ],
                "solo_findings": [],
                "auto_family_candidates": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_entry_bottleneck_auto_resolution",
                        "title": "swing entry bottleneck automatic resolution handoff",
                        "lifecycle_stage": "entry",
                        "target_subsystem": "swing_entry",
                        "route": "instrumentation_order",
                        "mapped_family": "swing_gatekeeper_accept_reject",
                        "threshold_family": "swing_gatekeeper_accept_reject",
                        "priority": 0,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
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

    report = mod.build_code_improvement_workorder("2026-05-22", max_orders=1)

    selected_ids = {item["order_id"] for item in report["orders"]}
    assert "order_swing_entry_bottleneck_auto_resolution" in selected_ids
    order = next(
        item
        for item in report["orders"]
        if item["order_id"] == "order_swing_entry_bottleneck_auto_resolution"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert (
        report["summary"]["swing_entry_bottleneck_primary"]
        == "SWING_ENTRY_DROUGHT_CRITICAL"
    )
    assert report["summary"]["swing_entry_bottleneck_selected"] is True


def test_followup_order_ids_keep_hash_for_long_source_keys():
    prefix = "same_long_source_prefix_" + ("x" * 120)
    ldm_ids = {
        mod._swing_ldm_order_id(
            {
                "lifecycle_stage": "selection",
                "bucket_type": "discovery_arm_attribution",
                "bucket_key": f"{prefix}_{suffix}",
            }
        )
        for suffix in ("first", "second")
    }
    bucket_orders = mod._swing_lifecycle_bucket_discovery_followup_orders(
        {
            "code_improvement_workorders": [
                {"bucket_id": f"{prefix}_{suffix}", "lifecycle_stage": "selection"}
                for suffix in ("first", "second")
            ]
        }
    )
    conversion_orders = mod._conversion_lane_followup_orders(
        {
            "conversion_blocker_rank": [
                {
                    "blocker_class": "source_quality",
                    "conversion_candidate_id": f"{prefix}_{suffix}",
                    "conversion_impact_rank": index,
                }
                for index, suffix in enumerate(("first", "second"), start=1)
            ]
        }
    )

    assert len(ldm_ids) == 2
    assert len({item["order_id"] for item in bucket_orders}) == 2
    assert len({item["order_id"] for item in conversion_orders}) == 2


def test_build_code_improvement_workorder_dedupes_duplicate_orders(
    tmp_path, monkeypatch
):
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
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(
        encoding="utf-8"
    )
    assert "Duplicate Order Collisions" in markdown


def test_build_code_improvement_workorder_adds_threshold_ev_hold_no_edge_followup(
    tmp_path, monkeypatch
):
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
                                "counterfactual_proxy_missing_actions": [
                                    "hold_defer",
                                    "avg_down_wait",
                                ],
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", scalping_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
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
    markdown = (doc_dir / "code_improvement_workorder_2026-05-11.md").read_text(
        encoding="utf-8"
    )
    assert "hold_no_edge" in markdown
    assert "counterfactual" in markdown


def test_build_code_improvement_workorder_skips_adm_followup_when_instrumentation_gap_closed(
    tmp_path, monkeypatch
):
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-11", max_orders=5)

    assert report["summary"]["threshold_ev_source_order_count"] == 0
    assert all(
        item["order_id"] != "order_holding_exit_decision_matrix_edge_counterfactual"
        for item in report["orders"]
    )


def test_build_code_improvement_workorder_skips_adm_followup_when_matrix_contract_closed(
    tmp_path,
    monkeypatch,
):
    scalping_dir = tmp_path / "scalping"
    ev_dir = tmp_path / "ev"
    matrix_dir = tmp_path / "holding-exit-matrix"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    scalping_dir.mkdir()
    ev_dir.mkdir()
    matrix_dir.mkdir()
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
                                "counterfactual_proxy_missing_actions": [
                                    "hold_defer",
                                    "avg_down_wait",
                                ],
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    (matrix_dir / "holding_exit_decision_matrix_2026-05-11.json").write_text(
        json.dumps(
            {
                "instrumentation_status": "implemented",
                "runtime_change": False,
                "summary": {
                    "non_no_clear_edge_count": 3,
                    "per_action_edge_buckets": {"hold_defer": {}, "exit_only": {}},
                },
                "counterfactual_proxy_summary": {
                    "ready": True,
                    "actions_present": [
                        "hold_defer",
                        "exit_only",
                        "avg_down_wait",
                        "pyramid_wait",
                    ],
                    "per_action_samples": {
                        "hold_defer": 10,
                        "exit_only": 8,
                        "avg_down_wait": 7,
                        "pyramid_wait": 6,
                    },
                    "per_action_joined": {
                        "hold_defer": 0,
                        "exit_only": 0,
                        "avg_down_wait": 0,
                        "pyramid_wait": 0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", scalping_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "HOLDING_EXIT_DECISION_MATRIX_DIR", matrix_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-11", max_orders=5)

    assert report["summary"]["threshold_ev_source_order_count"] == 0
    assert all(
        item["order_id"] != "order_holding_exit_decision_matrix_edge_counterfactual"
        for item in report["orders"]
    )


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
                            "family": "dynamic_entry_price_resolver",
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-11", max_orders=5)

    order = report["orders"][0]
    assert order["order_id"] == "order_latency_guard_miss_ev_recovery"
    assert order["decision"] == "attach_existing_family"
    assert order["mapped_family"] == "dynamic_entry_price_resolver"


def test_build_code_improvement_workorder_does_not_route_dynamic_entry_normal_telemetry(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    ev_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    (ev_dir / "threshold_cycle_ev_2026-05-12.json").write_text(
        json.dumps(
            {
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "dynamic_entry_price_resolver",
                            "source_metrics": {
                                "report_contract_gap": "false",
                                "candidate_quality_contract_gap": "0",
                                "sim_submit_path_contract_gap": "no",
                                "candidate_quality": {
                                    "AI_candidate": {
                                        "candidate_failure_count": 3,
                                        "candidate_failure_rate": 75.0,
                                        "failure_reasons": {
                                            "missing_snapshot": 2,
                                            "invalid_price": 1,
                                        },
                                    }
                                },
                                "unpriced_or_stale_warning_count": 4,
                                "sim_submit_path_quality": {
                                    "scalp_sim_buy_order_virtual_pending": {
                                        "sample_count": 5,
                                        "unpriced_sample_count": 4,
                                        "excluded_from_fill_ev_count": 4,
                                    }
                                },
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-pattern")
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-12", max_orders=10)

    orders = {item["order_id"]: item for item in report["orders"]}
    assert "order_dynamic_entry_price_ai_candidate_failure_contract" not in orders
    assert "order_dynamic_entry_price_sim_unpriced_stale_contract" not in orders


def test_build_code_improvement_workorder_routes_dynamic_entry_report_contract_gaps(
    tmp_path, monkeypatch
):
    ev_dir = tmp_path / "ev"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    ev_dir.mkdir()
    report_dir.mkdir()
    doc_dir.mkdir()
    (ev_dir / "threshold_cycle_ev_2026-05-12.json").write_text(
        json.dumps(
            {
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "dynamic_entry_price_resolver",
                            "source_metrics": {
                                "report_contract_gap": True,
                                "candidate_quality": {
                                    "AI_candidate": {
                                        "candidate_failure_count": 3,
                                        "candidate_failure_rate": 75.0,
                                        "failure_reasons": {
                                            "missing_snapshot": 2,
                                            "invalid_price": 1,
                                        },
                                    }
                                },
                                "unpriced_or_stale_warning_count": 4,
                                "sim_submit_path_quality": {
                                    "scalp_sim_buy_order_virtual_pending": {
                                        "sample_count": 5,
                                        "unpriced_sample_count": 4,
                                        "excluded_from_fill_ev_count": 4,
                                    }
                                },
                            },
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-pattern")
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-12", max_orders=10)

    orders = {item["order_id"]: item for item in report["orders"]}
    ai_order = orders["order_dynamic_entry_price_ai_candidate_failure_contract"]
    assert ai_order["mapped_family"] == "dynamic_entry_price_resolver"
    assert ai_order["runtime_effect"] is False
    assert any("candidate_failure_count=3" in item for item in ai_order["evidence"])
    unpriced_order = orders["order_dynamic_entry_price_sim_unpriced_stale_contract"]
    assert unpriced_order["lifecycle_stage"] == "submit"
    assert unpriced_order["allowed_runtime_apply"] is False
    assert any(
        "unpriced_or_stale_warning_count=4" in item
        for item in unpriced_order["evidence"]
    )


def test_build_code_improvement_workorder_reports_previous_generation_diff(
    tmp_path, monkeypatch
):
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
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", tmp_path / "missing-ev")
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-08", max_orders=5)

    assert report["lineage"]["previous_exists"] is True
    assert report["lineage"]["previous_generation_id"] == "2026-05-08-oldhash"
    assert report["lineage"]["new_order_ids"] == ["order_new"]
    assert report["lineage"]["removed_order_ids"] == ["order_old"]
    assert report["lineage"]["decision_changed_order_ids"] == ["order_keep"]
    markdown = (doc_dir / "code_improvement_workorder_2026-05-08.md").read_text(
        encoding="utf-8"
    )
    assert "order_new" in markdown
    assert "order_old" in markdown


def test_build_code_improvement_workorder_consumes_lifecycle_entry_bucket_workorders(
    tmp_path, monkeypatch
):
    automation_dir = tmp_path / "automation"
    ev_dir = tmp_path / "ev"
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    doc_dir = tmp_path / "docs"
    for directory in (automation_dir, ev_dir, ldm_dir):
        directory.mkdir()
    (automation_dir / "scalping_pattern_lab_automation_2026-05-21.json").write_text(
        json.dumps({"date": "2026-05-21", "code_improvement_orders": []}),
        encoding="utf-8",
    )
    ldm_path = ldm_dir / "lifecycle_decision_matrix_2026-05-21.json"
    ldm_path.write_text(
        json.dumps(
            {
                "entry_bucket_attribution": {
                    "metric_role": "sim_probe_ev",
                    "decision_authority": "adm_ldm_entry_bucket_attribution_source_only",
                    "window_policy": "daily_lifecycle_rows_plus_threshold_cycle_rolling_consumer",
                    "sample_floor": 10,
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_gate": "joined outcome labels",
                    "forbidden_uses": ["broker_order_submit"],
                    "code_improvement_workorders": [
                        {
                            "workorder_id": "entry_bucket_source_quality_1",
                            "bucket_type": "liquidity_bucket",
                            "bucket_key": "liquidity_unknown",
                            "reason": "bucket_has_edge_but_needs_rolling_or_feature_confirmation",
                            "recommended_route": "candidate_recovery_or_relax",
                            "metric_role": "source_quality_gate",
                            "runtime_effect": False,
                        }
                    ],
                },
                "scale_in_bucket_attribution": {
                    "metric_role": "sim_probe_ev",
                    "decision_authority": "adm_ldm_scale_in_bucket_attribution_source_only",
                    "window_policy": "daily_lifecycle_rows_plus_threshold_cycle_rolling_consumer",
                    "sample_floor": 5,
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_gate": "scale_in arm + blocker namespace + joined source labels",
                    "forbidden_uses": ["real_scale_in_submit"],
                    "code_improvement_workorders": [
                        {
                            "workorder_id": "scale_in_bucket_source_quality_1",
                            "bucket_type": "blocker_namespace",
                            "bucket_key": "PRICE_GUARD",
                            "reason": "scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation",
                            "recommended_route": "candidate_recovery_or_relax",
                            "metric_role": "source_quality_gate",
                            "runtime_effect": False,
                        }
                    ],
                },
                "overnight_bucket_attribution": {
                    "metric_role": "sim_probe_ev",
                    "decision_authority": "adm_ldm_overnight_bucket_attribution_source_only",
                    "runtime_effect": False,
                    "implementation_status": "implemented",
                    "window_policy": "daily_overnight_rows_plus_next_day_carry_label_join_consumer",
                    "sample_floor": 5,
                    "primary_decision_metric": "source_quality_adjusted_ev_pct",
                    "source_quality_gate": "overnight decision coverage + joined same/next-day source labels",
                    "forbidden_uses": ["hard_overnight_gate"],
                    "code_improvement_workorders": [
                        {
                            "workorder_id": "overnight_bucket_source_quality_1",
                            "bucket_type": "overnight_action",
                            "bucket_key": "SELL_TODAY",
                            "reason": "overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation",
                            "recommended_route": "candidate_recovery_or_relax",
                            "metric_role": "source_quality_gate",
                            "runtime_effect": False,
                        }
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-21.json").write_text(
        json.dumps({"sources": {"lifecycle_decision_matrix": str(ldm_path)}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "PATTERN_LAB_AUTOMATION_DIR", automation_dir)
    monkeypatch.setattr(
        mod, "SWING_IMPROVEMENT_AUTOMATION_DIR", tmp_path / "missing-swing"
    )
    monkeypatch.setattr(
        mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", tmp_path / "missing-swing-lab"
    )
    monkeypatch.setattr(mod, "THRESHOLD_CYCLE_EV_DIR", ev_dir)
    monkeypatch.setattr(mod, "LIFECYCLE_DECISION_MATRIX_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "PIPELINE_EVENT_VERBOSITY_DIR", tmp_path / "missing-verbosity"
    )
    monkeypatch.setattr(
        mod, "OBSERVATION_SOURCE_QUALITY_AUDIT_DIR", tmp_path / "missing-audit"
    )
    monkeypatch.setattr(
        mod, "CODEBASE_PERFORMANCE_WORKORDER_DIR", tmp_path / "missing-performance"
    )
    monkeypatch.setattr(
        mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing-currentness"
    )
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CODE_IMPROVEMENT_WORKORDER_DIR", doc_dir)

    report = mod.build_code_improvement_workorder("2026-05-21", max_orders=5)

    order = next(
        item
        for item in report["orders"]
        if item["order_id"]
        == "order_lifecycle_entry_bucket_liquidity_bucket_liquidity_unknown"
    )
    assert order["decision"] == "implement_now"
    assert order["runtime_effect"] is False
    assert (
        order["source_report_type"]
        == "lifecycle_decision_matrix_entry_bucket_attribution"
    )
    assert "bucket_key=liquidity_unknown" in order["evidence"]
    scale_order = next(
        item
        for item in report["orders"]
        if item["order_id"]
        == "order_lifecycle_scale_in_bucket_blocker_namespace_price_guard"
    )
    assert scale_order["decision"] == "implement_now"
    assert scale_order["runtime_effect"] is False
    assert scale_order["allowed_runtime_apply"] is False
    assert (
        scale_order["source_report_type"]
        == "lifecycle_decision_matrix_scale_in_bucket_attribution"
    )
    assert "bucket_key=PRICE_GUARD" in scale_order["evidence"]
    overnight_order = next(
        item
        for item in report["orders"]
        if item["order_id"]
        == "order_lifecycle_overnight_bucket_overnight_action_sell_today"
    )
    assert overnight_order["decision"] == "attach_existing_family"
    assert (
        overnight_order["derived_review_category"]
        == "already_implemented_source_handoff"
    )
    assert overnight_order["implementation_candidate"] is False
    assert overnight_order["runtime_effect"] is False
    assert overnight_order["allowed_runtime_apply"] is False
    assert overnight_order["implementation_status"] == "implemented"
    assert overnight_order["implementation_provenance"]["runtime_effect"] is False
    assert (
        overnight_order["implementation_provenance"]["decision_authority"]
        == "adm_ldm_overnight_bucket_attribution_source_only"
    )
    assert (
        overnight_order["source_report_type"]
        == "lifecycle_decision_matrix_overnight_bucket_attribution"
    )
    assert "bucket_key=SELL_TODAY" in overnight_order["evidence"]
    assert report["summary"]["already_implemented_source_handoff_count"] == 1
    assert report["summary"]["lifecycle_entry_bucket_source_order_count"] == 1
    assert report["summary"]["lifecycle_scale_in_bucket_source_order_count"] == 1
    assert report["summary"]["lifecycle_overnight_bucket_source_order_count"] == 1
    assert report["source"]["lifecycle_decision_matrix"] == str(ldm_path)


def test_sim_fill_canonical_price_gap_fires_only_for_unpriced_no_canonical():
    family_reports = [
        {
            "family": "dynamic_entry_price_resolver",
            "sim_submit_path_quality": {
                "scalp_sim_buy_order_virtual_pending": {
                    "priced_sample_count": 3,
                    "canonical_sim_fill_price_defect_breakdown": {
                        "priced_valid": 1,
                        "limit_fill_price_missing_but_assumed_present": 2,
                        "unpriced_no_canonical": 0,
                    },
                },
            },
        },
    ]
    ev_report = {
        "calibration": {"scalp_simulator": {}},
        "family_reports": family_reports,
    }
    orders = mod._sim_fill_and_match_report_contract_orders(ev_report)
    gap_ids = [o["order_id"] for o in orders]
    assert "order_sim_fill_canonical_price_contract_gap" not in gap_ids


def test_sim_fill_canonical_price_gap_fires_for_unpriced_no_canonical_present():
    family_reports = [
        {
            "family": "dynamic_entry_price_resolver",
            "sim_submit_path_quality": {
                "scalp_sim_buy_order_virtual_pending": {
                    "priced_sample_count": 3,
                    "canonical_sim_fill_price_defect_breakdown": {
                        "priced_valid": 1,
                        "limit_fill_price_missing_but_assumed_present": 1,
                        "unpriced_no_canonical": 1,
                    },
                },
            },
        },
    ]
    ev_report = {
        "calibration": {"scalp_simulator": {}},
        "family_reports": family_reports,
    }
    orders = mod._sim_fill_and_match_report_contract_orders(ev_report)
    gap_ids = [o["order_id"] for o in orders]
    assert "order_sim_fill_canonical_price_contract_gap" in gap_ids


def test_contract_missing_threshold_creates_workorder():
    ev_report = {
        "calibration": {
            "scalp_simulator": {
                "lifecycle_bucket_match_aggregation": {
                    "contract_missing_count": 5,
                    "active_seed_prefix_matched_parent_missing_count": 0,
                    "active_seed_matched_none_count": 5,
                    "eligible_active_seed_matched_none_count": 2,
                    "natural_no_match_count": 10,
                    "panic_scale_in_stage_excluded_count": 3,
                    "hypothesis_matched_but_parent_bucket_no_match_count": 0,
                },
                "swing_micro_source_quality": {
                    "provenance_gap_count": 0,
                    "missing_ws_quote_source_count": 0,
                    "ready_count": 0,
                },
            },
        },
        "family_reports": [],
    }
    orders = mod._sim_fill_and_match_report_contract_orders(ev_report)
    gap_ids = [o["order_id"] for o in orders]
    assert "order_active_seed_or_ldm_match_missing_contract_gap" in gap_ids
    gap = next(
        o
        for o in orders
        if o["order_id"] == "order_active_seed_or_ldm_match_missing_contract_gap"
    )
    assert "eligible_active_seed_matched_none_count=2" in gap["evidence"]


def test_contract_missing_threshold_reads_top_level_scalp_simulator():
    ev_report = {
        "scalp_simulator": {
            "lifecycle_bucket_match_aggregation": {
                "contract_missing_count": 563,
                "active_seed_prefix_matched_parent_missing_count": 0,
                "active_seed_matched_none_count": 5655,
                "not_instrumented_count": 4250,
                "natural_no_match_count": 0,
                "panic_scale_in_stage_excluded_count": 842,
                "hypothesis_matched_but_parent_bucket_no_match_count": 0,
            },
            "swing_micro_source_quality": {
                "provenance_gap_count": 0,
                "missing_ws_quote_source_count": 0,
                "ready_count": 0,
            },
        },
        "family_reports": [],
    }
    orders = mod._sim_fill_and_match_report_contract_orders(ev_report)
    gap_ids = [o["order_id"] for o in orders]
    assert "order_active_seed_or_ldm_match_missing_contract_gap" in gap_ids


def test_contract_missing_below_threshold_no_workorder():
    ev_report = {
        "calibration": {
            "scalp_simulator": {
                "lifecycle_bucket_match_aggregation": {
                    "contract_missing_count": 1,
                    "active_seed_prefix_matched_parent_missing_count": 1,
                    "active_seed_matched_none_count": 1,
                    "natural_no_match_count": 2,
                    "panic_scale_in_stage_excluded_count": 0,
                    "hypothesis_matched_but_parent_bucket_no_match_count": 0,
                },
                "swing_micro_source_quality": {
                    "provenance_gap_count": 0,
                    "missing_ws_quote_source_count": 0,
                    "ready_count": 0,
                },
            },
        },
        "family_reports": [],
    }
    orders = mod._sim_fill_and_match_report_contract_orders(ev_report)
    gap_ids = [o["order_id"] for o in orders]
    assert "order_active_seed_or_ldm_match_missing_contract_gap" not in gap_ids


def test_policy_missing_threshold_creates_workorder():
    ev_report = {
        "calibration": {
            "scalp_simulator": {
                "lifecycle_bucket_match_aggregation": {
                    "contract_missing_count": 0,
                    "eligible_policy_missing_count": 5,
                    "active_seed_prefix_matched_parent_missing_count": 0,
                    "active_seed_matched_none_count": 5,
                    "eligible_active_seed_matched_none_count": 5,
                    "natural_no_match_count": 0,
                    "panic_scale_in_stage_excluded_count": 0,
                    "hypothesis_matched_but_parent_bucket_no_match_count": 0,
                },
                "swing_micro_source_quality": {
                    "provenance_gap_count": 0,
                    "missing_ws_quote_source_count": 0,
                    "ready_count": 0,
                },
            },
        },
        "family_reports": [],
    }

    orders = mod._sim_fill_and_match_report_contract_orders(ev_report)

    gap = next(
        order
        for order in orders
        if order["order_id"] == "order_active_seed_or_ldm_match_missing_contract_gap"
    )
    assert "eligible_policy_missing_count=5" in gap["evidence"]
    assert "eligible_policy_missing_count < threshold" in gap["next_postclose_metric"]


def test_prefix_parent_missing_creates_workorder():
    ev_report = {
        "calibration": {
            "scalp_simulator": {
                "lifecycle_bucket_match_aggregation": {
                    "contract_missing_count": 0,
                    "active_seed_prefix_matched_parent_missing_count": 5,
                    "active_seed_matched_none_count": 1,
                    "natural_no_match_count": 0,
                    "panic_scale_in_stage_excluded_count": 0,
                    "hypothesis_matched_but_parent_bucket_no_match_count": 0,
                },
                "swing_micro_source_quality": {
                    "provenance_gap_count": 0,
                    "missing_ws_quote_source_count": 0,
                    "ready_count": 0,
                },
            },
        },
        "family_reports": [],
    }
    orders = mod._sim_fill_and_match_report_contract_orders(ev_report)
    gap_ids = [o["order_id"] for o in orders]
    assert "order_active_seed_or_ldm_match_missing_contract_gap" in gap_ids


def test_natural_no_match_not_workorder_trigger():
    ev_report = {
        "calibration": {
            "scalp_simulator": {
                "lifecycle_bucket_match_aggregation": {
                    "contract_missing_count": 0,
                    "active_seed_prefix_matched_parent_missing_count": 1,
                    "active_seed_matched_none_count": 0,
                    "natural_no_match_count": 20,
                    "panic_scale_in_stage_excluded_count": 5,
                    "hypothesis_matched_but_parent_bucket_no_match_count": 3,
                },
                "swing_micro_source_quality": {
                    "provenance_gap_count": 0,
                    "missing_ws_quote_source_count": 0,
                    "ready_count": 0,
                },
            },
        },
        "family_reports": [],
    }
    orders = mod._sim_fill_and_match_report_contract_orders(ev_report)
    gap_ids = [o["order_id"] for o in orders]
    assert "order_active_seed_or_ldm_match_missing_contract_gap" not in gap_ids


def test_entry_split_real_detail_primary_book_does_not_create_unused_real_sample_order():
    ev_report = {
        "entry_split_order_plan": {
            "available": True,
            "status": "pass",
            "schema_version": "entry_split_order_plan_v1",
            "real_sample_count": 100,
            "real_outcome_joined_sample": 17,
            "recommended_policy_candidate_count": 1,
            "primary_sample_book": "real_submit_post_submit_observed_low",
        }
    }

    assert mod._entry_split_order_plan_followup_orders(ev_report) == []


def test_source_quality_contract_gap_creates_workorder():
    sq_report = {"status": "fail"}
    ev_report = {
        "calibration": {
            "scalp_simulator": {
                "lifecycle_bucket_match_aggregation": {},
                "swing_micro_source_quality": {},
            },
        },
        "family_reports": [],
    }
    orders = mod._sim_fill_and_match_report_contract_orders(ev_report, sq_report)
    gap_ids = [o["order_id"] for o in orders]
    assert "order_source_quality_report_contract_status_gap" in gap_ids
