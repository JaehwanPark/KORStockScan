import json

from src.engine import swing_lifecycle_bucket_discovery as mod


def _ai_response(bucket_ids: list[str]) -> dict:
    contract_fields = [
        "metric_role",
        "decision_authority",
        "window_policy",
        "sample_floor",
        "primary_decision_metric",
        "source_quality_gate",
        "forbidden_uses",
    ]
    return {
        "schema_version": 1,
        "reviewer": "swing_lifecycle_bucket_discovery_ai_review",
        "ai_tier2_proposals": [
            {
                "bucket_id": bucket_id,
                "proposal_decision": "keep_bucket",
                "recommended_canonical_bucket": f"swing:{bucket_id}",
                "recommended_metric_or_dimension": ["source_quality_adjusted_ev_pct"],
                "reasoning_summary": "source-only swing bucket proposal",
                "confidence": "high",
                "required_source_fields": contract_fields,
                "forbidden_uses": mod.FORBIDDEN_USES,
            }
            for bucket_id in bucket_ids
        ],
        "comparative_reviews": [
            {
                "bucket_id": bucket_id,
                "selected_decision": "keep_bucket",
                "selected_source": "hybrid",
                "recommended_canonical_bucket": f"swing:{bucket_id}",
                "recommended_metric_or_dimension": ["source_quality_adjusted_ev_pct"],
                "comparison_summary": "deterministic and AI proposals agree",
                "rejected_alternative_reason": "",
                "confidence": "high",
                "required_source_fields": contract_fields,
                "forbidden_uses": mod.FORBIDDEN_USES,
                "workorder_title": "Review swing bucket",
                "workorder_priority": "medium",
            }
            for bucket_id in bucket_ids
        ],
        "audit": {"status": "pass", "issues": [], "forbidden_use_violations": [], "reason": "ok"},
    }


def test_swing_lifecycle_bucket_ai_review_rejects_real_preapply_primary_ev_claim():
    bucket_id = "swing_bucket_entry_entry_bucket_attribution_safe_pool_probe"
    payload = _ai_response([bucket_id])
    payload["comparative_reviews"][0][
        "comparison_summary"
    ] = "Use pre_apply_real primary_ev and merge real pnl with sim/probe EV before mapped policy is enabled."

    status, _, warnings = mod._parse_ai_review_response(payload)

    assert status == "parse_rejected"
    assert f"ai_review_comparative_reviews_evidence_authority_violation:{bucket_id}" in warnings


def test_bucket_discovery_auto_approves_sim_only_candidates(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    discovery_dir = tmp_path / "discovery"
    sim_approval_dir = tmp_path / "sim_auto_approvals"
    sim_policy_dir = tmp_path / "swing_sim_policies"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", discovery_dir)
    monkeypatch.setattr("src.engine.swing.sim_auto_approval_control_tower.SIM_AUTO_APPROVAL_DIR", sim_approval_dir)
    monkeypatch.setattr("src.engine.swing.sim_auto_approval_control_tower.SWING_SIM_POLICY_DIR", sim_policy_dir)

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "entry_bucket_attribution",
                            "bucket_key": "safe_pool|probe",
                            "lifecycle_stage": "entry",
                            "recommended_route": "sim_auto_approved",
                            "source_quality_gate": "pass",
                            "joined_sample": 3,
                            "sample_count": 3,
                            "source_quality_adjusted_ev_pct": 1.2,
                        }
                    ],
                    "code_improvement_workorders": [],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    bucket_id = "swing_bucket_entry_entry_bucket_attribution_safe_pool_probe"
    report = mod.build_swing_lifecycle_bucket_discovery(
        target,
        provider="openai",
        ai_raw_response=_ai_response([bucket_id]),
    )

    assert report["summary"]["sim_auto_approved_count"] == 1
    candidate = report["sim_auto_approved_candidates"][0]
    assert candidate["classification_state"] == "sim_auto_approved"
    assert candidate["next_route"] == "next_preopen_swing_sim_policy_input"
    assert candidate["actual_order_submitted"] is False
    assert candidate["broker_order_forbidden"] is True
    assert candidate["allowed_runtime_apply"] is False
    assert "real_order_submit" in candidate["forbidden_uses"]
    assert report["human_intervention_required"] is False
    assert report["allowed_runtime_apply"] is False

    mod.write_report(report)
    approval = json.loads((sim_approval_dir / "swing_sim_auto_approval_2026-05-22.json").read_text())
    catalog = json.loads((sim_policy_dir / "swing_sim_policy_catalog_2026-05-22.json").read_text())
    assert approval["approved"] is True
    assert approval["approved_source_ids"] == ["swing_lifecycle_bucket_discovery"]
    assert catalog["policies"][0]["bucket_id"] == candidate["bucket_id"]


def test_bucket_discovery_reviews_sim_auto_candidates_before_large_source_only_tail(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    source_only_buckets = [
        {
            "bucket_type": "entry_bucket_attribution",
            "bucket_key": f"source_only_{idx}",
            "lifecycle_stage": "entry",
            "recommended_route": "keep_collecting",
            "source_quality_gate": "hold_sample",
            "joined_sample": 0,
            "sample_count": 0,
        }
        for idx in range(120)
    ]
    sim_bucket = {
        "bucket_type": "holding_exit_bucket_attribution",
        "bucket_key": "mfe_high|trailing",
        "lifecycle_stage": "holding_exit",
        "recommended_route": "sim_auto_approved",
        "source_quality_gate": "pass",
        "joined_sample": 12,
        "sample_count": 12,
        "source_quality_adjusted_ev_pct": 2.4,
    }
    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "entry_bucket_attribution": {"buckets": source_only_buckets},
                "holding_exit_bucket_attribution": {"buckets": [sim_bucket]},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    calls = []

    def fake_call(context):
        calls.append(context)
        return _ai_response(context["candidate_ids"]), {
            "provider": "openai",
            "status": "success",
            "model": mod.AI_REVIEW_MODEL,
            "reasoning_effort": "low",
            "input_context_chars": 1000,
        }

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)

    sim_bucket_id = "swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_trailing"
    report = mod.build_swing_lifecycle_bucket_discovery(
        target,
        provider="openai",
    )

    assert report["summary"]["ai_two_pass_review_status"] == "parsed"
    assert report["summary"]["ai_fail_closed"] is False
    assert [call["shard_id"] for call in calls] == ["sim_policy_review", "taxonomy_discovery_review"]
    assert calls[0]["candidate_ids"] == [sim_bucket_id]
    assert report["summary"]["ai_reviewed_candidate_count"] == 11
    assert report["summary"]["ai_unreviewed_candidate_count"] == 110
    assert report["summary"]["unreviewed_sim_auto_candidate_count"] == 0
    assert report["summary"]["sim_auto_approved_count"] == 1
    assert report["sim_auto_approved_candidates"][0]["bucket_id"] == sim_bucket_id
    assert report["sim_auto_approved_candidates"][0]["ai_review_coverage"] == "reviewed"


def test_bucket_discovery_taxonomy_correction_does_not_block_parsed_sim_policy(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "holding_exit_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "holding_exit_bucket_attribution",
                            "bucket_key": "mfe_high|trailing",
                            "lifecycle_stage": "holding_exit",
                            "recommended_route": "sim_auto_approved",
                            "source_quality_gate": "pass",
                            "joined_sample": 12,
                            "sample_count": 12,
                        }
                    ]
                },
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "entry_bucket_attribution",
                            "bucket_key": "source_only_tail",
                            "lifecycle_stage": "entry",
                            "recommended_route": "keep_collecting",
                            "source_quality_gate": "hold_sample",
                            "joined_sample": 0,
                            "sample_count": 0,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    def fake_call(context):
        payload = _ai_response(context["candidate_ids"])
        if context["shard_id"] == "taxonomy_discovery_review":
            payload["audit"]["status"] = "correction_required"
            payload["audit"]["issues"] = ["source taxonomy should be normalized"]
        return payload, {"provider": "openai", "status": "success", "model": mod.AI_REVIEW_MODEL}

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)

    report = mod.build_swing_lifecycle_bucket_discovery(target, provider="openai")

    assert report["summary"]["ai_two_pass_review_status"] == "parsed"
    assert report["summary"]["ai_fail_closed"] is False
    assert report["summary"]["sim_auto_approved_count"] == 1
    assert "ai_two_pass_review_correction_required_source_only" in report["warnings"]
    assert "ai_two_pass_review_fail_closed_sim_auto_blocked" not in report["warnings"]


def test_bucket_discovery_non_sim_shard_missing_does_not_block_parsed_sim_policy(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "holding_exit_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "holding_exit_bucket_attribution",
                            "bucket_key": "mfe_high|trailing",
                            "lifecycle_stage": "holding_exit",
                            "recommended_route": "sim_auto_approved",
                            "source_quality_gate": "pass",
                            "joined_sample": 12,
                            "sample_count": 12,
                        }
                    ]
                },
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "entry_bucket_attribution",
                            "bucket_key": "source_only_tail",
                            "lifecycle_stage": "entry",
                            "recommended_route": "keep_collecting",
                            "source_quality_gate": "hold_sample",
                            "joined_sample": 0,
                            "sample_count": 0,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    def fake_call(context):
        if context["shard_id"] == "taxonomy_discovery_review":
            return None, {"provider": "openai", "status": "timeout", "model": mod.AI_REVIEW_MODEL}
        return _ai_response(context["candidate_ids"]), {"provider": "openai", "status": "success", "model": mod.AI_REVIEW_MODEL}

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)

    report = mod.build_swing_lifecycle_bucket_discovery(target, provider="openai")

    assert report["summary"]["ai_two_pass_review_status"] == "partial"
    assert report["summary"]["ai_fail_closed"] is False
    assert report["summary"]["sim_auto_approved_count"] == 1
    assert report["summary"]["missing_ai_tier2_proposal_count"] == 1
    assert report["summary"]["sim_missing_ai_tier2_proposal_count"] == 0
    assert "ai_two_pass_review_partial_source_only" in report["warnings"]
    assert "ai_two_pass_review_fail_closed_sim_auto_blocked" not in report["warnings"]


def test_bucket_discovery_provider_disabled_downgrades_sim_auto(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "entry_bucket_attribution",
                            "bucket_key": "safe_pool|probe",
                            "lifecycle_stage": "entry",
                            "recommended_route": "sim_auto_approved",
                            "source_quality_gate": "pass",
                            "joined_sample": 3,
                            "sample_count": 3,
                        }
                    ],
                    "code_improvement_workorders": [],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target, provider="none")

    assert report["summary"]["ai_fail_closed"] is True
    assert report["summary"]["sim_auto_approved_count"] == 0
    assert "ai_two_pass_review_missing_fail_closed" in report["warnings"]
    assert "ai_two_pass_review_fail_closed_sim_auto_blocked" in report["warnings"]
    candidate = report["surfaced_candidates"][0]
    assert candidate["classification_state"] == "source_only_keep_collecting"
    assert candidate["sim_auto_downgraded_by_ai_fail_closed"] is True
    assert candidate["allowed_runtime_apply"] is False


def test_bucket_discovery_flags_daily_simulation_contract_gap(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps({"input_contract": {"swing_daily_simulation_consumed": True}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    assert report["summary"]["source_contract_status"] == "fail"
    assert report["summary"]["runtime_blocked_contract_gap_count"] == 1
    assert report["surfaced_candidates"][0]["classification_state"] == "runtime_blocked_contract_gap"
    assert report["surfaced_candidates"][0]["allowed_runtime_apply"] is False
    assert "runtime_threshold_mutation" in report["surfaced_candidates"][0]["forbidden_uses"]


def test_bucket_discovery_long_bucket_ids_are_unique_and_stable(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    prefix = (
        "swing_strategy_discovery_sim_v1|no_block_observed|BOTTOM|"
        "discovery_gap_unobserved|discovery_score_unobserved|discovery_vpw_unobserved|"
    )
    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "entry_bucket_attribution",
                            "bucket_key": f"{prefix}next_open_entry|next_open|equal_notional",
                            "lifecycle_stage": "entry",
                            "recommended_route": "keep_collecting",
                            "source_quality_gate": "hold_sample",
                            "joined_sample": 0,
                            "sample_count": 0,
                        },
                        {
                            "bucket_type": "entry_bucket_attribution",
                            "bucket_key": f"{prefix}pullback_limit_entry|missing_next_quote|risk_capped",
                            "lifecycle_stage": "entry",
                            "recommended_route": "keep_collecting",
                            "source_quality_gate": "hold_sample",
                            "joined_sample": 0,
                            "sample_count": 0,
                        },
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    bucket_ids = [item["bucket_id"] for item in report["surfaced_candidates"]]
    assert len(bucket_ids) == len(set(bucket_ids))
    assert all(len(item.rsplit("_", 1)[-1]) == 12 for item in bucket_ids)


def test_bucket_discovery_code_patch_candidate_proposal_tracks_source_remediation(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "scale_in_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "scale_in_bucket_attribution",
                            "bucket_key": "ofi_qi_missing",
                            "lifecycle_stage": "scale_in",
                            "recommended_route": "keep_collecting",
                            "source_quality_gate": "source_quality_blocker",
                            "joined_sample": 3,
                            "sample_count": 3,
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    candidate = report["surfaced_candidates"][0]
    assert candidate["classification_state"] == "code_patch_required"
    assert candidate["deterministic_proposal"]["proposal_decision"] == "source_quality_blocker"
    assert candidate["runtime_effect"] is False
    assert candidate["allowed_runtime_apply"] is False


def test_bucket_discovery_normalizes_explicit_workorder_contract(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "entry_bucket_attribution": {
                    "buckets": [],
                    "code_improvement_workorders": [
                        {
                            "workorder_id": "source_gap",
                            "runtime_effect": True,
                            "allowed_runtime_apply": True,
                        }
                    ],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)
    workorder = report["code_improvement_workorders"][0]

    assert workorder["runtime_effect"] is False
    assert workorder["allowed_runtime_apply"] is False
    assert workorder["actual_order_submitted"] is False
    assert workorder["broker_order_forbidden"] is True
    assert "real_order_submit" in workorder["forbidden_uses"]


def test_bucket_discovery_surfaces_ai_review_augmentation_workorders(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "holding_exit_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "holding_exit_bucket_attribution",
                            "bucket_key": "mfe_low|mae_low|time_stop",
                            "lifecycle_stage": "holding_exit",
                            "recommended_route": "source_only_keep_collecting",
                            "source_quality_gate": "hold_sample",
                            "joined_sample": 1,
                            "sample_count": 1,
                        }
                    ],
                    "code_improvement_workorders": [],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    assert report["ai_review_policy"]["status"] == "configured_deterministic_two_pass"
    assert report["ai_review_policy"]["required_flow_status"] == {
        "interpretation": "implemented",
        "audit": "implemented",
        "final_conclusions": "implemented",
    }
    assert report["summary"]["ai_review_augmentation_point_count"] >= 3
    assert report["summary"]["ai_audit_point_count"] >= 3
    assert report["summary"]["ai_audit_explicit_gap_count"] == 0
    assert report["ai_audit"]["sim_auto_policy_preserved"] is True
    assert report["ai_audit"]["status"] == "configured_deterministic_two_pass"
    assert all(item["runtime_effect"] is False for item in report["ai_audit"]["audit_points"])
    assert all(item["allowed_runtime_apply"] is False for item in report["ai_audit"]["audit_points"])
    assert all(item["explicit_gap_type"] is None for item in report["ai_audit"]["audit_points"])
    assert "swing_ldm_ai_review_not_configured" not in report["warnings"]
    ai_workorders = [
        item
        for item in report["code_improvement_workorders"]
        if item["target_subsystem"] == "swing_lifecycle_bucket_discovery_ai_review"
    ]
    assert ai_workorders == []


def test_bucket_discovery_surfaces_swing_entry_bottleneck_handoff(tmp_path, monkeypatch):
    target = "2026-05-22"
    matrix_dir = tmp_path / "matrix"
    matrix_dir.mkdir()
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "discovery")

    matrix_path = matrix_dir / f"swing_lifecycle_decision_matrix_{target}.json"
    matrix_path.write_text(
        json.dumps(
            {
                "input_contract": {"swing_daily_simulation_consumed": False},
                "swing_entry_bottleneck": {
                    "primary": "SWING_ENTRY_DROUGHT_CRITICAL",
                    "matches": ["GATEKEEPER_PULLBACK_WAIT", "SUBMIT_ZERO"],
                    "counts": {"entry_unique": 15, "submitted_unique_records": 0},
                    "ratios": {"probe_to_blocked_unique_pct": 0.0},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(mod, "matrix_report_paths", lambda target_date: (matrix_path, matrix_path.with_suffix(".md")))

    report = mod.build_swing_lifecycle_bucket_discovery(target)

    candidate = next(
        item
        for item in report["surfaced_candidates"]
        if item["bucket_id"] == "swing_entry_bottleneck_swing_entry_drought_critical"
    )
    assert candidate["classification_state"] == "code_patch_required"
    assert candidate["next_route"] == "code_improvement_workorder"
    assert candidate["runtime_effect"] is False
    assert candidate["allowed_runtime_apply"] is False
    assert report["summary"]["swing_entry_bottleneck_primary"] == "SWING_ENTRY_DROUGHT_CRITICAL"
    assert report["summary"]["swing_entry_bottleneck_candidate_present"] is True
