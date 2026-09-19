import json
from pathlib import Path

from src.engine.automation import tuning_performance_control_tower as mod


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _patch_dirs(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    report_root = data_dir / "report"
    monkeypatch.setattr(mod, "DATA_DIR", data_dir)
    monkeypatch.setattr(mod, "REPORT_ROOT_DIR", report_root)
    monkeypatch.setattr(
        mod, "REPORT_DIR", report_root / "tuning_performance_control_tower"
    )
    return data_dir, report_root


def test_control_tower_reports_direct_evidence_without_fabricating_economics(
    monkeypatch, tmp_path
):
    _, report_root = _patch_dirs(monkeypatch, tmp_path)

    report = mod.build_tuning_performance_control_tower("2026-09-19")

    assert report["status"] == "direct_evidence_pending"
    assert report["summary"]["validated_improvement_count"] == 0
    assert report["summary"]["common_tuning_search_retired"] is True
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert "realized_pnl_krw" not in report["summary"]
    assert Path(mod.report_paths("2026-09-19")[0]).is_file()
    assert report_root in Path(mod.report_paths("2026-09-19")[0]).parents


def test_control_tower_binds_direct_generation_without_verifier_cycle(
    monkeypatch, tmp_path
):
    data_dir, report_root = _patch_dirs(monkeypatch, tmp_path)
    day = "2026-09-19"
    apply_day = "2026-09-21"
    _write(
        report_root / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json",
        {"date": day, "status": "direct_evidence_complete", "direct_evidence_state": "complete", "blocking_reasons": [], "economic_state": "measured_no_edge", "economic_state_counts": {"measured_no_edge": 1}, "validated_edge_count": 0, "policy_candidate_count": 0, "preopen_consumption_state": "verified", "natural_acceptance_state": "pending", "preopen_consumption_receipt": {"apply_date": apply_day}},
    )
    _write(
        report_root
        / "threshold_cycle_postclose_verification"
        / f"threshold_cycle_postclose_verification_{day}.json",
        {"date": day, "status": "pass", "issues": []},
    )
    _write(
        data_dir / "runtime" / "policy_bootstrap" / f"runtime_policy_bootstrap_{apply_day}.json",
        {
            "target_date": apply_day,
            "selected_families": ["entry_cancel_wait"],
            "selection_changes": [
                {"family": "entry_cancel_wait", "change_class": "retained_approved"}
            ],
        },
    )
    _write(
        data_dir
        / "runtime"
        / "policy_bootstrap"
        / f"runtime_policy_bootstrap_verify_{apply_day}.json",
        {"target_date": apply_day, "status": "pass", "pid": 123, "pid_passed": True},
    )

    report = mod.build_tuning_performance_control_tower(day)

    assert report["status"] == "pass"
    assert report["selected_runtime"]["selected_families"] == ["entry_cancel_wait"]
    assert report["selected_runtime"]["target_date"] == apply_day
    sources = report["source_generation_contract"]["sources"]
    assert set(sources) == {
        "runtime_approval_summary",
        "runtime_policy_bootstrap",
        "runtime_policy_bootstrap_verify",
    }
    assert "postclose_verifier" not in sources
    assert "threshold_cycle_ev" not in sources
