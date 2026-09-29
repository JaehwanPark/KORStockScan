from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from src.engine.automation.postclose_finalization_generation import (
    FinalizationGenerationError,
    capture_final_detector_receipt,
    capture_finalization_generation,
    finalization_marker_issues,
)


DAY = "2026-09-28"


def _write_json(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, sort_keys=True) + "\n").encode()
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _fixture(root: Path) -> tuple[Path, Path]:
    report = root / "data/report"
    summary_sha = _write_json(
        report / "runtime_approval_summary" / f"runtime_approval_summary_{DAY}.json",
        {"date": DAY, "status": "complete"},
    )
    main_sha = _write_json(
        report / "threshold_cycle_postclose_status"
        / f"threshold_cycle_postclose_{DAY}.status.json",
        {"target_date": DAY, "run_id": "main-run"},
    )
    checklist_path = root / "docs/checklists" / f"{DAY}-next.md"
    checklist_path.parent.mkdir(parents=True, exist_ok=True)
    checklist_path.write_text("# Next day\n")
    checklist_sha = hashlib.sha256(checklist_path.read_bytes()).hexdigest()
    stage_sha = _write_json(
        report / "postclose_stage_terminal" / DAY / "research_capacity.json",
        {"source_date": DAY, "status": "succeeded"},
    )
    strict_dir = report / "threshold_cycle_postclose_verification"
    strict_attempt = strict_dir / "attempts" / DAY / "strict.json"
    strict = {
        "date": DAY,
        "status": "pass",
        "verification_scope": "whole_native_chain",
        "whole_native_chain_done_claimed": True,
        "run_id": "main-run",
        "checklist_handoff": {"path": str(checklist_path)},
        "generation_binding": {
            "source_date": DAY,
            "main_run_id": "main-run",
            "summary_sha256": summary_sha,
            "main_terminal_sha256": main_sha,
            "checklist_sha256": checklist_sha,
            "stages": {"research_capacity": {"sha256": stage_sha}},
        },
    }
    strict_sha = _write_json(strict_attempt, strict)
    _write_json(strict_dir / f"threshold_cycle_postclose_verification_{DAY}.json", strict)
    controller_dir = report / "postclose_done_controller"
    controller_attempt = controller_dir / "attempts" / f"{DAY}_attempt.json"
    controller = {
        "date": DAY,
        "status": "done",
        "whole_native_chain_done_claimed": True,
        "final_verifier_status": "pass",
        "main_run_id": "main-run",
        "attempt_path": str(controller_attempt),
        "verification_attempt_path": str(strict_attempt),
        "verification_attempt_sha256": strict_sha,
    }
    _write_json(controller_attempt, controller)
    _write_json(controller_dir / f"postclose_done_controller_{DAY}.json", controller)

    snapshots = report / "monitor_snapshots"
    paths = {}
    shas = {}
    for kind in ("trade_review", "post_sell_feedback", "holding_exit_observation"):
        path = snapshots / f"{kind}_{DAY}.json"
        shas[kind] = _write_json(path, {"date": DAY, "kind": kind})
        paths[kind] = str(path)
    manifest_path = snapshots / "manifests" / f"monitor_snapshot_manifest_{DAY}_postclose_exit.json"
    _write_json(manifest_path, {
        "target_date": DAY,
        "profile": "postclose_exit",
        "snapshot_kinds": sorted(paths),
        "snapshot_paths": paths,
        "snapshot_sha256": shas,
    })
    return strict_attempt, manifest_path


def test_finalization_rejects_new_strict_generation_after_old_done(tmp_path):
    strict_attempt, _ = _fixture(tmp_path)
    captured = capture_finalization_generation(tmp_path, DAY)
    assert finalization_marker_issues(
        tmp_path, DAY, captured["chain_sha256"], captured["snapshot_sha256"]
    ) == []

    strict = json.loads(strict_attempt.read_text())
    strict["generation_binding"]["summary_sha256"] = _write_json(
        tmp_path / "data/report/runtime_approval_summary"
        / f"runtime_approval_summary_{DAY}.json",
        {"date": DAY, "status": "regenerated"},
    )
    new_attempt = strict_attempt.with_name("new-strict.json")
    new_sha = _write_json(new_attempt, strict)
    _write_json(strict_attempt.parents[2] / f"threshold_cycle_postclose_verification_{DAY}.json", strict)
    controller_path = tmp_path / "data/report/postclose_done_controller" / f"postclose_done_controller_{DAY}.json"
    controller = json.loads(controller_path.read_text())
    controller["verification_attempt_path"] = str(new_attempt)
    controller["verification_attempt_sha256"] = new_sha
    new_controller = Path(controller["attempt_path"]).with_name(f"{DAY}_new.json")
    controller["attempt_path"] = str(new_controller)
    _write_json(new_controller, controller)
    _write_json(controller_path, controller)

    assert "finalization_chain_generation_changed" in finalization_marker_issues(
        tmp_path, DAY, captured["chain_sha256"], captured["snapshot_sha256"]
    )


def test_finalization_snapshot_archive_and_coexistence(tmp_path):
    _, manifest_path = _fixture(tmp_path)
    captured = capture_finalization_generation(tmp_path, DAY)
    snapshot = tmp_path / "data/report/monitor_snapshots" / f"post_sell_feedback_{DAY}.json"
    compressed = Path(f"{snapshot}.gz")
    with gzip.open(compressed, "wb") as stream:
        stream.write(snapshot.read_bytes())
    snapshot.unlink()
    assert capture_finalization_generation(tmp_path, DAY)["snapshot_sha256"] == captured["snapshot_sha256"]

    trade = tmp_path / "data/report/monitor_snapshots" / f"trade_review_{DAY}.json"
    with gzip.open(f"{trade}.gz", "wb") as stream:
        stream.write(b'{"date":"2026-09-27","kind":"trade_review"}\n')
    coexist = capture_finalization_generation(tmp_path, DAY)
    assert coexist["snapshot_sha256"] == captured["snapshot_sha256"]
    assert coexist["snapshot_modes"]["trade_review"] == "canonical_raw_with_excluded_archive"

    compressed.write_bytes(b"broken archive")
    with pytest.raises(FinalizationGenerationError, match="snapshot_archive_invalid"):
        capture_finalization_generation(tmp_path, DAY)
    assert manifest_path.exists()


def test_release_data_symlink_preserves_snapshot_owner(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _fixture(workspace)
    release = tmp_path / "release"
    release.mkdir()
    (release / "data").symlink_to(workspace / "data", target_is_directory=True)
    assert capture_finalization_generation(release, DAY)["snapshot_modes"]["trade_review"] == "canonical_raw"


def test_finalization_rejects_wrong_snapshot_date_even_with_matching_manifest_hash(tmp_path):
    _, manifest_path = _fixture(tmp_path)
    snapshot = tmp_path / "data/report/monitor_snapshots" / f"trade_review_{DAY}.json"
    changed_sha = _write_json(snapshot, {"date": "2026-09-27", "kind": "trade_review"})
    manifest = json.loads(manifest_path.read_text())
    manifest["snapshot_sha256"]["trade_review"] = changed_sha
    _write_json(manifest_path, manifest)
    with pytest.raises(FinalizationGenerationError, match="snapshot_date_mismatch:trade_review"):
        capture_finalization_generation(tmp_path, DAY)


def test_finalization_rejects_missing_controller_attempt(tmp_path):
    _fixture(tmp_path)
    controller_path = tmp_path / "data/report/postclose_done_controller" / f"postclose_done_controller_{DAY}.json"
    controller = json.loads(controller_path.read_text())
    Path(controller["attempt_path"]).unlink()
    with pytest.raises(FinalizationGenerationError, match="controller_attempt_missing"):
        capture_finalization_generation(tmp_path, DAY)


def test_finalization_rejects_summary_change_without_new_strict_attempt(tmp_path):
    _fixture(tmp_path)
    captured = capture_finalization_generation(tmp_path, DAY)
    _write_json(
        tmp_path / "data/report/runtime_approval_summary"
        / f"runtime_approval_summary_{DAY}.json",
        {"date": DAY, "status": "later"},
    )
    assert "strict_summary_generation_stale" in finalization_marker_issues(
        tmp_path, DAY, captured["chain_sha256"], captured["snapshot_sha256"]
    )


def test_final_detector_receipt_requires_same_date_fresh_self_audit(tmp_path):
    report = tmp_path / "data/report/error_detection" / f"error_detection_{DAY}.json"
    _write_json(report, {
        "target_date": DAY,
        "mode": "full",
        "summary_severity": "warning",
        "expected_detector_count": 7,
        "expected_detector_ids": ["cron_completion"] + [f"other_{index}" for index in range(6)],
        "initialized_detector_count": 7,
        "initialized_detector_ids": ["cron_completion"] + [f"other_{index}" for index in range(6)],
        "detector_count": 7,
        "run_id": "cron-20260929T071129-1014922",
        "timestamp": "2026-09-29T07:11:30+09:00",
        "results": [{"detector_id": "cron_completion", "details": {
            "postclose_finalization_status": "pending_self_audit",
        }}] + [{"detector_id": f"other_{index}"} for index in range(6)],
    })
    receipt = capture_final_detector_receipt(tmp_path, DAY, started_after_ns=0)
    assert receipt["run_id"] == "cron-20260929T071129-1014922"
    with pytest.raises(FinalizationGenerationError, match="final_detector_attempt_invalid"):
        capture_final_detector_receipt(
            tmp_path, DAY, started_after_ns=report.stat().st_mtime_ns + 1
        )


def test_detector_rejects_unbound_done_and_accepts_bound_generation(tmp_path, monkeypatch):
    import src.engine.error_detectors.cron_completion as cc

    _fixture(tmp_path)
    log = tmp_path / "logs/postclose_finalization_cron.log"
    log.parent.mkdir(parents=True)
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-29")
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (22, 0))
    monkeypatch.setattr(cc, "CRON_INSTALL_MARKERS", {})
    monkeypatch.setattr(cc, "CRON_JOB_REGISTRY", [{
        "id": "postclose_finalization",
        "log": "logs/postclose_finalization_cron.log",
        "window_start": (21, 55),
        "window_end": (23, 55),
        "mode": "once",
        "critical": True,
        "terminal_error_immediate": True,
    }])
    detector = cc.CronCompletionDetector()
    detector.postclose_source_date = DAY
    log.write_text(f"[DONE] postclose_finalization target_date={DAY} cleanup=done detector=done\n")
    assert detector.check().details["postclose_finalization_status"] == "fail"

    receipt = capture_finalization_generation(tmp_path, DAY)
    log.write_text(
        f"[DONE] postclose_finalization target_date={DAY} cleanup=done detector=done "
        f"chain_sha256={receipt['chain_sha256']} "
        f"snapshot_generation_sha256={receipt['snapshot_sha256']} "
        f"detector_run_id=cron-20260929T071129-1014922 "
        f"detector_report_sha256={'d' * 64}\n"
    )
    assert detector.check().details["postclose_finalization_status"] == "pass"

    snapshot = tmp_path / "data/report/monitor_snapshots" / f"trade_review_{DAY}.json"
    _write_json(snapshot, {"date": DAY, "kind": "trade_review", "changed": True})
    result = detector.check()
    assert result.details["postclose_finalization_status"] == "fail"
    assert "snapshot_hash_mismatch:trade_review" in result.details["postclose_finalization_generation_issues"]
