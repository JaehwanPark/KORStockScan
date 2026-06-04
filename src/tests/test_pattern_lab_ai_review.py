import json
from pathlib import Path

from src.engine import pattern_lab_ai_review as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_pattern_lab_ai_review_builds_two_pass_source_only_report(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "warning",
            "checks": [
                {
                    "check_id": "scalping_ldm_threshold_reentry_sources",
                    "status": "fail",
                    "severity": "automation_handoff_gap",
                    "finding": "missing LDM feedback",
                },
                {
                    "check_id": "pattern_lab_ai_review_contract",
                    "status": "fail",
                    "severity": "ai_review_gap",
                    "finding": "missing reviewer",
                },
            ],
        },
    )
    _write_json(
        report_dir / "scalping_pattern_lab_automation" / "scalping_pattern_lab_automation_2026-05-15.json",
        {"runtime_effect": False, "ev_report_summary": {"consensus_count": 1}},
    )

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="none")

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["runtime_mutation_allowed"] is False
    assert report["decision_authority"] == "pattern_lab_ai_review_source_only"
    assert report["summary"]["ai_two_pass_review_status"] == "disabled_deterministic_review"
    assert report["ai_two_pass_review"]["interpretation"]["review_items"]
    assert report["ai_two_pass_review"]["audit"]["status"] == "pass"
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert "auditor_pass" in conclusion
    assert conclusion["explicit_gap_type"] == "automation_handoff_gap"
    assert conclusion["forbidden_runtime_uses"]
    assert {order["improvement_type"] for order in report["code_improvement_orders"]} == {
        "automation_handoff_gap",
        "ai_review_gap",
    }
    assert all(order["runtime_effect"] is False for order in report["code_improvement_orders"])
    assert (report_dir / "pattern_lab_ai_review" / "pattern_lab_ai_review_2026-05-15.json").exists()


def test_pattern_lab_ai_review_embeds_feedback_handoff_summary(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {
                "status": "pass",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "summary": {"candidate_count": 1},
            },
        )

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="none")

    handoff = report["feedback_handoff_summary"]
    assert handoff["status"] == "pass"
    assert handoff["runtime_effect"] is False
    assert report["summary"]["feedback_handoff_status"] == "pass"
    assert "automation_handoff_gap" in handoff["interpretation_hint"]


def test_pattern_lab_ai_review_resolves_generic_handoff_gap_when_feedback_sources_closed(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["automation_handoff_gap:1"],
            "forbidden_use_violations": [],
            "reason": "AI over-classified a generic handoff gap.",
        },
        "final_conclusions": [
            {
                "review_id": "interpretation_1",
                "domain": "swing",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "Generic handoff gap despite currentness pass.",
                "required_followup": ["create_workorder"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["final_decision"] == "keep"
    assert conclusion["feedback_handoff_resolution"]["status"] == "resolved_by_currentness_feedback_handoff_pass"


def test_pattern_lab_ai_review_keeps_specific_handoff_gap_when_feedback_sources_closed(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["automation_handoff_gap:1"],
            "forbidden_use_violations": [],
            "reason": "AI surfaced a specific unresolved workorder handoff.",
        },
        "final_conclusions": [
            {
                "review_id": "order_swing_lifecycle_candidate_handoff_missing",
                "domain": "swing",
                "final_state": "automation_handoff_gap",
                "final_decision": "surface_workorder",
                "reason": "Specific candidate handoff remains unresolved.",
                "required_followup": ["create_workorder"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "warning"
    assert report["summary"]["audit_status"] == "correction_required"
    assert report["summary"]["ai_review_followup_required"] is False
    assert report["summary"]["generic_ai_review_followup_resolved_by_concrete_orders"] is True
    assert any(
        order["order_id"] == "order_pattern_lab_ai_review_order_swing_lifecycle_candidate_handoff_missing"
        for order in report["code_improvement_orders"]
    )
    assert not any(order["improvement_type"] == "ai_review_followup" for order in report["code_improvement_orders"])
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "automation_handoff_gap"
    assert "feedback_handoff_resolution" not in conclusion


def test_pattern_lab_ai_review_resolves_stale_source_missing_gaps_when_feedback_sources_closed(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
        "code_improvement_workorder",
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "insufficient_context",
            "issues": ["automation_handoff_gap"],
            "forbidden_use_violations": [],
            "reason": "Missing threshold_cycle_ev and code_improvement_workorder.",
        },
        "final_conclusions": [
            {
                "review_id": "threshold_cycle_ev",
                "domain": "cross_domain",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "Source is missing, breaking feedback loop.",
                "required_followup": ["create_workorder"],
            },
            {
                "review_id": "code_improvement_workorder",
                "domain": "cross_domain",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "Source is missing, preventing translation of findings.",
                "required_followup": ["create_workorder"],
            },
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["summary"]["ai_review_followup_required"] is False
    assert report["code_improvement_orders"] == []
    assert {
        item["feedback_handoff_resolution"]["status"]
        for item in report["ai_two_pass_review"]["final_conclusions"]
    } == {"resolved_by_existing_feedback_source_context"}


def test_pattern_lab_ai_review_generic_resolution_ids_exclude_specific_source_gaps():
    assert "ai_review_two_pass_missing" not in mod.GENERIC_FEEDBACK_HANDOFF_REVIEW_IDS
    assert "ai_two_pass_review_missing" not in mod.GENERIC_FEEDBACK_HANDOFF_REVIEW_IDS
    assert "threshold_cycle_ev_source_contract_drift_warning" not in mod.GENERIC_FEEDBACK_HANDOFF_REVIEW_IDS


def test_pattern_lab_ai_review_resolves_swing_ai_review_missing_when_no_sim_auto_candidates(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    _write_json(
        report_dir / "swing_lifecycle_bucket_discovery" / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "source_contract_status": "pass",
                "ai_fail_closed": False,
                "ai_review_followup_required": False,
                "sim_auto_blocked_by_ai_review_followup": False,
                "pre_review_sim_auto_candidate_count": 0,
                "sim_auto_unreviewed_candidate_count": 0,
                "sim_auto_downgraded_by_review_count": 0,
            },
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["ai_review_two_pass_missing"],
            "forbidden_use_violations": [],
            "reason": "AI over-classified source-only empty swing AI review.",
        },
        "final_conclusions": [
            {
                "review_id": "ai_review_two_pass_missing",
                "domain": "swing",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "swing_lifecycle_bucket_discovery lacks required two-pass AI review.",
                "required_followup": ["review_ai_contract"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["source_context_resolution"]["status"] == "resolved_by_source_only_empty_sim_auto_review_contract"


def test_pattern_lab_ai_review_keeps_swing_ai_review_missing_when_sim_auto_candidates_unreviewed(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    _write_json(
        report_dir / "swing_lifecycle_bucket_discovery" / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "source_contract_status": "pass",
                "ai_fail_closed": False,
                "ai_review_followup_required": False,
                "sim_auto_blocked_by_ai_review_followup": False,
                "pre_review_sim_auto_candidate_count": 1,
                "sim_auto_unreviewed_candidate_count": 1,
                "sim_auto_downgraded_by_review_count": 0,
            },
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["ai_review_two_pass_missing"],
            "forbidden_use_violations": [],
            "reason": "AI surfaced a real swing review gap.",
        },
        "final_conclusions": [
            {
                "review_id": "ai_review_two_pass_missing",
                "domain": "swing",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "swing_lifecycle_bucket_discovery lacks required two-pass AI review.",
                "required_followup": ["review_ai_contract"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "warning"
    assert report["summary"]["audit_status"] == "correction_required"
    assert any(order["review_id"] == "ai_review_two_pass_missing" for order in report["code_improvement_orders"])
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "ai_review_gap"
    assert "source_context_resolution" not in conclusion


def test_pattern_lab_ai_review_resolves_threshold_ev_incomplete_with_classified_source_only_warnings(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    _write_json(
        report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": [
                "swing_lifecycle_bucket_discovery:ai_two_pass_review_missing_fail_closed",
                "pattern_lab_ai_review_warning",
            ],
        },
    )
    _write_json(
        report_dir / "swing_lifecycle_bucket_discovery" / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "source_contract_status": "pass",
                "ai_fail_closed": False,
                "ai_review_followup_required": False,
                "pre_review_sim_auto_candidate_count": 0,
                "sim_auto_unreviewed_candidate_count": 0,
            },
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["threshold_cycle_ev_incomplete"],
            "forbidden_use_violations": [],
            "reason": "AI over-classified classified threshold EV warnings.",
        },
        "final_conclusions": [
            {
                "review_id": "threshold_cycle_ev_incomplete",
                "domain": "scalping",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "threshold_cycle_ev has null status and classified warnings.",
                "required_followup": ["review_threshold_ev"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["source_context_resolution"]["status"] == "resolved_by_classified_threshold_ev_source_only_warnings"


def test_pattern_lab_ai_review_keeps_threshold_ev_incomplete_on_unclassified_warning(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    _write_json(
        report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": ["unexpected_contract_warning"],
        },
    )
    _write_json(
        report_dir / "swing_lifecycle_bucket_discovery" / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "source_contract_status": "pass",
                "ai_fail_closed": False,
                "ai_review_followup_required": False,
                "pre_review_sim_auto_candidate_count": 0,
                "sim_auto_unreviewed_candidate_count": 0,
            },
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["threshold_cycle_ev_incomplete"],
            "forbidden_use_violations": [],
            "reason": "AI surfaced threshold EV warning.",
        },
        "final_conclusions": [
            {
                "review_id": "threshold_cycle_ev_incomplete",
                "domain": "scalping",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "threshold_cycle_ev has an unclassified warning.",
                "required_followup": ["review_threshold_ev"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "warning"
    assert any(order["review_id"] == "threshold_cycle_ev_incomplete" for order in report["code_improvement_orders"])
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "automation_handoff_gap"
    assert "source_context_resolution" not in conclusion


def test_pattern_lab_ai_review_keeps_forbidden_use_gap_when_feedback_sources_closed(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "pattern_lab_currentness_audit" / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["automation_handoff_gap:1"],
            "forbidden_use_violations": ["runtime env apply"],
            "reason": "AI attempted a forbidden runtime use.",
        },
        "final_conclusions": [
            {
                "review_id": "interpretation_1",
                "domain": "swing",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "Forbidden runtime use must remain blocked.",
                "required_followup": ["remove_forbidden_use"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "warning"
    assert report["summary"]["audit_status"] == "correction_required"
    assert report["ai_two_pass_review"]["audit"]["forbidden_use_violations"] == ["runtime env apply"]
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "automation_handoff_gap"
    assert "feedback_handoff_resolution" not in conclusion


def test_pattern_lab_ai_review_accepts_strict_ai_response_with_audit(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    raw_response = {
        "schema_version": 1,
        "interpretation": {
            "review_items": [
                {
                    "review_id": "manual:keep",
                    "domain": "cross_domain",
                    "interpreted_state": "source_only_keep_collecting",
                    "confidence": "medium",
                    "reason": "keep source-only",
                }
            ],
            "source_feedback_status": "pass",
        },
        "audit": {
            "status": "pass",
            "issues": [],
            "forbidden_use_violations": [],
            "reason": "audited",
        },
        "final_conclusions": [
            {
                "review_id": "manual:keep",
                "domain": "cross_domain",
                "final_state": "source_only_keep_collecting",
                "final_decision": "keep",
                "reason": "audited keep",
                "required_followup": ["keep_collecting"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "pass"
    assert report["summary"]["ai_two_pass_review_status"] == "parsed"
    assert report["summary"]["audit_status"] == "pass"
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["auditor_pass"] is True
    assert conclusion["explicit_gap_type"] is None
    assert conclusion["forbidden_runtime_uses"] == mod.FORBIDDEN_USES
    assert report["code_improvement_orders"] == []


def test_pattern_lab_ai_review_does_not_retry_parsed_audit_correction(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    calls = []

    def fake_call(context, *, config=None):
        calls.append(config)
        return {
            "schema_version": 1,
            "interpretation": {"review_items": [], "source_feedback_status": "warning"},
            "audit": {
                "status": "correction_required",
                "issues": ["source follow-up required"],
                "forbidden_use_violations": [],
                "reason": "parsed review requires source-only follow-up",
            },
            "final_conclusions": [
                {
                    "review_id": "manual:followup",
                    "domain": "cross_domain",
                    "final_state": "source_quality_gap",
                    "final_decision": "surface_workorder",
                    "reason": "surface source-only follow-up",
                    "required_followup": ["review_source_quality"],
                }
            ],
        }, {"provider": "openai", "status": "success", **config.provider_status_fields()}

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai")

    assert [call.reasoning_effort for call in calls] == ["medium"]
    assert report["summary"]["ai_review_followup_required"] is True
    assert report["ai_two_pass_review"]["provider_status"]["retry_attempted"] is False
    assert any(order["improvement_type"] == "source_quality_gap" for order in report["code_improvement_orders"])


def test_pattern_lab_ai_review_normalizes_empty_correction_audit(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "pass"},
        "audit": {
            "status": "correction_required",
            "issues": [],
            "forbidden_use_violations": [],
            "reason": "empty correction marker",
        },
        "final_conclusions": [
            {
                "review_id": "manual:keep",
                "domain": "cross_domain",
                "final_state": "source_only_keep_collecting",
                "final_decision": "keep",
                "reason": "keep collecting",
                "required_followup": ["keep_collecting"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["summary"]["ai_review_followup_required"] is False
    assert report["code_improvement_orders"] == []


def test_pattern_lab_ai_review_keeps_empty_correction_audit_when_gap_remains(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": [],
            "forbidden_use_violations": [],
            "reason": "empty correction marker with unresolved gap",
        },
        "final_conclusions": [
            {
                "review_id": "threshold_cycle_ev_source_contract_drift_warning",
                "domain": "cross_domain",
                "final_state": "source_quality_gap",
                "final_decision": "surface_workorder",
                "reason": "source contract drift warning remains unresolved",
                "required_followup": ["review_source_contract_drift"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["summary"]["audit_status"] == "correction_required"
    assert any(
        order["order_id"] == "order_pattern_lab_ai_review_threshold_cycle_ev_source_contract_drift_warning"
        for order in report["code_improvement_orders"]
    )


def test_pattern_lab_ai_review_resolves_implemented_swing_micro_context_contract(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir / "swing_pattern_lab_automation" / "swing_pattern_lab_automation_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "decision_authority": "swing_pattern_lab_analysis_workorder_source_only",
            "ev_report_summary": {
                "source_quality_contracts": {
                    "swing_micro_context": {
                        "source_contract_status": "implemented",
                        "decision_authority": "swing_pattern_lab_analysis_workorder_source_only",
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    }
                }
            },
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["source_quality_gap:1"],
            "forbidden_use_violations": [],
            "reason": "AI surfaced swing micro context source gap.",
        },
        "final_conclusions": [
            {
                "review_id": "order_pattern_lab_ai_review_swing_micro_context_source_quality",
                "domain": "swing",
                "final_state": "source_quality_gap",
                "final_decision": "surface_workorder",
                "reason": "Repair swing micro-context source contract for OFI/QI inputs.",
                "required_followup": ["repair_source_contract"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["final_decision"] == "keep"
    assert conclusion["source_contract_resolution"]["status"] == "resolved_by_implemented_source_contract"


def test_pattern_lab_ai_review_resolves_closed_swing_lifecycle_bucket_discovery_gap(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir / "swing_lifecycle_bucket_discovery" / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "source_contract_status": "pass",
                "code_patch_required_count": 0,
                "implemented_source_quality_waiting_sample_count": 18,
                "ai_review_followup_required": False,
            },
            "warnings": [],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["code_patch_required:1"],
            "forbidden_use_violations": [],
            "reason": "AI surfaced stale swing bucket discovery code patch signal.",
        },
        "final_conclusions": [
            {
                "review_id": "order_pattern_lab_ai_review_swing_lifecycle_bucket_discovery",
                "domain": "swing",
                "final_state": "code_patch_required",
                "final_decision": "surface_workorder",
                "reason": "swing_lifecycle_bucket_discovery still lists code_patch_required items",
                "required_followup": ["review_source_workorders"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["final_decision"] == "keep"
    assert conclusion["source_contract_resolution"]["contract_id"] == "swing_lifecycle_bucket_discovery_code_patch_triage"


def test_pattern_lab_ai_review_keeps_unresolved_swing_lifecycle_bucket_discovery_gap(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir / "swing_lifecycle_bucket_discovery" / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "source_contract_status": "pass",
                "code_patch_required_count": 1,
                "implemented_source_quality_waiting_sample_count": 17,
                "ai_review_followup_required": False,
            },
            "warnings": [],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["code_patch_required:1"],
            "forbidden_use_violations": [],
            "reason": "AI surfaced unresolved swing bucket discovery code patch signal.",
        },
        "final_conclusions": [
            {
                "review_id": "order_pattern_lab_ai_review_swing_lifecycle_bucket_discovery",
                "domain": "swing",
                "final_state": "code_patch_required",
                "final_decision": "surface_workorder",
                "reason": "swing_lifecycle_bucket_discovery still has unresolved code patch",
                "required_followup": ["review_source_workorders"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai", ai_raw_response=raw_response)

    assert report["summary"]["audit_status"] == "correction_required"
    assert any(
        order["order_id"] == "order_pattern_lab_ai_review_order_pattern_lab_ai_review_swing_lifecycle_bucket_discovery"
        and order["improvement_type"] == "code_patch_required"
        for order in report["code_improvement_orders"]
    )
