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


def capture_detector_retry_prefix(project: Path, target_date: str) -> dict:
    """Reuse only an unchanged native prefix whose last detector failed.

    This runs under the finalizer lock before its next START. It grants no
    activation authority and never writes controller, policy or DONE markers.
    """
    from src.engine.automation.postclose_done_controller import done_terminal_receipt_issues
    from src.engine.infrastructure.runtime_release_router import selected_release
    import os
    import stat
    import uuid

    project = Path(project).resolve(strict=True)
    data = (project / 'data').resolve(strict=True)
    selected, commit = selected_release(data.parent)
    if selected != project:
        raise FinalizationGenerationError('retry_selected_release_mismatch')
    paths = {
        'finalization_log': project / 'logs/postclose_finalization_cron.log',
        'cleanup_log': project / 'logs/log_rotation_cleanup_cron.log',
        'failed_detector': data / 'report/error_detection' / f'error_detection_{target_date}.json',
    }
    def stable_read(path):
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > 16 * 1024 * 1024:
            raise FinalizationGenerationError('retry_bounded_regular_source_required')
        identity = lambda item: (item.st_dev,item.st_ino,item.st_size,item.st_mtime_ns,item.st_ctime_ns)
        with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW),'rb') as stream:
            opened=os.fstat(stream.fileno());raw=stream.read(16*1024*1024+1)
            if identity(opened)!=identity(os.fstat(stream.fileno())):
                raise FinalizationGenerationError('retry_source_changed')
        after = path.lstat()
        if (not stat.S_ISREG(after.st_mode) or len(raw)!=before.st_size
                or identity(before)!=identity(opened) or identity(before)!=identity(after)):
            raise FinalizationGenerationError('retry_source_changed')
        return raw
    frozen = {name:stable_read(path) for name,path in paths.items()}
    log = frozen['finalization_log'].decode()
    start = f'[START] postclose_finalization target_date={target_date} '
    segment = log[log.rfind(start):] if start in log else ''
    lines = segment.splitlines()
    failure = f'[FAIL] postclose_finalization target_date={target_date} reason=final_detector_failed'
    handoff = f'[INFO] postclose_finalization target_date={target_date} cleanup=done detector_handoff=started'
    latest_started = lines[0] if lines else ''
    anchor = frozen
    native_prefix = None
    prior_generation = None
    reused = [line.split(' prefix_reused=', 1)[1] for line in lines
              if line.startswith(f'[INFO] postclose_finalization target_date={target_date} prefix_reused=')]
    if reused:
        # A failed detector-only retry does not invalidate its original native
        # controller/cleanup. Revalidate the immutable anchor and retain both
        # failed attempts; never rerun producers or manufacture terminal lines.
        if len(reused) != 1 or not lines or lines[-1] != failure or handoff not in lines:
            raise FinalizationGenerationError('retry_suffix_chain_invalid')
        reference = json.loads(reused[0])
        base = data / 'report/postclose_finalization_recovery' / target_date
        def preserved(ref, filename):
            path = Path(ref['path'])
            if (path.name != filename or path.parent.parent != base
                    or not re.fullmatch('[0-9a-f]{32}', path.parent.name)
                    or path.resolve() != path or path.parent.is_symlink()):
                raise FinalizationGenerationError('retry_preserved_path_invalid')
            raw = stable_read(path)
            if hashlib.sha256(raw).hexdigest() != ref.get('sha256'):
                raise FinalizationGenerationError('retry_preserved_hash_changed')
            return raw
        prior = json.loads(preserved(dict(path=reference['receipt_path'],
            sha256=reference['receipt_sha256']), 'receipt.json'))
        if (prior.get('schema') != 'postclose_detector_suffix_recovery_v1'
                or prior.get('source_date') != target_date or prior.get('runtime_effect') is not False
                or prior.get('allowed_runtime_apply') is not False or prior.get('actual_pid_consumed') is not False):
            raise FinalizationGenerationError('retry_preserved_receipt_invalid')
        native_prefix = prior.get('native_prefix') or prior['originals']
        anchor = {name:preserved(native_prefix[name], name+'.original') for name in paths}
        if (not frozen['finalization_log'].startswith(anchor['finalization_log'])
                or frozen['cleanup_log'] != anchor['cleanup_log']):
            raise FinalizationGenerationError('retry_native_prefix_changed')
        prior_generation = prior['generation']
        if (reference.get('chain_sha256') != prior_generation.get('chain_sha256')
                or reference.get('snapshot_sha256') != prior_generation.get('snapshot_sha256')):
            raise FinalizationGenerationError('retry_preserved_generation_invalid')
        original_log = anchor['finalization_log'].decode()
        lines = original_log[original_log.rfind(start):].splitlines() if start in original_log else []
    if (not lines or lines[-1] != failure or 'recovery=true' not in lines[0]
            or 'recovery=true' not in latest_started
            or '[INFO] postclose_finalization controller_terminal_receipt={"issues": [], "status": "pass"}' not in lines
            or f'[INFO] postclose_finalization cleanup_done target_date={target_date}' not in lines
            or f'[INFO] postclose_finalization target_date={target_date} cleanup=done detector_handoff=started' not in lines):
        raise FinalizationGenerationError('retry_requires_failed_native_detector_suffix')
    cleanup = frozen['cleanup_log'].decode().splitlines()
    cleanup_starts = [i for i, line in enumerate(cleanup)
                      if line.startswith('[START] log_rotation_cleanup ')]
    terminal = cleanup[-1] if cleanup else ''
    if (not cleanup_starts
            or f'target_date={target_date} ' not in cleanup[cleanup_starts[-1]]
            or not terminal.startswith(f'[DONE] log_rotation_cleanup target_date={target_date} ')):
        raise FinalizationGenerationError('retry_cleanup_not_successful_latest_attempt')
    def stamp(line, key):
        match = re.search(r'\b' + key + r'=([^ ]+)', line)
        value = datetime.fromisoformat(match.group(1)) if match else None
        if value is None or value.tzinfo is None:
            raise FinalizationGenerationError('retry_clock_unbound')
        return value
    started = stamp(lines[0], 'started_at')
    cleanup_started = stamp(cleanup[cleanup_starts[-1]], 'started_at')
    cleanup_finished = stamp(terminal, 'finished_at')
    failed = json.loads(anchor['failed_detector'])
    failed_at = datetime.fromisoformat(failed['timestamp'])
    latest_failed = json.loads(frozen['failed_detector'])
    latest_failed_at = datetime.fromisoformat(latest_failed['timestamp'])
    retry_started = stamp(latest_started, 'started_at')
    controller_path = data / 'report/postclose_done_controller' / f'postclose_done_controller_{target_date}.json'
    controller = _load(controller_path, 'retry_controller_missing')
    generated = datetime.fromisoformat(controller['generated_at'])
    if (failed.get('mode') != 'full' or failed.get('target_date') != target_date
            or failed.get('postclose_recovery') is not True or failed.get('summary_severity') != 'fail'
            or failed_at.tzinfo is None or generated.tzinfo is None
            or not started <= generated <= cleanup_started <= cleanup_finished <= failed_at
            or latest_failed.get('mode') != 'full' or latest_failed.get('target_date') != target_date
            or latest_failed.get('postclose_recovery') is not True or latest_failed.get('summary_severity') != 'fail'
            or latest_failed_at.tzinfo is None or not retry_started <= latest_failed_at
            or native_prefix is not None and not failed_at <= retry_started
            or latest_failed_at.timestamp() > paths['finalization_log'].stat().st_mtime + 1):
        raise FinalizationGenerationError('retry_prefix_clock_or_detector_invalid')
    generation = capture_finalization_generation(project, target_date)
    if prior_generation is not None and prior_generation != generation:
        raise FinalizationGenerationError('retry_native_generation_changed')
    issues = done_terminal_receipt_issues(controller_path, target_date, started_after_ns=0,
                                         generation_only=True)
    if issues:
        raise FinalizationGenerationError('retry_controller_invalid:' + ','.join(issues))
    if (selected_release(data.parent) != (selected, commit)
            or any(stable_read(path) != frozen[name] for name, path in paths.items())):
        raise FinalizationGenerationError('retry_source_changed')
    folder = data / 'report/postclose_finalization_recovery' / target_date / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=False)
    originals = {}
    for name, raw in frozen.items():
        destination = folder / (name + '.original')
        with destination.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        originals[name] = dict(path=str(destination), sha256=hashlib.sha256(raw).hexdigest())
    receipt = dict(schema='postclose_detector_suffix_recovery_v1', source_date=target_date,
        selected_release_root=str(selected), selected_release_commit=commit,
        original_started_at=started.isoformat(), cleanup_finished_at=cleanup_finished.isoformat(),
        failed_detector_at=failed_at.isoformat(), originals=originals, generation=generation,
        latest_failed_detector_at=latest_failed_at.isoformat(),
        native_prefix=native_prefix or originals,
        controller_sha256=_sha(controller_path), recovery_code_sha256=_sha(Path(__file__)),
        runtime_effect=False, allowed_runtime_apply=False, actual_pid_consumed=False)
    destination = folder / 'receipt.json'
    with destination.open('x') as stream:
        json.dump(receipt, stream, sort_keys=True, indent=2); stream.flush(); os.fsync(stream.fileno())
    return dict(receipt_path=str(destination), receipt_sha256=_sha(destination),
                original_started_at=receipt['original_started_at'],
                cleanup_finished_at=receipt['cleanup_finished_at'],
                chain_sha256=generation['chain_sha256'], snapshot_sha256=generation['snapshot_sha256'])


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Validate and preserve a failed native detector suffix.')
    parser.add_argument('--resume-prefix', action='store_true', required=True)
    parser.add_argument('project', type=Path)
    parser.add_argument('source_date')
    arguments = parser.parse_args()
    print(json.dumps(capture_detector_retry_prefix(arguments.project, arguments.source_date), sort_keys=True))
