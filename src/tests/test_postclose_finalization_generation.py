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
    snapshot_kinds_for_date,
    capture_detector_retry_prefix,
)

DAY = "2026-09-28"


def _retry_fixture(root, monkeypatch):
    _fixture(root)
    from src.engine.infrastructure import runtime_release_router as router
    from src.engine.automation import postclose_done_controller as controller

    monkeypatch.setattr(router, "selected_release", lambda _: (root, "a" * 40))
    calls = []
    monkeypatch.setattr(
        controller,
        "done_terminal_receipt_issues",
        lambda *a, **kw: calls.append(kw) or [],
    )
    log = root / "logs"
    log.mkdir()
    (log / "postclose_finalization_cron.log").write_text(
        f"[START] postclose_finalization target_date={DAY} effective_date=2026-09-29 recovery=true started_at=2026-09-29T07:00:00+0900\n"
        '[INFO] postclose_finalization controller_terminal_receipt={"issues": [], "status": "pass"}\n'
        f"[INFO] postclose_finalization cleanup_done target_date={DAY}\n"
        f"[INFO] postclose_finalization target_date={DAY} cleanup=done detector_handoff=started\n"
        f"[FAIL] postclose_finalization target_date={DAY} reason=final_detector_failed\n"
    )
    (log / "log_rotation_cleanup_cron.log").write_text(
        f"[START] log_rotation_cleanup target_date={DAY} started_at=2026-09-29T07:02:00+0900\n"
        f"[DONE] log_rotation_cleanup target_date={DAY} finished_at=2026-09-29T07:03:00+0900\n"
    )
    path = (
        root
        / "data/report/postclose_done_controller"
        / f"postclose_done_controller_{DAY}.json"
    )
    body = json.loads(path.read_bytes())
    body["generated_at"] = "2026-09-29T07:01:00+09:00"
    _write_json(path, body)
    _write_json(Path(body["attempt_path"]), body)
    failed = root / "data/report/error_detection" / f"error_detection_{DAY}.json"
    _write_json(
        failed,
        dict(
            mode="full",
            target_date=DAY,
            postclose_recovery=True,
            summary_severity="fail",
            timestamp="2026-09-29T07:04:00+09:00",
        ),
    )
    return log, failed, calls


def test_detector_suffix_retry_preserves_native_prefix_and_failure(
    tmp_path, monkeypatch
):
    log, failed, calls = _retry_fixture(tmp_path, monkeypatch)
    before = {
        p: p.read_bytes()
        for p in (
            log / "postclose_finalization_cron.log",
            log / "log_rotation_cleanup_cron.log",
            failed,
        )
    }
    result = capture_detector_retry_prefix(tmp_path, DAY)
    receipt = json.loads(Path(result["receipt_path"]).read_bytes())
    assert receipt["generation"] == capture_finalization_generation(tmp_path, DAY)
    assert (
        receipt["runtime_effect"] is False and receipt["allowed_runtime_apply"] is False
    )
    assert calls == [dict(started_after_ns=0, generation_only=True)]
    assert all(p.read_bytes() == raw for p, raw in before.items())
    assert (
        Path(receipt["originals"]["failed_detector"]["path"]).read_bytes()
        == before[failed]
    )


@pytest.mark.parametrize(
    "defect",
    [
        None,
        "legacy_parent",
        "anchor",
        "cleanup",
        "receipt_hash",
        "generation",
        "clock",
        "not_failure",
    ],
)
def test_failed_suffix_can_retry_only_with_unchanged_original_native_anchor(
    tmp_path, monkeypatch, defect
):
    log, failed, _ = _retry_fixture(tmp_path, monkeypatch)
    first = capture_detector_retry_prefix(tmp_path, DAY)
    first_receipt = json.loads(Path(first["receipt_path"]).read_bytes())
    if defect == "legacy_parent":
        first_receipt.pop("native_prefix")
        _write_json(Path(first["receipt_path"]), first_receipt)
        first["receipt_sha256"] = hashlib.sha256(
            Path(first["receipt_path"]).read_bytes()
        ).hexdigest()
    final = log / "postclose_finalization_cron.log"
    with final.open("a") as out:
        out.write(
            f"[START] postclose_finalization target_date={DAY} recovery=true started_at=2026-09-29T07:05:00+0900\n"
            f"[INFO] postclose_finalization target_date={DAY} prefix_reused={json.dumps(first)}\n"
            f"[INFO] postclose_finalization target_date={DAY} cleanup=done detector_handoff=started\n"
            f"[FAIL] postclose_finalization target_date={DAY} reason=final_detector_failed\n"
        )
    body = json.loads(failed.read_bytes())
    body["timestamp"] = "2026-09-29T07:06:00+09:00"
    _write_json(failed, body)
    if defect == "anchor":
        Path(first_receipt["native_prefix"]["finalization_log"]["path"]).write_text(
            "changed"
        )
    elif defect == "cleanup":
        (log / "log_rotation_cleanup_cron.log").write_text("changed")
    elif defect == "receipt_hash":
        Path(first["receipt_path"]).write_text("{}")
    elif defect == "generation":
        p = (
            tmp_path
            / "data/report/postclose_done_controller"
            / f"postclose_done_controller_{DAY}.json"
        )
        d = json.loads(p.read_bytes())
        d["generated_at"] = "2026-09-29T07:01:01+09:00"
        _write_json(p, d)
    elif defect == "clock":
        body["timestamp"] = "2026-09-29T07:04:30+09:00"
        _write_json(failed, body)
    elif defect == "not_failure":
        body["summary_severity"] = "pass"
        _write_json(failed, body)
    before = {
        p: p.read_bytes()
        for p in (final, log / "log_rotation_cleanup_cron.log", failed)
    }
    if defect not in (None, "legacy_parent"):
        with pytest.raises((FinalizationGenerationError, KeyError, ValueError)):
            capture_detector_retry_prefix(tmp_path, DAY)
    else:
        second = capture_detector_retry_prefix(tmp_path, DAY)
        receipt = json.loads(Path(second["receipt_path"]).read_bytes())
        assert receipt["native_prefix"] == first_receipt.get(
            "native_prefix", first_receipt["originals"]
        )
        assert receipt["generation"] == first_receipt["generation"]
        assert receipt["failed_detector_at"] == "2026-09-29T07:04:00+09:00"
        assert receipt["latest_failed_detector_at"] == "2026-09-29T07:06:00+09:00"
        assert (
            Path(receipt["originals"]["failed_detector"]["path"]).read_bytes()
            == before[failed]
        )
    assert all(p.read_bytes() == raw for p, raw in before.items())


@pytest.mark.parametrize(
    "defect",
    [
        "cleanup_failed",
        "new_cleanup",
        "new_finalization",
        "wrong_detector_date",
        "changed_summary",
        "late_controller",
        "symlink",
    ],
)
def test_detector_suffix_retry_rejects_changed_or_incomplete_prefix(
    tmp_path, monkeypatch, defect
):
    log, failed, _ = _retry_fixture(tmp_path, monkeypatch)
    cleanup = log / "log_rotation_cleanup_cron.log"
    finalization = log / "postclose_finalization_cron.log"
    if defect == "cleanup_failed":
        cleanup.write_text(cleanup.read_text().replace("[DONE]", "[FAIL]"))
    elif defect == "new_cleanup":
        cleanup.write_text(
            cleanup.read_text()
            + f"[START] log_rotation_cleanup target_date={DAY} started_at=2026-09-29T07:05:00+0900\n"
        )
    elif defect == "new_finalization":
        finalization.write_text(
            finalization.read_text()
            + f"[START] postclose_finalization target_date={DAY} recovery=true\n"
        )
    elif defect == "wrong_detector_date":
        body = json.loads(failed.read_bytes())
        body["target_date"] = "2026-09-27"
        _write_json(failed, body)
    elif defect == "changed_summary":
        (
            tmp_path
            / "data/report/runtime_approval_summary"
            / f"runtime_approval_summary_{DAY}.json"
        ).write_text("{}")
    elif defect == "late_controller":
        path = (
            tmp_path
            / "data/report/postclose_done_controller"
            / f"postclose_done_controller_{DAY}.json"
        )
        body = json.loads(path.read_bytes())
        body["generated_at"] = "2026-09-29T07:06:00+09:00"
        _write_json(path, body)
    else:
        target = cleanup.with_suffix(".original")
        cleanup.rename(target)
        cleanup.symlink_to(target)
    with pytest.raises(FinalizationGenerationError):
        capture_detector_retry_prefix(tmp_path, DAY)
    assert not (tmp_path / "data/report/postclose_finalization_recovery").exists()


def _write_json(path: Path, payload: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, sort_keys=True) + "\n").encode()
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def _fixture(root: Path, day: str = DAY) -> tuple[Path, Path]:
    report = root / "data/report"
    summary_sha = _write_json(
        report / "runtime_approval_summary" / f"runtime_approval_summary_{day}.json",
        {"date": day, "status": "complete"},
    )
    main_sha = _write_json(
        report
        / "threshold_cycle_postclose_status"
        / f"threshold_cycle_postclose_{day}.status.json",
        {"target_date": day, "run_id": "main-run"},
    )
    checklist_path = root / "docs/checklists" / f"{day}-next.md"
    checklist_path.parent.mkdir(parents=True, exist_ok=True)
    checklist_path.write_text("# Next day\n")
    checklist_sha = hashlib.sha256(checklist_path.read_bytes()).hexdigest()
    stage_sha = _write_json(
        report / "postclose_stage_terminal" / day / "research_capacity.json",
        {"source_date": day, "status": "succeeded"},
    )
    strict_dir = report / "threshold_cycle_postclose_verification"
    strict_attempt = strict_dir / "attempts" / day / "strict.json"
    strict = {
        "date": day,
        "status": "pass",
        "verification_scope": "whole_native_chain",
        "whole_native_chain_done_claimed": True,
        "run_id": "main-run",
        "checklist_handoff": {"path": str(checklist_path)},
        "generation_binding": {
            "source_date": day,
            "main_run_id": "main-run",
            "summary_sha256": summary_sha,
            "main_terminal_sha256": main_sha,
            "checklist_sha256": checklist_sha,
            "stages": {"research_capacity": {"sha256": stage_sha}},
        },
    }
    strict_sha = _write_json(strict_attempt, strict)
    _write_json(
        strict_dir / f"threshold_cycle_postclose_verification_{day}.json", strict
    )
    controller_dir = report / "postclose_done_controller"
    controller_attempt = controller_dir / "attempts" / f"{day}_attempt.json"
    controller = {
        "date": day,
        "status": "done",
        "whole_native_chain_done_claimed": True,
        "final_verifier_status": "pass",
        "main_run_id": "main-run",
        "attempt_path": str(controller_attempt),
        "verification_attempt_path": str(strict_attempt),
        "verification_attempt_sha256": strict_sha,
    }
    _write_json(controller_attempt, controller)
    _write_json(controller_dir / f"postclose_done_controller_{day}.json", controller)

    snapshots = report / "monitor_snapshots"
    paths = {}
    shas = {}
    for kind in snapshot_kinds_for_date(day):
        path = snapshots / f"{kind}_{day}.json"
        shas[kind] = _write_json(path, {"date": day, "kind": kind})
        paths[kind] = str(path)
    manifest_path = (
        snapshots / "manifests" / f"monitor_snapshot_manifest_{day}_postclose_exit.json"
    )
    _write_json(
        manifest_path,
        {
            "target_date": day,
            "profile": "postclose_exit",
            "snapshot_kinds": sorted(paths),
            "snapshot_paths": paths,
            "snapshot_sha256": shas,
        },
    )
    return strict_attempt, manifest_path


@pytest.mark.parametrize(
    "damage",
    [None, "missing", "tamper", "symlink", "oversize", "summary", "stage", "binding"],
)
def test_completed_finalization_uses_original_strict_snapshot_after_cost_refresh(
    tmp_path, monkeypatch, damage
):
    from src.engine.automation import intraday_release_handoff as handoff

    day = "2026-10-20"
    strict_path, _ = _fixture(tmp_path, day)
    captured = capture_finalization_generation(tmp_path, day)
    strict = json.loads(strict_path.read_bytes())
    checklist = Path(strict["checklist_handoff"]["path"])
    expected = strict["generation_binding"]["checklist_sha256"]
    saved = (
        tmp_path
        / "data/runtime/policy_bootstrap/historical_checklists"
        / (expected + ".md")
    )
    saved.parent.mkdir(parents=True)
    saved.write_bytes(checklist.read_bytes())
    checklist.write_text("current operating work\n")
    monkeypatch.setattr(
        handoff,
        "historical_checklist_for_observer",
        lambda *a: (_ for _ in ()).throw(
            ValueError("intraday_bootstrap_invalid:main_stop_confirmation_invalid")
        ),
    )
    if damage == "missing":
        saved.unlink()
    elif damage == "tamper":
        saved.write_text("changed original")
    elif damage == "symlink":
        original = tmp_path / "outside.md"
        original.write_bytes(saved.read_bytes())
        saved.unlink()
        saved.symlink_to(original)
    elif damage == "oversize":
        saved.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    elif damage in {"summary", "stage"}:
        path = (
            tmp_path
            / f"data/report/runtime_approval_summary/runtime_approval_summary_{day}.json"
            if damage == "summary"
            else tmp_path
            / f"data/report/postclose_stage_terminal/{day}/research_capacity.json"
        )
        path.write_text("{}")
    elif damage == "binding":
        strict["generation_binding"]["checklist_sha256"] = "f" * 64
        strict_path.write_text(json.dumps(strict))
    original_operating = checklist.read_bytes()
    details = {}
    issues = finalization_marker_issues(
        tmp_path,
        day,
        captured["chain_sha256"],
        captured["snapshot_sha256"],
        validation_details=details,
    )
    assert checklist.read_bytes() == original_operating
    if damage is None:
        assert issues == []
        assert details["basis"] == "preserved_strict_bound_checklist"
        assert details["sha256"] == expected
        assert details["new_finalization_claimed"] is False
        # New finalization publication still requires the current native chain.
        with pytest.raises(
            FinalizationGenerationError, match="strict_checklist_generation_stale"
        ):
            capture_finalization_generation(tmp_path, day)
    else:
        assert issues


def test_snapshot_manifest_contract_preserves_legacy_and_requires_current_source(
    tmp_path,
):
    assert "missed_entry_counterfactual" not in snapshot_kinds_for_date("2026-09-29")
    assert "missed_entry_counterfactual" in snapshot_kinds_for_date("2026-09-30")
    _fixture(tmp_path, day="2026-09-30")
    captured = capture_finalization_generation(tmp_path, "2026-09-30")
    assert captured["snapshot_modes"]


def test_finalization_rejects_new_strict_generation_after_old_done(tmp_path):
    strict_attempt, _ = _fixture(tmp_path)
    captured = capture_finalization_generation(tmp_path, DAY)
    assert (
        finalization_marker_issues(
            tmp_path, DAY, captured["chain_sha256"], captured["snapshot_sha256"]
        )
        == []
    )

    strict = json.loads(strict_attempt.read_text())
    strict["generation_binding"]["summary_sha256"] = _write_json(
        tmp_path
        / "data/report/runtime_approval_summary"
        / f"runtime_approval_summary_{DAY}.json",
        {"date": DAY, "status": "regenerated"},
    )
    new_attempt = strict_attempt.with_name("new-strict.json")
    new_sha = _write_json(new_attempt, strict)
    _write_json(
        strict_attempt.parents[2]
        / f"threshold_cycle_postclose_verification_{DAY}.json",
        strict,
    )
    controller_path = (
        tmp_path
        / "data/report/postclose_done_controller"
        / f"postclose_done_controller_{DAY}.json"
    )
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
    snapshot = (
        tmp_path / "data/report/monitor_snapshots" / f"post_sell_feedback_{DAY}.json"
    )
    compressed = Path(f"{snapshot}.gz")
    with gzip.open(compressed, "wb") as stream:
        stream.write(snapshot.read_bytes())
    snapshot.unlink()
    assert (
        capture_finalization_generation(tmp_path, DAY)["snapshot_sha256"]
        == captured["snapshot_sha256"]
    )

    trade = tmp_path / "data/report/monitor_snapshots" / f"trade_review_{DAY}.json"
    with gzip.open(f"{trade}.gz", "wb") as stream:
        stream.write(b'{"date":"2026-09-27","kind":"trade_review"}\n')
    coexist = capture_finalization_generation(tmp_path, DAY)
    assert coexist["snapshot_sha256"] == captured["snapshot_sha256"]
    assert (
        coexist["snapshot_modes"]["trade_review"]
        == "canonical_raw_with_excluded_archive"
    )

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
    assert (
        capture_finalization_generation(release, DAY)["snapshot_modes"]["trade_review"]
        == "canonical_raw"
    )


def test_finalization_rejects_wrong_snapshot_date_even_with_matching_manifest_hash(
    tmp_path,
):
    _, manifest_path = _fixture(tmp_path)
    snapshot = tmp_path / "data/report/monitor_snapshots" / f"trade_review_{DAY}.json"
    changed_sha = _write_json(snapshot, {"date": "2026-09-27", "kind": "trade_review"})
    manifest = json.loads(manifest_path.read_text())
    manifest["snapshot_sha256"]["trade_review"] = changed_sha
    _write_json(manifest_path, manifest)
    with pytest.raises(
        FinalizationGenerationError, match="snapshot_date_mismatch:trade_review"
    ):
        capture_finalization_generation(tmp_path, DAY)


def test_finalization_rejects_missing_controller_attempt(tmp_path):
    _fixture(tmp_path)
    controller_path = (
        tmp_path
        / "data/report/postclose_done_controller"
        / f"postclose_done_controller_{DAY}.json"
    )
    controller = json.loads(controller_path.read_text())
    Path(controller["attempt_path"]).unlink()
    with pytest.raises(FinalizationGenerationError, match="controller_attempt_missing"):
        capture_finalization_generation(tmp_path, DAY)


def test_finalization_rejects_summary_change_without_new_strict_attempt(tmp_path):
    _fixture(tmp_path)
    captured = capture_finalization_generation(tmp_path, DAY)
    _write_json(
        tmp_path
        / "data/report/runtime_approval_summary"
        / f"runtime_approval_summary_{DAY}.json",
        {"date": DAY, "status": "later"},
    )
    assert "strict_summary_generation_stale" in finalization_marker_issues(
        tmp_path, DAY, captured["chain_sha256"], captured["snapshot_sha256"]
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "handoff",
        "snapshot",
        "summary",
        "stage",
        "chain_marker",
        "snapshot_marker",
    ],
)
def test_observer_handoff_preserves_done_hashes_without_new_finalization_authority(
    tmp_path, monkeypatch, damage
):
    from src.engine.automation import intraday_release_handoff as handoff

    strict_path, _ = _fixture(tmp_path)
    captured = capture_finalization_generation(tmp_path, DAY)
    checklist = Path(json.loads(strict_path.read_text())["checklist_handoff"]["path"])
    historical = tmp_path / "consumed-historical-checklist.md"
    historical.write_bytes(checklist.read_bytes())
    checklist.write_text("current intraday work\n")

    def source(project, day):
        assert project == tmp_path and day == DAY
        if damage == "handoff":
            raise ValueError("intraday_observer_current_pid_not_bound")
        return dict(
            path=str(historical),
            basis="consumed_intraday_preserved_historical_generation",
            new_finalization_claimed=False,
            runtime_effect=False,
        )

    monkeypatch.setattr(handoff, "historical_checklist_for_observer", source)
    # A finalizer producer still requires the current checklist generation.
    with pytest.raises(
        FinalizationGenerationError, match="strict_checklist_generation_stale"
    ):
        capture_finalization_generation(tmp_path, DAY)
    if damage == "snapshot":
        historical.write_text("tampered")
    if damage == "summary":
        (
            tmp_path
            / f"data/report/runtime_approval_summary/runtime_approval_summary_{DAY}.json"
        ).write_text("{}")
    if damage == "stage":
        (
            tmp_path
            / f"data/report/postclose_stage_terminal/{DAY}/research_capacity.json"
        ).write_text("{}")
    details = {}
    issues = finalization_marker_issues(
        tmp_path,
        DAY,
        "f" * 64 if damage == "chain_marker" else captured["chain_sha256"],
        "f" * 64 if damage == "snapshot_marker" else captured["snapshot_sha256"],
        validation_details=details,
    )
    if damage is None:
        assert issues == []
        assert details["basis"] == "consumed_intraday_preserved_historical_generation"
        assert details["new_finalization_claimed"] is False
    else:
        assert issues
        if damage == "chain_marker":
            assert issues == ["finalization_chain_generation_changed"]
        if damage == "snapshot_marker":
            assert issues == ["finalization_snapshot_generation_changed"]


def test_final_detector_receipt_requires_same_date_fresh_self_audit(tmp_path):
    report = tmp_path / "data/report/error_detection" / f"error_detection_{DAY}.json"
    _write_json(
        report,
        {
            "target_date": DAY,
            "mode": "full",
            "summary_severity": "warning",
            "expected_detector_count": 7,
            "expected_detector_ids": ["cron_completion"]
            + [f"other_{index}" for index in range(6)],
            "initialized_detector_count": 7,
            "initialized_detector_ids": ["cron_completion"]
            + [f"other_{index}" for index in range(6)],
            "detector_count": 7,
            "run_id": "cron-20260929T071129-1014922",
            "timestamp": "2026-09-29T07:11:30+09:00",
            "results": [
                {
                    "detector_id": "cron_completion",
                    "details": {
                        "postclose_finalization_status": "pending_self_audit",
                    },
                }
            ]
            + [{"detector_id": f"other_{index}"} for index in range(6)],
        },
    )
    receipt = capture_final_detector_receipt(tmp_path, DAY, started_after_ns=0)
    assert receipt["run_id"] == "cron-20260929T071129-1014922"
    assert receipt["postclose_completion"]["overall_success"] is False
    assert (
        receipt["postclose_completion"]["source_cost_semantic_status"] == "unverified"
    )
    with pytest.raises(
        FinalizationGenerationError, match="final_detector_attempt_invalid"
    ):
        capture_final_detector_receipt(
            tmp_path, DAY, started_after_ns=report.stat().st_mtime_ns + 1
        )


def test_detector_rejects_unbound_done_and_accepts_bound_generation(
    tmp_path, monkeypatch
):
    import src.engine.error_detectors.cron_completion as cc

    _fixture(tmp_path)
    log = tmp_path / "logs/postclose_finalization_cron.log"
    log.parent.mkdir(parents=True)
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-29")
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (22, 0))
    monkeypatch.setattr(cc, "CRON_INSTALL_MARKERS", {})
    monkeypatch.setattr(
        cc,
        "CRON_JOB_REGISTRY",
        [
            {
                "id": "postclose_finalization",
                "log": "logs/postclose_finalization_cron.log",
                "window_start": (21, 55),
                "window_end": (23, 55),
                "mode": "once",
                "critical": True,
                "terminal_error_immediate": True,
            }
        ],
    )
    detector = cc.CronCompletionDetector()
    detector.postclose_source_date = DAY
    log.write_text(
        f"[DONE] postclose_finalization target_date={DAY} cleanup=done detector=done\n"
    )
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
    assert (
        "snapshot_hash_mismatch:trade_review"
        in result.details["postclose_finalization_generation_issues"]
    )


def _completed_rebind_fixture(root, monkeypatch):
    from src.engine.automation import intraday_release_handoff as handoff

    log, detector, calls = _retry_fixture(root, monkeypatch)
    report = root / "data/report"
    controller_path = (
        report / "postclose_done_controller" / f"postclose_done_controller_{DAY}.json"
    )
    old = json.loads(controller_path.read_bytes())
    old_path = report / "postclose_done_controller/attempts" / f"{DAY}_original.json"
    old["attempt_path"] = str(old_path)
    _write_json(controller_path, old)
    controller_sha = _write_json(old_path, old)
    generation = capture_finalization_generation(root, DAY)
    body = dict(
        mode="full",
        target_date=DAY,
        postclose_recovery=True,
        summary_severity="warning",
        timestamp="2026-09-29T07:04:00+09:00",
        run_id="cron-original",
        expected_detector_count=1,
        initialized_detector_count=1,
        detector_count=1,
        expected_detector_ids=["cron_completion"],
        initialized_detector_ids=["cron_completion"],
        results=[
            dict(
                detector_id="cron_completion",
                details={"postclose_finalization_status": "pending_self_audit"},
            )
        ],
    )
    detector_sha = _write_json(detector, body)
    fields = (
        f"chain_sha256={generation['chain_sha256']} snapshot_generation_sha256={generation['snapshot_sha256']} "
        f"detector_run_id=cron-original detector_report_sha256={detector_sha} finished_at=2026-09-29T07:04:01+0900"
    )
    final = log / "postclose_finalization_cron.log"
    lines = final.read_text().splitlines()[:-1]
    lines.insert(
        -1,
        json.dumps(
            dict(
                schema="next_preopen_readiness_v1",
                status="prepared_verified",
                source_date=DAY,
                controller_sha256=controller_sha,
            )
        ),
    )
    lines += [
        f"[DONE] postclose_finalization target_date={DAY} cleanup=done detector=done {fields}",
        f"[DONE] postclose_final_detector target_date={DAY} finalization=done detector=done {fields}",
    ]
    final.write_text("\n".join(lines) + "\n")
    strict_path = (
        report
        / "threshold_cycle_postclose_verification"
        / f"threshold_cycle_postclose_verification_{DAY}.json"
    )
    strict = json.loads(strict_path.read_bytes())
    summary = (
        report / "runtime_approval_summary" / f"runtime_approval_summary_{DAY}.json"
    )
    strict["generation_binding"]["summary_sha256"] = _write_json(
        summary, dict(date=DAY, status="revalidated")
    )
    strict_attempt = strict_path.parent / "attempts" / DAY / "new.json"
    sha = _write_json(strict_attempt, strict)
    _write_json(strict_path, strict)
    current = {
        **old,
        "verification_attempt_path": str(strict_attempt),
        "verification_attempt_sha256": sha,
        "attempt_path": str(old_path.with_name(f"{DAY}_current.json")),
        "generated_at": "2026-09-29T07:05:00+09:00",
    }
    _write_json(Path(current["attempt_path"]), current)
    _write_json(controller_path, current)
    monkeypatch.setattr(
        handoff,
        "historical_checklist_for_observer",
        lambda *args: {"path": strict["checklist_handoff"]["path"]},
    )
    return final, detector, calls


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "snapshot",
        "stage",
        "old_controller",
        "old_strict",
        "detector",
        "detector_count",
        "native_failure",
        "new_attempt",
        "cleanup",
        "handoff",
        "current_summary",
        "current_controller",
    ],
)
def test_completed_rebind_requires_unchanged_sources_and_both_native_generations(
    tmp_path, monkeypatch, damage
):
    from src.engine.automation import intraday_release_handoff as handoff
    from src.engine.automation import postclose_done_controller as controller

    final, detector, calls = _completed_rebind_fixture(tmp_path, monkeypatch)
    report = tmp_path / "data/report"
    if damage == "snapshot":
        (report / "monitor_snapshots" / f"trade_review_{DAY}.json").write_text("{}")
    elif damage == "stage":
        (
            report / "postclose_stage_terminal" / DAY / "research_capacity.json"
        ).write_text("{}")
    elif damage == "old_controller":
        (
            report / "postclose_done_controller/attempts" / f"{DAY}_original.json"
        ).unlink()
    elif damage == "old_strict":
        (
            report
            / "threshold_cycle_postclose_verification/attempts"
            / DAY
            / "strict.json"
        ).write_text("{}")
    elif damage == "detector":
        detector.write_text("{}")
    elif damage == "detector_count":
        body = json.loads(detector.read_bytes())
        body["detector_count"] = 0
        old = hashlib.sha256(detector.read_bytes()).hexdigest()
        new = _write_json(detector, body)
        final.write_text(final.read_text().replace(old, new))
    elif damage == "native_failure":
        final.write_text(
            final.read_text().replace(
                "[DONE] postclose_final_detector", "[FAIL] postclose_final_detector"
            )
        )
    elif damage == "new_attempt":
        final.write_text(
            final.read_text()
            + f"[START] postclose_finalization target_date={DAY} recovery=true\n"
        )
    elif damage == "cleanup":
        (tmp_path / "logs/log_rotation_cleanup_cron.log").write_text("[FAIL]\n")
    elif damage == "handoff":
        strict = json.loads(
            (
                report
                / "threshold_cycle_postclose_verification"
                / f"threshold_cycle_postclose_verification_{DAY}.json"
            ).read_bytes()
        )
        Path(strict["checklist_handoff"]["path"]).write_text(
            "advanced operating checklist\n"
        )
        monkeypatch.setattr(
            handoff,
            "historical_checklist_for_observer",
            lambda *a: (_ for _ in ()).throw(ValueError("invalid_live_handoff")),
        )
    elif damage == "current_summary":
        (
            report / "runtime_approval_summary" / f"runtime_approval_summary_{DAY}.json"
        ).write_text("{}")
    elif damage == "current_controller":
        monkeypatch.setattr(
            controller, "done_terminal_receipt_issues", lambda *a, **k: ["invalid"]
        )
    originals = {
        p: p.read_bytes()
        for p in (final, detector, tmp_path / "logs/log_rotation_cleanup_cron.log")
    }
    if damage:
        with pytest.raises((FinalizationGenerationError, ValueError)):
            capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
        assert not (report / "postclose_finalization_recovery").exists()
    else:
        result = capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
        receipt = json.loads(Path(result["receipt_path"]).read_bytes())
        assert receipt["recovery_mode"] == "completed_generation_rebinding"
        assert (
            receipt["cleanup_reexecuted"] is receipt["controller_reexecuted"] is False
        )
        assert receipt["generation"] == capture_finalization_generation(tmp_path, DAY)
        assert receipt["cleanup_finished_at"] == "2026-09-29T07:03:00+09:00"
        assert calls and calls[-1]["generation_only"] is True
        assert calls[-1]["checklist_snapshot"] is None
    assert all(p.read_bytes() == raw for p, raw in originals.items())


@pytest.mark.parametrize(
    "damage", [None, "summary", "checklist", "controller", "preflight_failure"]
)
def test_completed_rebind_before_new_pid_uses_exact_current_checklist(
    tmp_path, monkeypatch, damage
):
    from src.engine.automation import intraday_release_handoff as handoff
    from src.engine.automation import postclose_done_controller as controller

    final, _, _ = _completed_rebind_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        handoff,
        "historical_checklist_for_observer",
        lambda *a: (_ for _ in ()).throw(ValueError("no_consumed_pid")),
    )
    report = tmp_path / "data/report"
    if damage == "summary":
        (
            report / "runtime_approval_summary" / f"runtime_approval_summary_{DAY}.json"
        ).write_text("{}")
    elif damage == "checklist":
        strict = json.loads(
            (
                report
                / "threshold_cycle_postclose_verification"
                / f"threshold_cycle_postclose_verification_{DAY}.json"
            ).read_bytes()
        )
        Path(strict["checklist_handoff"]["path"]).write_text("changed")
    elif damage == "controller":
        monkeypatch.setattr(
            controller, "done_terminal_receipt_issues", lambda *a, **k: ["invalid"]
        )
    elif damage == "preflight_failure":
        with final.open("a") as out:
            out.write(
                "Traceback: preflight failed before native START\n"
                f"[FAIL] postclose_finalization target_date={DAY} reason=detector_resume_prefix_invalid\n"
            )
    if damage not in {None, "preflight_failure"}:
        with pytest.raises((FinalizationGenerationError, ValueError)):
            capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
    else:
        result = capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
        receipt = json.loads(Path(result["receipt_path"]).read_bytes())
        assert receipt["generation"] == capture_finalization_generation(tmp_path, DAY)
        assert (
            Path(receipt["originals"]["finalization_log"]["path"]).read_bytes()
            == final.read_bytes()
        )


def test_completed_rebind_uses_consumed_proof_only_after_checklist_changes(
    tmp_path, monkeypatch
):
    from src.engine.automation import intraday_release_handoff as handoff

    _, _, calls = _completed_rebind_fixture(tmp_path, monkeypatch)
    strict = json.loads(
        (
            tmp_path
            / "data/report/threshold_cycle_postclose_verification"
            / f"threshold_cycle_postclose_verification_{DAY}.json"
        ).read_bytes()
    )
    checklist = Path(strict["checklist_handoff"]["path"])
    saved = tmp_path / "consumed.md"
    saved.write_bytes(checklist.read_bytes())
    checklist.write_text("advanced operating checklist\n")
    monkeypatch.setattr(
        handoff, "historical_checklist_for_observer", lambda *a: {"path": str(saved)}
    )
    capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
    assert calls[-1]["checklist_snapshot"] == saved


def test_completed_rebind_failed_detector_retry_preserves_original_success(
    tmp_path, monkeypatch
):
    final, detector, _ = _completed_rebind_fixture(tmp_path, monkeypatch)
    first = capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
    original = final.read_bytes()
    with final.open("a") as stream:
        stream.write(
            f"[START] postclose_finalization target_date={DAY} recovery=true started_at=2026-09-29T07:06:00+0900\n"
            f"[INFO] postclose_finalization target_date={DAY} prefix_reused={json.dumps(first)}\n"
            f"[INFO] postclose_finalization target_date={DAY} cleanup=done detector_handoff=started\n"
            f"[FAIL] postclose_finalization target_date={DAY} reason=final_detector_failed\n"
        )
    body = json.loads(detector.read_bytes())
    body.update(summary_severity="fail", timestamp="2026-09-29T07:07:00+09:00")
    _write_json(detector, body)
    with pytest.raises(FinalizationGenerationError):
        capture_detector_retry_prefix(tmp_path, DAY)
    second = capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
    receipt = json.loads(Path(second["receipt_path"]).read_bytes())
    assert (
        Path(receipt["native_prefix"]["finalization_log"]["path"]).read_bytes()
        == original
    )
    assert (
        receipt["generation"]
        == json.loads(Path(first["receipt_path"]).read_bytes())["generation"]
    )


@pytest.mark.parametrize('damage', [None, 'report_changed', 'wrong_date', 'snapshot', 'cleanup', 'missing_prefix', 'handoff'])
def test_completed_rebind_resumes_failed_suffix_without_published_detector(
    tmp_path, monkeypatch, damage
):
    final, detector, _ = _completed_rebind_fixture(tmp_path, monkeypatch)
    first = capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
    original = detector.read_bytes()
    with final.open('a') as stream:
        stream.write(
            f'[START] postclose_finalization target_date={DAY} recovery=true started_at=2026-09-29T07:06:00+0900\n'
            + ('' if damage == 'missing_prefix' else f'[INFO] postclose_finalization target_date={DAY} prefix_reused={json.dumps(first)}\n')
            + ('' if damage == 'handoff' else f'[INFO] postclose_finalization target_date={DAY} cleanup=done detector_handoff=started\n')
            + f'[FAIL] postclose_finalization target_date={DAY} reason=final_detector_failed\n'
        )
    if damage in {'report_changed', 'wrong_date'}:
        body = json.loads(original)
        body['timestamp'] = '2026-09-29T07:07:00+09:00'
        if damage == 'wrong_date':
            body['target_date'] = '2026-09-28'
        _write_json(detector, body)
    elif damage == 'snapshot':
        (tmp_path/'data/report/monitor_snapshots'/f'trade_review_{DAY}.json').write_text('{}')
    elif damage == 'cleanup':
        (tmp_path/'logs/log_rotation_cleanup_cron.log').write_text('[FAIL]\n')
    if damage:
        with pytest.raises((FinalizationGenerationError, ValueError)):
            capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
        return
    second = capture_detector_retry_prefix(tmp_path, DAY, rebind_completed=True)
    receipt = json.loads(Path(second['receipt_path']).read_bytes())
    assert receipt['latest_detector_report_state'] == 'not_published_after_failed_suffix'
    assert receipt['latest_suffix_started_at'] == '2026-09-29T07:06:00+09:00'
    assert receipt['runtime_effect'] is receipt['actual_pid_consumed'] is False
    assert receipt['cleanup_reexecuted'] is receipt['controller_reexecuted'] is False
    assert detector.read_bytes() == original
    assert receipt['generation'] == json.loads(Path(first['receipt_path']).read_bytes())['generation']


def test_final_detector_generation_cannot_change_during_completion_read(
    tmp_path, monkeypatch
):
    import src.engine.error_detector as detector

    test_final_detector_receipt_requires_same_date_fresh_self_audit(tmp_path)
    path = tmp_path / "data/report/error_detection" / f"error_detection_{DAY}.json"
    original = path.read_bytes()
    assess = detector.postclose_completion_assessment

    def changed(report, day):
        path.write_bytes(original + b"\n")
        return assess(report, day)

    monkeypatch.setattr(detector, "postclose_completion_assessment", changed)
    with pytest.raises(
        FinalizationGenerationError, match="final_detector_generation_changed"
    ):
        capture_final_detector_receipt(tmp_path, DAY, started_after_ns=0)
