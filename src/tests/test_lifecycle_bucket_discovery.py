import json
from types import SimpleNamespace

from src.engine import lifecycle_bucket_discovery as mod


def _ai_keep_response():
    return {
        "schema_version": 1,
        "interpretation": {
            "bucket_reviews": [],
            "source_contract_review": {"status": "pass", "changes": [], "reason": "contract stable"},
        },
        "audit": {"status": "pass", "issues": [], "reason": "two-pass review accepted"},
        "ai_tier2_proposals": [],
        "comparative_reviews": [],
        "final_conclusions": [],
    }


def _ai_block_response(reason, *, bucket_id=None):
    target_bucket_id = bucket_id or (
        "entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown"
    )
    return {
        "schema_version": 1,
        "interpretation": {
            "bucket_reviews": [],
            "source_contract_review": {"status": "pass", "changes": [], "reason": "contract stable"},
        },
        "audit": {"status": "correction_required", "issues": [reason], "reason": reason},
        "ai_tier2_proposals": [],
        "comparative_reviews": [],
        "final_conclusions": [
            {
                "bucket_id": target_bucket_id,
                "final_bucket_relation": "existing_bucket_refinement",
                "final_classification_state": "runtime_blocked_contract_gap",
                "final_decision": "block",
                "reason": reason,
            }
        ],
    }


def _ai_hybrid_taxonomy_response(bucket_id):
    return {
        "schema_version": 1,
        "interpretation": {
            "bucket_reviews": [],
            "source_contract_review": {"status": "pass", "changes": [], "reason": "contract stable"},
        },
        "audit": {"status": "pass", "issues": [], "reason": "dual proposal comparison accepted"},
        "ai_tier2_proposals": [
            {
                "bucket_id": bucket_id,
                "proposal_decision": "create_new_dimension",
                "recommended_canonical_bucket": "scale_in:blocker_reason:pnl_out_of_range",
                "recommended_metric_or_dimension": ["pnl_delta_pct", "pnl_delta_pct_bucket"],
                "reasoning_summary": "Use a shared PnL dimension rather than a separate bucket per numeric value.",
                "confidence": "high",
                "required_source_fields": [
                    "metric_role",
                    "decision_authority",
                    "window_policy",
                    "sample_floor",
                    "primary_decision_metric",
                    "source_quality_gate",
                    "forbidden_uses",
                ],
                "forbidden_uses": ["runtime_threshold_apply", "broker_submit"],
            }
        ],
        "comparative_reviews": [
            {
                "bucket_id": bucket_id,
                "selected_decision": "absorb_as_dimension",
                "selected_source": "hybrid",
                "recommended_canonical_bucket": "scale_in:blocker_reason:pnl_out_of_range",
                "recommended_metric_or_dimension": ["pnl_delta_pct", "pnl_delta_pct_bucket"],
                "comparison_summary": "Deterministic numeric extraction and AI dimension proposal agree.",
                "rejected_alternative_reason": "Creating a distinct numeric bucket would overfit.",
                "confidence": "high",
                "required_source_fields": [
                    "metric_role",
                    "decision_authority",
                    "window_policy",
                    "sample_floor",
                    "primary_decision_metric",
                    "source_quality_gate",
                    "forbidden_uses",
                ],
                "forbidden_uses": ["runtime_threshold_apply", "broker_submit"],
                "workorder_title": "Absorb numeric PnL blocker buckets into dimensions",
                "workorder_priority": "medium",
            }
        ],
        "final_conclusions": [],
    }


def _ai_proposal_without_comparison_response(bucket_id):
    payload = _ai_hybrid_taxonomy_response(bucket_id)
    payload["comparative_reviews"] = []
    return payload


def _legacy_ai_response_without_dual_taxonomy_fields():
    return {
        "schema_version": 1,
        "interpretation": {
            "bucket_reviews": [],
            "source_contract_review": {"status": "pass", "changes": [], "reason": "legacy schema"},
        },
        "audit": {"status": "pass", "issues": [], "reason": "legacy response"},
        "final_conclusions": [],
    }


def _write_ldm(path):
    path.write_text(
        json.dumps(
            {
                "date": path.stem.removeprefix("lifecycle_decision_matrix_"),
                "lifecycle_flow_bucket_attribution": {
                    "buckets": [
                        {
                            "lifecycle_flow_bucket_id": "lifecycle_flow:combo_lifecycle_flow:complete_good",
                            "bucket_type": "combo_lifecycle_flow",
                            "bucket_key": (
                                "entry=entry:combo_entry_spot:score_66_69|"
                                "submit=submit:combo_submit_quality:thin_ok|"
                                "holding=holding:combo_holding_flow:baseline_hold|"
                                "scale_in=scale_in:none|"
                                "exit=exit:combo_exit_result:tp"
                            ),
                            "sample": 22,
                            "joined_sample": 22,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 1.7,
                            "equal_weight_avg_profit_pct": 1.2,
                            "diagnostic_win_rate": 0.64,
                            "recommended_route": "candidate_recovery_or_relax",
                            "metric_scope": "lifecycle_bundle_ev",
                            "entry_bucket_id": "entry:combo_entry_spot:score_66_69",
                            "submit_bucket_id": "submit:combo_submit_quality:thin_ok",
                            "holding_bucket_id": "holding:combo_holding_flow:baseline_hold",
                            "exit_bucket_id": "exit:combo_exit_result:tp",
                            "child_bucket_ids": {
                                "entry": "entry:combo_entry_spot:score_66_69",
                                "submit": "submit:combo_submit_quality:thin_ok",
                                "holding": "holding:combo_holding_flow:baseline_hold",
                                "scale_in": [],
                                "exit": "exit:combo_exit_result:tp",
                            },
                            "stage_contract": {
                                "entry": {"contract_state": "present"},
                                "submit": {"contract_state": "present"},
                                "holding": {"contract_state": "present"},
                                "exit": {"contract_state": "present"},
                            },
                            "attribution_key": "sim_record_id:SIM-1",
                            "rollback_guard": "hard_safety_priority_plus_source_quality_and_post_apply_attribution",
                        }
                    ]
                },
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "combo_entry_spot",
                            "bucket_key": mod.ENTRY_LIVE_AUTO_BUCKET_KEY,
                            "sample": 44,
                            "joined_sample": 44,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 1.7,
                            "equal_weight_avg_profit_pct": 3.5,
                            "mfe_10m_pct": 5.0,
                            "mae_10m_pct": -3.1,
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                        {
                            "bucket_type": "combo_entry_spot",
                            "bucket_key": "score=unknown|source=blocked_ai_score",
                            "sample": 12,
                            "joined_sample": 12,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 2.2,
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                        {
                            "bucket_type": "score_band",
                            "bucket_key": "score_70_74",
                            "sample": 15,
                            "joined_sample": 6,
                            "join_rate": 0.4,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 1.4,
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                    ]
                },
                "holding_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "combo_holding_flow",
                            "bucket_key": "source=scalp_sim_holding_snapshot|action=HOLD|profit=profit_pos080_pos150|held=held_180_600s",
                            "sample": 15,
                            "joined_sample": 15,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 0.6,
                            "recommended_route": "candidate_recovery_or_relax",
                            "ai_inference_proposal": {
                                "model": "gpt-5.4-mini",
                                "reasoning_effort": "medium",
                                "runtime_effect": False,
                            },
                        }
                    ],
                    "runtime_approval_candidates": [],
                },
                "exit_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "combo_exit_result",
                            "bucket_key": "source=sim_post_sell_evaluations|rule=tp|outcome=GOOD_ENTRY|profit=profit_pos080_pos150",
                            "sample": 15,
                            "joined_sample": 15,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 0.6,
                            "recommended_route": "candidate_recovery_or_relax",
                        }
                    ],
                    "runtime_approval_candidates": [],
                },
                "scale_in_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "arm",
                            "bucket_key": "PYRAMID",
                            "sample": 38,
                            "joined_sample": 38,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": -13.3,
                            "recommended_route": "candidate_tighten_or_exclude",
                        },
                        {
                            "bucket_type": "blocker_reason",
                            "bucket_key": "pnl_out_of_range(0.32)",
                            "sample": 48,
                            "joined_sample": 48,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 0.32,
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                    ]
                },
                "overnight_bucket_attribution": {"buckets": []},
                "policy_entries": [
                    {
                        "policy_key": "holding:weighted_adm_v1",
                        "stage": "holding",
                        "sample": 25,
                        "joined_sample": 20,
                        "join_rate": 0.8,
                        "source_quality_gate": "pass",
                        "stage_ev_composite_pct": 0.42,
                        "selected_action": "HOLD",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_lifecycle_bucket_discovery_classifies_live_sim_and_new_buckets(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_keep_response(),
    )

    states = {item["bucket_id"]: item for item in report["surfaced_candidates"]}
    live = [item for item in states.values() if item["classification_state"] == "live_auto_apply_ready"]
    sim = [item for item in states.values() if item["classification_state"] == "sim_auto_approved"]
    entry_only_sources = [
        item for item in report["candidates"] if item.get("source_bucket_kind") == "entry_only_source_candidate"
    ]
    assert {item["live_auto_apply_family"] for item in live} == {
        mod.GREENFIELD_REAL_ENV_FAMILY,
        mod.SCALE_IN_LIVE_AUTO_FAMILY,
    }
    wait6579 = states["entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown"]
    assert wait6579["classification_state"] == "entry_only_sim_auto_approved"
    assert wait6579["evidence_grade"] == mod.EVIDENCE_GRADE_2_COUNTERFACTUAL
    assert wait6579["transition_target"] == "sim_lifecycle_handoff"
    assert wait6579["full_real_conversion_allowed"] is False
    assert wait6579["live_auto_apply_family"] is None
    assert wait6579["legacy_contract_known_unknown"] is False
    assert wait6579["source_dimension_gap"] == "unknown_source_dimensions"
    assert (wait6579["auto_promotion_contract"] or {})["deterministic_contract_required"] is False
    flow_live = next(item for item in live if item["live_auto_apply_family"] == mod.GREENFIELD_REAL_ENV_FAMILY)
    assert flow_live["stage"] == "lifecycle_flow"
    assert flow_live["metric_scope"] == "lifecycle_bundle_ev"
    assert flow_live["entry_bucket_id"] == "entry:combo_entry_spot:score_66_69"
    candidates_by_id = {item["bucket_id"]: item for item in report["candidates"]}
    holding = candidates_by_id[
        "holding:combo_holding_flow:source_scalp_sim_holding_snapshot_action_hold_profit_profit_pos080_pos150_held_held_180_600s"
    ]
    assert holding["classification_state"] == "source_only_keep_collecting"
    assert holding["bounded_live_canary_allowed"] is False
    assert holding["sim_lifecycle_handoff_allowed"] is False
    assert holding["ai_inference_proposal"]["model"] == "gpt-5.4-mini"
    mixed = states["entry:score_band:score_70_74"]
    assert mixed["evidence_grade"] == mod.EVIDENCE_GRADE_MIXED_SOURCE
    assert mixed["classification_state"] == "sim_auto_approved"
    assert mixed["bounded_live_canary_allowed"] is False
    scale_blocker = states["scale_in:blocker_reason:pnl_out_of_range_0_32"]
    assert scale_blocker["recommended_action"] == "keep_or_tighten_blocker_candidate"
    assert scale_blocker["legacy_raw_bucket_key"] == "pnl_out_of_range(0.32)"
    assert scale_blocker["canonical_bucket"] == "scale_in:blocker_reason:pnl_out_of_range"
    assert scale_blocker["normalized_metrics"]["pnl_delta_pct"] == 0.32
    assert scale_blocker["deterministic_proposal"]["proposal_decision"] == "absorb_as_dimension"
    assert scale_blocker["ai_tier2_comparative_review"]["selected_decision"] == "absorb_as_dimension"
    assert report["summary"]["deterministic_proposal_count"] == len(report["candidates"])
    assert report["summary"]["absorbed_bucket_count"] >= 1
    assert "canonical_bucket_count" in report["summary"]
    assert sim
    assert entry_only_sources
    assert entry_only_sources[0]["bucket_relation"] == "new_bucket_candidate"
    assert entry_only_sources[0]["classification_state"] == "entry_only_source_candidate"
    assert entry_only_sources[0]["source_bucket_id"]
    assert "recommended_resolution" in entry_only_sources[0]
    assert "source_bucket_kind_counts" in report["summary"]
    assert report["summary"]["human_intervention_required"] is False
    assert report["ai_two_pass_review"]["sharded"] is True
    assert {item["shard_id"] for item in report["ai_two_pass_review"]["shards"]} >= {
        "live_contract_review",
        "lifecycle_flow_review",
        "sim_policy_review",
        "gap_workorder_review",
        "taxonomy_discovery_review",
    }
    assert report["summary"]["ai_two_pass_review_shard_count"] == 5
    assert (report_dir / "lifecycle_bucket_discovery_2026-05-22.json").exists()
    assert (catalog_dir / "lifecycle_bucket_catalog_2026-05-22.json").exists()
    auto = json.loads((sim_dir / "lifecycle_bucket_sim_auto_approval_2026-05-22.json").read_text())
    assert auto["approved"] is True
    assert auto["broker_order_forbidden"] is True
    assert auto["actual_order_submitted"] is False
    assert auto["runtime_effect"] is False
    assert auto["allowed_runtime_apply"] is False
    assert auto["approved_bucket_count"] == len(auto["approved_bucket_ids"])
    assert auto["approved_evidence_grade_counts"].get(mod.EVIDENCE_GRADE_2_COUNTERFACTUAL, 0) == 0
    assert auto["source_quality_status"] == "pass"


def test_lifecycle_bucket_discovery_quarantines_contaminated_live_candidates(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    quarantine_dir = tmp_path / "quarantine"
    ldm_dir.mkdir()
    quarantine_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    monkeypatch.setattr(mod, "CONTAMINATION_WINDOW_DIR", quarantine_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-28.json")
    (quarantine_dir / "lifecycle_bucket_quarantine_2026-05-28.json").write_text(
        json.dumps(
            {
                "quarantine_id": "greenfield_partial_lifecycle_2026-05-28",
                "reason": "contaminated_greenfield_partial_lifecycle_policy",
                "exclude_live_auto_apply": True,
                "affected_families": [mod.GREENFIELD_REAL_ENV_FAMILY],
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_bucket_discovery_report(
        "2026-05-28",
        ai_raw_response=_ai_keep_response(),
    )

    by_id = {item["bucket_id"]: item for item in report["candidates"]}
    flow = next(item for item in by_id.values() if item.get("live_auto_apply_family") == mod.GREENFIELD_REAL_ENV_FAMILY)
    assert flow["classification_state"] == "runtime_blocked_contract_gap"
    assert flow["allowed_runtime_apply"] is False
    assert flow["promotion_ev_excluded_reason"] == "contaminated_greenfield_partial_lifecycle_policy"
    wait6579 = by_id[
        "entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown"
    ]
    assert wait6579["classification_state"] == "entry_only_sim_auto_approved"
    assert report["summary"]["live_auto_apply_ready_count"] == 1
    assert "contamination_quarantine_live_auto_blocked:1" in report["warnings"]


def test_lifecycle_bucket_discovery_blocks_deterministic_live_when_ai_review_disabled(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report("2026-05-22", ai_review_provider="none")

    blocked = [item for item in report["surfaced_candidates"] if item["classification_state"] == "runtime_blocked_contract_gap"]
    assert {item["live_auto_apply_family"] for item in blocked if item.get("live_auto_apply_family")} == {
        mod.GREENFIELD_REAL_ENV_FAMILY,
        mod.SCALE_IN_LIVE_AUTO_FAMILY,
    }
    assert all(item.get("ai_tier2_blocked_reason") == "ai_tier2_validation_not_parsed:disabled" for item in blocked)
    assert report["summary"]["ai_two_pass_review_status"] == "disabled"
    assert "ai_two_pass_review_disabled_fail_closed_live_auto_blocked" in report["warnings"]


def test_lifecycle_bucket_discovery_ignores_ambiguous_ai_block_for_live_candidate(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_block_response(
            "effect is only about 1 percent and confidence is low",
            bucket_id="scale_in:arm:pyramid",
        ),
    )

    live = [item for item in report["surfaced_candidates"] if item["classification_state"] == "live_auto_apply_ready"]
    ignored = [item for item in live if item.get("ai_review_block_ignored_reason")]
    assert all((item.get("auto_promotion_contract") or {}).get("tier2_status") == "parsed" for item in live)
    assert report["summary"]["live_auto_apply_ready_count"] == 2
    assert len(ignored) == 1
    assert "ai_review_ambiguous_live_candidate_kept_for_post_apply" in report["warnings"]


def test_lifecycle_bucket_discovery_compares_deterministic_and_ai_taxonomy_proposals(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    bucket_id = "scale_in:blocker_reason:pnl_out_of_range_0_32"
    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_hybrid_taxonomy_response(bucket_id),
    )

    item = next(candidate for candidate in report["candidates"] if candidate["bucket_id"] == bucket_id)
    assert item["ai_tier2_proposal"]["proposal_status"] == "provided"
    assert item["ai_tier2_proposal"]["proposal_decision"] == "create_new_dimension"
    assert item["ai_tier2_comparative_review"]["selected_source"] == "hybrid"
    assert item["ai_tier2_comparative_review"]["selected_decision"] == "absorb_as_dimension"
    assert item["ai_tier2_taxonomy_decision"] == "absorb_as_dimension"
    assert item["ai_tier2_confidence"] == "high"
    assert report["summary"]["ai_tier2_proposal_count"] == 1
    assert report["summary"]["reviewer_selected_hybrid_count"] == 1
    assert report["summary"]["taxonomy_selected_decision_counts"]["absorb_as_dimension"] >= 1


def test_lifecycle_bucket_discovery_fails_closed_when_ai_proposal_lacks_comparison(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_proposal_without_comparison_response("scale_in:blocker_reason:pnl_out_of_range_0_32"),
    )

    assert report["summary"]["ai_two_pass_review_status"] == "parse_rejected"
    assert "ai_review_comparative_review_missing:scale_in:blocker_reason:pnl_out_of_range_0_32" in report["warnings"]
    blocked = [item for item in report["surfaced_candidates"] if item["classification_state"] == "runtime_blocked_contract_gap"]
    assert blocked


def test_lifecycle_bucket_discovery_rejects_real_preapply_primary_ev_claim():
    bucket_id = "scale_in:blocker_reason:pnl_out_of_range_0_32"
    payload = _ai_hybrid_taxonomy_response(bucket_id)
    payload["comparative_reviews"][0][
        "comparison_summary"
    ] = "Use preapply_real primary_ev and merge_real_pnl_with_sim because one-share was profitable."

    status, _, warnings = mod._parse_ai_review_response(payload)

    assert status == "parse_rejected"
    assert f"ai_review_selected_evidence_authority_violation:{bucket_id}" in warnings


def test_lifecycle_bucket_discovery_rejects_legacy_ai_response_without_dual_taxonomy_fields(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_legacy_ai_response_without_dual_taxonomy_fields(),
    )

    assert report["summary"]["ai_two_pass_review_status"] == "parse_rejected"
    assert "ai_review_ai_tier2_proposals_invalid" in report["warnings"]
    assert "ai_review_comparative_reviews_invalid" in report["warnings"]
    assert report["summary"]["live_auto_apply_ready_count"] == 0


def test_lifecycle_bucket_discovery_applies_explicit_contract_ai_block_for_live_candidate(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_block_response(
            "env mapping and post-apply attribution contract are missing",
            bucket_id="scale_in:arm:pyramid",
        ),
    )

    blocked = [
        item
        for item in report["surfaced_candidates"]
        if item.get("bucket_id") == "scale_in:arm:pyramid"
        and item["classification_state"] == "runtime_blocked_contract_gap"
    ]
    assert blocked
    assert report["summary"]["live_auto_apply_ready_count"] == 1


def test_lifecycle_bucket_discovery_surfaces_source_contract_drift(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    report_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    (report_dir / "lifecycle_bucket_discovery_2026-05-21.json").write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "source_contract": {
                    "schema_version": "lifecycle_source_contract_snapshot_v1",
                    "source_keys": ["removed_source"],
                    "sections": {
                        "entry_bucket_attribution": {
                            "bucket_fields": ["bucket_type", "bucket_key", "removed_field"],
                            "bucket_types": ["combo_entry_spot"],
                            "dimension_keys": ["score"],
                        }
                    },
                    "policy_fields": [],
                },
            }
        ),
        encoding="utf-8",
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_keep_response(),
    )

    assert report["summary"]["source_contract_status"] == "fail"
    assert report["source_contract_changes"]
    drift = [
        item
        for item in report["surfaced_candidates"]
        if item["stage"] == "source_contract" and item["classification_state"] == "code_patch_required"
    ]
    assert drift


def test_lifecycle_bucket_discovery_does_not_treat_empty_declared_section_as_contract_removal(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    report_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    (report_dir / "lifecycle_bucket_discovery_2026-05-21.json").write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "source_contract": {
                    "schema_version": "lifecycle_source_contract_snapshot_v1",
                    "source_keys": [],
                    "sections": {
                        "overnight_bucket_attribution": {
                            "present": True,
                            "bucket_count": 21,
                            "bucket_fields": ["bucket_type", "bucket_key", "next_day_mfe_pct"],
                            "bucket_types": ["combo_overnight_decision"],
                            "dimension_keys": ["action"],
                        }
                    },
                    "policy_fields": [],
                },
            }
        ),
        encoding="utf-8",
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_keep_response(),
    )

    assert report["summary"]["source_contract_status"] == "pass"
    assert report["source_contract_changes"] == []


def test_lifecycle_bucket_discovery_openai_review_uses_tier2_schema_and_english_prompt(monkeypatch):
    captured = {}

    class _FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text=json.dumps(_ai_keep_response()), usage=SimpleNamespace())

    class _FakeOpenAI:
        def __init__(self, api_key, timeout=None):
            captured["client_timeout"] = timeout
            self.api_key = api_key
            self.timeout = timeout
            self.responses = _FakeResponses()

    monkeypatch.setattr("src.engine.daily_threshold_cycle_report._load_threshold_ai_openai_keys", lambda: [("OPENAI_API_KEY", "key")])
    monkeypatch.setattr("openai.OpenAI", _FakeOpenAI)

    raw, status = mod._call_openai_ai_review(
        {"surfaced_candidates": [{"label": "수급"}]},
        shard_id="sim_policy_review",
    )

    assert json.loads(raw)["schema_version"] == 1
    assert status["model"] == mod.AI_REVIEW_SOURCE_ONLY_MODEL
    assert status["reasoning_effort"] == mod.AI_REVIEW_SOURCE_ONLY_REASONING_EFFORT
    assert captured["model"] == mod.AI_REVIEW_SOURCE_ONLY_MODEL
    assert captured["reasoning"]["effort"] == mod.AI_REVIEW_SOURCE_ONLY_REASONING_EFFORT
    assert captured["client_timeout"] == mod.AI_REVIEW_TIMEOUT_SEC
    assert captured["timeout"] == mod.AI_REVIEW_TIMEOUT_SEC
    assert captured["text"]["format"]["name"] == mod.AI_REVIEW_SCHEMA_NAME
    assert captured["text"]["format"]["strict"] is True
    assert "AI Tier2" in captured["instructions"]
    assert "\\uc218\\uae09" in captured["input"]
    assert not any("\uac00" <= char <= "\ud7a3" for char in captured["instructions"])
    assert not any("\uac00" <= char <= "\ud7a3" for char in captured["input"])


def test_lifecycle_bucket_discovery_ai_context_is_bounded():
    report = {
        "date": "2026-05-27",
        "summary": {},
        "surfaced_candidates": [
            {
                "bucket_id": f"bucket-{index}",
                "stage": "entry",
                "bucket_type": "combo",
                "bucket_key": "score=score_66_69",
                "normalized_metrics": {"huge": "x" * 5000},
                "deterministic_proposal": {"huge": "y" * 5000},
                "evidence_authority_contract": {"huge": "z" * 5000},
            }
            for index in range(mod.AI_REVIEW_MAX_CANDIDATES + 5)
        ],
    }

    context = mod._build_ai_review_context(report)
    raw = json.dumps(context, ensure_ascii=True, default=str)

    assert len(context["surfaced_candidates"]) == mod.AI_REVIEW_MAX_CANDIDATES
    assert "truncated" in raw
    assert len(raw) < 80_000


def test_lifecycle_bucket_discovery_ai_shards_prioritize_and_dedupe():
    report = {
        "date": "2026-05-27",
        "summary": {},
        "surfaced_candidates": [
            {
                "bucket_id": "live-1",
                "classification_state": "live_auto_apply_ready",
                "joined_sample": 1,
                "source_quality_adjusted_ev_pct": 1.1,
            },
            {
                "bucket_id": "sim-1",
                "classification_state": "sim_auto_approved",
                "joined_sample": 50,
                "source_quality_adjusted_ev_pct": 2.0,
            },
            {
                "bucket_id": "gap-1",
                "classification_state": "code_patch_required",
                "stage": "source_contract",
            },
            {
                "bucket_id": "new-1",
                "classification_state": "new_bucket_candidate",
                "joined_sample": 100,
                "source_quality_adjusted_ev_pct": -3.0,
            },
        ],
    }

    shards = mod._build_ai_review_shards(report)
    by_id = {item["shard_id"]: item for item in shards}

    assert by_id["live_contract_review"]["candidate_ids"] == ["live-1"]
    assert by_id["sim_policy_review"]["candidate_ids"] == ["sim-1"]
    assert by_id["gap_workorder_review"]["candidate_ids"] == ["gap-1"]
    assert by_id["taxonomy_discovery_review"]["candidate_ids"] == ["new-1"]
    assert all(item["context_chars"] <= mod.AI_REVIEW_SHARD_CONTEXT_BUDGET_CHARS for item in shards)


def test_lifecycle_bucket_discovery_shard_failures_only_block_live_targets():
    candidates = [
        {
            "bucket_id": "live-1",
            "classification_state": "live_auto_apply_ready",
            "live_auto_apply_family": mod.ENTRY_LIVE_AUTO_FAMILY,
            "deterministic_proposal": {},
        },
        {
            "bucket_id": "sim-1",
            "classification_state": "sim_auto_approved",
            "deterministic_proposal": {},
        },
        {
            "bucket_id": "new-1",
            "classification_state": "new_bucket_candidate",
            "deterministic_proposal": {},
        },
    ]
    warnings = []

    after_sim_timeout = mod._apply_ai_review(
        candidates,
        ai_status="timeout",
        ai_payload={},
        warnings=warnings,
        reviewed_bucket_ids={"sim-1"},
        fail_closed_live=False,
    )
    by_id = {item["bucket_id"]: item for item in after_sim_timeout}
    assert by_id["live-1"]["classification_state"] == "live_auto_apply_ready"
    assert by_id["sim-1"]["classification_state"] == "sim_auto_approved"
    assert by_id["sim-1"]["ai_review_coverage"] == "reviewed"
    assert by_id["new-1"]["ai_review_coverage"] == "unreviewed"

    after_live_timeout = mod._apply_ai_review(
        after_sim_timeout,
        ai_status="timeout",
        ai_payload={},
        warnings=warnings,
        reviewed_bucket_ids={"live-1"},
        fail_closed_live=True,
    )
    by_id = {item["bucket_id"]: item for item in after_live_timeout}
    assert by_id["live-1"]["classification_state"] == "runtime_blocked_contract_gap"
    assert by_id["live-1"]["ai_tier2_blocked_reason"] == "ai_tier2_validation_not_parsed:timeout"
    assert by_id["sim-1"]["classification_state"] == "sim_auto_approved"
