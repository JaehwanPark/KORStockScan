import json
from pathlib import Path

from src.engine.automation import postclose_done_controller as mod


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_controller_never_reruns_common_tuning_or_wrapper(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", data / "report" / "postclose_done_controller")
    _write(
        data / "report" / "threshold_cycle_postclose_status" / "threshold_cycle_postclose_2026-09-19.status.json",
        {"status": "succeeded"},
    )
    monkeypatch.setattr(
        mod,
        "build_runtime_approval_summary",
        lambda date: {"status": "direct_evidence_complete"},
    )
    monkeypatch.setattr(
        mod,
        "build_next_stage2_checklist",
        lambda date: {"task_count": 0},
    )
    monkeypatch.setattr(
        mod,
        "build_threshold_cycle_postclose_verification",
        lambda *args, **kwargs: {"status": "pass", "issues": []},
    )
    monkeypatch.setattr(mod, "_write_verification_receipts", lambda date, report, invocation: (report, None, None, None))

    report = mod.build_postclose_done_controller("2026-09-19", allow_wrapper_rerun=True)

    assert report["status"] == "done"
    assert report["full_wrapper_rerun_used"] is False
    assert report["common_tuning_recovery_retired"] is True
    assert report["actions"] == [
        "runtime_approval_summary_refreshed",
        "next_stage2_checklist_refreshed",
        "direct_postclose_verification_refreshed",
    ]


def test_controller_blocks_before_summary_when_predecessor_not_succeeded(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", data / "report" / "postclose_done_controller")

    report = mod.build_postclose_done_controller("2026-09-19")

    assert report["status"] == "blocked_predecessor_not_succeeded"
    assert report["actions"] == []


def test_controller_waits_for_running_predecessor_without_rerun(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", data / "report" / "postclose_done_controller")
    status_path = (
        data
        / "report"
        / "threshold_cycle_postclose_status"
        / "threshold_cycle_postclose_2026-09-21.status.json"
    )
    _write(status_path, {"status": "running", "run_id": "active"})

    def finish_predecessor(_seconds: float) -> None:
        _write(status_path, {"status": "succeeded", "run_id": "active"})

    monkeypatch.setattr(mod.time, "sleep", finish_predecessor)

    assert mod._wait_for_predecessor_succeeded(
        "2026-09-21", wait_sec=60, timeout_sec=43200
    ) is True
    assert json.loads(status_path.read_text())["run_id"] == "active"


def test_controller_predecessor_wait_times_out_without_mutation(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", data / "report" / "postclose_done_controller")

    assert mod._wait_for_predecessor_succeeded(
        "2026-09-21", wait_sec=60, timeout_sec=0
    ) is False
    assert not (data / "report" / "threshold_cycle_postclose_status").exists()


def test_finalizer_requires_fresh_whole_chain_done_attempt_receipt(tmp_path):
    from datetime import datetime

    report_path = tmp_path / "postclose_done_controller_2026-09-22.json"
    attempt_path = report_path.parent / "attempts" / "2026-09-22_attempt.json"
    report = {
        "date": "2026-09-22",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "done",
        "whole_native_chain_done_claimed": True,
        "require_independent_producers": True,
        "final_verifier_status": "pass",
        "attempt_path": str(attempt_path),
    }
    _write(attempt_path, report)
    _write(report_path, report)

    assert mod.done_terminal_receipt_issues(
        report_path, "2026-09-22", started_after_ns=0
    ) == []
    import time

    assert "controller_report_not_fresh_for_finalization" in mod.done_terminal_receipt_issues(
        report_path,
        "2026-09-22",
        started_after_ns=time.time_ns() + 1_000_000_000,
    )

    report["status"] = "summary_verified"
    _write(attempt_path, report)
    _write(report_path, report)
    assert "controller_report_not_done" in mod.done_terminal_receipt_issues(
        report_path, "2026-09-22", started_after_ns=0
    )
