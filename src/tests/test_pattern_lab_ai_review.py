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
