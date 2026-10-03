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

    assert report["status"] == "summary_verified"
    assert report["whole_native_chain_done_claimed"] is False
    assert report["full_wrapper_rerun_used"] is False
    assert report["common_tuning_recovery_retired"] is True
    assert report["actions"] == [
        "runtime_approval_summary_refreshed",
        "next_stage2_checklist_refreshed",
        "direct_postclose_verification_refreshed",
    ]


def test_controller_does_not_promote_main_scope_to_whole_chain_done(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", data / "report" / "postclose_done_controller")
    _write(mod._status_path("2026-09-19"), {"status": "succeeded"})
    from src.engine.automation import postclose_summary_handoff as handoff
    monkeypatch.setattr(handoff, "producer_receipt_issues", lambda *a: [])
    monkeypatch.setattr(mod, "build_runtime_approval_summary", lambda *a: {})
    monkeypatch.setattr(mod, "build_next_stage2_checklist", lambda *a: {})
    strict_path = tmp_path / "strict.json"
    _write(strict_path, {"status": "pass"})
    monkeypatch.setattr(mod, "_write_verification_receipts", lambda date, report, invocation: (
        {**report, "verification_attempt": {"path": str(strict_path)}}, None, None, strict_path
    ))
    monkeypatch.setattr(mod, "current_strict_receipt_issues", lambda *a, **k: [])
    monkeypatch.setattr(mod, "build_threshold_cycle_postclose_verification", lambda *a, **k: {
        "status": "pass", "issues": [], "verification_scope": "main_terminal",
        "whole_native_chain_done_claimed": False,
    })
    report = mod.build_postclose_done_controller(
        "2026-09-19", require_independent_producers=True
    )
    assert report["status"] == "summary_verified"
    assert report["whole_native_chain_done_claimed"] is False
    monkeypatch.setattr(mod, "build_threshold_cycle_postclose_verification", lambda *a, **k: {
        "status": "pass", "issues": [], "verification_scope": "whole_native_chain",
        "whole_native_chain_done_claimed": True,
    })
    report = mod.build_postclose_done_controller(
        "2026-09-19", require_independent_producers=True
    )
    assert report["status"] == "done"
    monkeypatch.setattr(mod, "current_strict_receipt_issues", lambda *a, **k: [
        "strict_stage_generation_stale:research_capacity"
    ])
    report = mod.build_postclose_done_controller(
        "2026-09-19", require_independent_producers=True
    )
    assert report["status"] == "blocked_direct_evidence_gap"
    assert "strict_stage_generation_stale:research_capacity" in report["blocked_reasons"]


def test_controller_blocks_before_summary_when_predecessor_not_succeeded(monkeypatch, tmp_path):
    data = tmp_path / "data"
    monkeypatch.setattr(mod, "DATA_DIR", data)
    monkeypatch.setattr(mod, "REPORT_DIR", data / "report" / "postclose_done_controller")

    report = mod.build_postclose_done_controller("2026-09-19")

    assert report["status"] == "blocked_predecessor_not_succeeded"
    assert report["actions"] == []


def test_controller_materializes_required_cancel_tower_and_detector_accepts_it(monkeypatch, tmp_path):
    from src.tests.test_error_detector_artifact_freshness import _cancel_wait_consumer_fixture
    from src.engine.error_detectors.artifact_freshness import _entry_cancel_wait_result_semantics
    from src.engine.automation import tuning_performance_control_tower as tower
    paths = _cancel_wait_consumer_fixture(tmp_path, monkeypatch)
    paths['tower'].unlink()
    data = tmp_path / 'data'
    monkeypatch.setattr(mod, 'DATA_DIR', data)
    monkeypatch.setattr(mod, 'REPORT_DIR', data / 'report/postclose_done_controller')
    monkeypatch.setattr(tower, 'DATA_DIR', data)
    monkeypatch.setattr(tower, 'REPORT_ROOT_DIR', data / 'report')
    monkeypatch.setattr(tower, 'REPORT_DIR', paths['tower'].parent)
    monkeypatch.setattr(mod, 'build_runtime_approval_summary',
                        lambda day: json.loads(paths['summary'].read_text()))
    monkeypatch.setattr(mod, 'build_next_stage2_checklist', lambda day: {})
    monkeypatch.setattr(mod, 'build_threshold_cycle_postclose_verification',
                        lambda *a, **k: {'status': 'pass', 'issues': []})
    monkeypatch.setattr(mod, '_write_verification_receipts',
                        lambda day, report, invocation: (report, None, None, None))
    report = mod.build_postclose_done_controller('2026-10-02')
    assert report['status'] == 'summary_verified'
    assert report['actions'].index('direct_control_tower_refreshed') < report['actions'].index('next_stage2_checklist_refreshed')
    result = _entry_cancel_wait_result_semantics(tmp_path, '2026-10-02')
    assert result['findings'] == []
    assert result['consumers']['status'] == 'verified'


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


def test_finalizer_requires_fresh_whole_chain_done_attempt_receipt(tmp_path, monkeypatch):
    from datetime import datetime

    monkeypatch.setattr(mod, "DATA_DIR", tmp_path)
    report_path = tmp_path / "postclose_done_controller_2026-09-22.json"
    attempt_path = report_path.parent / "attempts" / "2026-09-22_attempt.json"
    verifier_path = tmp_path / "report" / "threshold_cycle_postclose_verification" / "attempts" / "2026-09-22" / "attempt.json"
    _write(verifier_path, {"status": "pass", "verification_scope": "whole_native_chain", "run_id": "run-1"})
    monkeypatch.setattr(mod, "current_strict_receipt_issues", lambda *a, **k: [])
    report = {
        "date": "2026-09-22",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "done",
        "whole_native_chain_done_claimed": True,
        "require_independent_producers": True,
        "final_verifier_status": "pass",
        "main_run_id": "run-1",
        "attempt_path": str(attempt_path),
        "verification_attempt_path": str(verifier_path),
        "verification_attempt_sha256": mod._sha(verifier_path),
    }
    _write(attempt_path, report)
    _write(report_path, report)

    assert mod.done_terminal_receipt_issues(
        report_path, "2026-09-22", started_after_ns=0
    ) == []
    verifier_path.write_text('{"status":"rewritten"}', encoding="utf-8")
    assert "controller_verification_attempt_missing_or_invalid" in mod.done_terminal_receipt_issues(
        report_path, "2026-09-22", started_after_ns=0
    )
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
