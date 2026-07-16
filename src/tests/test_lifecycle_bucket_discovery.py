import json
from types import SimpleNamespace

from src.engine import lifecycle_bucket_discovery as mod
from src.engine import lifecycle_decision_matrix as ldm_mod
from src.engine.lifecycle.bucket_taxonomy import normalize_lifecycle_bucket


def _ai_keep_response():
    return {
        "schema_version": 1,
        "interpretation": {
            "bucket_reviews": [],
            "source_contract_review": {
                "status": "pass",
                "changes": [],
                "reason": "contract stable",
            },
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
            "source_contract_review": {
                "status": "pass",
                "changes": [],
                "reason": "contract stable",
            },
        },
        "audit": {
            "status": "correction_required",
            "issues": [reason],
            "reason": reason,
        },
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
            "source_contract_review": {
                "status": "pass",
                "changes": [],
                "reason": "contract stable",
            },
        },
        "audit": {
            "status": "pass",
            "issues": [],
            "reason": "dual proposal comparison accepted",
        },
        "ai_tier2_proposals": [
            {
                "bucket_id": bucket_id,
                "proposal_decision": "create_new_dimension",
                "recommended_canonical_bucket": "scale_in:blocker_reason:pnl_out_of_range",
                "recommended_metric_or_dimension": [
                    "pnl_delta_pct",
                    "pnl_delta_pct_bucket",
                ],
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
                "recommended_metric_or_dimension": [
                    "pnl_delta_pct",
                    "pnl_delta_pct_bucket",
                ],
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
            "source_contract_review": {
                "status": "pass",
                "changes": [],
                "reason": "legacy schema",
            },
        },
        "audit": {"status": "pass", "issues": [], "reason": "legacy response"},
        "final_conclusions": [],
    }


def test_active_sim_priority_seed_uses_observable_prefix_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    report = {
        "date": "2026-06-01",
        "parent_bucket_summaries": [
            {
                "source_parent_bucket_id": "parent_positive",
                "parent_source_quality_adjusted_ev_pct": 2.5685,
                "complete_flow_count": 1,
                "parent_joined_sample": 1,
                "parent_granularity_floor_passed": True,
                "dimension_filters": {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_blocked_ai_score",
                    "submit_quality_parent": "submit_revalidation_ok",
                    "exit_outcome_parent": "exit_missed_upside",
                    "major_holding_parent": "holding_whipsaw_recovery",
                    "scale_in_parent": "scale_in_absent",
                },
            },
            {
                "source_parent_bucket_id": "parent_nonpositive",
                "parent_source_quality_adjusted_ev_pct": 0.0,
                "complete_flow_count": 3,
                "parent_joined_sample": 3,
                "parent_granularity_floor_passed": True,
                "dimension_filters": {
                    "entry_score_parent": "score_mid_recovery",
                    "entry_source_parent": "entry_source_action_decision",
                },
            },
        ],
    }

    seeds = mod._build_active_sim_priority_seeds(report)

    active = next(
        seed for seed in seeds if seed["source_parent_bucket_id"] == "parent_positive"
    )
    assert active["status"] == "active"
    assert active["active_seed_id"].startswith("active_seed_")
    assert active["observable_prefix"] == {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_blocked_ai_score",
        "submit_quality_parent": "submit_revalidation_ok",
    }
    assert active["target_validation_parent_dimensions"] == {
        "exit_outcome_parent": "exit_missed_upside",
        "major_holding_parent": "holding_whipsaw_recovery",
        "scale_in_parent": "scale_in_absent",
    }
    plan = active["positive_ev_stage_sampling_plan"]
    assert plan["sampling_scope"] == "positive_ev_parent_stage_completion"
    assert plan["runtime_match_fields"] == active["observable_prefix"]
    assert "exit_outcome_parent" in plan["runtime_match_forbidden_fields"]
    assert {item["stage"] for item in plan["stage_targets"]} == {
        "entry",
        "submit",
        "holding",
        "exit",
        "scale_in",
    }
    assert plan["actual_order_submitted"] is False
    assert plan["broker_order_forbidden"] is True
    assert (
        active["stage_counterfactual_variant_plan"]["schema_version"]
        == "stage_counterfactual_variant_plan_v1"
    )
    assert len(active["stage_counterfactual_variant_plan"]["variants"]) == 5
    assert active["actual_order_submitted"] is False
    assert active["broker_order_forbidden"] is True
    cooldown = next(
        seed
        for seed in seeds
        if seed["source_parent_bucket_id"] == "parent_nonpositive"
    )
    assert cooldown["status"] == "cooldown"


def test_active_sim_priority_dedupes_duplicate_active_observable_prefix(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    shared_dimensions = {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_wait6579",
        "exit_outcome_parent": "exit_missed_upside",
    }
    report = {
        "date": "2026-06-01",
        "parent_bucket_summaries": [
            {
                "source_parent_bucket_id": "parent_lower_ev",
                "parent_source_quality_adjusted_ev_pct": 0.8,
                "complete_flow_count": 3,
                "parent_joined_sample": 20,
                "parent_granularity_floor_passed": True,
                "dimension_filters": shared_dimensions,
            },
            {
                "source_parent_bucket_id": "parent_higher_ev",
                "parent_source_quality_adjusted_ev_pct": 1.2,
                "complete_flow_count": 1,
                "parent_joined_sample": 10,
                "parent_granularity_floor_passed": True,
                "dimension_filters": {
                    **shared_dimensions,
                    "major_holding_parent": "holding_active_decision",
                },
            },
        ],
    }

    seeds = mod._build_active_sim_priority_seeds(report)

    active = [seed for seed in seeds if seed["status"] == "active"]
    cooldown = [seed for seed in seeds if seed["status"] == "cooldown"]
    assert [seed["source_parent_bucket_id"] for seed in active] == ["parent_higher_ev"]
    assert [seed["source_parent_bucket_id"] for seed in cooldown] == ["parent_lower_ev"]
    assert active[0]["active_observable_prefix_dedup_state"] == "winner"
    assert active[0]["active_observable_prefix_duplicate_count"] == 2
    assert cooldown[0]["active_observable_prefix_dedup_state"] == "suppressed_duplicate"
    assert (
        cooldown[0]["active_collection_reason"]
        == "duplicate_observable_prefix_suppressed"
    )
    assert (
        cooldown[0]["source_quality_status"] == "observable_prefix_duplicate_suppressed"
    )
    assert cooldown[0]["targeted_sim_quota"]["needs_revisit_sample"] is False
    assert cooldown[0]["runtime_effect"] is False
    assert cooldown[0]["allowed_runtime_apply"] is False


def test_ldm_refinement_pressure_is_consumed_without_hypothesis_seed_fragmentation(
    tmp_path, monkeypatch
):
    refinement_dir = tmp_path / "ldm_refinement"
    refinement_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REFINEMENT_REPORT_DIR", refinement_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", tmp_path / "catalog")
    monkeypatch.setattr(
        mod, "_load_previous_active_sim_priority_seeds", lambda target_date: {}
    )
    refinement_dir.joinpath(
        "ldm_hypothesis_parent_refinement_2026-06-01.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": "ldm_hypothesis_parent_refinement_v1",
                "consumer": "lifecycle_bucket_discovery",
                "date": "2026-06-01",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "refinement_inputs": [
                    {
                        "refinement_input_id": "ref_input_1",
                        "soft_hypothesis_id": "ldm_hypothesis_direct_seed_forbidden",
                        "classification": "parent_conflict",
                        "source_parent_bucket_ids": ["parent_positive"],
                        "match_count": 5,
                        "refinement_pressure_score": 3.2,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "consumption_required": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = {
        "date": "2026-06-01",
        "parent_bucket_summaries": [
            {
                "source_parent_bucket_id": "parent_positive",
                "parent_source_quality_adjusted_ev_pct": 2.5,
                "complete_flow_count": 2,
                "parent_joined_sample": 2,
                "parent_granularity_floor_passed": True,
                "dimension_filters": {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_blocked_ai_score",
                },
            }
        ],
    }
    summary = {}

    mod._apply_ldm_refinement_pressure(report, summary)
    seeds = mod._build_active_sim_priority_seeds(report)

    ledger = report["ldm_refinement_pressure_consumption"]
    assert ledger["status"] == "pass"
    assert ledger["input_count"] == 1
    assert ledger["consumed_count"] == 1
    assert (
        ledger["entries"][0]["closure_status"] == "parent_refinement_candidate_created"
    )
    assert report["parent_bucket_summaries"][0]["ldm_refinement_pressure"][0][
        "soft_hypothesis_id"
    ] == ("ldm_hypothesis_direct_seed_forbidden")
    assert seeds[0]["active_seed_id"].startswith("active_seed_")
    assert seeds[0]["active_seed_id"] != "ldm_hypothesis_direct_seed_forbidden"
    assert seeds[0]["source_parent_bucket_id"] == "parent_positive"
    assert seeds[0]["ldm_refinement_pressure_summary"]["input_count"] == 1


def test_ldm_refinement_pressure_preserves_derived_contract_drift_provenance(
    tmp_path, monkeypatch
):
    refinement_dir = tmp_path / "ldm_refinement"
    refinement_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REFINEMENT_REPORT_DIR", refinement_dir)
    refinement_dir.joinpath(
        "ldm_hypothesis_parent_refinement_2026-06-01.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": "ldm_hypothesis_parent_refinement_v1",
                "consumer": "lifecycle_bucket_discovery",
                "date": "2026-06-01",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "refinement_inputs": [
                    {
                        "refinement_input_id": "ref_input_derived",
                        "soft_hypothesis_id": "ldm_hypothesis_derived",
                        "classification": "parent_support",
                        "source_parent_bucket_ids": ["parent_positive"],
                        "match_count": 7,
                        "runtime_match_count": 0,
                        "derived_match_count": 7,
                        "source_match_origin": "derived_contract_drift_recompute",
                        "derived_from_contract_drift": True,
                        "raw_event_mutated": False,
                        "refinement_pressure_score": 2.5,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "consumption_required": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = {
        "date": "2026-06-01",
        "parent_bucket_summaries": [
            {
                "source_parent_bucket_id": "parent_positive",
                "parent_source_quality_adjusted_ev_pct": 2.5,
                "complete_flow_count": 2,
                "parent_joined_sample": 2,
                "parent_granularity_floor_passed": True,
                "dimension_filters": {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_blocked_ai_score",
                },
            }
        ],
    }
    summary = {}

    mod._apply_ldm_refinement_pressure(report, summary)

    ledger_entry = report["ldm_refinement_pressure_consumption"]["entries"][0]
    parent_pressure = report["parent_bucket_summaries"][0]["ldm_refinement_pressure"][0]
    assert ledger_entry["source_match_origin"] == "derived_contract_drift_recompute"
    assert ledger_entry["derived_from_contract_drift"] is True
    assert ledger_entry["raw_event_mutated"] is False
    assert ledger_entry["runtime_effect"] is False
    assert ledger_entry["allowed_runtime_apply"] is False
    assert ledger_entry["actual_order_submitted"] is False
    assert ledger_entry["broker_order_forbidden"] is True
    assert parent_pressure["derived_from_contract_drift"] is True
    assert parent_pressure["runtime_effect"] is False
    assert parent_pressure["allowed_runtime_apply"] is False


def test_ldm_refinement_pressure_uses_target_date_for_rolling_output_key(
    tmp_path, monkeypatch
):
    refinement_dir = tmp_path / "ldm_refinement"
    refinement_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REFINEMENT_REPORT_DIR", refinement_dir)
    refinement_dir.joinpath(
        "ldm_hypothesis_parent_refinement_2026-06-01.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": "ldm_hypothesis_parent_refinement_v1",
                "consumer": "lifecycle_bucket_discovery",
                "date": "2026-06-01",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "refinement_inputs": [
                    {
                        "refinement_input_id": "ref_input_rolling",
                        "soft_hypothesis_id": "ldm_hypothesis_rolling",
                        "classification": "taxonomy_gap_candidate",
                        "gap_reason": "parent_not_found",
                        "match_count": 5,
                        "refinement_pressure_score": 2.1,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "consumption_required": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = {
        "date": "2026-06-01_rolling5d",
        "target_date": "2026-06-01",
        "parent_bucket_summaries": [],
    }
    summary = {}

    mod._apply_ldm_refinement_pressure(report, summary)

    ledger = report["ldm_refinement_pressure_consumption"]
    assert ledger["status"] == "pass"
    assert ledger["source_artifact"].endswith(
        "ldm_hypothesis_parent_refinement_2026-06-01.json"
    )
    assert ledger["input_count"] == 1
    assert ledger["consumed_count"] == 1
    assert summary["ldm_refinement_pressure_input_count"] == 1


def test_ldm_refinement_pressure_rejects_invalid_artifact_contract(
    tmp_path, monkeypatch
):
    refinement_dir = tmp_path / "ldm_refinement"
    refinement_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REFINEMENT_REPORT_DIR", refinement_dir)
    refinement_dir.joinpath(
        "ldm_hypothesis_parent_refinement_2026-06-01.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": "wrong_schema",
                "date": "2026-05-31",
                "consumer": "wrong_consumer",
                "runtime_effect": True,
                "refinement_inputs": [
                    {
                        "refinement_input_id": "ref_input_1",
                        "soft_hypothesis_id": "ldm_hypothesis_invalid",
                        "classification": "parent_support",
                        "source_parent_bucket_ids": ["parent_positive"],
                        "match_count": 5,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "consumption_required": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = {
        "date": "2026-06-01",
        "parent_bucket_summaries": [{"source_parent_bucket_id": "parent_positive"}],
    }
    summary = {}

    mod._apply_ldm_refinement_pressure(report, summary)

    ledger = report["ldm_refinement_pressure_consumption"]
    assert ledger["status"] == "fail"
    assert ledger["input_count"] == 1
    assert ledger["consumed_count"] == 0
    assert "ldm_refinement_schema_version_invalid" in ledger["contract_issues"]
    assert "ldm_refinement_date_mismatch" in ledger["contract_issues"]
    assert "ldm_refinement_consumer_mismatch" in ledger["contract_issues"]
    assert "ldm_refinement_runtime_effect_contract_invalid" in ledger["contract_issues"]


def test_ldm_refinement_parent_match_requires_more_than_single_feature(
    tmp_path, monkeypatch
):
    refinement_dir = tmp_path / "ldm_refinement"
    refinement_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REFINEMENT_REPORT_DIR", refinement_dir)
    refinement_dir.joinpath(
        "ldm_hypothesis_parent_refinement_2026-06-01.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": "ldm_hypothesis_parent_refinement_v1",
                "consumer": "lifecycle_bucket_discovery",
                "date": "2026-06-01",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "refinement_inputs": [
                    {
                        "refinement_input_id": "ref_input_1",
                        "soft_hypothesis_id": "ldm_hypothesis_single_feature",
                        "classification": "taxonomy_gap_candidate",
                        "gap_reason": "parent_not_found",
                        "runtime_observable_features": {
                            "entry_score_parent": "score_watch_recovery"
                        },
                        "match_count": 5,
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "consumption_required": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = {
        "date": "2026-06-01",
        "parent_bucket_summaries": [
            {
                "source_parent_bucket_id": "parent_positive",
                "dimension_filters": {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_blocked_ai_score",
                },
            }
        ],
    }
    summary = {}

    mod._apply_ldm_refinement_pressure(report, summary)

    entry = report["ldm_refinement_pressure_consumption"]["entries"][0]
    assert entry["matched_parent_ids"] == []
    assert entry["closure_status"] == "new_parent_candidate_created"


def test_ldm_refinement_repeated_diagnosis_forces_budget_cap_without_seed_fragmentation(
    tmp_path, monkeypatch
):
    refinement_dir = tmp_path / "ldm_refinement"
    refinement_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REFINEMENT_REPORT_DIR", refinement_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    refinement_dir.joinpath(
        "ldm_hypothesis_parent_refinement_2026-06-01.json"
    ).write_text(
        json.dumps(
            {
                "schema_version": "ldm_hypothesis_parent_refinement_v1",
                "consumer": "lifecycle_bucket_discovery",
                "date": "2026-06-01",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "refinement_inputs": [
                    {
                        "refinement_input_id": "ref_input_repeated",
                        "soft_hypothesis_id": "ldm_hypothesis_repeated",
                        "classification": "parent_support",
                        "contrary_sample_need": True,
                        "match_count": 10,
                        "retry_count": 2,
                        "recommended_closure_bias": "rare_observation_only_budget_capped",
                        "diagnosed_status": "runtime_match_zero_or_low",
                        "diagnosis_reason": "repeated_contrast_gap_with_low_or_fragile_runtime_coverage",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "consumption_required": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    report = {"date": "2026-06-01", "parent_bucket_summaries": []}
    summary = {}

    mod._apply_ldm_refinement_pressure(report, summary)
    seeds = mod._build_active_sim_priority_seeds(report)

    ledger = report["ldm_refinement_pressure_consumption"]
    assert (
        ledger["entries"][0]["closure_status"] == "rare_observation_only_budget_capped"
    )
    assert ledger["entries"][0]["diagnosed_status"] == "runtime_match_zero_or_low"
    assert seeds == []


def test_active_sim_priority_seed_status_uses_two_day_cooldown_and_five_day_retire(
    tmp_path, monkeypatch
):
    previous_seed = {
        "active_seed_id": "active_seed_previous",
        "source_parent_bucket_id": "parent_was_positive",
        "status": "active",
        "observable_prefix": {
            "entry_score_parent": "score_watch_recovery",
            "entry_source_parent": "entry_source_blocked_ai_score",
        },
        "consecutive_fail_count": 0,
        "consecutive_missing_count": 0,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    tmp_path.joinpath("lifecycle_bucket_discovery_2026-05-31.json").write_text(
        json.dumps({"active_sim_priority_seeds": [previous_seed]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)

    first_fail = mod._build_active_sim_priority_seeds(
        {
            "date": "2026-06-01",
            "parent_bucket_summaries": [
                {
                    "source_parent_bucket_id": "parent_was_positive",
                    "parent_source_quality_adjusted_ev_pct": -0.1,
                    "complete_flow_count": 1,
                    "parent_granularity_floor_passed": True,
                    "dimension_filters": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_blocked_ai_score",
                    },
                }
            ],
        }
    )[0]

    assert first_fail["status"] == "cooldown"
    assert (
        first_fail["source_quality_status"] == "source_quality_or_granularity_blocked"
    )
    assert first_fail["active_grace_blocked_reason"] == "nonpositive_ev"
    assert first_fail["consecutive_fail_count"] == 1

    previous_seed["consecutive_fail_count"] = 1
    tmp_path.joinpath("lifecycle_bucket_discovery_2026-05-31.json").write_text(
        json.dumps({"active_sim_priority_seeds": [previous_seed]}),
        encoding="utf-8",
    )
    second_fail = mod._build_active_sim_priority_seeds(
        {
            "date": "2026-06-01",
            "parent_bucket_summaries": [
                {
                    "source_parent_bucket_id": "parent_was_positive",
                    "parent_source_quality_adjusted_ev_pct": -0.1,
                    "complete_flow_count": 1,
                    "parent_granularity_floor_passed": True,
                    "dimension_filters": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_blocked_ai_score",
                    },
                }
            ],
        }
    )[0]
    assert second_fail["status"] == "cooldown"

    previous_seed["consecutive_missing_count"] = 4
    previous_seed["consecutive_fail_count"] = 0
    tmp_path.joinpath("lifecycle_bucket_discovery_2026-05-31.json").write_text(
        json.dumps({"active_sim_priority_seeds": [previous_seed]}),
        encoding="utf-8",
    )
    missing = mod._build_active_sim_priority_seeds(
        {"date": "2026-06-01", "parent_bucket_summaries": []}
    )[0]
    assert missing["status"] == "retired"
    assert missing["retired_reason"] == "consecutive_missing"

    previous_seed["status"] = "active"
    previous_seed["consecutive_fail_count"] = 4
    previous_seed["consecutive_missing_count"] = 0
    tmp_path.joinpath("lifecycle_bucket_discovery_2026-05-31.json").write_text(
        json.dumps({"active_sim_priority_seeds": [previous_seed]}),
        encoding="utf-8",
    )
    recovered = mod._build_active_sim_priority_seeds(
        {
            "date": "2026-06-01",
            "parent_bucket_summaries": [
                {
                    "source_parent_bucket_id": "parent_was_positive",
                    "parent_source_quality_adjusted_ev_pct": 1.1,
                    "complete_flow_count": 1,
                    "parent_granularity_floor_passed": True,
                    "dimension_filters": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_blocked_ai_score",
                    },
                }
            ],
        }
    )[0]
    assert recovered["status"] == "active"
    assert recovered["consecutive_fail_count"] == 0

    tmp_path.joinpath("lifecycle_bucket_discovery_2026-05-31.json").write_text(
        json.dumps({"active_sim_priority_seeds": [recovered]}),
        encoding="utf-8",
    )
    fail_after_recovery = mod._build_active_sim_priority_seeds(
        {
            "date": "2026-06-01",
            "parent_bucket_summaries": [
                {
                    "source_parent_bucket_id": "parent_was_positive",
                    "parent_source_quality_adjusted_ev_pct": -0.1,
                    "complete_flow_count": 1,
                    "parent_granularity_floor_passed": True,
                    "dimension_filters": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_blocked_ai_score",
                    },
                }
            ],
        }
    )[0]
    assert fail_after_recovery["status"] == "cooldown"
    assert fail_after_recovery["active_grace_blocked_reason"] == "nonpositive_ev"
    assert fail_after_recovery["consecutive_fail_count"] == 1

    recovered["status"] = "cooldown"
    recovered["consecutive_missing_count"] = 0
    tmp_path.joinpath("lifecycle_bucket_discovery_2026-05-31.json").write_text(
        json.dumps({"active_sim_priority_seeds": [recovered]}),
        encoding="utf-8",
    )
    cooldown_missing = mod._build_active_sim_priority_seeds(
        {"date": "2026-06-01", "parent_bucket_summaries": []}
    )[0]
    assert cooldown_missing["status"] == "cooldown"
    assert cooldown_missing["consecutive_missing_count"] == 1


def test_active_sim_priority_first_fail_grace_requires_positive_ev(
    tmp_path, monkeypatch
):
    previous_seed = {
        "active_seed_id": "active_seed_previous",
        "source_parent_bucket_id": "parent_was_positive",
        "status": "active",
        "observable_prefix": {
            "entry_score_parent": "score_watch_recovery",
            "entry_source_parent": "entry_source_blocked_ai_score",
        },
        "consecutive_fail_count": 0,
        "consecutive_missing_count": 0,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    tmp_path.joinpath("lifecycle_bucket_discovery_2026-05-31.json").write_text(
        json.dumps({"active_sim_priority_seeds": [previous_seed]}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)

    floor_gap = mod._build_active_sim_priority_seeds(
        {
            "date": "2026-06-01",
            "parent_bucket_summaries": [
                {
                    "source_parent_bucket_id": "parent_was_positive",
                    "parent_source_quality_adjusted_ev_pct": 0.4,
                    "complete_flow_count": 1,
                    "parent_granularity_floor_passed": False,
                    "dimension_filters": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_blocked_ai_score",
                    },
                }
            ],
        }
    )[0]

    assert floor_gap["status"] == "active"
    assert floor_gap["source_quality_status"] == "first_fail_grace"
    assert floor_gap["active_collection_reason"] == "previous_active_first_fail_grace"


def test_active_sim_priority_allows_incomplete_positive_parent_for_collection(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)

    seeds = mod._build_active_sim_priority_seeds(
        {
            "date": "2026-06-01",
            "parent_bucket_summaries": [
                {
                    "source_parent_bucket_id": "parent_positive_incomplete",
                    "parent_source_quality_adjusted_ev_pct": 1.1,
                    "complete_flow_count": 0,
                    "parent_granularity_floor_passed": True,
                    "dimension_filters": {
                        "entry_score_parent": "score_watch_recovery",
                        "entry_source_parent": "entry_source_wait6579",
                        "entry_source_parent_contract_state": "canonical_alias",
                        "entry_source_parent_contract_reason": "alias_of_wait6579_counterfactual",
                        "entry_source_parent_alias_version": "entry_source_parent_alias_v1",
                        "entry_source_parent_consume_data": "True",
                        "entry_source_parent_runtime_effect_allowed": "True",
                    },
                }
            ],
        }
    )

    assert len(seeds) == 1
    seed = seeds[0]
    assert seed["status"] == "active"
    assert seed["complete_flow_count"] == 0
    assert seed["active_collection_reason"] == "positive_ev_parent_needs_sim_collection"
    assert seed["live_conversion_blocked_reason"] == "incomplete_lifecycle_flow"
    assert seed["entry_source_taxonomy_contract"]["contract_state"] == "canonical_alias"
    assert seed["taxonomy_contract_data_consumed"] is True
    assert seed["taxonomy_contract_runtime_effect_allowed"] is True
    assert seed["runtime_effect"] is False
    assert seed["broker_order_forbidden"] is True


def test_entry_source_parent_maps_first_ai_wait_to_wait6579_parent():
    assert mod._entry_source_parent("first_ai_wait") == "entry_source_wait6579"
    assert (
        mod._entry_source_parent(
            "entry:combo_entry_spot:score_score_60_62_source_first_ai_wait_stale_fresh_or_unflagged"
        )
        == "entry_source_wait6579"
    )


def test_entry_source_parent_unknown_axis_is_consumed_as_pending_taxonomy():
    from src.engine.lifecycle.bucket_taxonomy import normalize_entry_source_parent

    normalized = normalize_entry_source_parent("new_observation_axis_v1")

    assert normalized["parent"] == "entry_source_observed_other"
    assert normalized["contract_state"] == "new_axis_pending_taxonomy"
    assert normalized["consume_data"] is True
    assert normalized["runtime_effect_allowed"] is False


def test_lifecycle_parent_dimensions_preserve_pending_taxonomy_metadata():
    dimensions = mod._lifecycle_flow_parent_dimensions(
        {
            "entry_bucket_id": "entry:combo_entry_spot:score_score_60_62_source_new_axis_v1",
            "submit_bucket_id": "submit:combo_submit_quality:submit_missing",
            "holding_bucket_id": "holding:combo_holding_flow:holding_missing",
            "scale_in_bucket_id": "scale_in:none",
            "exit_bucket_id": "exit:combo_exit_result:exit_missing",
        }
    )

    assert dimensions["entry_source_parent"] == "entry_source_observed_other"
    assert (
        dimensions["entry_source_parent_contract_state"] == "new_axis_pending_taxonomy"
    )
    assert dimensions["entry_source_parent_consume_data"] == "True"
    assert dimensions["entry_source_parent_runtime_effect_allowed"] == "False"


def test_active_sim_priority_summary_exposes_collection_and_live_blockers(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(mod, "LIFECYCLE_FLOW_PARENT_TARGET_MIN", 1)
    candidates = [
        mod._candidate_from_bucket(
            "lifecycle_flow",
            {
                "bucket_type": "combo_lifecycle_flow",
                "bucket_key": (
                    "entry=entry:combo_entry_spot:"
                    "score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown|"
                    "submit=submit:combo_submit_quality:submit_missing|"
                    "holding=holding:combo_holding_flow:holding_missing|"
                    "scale_in=scale_in:none|"
                    "exit=exit:combo_exit_result:exit_missing"
                ),
                "sample": 3,
                "joined_sample": 3,
                "complete_flow_count": 0,
                "incomplete_flow_count": 3,
                "source_quality_gate": "pass",
                "source_quality_adjusted_ev_pct": 1.2,
                "recommended_route": "hold_sample",
            },
        )
    ]

    report = mod._finalize_report({"date": "2026-06-01", "summary": {}}, candidates, [])

    assert report["summary"]["active_sim_priority_eligible_count"] == 1
    assert report["summary"]["active_sim_priority_active_seed_count"] == 1
    assert (
        report["summary"][
            "active_sim_priority_live_conversion_blocked_incomplete_flow_count"
        ]
        == 1
    )
    assert report["summary"]["active_sim_priority_targeted_quota_count"] == 1
    assert report["summary"]["active_sim_priority_revisit_sample_need_count"] == 1
    assert report["summary"]["active_sim_priority_targeted_total_share_pct"] == 35
    assert report["summary"]["active_sim_priority_targeted_per_seed_daily_limit"] == 20
    assert report["summary"]["active_sim_priority_sample_goal_per_bucket"] == 10
    assert report["summary"]["active_sim_priority_complete_flow_goal_per_bucket"] == 5
    assert report["summary"]["active_sim_priority_complete_flow_need_count"] == 1
    assert (
        report["summary"]["active_sim_priority_stage_counterfactual_variant_count"] == 5
    )
    assert report["summary"]["positive_parent_count"] == 1
    assert report["summary"]["positive_parent_sample_ready_count"] == 0
    assert report["summary"]["top_positive_parent_buckets"][0]["parent_ev_pct"] == 1.2
    assert report["summary"]["parent_live_auto_apply_ready_count"] == 0
    seed = report["active_sim_priority_seeds"][0]
    assert seed["live_conversion_blocked_reason"] == "incomplete_lifecycle_flow"
    assert (
        seed["targeted_sim_quota"]["quota_policy_version"]
        == "active_parent_seed_targeted_quota_v1"
    )
    assert seed["targeted_sim_quota"]["daily_total_share_pct"] == 35
    assert seed["targeted_sim_quota"]["per_seed_daily_limit"] == 20
    assert seed["targeted_sim_quota"]["sample_goal_per_bucket"] == 10
    assert seed["targeted_sim_quota"]["needs_revisit_sample"] is True
    assert (
        seed["positive_ev_stage_sampling_plan"]["additional_complete_flow_needed"] == 5
    )
    assert (
        seed["positive_ev_stage_sampling_plan"]["runtime_match_fields"]
        == seed["observable_prefix"]
    )
    assert seed["positive_ev_stage_sampling_plan"]["runtime_effect"] is False
    assert seed["stage_counterfactual_variant_plan"]["actual_order_submitted"] is False
    assert seed["targeted_sim_quota"]["actual_order_submitted"] is False
    assert seed["targeted_sim_quota"]["broker_order_forbidden"] is True


def test_active_sim_priority_preserves_conflict_child_stratified_targets(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    report = {
        "date": "2026-06-01",
        "parent_bucket_summaries": [
            {
                "source_parent_bucket_id": "parent_conflict_positive",
                "parent_source_quality_adjusted_ev_pct": 1.4,
                "complete_flow_count": 1,
                "parent_joined_sample": 8,
                "parent_granularity_floor_passed": True,
                "child_conflict_warning": True,
                "dimension_filters": {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_action_decision",
                    "submit_quality_parent": "submit_revalidation_ok",
                    "exit_outcome_parent": "exit_missed_upside",
                    "major_holding_parent": "holding_active_decision",
                    "scale_in_parent": "scale_in_none",
                },
                "conflicting_child_patterns": [
                    {
                        "bucket_id": "child_positive_thin",
                        "bucket_key": "entry=score_watch|holding=wait|exit=missed",
                        "joined_sample": 1,
                        "source_quality_adjusted_ev_pct": 2.3,
                    }
                ],
            }
        ],
    }

    seed = mod._build_active_sim_priority_seeds(report)[0]

    strata = seed["child_conflict_stratified_targets"]
    assert strata["enabled"] is True
    assert strata["sample_goal_per_conflict_child"] == 5
    assert strata["strata"][0]["child_bucket_id"] == "child_positive_thin"
    assert strata["strata"][0]["additional_sample_needed"] == 4
    assert strata["strata"][0]["runtime_consumption_allowed"] is False
    assert strata["strata"][0]["post_observation_validation_only"] is True
    assert strata["runtime_match_fields"] == seed["observable_prefix"]
    assert strata["runtime_consumption_allowed"] is False
    assert strata["actual_order_submitted"] is False
    assert strata["allowed_runtime_apply"] is False


def test_sim_auto_approval_separates_positive_and_nonpositive_ev(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", tmp_path)
    candidates = [
        {
            "bucket_id": "entry:positive",
            "source_bucket_id": "entry:positive:source",
            "classification_state": "sim_auto_approved",
            "stage": "entry",
            "bucket_type": "score_band",
            "source_quality_adjusted_ev_pct": 1.2,
            "sample": 20,
            "joined_sample": 12,
            "source_quality_gate": "pass",
        },
        {
            "bucket_id": "entry:avoid",
            "source_bucket_id": "entry:avoid:source",
            "classification_state": "entry_only_sim_auto_approved",
            "stage": "entry",
            "bucket_type": "chosen_action",
            "source_quality_adjusted_ev_pct": -0.4,
            "sample": 30,
            "joined_sample": 20,
            "source_quality_gate": "pass",
        },
    ]

    report = mod._finalize_report({"date": "2026-06-01", "summary": {}}, candidates, [])
    summary = report["summary"]

    assert summary["sim_auto_positive_ev_count"] == 1
    assert summary["sim_auto_nonpositive_ev_count"] == 1
    assert summary["entry_only_sim_auto_positive_ev_count"] == 0
    assert summary["entry_only_sim_auto_nonpositive_ev_count"] == 1
    assert summary["sim_auto_positive_ev_top"][0]["bucket_id"] == "entry:positive"
    assert summary["sim_auto_nonpositive_ev_top"][0]["bucket_id"] == "entry:avoid"

    mod._write_sim_auto_approval(report)
    payload = json.loads(
        (tmp_path / "lifecycle_bucket_sim_auto_approval_2026-06-01.json").read_text()
    )

    assert payload["approved_bucket_count"] == 2
    assert payload["positive_ev_approved_bucket_count"] == 1
    assert payload["nonpositive_ev_approved_bucket_count"] == 1
    assert payload["positive_ev_bucket_rows"][0]["bucket_id"] == "entry:positive"
    assert payload["nonpositive_ev_bucket_rows"][0]["bucket_id"] == "entry:avoid"


def test_lifecycle_bucket_discovery_summarizes_quiet_gaps():
    report = {
        "ai_two_pass_review": {
            "status": "parsed",
            "shard_count": 5,
            "parsed_shard_count": 2,
            "reviewed_candidate_count": 2,
        }
    }
    candidates = [
        {
            "bucket_id": "lifecycle_flow:conflict-child",
            "source_bucket_id": "lifecycle_flow:conflict-child",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "classification_state": "source_only_keep_collecting",
            "child_conflict_warning": True,
            "exclusion_dimension_candidate": True,
            "source_quality_adjusted_ev_pct": -0.5,
        },
        {
            "bucket_id": "entry:positive-source-only",
            "source_bucket_id": "entry:positive-source-only",
            "stage": "entry",
            "bucket_type": "combo_entry_spot",
            "classification_state": "source_only_keep_collecting",
            "source_quality_gate": "pass",
            "source_quality_adjusted_ev_pct": 1.2,
        },
        {
            "bucket_id": "lifecycle_flow:absorbed",
            "source_bucket_id": "lifecycle_flow:absorbed",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "classification_state": "source_only_keep_collecting",
            "recommended_resolution": "absorbed_into_parent_policy",
        },
    ]

    summary = mod._quiet_gap_summary(report, candidates)

    assert summary["runtime_effect"] is False
    assert summary["allowed_runtime_apply"] is False
    assert summary["decision_authority"] == "source_quality_gap_discovery"
    assert summary["quiet_gap_count"] == 4
    assert summary["parent_conflict_child_count"] == 1
    assert summary["exclusion_dimension_candidate_count"] == 1
    assert summary["positive_source_only_keep_collecting_count"] == 1
    assert summary["absorbed_into_parent_policy_count"] == 1
    assert summary["ai_review_parsed_low_coverage_count"] == 1


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
                        },
                        {
                            "lifecycle_flow_bucket_id": "lifecycle_flow:combo_lifecycle_flow:complete_probe",
                            "bucket_type": "combo_lifecycle_flow",
                            "bucket_key": (
                                "entry=entry:combo_entry_spot:score_60_62|"
                                "submit=submit:combo_submit_quality:thin_ok|"
                                "holding=holding:combo_holding_flow:baseline_hold|"
                                "scale_in=scale_in:none|"
                                "exit=exit:combo_exit_result:tp"
                            ),
                            "sample": 1,
                            "joined_sample": 1,
                            "join_rate": 1.0,
                            "complete_flow_count": 1,
                            "incomplete_flow_count": 0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 0.4,
                            "equal_weight_avg_profit_pct": 0.4,
                            "diagnostic_win_rate": 1.0,
                            "recommended_route": "hold_sample",
                            "metric_scope": "lifecycle_bundle_ev",
                            "entry_bucket_id": "entry:combo_entry_spot:score_60_62",
                            "submit_bucket_id": "submit:combo_submit_quality:thin_ok",
                            "holding_bucket_id": "holding:combo_holding_flow:baseline_hold",
                            "exit_bucket_id": "exit:combo_exit_result:tp",
                            "child_bucket_ids": {
                                "entry": "entry:combo_entry_spot:score_60_62",
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
                            "attribution_key": "sim_record_id:SIM-PROBE",
                            "rollback_guard": "hard_safety_priority_plus_source_quality_and_post_apply_attribution",
                        },
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
                            "scale_in_ev_coverage_state": "v2_ready",
                            "scale_in_ev_label_version": "incremental_counterfactual_v2",
                            "primary_decision_metric": "incremental_notional_ev_pct",
                            "runtime_authority_ready": True,
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
                            "runtime_authority_ready": True,
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


def test_lifecycle_bucket_discovery_summarizes_source_dimension_gaps():
    candidates = [
        {
            "bucket_id": "entry:combo:unknown",
            "source_bucket_id": "entry:combo:unknown",
            "stage": "entry",
            "bucket_type": "combo_entry_spot",
            "classification_state": "source_only_keep_collecting",
            "source_dimension_gap": "unknown_source_dimensions",
            "recommended_resolution": "resolve_unknown_source_dimensions",
            "missing_dimension_keys": ["liquidity_bucket"],
            "unknown_reason_counts": {"missing_source_field": 1},
        },
        {
            "bucket_id": "exit:rule:join-gap",
            "stage": "exit",
            "bucket_type": "exit_rule",
            "classification_state": "source_only_keep_collecting",
            "source_dimension_gap": "unknown_source_dimensions",
            "recommended_resolution": "join_labels_before_bucket_decision",
            "missing_dimension_keys": ["exit"],
            "unknown_reason_counts": {"join_gap": 1},
        },
        {
            "bucket_id": "lifecycle_flow:combo:missing",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "classification_state": "source_only_keep_collecting",
            "source_dimension_gap": "lifecycle_flow_incomplete_stage_contract",
            "recommended_resolution": "explicit_lifecycle_flow_source_only_blocker",
            "missing_lifecycle_flow_stage_keys": ["holding"],
        },
    ]

    summary = mod._source_dimension_gap_summary(candidates)

    assert summary["decision_authority"] == "source_quality_gap_discovery"
    assert summary["runtime_effect"] is False
    assert summary["allowed_runtime_apply"] is False
    assert summary["gap_count"] == 3
    assert summary["actionable_unknown_gap_count"] == 1
    assert summary["rollup_only_gap_count"] == 2
    assert summary["lifecycle_flow_incomplete_stage_contract_count"] == 1
    assert summary["missing_dimension_key_counts"]["liquidity_bucket"] == 1
    assert summary["missing_dimension_key_counts"]["holding"] == 1
    assert summary["join_gap_enrichment"]["runtime_effect"] is False
    assert summary["join_gap_enrichment"]["allowed_runtime_apply"] is False
    assert summary["join_gap_enrichment"]["candidate_count"] == 1
    assert summary["join_gap_enrichment"]["stage_counts"]["exit"] == 1
    assert summary["join_gap_enrichment"]["bucket_type_counts"]["exit_rule"] == 1
    assert summary["join_gap_enrichment"]["candidates"][0]["join_gap_resolution"] == (
        "enrich_bucket_label_or_join_key_before_bucket_decision"
    )


def test_lifecycle_flow_source_dimensions_use_explicit_stage_bucket_ids():
    bucket = {
        "bucket_type": "combo_lifecycle_flow",
        "bucket_key": "entry=unknown|submit=unknown|holding=hold_winner|exit=exit_good",
        "source_quality_gate": "pass",
        "recommended_route": "candidate_recovery_or_relax",
        "complete_flow_count": 3,
        "incomplete_flow_count": 0,
        "joined_sample": 3,
        "source_quality_adjusted_ev_pct": 1.2,
        "entry_bucket_id": "entry:combo_entry_spot:score_66_69",
        "submit_bucket_id": "submit:submit_quality:submitted",
        "holding_bucket_id": "holding:holding_outcome:hold_winner",
        "exit_bucket_id": "exit:exit_outcome:exit_good",
    }

    candidate = mod._candidate_from_bucket("lifecycle_flow", bucket)

    assert (
        candidate["source_dimensions"]["entry"] == "entry:combo_entry_spot:score_66_69"
    )
    assert candidate["source_dimensions"]["submit"] == "submit:submit_quality:submitted"
    assert candidate["missing_dimension_keys"] == []
    assert candidate["source_dimension_gap"] == ""


def test_lifecycle_source_dimension_explicit_unknown_and_flow_tokens_are_not_actionable_gaps():
    exit_candidate = mod._candidate_from_bucket(
        "exit",
        {
            "bucket_type": "exit_outcome",
            "bucket_key": "outcome_unknown",
            "source_quality_gate": "pass",
            "recommended_route": "keep_collecting",
            "joined_sample": 1,
        },
    )

    flow_candidate = mod._candidate_from_bucket(
        "lifecycle_flow",
        {
            "bucket_type": "combo_lifecycle_flow",
            "bucket_key": (
                "entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_"
                "stale_stale_unknown_liquid"
            ),
            "submit_bucket_id": "submit:submit_quality:submitted",
            "holding_bucket_id": "holding:holding_outcome:hold_winner",
            "exit_bucket_id": "exit:exit_outcome:exit_good",
            "source_quality_gate": "pass",
            "recommended_route": "source_only_keep_collecting",
            "joined_sample": 1,
        },
    )

    assert exit_candidate["source_dimension_gap"] == ""
    assert exit_candidate["missing_dimension_keys"] == []
    assert flow_candidate["source_dimensions"]["entry"].startswith(
        "entry_source_token:"
    )
    assert flow_candidate["missing_dimension_keys"] == []
    assert flow_candidate["missing_lifecycle_flow_stage_keys"] == []
    assert flow_candidate["source_dimension_gap"] == ""
    summary = mod._source_dimension_gap_summary([exit_candidate, flow_candidate])
    assert summary["actionable_unknown_gap_count"] == 0


def test_scale_in_ai_score_unknown_keeps_source_quality_blocker_provenance():
    candidate = mod._candidate_from_bucket(
        "scale_in",
        {
            "bucket_type": "ai_score_band",
            "bucket_key": "score_unknown",
            "sample": 167,
            "joined_sample": 4,
            "source_quality_gate": "hold_sample",
            "recommended_route": "hold_sample",
            "unknown_dimension_counts": {"ai_score_band": 1},
            "unknown_reason_counts": {"missing_source_field": 1},
            "source_field_coverage": {
                "ai_score_band": {
                    "source_fields": ["runtime_features.ai_score"],
                    "present_count": 0,
                    "sample_count": 167,
                    "coverage_rate": 0.0,
                }
            },
        },
    )

    assert candidate["source_dimension_gap"] == mod.SCALE_IN_AI_SCORE_SOURCE_MISSING_GAP
    assert (
        candidate["recommended_resolution"]
        == mod.SCALE_IN_AI_SCORE_SOURCE_MISSING_RESOLUTION
    )
    assert candidate["source_dimension_gap_provenance"] == {
        "gap": mod.SCALE_IN_AI_SCORE_SOURCE_MISSING_GAP,
        "resolution": mod.SCALE_IN_AI_SCORE_SOURCE_MISSING_RESOLUTION,
        "source_fields": ["runtime_features.ai_score"],
        "present_count": 0,
        "sample_count": 167,
        "coverage_rate": 0.0,
        "decision_authority": "source_quality_gap_discovery",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    assert candidate["runtime_effect"] is False
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["broker_order_forbidden"] is True

    summary = mod._source_dimension_gap_summary([candidate])
    assert summary["actionable_unknown_gap_count"] == 0
    assert summary["rollup_only_gap_count"] == 1
    assert (
        summary["source_dimension_gap_counts"][mod.SCALE_IN_AI_SCORE_SOURCE_MISSING_GAP]
        == 1
    )
    assert (
        summary["rollup_candidates"][0]["source_dimension_gap_provenance"][
            "sample_count"
        ]
        == 167
    )


def test_scale_in_held_unknown_is_source_only_observation_rollup():
    candidate = mod._candidate_from_bucket(
        "scale_in",
        {
            "bucket_type": "held_bucket",
            "bucket_key": "held_unknown",
            "sample": 12,
            "joined_sample": 0,
            "source_quality_gate": "hold_sample",
            "recommended_route": "hold_sample",
            "unknown_dimension_counts": {"held_bucket": 12},
            "unknown_reason_counts": {"missing_source_field": 12},
        },
    )

    assert candidate["source_dimension_gap"] == ""
    assert candidate["missing_dimension_keys"] == []
    assert (
        candidate["recommended_resolution"]
        == mod.SCALE_IN_HELD_BUCKET_OBSERVATION_RESOLUTION
    )
    assert candidate["runtime_effect"] is False
    assert candidate["allowed_runtime_apply"] is False

    summary = mod._source_dimension_gap_summary([candidate])
    assert summary["actionable_unknown_gap_count"] == 0
    assert summary["rollup_only_gap_count"] == 0


def test_scale_in_source_dimension_unknowns_are_observation_rollups():
    candidates = [
        mod._candidate_from_bucket(
            "scale_in",
            {
                "bucket_type": bucket_type,
                "bucket_key": bucket_key,
                "sample": 1,
                "joined_sample": 0,
                "source_quality_gate": "hold_sample",
                "recommended_route": "hold_sample",
                "unknown_dimension_counts": {bucket_type: 1},
                "unknown_reason_counts": {"missing_source_field": 1},
            },
        )
        for bucket_type, bucket_key in sorted(
            mod.SCALE_IN_SOURCE_DIMENSION_ROLLUP_BUCKETS
        )
    ]

    assert {item["source_dimension_gap"] for item in candidates} == {""}
    assert {item["recommended_resolution"] for item in candidates} == {
        mod.SCALE_IN_SOURCE_DIMENSION_OBSERVATION_RESOLUTION
    }
    assert all(item["runtime_effect"] is False for item in candidates)
    assert all(item["allowed_runtime_apply"] is False for item in candidates)

    summary = mod._source_dimension_gap_summary(candidates)
    assert summary["actionable_unknown_gap_count"] == 0


def test_lifecycle_bucket_discovery_classifies_live_sim_and_new_buckets(
    tmp_path, monkeypatch
):
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

    states = {item["bucket_id"]: item for item in report["candidates"]}
    live = [
        item
        for item in states.values()
        if item["classification_state"] == "live_auto_apply_ready"
    ]
    sim = [
        item
        for item in states.values()
        if item["classification_state"] == "sim_auto_approved"
    ]
    entry_only_sources = [
        item
        for item in report["candidates"]
        if item.get("source_bucket_kind") == "entry_only_source_candidate"
    ]
    assert {item["live_auto_apply_family"] for item in live} == {
        mod.SCALE_IN_LIVE_AUTO_FAMILY
    }
    wait6579 = states[
        "entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown"
    ]
    assert wait6579["classification_state"] == mod.ENTRY_ONLY_BRIDGE_METADATA_STATE
    assert wait6579["review_category"] == "source_only_keep_collecting"
    assert wait6579["review_sub_state"] == "entry_only_bridge_metadata"
    assert wait6579["evidence_grade"] == mod.EVIDENCE_GRADE_2_COUNTERFACTUAL
    assert wait6579["transition_target"] == "entry_dimension_provenance_only"
    assert wait6579["full_real_conversion_allowed"] is False
    assert wait6579["live_auto_apply_family"] is None
    assert wait6579["legacy_contract_known_unknown"] is False
    assert wait6579["source_dimension_gap"] == "unknown_source_dimensions"
    assert (wait6579["auto_promotion_contract"] or {})[
        "deterministic_contract_required"
    ] is False
    assert wait6579["bounded_live_canary_allowed"] is False
    flow_parent = next(
        item
        for item in states.values()
        if item["stage"] == "lifecycle_flow"
        and item.get("entry_bucket_id") == "entry:combo_entry_spot:score_66_69"
    )
    assert flow_parent["classification_state"] == "source_only_keep_collecting"
    assert flow_parent["live_auto_apply_family"] is None
    assert flow_parent["metric_scope"] == "lifecycle_bundle_ev"
    assert flow_parent["policy_bucket_id"].startswith(
        "lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery"
    )
    assert flow_parent["parent_granularity_status"] == "too_broad"
    assert flow_parent["parent_granularity_floor_passed"] is False
    assert flow_parent["parent_live_floor_passed"] is False
    assert flow_parent["parent_joined_sample"] == 22
    assert flow_parent["absorbed_child_count"] == 1
    assert flow_parent["absorbed_child_bucket_ids"] == [flow_parent["bucket_id"]]
    flow_probe = next(
        item
        for item in states.values()
        if item["stage"] == "lifecycle_flow"
        and item["classification_state"] == mod.LIFECYCLE_FLOW_SIM_PROBE_STATE
    )
    assert flow_probe["classification_state"] == mod.LIFECYCLE_FLOW_SIM_PROBE_STATE
    assert flow_probe["review_category"] == "sim_auto_approved"
    assert flow_probe["review_sub_state"] == "lifecycle_flow_sim_probe_candidate"
    assert flow_probe["source_bucket_kind"] == "lifecycle_flow_sim_probe_policy"
    assert flow_probe["live_auto_apply_family"] is None
    assert flow_probe["allowed_runtime_apply"] is False
    assert flow_probe["runtime_effect"] is False
    assert flow_probe["broker_order_forbidden"] is True
    assert (
        flow_probe["decision_authority"]
        == "lifecycle_bucket_discovery_lifecycle_flow_sim_probe"
    )
    assert flow_probe["complete_flow_count"] == 1
    assert flow_probe["incomplete_flow_count"] == 0
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
    assert (
        scale_blocker["canonical_bucket"] == "scale_in:blocker_reason:pnl_out_of_range"
    )
    assert scale_blocker["normalized_metrics"]["pnl_delta_pct"] == 0.32
    assert (
        scale_blocker["deterministic_proposal"]["proposal_decision"]
        == "absorb_as_dimension"
    )
    assert (
        scale_blocker["ai_tier2_comparative_review"]["selected_decision"]
        == "absorb_as_dimension"
    )
    assert report["summary"]["deterministic_proposal_count"] == len(
        report["candidates"]
    )
    assert report["summary"]["absorbed_bucket_count"] >= 1
    assert "canonical_bucket_count" in report["summary"]
    assert report["summary"]["parent_live_auto_apply_ready_count"] == 0
    assert report["summary"]["absorbed_sample_count"] >= 22
    assert sim
    assert entry_only_sources
    assert entry_only_sources[0]["bucket_relation"] == "new_bucket_candidate"
    assert (
        entry_only_sources[0]["classification_state"] == "entry_only_source_candidate"
    )
    assert entry_only_sources[0]["review_category"] == "source_only_keep_collecting"
    assert entry_only_sources[0]["review_sub_state"] == "entry_only_source_candidate"
    assert entry_only_sources[0]["source_bucket_id"]
    assert "recommended_resolution" in entry_only_sources[0]
    assert "source_bucket_kind_counts" in report["summary"]
    assert report["summary"]["review_category_counts"]["sim_auto_approved"] >= len(sim)
    assert (
        report["summary"]["review_sub_state_counts"][
            "lifecycle_flow_sim_probe_candidate"
        ]
        == 1
    )
    assert report["summary"]["human_intervention_required"] is False
    assert report["summary"]["lifecycle_flow_sim_probe_candidate_count"] == 1
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
    catalog = json.loads(
        (catalog_dir / "lifecycle_bucket_catalog_2026-05-22.json").read_text()
    )
    assert (
        catalog["targeted_sim_collection"]["policy_version"]
        == "active_parent_seed_targeted_quota_v1"
    )
    assert catalog["targeted_sim_collection"]["daily_total_share_pct"] == 35
    assert catalog["targeted_sim_collection"]["per_seed_daily_limit"] == 20
    assert catalog["targeted_sim_collection"]["complete_flow_goal_per_bucket"] == 5
    assert catalog["targeted_sim_collection"]["conflict_child_sample_goal"] == 5
    assert (
        catalog["targeted_sim_collection"]["runtime_match_policy"]
        == "observable_prefix_only"
    )
    assert "active_sim_priority_seeds" in catalog
    auto = json.loads(
        (sim_dir / "lifecycle_bucket_sim_auto_approval_2026-05-22.json").read_text()
    )
    assert auto["approved"] is True
    assert auto["broker_order_forbidden"] is True
    assert auto["actual_order_submitted"] is False
    assert auto["runtime_effect"] is False
    assert auto["allowed_runtime_apply"] is False
    assert auto["approved_bucket_count"] == len(auto["approved_bucket_ids"])
    assert auto["approved_bucket_count"] == len(auto["approved_bucket_rows"])
    assert auto["approved_unique_source_bucket_count"] <= auto["approved_bucket_count"]
    assert auto["approved_lifecycle_flow_sim_probe_count"] == 1
    assert auto["approved_state_counts"][mod.LIFECYCLE_FLOW_SIM_PROBE_STATE] == 1
    assert flow_probe["bucket_id"] in auto["approved_bucket_ids"]
    assert (
        auto["targeted_sim_collection"]["policy_version"]
        == "active_parent_seed_targeted_quota_v1"
    )
    assert auto["targeted_sim_collection"]["daily_total_share_pct"] == 35
    assert auto["targeted_sim_collection"]["per_seed_daily_limit"] == 20
    assert auto["targeted_sim_collection"][
        "stage_counterfactual_variant_plan_version"
    ] == ("stage_counterfactual_variant_plan_v1")
    flow_probe_row = next(
        row
        for row in auto["approved_bucket_rows"]
        if row["bucket_id"] == flow_probe["bucket_id"]
    )
    assert flow_probe_row["source_bucket_id"] == flow_probe["source_bucket_id"]
    assert flow_probe_row["complete_flow_count"] == 1
    assert flow_probe_row["incomplete_flow_count"] == 0
    assert (
        auto["approved_evidence_grade_counts"].get(
            mod.EVIDENCE_GRADE_2_COUNTERFACTUAL, 0
        )
        == 0
    )
    assert auto["source_quality_status"] == "pass"


def test_lifecycle_bucket_discovery_assigns_live_family_to_avg_down_arm(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    ldm_path = ldm_dir / "lifecycle_decision_matrix_2026-05-22.json"
    _write_ldm(ldm_path)
    payload = json.loads(ldm_path.read_text(encoding="utf-8"))
    payload["scale_in_bucket_attribution"]["buckets"].append(
        {
            "bucket_type": "arm",
            "bucket_key": "AVG_DOWN",
            "sample": 12,
            "joined_sample": 12,
            "join_rate": 1.0,
            "source_quality_gate": "pass",
            "source_quality_adjusted_ev_pct": -1.4,
            "recommended_route": "candidate_tighten_or_exclude",
            "scale_in_ev_coverage_state": "v2_ready",
            "scale_in_ev_label_version": "incremental_counterfactual_v2",
            "primary_decision_metric": "incremental_notional_ev_pct",
            "runtime_authority_ready": True,
        }
    )
    ldm_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_keep_response(),
    )

    states = {item["bucket_id"]: item for item in report["candidates"]}
    avg_down = states["scale_in:arm:avg_down"]
    assert avg_down["classification_state"] == "live_auto_apply_ready"
    assert avg_down["live_auto_apply_family"] == mod.SCALE_IN_LIVE_AUTO_FAMILY
    assert avg_down["bucket_type"] == "arm"
    assert avg_down["bucket_key"] == "AVG_DOWN"


def test_lifecycle_bucket_discovery_blocks_scale_in_arm_without_v2_coverage(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    ldm_path = ldm_dir / "lifecycle_decision_matrix_2026-05-22.json"
    _write_ldm(ldm_path)
    payload = json.loads(ldm_path.read_text(encoding="utf-8"))
    payload["scale_in_bucket_attribution"]["buckets"].append(
        {
            "bucket_type": "arm",
            "bucket_key": "AVG_DOWN",
            "sample": 12,
            "joined_sample": 12,
            "join_rate": 1.0,
            "source_quality_gate": "pass",
            "source_quality_adjusted_ev_pct": -1.4,
            "recommended_route": "candidate_tighten_or_exclude",
            "runtime_authority_ready": True,
        }
    )
    ldm_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_keep_response(),
    )

    states = {item["bucket_id"]: item for item in report["candidates"]}
    avg_down = states["scale_in:arm:avg_down"]
    assert avg_down["classification_state"] == "source_only_keep_collecting"
    assert avg_down.get("live_auto_apply_family") is None
    assert avg_down["grade_reason"] == "scale_in_incremental_v2_coverage_not_ready"


def test_lifecycle_flow_parent_absorbs_thin_children_for_live_policy(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)

    def _flow_bucket(score, submit, holding, exit_bucket, *, sample, ev, route, sim_id):
        return {
            "lifecycle_flow_bucket_id": f"lifecycle_flow:combo_lifecycle_flow:{sim_id}",
            "bucket_type": "combo_lifecycle_flow",
            "bucket_key": (
                f"entry=entry:combo_entry_spot:{score}|"
                f"submit={submit}|"
                f"holding={holding}|"
                "scale_in=scale_in:none|"
                f"exit={exit_bucket}"
            ),
            "sample": sample,
            "joined_sample": sample,
            "real_joined_sample": sample,
            "real_submitted_count": sample,
            "join_rate": 1.0,
            "complete_flow_count": sample,
            "incomplete_flow_count": 0,
            "source_quality_gate": "pass",
            "source_quality_adjusted_ev_pct": ev,
            "recommended_route": route,
            "metric_scope": "lifecycle_bundle_ev",
            "entry_bucket_id": f"entry:combo_entry_spot:{score}",
            "submit_bucket_id": submit,
            "holding_bucket_id": holding,
            "exit_bucket_id": exit_bucket,
            "child_bucket_ids": {
                "entry": f"entry:combo_entry_spot:{score}",
                "submit": submit,
                "holding": holding,
                "scale_in": [],
                "exit": exit_bucket,
            },
            "stage_contract": {
                "entry": {"contract_state": "present"},
                "submit": {"contract_state": "present"},
                "holding": {"contract_state": "present"},
                "exit": {"contract_state": "present"},
            },
            "attribution_key": f"sim_record_id:{sim_id}",
        }

    flow_buckets = []
    parent_submit = "submit:combo_submit_quality:revalidation_ok"
    parent_holding = "holding:combo_holding_flow:baseline_hold"
    parent_exit = "exit:combo_exit_result:take_profit"
    for score, ev, sim_id in (
        ("score_66_69", 1.4, "SIM-A"),
        ("score_70_74", 1.2, "SIM-B"),
    ):
        flow_buckets.append(
            _flow_bucket(
                score,
                parent_submit,
                parent_holding,
                parent_exit,
                sample=5,
                ev=ev,
                route="candidate_recovery_or_relax",
                sim_id=sim_id,
            )
        )
    score_variants = ["score_lt60", "score_60_62", "score_76_80", "score_90p"]
    submit_variants = [
        "submit:combo_submit_quality:missing",
        "submit:combo_submit_quality:stale_context_or_quote",
        "submit:combo_submit_quality:price_guard_would_block",
        "submit:combo_submit_quality:observed_other",
    ]
    exit_variants = [
        "exit:combo_exit_result:missed_upside",
        "exit:combo_exit_result:soft_stop_loss",
        "exit:combo_exit_result:neutral",
        "exit:combo_exit_result:missing",
        "exit:combo_exit_result:observed_other",
    ]
    sibling_index = 0
    for score in score_variants:
        for submit in submit_variants:
            for exit_bucket in exit_variants:
                if len(flow_buckets) >= 31:
                    break
                sibling_index += 1
                flow_buckets.append(
                    _flow_bucket(
                        score,
                        submit,
                        f"holding:combo_holding_flow:baseline_hold_variant_{sibling_index}",
                        exit_bucket,
                        sample=1,
                        ev=0.2,
                        route="hold_sample",
                        sim_id=f"SIM-SIB-{sibling_index}",
                    )
                )
            if len(flow_buckets) >= 31:
                break
        if len(flow_buckets) >= 31:
            break
    (ldm_dir / "lifecycle_decision_matrix_2026-05-22.json").write_text(
        json.dumps(
            {
                "date": "2026-05-22",
                "lifecycle_flow_bucket_attribution": {"buckets": flow_buckets},
            }
        ),
        encoding="utf-8",
    )

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_keep_response(),
    )

    flow_candidates = [
        item
        for item in report["candidates"]
        if item["stage"] == "lifecycle_flow"
        and item["bucket_type"] == "combo_lifecycle_flow"
    ]
    live = [
        item
        for item in flow_candidates
        if item["classification_state"] == "live_auto_apply_ready"
    ]
    absorbed = [
        item
        for item in flow_candidates
        if item.get("recommended_resolution") == "absorbed_into_parent_live_policy"
    ]
    assert len(live) == 1
    assert len(absorbed) >= 1
    assert live[0]["policy_bucket_id"].startswith(
        "lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery"
    )
    assert live[0]["parent_granularity_status"] == "target_pass"
    assert live[0]["parent_granularity_floor_passed"] is True
    assert live[0]["parent_joined_sample"] == 10
    assert live[0]["parent_source_quality_adjusted_ev_pct"] == 1.3
    assert live[0]["parent_live_floor_passed"] is True
    assert live[0]["child_live_authority_allowed"] is False
    assert live[0]["absorbed_child_count"] == 2
    assert set(live[0]["absorbed_child_bucket_ids"]) == {
        item["bucket_id"]
        for item in flow_candidates
        if item.get("policy_bucket_id") == live[0]["policy_bucket_id"]
    }
    assert live[0]["absorbed_dimensions"]["entry_detail"] == [
        "entry:combo_entry_spot:score_66_69",
        "entry:combo_entry_spot:score_70_74",
    ]
    assert absorbed[0]["recommended_resolution"] == "absorbed_into_parent_live_policy"
    assert report["summary"]["parent_live_auto_apply_ready_count"] == 1
    assert report["summary"]["parent_granularity_status"] == "target_pass"
    assert 30 <= report["summary"]["parent_bucket_count"] <= 60
    assert report["summary"]["absorbed_child_count"] == len(flow_buckets)
    assert report["summary"]["absorbed_sample_count"] == sum(
        item["sample"] for item in flow_buckets
    )


def test_score_family_without_separator_rolls_up_to_parent_group():
    normalized = normalize_lifecycle_bucket(
        stage="entry",
        bucket_type="score_band",
        bucket_key="score65_74_recovery_probe",
        source_dimensions={},
    )

    assert normalized["canonical_bucket"] == "entry:score_band:score_mid_recovery"
    assert normalized["normalized_dimensions"]["score_parent"] == "score_mid_recovery"
    assert (
        normalized["normalized_dimensions"]["bucket_detail"]
        == "score65_74_recovery_probe"
    )
    assert (
        normalized["deterministic_proposal"]["proposal_decision"]
        == "absorb_as_dimension"
    )


def test_score_variants_roll_up_to_expected_parent_groups():
    cases = {
        "score_score_66_69": "score_mid_recovery",
        "score65_74": "score_mid_recovery",
        "score_70p": "score_mid_recovery",
        "score_lt60": "score_low_observation",
    }
    for bucket_key, expected_parent in cases.items():
        normalized = normalize_lifecycle_bucket(
            stage="entry",
            bucket_type="score_band",
            bucket_key=bucket_key,
            source_dimensions={},
        )
        assert normalized["canonical_bucket"] == f"entry:score_band:{expected_parent}"
        assert normalized["normalized_dimensions"]["score_parent"] == expected_parent


def test_lifecycle_flow_parent_rebuild_keeps_synthetic_102_children_in_target_range():
    scores = ["score_lt60", "score_60_62", "score_66_69", "score_76_80"]
    submits = [
        "submit:combo_submit_quality:revalidation_ok",
        "submit:combo_submit_quality:stale_context_or_quote",
        "submit:combo_submit_quality:price_guard_would_block",
    ]
    exits = [
        "exit:combo_exit_result:take_profit",
        "exit:combo_exit_result:missed_upside",
        "exit:combo_exit_result:soft_stop_loss",
    ]
    candidates = []
    for index in range(102):
        score = scores[index % len(scores)]
        submit = submits[(index // len(scores)) % len(submits)]
        exit_bucket = exits[(index // (len(scores) * len(submits))) % len(exits)]
        holding = f"holding:combo_holding_flow:baseline_hold_variant_{index}"
        candidates.append(
            mod._candidate_from_bucket(
                "lifecycle_flow",
                {
                    "bucket_type": "combo_lifecycle_flow",
                    "bucket_key": (
                        f"entry=entry:combo_entry_spot:{score}|"
                        f"submit={submit}|"
                        f"holding={holding}|"
                        "scale_in=scale_in:none|"
                        f"exit={exit_bucket}"
                    ),
                    "sample": 1,
                    "joined_sample": 1,
                    "complete_flow_count": 1,
                    "incomplete_flow_count": 0,
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 0.2,
                    "recommended_route": "hold_sample",
                    "stage_contract": {
                        "entry": {"contract_state": "present"},
                        "submit": {"contract_state": "present"},
                        "holding": {"contract_state": "present"},
                        "exit": {"contract_state": "present"},
                    },
                },
            )
        )

    report = mod._finalize_report({"summary": {}}, candidates, [])

    assert report["summary"]["parent_granularity_status"] == "target_pass"
    assert 30 <= report["summary"]["parent_bucket_count"] <= 60
    assert report["summary"]["selected_parent_level"] == "L1_broad"
    assert report["summary"]["absorbed_child_count"] == 102
    assert report["summary"]["absorbed_sample_count"] == 102
    assert (
        len(report["parent_bucket_summaries"])
        == report["summary"]["parent_bucket_count"]
    )
    first_parent = report["parent_bucket_summaries"][0]
    assert first_parent["parent_bucket_id"] == first_parent["policy_bucket_id"]
    assert (
        first_parent["parent_ev"]
        == first_parent["parent_source_quality_adjusted_ev_pct"]
    )


def test_ai_parent_granularity_review_accepts_only_deterministic_levels():
    valid = {
        **_ai_keep_response(),
        "parent_granularity_reviews": [
            {
                "decision": "prefer_level",
                "preferred_level": "L2_default",
                "reason": "Better parent spread.",
            }
        ],
    }
    status, payload, warnings = mod._parse_ai_review_response(valid)
    assert status == "parsed"
    assert warnings == []
    assert payload["parent_granularity_reviews"][0]["preferred_level"] == "L2_default"

    invalid = {
        **_ai_keep_response(),
        "parent_granularity_reviews": [
            {
                "decision": "prefer_level",
                "preferred_level": "custom_ai_parent",
                "reason": "Invented.",
            }
        ],
    }
    status, _, warnings = mod._parse_ai_review_response(invalid)
    assert status == "parse_rejected"
    assert "ai_review_invalid_parent_granularity_level" in warnings

    items = [
        mod._candidate_from_bucket(
            "lifecycle_flow",
            {
                "bucket_type": "combo_lifecycle_flow",
                "bucket_key": (
                    "entry=entry:combo_entry_spot:score_66_69|"
                    "submit=submit:combo_submit_quality:revalidation_ok|"
                    "holding=holding:combo_holding_flow:baseline_hold|"
                    "scale_in=scale_in:none|"
                    "exit=exit:combo_exit_result:take_profit"
                ),
                "sample": 1,
                "joined_sample": 1,
            },
        )
    ]
    selected, _, metadata = mod._select_parent_level(
        items,
        {
            "ai_two_pass_review": {
                "parent_granularity_reviews": [
                    {
                        "decision": "prefer_level",
                        "preferred_level": "L3_detailed",
                        "reason": "Too narrow.",
                    }
                ]
            }
        },
    )
    assert selected == "L1_broad"
    assert metadata["ai_parent_granularity_choice"]["accepted"] is False


def test_lifecycle_flow_parent_summary_counts_absorption_without_live_policy():
    candidates = []
    for score, ev in (("score_66_69", 0.2), ("score_70_74", -2.0)):
        candidates.append(
            mod._candidate_from_bucket(
                "lifecycle_flow",
                {
                    "bucket_type": "combo_lifecycle_flow",
                    "bucket_key": (
                        f"entry=entry:combo_entry_spot:{score}|"
                        "submit=submit:combo_submit_quality:thin_ok|"
                        "holding=holding:combo_holding_flow:baseline_hold|"
                        "scale_in=scale_in:none|"
                        "exit=exit:combo_exit_result:tp"
                    ),
                    "sample": 5,
                    "joined_sample": 5,
                    "complete_flow_count": 5,
                    "incomplete_flow_count": 0,
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": ev,
                    "recommended_route": "candidate_recovery_or_relax",
                    "stage_contract": {
                        "entry": {"contract_state": "present"},
                        "submit": {"contract_state": "present"},
                        "holding": {"contract_state": "present"},
                        "exit": {"contract_state": "present"},
                    },
                },
            )
        )

    report = mod._finalize_report({"summary": {}}, candidates, [])

    assert report["summary"]["parent_bucket_count"] == 1
    assert report["summary"]["parent_live_auto_apply_ready_count"] == 0
    assert report["summary"]["absorbed_child_count"] == 2
    assert report["summary"]["absorbed_sample_count"] == 10
    assert report["summary"]["child_conflict_warning_count"] == 1


def test_lifecycle_bucket_discovery_ai_final_state_recomputes_runtime_metadata():
    candidates = [
        {
            "bucket_id": "flow-probe-1",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "bucket_key": "entry=entry_a|submit=submit_a|holding=holding_a|exit=exit_a",
            "classification_state": mod.LIFECYCLE_FLOW_SIM_PROBE_STATE,
            "source_bucket_kind": "lifecycle_flow_sim_probe_policy",
            "decision_authority": "lifecycle_bucket_discovery_lifecycle_flow_sim_probe",
            "runtime_effect_after_approval": "lifecycle_flow_sim_probe_policy",
            "live_auto_apply_family": None,
            "allowed_runtime_apply": False,
            "runtime_effect": False,
            "broker_order_forbidden": True,
            "sim_lifecycle_handoff_allowed": True,
            "bounded_live_canary_allowed": False,
            "auto_promotion_contract": {"state": "lifecycle_flow_sim_probe_candidate"},
        }
    ]
    payload = {
        "final_conclusions": [
            {
                "bucket_id": "flow-probe-1",
                "final_bucket_relation": "new_bucket_candidate",
                "final_classification_state": "new_bucket_candidate",
                "final_decision": "revise",
                "reason": "taxonomy needs separate tracking",
            }
        ]
    }

    updated = mod._apply_ai_review(
        candidates,
        ai_status="parsed",
        ai_payload=payload,
        warnings=[],
        reviewed_bucket_ids={"flow-probe-1"},
        fail_closed_live=False,
    )

    row = updated[0]
    assert row["classification_state"] == "new_bucket_candidate"
    assert row["source_bucket_kind"] == "source_only_observation"
    assert row["decision_authority"] == "lifecycle_bucket_discovery_source_quality"
    assert row["runtime_effect_after_approval"] == "none"
    assert row["live_auto_apply_family"] is None
    assert row["allowed_runtime_apply"] is False
    assert row["runtime_effect"] is False
    assert row["broker_order_forbidden"] is True
    assert row["sim_lifecycle_handoff_allowed"] is False
    assert row["bounded_live_canary_allowed"] is False
    assert row["auto_promotion_contract"]["state"] == "source_only"


def test_lifecycle_flow_incomplete_stage_contract_is_explicit_source_only_blocker():
    candidate = mod._candidate_from_bucket(
        "lifecycle_flow",
        {
            "bucket_type": "combo_lifecycle_flow",
            "bucket_key": (
                "entry=entry:combo_entry_spot:score_score_60_62|"
                "submit=submit:missing|holding=holding:missing|scale_in=scale_in:none|exit=exit:missing"
            ),
            "source_quality_gate": "pass",
            "recommended_route": "candidate_recovery_or_relax",
            "sample": 12,
            "joined_sample": 6,
            "entry_bucket_id": "entry:combo_entry_spot:score_score_60_62",
            "submit_bucket_id": "submit:missing",
            "holding_bucket_id": "holding:missing",
            "exit_bucket_id": "exit:missing",
            "stage_contract": {
                "entry": "present",
                "submit": "missing",
                "holding": "missing",
                "exit": "missing",
            },
        },
    )

    assert candidate["source_bucket_kind"] == "taxonomy_provenance_gap"
    assert candidate["explicit_runtime_exclusion"] is True
    assert candidate["source_only_explicit_exclusion"] is True
    assert (
        candidate["runtime_exclusion_reason"]
        == "lifecycle_flow_incomplete_stage_contract"
    )
    assert (
        candidate["lifecycle_flow_contract_status"]
        == "source_only_blocked_incomplete_stage_contract"
    )
    assert candidate["missing_lifecycle_flow_stage_keys"] == [
        "submit",
        "holding",
        "exit",
    ]
    assert candidate["allowed_runtime_apply"] is False
    assert candidate["runtime_effect"] is False


def test_lifecycle_flow_source_only_blocker_overrides_live_runtime_metadata():
    item = {
        "stage": "lifecycle_flow",
        "bucket_type": "combo_lifecycle_flow",
        "bucket_key": (
            "entry=entry:combo_entry_spot:score_score_70p|"
            "submit=submit:missing|holding=holding:missing|exit=exit:missing"
        ),
        "classification_state": "live_auto_apply_ready",
        "live_auto_apply_family": "greenfield_real_environment_authority",
        "entry_bucket_id": "entry:combo_entry_spot:score_score_70p",
        "submit_bucket_id": "submit:missing",
        "holding_bucket_id": "holding:missing",
        "exit_bucket_id": "exit:missing",
        "auto_promotion_contract": {"state": "bounded_live_auto_apply_ready"},
    }

    mod._normalize_candidate_runtime_metadata(item)

    assert item["source_bucket_kind"] == "taxonomy_provenance_gap"
    assert item["review_category"] == "source_only_keep_collecting"
    assert item["review_sub_state"] is None
    assert item["explicit_runtime_exclusion"] is True
    assert item["live_auto_apply_family"] is None
    assert item["allowed_runtime_apply"] is False
    assert item["runtime_effect"] is False
    assert item["runtime_effect_after_approval"] == "none"
    assert item["sim_lifecycle_handoff_allowed"] is False
    assert item["bounded_live_canary_allowed"] is False
    assert item["broker_order_forbidden"] is True
    assert item["auto_promotion_contract"]["state"] == "source_only"
    assert item["auto_promotion_contract"]["deterministic_contract_components"] == []


def test_lifecycle_bucket_discovery_quarantines_contaminated_live_candidates(
    tmp_path, monkeypatch
):
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
                "quarantine_id": "scale_in_policy_2026-05-28",
                "reason": "contaminated_scale_in_policy",
                "exclude_live_auto_apply": True,
                "affected_families": [mod.SCALE_IN_LIVE_AUTO_FAMILY],
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_bucket_discovery_report(
        "2026-05-28",
        ai_raw_response=_ai_keep_response(),
    )

    by_id = {item["bucket_id"]: item for item in report["candidates"]}
    scale_in = next(
        item
        for item in by_id.values()
        if item.get("live_auto_apply_family") == mod.SCALE_IN_LIVE_AUTO_FAMILY
    )
    assert scale_in["classification_state"] == "runtime_blocked_contract_gap"
    assert scale_in["allowed_runtime_apply"] is False
    assert scale_in["promotion_ev_excluded_reason"] == "contaminated_scale_in_policy"
    wait6579 = by_id[
        "entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown"
    ]
    assert wait6579["classification_state"] == mod.ENTRY_ONLY_BRIDGE_METADATA_STATE
    assert wait6579["bounded_live_canary_allowed"] is False
    assert report["summary"]["live_auto_apply_ready_count"] == 0
    assert "contamination_quarantine_live_auto_blocked:1" in report["warnings"]


def test_lifecycle_bucket_discovery_blocks_deterministic_live_when_ai_review_disabled(
    tmp_path, monkeypatch
):
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
        "2026-05-22", ai_review_provider="none"
    )

    blocked = [
        item
        for item in report["surfaced_candidates"]
        if item["classification_state"] == "runtime_blocked_contract_gap"
    ]
    assert {
        item["live_auto_apply_family"]
        for item in blocked
        if item.get("live_auto_apply_family")
    } == {
        mod.SCALE_IN_LIVE_AUTO_FAMILY,
    }
    assert all(
        item.get("ai_tier2_blocked_reason") == "ai_tier2_validation_not_parsed:disabled"
        for item in blocked
    )
    assert report["summary"]["ai_two_pass_review_status"] == "disabled"
    assert (
        "ai_two_pass_review_disabled_fail_closed_live_auto_blocked"
        in report["warnings"]
    )


def test_lifecycle_bucket_discovery_ignores_ambiguous_ai_block_for_live_candidate(
    tmp_path, monkeypatch
):
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

    live = [
        item
        for item in report["surfaced_candidates"]
        if item["classification_state"] == "live_auto_apply_ready"
    ]
    ignored = [item for item in live if item.get("ai_review_block_ignored_reason")]
    assert all(
        (item.get("auto_promotion_contract") or {}).get("tier2_status") == "parsed"
        for item in live
    )
    assert report["summary"]["live_auto_apply_ready_count"] == 1
    assert len(ignored) == 1
    assert (
        "ai_review_ambiguous_live_candidate_kept_for_post_apply" in report["warnings"]
    )


def test_lifecycle_bucket_discovery_compares_deterministic_and_ai_taxonomy_proposals(
    tmp_path, monkeypatch
):
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

    item = next(
        candidate
        for candidate in report["candidates"]
        if candidate["bucket_id"] == bucket_id
    )
    assert item["ai_tier2_proposal"]["proposal_status"] == "provided"
    assert item["ai_tier2_proposal"]["proposal_decision"] == "create_new_dimension"
    assert item["ai_tier2_comparative_review"]["selected_source"] == "hybrid"
    assert (
        item["ai_tier2_comparative_review"]["selected_decision"]
        == "absorb_as_dimension"
    )
    assert item["ai_tier2_taxonomy_decision"] == "absorb_as_dimension"
    assert item["ai_tier2_confidence"] == "high"
    assert report["summary"]["ai_tier2_proposal_count"] == 1
    assert report["summary"]["reviewer_selected_hybrid_count"] == 1
    assert (
        report["summary"]["taxonomy_selected_decision_counts"]["absorb_as_dimension"]
        >= 1
    )


def test_lifecycle_bucket_discovery_fails_closed_when_ai_proposal_lacks_comparison(
    tmp_path, monkeypatch
):
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
        ai_raw_response=_ai_proposal_without_comparison_response(
            "scale_in:blocker_reason:pnl_out_of_range_0_32"
        ),
    )

    assert report["summary"]["ai_two_pass_review_status"] == "parse_rejected"
    assert (
        "ai_review_comparative_review_missing:scale_in:blocker_reason:pnl_out_of_range_0_32"
        in report["warnings"]
    )
    blocked = [
        item
        for item in report["surfaced_candidates"]
        if item["classification_state"] == "runtime_blocked_contract_gap"
    ]
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


def test_lifecycle_bucket_discovery_rejects_legacy_ai_response_without_dual_taxonomy_fields(
    tmp_path, monkeypatch
):
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


def test_lifecycle_bucket_discovery_applies_explicit_contract_ai_block_for_live_candidate(
    tmp_path, monkeypatch
):
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
    assert report["summary"]["live_auto_apply_ready_count"] == 0


def test_lifecycle_bucket_discovery_surfaces_source_contract_drift(
    tmp_path, monkeypatch
):
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
                            "bucket_fields": [
                                "bucket_type",
                                "bucket_key",
                                "removed_field",
                            ],
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
        if item["stage"] == "source_contract"
        and item["classification_state"] == "code_patch_required"
    ]
    assert drift


def test_lifecycle_bucket_discovery_does_not_treat_empty_declared_section_as_contract_removal(
    tmp_path, monkeypatch
):
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
                            "bucket_fields": [
                                "bucket_type",
                                "bucket_key",
                                "next_day_mfe_pct",
                            ],
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


def test_lifecycle_bucket_discovery_accepts_legacy_daily_source_split_alias():
    previous = {
        "schema_version": "lifecycle_source_contract_snapshot_v1",
        "source_keys": ["daily_lifecycle_decision_matrix_reports"],
        "sections": {},
    }
    current = {
        "schema_version": "lifecycle_source_contract_snapshot_v2",
        "source_keys": ["per_date_sources"],
        "sections": {},
    }

    changes = mod._compare_source_contracts(current, previous)

    assert not [item for item in changes if item["change_type"] == "source_removed"]


def test_lifecycle_bucket_discovery_warns_on_duplicate_legacy_source_alias():
    previous = {
        "schema_version": "lifecycle_source_contract_snapshot_v2",
        "source_keys": ["per_date_sources"],
        "sections": {},
    }
    current = {
        "schema_version": "lifecycle_source_contract_snapshot_v2",
        "source_keys": ["daily_lifecycle_decision_matrix_reports", "per_date_sources"],
        "sections": {},
    }

    changes = mod._compare_source_contracts(current, previous)

    duplicate_warnings = [
        item
        for item in changes
        if item["change_type"] == "source_alias_duplicate"
        and item["severity"] == "warning"
        and item["subject"] == "per_date_sources"
    ]
    assert duplicate_warnings
    assert not [item for item in changes if item["change_type"] == "source_removed"]


def test_submit_bucket_rows_emit_ev_and_diagnostic_fields():
    report = ldm_mod._submit_bucket_attribution(
        [
            {
                "stage": "submit",
                "stage_ev_composite_pct": 1.0,
                "runtime_features": {},
            },
            {
                "stage": "submit",
                "stage_ev_composite_pct": -0.5,
                "runtime_features": {},
            },
        ]
    )

    assert report["buckets"]
    assert "equal_weight_avg_profit_pct" in report["buckets"][0]
    assert "diagnostic_win_rate" in report["buckets"][0]


def test_lifecycle_bucket_discovery_openai_review_uses_tier2_schema_and_english_prompt(
    monkeypatch,
):
    captured = {}
    monkeypatch.setenv(
        "KORSTOCKSCAN_LIFECYCLE_BUCKET_DISCOVERY_SOURCE_ONLY_AI_PRIMARY_PROVIDER",
        "openai",
    )

    class _FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                output_text=json.dumps(_ai_keep_response()), usage=SimpleNamespace()
            )

    class _FakeOpenAI:
        def __init__(self, api_key, timeout=None):
            captured["client_timeout"] = timeout
            self.api_key = api_key
            self.timeout = timeout
            self.responses = _FakeResponses()

    monkeypatch.setattr(
        "src.engine.daily_threshold_cycle_report._load_threshold_ai_openai_keys",
        lambda: [("OPENAI_API_KEY", "key")],
    )
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
    assert all(
        item["context_chars"] <= mod.AI_REVIEW_SHARD_CONTEXT_BUDGET_CHARS
        for item in shards
    )


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
    assert (
        by_id["live-1"]["ai_tier2_blocked_reason"]
        == "ai_tier2_validation_not_parsed:timeout"
    )
    assert by_id["sim-1"]["classification_state"] == "sim_auto_approved"


def test_parent_conflict_resolution_classifies_source_quality_gap_children():
    report = {
        "parent_bucket_summaries": [
            {
                "parent_bucket_id": "lifecycle_flow:parent_1",
                "parent_ev": 0.5,
                "parent_joined_sample": 30,
                "child_conflict_warning": True,
                "child_ev_dispersion_pct": 3.0,
                "absorbed_child_bucket_ids": ["child_1", "child_2"],
                "conflicting_child_patterns": [],
            }
        ]
    }
    candidates = [
        {
            "bucket_id": "child_1",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "canonical_parent_bucket": "lifecycle_flow:parent_1",
            "joined_sample": 15,
            "source_quality_adjusted_ev_pct": -1.2,
            "source_quality_gate": "source_quality_blocker",
            "unknown_dimension_counts": {"liquidity_bucket": 2},
        },
        {
            "bucket_id": "child_2",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "canonical_parent_bucket": "lifecycle_flow:parent_1",
            "joined_sample": 10,
            "source_quality_adjusted_ev_pct": 0.3,
            "source_quality_gate": "pass",
        },
    ]

    resolutions = mod._build_parent_conflict_resolution(report, candidates)

    assert len(resolutions) == 1
    r = resolutions[0]
    assert r["parent_bucket_id"] == "lifecycle_flow:parent_1"
    assert r["source_quality_gap_child_count"] == 1
    assert r["child_same_direction_absorbed_count"] >= 0
    assert r["conflict_resolution_state"] in {
        "resolution_blocked_source_quality",
        "resolution_complete",
    }
    assert r["runtime_effect"] is False
    assert r["allowed_runtime_apply"] is False
    items = r["child_resolution_items"]
    child1 = next(i for i in items if i["child_bucket_id"] == "child_1")
    assert child1["child_resolution_state"] == "source_quality_gap"


def test_parent_conflict_resolution_treats_blank_quality_as_gap_but_hold_sample_as_collecting():
    blank_state, blank_details = mod._classify_conflict_child(
        {
            "source_quality_gate": "",
            "source_quality_adjusted_ev_pct": 1.0,
            "joined_sample": 20,
        },
        -0.5,
    )
    hold_state, hold_details = mod._classify_conflict_child(
        {
            "source_quality_gate": "hold_sample_or_incomplete_flow",
            "source_quality_adjusted_ev_pct": 1.0,
            "joined_sample": 1,
        },
        -0.5,
    )

    assert blank_state == "source_quality_gap"
    assert blank_details["source_quality_gate"] == ""
    assert hold_state == "positive_thin_child"
    assert (
        hold_details["floor"] == mod.LIFECYCLE_FLOW_CHILD_STANDALONE_MIN_JOINED_SAMPLE
    )


def test_parent_conflict_resolution_detects_strategy_reversal_and_exclude():
    report = {
        "parent_bucket_summaries": [
            {
                "parent_bucket_id": "lifecycle_flow:parent_ev_pos",
                "parent_ev": 1.5,
                "parent_joined_sample": 40,
                "child_conflict_warning": True,
                "child_ev_dispersion_pct": 4.0,
                "absorbed_child_bucket_ids": ["child_a", "child_b"],
                "conflicting_child_patterns": [
                    {
                        "bucket_id": "child_a",
                        "joined_sample": 15,
                        "source_quality_adjusted_ev_pct": -2.0,
                    },
                ],
            }
        ]
    }
    candidates = [
        {
            "bucket_id": "child_a",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "canonical_parent_bucket": "lifecycle_flow:parent_ev_pos",
            "joined_sample": 15,
            "source_quality_adjusted_ev_pct": -2.0,
            "source_quality_gate": "pass",
            "source_dimensions": {"exclusion_dimension_candidate": "true"},
        },
        {
            "bucket_id": "child_b",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "canonical_parent_bucket": "lifecycle_flow:parent_ev_pos",
            "joined_sample": 25,
            "source_quality_adjusted_ev_pct": 3.0,
            "source_quality_gate": "pass",
        },
    ]

    resolutions = mod._build_parent_conflict_resolution(report, candidates)

    assert len(resolutions) == 1
    r = resolutions[0]
    assert r["strategy_reversal_child_count"] >= 0
    assert r["parent_ev_after_exclusion_estimate"] is not None
    items = r["child_resolution_items"]
    child_a = next(i for i in items if i["child_bucket_id"] == "child_a")
    assert child_a["child_resolution_state"] in {
        "strategy_reversal",
        "exclude_child_candidate",
    }
    assert r["runtime_effect"] is False


def test_parent_conflict_resolution_classifies_positive_thin_as_keep_collecting():
    report = {
        "parent_bucket_summaries": [
            {
                "parent_bucket_id": "lifecycle_flow:parent_ev_neg",
                "parent_ev": -0.8,
                "parent_joined_sample": 20,
                "child_conflict_warning": True,
                "child_ev_dispersion_pct": 5.0,
                "absorbed_child_bucket_ids": ["child_x"],
                "conflicting_child_patterns": [],
            }
        ]
    }
    candidates = [
        {
            "bucket_id": "child_x",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "canonical_parent_bucket": "lifecycle_flow:parent_ev_neg",
            "joined_sample": 4,
            "source_quality_adjusted_ev_pct": -0.3,
            "source_quality_gate": "pass",
        },
    ]

    resolutions = mod._build_parent_conflict_resolution(report, candidates)

    assert len(resolutions) == 1
    r = resolutions[0]
    items = r["child_resolution_items"]
    child = items[0]
    assert child["child_resolution_state"] in {
        "keep_collecting",
        "child_same_direction_absorbed",
        "positive_thin_child",
    }


def test_parent_conflict_resolution_empty_when_no_conflict_parents():
    report = {
        "parent_bucket_summaries": [
            {
                "parent_bucket_id": "lifecycle_flow:no_conflict",
                "parent_ev": 1.0,
                "parent_joined_sample": 50,
                "child_conflict_warning": False,
                "child_ev_dispersion_pct": 1.5,
                "absorbed_child_bucket_ids": [],
            }
        ]
    }
    candidates = []

    resolutions = mod._build_parent_conflict_resolution(report, candidates)

    assert resolutions == []


def test_parent_conflict_resolution_children_same_direction_absorbed():
    report = {
        "parent_bucket_summaries": [
            {
                "parent_bucket_id": "lifecycle_flow:all_absorbed",
                "parent_ev": 2.0,
                "parent_joined_sample": 25,
                "child_conflict_warning": True,
                "child_ev_dispersion_pct": 6.0,
                "absorbed_child_bucket_ids": ["child_one", "child_two"],
                "conflicting_child_patterns": [],
            }
        ]
    }
    candidates = [
        {
            "bucket_id": "child_one",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "canonical_parent_bucket": "lifecycle_flow:all_absorbed",
            "joined_sample": 12,
            "source_quality_adjusted_ev_pct": 3.5,
            "source_quality_gate": "pass",
        },
        {
            "bucket_id": "child_two",
            "stage": "lifecycle_flow",
            "bucket_type": "combo_lifecycle_flow",
            "canonical_parent_bucket": "lifecycle_flow:all_absorbed",
            "joined_sample": 8,
            "source_quality_adjusted_ev_pct": 1.2,
            "source_quality_gate": "pass",
        },
    ]

    resolutions = mod._build_parent_conflict_resolution(report, candidates)

    assert len(resolutions) == 1
    r = resolutions[0]
    assert r["child_same_direction_absorbed_count"] == 2
    assert r["conflict_resolution_state"] == "resolution_complete"


def test_policy_stage_candidates_missing_policy_key_generates_source_dimension_gap():
    from src.engine.lifecycle_bucket_discovery import (
        _policy_stage_candidates,
        _source_dimension_gap_summary,
    )

    payload = {
        "policy_entries": [
            {
                "stage": "entry",
                "policy_key": "",
                "source_quality_gate": "pass",
                "confidence": 0.9,
                "selected_action": "BUY_DEFENSIVE",
            },
            {
                "stage": "submit",
                "policy_key": "submit:valid_key",
                "source_quality_gate": "pass",
                "confidence": 0.8,
                "selected_action": "ALLOW_SUBMIT",
            },
            {
                "stage": "exit",
                "policy_key": "",
                "source_quality_gate": "fail",
                "confidence": 0.7,
                "selected_action": "EXIT",
            },
        ]
    }

    candidates = _policy_stage_candidates(payload)
    assert len(candidates) == 3

    entry_candidate = [c for c in candidates if c["stage"] == "entry"][0]
    assert entry_candidate["bucket_key"] == "-"
    assert entry_candidate["source_dimension_gap"] == "unknown_source_dimensions"
    assert "policy_key" in entry_candidate["missing_dimension_keys"]
    assert (
        entry_candidate["policy_key_gap_classification"]
        == "policy_key_required_missing"
    )
    assert entry_candidate["classification_state"] == "source_only_keep_collecting"
    assert entry_candidate["sim_lifecycle_handoff_allowed"] is False
    assert entry_candidate["source_bucket_kind"] == "source_only_observation"

    submit_candidate = [c for c in candidates if c["stage"] == "submit"][0]
    assert submit_candidate["bucket_key"] == "submit:valid_key"
    assert submit_candidate["source_dimension_gap"] is None
    assert "policy_key" not in submit_candidate["missing_dimension_keys"]
    assert submit_candidate["policy_key_gap_classification"] == "policy_key_provided"
    assert submit_candidate["classification_state"] == "sim_auto_approved"

    exit_candidate = [c for c in candidates if c["stage"] == "exit"][0]
    assert exit_candidate["bucket_key"] == "-"
    assert exit_candidate["source_dimension_gap"] == "unknown_source_dimensions"
    assert "policy_key" in exit_candidate["missing_dimension_keys"]
    assert (
        exit_candidate["policy_key_gap_classification"] == "policy_key_required_missing"
    )
    assert exit_candidate["classification_state"] == "source_only_keep_collecting"

    summary = _source_dimension_gap_summary(candidates)
    assert summary["missing_dimension_key_counts"].get("policy_key", 0) == 2
    assert (
        summary["policy_key_gap_classification_counts"].get(
            "policy_key_required_missing", 0
        )
        == 2
    )
