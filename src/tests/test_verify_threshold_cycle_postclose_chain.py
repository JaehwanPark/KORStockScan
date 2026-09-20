import json
from pathlib import Path

from src.engine import runtime_approval_summary as summary_mod
from src.engine import verify_threshold_cycle_postclose_chain as mod
from src.engine import build_next_stage2_checklist as checklist_mod


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _seed(monkeypatch, tmp_path: Path, target: str):
    data = tmp_path / "data"
    report = data / "report"
    monkeypatch.setattr(summary_mod, "DATA_DIR", data)
    monkeypatch.setattr(summary_mod, "REPORT_DIR", report / "runtime_approval_summary")
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", report)
    monkeypatch.setattr(mod, "OUTPUT_DIR", report / "threshold_cycle_postclose_verification")
    for owner, path in summary_mod._paths(target).items():
        if owner in summary_mod.REQUIRED_DIRECT_OWNERS:
            _write(path, {"report_type": owner, "target_date": target, "status": "pass"})
    summary = summary_mod.build_runtime_approval_summary(target)
    status_path = report / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target}.status.json"
    proof = report / "proof.json"
    _write(proof, {"date": target, "status": "pass", "verification_scope": "main_precommit",
                   "run_id": "run-1", "code_commit": "a" * 40})
    _write(status_path, {"target_date": target, "status": "succeeded", "exit_code": 0,
                        "run_id": "run-1", "code_commit": "a" * 40,
                        "started_at": "2026-09-19T20:10:00+09:00", "finished_at": "2026-09-19T21:00:00+09:00",
                        "verification_receipt": {"path": str(proof), "sha256": mod._sha(proof)}})
    return summary


def _build_direct_checklist(monkeypatch, tmp_path: Path, target: str) -> Path:
    monkeypatch.setattr(checklist_mod, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(checklist_mod, "DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr(checklist_mod, "CHECKLIST_DIR", tmp_path / "docs" / "checklists")
    monkeypatch.setattr(checklist_mod, "CHECKLIST_LOCK_DIR", tmp_path / "locks")
    result = checklist_mod.build_next_stage2_checklist(target)
    return Path(result["path"])


def test_verifier_passes_without_retired_daily_ev_or_generic_preopen(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert report["status"] == "pass"
    assert report["issues"] == []
    assert report["retired_common_layers"] == [
        "daily_threshold_cycle_report",
        "threshold_cycle_ev_report",
        "threshold_cycle_preopen_apply",
    ]


def test_verifier_recomputes_direct_source_hash(monkeypatch, tmp_path):
    target = "2026-09-19"
    summary = _seed(monkeypatch, tmp_path, target)
    Path(summary["sources"]["entry_split"]["path"]).write_text("{}", encoding="utf-8")

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert report["status"] == "fail"
    assert "direct_source_hash_mismatch:entry_split" in report["issues"]


def test_optional_direct_receipt_may_be_absent(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)

    report = mod.build_threshold_cycle_postclose_verification(target)

    optional = next(row for row in report["direct_source_checks"] if row["owner"] == "entry_split_policy")
    assert optional["exists"] is False
    assert optional["required"] is False
    assert report["status"] == "pass"


def test_stale_optional_policy_blocks_only_family_handoff(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)
    _write(
        summary_mod._paths(target)["low_price_expansion_policy"],
        {"source_date": "2026-09-18", "allowed_runtime_apply": True},
    )
    summary = summary_mod.build_runtime_approval_summary(target)

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert summary["sources"]["low_price_expansion"]["economic_evidence"]["policy_handoff_state"] == "blocked"
    assert report["status"] == "pass"
    assert "direct_source_date_mismatch:low_price_expansion_policy" not in report["issues"]


def test_missing_postclose_terminal_fails_closed(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)
    (mod.REPORT_DIR / "threshold_cycle_postclose_status" / f"threshold_cycle_postclose_{target}.status.json").unlink()

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert report["status"] == "fail"
    assert "postclose_terminal_status_missing" in report["issues"]


def test_verifier_rejects_source_gap_marked_runtime_applyable(monkeypatch, tmp_path):
    target = "2026-09-19"
    summary = _seed(monkeypatch, tmp_path, target)
    summary["sources"]["entry_split"]["economic_evidence"].update(
        comparison_status="source_gap", policy_apply_allowed=True
    )
    _write(mod._artifact_paths(target)["runtime_summary"], summary)

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert report["status"] == "fail"
    assert "blocked_economic_source_marked_applyable:entry_split" in report["issues"]


def test_verifier_rejects_natural_acceptance_without_pid_receipt(
    monkeypatch, tmp_path
):
    target = "2026-09-19"
    summary = _seed(monkeypatch, tmp_path, target)
    summary["natural_acceptance_state"] = "pending"
    _write(mod._artifact_paths(target)["runtime_summary"], summary)

    report = mod.build_threshold_cycle_postclose_verification(target)

    assert report["status"] == "fail"
    assert any(
        issue.startswith("runtime_summary_contract_invalid:")
        and "natural acceptance lacks PID receipt" in issue
        for issue in report["issues"]
    )


def test_required_summary_handoff_verifies_marker_and_task_projection(
    monkeypatch, tmp_path
):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)
    checklist = _build_direct_checklist(monkeypatch, tmp_path, target)

    report = mod.build_threshold_cycle_postclose_verification(
        target, require_summary_handoff=True
    )

    assert report["status"] == "pass"
    assert report["checklist_handoff"]["status"] == "pass"
    assert report["checklist_handoff"]["path"] == str(checklist)
    assert (
        report["checklist_handoff"]["expected_task_ids"]
        == report["checklist_handoff"]["actual_task_ids"]
    )


def test_required_summary_handoff_rejects_task_projection_drift(
    monkeypatch, tmp_path
):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)
    checklist = _build_direct_checklist(monkeypatch, tmp_path, target)
    checklist.write_text(
        checklist.read_text(encoding="utf-8")
        + "\n- [ ] `[DirectFamilySourceRepairEntrySplit] stale task` "
        "(`Due: 2026-09-21`, `Slot: POSTCLOSE`, `TimeWindow: 16:30~21:40`, "
        "`Track: RuntimeStability`)\n",
        encoding="utf-8",
    )

    report = mod.build_threshold_cycle_postclose_verification(
        target, require_summary_handoff=True
    )

    assert report["status"] == "fail"
    assert "direct_checklist_task_projection_mismatch" in report["issues"]


def test_main_mechanistic_scope_rejects_compact_only_report(
    monkeypatch, tmp_path
):
    from src.engine.scalping import ai_action_outcome_calibration as calibration

    target = "2026-09-17"
    data = tmp_path / "data"
    report_root = data / "report"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", report_root)
    source = calibration._with_artifact_content_sha256(
        {
            "schema": calibration.SCHEMA,
            "target_date": target,
            "report_scope": "compact_auxiliary_only",
            "noncompact_sections_refreshed": False,
            "machine_full_evaluation": {},
        }
    )
    _write(
        report_root
        / "ai_decision_action_outcome_calibration"
        / f"ai_decision_action_outcome_calibration_{target}.json",
        source,
    )

    result = mod._main_mechanistic_scope(target)

    assert result["status"] == "fail"
    assert "main_machine_report_scope_invalid" in result["issues"]
    assert "main_machine_noncompact_refresh_missing" in result["issues"]
    assert "main_machine_future_policy_missing_or_ambiguous" in result["issues"]


def test_terminal_rejects_wrong_date_nonzero_exit_missing_identity_and_stale_proof(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)
    path = mod._artifact_paths(target)["postclose_status"]
    original = mod._load(path)
    for change, issue in [({"target_date": "2000-01-01"}, "postclose_terminal_date_mismatch"),
                          ({"exit_code": 17}, "postclose_terminal_exit_code_invalid"),
                          ({"run_id": "new-run"}, "postclose_terminal_verification_binding_invalid"),
                          ({"code_commit": None}, "postclose_terminal_code_missing"),
                          ({"verification_receipt": {}}, "postclose_terminal_verification_binding_invalid")]:
        _write(path, {**original, **change})
        result = mod.build_threshold_cycle_postclose_verification(target)
        assert result["status"] == "fail" and issue in result["issues"]


def test_attempts_never_overwrite_failure_and_preterminal_is_not_done(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)
    report = mod.build_threshold_cycle_postclose_verification(target, require_done_marker=False)
    assert report["completion_state"] == "preterminal_verified"
    assert report["whole_native_chain_done_claimed"] is False
    failed = {**report, "status": "fail", "issues": ["first_failure"]}
    _, _, _, first = mod._write_verification_receipts(target, failed, invocation={})
    original = first.read_bytes()
    _, _, _, second = mod._write_verification_receipts(target, report, invocation={})
    assert first != second and first.read_bytes() == original
    assert mod._load(first)["issues"] == ["first_failure"]


def test_cli_seals_only_current_precommit_after_checklist_verification(monkeypatch, tmp_path):
    target = "2026-09-19"
    _seed(monkeypatch, tmp_path, target)
    _build_direct_checklist(monkeypatch, tmp_path, target)
    path = mod._artifact_paths(target)["postclose_status"]
    before = mod._load(path)
    _write(path, {**before, "status": "producers_completed", "verification_receipt": None})
    assert mod.main(["--date", target, "--seal-main-run", "--expected-run-id", "other", "--require-summary-handoff"]) == 1
    assert mod._load(path)["status"] == "producers_completed"
    assert mod.main(["--date", target, "--seal-main-run", "--expected-run-id", "run-1", "--require-summary-handoff"]) == 0
    assert mod._load(path)["status"] == "succeeded"
    assert mod.build_threshold_cycle_postclose_verification(target, require_summary_handoff=True)["status"] == "pass"


def test_disabled_active_stage_is_not_an_escape_hatch(monkeypatch, tmp_path):
    _seed(monkeypatch, tmp_path, "2026-09-19")
    result = mod.build_threshold_cycle_postclose_verification("2026-09-19", disabled_stages={"entry_split"})
    assert "disabled_stage_not_allowed:entry_split" in result["issues"]
