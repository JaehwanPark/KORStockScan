import json
from pathlib import Path

from src.engine import pattern_lab_ai_review as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_pattern_lab_ai_review_builds_two_pass_source_only_report(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
        report_dir
        / "scalping_pattern_lab_automation"
        / "scalping_pattern_lab_automation_2026-05-15.json",
        {"runtime_effect": False, "ev_report_summary": {"consensus_count": 1}},
    )

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="none")

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["runtime_mutation_allowed"] is False
    assert report["decision_authority"] == "pattern_lab_ai_review_source_only"
    assert (
        report["summary"]["ai_two_pass_review_status"]
        == "disabled_deterministic_review"
    )
    assert report["ai_two_pass_review"]["interpretation"]["review_items"]
    assert report["ai_two_pass_review"]["audit"]["status"] == "pass"
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert "auditor_pass" in conclusion
    assert conclusion["explicit_gap_type"] == "automation_handoff_gap"
    assert conclusion["forbidden_runtime_uses"]
    assert {
        order["improvement_type"] for order in report["code_improvement_orders"]
    } == {
        "automation_handoff_gap",
        "ai_review_gap",
    }
    assert all(
        order["runtime_effect"] is False for order in report["code_improvement_orders"]
    )
    assert (
        report_dir / "pattern_lab_ai_review" / "pattern_lab_ai_review_2026-05-15.json"
    ).exists()


def test_pattern_lab_ai_review_embeds_feedback_handoff_summary(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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


def test_pattern_lab_ai_review_resolves_source_only_warnings_before_late_bound_threshold_ev(
    tmp_path,
    monkeypatch,
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 8,
                "missing_feedback_source_count": 0,
            },
            "checks": [],
        },
    )
    _write_json(
        report_dir
        / "scalping_pattern_lab_automation"
        / "scalping_pattern_lab_automation_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "ev_report_summary": {
                "scalp_entry_adm_status": "warning",
                "scalp_entry_adm_joined_sample": 10,
            },
        },
    )
    source_payloads = {
        "lifecycle_decision_matrix": {"status": "pass", "runtime_effect": False},
        "lifecycle_bucket_discovery": {
            "status": "pass",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {"source_contract_status": "warning"},
            "warnings": ["source_contract_drift_warning"],
        },
        "swing_lifecycle_decision_matrix": {"status": "pass", "runtime_effect": False},
        "swing_lifecycle_bucket_discovery": {
            "status": "pass",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
        "swing_strategy_discovery_ev": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": ["pending_future_quotes"],
        },
    }
    for label, payload in source_payloads.items():
        _write_json(report_dir / label / f"{label}_2026-05-15.json", payload)

    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": [
                "scalp_entry_adm_status_warning",
                "lifecycle_bucket_discovery_source_contract_drift",
                "swing_strategy_discovery_pending_quotes",
            ],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "scalp_entry_adm_status_warning",
                "domain": "scalping",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "scalp_entry_adm_status='warning' with only 10 joined samples.",
            },
            {
                "review_id": "lifecycle_bucket_discovery_source_contract_drift",
                "domain": "scalping",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "lifecycle_bucket_discovery reports source_contract_drift_warning.",
            },
            {
                "review_id": "swing_strategy_discovery_pending_quotes",
                "domain": "swing",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "swing_strategy_discovery_ev has pending_future_quotes.",
            },
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusions = report["ai_two_pass_review"]["final_conclusions"]
    assert {item["final_state"] for item in conclusions} == {
        "source_only_keep_collecting"
    }
    assert {item["source_context_resolution"]["status"] for item in conclusions} == {
        "resolved_by_classified_source_quality_warning"
    }
    assert all(
        item["source_context_resolution"]["runtime_effect"] is False
        for item in conclusions
    )


def test_pattern_lab_ai_review_resolves_generic_handoff_gap_when_feedback_sources_closed(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["final_decision"] == "keep"
    assert (
        conclusion["feedback_handoff_resolution"]["status"]
        == "resolved_by_currentness_feedback_handoff_pass"
    )


def test_pattern_lab_ai_review_resolves_closed_propagation_and_workorder_source_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 8,
                "missing_feedback_source_count": 0,
            },
            "checks": [
                {
                    "check_id": "pattern_lab_ai_review_contract",
                    "status": "pass",
                    "severity": "info",
                    "finding": "Pattern lab AI reviewer contract is present.",
                }
            ],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "code_improvement_workorder",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
        "pattern_lab_propagation_audit",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {
                "status": "pass",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "summary": {},
            },
        )
    _write_json(
        report_dir
        / "scalping_pattern_lab_automation"
        / "scalping_pattern_lab_automation_2026-05-15.json",
        {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": [
                "Missing threshold_cycle_ev source prevents validation.",
                "Missing code_improvement_workorder source prevents tracking.",
                "Missing pattern_lab_propagation_audit source prevents handoff verification.",
            ],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "ai_review_gap",
                "domain": "scalping",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": (
                    "The reviewer contract is missing and threshold_cycle_ev, code_improvement_workorder, "
                    "and pattern_lab_propagation_audit sources are missing."
                ),
                "required_followup": ["restore_sources"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    handoff = report["feedback_handoff_summary"]
    assert handoff["status"] == "pass"
    assert handoff["present_auxiliary_source_count"] == 2
    assert handoff["missing_auxiliary_source_labels"] == []
    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["final_decision"] == "keep"
    assert conclusion["feedback_handoff_resolution"]["runtime_effect"] is False
    assert any(
        "pattern_lab_propagation_audit" in path for path in conclusion["source_paths"]
    )


def test_pattern_lab_ai_review_keeps_unclosed_propagation_source_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 8,
                "missing_feedback_source_count": 0,
            },
            "checks": [
                {
                    "check_id": "pattern_lab_ai_review_contract",
                    "status": "pass",
                    "severity": "info",
                    "finding": "Pattern lab AI reviewer contract is present.",
                }
            ],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "code_improvement_workorder",
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
                "summary": {},
            },
        )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": [],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "ai_review_gap",
                "domain": "scalping",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "The reviewer contract is present but pattern_lab_propagation_audit source is missing.",
                "required_followup": ["restore_pattern_lab_propagation_audit"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    handoff = report["feedback_handoff_summary"]
    assert handoff["missing_auxiliary_source_labels"] == [
        "pattern_lab_propagation_audit"
    ]
    assert report["summary"]["audit_status"] == "correction_required"
    assert any(
        order["review_id"] == "ai_review_gap"
        for order in report["code_improvement_orders"]
    )
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "ai_review_gap"
    assert "feedback_handoff_resolution" not in conclusion


def test_pattern_lab_ai_review_keeps_specific_handoff_gap_when_feedback_sources_closed(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "warning"
    assert report["summary"]["audit_status"] == "correction_required"
    assert report["summary"]["ai_review_followup_required"] is False
    assert (
        report["summary"]["generic_ai_review_followup_resolved_by_concrete_orders"]
        is True
    )
    assert any(
        order["order_id"]
        == "order_pattern_lab_ai_review_order_swing_lifecycle_candidate_handoff_missing"
        for order in report["code_improvement_orders"]
    )
    assert not any(
        order["improvement_type"] == "ai_review_followup"
        for order in report["code_improvement_orders"]
    )
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "automation_handoff_gap"
    assert "feedback_handoff_resolution" not in conclusion


def test_pattern_lab_ai_review_resolves_closed_ldm_threshold_feedback_false_positive(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
            "issues": ["scalp_entry_adm_unknown_bucket_source_quality_gap"],
            "forbidden_use_violations": [],
            "reason": "AI over-classified a closed feedback handoff.",
        },
        "final_conclusions": [
            {
                "review_id": "scalp_entry_adm_unknown_bucket_source_quality_gap",
                "domain": "scalping",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "Missing LDM/threshold feedback in scalping pattern lab prevents closed-loop improvement",
                "required_followup": ["create_workorder"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert (
        conclusion["feedback_handoff_resolution"]["status"]
        == "resolved_by_currentness_feedback_handoff_pass"
    )


def test_pattern_lab_ai_review_resolves_contract_gap_when_currentness_contract_passes(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [
                {
                    "check_id": "pattern_lab_ai_review_contract",
                    "status": "pass",
                    "severity": "info",
                    "finding": "AI review contract is present.",
                }
            ],
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
            "issues": ["ai_review_gap"],
            "forbidden_use_violations": [],
            "reason": "AI over-classified an implemented reviewer contract.",
        },
        "final_conclusions": [
            {
                "review_id": "ai_review_gap",
                "domain": "scalping",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "The scalping pattern lab lacks a mandatory two-pass AI reviewer contract.",
                "required_followup": ["create_workorder"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert (
        conclusion["feedback_handoff_resolution"]["status"]
        == "resolved_by_currentness_ai_review_contract_pass"
    )


def test_pattern_lab_ai_review_resolves_stale_source_missing_gaps_when_feedback_sources_closed(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["summary"]["ai_review_followup_required"] is False
    assert report["code_improvement_orders"] == []
    assert {
        item["feedback_handoff_resolution"]["status"]
        for item in report["ai_two_pass_review"]["final_conclusions"]
    } == {"resolved_by_existing_feedback_source_context"}


def test_pattern_lab_ai_review_resolves_code_improvement_workorder_self_review_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
            "status": "correction_required",
            "issues": ["ai_review_gap"],
            "forbidden_use_violations": [],
            "reason": "AI over-classified the workorder feedback source.",
        },
        "final_conclusions": [
            {
                "review_id": "code_improvement_workorder",
                "domain": "cross_domain",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "AI review process has warnings and duplicate orders.",
                "required_followup": ["audit pattern_lab_ai_review"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["feedback_handoff_resolution"]["status"] == (
        "resolved_by_existing_code_improvement_workorder_context"
    )


def test_pattern_lab_ai_review_resolves_current_pattern_lab_self_pending_workorders(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
    ):
        _write_json(
            report_dir / label / f"{label}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-05-15.json",
        {
            "status": "pass",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {"selected_implement_now_new_runtime_effect_false_count": 2},
            "orders": [
                {
                    "order_id": "order_pattern_lab_ai_review_ai_review_gap_missing_contract",
                    "source_report_type": "pattern_lab_ai_review",
                    "decision": "implement_now",
                },
                {
                    "order_id": "order_pattern_lab_ai_review_code_improvement_order_pending",
                    "source_report_type": "pattern_lab_ai_review",
                    "decision": "implement_now",
                },
                {
                    "order_id": "order_pattern_lab_ai_review_automation_handoff_gap_missing_feedback",
                    "source_report_type": "pattern_lab_ai_review",
                    "decision": "attach_existing_family",
                },
            ],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["code_improvement_order_pending"],
            "forbidden_use_violations": [],
            "reason": "AI surfaced self-referential pattern lab workorder pending state.",
        },
        "final_conclusions": [
            {
                "review_id": "code_improvement_order_pending",
                "domain": "cross_domain",
                "final_state": "code_patch_required",
                "final_decision": "surface_workorder",
                "reason": "10 pending code improvement orders require implementation.",
                "required_followup": ["implement_current_workorder"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["source_context_resolution"]["status"] == (
        "resolved_by_current_code_improvement_workorder_self_reference"
    )


def test_pattern_lab_ai_review_resolves_code_improvement_workorder_ai_review_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [
                {
                    "check_id": "pattern_lab_ai_review_contract",
                    "status": "pass",
                }
            ],
        },
    )
    for label in (
        "threshold_cycle_ev",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
        "code_improvement_workorder",
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
            "issues": ["code_improvement_workorder_ai_review_gap"],
            "forbidden_use_violations": [],
            "reason": "AI over-classified a closed workorder self-review gap.",
        },
        "final_conclusions": [
            {
                "review_id": "code_improvement_workorder_ai_review_gap",
                "domain": "cross_domain",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "The pattern lab AI review system generated self-referential orders.",
                "required_followup": ["review_workorder"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["feedback_handoff_resolution"]["status"] == (
        "resolved_by_existing_code_improvement_workorder_context"
    )


def test_pattern_lab_ai_review_resolves_classified_source_quality_warning_gaps(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [
                {
                    "check_id": "pattern_lab_ai_review_contract",
                    "status": "pass",
                }
            ],
        },
    )
    for label in (
        "lifecycle_decision_matrix",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
        "code_improvement_workorder",
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
                "lifecycle_bucket_discovery:source_contract_drift_warning",
                "swing_strategy_discovery:pending_future_quotes",
                "scalp_entry_adm:joined_sample_below_sample_floor",
                "scalp_entry_adm:unknown_bucket_source_quality_gap",
                "producer_gap_discovery_ai_review_followup_required",
            ],
        },
    )
    _write_json(
        report_dir
        / "lifecycle_bucket_discovery"
        / "lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": ["source_contract_drift_warning"],
            "summary": {"status": "pass", "source_contract_status": "warning"},
        },
    )
    _write_json(
        report_dir
        / "swing_strategy_discovery_ev"
        / "swing_strategy_discovery_ev_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": ["pending_future_quotes"],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": [
                "lifecycle_bucket_discovery_source_contract_drift",
                "swing_strategy_discovery_pending_future_quotes",
                "scalp_entry_adm_status_warning",
            ],
            "forbidden_use_violations": [],
            "reason": "AI elevated classified source-quality warnings.",
        },
        "final_conclusions": [
            {
                "review_id": "lifecycle_bucket_discovery_source_contract_drift",
                "domain": "cross_domain",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "source_contract_drift_warning remains source-only warning.",
                "required_followup": ["review_source_quality"],
            },
            {
                "review_id": "swing_strategy_discovery_pending_future_quotes",
                "domain": "swing",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "pending_future_quotes are incomplete observation windows.",
                "required_followup": ["review_source_quality"],
            },
            {
                "review_id": "scalp_entry_adm_status_warning",
                "domain": "scalping",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "Entry ADM status is warning with joined sample below floor.",
                "required_followup": ["review_source_quality"],
            },
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["code_improvement_orders"] == []
    assert {
        item["source_context_resolution"]["status"]
        for item in report["ai_two_pass_review"]["final_conclusions"]
    } == {"resolved_by_classified_source_quality_warning"}


def test_pattern_lab_ai_review_resolves_lifecycle_drift_from_source_wrapper(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
        },
    )
    for label in (
        "lifecycle_decision_matrix",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
        "code_improvement_workorder",
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
            "warnings": ["lifecycle_bucket_discovery:source_contract_drift_warning"],
        },
    )
    _write_json(
        report_dir
        / "lifecycle_bucket_discovery"
        / "lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "warnings": ["source_contract_drift_warning"],
            "summary": {"source_contract_status": "warning", "status": "pass"},
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["lifecycle_bucket_discovery_source_contract_drift"],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "lifecycle_bucket_discovery_source_contract_drift",
                "domain": "cross_domain",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "source_contract_drift_warning remains source-only warning.",
            },
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert (
        conclusion["source_context_resolution"]["status"]
        == "resolved_by_classified_source_quality_warning"
    )


def test_pattern_lab_ai_review_resolves_generic_source_report_warning_ids(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 6,
                "missing_feedback_source_count": 0,
            },
            "checks": [
                {
                    "check_id": "pattern_lab_ai_review_contract",
                    "status": "pass",
                }
            ],
        },
    )
    for label in (
        "lifecycle_decision_matrix",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
        "code_improvement_workorder",
        "pattern_lab_propagation_audit",
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
                "scalp_entry_adm:joined_sample_below_sample_floor",
                "lifecycle_bucket_discovery:source_contract_drift_warning",
                "swing_strategy_discovery:pending_future_quotes",
                "producer_gap_discovery_ai_review_followup_required",
            ],
            "summary": {
                "status": "warning",
                "primary_verdict": "sim_evidence_present_no_live_bucket",
                "live_auto_ready_count": 0,
                "runtime_effect": False,
            },
        },
    )
    _write_json(
        report_dir
        / "lifecycle_bucket_discovery"
        / "lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": ["source_contract_drift_warning"],
            "summary": {"status": "pass", "source_contract_status": "warning"},
        },
    )
    _write_json(
        report_dir
        / "swing_strategy_discovery_ev"
        / "swing_strategy_discovery_ev_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": ["pending_future_quotes"],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": [
                "source_quality_gap: scalping_pattern_lab_automation has scalp_entry_adm_status_warning",
                "source_quality_gap: lifecycle_bucket_discovery has source_contract_drift_warning",
                "source_quality_gap: swing_strategy_discovery_ev has pending_future_quotes",
                "automation_handoff_gap: threshold_cycle_ev has sim_evidence_present_no_live_bucket",
                "ai_review_gap",
            ],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "ai_review_gap",
                "domain": "scalping",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "Missing AI review contract in scalping pattern lab.",
            },
            {
                "review_id": "scalping_pattern_lab_automation",
                "domain": "scalping",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "scalp_entry_adm_joined_sample=18 below sample_floor",
            },
            {
                "review_id": "lifecycle_bucket_discovery",
                "domain": "cross_domain",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "source_contract_status=warning",
            },
            {
                "review_id": "swing_strategy_discovery_ev",
                "domain": "swing",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "pending_future_quotes",
            },
            {
                "review_id": "threshold_cycle_ev",
                "domain": "cross_domain",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "sim_evidence_present_no_live_bucket",
            },
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["code_improvement_orders"] == []
    resolution_statuses = {
        (
            item.get("source_context_resolution")
            or item.get("feedback_handoff_resolution")
            or {}
        ).get("status")
        for item in report["ai_two_pass_review"]["final_conclusions"]
    }
    assert resolution_statuses == {
        "resolved_by_currentness_ai_review_contract_pass",
        "resolved_by_classified_source_quality_warning",
        "resolved_by_classified_threshold_ev_source_only_warnings",
    }


def test_pattern_lab_ai_review_generic_resolution_ids_exclude_specific_source_gaps():
    assert "ai_review_two_pass_missing" not in mod.GENERIC_FEEDBACK_HANDOFF_REVIEW_IDS
    assert "ai_two_pass_review_missing" not in mod.GENERIC_FEEDBACK_HANDOFF_REVIEW_IDS
    assert (
        "threshold_cycle_ev_source_contract_drift_warning"
        not in mod.GENERIC_FEEDBACK_HANDOFF_REVIEW_IDS
    )


def test_pattern_lab_ai_review_resolves_swing_ai_review_missing_when_no_sim_auto_candidates(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert (
        conclusion["source_context_resolution"]["status"]
        == "resolved_by_source_only_sim_auto_review_contract"
    )


def test_pattern_lab_ai_review_resolves_swing_ai_review_missing_when_sim_auto_candidates_reviewed(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "source_contract_status": "pass",
                "ai_fail_closed": False,
                "ai_review_followup_required": False,
                "sim_auto_blocked_by_ai_review_followup": False,
                "pre_review_sim_auto_candidate_count": 24,
                "sim_auto_unreviewed_candidate_count": 0,
                "sim_auto_downgraded_by_review_count": 0,
                "sim_auto_policy_audited": True,
                "ai_reviewed_candidate_count": 24,
            },
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["ai_review_gap_missing_contract"],
            "forbidden_use_violations": [],
            "reason": "AI over-classified reviewed source-only swing AI review coverage.",
        },
        "final_conclusions": [
            {
                "review_id": "ai_review_gap_missing_contract",
                "domain": "swing",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "AI two-pass review incomplete: swing_lifecycle_bucket_discovery candidates include deferred items.",
                "required_followup": ["review_ai_contract"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert (
        conclusion["source_context_resolution"]["status"]
        == "resolved_by_source_only_sim_auto_review_contract"
    )


def test_pattern_lab_ai_review_keeps_swing_ai_review_missing_when_sim_auto_candidates_unreviewed(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "warning"
    assert report["summary"]["audit_status"] == "correction_required"
    assert any(
        order["review_id"] == "ai_review_two_pass_missing"
        for order in report["code_improvement_orders"]
    )
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "ai_review_gap"
    assert "source_context_resolution" not in conclusion


def test_pattern_lab_ai_review_resolves_threshold_ev_incomplete_with_classified_source_only_warnings(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert (
        conclusion["source_context_resolution"]["status"]
        == "resolved_by_classified_threshold_ev_source_only_warnings"
    )


def test_pattern_lab_ai_review_resolves_current_source_only_warning_set(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 8,
                "missing_feedback_source_count": 0,
            },
            "checks": [
                {"check_id": "pattern_lab_ai_review_contract", "status": "pass"},
            ],
        },
    )
    _write_json(
        report_dir
        / "scalping_pattern_lab_automation"
        / "scalping_pattern_lab_automation_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        },
    )
    _write_json(
        report_dir
        / "lifecycle_decision_matrix"
        / "lifecycle_decision_matrix_2026-05-15.json",
        {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
    )
    _write_json(
        report_dir
        / "lifecycle_bucket_discovery"
        / "lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": ["source_contract_drift_warning"],
            "summary": {
                "source_contract_status": "warning",
                "status": "pass",
                "code_patch_required_count": 0,
            },
        },
    )
    _write_json(
        report_dir
        / "swing_strategy_discovery_ev"
        / "swing_strategy_discovery_ev_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": [
                "pending_future_quotes",
                "clean_tuning_baseline_swing_discovery_lookback_filtered",
            ],
        },
    )
    _write_json(
        report_dir
        / "swing_lifecycle_decision_matrix"
        / "swing_lifecycle_decision_matrix_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": [
                "swing_intraday_live_equiv_probe_missing",
                "pending_future_quotes",
                "clean_tuning_baseline_swing_discovery_lookback_filtered",
            ],
        },
    )
    _write_json(
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "source_contract_status": "pass",
                "code_patch_required_count": 2,
                "implemented_code_improvement_workorder_ids": ["a", "b"],
                "pending_code_improvement_workorder_ids": [],
            },
        },
    )
    _write_json(
        report_dir / "threshold_cycle_ev" / "threshold_cycle_ev_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "warnings": [
                "scalp_entry_adm:ai_numeric_consistency_rows_excluded_from_aggregates",
                "lifecycle_bucket_discovery:source_contract_drift_warning",
                "swing_strategy_discovery:pending_future_quotes",
                "swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered",
                "swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing",
                "swing_lifecycle_decision_matrix:pending_future_quotes",
                "swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered",
                "scalp_entry_adm:joined_sample_below_sample_floor",
                "scalp_entry_adm:unknown_bucket_source_quality_gap",
                "pattern_lab_ai_review_warning",
                "pattern_lab_ai_review_ai_review_followup_required",
                "pattern_lab_propagation_audit_warning",
            ],
        },
    )
    _write_json(
        report_dir
        / "code_improvement_workorder"
        / "code_improvement_workorder_2026-05-15.json",
        {
            "status": "pass",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "orders": [],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["source_quality_gap:5", "ai_review_gap:1"],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "ai_two_pass_review_incomplete",
                "domain": "scalping",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "AI two-pass review is incomplete.",
            },
            {
                "review_id": "source-quality",
                "domain": "scalping",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "The warning status in the scalping entry admission metric indicates a data quality problem.",
            },
            {
                "review_id": "source-quality",
                "domain": "scalping",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "The source contract drift in lifecycle_bucket_discovery is a source-quality issue.",
            },
            {
                "review_id": "swing_strategy_discovery_pending_future_quotes",
                "domain": "swing",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "pending future quotes.",
            },
            {
                "review_id": "swing_lifecycle_decision_matrix_warnings",
                "domain": "swing",
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "reason": "The pending future quotes and missing intraday live probe are instrumentation gaps.",
            },
            {
                "review_id": "missing_code_improvement_workorder",
                "domain": "swing",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "Gap in code improvement workorder handoff.",
            },
            {
                "review_id": "ai_review_followup_2026_06_24",
                "domain": "scalping",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "AI review follow-up required per code_improvement_workorder warnings.",
            },
            {
                "review_id": "automation_handoff_gap",
                "domain": "swing",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "49 code patches are required in swing lifecycle bucket discovery before automation can proceed.",
            },
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    assert {
        item["final_state"]
        for item in report["ai_two_pass_review"]["final_conclusions"]
    } == {"source_only_keep_collecting"}


def test_pattern_lab_ai_review_marks_same_run_late_bound_sources_as_source_only(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 8,
                "missing_feedback_source_count": 0,
            },
            "checks": [
                {"check_id": "pattern_lab_ai_review_contract", "status": "pass"},
            ],
        },
    )
    for name in (
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / name / f"{name}_2026-05-15.json",
            {"status": "pass", "runtime_effect": False, "allowed_runtime_apply": False},
        )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["automation_handoff_gap:1", "ai_review_gap:1"],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "automation_handoff_gap",
                "domain": "scalping",
                "final_state": "automation_handoff_gap",
                "final_decision": "block_runtime_use",
                "reason": "Missing code_improvement_workorder and threshold_cycle_ev sources break the automation handoff.",
            },
            {
                "review_id": "ai_review_gap",
                "domain": "scalping",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "No AI review contract or output found despite passing pattern_lab_ai_review_contract check. Two-pass review process not implemented.",
            },
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    assert set(
        report["feedback_handoff_summary"]["missing_late_bound_source_labels"]
    ) == {
        "threshold_cycle_ev",
        "code_improvement_workorder",
    }
    assert {
        item["final_state"]
        for item in report["ai_two_pass_review"]["final_conclusions"]
    } == {"source_only_keep_collecting"}


def test_pattern_lab_ai_review_normalizes_keep_decision_gap_state(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 0,
                "missing_feedback_source_count": 0,
            },
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "pass"},
        "audit": {"status": "pass", "issues": [], "forbidden_use_violations": []},
        "final_conclusions": [
            {
                "review_id": "ai_review_gap",
                "domain": "scalping",
                "final_state": "ai_review_gap",
                "final_decision": "keep",
                "reason": "No new source-only work remains.",
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["final_decision"] == "keep"
    assert conclusion["auditor_pass"] is True
    assert report["summary"]["state_counts"] == {"source_only_keep_collecting": 1}


def test_pattern_lab_ai_review_resolves_generic_instrumentation_gap_with_workorder_ledger(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
        {
            "status": "pass",
            "summary": {
                "consumed_feedback_source_count": 8,
                "missing_feedback_source_count": 0,
            },
        },
    )
    for name in (
        "scalping_pattern_lab_automation",
        "swing_pattern_lab_automation",
        "threshold_cycle_ev",
        "code_improvement_workorder",
        "lifecycle_decision_matrix",
        "lifecycle_bucket_discovery",
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_bucket_discovery",
        "swing_strategy_discovery_ev",
    ):
        _write_json(
            report_dir / name / f"{name}_2026-05-15.json",
            {
                "status": "pass",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "summary": {},
            },
        )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["code_patch_required:1"],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "instrumentation_gap",
                "domain": "scalping",
                "final_state": "code_patch_required",
                "final_decision": "block_runtime_use",
                "reason": "scalping_pattern_lab_automation reports code improvement orders; no confirmation of implementation status.",
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["source_context_resolution"]["status"] == (
        "resolved_by_current_code_improvement_workorder_self_reference"
    )


def test_pattern_lab_ai_review_keeps_threshold_ev_incomplete_on_unclassified_warning(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "warning"
    assert any(
        order["review_id"] == "threshold_cycle_ev_incomplete"
        for order in report["code_improvement_orders"]
    )
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "automation_handoff_gap"
    assert "source_context_resolution" not in conclusion


def test_pattern_lab_ai_review_keeps_forbidden_use_gap_when_feedback_sources_closed(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir
        / "pattern_lab_currentness_audit"
        / "pattern_lab_currentness_audit_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "warning"
    assert report["summary"]["audit_status"] == "correction_required"
    assert report["ai_two_pass_review"]["audit"]["forbidden_use_violations"] == [
        "runtime env apply"
    ]
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "automation_handoff_gap"
    assert "feedback_handoff_resolution" not in conclusion


def test_pattern_lab_ai_review_accepts_strict_ai_response_with_audit(
    tmp_path, monkeypatch
):
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["ai_two_pass_review_status"] == "parsed"
    assert report["summary"]["audit_status"] == "pass"
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["auditor_pass"] is True
    assert conclusion["explicit_gap_type"] is None
    assert conclusion["forbidden_runtime_uses"] == mod.FORBIDDEN_USES
    assert report["code_improvement_orders"] == []


def test_pattern_lab_ai_review_does_not_retry_parsed_audit_correction(
    tmp_path, monkeypatch
):
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
        }, {
            "provider": "openai",
            "status": "success",
            **config.provider_status_fields(),
        }

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)

    report = mod.build_pattern_lab_ai_review_report("2026-05-15", provider="openai")

    assert [call.reasoning_effort for call in calls] == ["medium"]
    assert report["summary"]["ai_review_followup_required"] is False
    assert (
        report["summary"]["generic_ai_review_followup_resolved_by_concrete_orders"]
        is True
    )
    assert report["ai_two_pass_review"]["provider_status"]["retry_attempted"] is False
    assert any(
        order["improvement_type"] == "source_quality_gap"
        for order in report["code_improvement_orders"]
    )
    assert not any(
        order["improvement_type"] == "ai_review_followup"
        for order in report["code_improvement_orders"]
    )


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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["summary"]["ai_review_followup_required"] is False
    assert report["code_improvement_orders"] == []


def test_pattern_lab_ai_review_keeps_empty_correction_audit_when_gap_remains(
    tmp_path, monkeypatch
):
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["summary"]["audit_status"] == "correction_required"
    assert any(
        order["order_id"]
        == "order_pattern_lab_ai_review_threshold_cycle_ev_source_contract_drift_warning"
        for order in report["code_improvement_orders"]
    )


def test_pattern_lab_ai_review_resolves_implemented_swing_micro_context_contract(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir
        / "swing_pattern_lab_automation"
        / "swing_pattern_lab_automation_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["final_decision"] == "keep"
    assert (
        conclusion["source_contract_resolution"]["status"]
        == "resolved_by_implemented_source_contract"
    )


def test_pattern_lab_ai_review_resolves_closed_swing_lifecycle_bucket_discovery_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["status"] == "pass"
    assert report["summary"]["audit_status"] == "pass"
    assert report["code_improvement_orders"] == []
    conclusion = report["ai_two_pass_review"]["final_conclusions"][0]
    assert conclusion["final_state"] == "source_only_keep_collecting"
    assert conclusion["final_decision"] == "keep"
    assert (
        conclusion["source_contract_resolution"]["contract_id"]
        == "swing_lifecycle_bucket_discovery_code_patch_triage"
    )


def test_pattern_lab_ai_review_keeps_unresolved_swing_lifecycle_bucket_discovery_gap(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
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

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    assert report["summary"]["audit_status"] == "correction_required"
    assert any(
        order["order_id"]
        == "order_pattern_lab_ai_review_order_pattern_lab_ai_review_swing_lifecycle_bucket_discovery"
        and order["improvement_type"] == "code_patch_required"
        for order in report["code_improvement_orders"]
    )


def test_pattern_lab_ai_review_marks_swing_partial_ai_gap_as_implemented_source_only(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "ai_two_pass_review_status": "partial",
                "sim_auto_review_shard_count": 2,
                "sim_auto_reviewed_candidate_count": 14,
                "sim_auto_unreviewed_candidate_count": 20,
                "sim_auto_downgraded_by_review_count": 20,
                "ai_review_followup_required": True,
                "ai_review_followup_reasons": ["audit_status_missing"],
            },
            "warnings": [],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["ai_review_gap:1"],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "swing_lifecycle_bucket_discovery_ai_two_pass_partial",
                "domain": "swing",
                "final_state": "ai_review_gap",
                "final_decision": "surface_workorder",
                "reason": "AI two-pass review is partial and leaves an unreviewed Swing candidate set.",
                "source_context_resolution": {
                    "source_summary": {
                        "ai_two_pass_review_status": "partial",
                        "sim_auto_review_shard_count": 2,
                        "sim_auto_reviewed_candidate_count": 14,
                        "sim_auto_unreviewed_candidate_count": 20,
                        "sim_auto_downgraded_by_review_count": 20,
                        "ai_review_followup_required": True,
                        "ai_review_followup_reasons": ["audit_status_missing"],
                    }
                },
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    order = next(
        item
        for item in report["code_improvement_orders"]
        if item["order_id"]
        == "order_pattern_lab_ai_review_swing_lifecycle_bucket_discovery_ai_two_pass_partial"
    )
    assert order["implementation_status"] == "implemented"
    assert order["implementation_provenance"]["implementation_type"] == (
        "pattern_lab_swing_bucket_ai_two_pass_partial_provenance"
    )
    assert order["implementation_provenance"]["sim_auto_reviewed_candidate_count"] == 14
    assert order["implementation_provenance"]["runtime_effect"] is False


def test_pattern_lab_ai_review_marks_swing_ai_two_pass_incomplete_as_implemented_source_only(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "ai_two_pass_review_status": "partial",
                "sim_auto_review_shard_count": 2,
                "sim_auto_reviewed_candidate_count": 13,
                "sim_auto_unreviewed_candidate_count": 20,
                "sim_auto_downgraded_by_review_count": 20,
                "ai_review_followup_required": True,
                "ai_review_followup_reasons": ["audit_status_missing"],
            },
            "warnings": [],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["ai_review_gap:1"],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "swing_ai_two_pass_review_incomplete",
                "domain": "swing",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "AI two-pass review incomplete for source-only Swing follow-up.",
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    order = next(
        item
        for item in report["code_improvement_orders"]
        if item["order_id"]
        == "order_pattern_lab_ai_review_swing_ai_two_pass_review_incomplete"
    )
    assert order["implementation_status"] == "implemented"
    assert order["implementation_provenance"]["implementation_type"] == (
        "pattern_lab_swing_ai_two_pass_followup_provenance"
    )


def test_pattern_lab_ai_review_marks_generic_swing_ai_gap_as_source_only_two_pass_provenance(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)

    _write_json(
        report_dir
        / "swing_lifecycle_bucket_discovery"
        / "swing_lifecycle_bucket_discovery_2026-05-15.json",
        {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "summary": {
                "ai_two_pass_review_status": "parsed",
                "sim_auto_review_shard_count": 3,
                "sim_auto_reviewed_candidate_count": 43,
                "sim_auto_unreviewed_candidate_count": 0,
                "sim_auto_downgraded_by_review_count": 0,
                "ai_unreviewed_candidate_count": 627,
                "missing_ai_tier2_proposal_count": 627,
                "ai_review_optional_deferred_candidate_count": 47,
                "ai_review_optional_deferred_shard_count": 2,
                "ai_review_followup_required": False,
                "ai_review_followup_reasons": [],
            },
            "warnings": [],
        },
    )
    raw_response = {
        "schema_version": 1,
        "interpretation": {"review_items": [], "source_feedback_status": "warning"},
        "audit": {
            "status": "correction_required",
            "issues": ["ai_review_gap:1"],
            "forbidden_use_violations": [],
        },
        "final_conclusions": [
            {
                "review_id": "ai_review_gap",
                "domain": "swing",
                "final_state": "ai_review_gap",
                "final_decision": "block_runtime_use",
                "reason": "Broad Swing candidates remain deferred while critical sim-auto candidates were reviewed.",
                "source_paths": ["/tmp/swing_lifecycle_bucket_discovery.json"],
            }
        ],
    }

    report = mod.build_pattern_lab_ai_review_report(
        "2026-05-15", provider="openai", ai_raw_response=raw_response
    )

    order = next(
        item
        for item in report["code_improvement_orders"]
        if item["order_id"] == "order_pattern_lab_ai_review_ai_review_gap"
    )
    assert order["implementation_status"] == "implemented"
    provenance = order["implementation_provenance"]
    assert (
        provenance["implementation_type"]
        == "pattern_lab_swing_generic_ai_gap_two_pass_provenance"
    )
    assert provenance["sim_auto_unreviewed_candidate_count"] == 0
    assert provenance["ai_unreviewed_candidate_count"] == 627
    assert provenance["missing_ai_tier2_proposal_count"] == 627
    assert provenance["runtime_effect"] is False


def test_pattern_lab_ai_review_marks_recursive_workorder_review_id_as_implemented_source_only():
    status, provenance = mod._implementation_marker_for_conclusion(
        {
            "review_id": "order_pattern_lab_ai_review_swing_lifecycle_bucket_discovery",
            "final_state": "code_patch_required",
            "final_decision": "surface_workorder",
            "explicit_gap_type": "code_patch_required",
            "auditor_pass": True,
            "source_paths": ["/tmp/swing_lifecycle_bucket_discovery.json"],
        },
        {},
    )

    assert status == "implemented"
    assert provenance["normalized_review_id"] == "swing_lifecycle_bucket_discovery"
    assert provenance["runtime_effect"] is False
    assert provenance["allowed_runtime_apply"] is False
    assert provenance["requires_separate_runtime_apply_candidate"] is True


def test_pattern_lab_ai_review_marks_report_only_source_quality_reviews_as_implemented():
    for review_id in (
        "threshold_cycle_ev",
        "pattern_lab_propagation_audit",
        "lifecycle_decision_matrix",
        "lifecycle_decision_matrix_source_quality_blocked",
        "order_pattern_lab_ai_review_source_quality_gap",
    ):
        status, provenance = mod._implementation_marker_for_conclusion(
            {
                "review_id": review_id,
                "final_state": "source_quality_gap",
                "final_decision": "block_runtime_use",
                "explicit_gap_type": "source_quality_gap",
                "auditor_pass": False,
                "source_paths": [f"/tmp/{review_id}.json"],
            },
            {},
        )

        assert status == "implemented"
        expected_review_id = (
            "source_quality_gap"
            if review_id == "order_pattern_lab_ai_review_source_quality_gap"
            else review_id
        )
        assert provenance["normalized_review_id"] == expected_review_id
        assert provenance["runtime_effect"] is False
        assert provenance["allowed_runtime_apply"] is False
        assert provenance["requires_separate_runtime_apply_candidate"] is True


def test_pattern_lab_ai_review_keeps_sample_warning_followup_visible():
    status, provenance = mod._implementation_marker_for_conclusion(
        {
            "review_id": "scalp_entry_adm_source_quality",
            "final_state": "source_quality_gap",
            "final_decision": "block_runtime_use",
            "explicit_gap_type": "source_quality_gap",
            "auditor_pass": False,
            "source_paths": ["/tmp/scalp_entry_action_decision_matrix.json"],
        },
        {},
    )

    assert status == "implemented_but_waiting_sample"
    assert provenance["normalized_review_id"] == "scalp_entry_adm_source_quality"
    assert provenance["root_cause_closure_status_hint"] == (
        "handoff_closed_root_cause_open"
    )
    assert provenance["runtime_effect"] is False
    assert provenance["allowed_runtime_apply"] is False


def test_pattern_lab_ai_review_marks_present_propagation_audit_missing_review_as_implemented():
    status, provenance = mod._implementation_marker_for_conclusion(
        {
            "review_id": "pattern_lab_propagation_audit_missing",
            "final_state": "ai_review_gap",
            "final_decision": "block_runtime_use",
            "explicit_gap_type": "ai_review_gap",
            "auditor_pass": False,
            "source_paths": ["/tmp/pattern_lab_propagation_audit.json"],
        },
        {
            "feedback_handoff_summary": {"status": "pass"},
            "sources": {
                "pattern_lab_propagation_audit": {
                    "exists": True,
                    "status": "warning",
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "summary": {"warning_count": 2},
                }
            },
        },
    )

    assert status == "implemented"
    assert provenance["source_report_type"] == "pattern_lab_propagation_audit"
    assert provenance["source_warning_count"] == 2
    assert provenance["runtime_effect"] is False
    assert provenance["allowed_runtime_apply"] is False


def test_pattern_lab_ai_review_marks_workorder_duplicate_warnings_as_source_only_provenance():
    status, provenance = mod._implementation_marker_for_conclusion(
        {
            "review_id": "code_improvement_workorder_duplicate_orders",
            "final_state": "source_quality_gap",
            "final_decision": "block_runtime_use",
            "source_paths": ["/tmp/code_improvement_workorder.json"],
        },
        {
            "sources": {
                "code_improvement_workorder": {
                    "summary": {
                        "summary": {
                            "duplicate_order_warnings": [
                                "duplicate_order_id=order_a source=swing_lifecycle_bucket_discovery"
                            ]
                        }
                    }
                }
            }
        },
    )

    assert status == "implemented"
    assert (
        provenance["implementation_type"]
        == "pattern_lab_code_improvement_workorder_duplicate_warning_provenance"
    )
    assert provenance["duplicate_order_warning_count"] == 1
    assert provenance["runtime_effect"] is False
