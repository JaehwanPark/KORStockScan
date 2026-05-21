import json
from pathlib import Path

from src.engine import build_code_improvement_workorder as workorder_mod
from src.engine import pattern_lab_currentness_audit as currentness_mod
from src.engine import pattern_lab_propagation_audit as mod
from src.engine import runtime_approval_summary as runtime_mod
from src.engine import scalping_pattern_lab_automation as scalping_mod
from src.engine import swing_pattern_lab_automation as swing_mod
from src.engine import threshold_cycle_ev_report as ev_mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _patch_dirs(tmp_path: Path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    docs_dir = tmp_path / "docs" / "code-improvement-workorders"
    monkeypatch.setattr(mod, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(currentness_mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(scalping_mod, "PATTERN_LAB_AUTOMATION_DIR", report_dir / "scalping_pattern_lab_automation")
    monkeypatch.setattr(swing_mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")
    monkeypatch.setattr(workorder_mod, "CODE_IMPROVEMENT_WORKORDER_REPORT_DIR", report_dir / "code_improvement_workorder")
    monkeypatch.setattr(workorder_mod, "CODE_IMPROVEMENT_WORKORDER_DIR", docs_dir)
    monkeypatch.setattr(ev_mod, "EV_REPORT_DIR", report_dir / "threshold_cycle_ev")
    monkeypatch.setattr(runtime_mod, "SUMMARY_DIR", report_dir / "runtime_approval_summary")
    return report_dir


def _seed_propagation_chain(tmp_path: Path, report_dir: Path, target_date: str) -> None:
    scalping_path = report_dir / "scalping_pattern_lab_automation" / f"scalping_pattern_lab_automation_{target_date}.json"
    swing_path = report_dir / "swing_pattern_lab_automation" / f"swing_pattern_lab_automation_{target_date}.json"
    currentness_path = report_dir / "pattern_lab_currentness_audit" / f"pattern_lab_currentness_audit_{target_date}.json"
    workorder_path = report_dir / "code_improvement_workorder" / f"code_improvement_workorder_{target_date}.json"
    ev_path = report_dir / "threshold_cycle_ev" / f"threshold_cycle_ev_{target_date}.json"
    runtime_path = report_dir / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json"
    propagation_path = report_dir / "pattern_lab_propagation_audit" / f"pattern_lab_propagation_audit_{target_date}.json"
    ldm_path = report_dir / "lifecycle_decision_matrix" / f"lifecycle_decision_matrix_{target_date}.json"

    _write_json(
        scalping_path,
        {
            "date": target_date,
            "runtime_change": False,
            "ev_report_summary": {"gemini_fresh": True, "claude_fresh": True},
        },
    )
    _write_json(
        swing_path,
        {
            "date": target_date,
            "runtime_change": False,
            "ev_report_summary": {"deepseek_lab_available": True},
        },
    )
    _write_json(
        currentness_path,
        {
            "report_type": "pattern_lab_currentness_audit",
            "runtime_effect": False,
            "code_improvement_orders": [{"order_id": "order_currentness", "runtime_effect": False}],
        },
    )
    _write_json(
        workorder_path,
        {
            "source": {
                "pattern_lab_currentness_audit": str(currentness_path),
                "lifecycle_decision_matrix": str(ldm_path),
            },
            "summary": {
                "pattern_lab_currentness_source_order_count": 1,
                "lifecycle_entry_bucket_source_order_count": 0,
                "lifecycle_scale_in_bucket_source_order_count": 0,
                "lifecycle_overnight_bucket_source_order_count": 0,
            },
            "orders": [{"order_id": "order_currentness", "runtime_effect": False}],
        },
    )
    _write_json(
        ev_path,
        {
            "runtime_apply": {"runtime_change": False},
            "sources": {
                "pattern_lab_currentness_audit": str(currentness_path),
                "pattern_lab_propagation_audit": str(propagation_path),
                "lifecycle_decision_matrix": str(ldm_path),
            },
        },
    )
    _write_json(
        ldm_path,
        {
            "entry_bucket_attribution": {"code_improvement_workorders": []},
            "scale_in_bucket_attribution": {"code_improvement_workorders": []},
            "overnight_bucket_attribution": {"code_improvement_workorders": []},
        },
    )
    _write_json(
        runtime_path,
        {"sources": {"pattern_lab_propagation_audit": str(propagation_path)}},
    )
    _write_json(
        tmp_path / "analysis" / "deepseek_swing_pattern_lab" / "outputs" / "data_quality_report.json",
        {"sim_probe_provenance": {"sequence_fact_actual_order_submitted_false": 1}},
    )


def test_propagation_audit_passes_when_lineage_is_connected(tmp_path, monkeypatch):
    target_date = "2026-05-15"
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _seed_propagation_chain(tmp_path, report_dir, target_date)

    report = mod.build_pattern_lab_propagation_audit(target_date)

    assert report["status"] == "pass"
    assert report["summary"]["fail_count"] == 0
    assert report["runtime_effect"] is False
    assert (report_dir / "pattern_lab_propagation_audit" / f"pattern_lab_propagation_audit_{target_date}.json").exists()


def test_propagation_audit_fails_when_workorder_lineage_missing(tmp_path, monkeypatch):
    target_date = "2026-05-15"
    report_dir = _patch_dirs(tmp_path, monkeypatch)
    _seed_propagation_chain(tmp_path, report_dir, target_date)
    _write_json(
        report_dir / "code_improvement_workorder" / f"code_improvement_workorder_{target_date}.json",
        {"source": {}, "summary": {"pattern_lab_currentness_source_order_count": 0}},
    )

    report = mod.build_pattern_lab_propagation_audit(target_date)

    assert report["status"] == "fail"
    failed_ids = {check["check_id"] for check in report["checks"] if check["status"] == "fail"}
    assert "workorder_consumes_currentness_audit" in failed_ids
    assert "workorder_currentness_order_count" in failed_ids
    assert all(order["runtime_effect"] is False for order in report["code_improvement_orders"])
