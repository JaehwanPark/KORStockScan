import json
from pathlib import Path

from src.engine.automation import stage_hook_runtime_scaffold as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_stage_hook_runtime_scaffold_records_disabled_source_only_hooks(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "stage_hook_workorder_discovery" / "stage_hook_workorder_discovery_2026-05-26.json",
        {
            "status": "warning",
            "summary": {"ai_two_pass_review_status": "parsed", "audit_status": "pass"},
            "stage_hook_candidates": [
                {
                    "stage_hook_candidate_contract": {
                        "hook_name": "holding_flow_runner_debounce_guard",
                        "source_candidate_ids": ["producer_gap_sim_holding_runner_gap_missing"],
                    }
                },
                {
                    "stage_hook_candidate_contract": {
                        "hook_name": "plateau_breakdown_exit_arbitration_probe",
                        "source_candidate_ids": ["producer_gap_sim_exit_plateau_breakdown_gap_missing"],
                    }
                },
            ]
        },
    )

    report = mod.build_stage_hook_runtime_scaffold_report("2026-05-26")

    assert report["status"] == "pass"
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    hooks = {item["hook_name"]: item for item in report["implemented_hooks"]}
    assert set(hooks) == {"holding_flow_runner_debounce_guard", "plateau_breakdown_exit_arbitration_probe"}
    assert all(item["initial_runtime_state"] == "disabled" for item in hooks.values())
    assert all(item["requires_separate_runtime_apply_candidate"] is True for item in hooks.values())
    assert all(item["action_namespace_scope"] == "review_only_labels_not_runtime_actions" for item in hooks.values())


def test_stage_hook_runtime_scaffold_fails_closed_without_parsed_source(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_json(
        report_dir / "stage_hook_workorder_discovery" / "stage_hook_workorder_discovery_2026-05-26.json",
        {
            "status": "fail",
            "summary": {"ai_two_pass_review_status": "parse_rejected", "audit_status": "missing"},
            "stage_hook_candidates": [
                {
                    "stage_hook_candidate_contract": {
                        "hook_name": "holding_flow_runner_debounce_guard",
                        "source_candidate_ids": ["producer_gap_sim_holding_runner_gap_missing"],
                    }
                }
            ],
        },
    )

    report = mod.build_stage_hook_runtime_scaffold_report("2026-05-26")

    assert report["status"] == "fail"
    assert report["summary"]["source_contract_pass"] is False
    assert report["implemented_hooks"] == []
