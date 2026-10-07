"""Read-only generation binding for the postclose finalizer and its detector."""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import zlib
from datetime import datetime
from pathlib import Path


LEGACY_SNAPSHOT_KINDS = frozenset({
    "trade_review", "post_sell_feedback", "holding_exit_observation",
})
SNAPSHOT_KINDS = frozenset({
    "trade_review", "post_sell_feedback", "missed_entry_counterfactual",
    "holding_exit_observation",
})
MISSED_ENTRY_SNAPSHOT_FROM = "2026-09-30"


def snapshot_kinds_for_date(target_date: str) -> frozenset[str]:
    """Keep sealed pre-rollout manifests valid; require the new source afterward."""
    return (
        SNAPSHOT_KINDS
        if str(target_date) >= MISSED_ENTRY_SNAPSHOT_FROM
        else LEGACY_SNAPSHOT_KINDS
    )


class FinalizationGenerationError(ValueError):
    """A finalization input cannot be bound to the requested source date."""


def _load(path: Path, reason: str) -> dict:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise FinalizationGenerationError(reason) from exc
    if not isinstance(value, dict):
        raise FinalizationGenerationError(reason)
    return value


def _sha(path: Path, *, compressed: bool = False) -> str:
    digest = hashlib.sha256()
    try:
        stream = gzip.open(path, "rb") if compressed else path.open("rb")
        with stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except (OSError, EOFError, ValueError, zlib.error) as exc:
        raise FinalizationGenerationError(
            "snapshot_archive_invalid" if compressed else "finalization_source_unreadable"
        ) from exc
    return digest.hexdigest()


def _logical_sha(value: dict) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def _snapshot_date(path: Path, *, compressed: bool) -> str | None:
    try:
        stream = gzip.open(path, "rb") if compressed else path.open("rb")
        with stream:
            header = stream.read(4096)
    except (OSError, EOFError, ValueError, zlib.error) as exc:
        raise FinalizationGenerationError("snapshot_archive_invalid") from exc
    match = re.match(rb'\s*\{\s*"date"\s*:\s*"(\d{4}-\d{2}-\d{2})"', header)
    return match.group(1).decode() if match else None


def capture_finalization_generation(project: Path, target_date: str) -> dict:
    """Bind the current controller generation and postclose exit source bytes."""
    return _capture_finalization_generation(project, target_date)


def _capture_finalization_generation(project: Path, target_date: str, *,
                                     checklist_snapshot: Path | None = None) -> dict:
    project = Path(project).resolve()
    report = project / "data/report"
    controller_dir = report / "postclose_done_controller"
    controller_path = controller_dir / f"postclose_done_controller_{target_date}.json"
    controller = _load(controller_path, "controller_missing_or_invalid")
    if (controller.get("date") != target_date or controller.get("status") != "done"
            or controller.get("whole_native_chain_done_claimed") is not True
            or controller.get("final_verifier_status") != "pass"):
        raise FinalizationGenerationError("controller_not_whole_chain_done")
    try:
        attempt = Path(str(controller.get("attempt_path") or "")).resolve(strict=True)
        expected_dir = (controller_dir / "attempts").resolve()
        if attempt.parent != expected_dir or _sha(attempt) != _sha(controller_path):
            raise FinalizationGenerationError("controller_attempt_mismatch")
    except OSError as exc:
        raise FinalizationGenerationError("controller_attempt_missing") from exc
    strict_dir = report / "threshold_cycle_postclose_verification"
    strict_path = strict_dir / f"threshold_cycle_postclose_verification_{target_date}.json"
    try:
        strict_attempt = Path(str(controller.get("verification_attempt_path") or "")).resolve(strict=True)
        if strict_attempt.parent != (strict_dir / "attempts" / target_date).resolve():
            raise FinalizationGenerationError("strict_attempt_owner_invalid")
    except OSError as exc:
        raise FinalizationGenerationError("strict_attempt_missing") from exc
    strict_sha = _sha(strict_attempt)
    if strict_sha != controller.get("verification_attempt_sha256"):
        raise FinalizationGenerationError("strict_attempt_hash_mismatch")
    strict = _load(strict_attempt, "strict_attempt_invalid")
    current_strict = _load(strict_path, "strict_current_missing_or_invalid")
    binding = strict.get("generation_binding")
    if (strict.get("date") != target_date or strict.get("status") != "pass"
            or strict.get("verification_scope") != "whole_native_chain"
            or strict.get("whole_native_chain_done_claimed") is not True
            or strict.get("run_id") != controller.get("main_run_id")
            or not isinstance(binding, dict)
            or binding.get("source_date") != target_date
            or binding.get("main_run_id") != controller.get("main_run_id")
            or current_strict.get("date") != target_date
            or current_strict.get("status") != "pass"
            or current_strict.get("verification_scope") != "whole_native_chain"
            or current_strict.get("whole_native_chain_done_claimed") is not True
            or current_strict.get("run_id") != controller.get("main_run_id")
            or current_strict.get("generation_binding") != binding):
        raise FinalizationGenerationError("strict_generation_not_current")
    bound_paths = {
        "strict_summary_generation_stale": (
            report / "runtime_approval_summary" / f"runtime_approval_summary_{target_date}.json",
            binding.get("summary_sha256"),
        ),
        "strict_main_terminal_generation_stale": (
            report / "threshold_cycle_postclose_status"
            / f"threshold_cycle_postclose_{target_date}.status.json",
            binding.get("main_terminal_sha256"),
        ),
        "strict_checklist_generation_stale": (
            checklist_snapshot or Path(str((strict.get("checklist_handoff") or {}).get("path") or "")),
            binding.get("checklist_sha256"),
        ),
    }
    stages = binding.get("stages")
    if not isinstance(stages, dict) or not stages:
        raise FinalizationGenerationError("strict_stage_set_missing")
    for stage, value in stages.items():
        if (not isinstance(stage, str)
                or not re.fullmatch(r"[a-z][a-z0-9_]*", stage)
                or not isinstance(value, dict)):
            raise FinalizationGenerationError("strict_stage_identity_invalid")
        bound_paths[f"strict_stage_generation_stale:{stage}"] = (
            report / "postclose_stage_terminal" / target_date / f"{stage}.json",
            value.get("sha256"),
        )
    for reason, (path, expected_sha) in bound_paths.items():
        if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            raise FinalizationGenerationError(reason)
        try:
            current_sha = _sha(path)
        except FinalizationGenerationError as exc:
            raise FinalizationGenerationError(reason) from exc
        if current_sha != expected_sha:
            raise FinalizationGenerationError(reason)

    snapshot_dir = report / "monitor_snapshots"
    manifest_path = (snapshot_dir / "manifests"
                     / f"monitor_snapshot_manifest_{target_date}_postclose_exit.json")
    manifest = _load(manifest_path, "postclose_exit_manifest_missing_or_invalid")
    paths = manifest.get("snapshot_paths") or {}
    sources = manifest.get("snapshot_sha256") or {}
    kinds = manifest.get("snapshot_kinds")
    expected_kinds = snapshot_kinds_for_date(target_date)
    if (manifest.get("target_date") != target_date
            or manifest.get("profile") != "postclose_exit"
            or not isinstance(kinds, list)
            or not all(isinstance(kind, str) for kind in kinds)
            or set(kinds) != expected_kinds
            or not isinstance(paths, dict) or set(paths) != expected_kinds
            or not isinstance(sources, dict) or set(sources) != expected_kinds):
        raise FinalizationGenerationError("postclose_exit_manifest_contract_invalid")
    source_modes = {}
    for kind in sorted(expected_kinds):
        path = snapshot_dir / f"{kind}_{target_date}.json"
        try:
            owner_matches = Path(str(paths[kind])).resolve() == path.resolve()
        except OSError:
            owner_matches = False
        if not owner_matches or not isinstance(sources[kind], str):
            raise FinalizationGenerationError("snapshot_path_or_hash_invalid:" + kind)
        archived = Path(f"{path}.gz")
        if path.is_file():
            if _sha(path) != sources[kind]:
                raise FinalizationGenerationError("snapshot_hash_mismatch:" + kind)
            if _snapshot_date(path, compressed=False) != target_date:
                raise FinalizationGenerationError("snapshot_date_mismatch:" + kind)
            source_modes[kind] = "canonical_raw"
            if archived.is_file():
                try:
                    archive_matches = _sha(archived, compressed=True) == sources[kind]
                except FinalizationGenerationError:
                    archive_matches = False
                source_modes[kind] = (
                    "canonical_raw_with_matching_archive" if archive_matches
                    else "canonical_raw_with_excluded_archive"
                )
        elif archived.is_file():
            if _sha(archived, compressed=True) != sources[kind]:
                raise FinalizationGenerationError("snapshot_hash_mismatch:" + kind)
            if _snapshot_date(archived, compressed=True) != target_date:
                raise FinalizationGenerationError("snapshot_date_mismatch:" + kind)
            source_modes[kind] = "archive_logical"
        else:
            raise FinalizationGenerationError("snapshot_missing:" + kind)
    snapshot_generation = {
        "source_date": target_date,
        "profile": "postclose_exit",
        "sources": sources,
    }
    return {
        "chain_sha256": _logical_sha(binding),
        "snapshot_sha256": _logical_sha(snapshot_generation),
        "controller_attempt_sha256": _sha(attempt),
        "strict_attempt_sha256": strict_sha,
        "manifest_sha256": _sha(manifest_path),
        "snapshot_modes": source_modes,
    }


def finalization_marker_issues(
    project: Path, target_date: str, chain_sha256: str, snapshot_sha256: str,
    *, validation_details: dict | None = None,
) -> list[str]:
    if not chain_sha256 or not snapshot_sha256:
        return ["finalization_generation_unbound"]
    try:
        current = capture_finalization_generation(project, target_date)
    except FinalizationGenerationError as exc:
        if str(exc) != 'strict_checklist_generation_stale':
            return [str(exc)]
        try:
            from src.engine.automation.intraday_release_handoff import historical_checklist_for_observer
            preserved = historical_checklist_for_observer(project, target_date)
            current = _capture_finalization_generation(
                project, target_date, checklist_snapshot=Path(preserved['path']))
            if validation_details is not None:
                validation_details.update(preserved)
        except (OSError, ValueError, TypeError, KeyError) as fallback:
            if validation_details is not None:
                validation_details.update(historical_handoff_status='invalid', reason=str(fallback))
            return [str(fallback)] if isinstance(fallback, FinalizationGenerationError) else [str(exc)]
    issues = []
    if current["chain_sha256"] != chain_sha256:
        issues.append("finalization_chain_generation_changed")
    if current["snapshot_sha256"] != snapshot_sha256:
        issues.append("finalization_snapshot_generation_changed")
    return issues


def capture_final_detector_receipt(
    project: Path, target_date: str, *, started_after_ns: int
) -> dict:
    """Bind the child detector report generated by this finalizer attempt."""
    path = (Path(project) / "data/report/error_detection"
            / f"error_detection_{target_date}.json")
    report = _load(path, "final_detector_report_missing_or_invalid")
    try:
        fresh = path.stat().st_mtime_ns >= started_after_ns
    except OSError:
        fresh = False
    results = report.get("results") or []
    cron = next((item for item in results
                 if isinstance(item, dict)
                 and item.get("detector_id") == "cron_completion"), {})
    expected = report.get("expected_detector_count")
    expected_ids = report.get("expected_detector_ids")
    initialized_ids = report.get("initialized_detector_ids")
    observed_ids = [item.get("detector_id") for item in results
                    if isinstance(item, dict)]
    try:
        timestamp = datetime.fromisoformat(str(report.get("timestamp") or ""))
        timestamp_valid = timestamp.tzinfo is not None
    except ValueError:
        timestamp_valid = False
    if (not fresh or report.get("target_date") != target_date
            or report.get("mode") != "full"
            or report.get("summary_severity") not in {"pass", "warning"}
            or not isinstance(expected, int) or expected <= 0
            or report.get("initialized_detector_count") != expected
            or report.get("detector_count") != expected
            or len(results) != expected
            or not isinstance(expected_ids, list) or len(expected_ids) != expected
            or not isinstance(initialized_ids, list) or len(initialized_ids) != expected
            or not all(isinstance(item, str) for item in expected_ids + initialized_ids)
            or not all(isinstance(item, str) for item in observed_ids)
            or len(set(expected_ids)) != expected
            or set(initialized_ids) != set(expected_ids)
            or set(observed_ids) != set(expected_ids)
            or (cron.get("details") or {}).get("postclose_finalization_status")
            != "pending_self_audit"
            or not isinstance(report.get("run_id"), str)
            or not report["run_id"].startswith("cron-")
            or not timestamp_valid):
        raise FinalizationGenerationError("final_detector_attempt_invalid")
    return {
        "run_id": report["run_id"],
        "report_sha256": _sha(path),
        "timestamp": report["timestamp"],
    }
