import json
import pytest
from src.engine.automation import codex_workorder_runner
from src.engine.lifecycle.archive import build_code_improvement_workorder_readers as mod
from src.engine.lifecycle.archive import lifecycle_decision_matrix_readers as ldm_mod


def test_retired_recheck_order_repetition_cannot_restore_implementation():
    item = mod.ClassifiedOrder(
        order={
            "order_id": "order_entry_recheck_source_repair",
            "source_report_type": "entry_recheck_drought_controller",
            "implementation_status": "source_gap",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        decision="defer_evidence",
        reason="historical",
        mapped_family="entry_opportunity_recheck_runtime",
        route="maintenance_review",
        confidence="historical",
        automation_reentry="retired",
    )
    result, ids = mod._escalate_repeated_unresolved_orders(
        [item], repeat_counts={"order_entry_recheck_source_repair": {"count": 3}}
    )
    assert ids == []
    assert result == []


def test_scanner_source_repair_emits_its_actual_downstream_contract():
    from src.engine.lifecycle.archive.build_code_improvement_workorder_readers import (
        _intraday_ws_freshness_followup_orders,
    )

    rows = _intraday_ws_freshness_followup_orders(
        {
            "workorder_directives": [
                {
                    "order_id": "order_scanner_eligible_no_heavy_closed_loop",
                    "decision": "implement_now",
                }
            ]
        }
    )
    assert rows[0]["required_downstream"] == [
        "intraday_ws_freshness_monitor",
        "code_improvement_workorder",
        "runtime_approval_summary",
        "threshold_cycle_postclose_verification",
    ]
    assert rows[0]["runtime_effect"] is False
    assert rows[0]["allowed_runtime_apply"] is False
    assert rows[0]["resolution_mode"] == "producer_repair"
    assert rows[0]["economic_eligibility"] == "blocked_structural"
    assert rows[0]["action_priority_class"] == "P2"


def test_ws_subscription_stale_observability_uses_existing_repair_receipts():
    rows = mod._intraday_ws_freshness_followup_orders(
        {
            "workorder_directives": [
                {
                    "order_id": "order_ws_subscription_stale_repair_observability",
                    "decision": "implement_now",
                    "evidence": [
                        "pipeline_subscription_stale_count=971",
                        "snapshot_repair_recommended_count=0",
                    ],
                }
            ]
        }
    )

    assert rows[0]["implementation_status"] == (
        "implemented_source_quality_contract_waiting_sample"
    )
    assert rows[0]["resolution_mode"] == "natural_maturity"
    assert rows[0]["economic_eligibility"] == "pending_maturity"
    classified = mod._classify_order(
        rows[0],
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "attach_existing_family"


def test_scanner_economics_preserves_measured_no_edge_and_actual_source_gap():
    evidence = mod._scanner_lookup_attention_economic_evidence(
        {
            "target_date": "2026-09-17",
            "scanner_lookup_attention_publication": {
                "source_evaluation_date": "2026-09-17",
                "publication_date": "2026-09-19",
                "effective_date": "2026-09-21",
                "policy_artifact_sha256": "policy-sha",
            },
            "scanner_unique_funnel": {
                "economic_cohorts": {
                    "lookup_attention_selection": {
                        "artifact_sha256": "economic-sha",
                        "closure_test": "future_assigned_arm_completed",
                        "eta": None,
                        "selection_opportunity_economics": {
                            "status": "hold_no_edge",
                            "metric_role": "sim_probe_ev",
                            "selection_opportunity_ev_pct": -2.38954987,
                            "daily_incremental_opportunity_pct": {
                                "2026-09-17": -0.93445645
                            },
                            "daily_net_profit_krw": None,
                            "daily_net_profit_reason": (
                                "entry_quantity_and_actual_fill_not_observed_for_unselected_arm"
                            ),
                            "resolved_pair_count": 3,
                            "resolved_date_count": 3,
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                        },
                        "primary_economics": {
                            "status": "source_gap",
                            "baseline_budget_ev_pct": None,
                            "candidate_budget_ev_pct": None,
                            "paired_delta_ev_pct": None,
                            "source_gaps": [
                                "complete_partition_or_actual_selection_missing",
                                "original_unselected_entry_recipe_quantity_guard_missing",
                            ],
                        },
                        "actual_completed": {
                            "metric_role": "observational_completed_net",
                            "causal_uplift": None,
                            "book": {"candidate_control_ev_uplift_pct": 0.02},
                        },
                    }
                }
            },
        }
    )

    assert evidence["opportunity"]["comparison_status"] == "measured_no_edge"
    assert evidence["opportunity"]["paired_delta_ev_pct"] == -2.38954987
    assert evidence["opportunity"]["daily_net_profit_krw"] is None
    assert (
        evidence["actual_policy_comparison"]["resolution_mode"]
        == "historical_unrecoverable"
    )
    assert evidence["policy_handoff"]["disposition"] == "incumbent_preserved"
    semantic = dict(evidence)
    semantic.pop("semantic_sha256")
    from src.engine.automation.postclose_workorder_contract import digest

    assert evidence["semantic_sha256"] == digest(semantic)


def test_structural_priority_precedes_non_actionable_no_edge():
    p0 = mod.ClassifiedOrder(
        order={
            "order_id": "p0",
            "priority": 9,
            "action_priority_class": "P0",
        },
        decision="implement_now",
        reason="fixture",
        mapped_family=None,
        route=None,
        confidence=None,
        automation_reentry="fixture",
    )
    p1 = mod.ClassifiedOrder(
        order={
            "order_id": "p1",
            "priority": 0,
            "action_priority_class": "P1",
        },
        decision="implement_now",
        reason="fixture",
        mapped_family=None,
        route=None,
        confidence=None,
        automation_reentry="fixture",
    )
    assert [row.order["order_id"] for row in mod._sort_classified([p1, p0])] == [
        "p0",
        "p1",
    ]


def test_direct_family_mode_drops_retired_owner_and_stale_file_references():
    assert (
        mod._direct_family_order(
            {
                "source_report_type": "observation_source_quality_audit",
                "target_subsystem": "daily_threshold_cycle_report",
            }
        )
        is None
    )
    sanitized = mod._direct_family_order(
        {
            "source_report_type": "buy_funnel_sentinel",
            "target_subsystem": "runtime_instrumentation",
            "files_likely_touched": [
                "src/engine/buy_funnel_sentinel.py",
                "src/engine/threshold_cycle_ev_report.py",
            ],
            "acceptance_tests": [
                "pytest src/tests/test_buy_funnel_sentinel.py",
                "pytest src/tests/test_threshold_cycle_ev_report.py",
            ],
            "required_downstream": [
                "runtime_approval_summary",
                "threshold_cycle_ev_report",
            ],
            "implementation_provenance": {
                "required_downstream": [
                    "runtime_approval_summary",
                    "threshold_cycle_ev_report",
                ]
            },
        }
    )
    assert sanitized["files_likely_touched"] == ["src/engine/buy_funnel_sentinel.py"]
    assert sanitized["acceptance_tests"] == [
        "pytest src/tests/test_buy_funnel_sentinel.py"
    ]
    assert sanitized["required_downstream"] == ["runtime_approval_summary"]
    assert sanitized["implementation_provenance"]["required_downstream"] == [
        "runtime_approval_summary"
    ]


def test_generation_identity_binds_direct_family_mode():
    source_hash = "a" * 64
    legacy = mod._generation_fingerprint(
        source_hash,
        max_orders=12,
        include_swing=True,
        direct_family_only=False,
    )
    direct = mod._generation_fingerprint(
        source_hash,
        max_orders=12,
        include_swing=True,
        direct_family_only=True,
    )

    assert legacy["generation_hash"] != direct["generation_hash"]
    assert direct["inputs"]["direct_family_only"] is True
    assert direct["inputs"]["source_hash_contract"] == "logical_source_content_v2"


def test_source_hash_ignores_managed_release_root_alias(tmp_path):
    source = tmp_path / "canonical" / "source.json"
    source.parent.mkdir()
    source.write_text('{"value":1}')
    first = tmp_path / "release-a.json"
    second = tmp_path / "release-b.json"
    first.symlink_to(source)
    second.symlink_to(source)

    first_fingerprint = mod._source_fingerprint({"source": first})
    second_fingerprint = mod._source_fingerprint({"source": second})

    assert (
        first_fingerprint["files"][0]["path"] != second_fingerprint["files"][0]["path"]
    )
    assert first_fingerprint["source_hash"] == second_fingerprint["source_hash"]


def test_panic_report_only_provenance_is_explicit_at_native_row_boundary():
    from src.engine.automation.postclose_workorder_contract import authority_class

    row = mod._panic_lifecycle_followup_orders(
        {
            "calibration_source_bundle": {
                "source_metrics": {
                    "panic_sell_defense": {"panic_state": "RECOVERY_WATCH"}
                }
            }
        }
    )[0]
    assert row["implementation_provenance"]["allowed_runtime_apply"] is False
    assert authority_class(row) == "eligible_runtime_effect_false"
    assert row["actual_order_submitted"] is False
    assert row["broker_order_forbidden"] is True
    assert "runtime_approval_summary" in row["required_downstream"]


def test_prompt_research_source_preserves_hash_and_reports_corruption(tmp_path):
    from src.engine.scalping import main_ai_prompt_consumer as consumer

    path = tmp_path / "optimizer.json"
    assert mod._load_prompt_research_source(path, isolated_source_mode=False) == {}
    original = {"historical_audit": {"entry_adm": {"status": "retired"}}}
    path.write_text(json.dumps(original), encoding="utf-8")
    assert (
        mod._load_prompt_research_source(path, isolated_source_mode=False) == original
    )
    for text in ("{bad", "[]", "{}"):
        path.write_text(text, encoding="utf-8")
        source = mod._load_prompt_research_source(path, isolated_source_mode=False)
        assert source.get("source_read_error")
        orders = consumer.prompt_revision_review_workorders(source, "2026-09-09")
        assert orders[0]["order_id"] == "order_entry_prompt_revision_source_contract"
        assert orders[0]["runtime_effect"] is False


def test_buy_funnel_workorder_uses_selected_venue_session_summary():
    report = {
        "classification": {
            "primary": "SUBMIT_DROUGHT_CRITICAL",
            "matches": ["SUBMIT_DROUGHT_CRITICAL"],
            "scope_key": "NXT|NXT_AFTERMARKET",
        },
        "current": {
            "session": {
                "stage_unique": {"ai_confirmed": 999, "order_bundle_submitted": 999},
                "ratios": {"submitted_to_ai_unique_pct": 100.0},
                "blocker_top": [],
                "upstream_blocker_top": [],
                "latency_blocker_top": [],
            },
            "by_venue_session": {
                "NXT|NXT_AFTERMARKET": {
                    "summary": {
                        "stage_unique": {
                            "ai_confirmed": 20,
                            "budget_pass": 5,
                            "latency_pass": 2,
                            "order_bundle_submitted": 1,
                        },
                        "ratios": {
                            "submitted_to_ai_unique_pct": 5.0,
                            "submitted_to_budget_unique_pct": 20.0,
                        },
                        "blocker_top": [],
                        "upstream_blocker_top": [],
                        "latency_blocker_top": [],
                    }
                }
            },
        },
        "entry_submit_drought_contract": {"critical": True},
    }

    orders = mod._buy_funnel_sentinel_followup_orders(report)

    evidence = orders[0]["evidence"]
    assert "scope_key=NXT|NXT_AFTERMARKET" in evidence
    assert "ai_confirmed_unique=20" in evidence
    assert "submitted_unique=1" in evidence
    assert "ai_confirmed_unique=999" not in evidence


def test_generation_fingerprint_binds_producer_contract_and_selection_scope():
    source_hash = "a" * 64

    base = mod._generation_fingerprint(
        source_hash,
        max_orders=12,
        include_swing=False,
        direct_family_only=False,
    )
    different_limit = mod._generation_fingerprint(
        source_hash,
        max_orders=13,
        include_swing=False,
        direct_family_only=False,
    )
    different_scope = mod._generation_fingerprint(
        source_hash,
        max_orders=12,
        include_swing=True,
        direct_family_only=False,
    )

    assert len(base["generation_hash"]) == 64
    assert base["generation_id"] == base["generation_hash"][:12]
    assert base["generation_hash"] != different_limit["generation_hash"]
    assert base["generation_hash"] != different_scope["generation_hash"]


def test_intraday_ws_directive_state_mapping_does_not_close_pending_code_gap():
    implemented_states = {
        "closed_loop_instrumentation_active",
        "scanner_prefilter_and_exact_terminalization_implemented",
        "scanner_candidate_prune_receipts_implemented_waiting_natural_generation",
        "bounded_prune_rest_bbo_collector_implemented_waiting_next_pid_natural_episode_receipts",
        "bounded_prune_rest_bbo_collector_schedule_receipts_observed",
        "bounded_prune_rest_bbo_collector_runtime_receipts_observed",
        "handoff_provenance_implemented_not_runtime_reflected",
        "implemented_in_source_report",
        "implemented_pending_new_dashboard_snapshot",
    }
    directives = [
        {
            "order_id": f"order_{index}",
            "implementation_state": state,
            "decision": "defer_evidence",
        }
        for index, state in enumerate(sorted(implemented_states))
    ]
    directives.append(
        {
            "order_id": "order_pending",
            "implementation_state": "cohorts_identified_bbo_join_pending",
            "decision": "defer_evidence",
        }
    )
    directives.append(
        {
            "order_id": "order_source_capture_design",
            "implementation_state": (
                "executable_bbo_consumer_implemented_source_capture_design_required"
            ),
            "decision": "design_family_candidate",
            "decision_authority": "scanner_funnel_executable_bbo_source_only",
        }
    )

    orders = mod._intraday_ws_freshness_followup_orders(
        {"source_paths": {}, "workorder_directives": directives}
    )
    by_id = {item["order_id"]: item for item in orders}

    assert all(
        by_id[f"order_{index}"]["implementation_status"]
        in {
            "implemented_but_waiting_sample",
            "implemented_source_quality_contract_waiting_sample",
        }
        for index in range(len(implemented_states))
    )
    assert by_id["order_pending"]["implementation_status"] is None
    assert by_id["order_source_capture_design"]["implementation_status"] is None
    assert by_id["order_source_capture_design"]["decision"] == (
        "design_family_candidate"
    )
    classified = mod._classify_order(
        by_id["order_source_capture_design"],
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    assert classified.decision == "design_family_candidate"
    assert classified.route == "design_family_candidate"
    serialized = mod._serialize_classified_order(classified)
    assert serialized["decision_authority"] == (
        "scanner_funnel_executable_bbo_source_only"
    )
    assert serialized["root_cause_closure_status"] == "needs_followup_workorder"


@pytest.mark.parametrize("source_gap", [False, True])
def test_repeated_one_share_evidence_is_not_a_new_code_defect(source_gap):
    order = {
        "order_id": "order_one_share_evidence",
        "source_report_type": "one_share_threshold_opportunity",
        "improvement_type": (
            "source_quality_gap"
            if source_gap
            else "source_only_existing_family_evidence"
        ),
        "implementation_status": "source_evidence_candidate",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "implementation_provenance": {
            "workorder_intake_role": "attach_existing_family_evidence",
            "source_audit_implementation_status": "implemented",
        },
    }
    item = mod.ClassifiedOrder(
        order,
        "attach_existing_family",
        "evidence",
        "entry_opportunity_recheck_runtime",
        "existing_family",
        "thin",
        "source-only",
    )
    result, ids = mod._escalate_repeated_unresolved_orders(
        [item],
        repeat_counts={"order_one_share_evidence": {"count": 3}},
    )
    assert ids == []
    assert result == []


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

    assert orders == []


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
    assert orders == []


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
    assert orders == []


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
    assert orders == []


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
    assert orders == []


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
    assert classified.decision == "attach_existing_family"
    assert classified.route == "existing_family"
    serialized = mod._serialize_classified_order(classified)
    assert serialized["forbidden_uses"]
    assert serialized["economic_eligibility"] == "not_applicable"
    assert serialized["action_priority_class"] == "P4"
    assert not codex_workorder_runner.is_safe_implement_now(serialized)
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
    assert unknown_orders[0]["decision"] == "attach_existing_family"
    assert unknown_orders[0]["economic_eligibility"] == "not_applicable"
    assert not codex_workorder_runner.is_safe_implement_now(unknown_orders[0])
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


def test_observation_source_quality_closed_data_revalidation_keeps_producer_gap_open():
    report = {
        "status": "pass",
        "summary": {
            "event_count": 20,
            "tuning_input_allowed": True,
            "hard_blocking_contract_gap_count": 0,
            "current_scan_hard_blocking_excluded_row_count": 0,
            "post_exclusion_hard_blocking_excluded_row_count": 0,
            "raw_row_exclusion_revalidation_required": False,
        },
        "raw_row_exclusion": {
            "excluded_row_count": 2,
            "stage_counts": {"legacy_gap": 2},
            "exclusion_reasons": {"required_field_missing": 2},
        },
    }

    order = next(
        item
        for item in mod._observation_source_quality_followup_orders(report)
        if item["order_id"]
        == "order_observation_source_quality_raw_row_exclusion_producer_gap"
    )
    classified = mod._serialize_classified_order(
        mod._classify_order(
            order,
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
    )

    assert classified["decision"] == "implement_now"
    assert classified["route"] == "source_quality_raw_row_exclusion_producer_fix"
    assert classified["implementation_status"] is None
    assert classified["terminal_disposition"] is None
    assert classified["raw_row_exclusion_context_classification"] is None
    assert classified["raw_row_exclusion_data_sanitation_revalidated"] is True
    assert classified["producer_gap_closure_contract"] == (
        "producer_fix_receipt_plus_post_fix_natural_zero_recurrence_required"
    )
    assert classified["runtime_effect"] is False
    assert classified["allowed_runtime_apply"] is False
    assert codex_workorder_runner.is_safe_implement_now(classified)


def test_observation_source_quality_closed_data_revalidation_with_warning_keeps_gap_open():
    report = {
        "status": "warning",
        "summary": {
            "event_count": 20,
            "review_warning_count": 1,
            "review_warning_stages": ["order_bundle_failed"],
            "tuning_input_allowed": True,
            "hard_blocking_contract_gap_count": 0,
            "current_scan_hard_blocking_excluded_row_count": 0,
            "post_exclusion_hard_blocking_excluded_row_count": 0,
            "raw_row_exclusion_revalidation_required": False,
        },
        "raw_row_exclusion": {
            "excluded_row_count": 1,
            "stage_counts": {"pre_submit_entry_ai_authority_guard_block": 1},
            "exclusion_reasons": {"required_field_missing": 1},
        },
    }

    order = next(
        item
        for item in mod._observation_source_quality_followup_orders(report)
        if item["order_id"]
        == "order_observation_source_quality_raw_row_exclusion_producer_gap"
    )
    classified = mod._serialize_classified_order(
        mod._classify_order(
            order,
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
    )

    assert classified["decision"] == "implement_now"
    assert classified["route"] == "source_quality_raw_row_exclusion_producer_fix"
    assert classified["implementation_status"] is None
    assert classified["terminal_disposition"] is None
    assert classified["raw_row_exclusion_context_classification"] is None
    assert classified["raw_row_exclusion_data_sanitation_revalidated"] is True
    assert codex_workorder_runner.is_safe_implement_now(classified)


def test_observation_source_quality_warning_missing_revalidation_counts_stays_open():
    report = {
        "status": "warning",
        "summary": {
            "tuning_input_allowed": True,
            "raw_row_exclusion_revalidation_required": False,
        },
        "raw_row_exclusion": {
            "excluded_row_count": 1,
            "stage_counts": {"custom_stage": 1},
            "exclusion_reasons": {"required_field_missing": 1},
        },
    }

    order = next(
        item
        for item in mod._observation_source_quality_followup_orders(report)
        if item["order_id"]
        == "order_observation_source_quality_raw_row_exclusion_producer_gap"
    )
    classified = mod._serialize_classified_order(
        mod._classify_order(
            order,
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
    )

    assert classified["decision"] == "implement_now"
    assert classified["route"] == "source_quality_raw_row_exclusion_producer_fix"
    assert classified["implementation_status"] is None


def test_legacy_raw_row_exclusion_revalidation_closure_is_reopened_for_producer_fix():
    order = {
        "order_id": "order_observation_source_quality_raw_row_exclusion_producer_gap",
        "source_report_type": "observation_source_quality_audit",
        "mapped_family": "observation_source_quality_audit",
        "improvement_type": "source_quality_raw_row_exclusion_revalidated_closed",
        "route": "source_quality_raw_row_exclusion_revalidated_closed",
        "confidence": "audit",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": ["runtime_threshold_apply"],
    }

    classified = mod._serialize_classified_order(
        mod._classify_order(
            order,
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
    )

    assert classified["decision"] == "implement_now"
    assert classified["route"] == "source_quality_raw_row_exclusion_producer_fix"
    assert classified["implementation_status"] is None
    assert classified["terminal_disposition"] is None


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


def test_observation_source_quality_entry_recheck_unknown_provenance_attaches_existing_family():
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
                "stage": "scalp_entry_action_decision_snapshot",
                "event_count": 100,
                "fields": [
                    {
                        "field": "entry_recheck_excluded_reason",
                        "count": 10,
                        "rate": 0.1,
                        "examples": ["unusable_source:unknown"],
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
    assert (
        order["implementation_provenance"]["current_raw_contains_pre_fix_rows"] is True
    )
    assert classified.decision == "attach_existing_family"


def test_observation_source_quality_scanner_venue_fix_attaches_existing_family():
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
                "stage": "scalping_scanner_fast_precheck",
                "event_count": 100,
                "fields": [
                    {
                        "field": "scanner_promotion_reanchor_effective_venue",
                        "count": 10,
                        "rate": 0.1,
                        "examples": ["UNKNOWN"],
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

    order = mod._lifecycle_bucket_discovery_followup_orders(report)
    assert order == []


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
        "order_id": "order_pattern_lab_ai_review_swing_pattern_lab_automation",
        "title": "Pattern Lab AI review follow-up: swing_pattern_lab_automation",
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


def test_submit_drought_marker_keeps_exact_source_quality_gap_open():
    from datetime import datetime
    from src.engine.buy_funnel_sentinel import PipelineEvent
    from src.tests.submit_drought_fixtures import make_report

    events = [
        PipelineEvent(
            datetime(2026, 9, 7, 10),
            "ENTRY_PIPELINE",
            "budget_pass",
            "fixture",
            "000001",
            "",
            {},
        )
    ]
    report = make_report(events=events)
    marker = mod._entry_submit_drought_implementation_marker(
        report, report["entry_submit_drought_contract"]
    )

    assert marker["implementation_status"] == "implemented_source_quality_gap_open"
    assert (
        marker["implementation_provenance"]["root_cause_closure_status_hint"]
        == "source_quality_blocked"
    )
    assert (
        marker["implementation_provenance"]["exact_attempt_source_quality_open"] is True
    )


def test_submit_drought_marker_routes_legacy_superseded_rows_to_natural_receipt():
    from datetime import datetime, timedelta

    from src.engine.buy_funnel_sentinel import PipelineEvent
    from src.tests.submit_drought_fixtures import make_report

    started = datetime(2026, 9, 7, 10)
    events = [
        PipelineEvent(
            started,
            "ENTRY_PIPELINE",
            "ai_confirmed",
            "fixture",
            "000001",
            "1",
            {"scanner_promotion_id": "SCANPROM-A"},
        ),
        PipelineEvent(
            started + timedelta(seconds=1),
            "ENTRY_PIPELINE",
            "ai_confirmed",
            "fixture",
            "000001",
            "1",
            {"scanner_promotion_id": "SCANPROM-B"},
        ),
        PipelineEvent(
            started + timedelta(seconds=2),
            "ENTRY_PIPELINE",
            "blocked_ai_score",
            "fixture",
            "000001",
            "1",
            {"scanner_promotion_id": "SCANPROM-B"},
        ),
    ]
    report = make_report(events=events)

    marker = mod._entry_submit_drought_implementation_marker(
        report, report["entry_submit_drought_contract"]
    )

    assert marker["implementation_status"] == (
        "implemented_source_quality_contract_waiting_sample"
    )
    assert marker["action_priority_class"] == "P3"
    assert marker["resolution_mode"] == "natural_maturity"
    assert marker["economic_eligibility"] == "pending_maturity"
    assert marker["implementation_provenance"]["historical_superseded_only"] is True
    assert (
        marker["implementation_provenance"]["root_cause_closure_status_hint"]
        == "implementation_done"
    )


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


def test_followup_order_ids_keep_hash_for_long_source_keys():
    prefix = "same_long_source_prefix_" + ("x" * 120)
    entry_ids = {
        mod._lifecycle_entry_bucket_order_id(
            {
                "bucket_type": "combo_entry_spot",
                "bucket_key": f"{prefix}_{suffix}",
            }
        )
        for suffix in ("first", "second")
    }
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

    assert len(entry_ids) == 2
    assert all(
        len(order_id.rsplit("_", 1)[-1]) == 8
        and all(char in "0123456789abcdef" for char in order_id.rsplit("_", 1)[-1])
        for order_id in entry_ids
    )
    assert len(ldm_ids) == 2
    assert len({item["order_id"] for item in bucket_orders}) == 2
    assert len({item["order_id"] for item in conversion_orders}) == 2


def test_latency_diagnostic_consolidation_does_not_accept_runtime_mutation():
    for runtime_effect, expected in [
        (False, "attach_existing_family"),
        (True, "reject"),
    ]:
        classified = mod._classify_order(
            {
                "order_id": "order_latency_guard_miss_ev_recovery",
                "runtime_effect": runtime_effect,
            },
            finding_by_order_id={},
            finding_by_title_slug={},
            auto_family_order_ids=set(),
            closed_instrumentation_order_families={},
        )
        assert classified.decision == expected
    assert (
        "order_latency_guard_miss_ev_recovery"
        not in mod._closed_instrumentation_order_families(
            {
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "dynamic_entry_price_resolver",
                            "source_metrics": {"instrumentation_status": "implemented"},
                        }
                    ]
                }
            },
            target_date="2026-09-04",
        )
    )


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


def test_workorder_swing_scope_classifier_is_explicit():
    assert mod._is_swing_scoped_order(
        {
            "order_id": "order_swing_lifecycle_gap",
            "source_report_type": "swing_lifecycle_bucket_discovery",
        }
    )
    assert not mod._is_swing_scoped_order(
        {
            "order_id": "order_scalp_lifecycle_gap",
            "source_report_type": "lifecycle_bucket_discovery",
        }
    )


def test_scale_in_conditioned_no_fill_is_normal_but_source_gap_is_actionable():
    from src.engine.lifecycle.archive.build_code_improvement_workorder_readers import (
        _scale_in_split_order_plan_followup_orders,
    )

    summary = {
        "available": True,
        "schema_version": "scale_in_split_order_plan_v4",
        "status": "skipped_no_actual_fill",
        "evaluation_state": {"status": "skipped_no_actual_fill", "reason": None},
    }
    assert (
        _scale_in_split_order_plan_followup_orders(
            {"scale_in_split_order_plan": summary}
        )
        == []
    )
    summary.update(
        status="pending_filled_outcome",
        evaluation_state={
            "status": "pending_filled_outcome",
            "reason": "filled_outcome_receipt_price_or_lot_basis_incomplete",
        },
    )
    assert _scale_in_split_order_plan_followup_orders(
        {"scale_in_split_order_plan": summary}
    )


def test_unknown_provenance_handoff_keeps_native_id_and_field_scope():
    report = {
        "target_date": "2026-09-17",
        "status": "warning",
        "summary": {"tuning_input_allowed": True},
        "unknown_token_findings": [
            {
                "stage": "scalping_scanner_candidate_pruned",
                "event_count": 10,
                "fields": [
                    {"field": "actual_execution_venue", "count": 5, "rate": 0.5},
                    {"field": "market_data_route", "count": 3, "rate": 0.3},
                ],
            }
        ],
    }
    order = next(
        row
        for row in mod._observation_source_quality_followup_orders(report)
        if row["order_id"]
        == "order_observation_source_quality_unknown_token_provenance_gap"
    )
    classified = mod._classify_order(
        order,
        finding_by_order_id={},
        finding_by_title_slug={},
        auto_family_order_ids=set(),
        closed_instrumentation_order_families={},
    )
    published = mod._serialize_classified_order(classified)
    receipt = published["implementation_provenance"]
    assert receipt["remaining_unknown_fields"] == ["market_data_route"]
    assert receipt["source_target_date"] == "2026-09-17"
    assert (
        receipt["field_provenance_review"][0]["disposition"]
        == "reviewed_not_available_before_broker_execution"
    )
    assert (
        receipt["field_provenance_review"][1]["producer"]
        == "src/scanners/scalping_scanner.py"
    )
    assert published["runtime_effect"] is False


def test_retired_current_producer_preserves_prior_and_has_no_authority(
    tmp_path, monkeypatch
):
    import importlib

    current = importlib.import_module("src.engine.build_code_improvement_workorder")
    prior = tmp_path / "prior.json"
    prior.write_text("original")

    def forbidden(*a, **kw):
        raise AssertionError("retired producer accessed storage")

    monkeypatch.setattr(type(prior), "write_text", forbidden)
    monkeypatch.setattr(type(prior), "read_text", forbidden)
    result = current.build_code_improvement_workorder("2026-10-12")
    assert result["status"] == "retired" and result["allowed_runtime_apply"] is False
