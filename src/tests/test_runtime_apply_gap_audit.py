import json
import re
from pathlib import Path

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
        lambda context, model: ("not-json", {"provider": "openai", "status": "success", "model": model}),
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
        lambda context, model: (
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
            {"provider": "openai", "status": "success", "model": model},
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

    report = mod.build_runtime_apply_gap_audit("2026-05-22", ai_review_provider="none")

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
