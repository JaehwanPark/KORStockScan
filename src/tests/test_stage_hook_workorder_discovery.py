import json
from pathlib import Path

from src.engine.automation import stage_hook_workorder_discovery as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _ai_response(candidate_ids: list[str]) -> dict:
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
        "reviewer": "stage_hook_workorder_discovery_ai_review",
        "candidate_reviews": [
            {
                "candidate_id": candidate_id,
                "hook_name": "reviewed_hook",
                "hook_class": "runtime_arbitration_hook",
                "priority": "high",
                "recommended_readiness_tier": "implementation_workorder_ready",
                "confidence": "high",
                "target_subsystem": "stage_hook.reviewed",
                "reason": "stage hook implementation workorder should be surfaced",
                "implementation_requirements": ["start disabled and source-only"],
                "acceptance_tests": ["pytest stage hook tests"],
                "files_likely_touched": ["src/engine/automation/stage_hook_workorder_discovery.py"],
            }
            for candidate_id in candidate_ids
        ],
        "ai_tier2_proposals": [
            {
                "candidate_id": candidate_id,
                "proposal_decision": "new_hook",
                "recommended_canonical_bucket": f"stage_hook:{candidate_id}",
                "recommended_metric_or_dimension": ["source_quality_adjusted_ev_pct", "diagnostic_win_rate"],
                "reasoning_summary": "source-only hook proposal",
                "confidence": "high",
                "required_source_fields": contract_fields,
                "forbidden_uses": mod.FORBIDDEN_USES,
            }
            for candidate_id in candidate_ids
        ],
        "comparative_reviews": [
            {
                "candidate_id": candidate_id,
                "selected_decision": "new_hook",
                "selected_source": "hybrid",
                "recommended_canonical_bucket": f"stage_hook:{candidate_id}",
                "recommended_metric_or_dimension": ["source_quality_adjusted_ev_pct", "diagnostic_win_rate"],
                "comparison_summary": "deterministic and AI hook proposals agree",
                "rejected_alternative_reason": "",
                "confidence": "high",
                "required_source_fields": contract_fields,
                "forbidden_uses": mod.FORBIDDEN_USES,
                "workorder_title": "Review stage hook",
                "workorder_priority": "high",
            }
            for candidate_id in candidate_ids
        ],
        "audit": {"status": "pass", "issues": [], "forbidden_use_violations": [], "reason": "ok"},
    }


def _deterministic_candidate_ids(target: str = "2026-05-26") -> list[str]:
    return [str(item["candidate_id"]) for item in mod._deterministic_candidates(target)[0]]


def test_stage_hook_ai_review_rejects_real_preapply_primary_ev_claim():
    candidate_id = "stage_hook_holding_flow_runner_debounce_guard_producer_gap_sim_holding_runner_gap_missing"
    payload = _ai_response([candidate_id])
    payload["ai_tier2_proposals"][0][
        "reasoning_summary"
    ] = "Use real_1share_primary_ev as the hook evidence and allow runtime_change_from_preapply_real."

    status, _, warnings = mod._parse_ai_review_response(payload)

    assert status == "parse_rejected"
    assert f"ai_review_ai_proposal_evidence_authority_violation:{candidate_id}" in warnings


def test_stage_hook_discovery_normalizes_all_stage_hook_classes(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    candidates = [
        ("producer_gap_sim_entry_selection_gap_missing", "sim_entry_selection_gap_missing", 12),
        ("producer_gap_sim_submit_fill_quality_gap_missing", "sim_submit_fill_quality_gap_missing", 12),
        ("producer_gap_sim_holding_runner_gap_missing", "sim_holding_runner_gap_missing", 40),
        ("producer_gap_sim_exit_plateau_breakdown_gap_missing", "sim_exit_plateau_breakdown_gap_missing", 40),
        ("producer_gap_sim_stop_recovery_gap_missing", "sim_stop_recovery_gap_missing", 40),
        ("producer_gap_sim_scale_in_counterfactual_gap_missing", "sim_scale_in_counterfactual_gap_missing", 12),
        ("producer_gap_sim_source_quality_join_gap_missing", "sim_source_quality_join_gap_missing", 40),
    ]
    _write_json(
        report_dir / "producer_gap_discovery" / "producer_gap_discovery_2026-05-26.json",
        {
            "status": "warning",
            "producer_gap_candidates": [
                {
                    "candidate_id": candidate_id,
                    "pattern_type": pattern_type,
                    "sample_count": sample_count,
                    "evidence": ["strict_match_count=10", "required_producer=x", "estimated_uplift_pct_sum=3.0"],
                }
                for candidate_id, pattern_type, sample_count in candidates
            ],
        },
    )

    report = mod.build_stage_hook_workorder_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response(_deterministic_candidate_ids()),
    )

    hook_classes = {item["stage_hook_candidate_contract"]["hook_class"] for item in report["stage_hook_candidates"]}
    assert {
        "entry_policy_hook_candidate",
        "submit_quality_hook_candidate",
        "runtime_arbitration_hook",
        "scale_in_policy_hook_candidate",
        "source_schema_provenance_hook",
    }.issubset(hook_classes)
    assert all(item["runtime_effect"] is False for item in report["stage_hook_candidates"])
    assert all(item["allowed_runtime_apply"] is False for item in report["stage_hook_candidates"])
    assert any(
        item["stage_hook_candidate_contract"]["readiness_tier"] == "implementation_workorder_ready"
        for item in report["stage_hook_candidates"]
    )
    assert report["code_improvement_orders"]
    assert all(order["runtime_effect"] is False for order in report["code_improvement_orders"])
    assert all(order["stage_hook_candidate_contract"]["allowed_runtime_apply"] is False for order in report["code_improvement_orders"])


def test_stage_hook_discovery_scores_are_not_hard_gates(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "producer_gap_discovery" / "producer_gap_discovery_2026-05-26.json",
        {
            "producer_gap_candidates": [
                {
                    "candidate_id": "producer_gap_sim_holding_runner_gap_missing",
                    "pattern_type": "sim_holding_runner_gap_missing",
                    "sample_count": 1,
                    "evidence": ["required_producer=runner_regime_counterfactual_producer"],
                }
            ]
        },
    )

    report = mod.build_stage_hook_workorder_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response(_deterministic_candidate_ids()),
    )

    candidate = report["stage_hook_candidates"][0]
    contract = candidate["stage_hook_candidate_contract"]
    assert contract["evidence_score"] > 0
    assert contract["readiness_tier"] in {"observe_only", "producer_needed", "hook_design_ready"}
    assert report["status"] == "pass"


def test_stage_hook_discovery_merges_duplicate_hook_names(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "producer_gap_discovery" / "producer_gap_discovery_2026-05-26.json",
        {
            "producer_gap_candidates": [
                {
                    "candidate_id": "producer_gap_scale_in_counterfactual_gap_missing",
                    "pattern_type": "scale_in_counterfactual_gap_missing",
                    "sample_count": 12,
                    "evidence": ["matched_scale_in_gap_rows=10", "required_producer=legacy_scale"],
                },
                {
                    "candidate_id": "producer_gap_sim_scale_in_counterfactual_gap_missing",
                    "pattern_type": "sim_scale_in_counterfactual_gap_missing",
                    "sample_count": 12,
                    "evidence": ["required_producer=sim_scale"],
                },
            ]
        },
    )

    report = mod.build_stage_hook_workorder_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response(_deterministic_candidate_ids()),
    )

    scale_candidates = [
        item
        for item in report["stage_hook_candidates"]
        if item["stage_hook_candidate_contract"]["hook_name"] == "scale_in_would_add_policy_probe"
    ]
    assert len(scale_candidates) == 1
    contract = scale_candidates[0]["stage_hook_candidate_contract"]
    assert contract["source_candidate_ids"] == [
        "producer_gap_scale_in_counterfactual_gap_missing",
        "producer_gap_sim_scale_in_counterfactual_gap_missing",
    ]
    assert contract["source_pattern_types"] == [
        "scale_in_counterfactual_gap_missing",
        "sim_scale_in_counterfactual_gap_missing",
    ]


def test_stage_hook_discovery_entry_time_gap_blocks_by_source_quality(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "producer_gap_discovery" / "producer_gap_discovery_2026-05-26.json",
        {
            "producer_gap_candidates": [
                {
                    "candidate_id": "producer_gap_sim_entry_selection_gap_missing",
                    "pattern_type": "sim_entry_selection_gap_missing",
                    "sample_count": 100,
                    "evidence": [
                        "entry_time_field_rate=0.0000",
                        "strict_match_count=10",
                        "required_producer=sim_entry_selection_bucket_producer",
                        "expected_ev=positive",
                    ],
                }
            ]
        },
    )

    report = mod.build_stage_hook_workorder_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response(_deterministic_candidate_ids()),
    )

    contract = report["stage_hook_candidates"][0]["stage_hook_candidate_contract"]
    assert contract["readiness_tier"] == "blocked_by_source_quality"
    assert "entry_time_provenance_penalty" in contract["risk_penalties"]
    assert report["code_improvement_orders"] == []


def test_stage_hook_discovery_ai_forbidden_use_fails_closed(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "producer_gap_discovery" / "producer_gap_discovery_2026-05-26.json",
        {
            "producer_gap_candidates": [
                {
                    "candidate_id": "producer_gap_sim_holding_runner_gap_missing",
                    "pattern_type": "sim_holding_runner_gap_missing",
                    "sample_count": 40,
                    "evidence": ["strict_match_count=20", "required_producer=x", "estimated_uplift_pct_sum=5"],
                }
            ]
        },
    )
    response = _ai_response(["stage_hook_holding_flow_runner_debounce_guard_producer_gap_sim_holding_runner_gap_missing"])
    response["audit"]["forbidden_use_violations"] = ["attempted_runtime_apply"]

    report = mod.build_stage_hook_workorder_discovery_report("2026-05-26", provider="openai", ai_raw_response=response)

    assert report["status"] == "fail"
    assert report["summary"]["ai_fail_closed"] is True
    assert report["code_improvement_orders"] == []
