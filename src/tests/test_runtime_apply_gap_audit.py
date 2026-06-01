import json
import re
from pathlib import Path

from src.engine.ai.postclose_review_config import PostcloseAIReviewConfig
from src.engine import runtime_apply_gap_audit as mod


def _patch_dirs(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    apply_dir = tmp_path / "data" / "threshold_cycle" / "apply_plans"
    monkeypatch.setattr(mod, "BASE_REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir / "runtime_apply_gap_audit")
    monkeypatch.setattr(mod, "APPLY_PLAN_DIR", apply_dir)
    return report_dir


def _write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_core_artifacts(report_dir: Path, target_date: str = "2026-05-22"):
    _write_json(
        report_dir / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json",
        {"report_type": "runtime_approval_summary", "summary": {}},
    )
    _write_json(
        report_dir / "code_improvement_workorder" / f"code_improvement_workorder_{target_date}.json",
        {"report_type": "code_improvement_workorder", "orders": []},
    )
    _write_json(
        report_dir / "runtime_apply_bridge" / f"runtime_apply_bridge_{target_date}.json",
        {"report_type": "runtime_apply_bridge", "candidates": []},
    )
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target_date}.json",
        {"report_type": "lifecycle_bucket_discovery", "surfaced_candidates": []},
    )


def _runtime_gemini_config() -> PostcloseAIReviewConfig:
    return PostcloseAIReviewConfig(
        artifact="RUNTIME_APPLY_GAP_AUDIT",
        model="gpt-5.4",
        reasoning_effort="low",
        timeout_sec=180,
        primary_provider="gemini_3_5_flash",
        failback_provider="openai",
        gemini_model="gemini-3.5-flash",
        gemini_shard_size=10,
    )


def test_runtime_apply_gap_audit_emits_source_dimension_gap_directive(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir, "2026-05-22")
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {
            "report_type": "lifecycle_bucket_discovery",
            "source_dimension_gap_summary": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": "source_quality_gap_discovery",
                "gap_count": 1,
                "actionable_unknown_gap_count": 1,
            },
            "surfaced_candidates": [
                {
                    "bucket_id": "entry:combo_entry_spot:unknown",
                    "stage": "entry",
                    "classification_state": "source_only_keep_collecting",
                    "source_quality_gate": "pass",
                    "source_dimension_gap": "unknown_source_dimensions",
                    "recommended_resolution": "resolve_unknown_source_dimensions",
                    "missing_dimension_keys": ["liquidity_bucket"],
                }
            ],
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    directives = report["codex_workorder_directives"]
    assert report["summary"]["actionable_unknown_gap_count"] == 1
    assert report["source_dimension_gap_summary"]["decision_authority"] == "source_quality_gap_discovery"
    source_gap_directives = [item for item in directives if item["directive_type"] == "RESOLVE_SOURCE_DIMENSION_GAP"]
    assert len(source_gap_directives) == 1


def test_runtime_apply_gap_audit_uses_source_dimension_summary_when_candidates_are_truncated(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir, "2026-05-22")
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {
            "report_type": "lifecycle_bucket_discovery",
            "source_dimension_gap_summary": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": "source_quality_gap_discovery",
                "gap_count": 2,
                "actionable_unknown_gap_count": 1,
                "actionable_candidates": [
                    {
                        "candidate_id": "entry:combo_entry_spot:summary-only",
                        "stage": "entry",
                        "classification_state": "source_only_keep_collecting",
                        "source_dimension_gap": "unknown_source_dimensions",
                        "recommended_resolution": "resolve_unknown_source_dimensions",
                    }
                ],
            },
            "surfaced_candidates": [],
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    assert any(
        item["directive_type"] == "RESOLVE_SOURCE_DIMENSION_GAP"
        and item["candidate_id"] == "entry:combo_entry_spot:summary-only"
        for item in report["codex_workorder_directives"]
    )


def test_runtime_apply_gap_audit_emits_quiet_gap_directive_when_rollup_missing(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir, "2026-05-22")
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {
            "report_type": "lifecycle_bucket_discovery",
            "quiet_gap_summary": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "decision_authority": "source_quality_gap_discovery",
                "quiet_gap_count": 2,
                "rollup_required_count": 2,
                "sim_live_connected_quiet_gap_count": 0,
                "quiet_gap_type_counts": {"parent_conflict_child": 1, "positive_source_only_keep_collecting": 1},
            },
            "surfaced_candidates": [],
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    assert report["summary"]["quiet_gap_count"] == 2
    assert report["summary"]["quiet_gap_rollup_count"] == 2
    assert report["summary"]["quiet_gap_codex_directive_count"] == 1
    assert any(item["directive_type"] == "REVIEW_LIFECYCLE_QUIET_GAP" for item in report["codex_workorder_directives"])


def test_runtime_apply_gap_audit_does_not_duplicate_quiet_gap_directive_when_workorder_exists(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir, "2026-05-22")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-22.json",
        {
            "report_type": "code_improvement_workorder",
            "orders": [{"order_id": "order_lifecycle_quiet_gap_parent_conflict_rollup"}],
        },
    )
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {
            "report_type": "lifecycle_bucket_discovery",
            "quiet_gap_summary": {
                "quiet_gap_count": 1,
                "rollup_required_count": 1,
                "quiet_gap_type_counts": {"parent_conflict_child": 1},
            },
            "surfaced_candidates": [],
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    assert report["summary"]["quiet_gap_count"] == 1
    assert report["summary"]["quiet_gap_codex_directive_count"] == 0
    assert not any(item["directive_type"] == "REVIEW_LIFECYCLE_QUIET_GAP" for item in report["codex_workorder_directives"])


def test_runtime_apply_gap_audit_emits_quiet_gap_directive_for_partial_rollup_handoff(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir, "2026-05-22")
    _write_json(
        report_dir / "code_improvement_workorder" / "code_improvement_workorder_2026-05-22.json",
        {
            "report_type": "code_improvement_workorder",
            "orders": [{"order_id": "order_lifecycle_quiet_gap_parent_conflict_rollup"}],
        },
    )
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {
            "report_type": "lifecycle_bucket_discovery",
            "quiet_gap_summary": {
                "quiet_gap_count": 2,
                "rollup_required_count": 2,
                "quiet_gap_type_counts": {
                    "parent_conflict_child": 1,
                    "ai_review_parsed_low_coverage": 1,
                },
            },
            "surfaced_candidates": [],
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    directive = next(item for item in report["codex_workorder_directives"] if item["directive_type"] == "REVIEW_LIFECYCLE_QUIET_GAP")
    assert report["summary"]["quiet_gap_codex_directive_count"] == 1
    assert directive["missing_workorder_order_ids"] == ["order_lifecycle_quiet_gap_ai_review_coverage_rollup"]


def test_runtime_apply_gap_audit_emits_observation_warning_rollup_directive(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir, "2026-05-22")
    _write_json(
        report_dir / "observation_source_quality_audit" / "observation_source_quality_audit_2026-05-22.json",
        {"status": "warning", "summary": {"warning_stage_count": 1}},
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    assert report["quiet_gap_summary"]["observation_source_quality_warning_count"] == 1
    assert any(
        item["directive_type"] == "REVIEW_OBSERVATION_SOURCE_QUALITY_WARNING"
        for item in report["codex_workorder_directives"]
    )


def test_runtime_apply_gap_gemini_review_splits_40_candidates_into_10_candidate_shards(monkeypatch):
    calls = []

    def fake_call(context, config):
        calls.append([item["candidate_id"] for item in context["review_candidates"]])
        return (
            json.dumps(
                {
                    "schema_version": 1,
                    "reviewer": "runtime_apply_gap_ai_review",
                    "candidate_reviews": [
                        {
                            "candidate_id": item["candidate_id"],
                            "recommended_disposition": "sim_auto_approved",
                            "route_decision": "keep_sim_policy",
                            "confidence": "medium",
                            "reason": "Shard review passed.",
                            "required_followup": [],
                        }
                        for item in context["review_candidates"]
                    ],
                    "audit": {"status": "pass", "issues": [], "reason": "ok"},
                    "codex_directives": [],
                }
            ),
            {"provider": "gemini", "status": "success", "gemini_key_rotation_attempts": 1},
        )

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)
    context = {
        "reviewer": "runtime_apply_gap_ai_review",
        "review_candidates": [{"candidate_id": f"candidate-{index}"} for index in range(40)],
    }

    raw, status = mod._call_sharded_gemini_runtime_review(context, config=_runtime_gemini_config())
    parse_status, payload, warnings = mod._parse_ai_review_response(raw)

    assert parse_status == "parsed"
    assert warnings == []
    assert len(calls) == 4
    assert all(len(call) == 10 for call in calls)
    assert [item["candidate_id"] for item in payload["candidate_reviews"]] == [
        f"candidate-{index}" for index in range(40)
    ]
    assert status["provider"] == "gemini"
    assert status["shard_count"] == 4
    assert status["parsed_shard_count"] == 4


def test_runtime_apply_gap_gemini_shard_failure_uses_openai_full_context_failback(monkeypatch):
    calls = []

    def fake_call(context, config):
        calls.append((config.primary_provider, len(context["review_candidates"])))
        if config.primary_provider == "gemini_3_5_flash":
            return "not-json", {"provider": "gemini", "status": "contract_failed"}
        return (
            json.dumps(
                {
                    "schema_version": 1,
                    "reviewer": "runtime_apply_gap_ai_review",
                    "candidate_reviews": [],
                    "audit": {"status": "pass", "issues": [], "reason": "openai failback"},
                    "codex_directives": [],
                }
            ),
            {"provider": "openai", "status": "success"},
        )

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)
    context = {
        "reviewer": "runtime_apply_gap_ai_review",
        "review_candidates": [{"candidate_id": f"candidate-{index}"} for index in range(12)],
    }

    raw, status = mod._call_sharded_gemini_runtime_review(context, config=_runtime_gemini_config())

    assert json.loads(raw)["audit"]["reason"] == "openai failback"
    assert calls == [("gemini_3_5_flash", 10), ("openai", 12)]
    assert status["provider"] == "openai"
    assert status["failback_used"] is True
    assert status["gemini_key_rotation_exhausted"] is True


def test_positive_edge_source_only_is_fail_visible(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "entry:positive-stuck",
                    "stage": "entry",
                    "classification_state": "source_only_keep_collecting",
                    "sample": 24,
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 1.05,
                    "recommended_route": "candidate_recovery_or_relax",
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    assert report["status"] == "fail"
    assert report["summary"]["critical_failure_count"] >= 1
    assert any(row["failure_reason"] == "positive_edge_stuck_source_only" for row in report["candidate_route_ledger"])
    assert any(
        item["directive_type"] == "RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE"
        for item in report["codex_workorder_directives"]
    )


def test_positive_edge_source_only_explicit_exclusion_is_provenance_not_fail(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    candidate_id = "lifecycle_flow:combo_lifecycle_flow:source-only"
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": candidate_id,
                    "stage": "lifecycle_flow",
                    "classification_state": "source_only_keep_collecting",
                    "source_bucket_kind": "taxonomy_provenance_gap",
                    "sample": 24,
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 1.05,
                    "recommended_route": "hold_no_edge",
                    "allowed_runtime_apply": False,
                    "broker_order_forbidden": True,
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == candidate_id)
    assert row["failure_state"] == "pass"
    assert row["final_disposition"] == "source_only_explicit_exclusion"
    assert row["explicit_runtime_exclusion"] is True
    assert row["runtime_exclusion_reason"] == "greenfield_policy_not_emitted_no_complete_lifecycle_flow"
    assert row["derived_review_category"] == "source_only_keep_collecting"
    assert row["derived_review_sub_state"] == "greenfield_policy_not_emitted"
    assert report["summary"]["critical_failure_count"] == 0
    assert report["summary"]["derived_review_category_counts"]["source_only_keep_collecting"] == 1
    assert not report["codex_workorder_directives"]


def test_ai_source_quality_blocker_positive_edge_is_not_runtime_gap_fail(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    _write_json(
        report_dir / "swing_lifecycle_bucket_discovery" / "swing_lifecycle_bucket_discovery_2026-05-22.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "swing:blocked-positive",
                    "lifecycle_stage": "holding_exit",
                    "classification_state": "source_only_keep_collecting",
                    "sample_count": 20,
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 8.2,
                    "comparative_review": {"selected_decision": "source_quality_blocker"},
                }
            ]
        },
    )
    monkeypatch.setattr(
        mod,
        "_call_openai_ai_review",
        lambda context, config: (
            json.dumps(
                {
                    "schema_version": 1,
                    "reviewer": "runtime_apply_gap_ai_review",
                    "candidate_reviews": [],
                    "audit": {"status": "pass", "issues": [], "reason": "source quality blocker already explicit"},
                    "codex_directives": [],
                }
            ),
            {"provider": "openai", "status": "success", "model": config.model},
        ),
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="openai")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == "swing:blocked-positive")
    assert row["failure_state"] == "blocked_source_quality"
    assert row["failure_reason"] == "ai_tier2_source_quality_blocker"
    assert row["final_disposition"] == "source_quality_blocker"
    assert report["summary"]["critical_failure_count"] == 0
    assert not any(
        item["candidate_id"] == "swing:blocked-positive"
        and item["directive_type"] == "RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE"
        for item in report["codex_workorder_directives"]
    )


def test_swing_positive_edge_source_only_tier2_missing_is_fail_closed_handoff(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    _write_json(
        report_dir / "swing_lifecycle_bucket_discovery" / "swing_lifecycle_bucket_discovery_2026-05-22.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "swing:positive-source-only",
                    "lifecycle_stage": "holding_exit",
                    "classification_state": "source_only_keep_collecting",
                    "sample_count": 20,
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 8.2,
                    "allowed_runtime_apply": False,
                    "broker_order_forbidden": True,
                    "forbidden_uses": [
                        "broker_submit",
                        "runtime_threshold_apply",
                        "provider_route_change",
                        "bot_restart_trigger",
                        "position_cap_release",
                    ],
                    "ai_review_status": "missing",
                    "ai_tier2_proposal": {"proposal_status": "not_provided", "proposal_decision": "reject"},
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == "swing:positive-source-only")
    assert row["failure_state"] == "pass"
    assert row["failure_reason"] == ""
    assert row["final_disposition"] == "tier2_fail_closed"
    assert row["runtime_exclusion_reason"] == "swing_tier2_missing_fail_closed_source_only"
    assert row["derived_review_category"] == "tier2_fail_closed_source_only"
    assert report["summary"]["critical_failure_count"] == 0
    assert report["summary"]["derived_review_category_counts"]["tier2_fail_closed_source_only"] == 1
    assert report["runtime_uptake_kpi"]["runtime_uptake_rate_pct"] == 0.0
    assert not any(
        item["candidate_id"] == "swing:positive-source-only"
        and item["directive_type"] == "RESOLVE_SOURCE_ONLY_STUCK_POSITIVE_EDGE"
        for item in report["codex_workorder_directives"]
    )


def test_missing_artifact_enters_retry_queue(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {"surfaced_candidates": []},
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    assert report["status"] == "fail"
    failure_codes = {item["failure_code"] for item in report["retry_queue"]}
    assert "runtime_apply_bridge_missing_artifact" in failure_codes
    assert "runtime_approval_summary_missing_artifact" in failure_codes
    assert any(
        item["directive_type"] == "RETRY_MISSING_ARTIFACT_CHAIN"
        for item in report["codex_workorder_directives"]
    )


def test_ai_review_parse_fail_is_retryable(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": "entry_gap:2026-05-22",
                    "family": "entry_gap",
                    "stage": "entry",
                    "bridge_candidate_state": "runtime_blocked_contract_gap",
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 0.5,
                    "target_env_keys": [],
                }
            ]
        },
    )
    monkeypatch.setattr(
        mod,
        "_call_openai_ai_review",
        lambda context, config: ("not-json", {"provider": "openai", "status": "success", "model": config.model}),
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="openai")

    assert report["ai_reasoning_review"]["failure_code"] == "ai_parse_fail"
    assert report["ai_reasoning_review"]["ai_review_retry_pending"] is True
    assert any(item["failure_code"] == "ai_parse_fail" for item in report["retry_queue"])


def test_ai_reason_is_stored_as_raw_en_and_user_reason_is_ko(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": "entry_gap:2026-05-22",
                    "family": "entry_gap",
                    "stage": "entry",
                    "bridge_candidate_state": "runtime_blocked_contract_gap",
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 0.5,
                    "target_env_keys": [],
                }
            ]
        },
    )
    monkeypatch.setattr(
        mod,
        "_call_openai_ai_review",
        lambda context, config: (
            json.dumps(
                {
                    "schema_version": 1,
                    "reviewer": "runtime_apply_gap_ai_review",
                    "candidate_reviews": [
                        {
                            "candidate_id": "entry_gap:2026-05-22",
                            "recommended_disposition": "code_patch_required",
                            "route_decision": "require_code_patch",
                            "confidence": "medium",
                            "reason": "Runtime hook mapping is missing.",
                            "required_followup": ["add runtime hook mapping"],
                        }
                    ],
                    "audit": {"status": "pass", "issues": [], "reason": "Reviewed."},
                    "codex_directives": [],
                }
            ),
            {"provider": "openai", "status": "success", "model": config.model},
        ),
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="openai")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == "entry_gap:2026-05-22")
    assert row["ai_reason_en"] == "Runtime hook mapping is missing."
    assert row["ai_reason_language_violation"] is False
    assert "코드 보완" in row["reason_ko"]


def test_ready_but_not_applied_remains_retry_target(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": "entry_ready:2026-05-22",
                    "family": "entry_ready",
                    "stage": "entry",
                    "bridge_candidate_state": "live_auto_apply_ready",
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    assert any(item["failure_code"] == "ready_but_not_applied" for item in report["retry_queue"])
    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == "entry_ready:2026-05-22")
    assert row["final_disposition"] == "post_apply_attribution_pending"
    assert row["retryable"] is True


def test_greenfield_ready_missing_policy_is_fail_before_preopen(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    family = mod.GREENFIELD_REAL_ENV_FAMILY
    candidate_id = f"{family}:2026-05-22"
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": candidate_id,
                    "family": family,
                    "stage": "greenfield_real_env",
                    "bridge_candidate_state": "live_auto_apply_ready",
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "target_env_keys": [
                        "GREENFIELD_REAL_ENV_AUTHORITY_ENABLED",
                        "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE",
                    ],
                    "recommended_values": {
                        "policy_file": str(tmp_path / "missing_greenfield_real_env_policy.json"),
                        "policy_version": candidate_id,
                    },
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == candidate_id)
    assert report["status"] == "fail"
    assert row["failure_state"] == "fail"
    assert row["failure_reason"] == "greenfield_policy_file_missing"
    assert row["greenfield_policy_state"] == "greenfield_policy_file_missing"
    assert any(item["failure_code"] == "greenfield_policy_file_missing" for item in report["retry_queue"])


def test_greenfield_discovery_live_candidate_uses_bridge_exclusion_not_handoff_fail(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    family = mod.GREENFIELD_REAL_ENV_FAMILY
    candidate_id = "lifecycle_flow:positive-greenfield"
    _write_json(
        report_dir / "lifecycle_bucket_discovery" / "lifecycle_bucket_discovery_2026-05-22.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": candidate_id,
                    "family": family,
                    "stage": "lifecycle_flow",
                    "classification_state": "live_auto_apply_ready",
                    "source_bucket_kind": "live_auto_candidate",
                    "sample": 1,
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "recommended_route": "candidate_recovery_or_relax",
                }
            ]
        },
    )
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "summary": {
                "greenfield_policy_emit_state": "not_emitted_no_complete_lifecycle_flow",
                "greenfield_lifecycle_flow_live_auto_apply_candidate_count": 1,
            },
            "candidates": [],
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == candidate_id)
    assert row["failure_state"] == "pass"
    assert row["final_disposition"] == "source_only_explicit_exclusion"
    assert row["consumer_state"] == "explicit_bridge_exclusion"
    assert row["runtime_exclusion_reason"] == "not_emitted_no_complete_lifecycle_flow"
    assert row["derived_review_category"] == "source_only_keep_collecting"
    assert row["derived_review_sub_state"] == "greenfield_policy_not_emitted"
    assert not any(item["failure_code"] == "producer_consumer_handoff_missing" for item in report["retry_queue"])
    assert not report["producer_consumer_contract_drift"]
    assert report["summary"]["critical_failure_count"] == 0


def test_ready_bridge_consumed_by_next_preopen_apply_is_not_retry_target(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    candidate_id = "entry_ready:2026-05-22"
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": candidate_id,
                    "family": "entry_ready",
                    "stage": "entry",
                    "bridge_candidate_state": "live_auto_apply_ready",
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "target_env_keys": ["AI_SCORE65_74_RECOVERY_PROBE_ENABLED"],
                }
            ]
        },
    )
    _write_json(
        mod.APPLY_PLAN_DIR / "threshold_apply_2026-05-23.json",
        {
            "runtime_apply_bridge": {
                "approved_requests": [
                    {
                        "candidate_id": candidate_id,
                        "family": "entry_ready",
                    }
                ]
            }
        },
    )
    monkeypatch.setattr(
        mod,
        "_call_openai_ai_review",
        lambda context, config: (
            json.dumps(
                {
                    "schema_version": 1,
                    "reviewer": "runtime_apply_gap_ai_review",
                    "candidate_reviews": [],
                    "audit": {"status": "pass", "issues": [], "reason": "source quality blocker already explicit"},
                    "codex_directives": [],
                }
            ),
            {"provider": "openai", "status": "success", "model": config.model},
        ),
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="openai")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == candidate_id)
    assert row["preopen_apply_state"] == "consumed_by_next_preopen"
    assert row["failure_state"] == "pass"
    assert not any(item["failure_code"] == "ready_but_not_applied" for item in report["retry_queue"])


def test_runtime_hook_gap_closes_with_codex_directive(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": "scale_gap:2026-05-22",
                    "family": "scale_gap",
                    "stage": "scale_in",
                    "bridge_candidate_state": "runtime_blocked_contract_gap",
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 0.25,
                    "target_env_keys": [],
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    assert any(
        item["directive_type"] == "IMPLEMENT_SCALE_IN_POLICY_CONTRACT"
        for item in report["codex_workorder_directives"]
    )


def test_bridge_counterfactual_source_field_gap_does_not_emit_runtime_directive(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    candidate_id = "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22"
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": candidate_id,
                    "family": "entry_wait6579_score66_69_recovery_gate_v1",
                    "stage": "entry",
                    "bridge_candidate_state": "runtime_blocked_contract_gap",
                    "source_quality_gate": "pass",
                    "source_quality_adjusted_ev_pct": 1.18,
                    "target_env_keys": [],
                    "evidence_grade": "grade_2_counterfactual",
                    "transition_target": "sim_lifecycle_handoff",
                    "explicit_runtime_exclusion": True,
                    "bridge_exclusion_reason": "counterfactual_source_field_gap",
                    "missing_runtime_source_fields": ["liquidity", "overbought", "time"],
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == candidate_id)
    assert row["failure_state"] == "blocked_contract"
    assert row["final_disposition"] == "source_only_explicit_exclusion"
    assert row["runtime_exclusion_reason"] == "counterfactual_source_field_gap"
    assert not any(
        item["candidate_id"] == candidate_id
        and item["directive_type"] == "IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET"
        for item in report["codex_workorder_directives"]
    )


def test_wait6579_bridge_missing_split_bucket_is_sim_lifecycle_handoff(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    candidate_id = "entry_wait6579_score66_69_recovery_gate_v1:2026-05-22"
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": candidate_id,
                    "family": "entry_wait6579_score66_69_recovery_gate_v1",
                    "stage": "entry",
                    "bridge_candidate_state": "blocked_source_quality",
                    "source_quality_gate": "unknown",
                    "target_env_keys": [],
                    "evidence_grade": "grade_2_counterfactual",
                    "transition_target": "sim_lifecycle_handoff",
                    "explicit_runtime_exclusion": True,
                    "bridge_exclusion_reason": "counterfactual_sim_lifecycle_handoff",
                    "missing_runtime_source_fields": [],
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == candidate_id)
    assert row["failure_state"] == "blocked_source_quality"
    assert row["final_disposition"] == "source_quality_blocker"
    assert row["runtime_hook_state"] == "not_applicable_source_only"
    assert row["runtime_exclusion_reason"] == "counterfactual_sim_lifecycle_handoff"
    assert not any(
        item["candidate_id"] == candidate_id
        and item["directive_type"] == "IMPLEMENT_RUNTIME_BRIDGE_FOR_ENTRY_BUCKET"
        for item in report["codex_workorder_directives"]
    )


def test_bridge_bootstrap_pending_with_env_mapping_is_not_code_directive(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)
    _write_json(
        report_dir / "runtime_apply_bridge" / "runtime_apply_bridge_2026-05-22.json",
        {
            "candidates": [
                {
                    "candidate_id": "scale_hold:2026-05-22",
                    "family": "scale_hold",
                    "stage": "scale_in",
                    "bridge_candidate_state": "bootstrap_pending",
                    "source_quality_gate": "pass",
                    "target_env_keys": ["SCALPING_SCALE_IN_EFFECTIVE_QTY_CAP"],
                    "rolling_confirmation": {
                        "avg_down": {
                            "runtime_bridge_exclusion_reason": "primary_ev_uplift_below_live_floor"
                        }
                    },
                }
            ]
        },
    )

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

    row = next(item for item in report["candidate_route_ledger"] if item["candidate_id"] == "scale_hold:2026-05-22")
    assert row["final_disposition"] == "source_only_keep_collecting"
    assert row["runtime_hook_state"] == "mapped"
    assert not any(
        item["candidate_id"] == "scale_hold:2026-05-22"
        and item["directive_type"] == "IMPLEMENT_SCALE_IN_POLICY_CONTRACT"
        for item in report["codex_workorder_directives"]
    )


def test_gpt_54_minimum_model_is_enforced(tmp_path, monkeypatch):
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _write_core_artifacts(report_dir)

    report = mod.build_runtime_apply_gap_audit(
        "2026-05-22",
        ai_review_provider="openai",
        ai_review_model="gpt-5.3",
    )

    assert report["status"] == "fail"
    assert report["ai_reasoning_review"]["failure_code"] == "ai_review_model_too_low"


def test_ai_prompt_is_english_and_markdown_is_korean():
    context = mod._render_ai_input_context_en(
        [
            {
                "candidate_id": "entry",
                "domain": "scalping",
                "stage": "entry",
                "primary_ev": 1.0,
                "source_quality_gate": "pass",
                "producer_state": "source_only_keep_collecting",
                "final_disposition": "code_patch_required",
                "failure_state": "fail",
                "failure_reason": "positive_edge_stuck_source_only",
            }
        ],
        [],
    )
    prompt = mod._build_ai_review_prompt_en(context)
    markdown = mod._render_markdown_ko(
        {
            "date": "2026-05-22",
            "status": "fail",
            "summary": {"critical_failure_count": 1},
            "runtime_uptake_kpi": {"runtime_uptake_rate_pct": 0, "positive_edge_source_quality_pass_count": 1},
            "retry_queue": [],
            "codex_workorder_directives": [],
            "aggressive_push_targets": [],
        }
    )

    assert not re.search(r"[가-힣]", prompt)
    assert "내부 AI 프롬프트 언어" in markdown
    assert re.search(r"[가-힣]", markdown)
