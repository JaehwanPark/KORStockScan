from __future__ import annotations


import csv
import gzip
import glob
import hashlib
import json
import math
import os
import re
import time
import stat
import zlib
from contextlib import contextmanager
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.utils.constants import PROJECT_ROOT
from src.utils.jsonl_io import existing_or_gzip_path
from src.utils.market_day import is_krx_trading_day

from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
)
from src.engine.error_detectors.schedule_contract import (
    evaluate_schedule_contract,
    load_installed_crontab,
)
from src.engine.error_detectors.cron_completion import CronCompletionDetector


def _today_kst_str(now_kst: datetime | None = None) -> str:
    return (now_kst or datetime.now()).strftime("%Y-%m-%d")




def _observer_file_signature(info):
    return tuple(getattr(info, "st_" + field) for field in (
        "dev", "ino", "mode", "nlink", "uid", "gid", "size", "mtime_ns", "ctime_ns"))


@contextmanager
def _observer_regular_fd(path, *, max_bytes=None):
    """Never block opening special files or follow a replacement symlink."""
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode): raise ValueError("observer_regular_file_required")
    if max_bytes is not None and before.st_size > max_bytes:
        raise ValueError("observer_file_size_limit")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode): raise ValueError("observer_regular_file_required")
        if _observer_file_signature(opened) != _observer_file_signature(before):
            raise ValueError("observer_file_changed_before_read")
        yield fd
        if (_observer_file_signature(os.fstat(fd)) != _observer_file_signature(opened)
                or _observer_file_signature(path.lstat()) != _observer_file_signature(opened)):
            raise ValueError("observer_file_changed_during_read")
    finally:
        os.close(fd)


def _observer_regular_bytes(path, *, limit):
    with _observer_regular_fd(path, max_bytes=limit) as fd:
        chunks, total = [], 0
        while True:
            chunk = os.read(fd, min(128 * 1024, limit + 1 - total))
            if not chunk: break
            chunks.append(chunk); total += len(chunk)
            if total > limit: raise ValueError("observer_file_size_limit")
        return b"".join(chunks)


def _observer_json_object(encoded):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result: raise ValueError("observer_json_duplicate_key")
            result[key] = value
        return result
    def number(value):
        result = float(value)
        if not math.isfinite(result): raise ValueError("observer_json_nonfinite")
        return result
    def invalid_constant(value):
        raise ValueError("observer_json_nonfinite")
    value = json.loads(encoded, object_pairs_hook=pairs, parse_float=number, parse_constant=invalid_constant)
    if not isinstance(value, dict): raise ValueError("observer_json_object_required")
    return value


def _observer_small_object(path, *, limit=1024 * 1024, hash_only=False):
    encoded = _observer_regular_bytes(path, limit=limit)
    return ({} if hash_only else _observer_json_object(encoded), hashlib.sha256(encoded).hexdigest())


def _submission_observer_snapshot(path):
    """Reuse one strict bounded report read, only while its exact inode is stable."""
    before = _observer_file_signature(path.lstat())
    payload, sha = _observer_small_object(path, limit=8 * 1024 * 1024)
    if _observer_file_signature(path.lstat()) != before:
        raise ValueError('observer_report_changed_during_snapshot')
    return payload, sha, before


def _submission_observer_input_identity(path, root):
    """Cheap publication boundary; unavailable inputs still reach validation."""
    report = existing_or_gzip_path(path)
    result = {}
    for name, candidate in (
            ('report', report),
            ('selection', Path(root) / 'data/runtime/runtime_release_selection.json')):
        try:
            identity = _observer_file_signature(candidate.lstat())
        except OSError as exc:
            identity = (type(exc).__name__, exc.errno)
        result[name] = dict(path=str(candidate), signature=identity)
    try:
        heartbeat, _ = _observer_small_object(Path(root)/'tmp/error_detector_heartbeat.json')
        terminal = (heartbeat.get('threads') or {}).get('sniper_engine') or {}
        result['engine_terminal'] = dict(pid=(heartbeat.get('main_loop') or {}).get('pid'),
            terminal=terminal if terminal.get('alive') is False else None)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        result['engine_terminal'] = dict(unavailable=type(exc).__name__)
    return result


def _submission_observer_dimensions(payload, path, sha):
    def scalar(value):
        if isinstance(value, str): return ' '.join(value.split())[:160]
        return value if isinstance(value, (int, float, bool)) or value is None else None
    stages = {}
    for name in ('source_gap_semantics', 'entry_execution_tuning_semantics', 'machine_semantics'):
        value = payload.get(name)
        if not isinstance(value, dict):
            continue
        stage = {key:scalar(value[key]) for key in ('status', 'reason', 'blocker', 'source_status', 'selection_status',
                 'observation_count', 'source_invalid_count', 'required_feature_guard_count')
                 if isinstance(value.get(key), (str, int, float, bool))}
        sources = value.get('sources')
        if isinstance(sources, dict):
            stage['sources'] = {str(key)[:80]:{field:scalar(source[field]) for field in (
                'status', 'recent_count', 'reason', 'window_covered', 'first_read_at', 'bytes_read')
                if isinstance(source.get(field), (str, int, float, bool))}
                for key, source in list(sources.items())[:16] if isinstance(source, dict)}
        for field in ('issues', 'diagnostics'):
            if isinstance(value.get(field), dict):
                stage[field] = {str(key)[:160]:scalar(count) for key,count in list(value[field].items())[:16]}
        stages[name] = stage
    provenance = payload.get('input_provenance')
    provenance = ({key:scalar(provenance[key]) for key in (
        'schema', 'target_date', 'evaluated_at', 'snapshot_as_of', 'latest_event_at',
        'latest_event_status', 'loaded_recent_event_count',
        'snapshot_age_seconds', 'latest_event_age_seconds', 'row_count', 'snapshot_order') if key in provenance}
        if isinstance(provenance, dict) else None)
    cohorts = {'evaluation_cohort': scalar(payload.get('evaluation_cohort'))}
    for name in ('identity_observation', 'fixed_watch_identity_observation'):
        value = payload.get(name)
        if isinstance(value, dict):
            cohorts[name] = {key:scalar(value[key]) for key in (
                'status', 'window_sec', 'window_policy', 'identified_event_count',
                'missing_event_count', 'identity_missing_event_count', 'latest_identified_at')
                if isinstance(value.get(key), (str, int, float, bool))}
    return dict(report=dict(path=str(path), byte_sha256=sha,
                           date=scalar(payload.get('date')), as_of=scalar(payload.get('as_of')), run_id=scalar(payload.get('run_id'))),
                execution=scalar(payload.get('execution_status')), semantic=scalar(payload.get('semantic_status')),
                source=dict(status=scalar(payload.get('status')), blocker=scalar(payload.get('blocker')), stages=stages,
                            input_provenance=provenance, cohorts=cohorts,
                            inherited_source_as_of=scalar(payload.get('source_as_of')),
                            inherited_source_as_of_is_upstream_clock=False),
                runtime_effect=False, allowed_runtime_apply=False)


def _submission_observer_partial_reason(dimensions):
    def text(value):
        return ' '.join(str(value).split())[:160]
    source = dimensions['source']
    reasons = []
    # Name the recomputed failed health conditions before the scanner-only
    # funnel blocker. Fixed-watch Main activity has its own cohort and clock.
    health = dimensions.get('observation_health') or {}
    unmet = health.get('unmet_conditions')
    if isinstance(unmet, list) and unmet:
        reasons.append('health_unmet=' + ','.join(text(value) for value in unmet[:12]))
    cohorts = source.get('cohorts') or {}
    if cohorts.get('evaluation_cohort'):
        reasons.append('evaluation_cohort=' + text(cohorts['evaluation_cohort']))
    for key, label in (('identity_observation', 'scanner_identified_events'),
                       ('fixed_watch_identity_observation', 'fixed_watch_identified_events')):
        count = (cohorts.get(key) or {}).get('identified_event_count')
        if count is not None:
            reasons.append(label + '=' + text(count))
    if source.get('blocker') is not None:
        reasons.append('blocker=' + text(source['blocker']))
    for name, stage in source['stages'].items():
        reasons.append(name + '=' + text(stage.get('status', 'not_reported')))
        for key in ('reason', 'blocker', 'source_status', 'selection_status'):
            if key in stage:
                reasons.append(name + '.' + key + '=' + text(stage[key]))
        for key in ('issues', 'diagnostics'):
            if stage.get(key):
                reasons.append(name + '.' + key + '=' + ','.join(list(stage[key])[:4]))
    return '; '.join(reasons) or 'source_reason_not_reported'


def _observer_clock(value):
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo is not None else None
    except (ValueError, TypeError):
        return None


def _observer_live_identity(pid):
    tail = Path("/proc", str(pid), "stat").read_text().rsplit(")", 1)[1].split()
    return {"pid": pid, "start_ticks": tail[19],
            "cwd": str(Path(os.readlink(f"/proc/{pid}/cwd")).resolve(strict=True))}


def _submission_observer_transition_pending(root, artifact_path, now, *, max_staleness_sec, report_snapshot=None):
    """Recognize only the exact frozen predecessor while its first slot is due.

    The report remains prior partial/validated evidence; this never synthesizes
    current validation, clears source gaps, or grants startup/policy authority.
    """
    try:
        if now.tzinfo is None: now = now.replace(tzinfo=ZoneInfo("Asia/Seoul"))
        data = (Path(root) / "data").resolve(strict=True)
        day = now.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat()
        expected_report = data / "report/buy_funnel_sentinel" / f"submission_bottleneck_monitor_{day}.json"
        if Path(artifact_path).resolve(strict=True) != expected_report or Path(artifact_path).is_symlink():
            return None
        snapshot = report_snapshot or _submission_observer_snapshot(Path(artifact_path))
        report, report_sha, report_signature = snapshot
        if _observer_file_signature(Path(artifact_path).lstat()) != report_signature: return None
        report_mtime = report_signature[7] / 1_000_000_000
        age = now.timestamp() - report_mtime
        if age < 0: return None
        if (report.get("schema") != "submission_bottleneck_monitor_v1" or report.get("date") != day
                or not re.fullmatch("[0-9a-f]{32}", str(report.get("run_id") or ""))
                or report.get("execution_status") != "completed"
                or report.get("semantic_status") not in {"partial", "validated"}):
            return None
        selected_path = data / "runtime/runtime_release_selection.json"
        selection, selection_sha = _observer_small_object(selected_path, limit=1024 * 1024)
        commit = selection.get("git_commit")
        release = selection.get("release_root")
        if (selection.get("schema") != "runtime_release_selection_v1"
                or not re.fullmatch("[0-9a-f]{40}", str(commit or ""))
                or not isinstance(release, str) or not Path(release).is_absolute()
                or selection.get("approval_scope") != "ordered_intraday_deploy_and_restart"
                or selection.get("approved_by") != "user"
                or selection.get("actual_pid_consumed") is not True):
            return None
        transition_path = data / "runtime/release_transitions" / day / commit / "status.json"
        if selection.get("deployment_transition") != str(transition_path): return None
        transition, transition_sha = _observer_small_object(transition_path, limit=1024 * 1024)
        selected_at = _observer_clock(selection.get("selected_at_kst"))
        complete_at = _observer_clock(transition.get("updated_at"))
        report_at = _observer_clock(report.get("as_of"))
        if (transition.get("schema") != "ordered_intraday_deployment_v1"
                or transition.get("authority") != "APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART"
                or transition.get("target_date") != day or transition.get("candidate_commit") != commit
                or transition.get("candidate_root") != release or transition.get("policy_effect") != "unchanged"
                or transition.get("phase") != "complete" or transition.get("status") != "pass"
                or selected_at is None or complete_at is None or report_at is None
                or not report_at < selected_at <= complete_at <= now):
            return None
        age_at_completion = complete_at.timestamp() - report_mtime
        if not 0 <= age_at_completion <= max_staleness_sec: return None
        # Strictly next five-minute cron slot, then the existing 180-second
        # total wrapper budget (Sentinel prefix + observer + cleanup).
        due_epoch = (math.floor(complete_at.timestamp() / 300) + 1) * 300 + 180
        if now.timestamp() > due_epoch: return None
        predecessor = transition.get("predecessor_observer") or {}
        if (predecessor.get("schema") != "startup_observer_predecessor_v1"
                or predecessor.get("status") != "captured" or predecessor.get("path") != str(expected_report)
                or predecessor.get("sha256") != report_sha
                or predecessor.get("mtime_ns") != Path(artifact_path).stat().st_mtime_ns
                or any(predecessor.get(key) != report.get(key) for key in (
                    "date", "as_of", "run_id", "execution_status", "semantic_status"))):
            return None
        receipt = selection.get("actual_pid_receipt") or {}
        identity = transition.get("successor_identity") or {}
        if (receipt.get("schema") != "runtime_release_pid_receipt_v1"
                or type(receipt.get("pid")) is not int or receipt["pid"] <= 0
                or not isinstance(identity.get("start_ticks"), str) or not identity["start_ticks"].isdigit()
                or receipt.get("git_commit") != commit or receipt.get("release_root") != release
                or receipt.get("pid") != identity.get("pid")
                or receipt.get('start_ticks') != identity['start_ticks']
                or receipt.get("process_cwd") != str(Path(release) / "src")
                or identity != _observer_live_identity(receipt["pid"])):
            return None
        # A selector/transition replacement during this check cannot inherit
        # pending status from an earlier deployment generation.
        if (_observer_small_object(selected_path, limit=1024 * 1024)[1] != selection_sha
                or _observer_small_object(transition_path, limit=1024 * 1024)[1] != transition_sha
                or _observer_small_object(Path(artifact_path), limit=8 * 1024 * 1024)[1] != report_sha
                or Path(artifact_path).stat().st_mtime_ns != predecessor["mtime_ns"]):
            return None
        return dict(status="pending_first_current_observer", source="exact_captured_predecessor",
            current_commit=commit, current_release_root=release, transition=str(transition_path),
            prior_run_id=report["run_id"], prior_sha256=report_sha,
            prior_execution_status=report["execution_status"], prior_semantic_status=report["semantic_status"],
            prior_blocker=report.get("blocker"), prior_status=report.get("status"),
            deadline=datetime.fromtimestamp(due_epoch, now.tzinfo).isoformat(),
            cron_deadline=datetime.fromtimestamp(due_epoch, now.tzinfo).isoformat(),
            freshness_deadline=datetime.fromtimestamp(predecessor['mtime_ns'] / 1_000_000_000 + max_staleness_sec, now.tzinfo).isoformat(),
            prior_age_sec=round(age, 1), age_at_completion_sec=round(age_at_completion, 1),
            freshness_at_completion='fresh', prior_stale_retained=age > max_staleness_sec,
            handoff_time_allowance='exact_captured_predecessor_through_first_slot_budget',
            current_observation_verified=False, runtime_effect=False, allowed_runtime_apply=False)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


def _submission_observer_generation_issue(payload, root, *, selection_path=None):
    generation = payload.get("observer_generation")
    if generation is None:
        return "observer_generation_missing" if str(payload.get("date") or "") >= "2026-10-14" else None
    if not isinstance(generation, dict): return "observer_generation_invalid"
    expected = hashlib.sha256(json.dumps({key: value for key, value in generation.items() if key != "sha256"},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    started = _observer_clock(generation.get("started_at"))
    completed = _observer_clock(generation.get("completed_at"))
    if (generation.get("schema") != "submission_monitor_observer_generation_v1"
            or generation.get("sha256") != expected
            or generation.get("target_date") != payload.get("date")
            or generation.get("run_id") != payload.get("run_id")
            or generation.get("status") != "current" or generation.get("generation_current") is not True
            or generation.get("policy_pid_consumption_proven") is not False
            or started is None or completed is None or completed < started
            or _observer_clock(payload.get("as_of")) != started
            or started.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat() != payload.get("date")
            or not isinstance(generation.get("release_root"), str)
            or not Path(generation["release_root"]).is_absolute()
            or not re.fullmatch("[0-9a-f]{40}", str(generation.get("git_commit") or ""))
            or not re.fullmatch("[0-9a-f]{64}", str(generation.get("observer_code_sha256") or ""))):
        return "observer_generation_invalid"
    try:
        selection, sha = _observer_small_object(
            selection_path or Path(root) / "data/runtime/runtime_release_selection.json", limit=1024 * 1024)
        if (selection.get("schema") != "runtime_release_selection_v1"
                or generation.get("selection_sha256") != sha or generation.get("final_selection_sha256") != sha
                or generation.get("release_root") != selection.get("release_root")
                or generation.get("git_commit") != selection.get("git_commit")
                or generation.get("selected_release_root") != selection.get("release_root")
                or generation.get("selected_git_commit") != selection.get("git_commit")
                or generation.get("selected_at_kst") != selection.get("selected_at_kst")
                or generation.get("selector_reported_actual_pid_consumed") != selection.get("actual_pid_consumed")
                or generation.get("selector_reported_pid_receipt") != selection.get("actual_pid_receipt")):
            return "observer_generation_not_current"
        observer_path = Path(generation["release_root"]) / "src/engine/monitoring/submission_bottleneck_monitor.py"
        if _observer_small_object(observer_path, limit=1024 * 1024, hash_only=True)[1] != generation["observer_code_sha256"]:
            return "observer_generation_code_mismatch"
        gap = payload.get('source_gap_semantics') or {}
        views = [gap, (gap.get('current_health_cohort') or {}).get('view') or {}]
        indexed = [((view.get('sources') or {}).get('probe') or {}) for view in views]
        indexed = [source for source in indexed
                   if source.get('coverage_basis') == 'verified_forward_sentinel_source_window_v1']
        if indexed:
            source_path = Path(generation['release_root'])/'src/engine/monitoring/sentinel_source_window.py'
            source_sha = _observer_small_object(source_path,limit=1024*1024,hash_only=True)[1]
            if any(source.get('projection_contract') != source_sha for source in indexed):
                return 'observer_source_window_code_mismatch'
    except (OSError, ValueError, TypeError):
        return "observer_generation_selection_unavailable"
    return None


def _submission_observer_actor_issue(payload):
    """Only the quiet-window WARNING exception requires a live consumed Main."""
    generation = payload.get('observer_generation') or {}
    if not isinstance(generation, dict): return 'observer_current_main_receipt_unproven'
    receipt = generation.get('selector_reported_pid_receipt') or {}
    if (generation.get('selector_reported_actual_pid_consumed') is not True
            or not isinstance(receipt, dict)
            or receipt.get('schema') != 'runtime_release_pid_receipt_v1'
            or type(receipt.get('pid')) is not int or receipt['pid'] <= 0
            or not isinstance(receipt.get('start_ticks'), str) or not receipt['start_ticks'].isdigit()
            or receipt.get('release_root') != generation.get('release_root')
            or receipt.get('git_commit') != generation.get('git_commit')
            or receipt.get('process_cwd') != str(Path(generation['release_root']) / 'src')):
        return 'observer_current_main_receipt_unproven'
    machine = payload.get('machine_semantics') or {}
    cohort = machine.get('current_health_cohort') if isinstance(machine, dict) else None
    if cohort is not None:
        # The pure health projection has already validated the exact current
        # cohort. The outer 30-minute ledger remains historical evidence.
        if (not isinstance(cohort, dict)
                or cohort.get('actor') != [str(receipt['pid']), receipt['start_ticks']]
                or not isinstance(cohort.get('view'), dict)):
            return 'observer_current_main_lineage_mismatch'
        machine = cohort['view']
    lineage = machine.get('reversal_provider_lineage') if isinstance(machine, dict) else None
    if lineage is not None and (not isinstance(lineage, dict)
            or lineage.get('exact_pid_filter') != [str(receipt['pid']), receipt['start_ticks']]):
        return 'observer_current_main_lineage_mismatch'
    closed = None
    try:
        if _observer_live_identity(receipt['pid']) != dict(pid=receipt['pid'], start_ticks=receipt['start_ticks'],
                                                        cwd=receipt['process_cwd']):
            return 'observer_current_main_identity_changed'
    except FileNotFoundError:
        try:
            from src.engine.automation.intraday_release_handoff import closed_consumption_observation
            closed = closed_consumption_observation(payload['date'])
            if closed['pid_identity'] != dict(pid=receipt['pid'], start_ticks=receipt['start_ticks'], cwd=receipt['process_cwd']):
                return 'observer_current_main_identity_changed'
        except (OSError, ValueError, TypeError, KeyError):
            return 'observer_current_main_not_running'
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        return 'observer_current_main_not_running'
    # A report may bound its health window by this exact process lifetime only
    # when the kernel independently confirms the declared birth evidence. Old
    # reports without this additive evidence retain their strict full-window
    # behavior; they do not acquire an inferred lifetime allowance here.
    declared = generation.get('actor_birth_proof')
    cohorts = [stage.get('current_health_cohort')
               for stage in (payload.get('source_gap_semantics'), payload.get('machine_semantics'))
               if isinstance(stage, dict)]
    cohort_proofs = [value.get('actor_birth_proof') for value in cohorts if isinstance(value, dict)]
    if declared is not None or any(value is not None for value in cohort_proofs):
        try:
            from src.engine.monitoring.submission_bottleneck_monitor import _attest_health_actor_birth, _observer_regular_bytes
            at = datetime.fromisoformat(str(payload.get('as_of')))
            if closed:
                # The consumed start ticks remain sealed after exit. The boot
                # epoch and tick rate still require an independent kernel read.
                boot = _observer_regular_bytes(Path('/proc/stat'), limit=256*1024).decode()
                epoch = int(next((line.split()[1] for line in boot.splitlines() if line.startswith('btime ')), None))
                native = dict(declared, boot_epoch=epoch, clock_ticks_per_second=os.sysconf('SC_CLK_TCK'))
            else:
                native = _attest_health_actor_birth(generation, at)
            if (not isinstance(declared, dict) or declared.get('status') != 'verified'
                    or native.get('status') != 'verified' or native != declared
                    or any(value != declared for value in cohort_proofs)):
                return 'observer_current_main_birth_unproven'
        except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError):
            return 'observer_current_main_birth_unproven'
    return None


def _holding_profit_exit_semantics(root: Path, source_date: str, *, now: datetime | None = None) -> dict[str, Any]:
    """Check the sentinel's exact-date semantic receipt separately from freshness."""
    # The vote/terminal semantic payload was introduced for the next natural
    # trading session. Older sentinel files are audit history, not malformed
    # receipts under the new schema.
    if source_date < "2026-09-28":
        return {"status": "not_required_before_introduction", "findings": []}
    path = (root / "data/report/holding_exit_sentinel" /
            f"holding_exit_sentinel_{source_date}.json")
    meta = dict(source_date=source_date, target_date=source_date, artifact=str(path),
                report_sha256=None, native_validated=False, observation_complete=False)
    if not path.exists() and not path.is_symlink():
        markdown = path.with_suffix(".md")
        if markdown.exists() or markdown.is_symlink():
            return dict(meta, status="source_invalid", findings=["holding_semantic_json_missing_with_markdown_report"])
        if now is None:
            return dict(meta, status="not_assessed", findings=[])
        registry = next((r for r in ARTIFACT_REGISTRY if r["id"] == "holding_exit_sentinel_premarket_report"), None)
        if registry is None:
            return dict(meta, status="not_installed", findings=[])
        start = datetime.fromisoformat(source_date).replace(tzinfo=now.tzinfo, hour=registry["window_start"][0], minute=registry["window_start"][1])
        # Match the registry freshness check's inclusive initial publication
        # grace. Existing JSON/markdown artifacts are checked outside this branch.
        overdue = now > start + timedelta(seconds=registry.get("window_grace_sec", 0))
        return dict(meta, status="unobservable" if overdue else "future_due",
                    expected_overdue=overdue, findings=["holding_semantic_receipt_missing_after_due"] if overdue else [])
    try:
        if path.is_symlink() or path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("untrusted_path_or_size")
        report, raw_sha = _semantic_object(path, limit=8 * 1024 * 1024)
        meta["report_sha256"] = raw_sha
        semantics = report.get("profit_exit_semantics") or {}
        if (report.get("target_date") != source_date
                or semantics.get("target_date") != source_date
                or semantics.get("schema") not in {"holding_profit_exit_semantics_v1", "holding_profit_exit_semantics_v2"}
                or semantics.get("status") not in {
                    "pass", "valid_empty", "source_gap", "policy_binding_gap",
                    "runtime_not_consumed", "pending_terminal", "economics_null",
                    "semantic_contract_invalid", "pending_submit",
                }):
            raise ValueError("semantic_receipt_missing_or_invalid")
        if semantics["schema"] == "holding_profit_exit_semantics_v2":
            from src.engine.scalping.holding_profit_exit_semantics import LIFECYCLE_STATES, ECONOMICS_STATES
            states = {"pass", "valid_empty", "source_gap", "policy_binding_gap",
                      "runtime_not_consumed", "semantic_contract_invalid"}
            generation = semantics.get("source_generation")
            semantic_as_of = datetime.fromisoformat(str(semantics.get("as_of")))
            report_as_of = datetime.fromisoformat(str(report.get("as_of")))
            if report_as_of.tzinfo is None:
                report_as_of = report_as_of.replace(tzinfo=ZoneInfo("Asia/Seoul"))
            if (semantics.get("semantic_status") not in states
                    or semantics.get("economics_status") not in ECONOMICS_STATES
                    or not isinstance(semantics.get("lifecycle"), list)
                    or not isinstance(generation, str) or len(generation) != 64
                    or any(c not in "0123456789abcdef" for c in generation)
                    or report.get("source_generation") != generation
                    or semantic_as_of.tzinfo is None
                    or semantic_as_of.astimezone(ZoneInfo("Asia/Seoul")).date().isoformat() != source_date
                    or report_as_of.timestamp() != semantic_as_of.timestamp()):
                raise ValueError("semantic_v2_generation_or_state_invalid")
            identities = set()
            for row in semantics["lifecycle"]:
                identity = (row.get("position_key"), row.get("buy_fill_identity"), row.get("signal_id"))
                if (row.get("lifecycle_state") not in LIFECYCLE_STATES
                        or row.get("economics_status") not in ECONOMICS_STATES
                        or not all(isinstance(key, str) and key for key in identity)
                        or len(identity[1]) != 64 or identity in identities
                        or (row.get("economics_status") == "verified" and row.get("lifecycle_state") != "completed")):
                    raise ValueError("semantic_v2_lifecycle_invalid")
                identities.add(identity)
            expected_status = semantics["semantic_status"]
            if expected_status == "pass":
                expected_status = ("pending_submit" if any(row["lifecycle_state"] == "pending_submit" for row in semantics["lifecycle"]) else
                                   "pending_terminal" if any(row["lifecycle_state"] == "pending_terminal" for row in semantics["lifecycle"]) else "pass")
            expected_economics = ("unavailable" if any(row["economics_status"] == "unavailable" for row in semantics["lifecycle"]) else
                                  "pending" if not identities or any(row["economics_status"] == "pending" for row in semantics["lifecycle"]) else "verified")
            if (semantics.get("status") != expected_status
                    or semantics["economics_status"] != expected_economics
                    or (semantics["semantic_status"] == "valid_empty" and identities)
                    or semantics.get("decision_authority") != "report_only_no_order_or_policy_mutation"):
                raise ValueError("semantic_v2_status_inconsistent")
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        return dict(meta, **_semantic_failure(exc))
    status = semantics["status"]
    from src.engine.monitoring.semantic_incident_contract import holding_gap_identity
    return {
        **meta, "native_validated": True, "observation_complete": True,
        "source_generation": semantics.get("source_generation"), "observed_at": report.get("as_of"),
        "source_gap_examples": (semantics.get("source_gaps") or [])[:16],
        "native_finding_examples": (semantics.get("findings") or [])[:16],
        "lifecycle_examples": (semantics.get("lifecycle") or [])[:16],
        "status": status,
        "findings": ([status] if status in {
            "source_gap", "policy_binding_gap", "runtime_not_consumed",
            "economics_null",
            "semantic_contract_invalid"
        } else []),
        "signal_count": (semantics.get("funnel") or {}).get("tp_signal_snapshots", 0),
        "source_gap_count": len(semantics.get("source_gaps") or []),
        "source_gap_identity": holding_gap_identity(semantics),
        "invalid_count": len(semantics.get("findings") or []),
        "semantic_status": semantics.get("semantic_status", status),
        "lifecycle_counts": dict(Counter(row.get("lifecycle_state") for row in semantics.get("lifecycle", []))),
        "economics_status": semantics.get("economics_status", "unavailable"),
        "lifecycle_verified": semantics.get("schema") == "holding_profit_exit_semantics_v2",
    }


def _main_stop_semantics(root, source_date, *, now):
    from src.engine.automation.main_stop_postclose import read_committed, committed_path, START_DATE
    data_root = (Path(root) / "data").resolve()
    path = committed_path(data_root, source_date)
    meta = dict(source_date=source_date, target_date=None, artifact=str(path),
        report_sha256=None, native_validated=False, observation_complete=False, findings=[])
    if not path.exists():
        if source_date < START_DATE:
            return dict(meta, status="not_installed")
        overdue = source_date < now.date().isoformat()
        return dict(meta, status="unobservable" if overdue else "future_due",
            expected_overdue=overdue, findings=["main_stop_committed_missing_after_due"] if overdue else [])
    try:
        _, before = _semantic_object(path, limit=1024*1024)
        bundle, report, pointer, _ = read_committed(data_root, source_date)
        from src.engine.automation.main_stop_postclose import runtime_consumption
        consumed = runtime_consumption(data_root, bundle)
        if _semantic_object(path, limit=1024*1024)[1] != before:
            return dict(meta, status="unobservable", generation_changed=True)
        comparison = ('source_gap' if any(c['status']=='source_gap'
            or any(n and (key.startswith('source_gap:') or key=='actual_cost_or_terminal_gap')
                   for key,n in c.get('source_census',{}).items()) for c in bundle['cells'].values())
            else 'baseline_carry' if all(c['status']!='selected' for c in bundle['cells'].values()) else 'selected')
        trailing = dict(status='not_observed', findings=[])
        holding_path = data_root/'report/monitor_snapshots'/f'holding_exit_observation_{source_date}.json'
        if holding_path.exists():
            from src.engine.monitoring.main_trailing_currentness import observe
            try:
                holding, _ = _semantic_object(holding_path, limit=4*1024*1024)
                trailing = observe(data_root, holding, target_date=bundle['target_date'])
            except (OSError, ValueError, TypeError, KeyError) as exc:
                trailing = dict(status='source_invalid', findings=[str(exc)])
        findings = list(consumed['findings']) + [
            'main_trailing_research_contract_invalid:' + reason for reason in trailing['findings']]
        return dict(meta, status='source_invalid' if trailing['findings'] else "published_policy", report_sha256=before,
            target_date=bundle["target_date"], policy_sha256=bundle["policy_sha256"],
            native_generation=pointer["generation"], main_stop_native_validated=True,
            native_validated=not bool(trailing['findings']),
            observation_complete=not bool(trailing['findings']), actual_pid_consumed=consumed['actual_pid_consumed'],
            runtime_consumption=consumed, findings=findings, all_scope_trailing_generation=trailing,
            comparison_state=comparison,policy_states=dict(comparison_state=comparison))
    except (OSError, ValueError, TypeError, KeyError):
        return dict(meta, status="source_invalid", findings=["main_stop_committed_binding_invalid"])


def _quantity_stage_observation(stage, source_date, read, *, stage_path=None, data_root=None,
                                projection_role='current_stage'):
    """Observe issued bounded generations; full replay remains a producer gate."""
    from src.engine.scalping.initial_quantity_policy import _digest, REPORT_SCHEMA
    schema = stage.get('schema_version')
    refresh = schema == 'initial_entry_quantity_refresh_stage_v1'
    if (schema not in {'initial_entry_quantity_stage_terminal_v1', 'initial_entry_quantity_refresh_stage_v1'}
            or stage.get('source_date') != source_date
            or stage.get('stage') != ('initial_entry_quantity_refresh' if refresh else 'initial_entry_quantity_type_policy')
            or stage.get('generation_kind') != ('refresh' if refresh else 'initial_completed_trade_seed')
            or stage.get('stage_status') != 'complete_source_only' or stage.get('terminal') is not True
            or type(stage.get('all_completed_initial_trades')) is not int
            or stage['all_completed_initial_trades'] < 0
            or any(stage.get(key) is not False for key in ('runtime_apply_allowed', 'runtime_effect', 'actual_order_submitted'))
            or stage.get('receipt_content_sha256') != _digest({k:v for k,v in stage.items() if k != 'receipt_content_sha256'})):
        raise ValueError('quantity_stage_envelope_invalid')
    if stage_path is not None:
        from src.engine.scalping.initial_quantity_monitor_projection import read_verified
        projection = read_verified(stage_path, stage, read=read, data_root=data_root, role=projection_role)
        if projection is not None:
            return {**projection['issued'], 'monitor_projection_observation': projection['observation']}
    def child(name, hash_name=None):
        path = Path(stage[name + '_path'])
        if not path.is_absolute(): raise ValueError('quantity_stage_child_path_invalid')
        payload = read(path, limit=4*1024*1024, expected_sha=stage[name + '_file_sha256'])
        if hash_name is not None:
            if (payload.get(hash_name) != _digest({k:v for k,v in payload.items() if k != hash_name})
                    or payload[hash_name] != stage[name + '_content_sha256']):
                raise ValueError('quantity_stage_child_content_invalid')
        return payload
    report = child('report', 'report_content_sha256')
    if (report.get('schema_version') != REPORT_SCHEMA
            or report.get('generation_kind') != ('refresh_post_apply_replay' if refresh else 'initial_completed_trade_seed')
            or not isinstance(report.get('trades'), list)
            or any(report.get(key) is not False for key in ('runtime_apply_allowed', 'runtime_effect', 'actual_order_submitted'))
            or report.get('source_date') != source_date
            or (report.get('census') or {}).get('all_completed_initial_trades') != stage.get('all_completed_initial_trades')):
        raise ValueError('quantity_stage_report_binding_invalid')
    result = {'report': report}
    if refresh:
        parent = child('parent_policy', 'policy_content_sha256')
        from src.engine.scalping.initial_quantity_activation import refresh_parent_policy_valid
        if (not refresh_parent_policy_valid(parent)
                or parent['effective_from'] > source_date):
            raise ValueError('quantity_stage_parent_contract_invalid')
        evaluation = child('evaluation')
        from src.engine.scalping.initial_quantity_refresh_evaluation import VERSION, SELECTION_VERSION
        execution_version = report.get('evaluation_algorithm')
        selection_version = evaluation.get('evaluation_algorithm')
        if (execution_version not in {None, VERSION}
                or (execution_version == VERSION and selection_version not in {VERSION, SELECTION_VERSION})
                or (execution_version is None and selection_version is not None)):
            raise ValueError('quantity_stage_selection_algorithm_invalid')
        if (stage.get('applied_policy_lineage_schema') != 'initial_quantity_trade_policy_binding_v1'
                or stage.get('decision') not in {'carry_parent', 'eligible_source_only'}
                or _digest(evaluation) != stage['evaluation_content_sha256']
                or evaluation.get('source_date') != source_date
                or evaluation.get('state') != stage.get('decision')
                or evaluation.get('report_content_sha256') != report['report_content_sha256']
                or evaluation.get('parent_policy_content_sha256') != parent['policy_content_sha256']):
            raise ValueError('quantity_stage_evaluation_binding_invalid')
        timeout = child('timeout_research', 'report_content_sha256')
        if (stage.get('timeout_research_status') != 'source_bound'
                or timeout.get('source_date') != source_date
                or timeout.get('generation_kind') != 'refresh_post_apply_timeout_research'
                or any(timeout.get(key) != report.get(key) for key in ('census', 'quantity_type_counts', 'pipeline_source_receipts'))):
            raise ValueError('quantity_stage_timeout_binding_invalid')
        result.update(parent_policy=parent, evaluation=evaluation)
        if stage.get('decision') == 'eligible_source_only':
            candidate = child('candidate', 'policy_content_sha256')
            if (stage.get('candidate_status') != 'source_only'
                    or candidate.get('source_date') != source_date
                    or candidate.get('report_content_sha256') != report['report_content_sha256']
                    or candidate.get('evaluation_content_sha256') != stage['evaluation_content_sha256']
                    or candidate.get('parent_policy_content_sha256') != parent['policy_content_sha256']
                    or candidate.get('runtime_apply_allowed') is not False
                    or candidate.get('runtime_effect') is not False):
                raise ValueError('quantity_stage_candidate_binding_invalid')
            result['candidate'] = candidate
        elif any(key.startswith('candidate_') for key in stage):
            raise ValueError('quantity_stage_candidate_unexpected')
    else:
        candidate = child('candidate_policy', 'policy_content_sha256')
        if (candidate.get('source_date') != source_date
                or candidate.get('report_content_sha256') != report['report_content_sha256']
                or candidate.get('runtime_apply_allowed') is not False):
            raise ValueError('quantity_seed_candidate_binding_invalid')
        result['candidate'] = candidate
    following_status = stage.get('following_bar_source_status')
    if stage.get('following_bar_source_path') is not None:
        following = child('following_bar_source', 'report_content_sha256')
        if (following.get('source_date') != source_date
                or following.get('replay_content_sha256') != report['report_content_sha256']
                or following.get('input_manifest_sha256') != report['census'].get('input_manifest_sha256')
                or (refresh and following_status != 'source_bound')):
            raise ValueError('quantity_stage_following_binding_invalid')
    elif refresh and following_status not in {'no_winners', 'cap_profile_only'}:
        raise ValueError('quantity_stage_following_missing')
    elif refresh:
        winners = [row for row in report.get('trades', [])
                   if row.get('actual_net_pnl_krw', 0) > 0 and row.get('actual_profit_rate', 0) > 0]
        from src.engine.scalping.initial_quantity_policy import REPAIR_VERSION
        if ((following_status == 'no_winners' and winners)
                or (following_status == 'cap_profile_only'
                    and (not winners or report.get('evaluation_algorithm') != REPAIR_VERSION))):
            raise ValueError('quantity_stage_following_population_invalid')
    return result


def _quantity_current_observation(current_path, target_date, read):
    """Bound the selected policy ancestry without invoking PREOPEN validation."""
    from src.engine.scalping.initial_quantity_policy import _digest
    from src.engine.scalping.initial_quantity_activation import (
        CURRENT_SCHEMA, CURRENT_V2_SCHEMA, ENV_FILE, ENV_SHA, refresh_parent_policy_valid,
    )
    seen = set()
    cached = getattr(read, '_quantity_current_observations', None)
    if cached is None:
        cached = {}
        read._quantity_current_observations = cached
    def observe(path):
        path = Path(path)
        if path in cached: return cached[path]
        if path in seen or len(seen) >= 32 or not path.is_absolute():
            raise ValueError('quantity_current_ancestry_invalid')
        seen.add(path)
        current = read(path)
        if (current.get('schema_version') not in {CURRENT_SCHEMA, CURRENT_V2_SCHEMA}
                or current.get('current_content_sha256') != _digest({k:v for k,v in current.items() if k != 'current_content_sha256'})):
            raise ValueError('quantity_current_envelope_invalid')
        policy_path, stage_path = Path(current['policy_file']), Path(current['stage_file'])
        if not policy_path.is_absolute() or not stage_path.is_absolute():
            raise ValueError('quantity_current_child_path_invalid')
        policy = read(policy_path, expected_sha=current['policy_file_sha256'])
        stage = read(stage_path, expected_sha=current['stage_file_sha256'])
        if (not refresh_parent_policy_valid(policy)
                or any(policy.get(k) != current.get(k) for k in ('source_date', 'effective_from', 'policy_content_sha256'))
                or stage.get('receipt_content_sha256') != current['stage_receipt_content_sha256']
                or policy.get('candidate_stage_receipt_content_sha256') != current['stage_receipt_content_sha256']):
            raise ValueError('quantity_current_policy_binding_invalid')
        issued = _quantity_stage_observation(stage, current['source_date'], read, stage_path=stage_path,
            data_root=next((parent.resolve() for parent in current_path.parents if parent.name == 'data'), None),
            projection_role='issued_ancestry')
        candidate_name = 'candidate' if stage.get('generation_kind') == 'refresh' else 'candidate_policy'
        if (policy.get('candidate_policy_file_sha256') != stage.get(candidate_name + '_file_sha256')
                or policy.get('candidate_policy_content_sha256') != stage.get(candidate_name + '_content_sha256')
                or policy.get('report_content_sha256') != stage.get('report_content_sha256')
                or policy.get('input_manifest_sha256') != issued['report']['census'].get('input_manifest_sha256')
                or policy.get('source_date') != issued['candidate'].get('source_date')
                or policy.get('effective_from') != issued['candidate'].get('effective_from')
                or policy.get('following_bar_source_content_sha256') != stage.get('following_bar_source_content_sha256')
                or policy.get('all_completed_initial_trades') != stage.get('all_completed_initial_trades')):
            raise ValueError('quantity_current_candidate_binding_invalid')
        if current['schema_version'] == CURRENT_V2_SCHEMA:
            choices = issued['candidate']['type_policies']
            if (set(policy['type_policies']) != set(choices)
                    or any(any(row.get(key) != choices[name].get(key) for key in (
                        'ratio_mode', 'selected_shape', 'timeout_mode', 'selected_total_wait_sec'))
                        for name, row in policy['type_policies'].items())):
                raise ValueError('quantity_current_selected_choices_invalid')
            if stage.get('generation_kind') == 'refresh' and any(
                    policy.get(key) != stage.get(key) for key in (
                        'evaluation_content_sha256', 'timeout_research_content_sha256')):
                raise ValueError('quantity_current_refresh_references_invalid')
        if current['schema_version'] == CURRENT_V2_SCHEMA:
            parent_path = Path(current['parent_current_file'])
            parent = read(parent_path, expected_sha=current['parent_current_file_sha256'])
            parent_env = observe(parent_path)
            if (parent.get('current_content_sha256') != current['parent_current_sha256']
                    or parent_env[ENV_FILE] != current['parent_policy_file']
                    or parent_env[ENV_SHA] != current['parent_policy_file_sha256']
                    or parent.get('policy_content_sha256') != current['parent_policy_content_sha256']
                    or policy.get('parent_current_content_sha256') != current['parent_current_sha256']
                    or policy.get('parent_policy_content_sha256') != current['parent_policy_content_sha256']):
                raise ValueError('quantity_current_parent_binding_invalid')
            if stage.get('generation_kind') == 'refresh' and (
                    stage.get('parent_policy_path') != current['parent_policy_file']
                    or stage.get('parent_policy_file_sha256') != current['parent_policy_file_sha256']
                    or stage.get('parent_policy_content_sha256') != current['parent_policy_content_sha256']
                    or parent['effective_from'] >= current['effective_from']):
                raise ValueError('quantity_current_refresh_parent_invalid')
        elif current.get('parent_current_sha256') is not None:
            raise ValueError('quantity_baseline_parent_invalid')
        cached[path] = {ENV_FILE: str(policy_path), ENV_SHA: current['policy_file_sha256']}
        return cached[path]
    result = observe(current_path)
    selected = read(Path(result[ENV_FILE]))
    if selected['effective_from'] > target_date:
        raise ValueError('quantity_current_not_yet_effective')
    return result


def _quantity_data_mount_generation(root):
    """Pin the shared data directory without treating child writes as a move."""
    logical = root / 'data'
    try:
        resolved = logical.resolve()
    except RuntimeError as exc:
        raise ValueError('quantity_data_mount_invalid') from exc
    def identity(path):
        try:
            observed = path.lstat()
        except FileNotFoundError:
            return None
        result = (observed.st_dev, observed.st_ino, observed.st_mode)
        if stat.S_ISLNK(observed.st_mode):
            result += (observed.st_mtime_ns, observed.st_ctime_ns)
        return result
    return resolved, (identity(logical), identity(resolved))


def _quantity_completion_overlay_observation(root, source_date, census, facts, read):
    """Authenticate bounded terminal observations separately from entry facts."""
    fields = {'completion_overlay_generations', 'completion_overlay_summary',
              'as_of_completed_population_count'}
    present = fields.intersection(census)
    tagged = [row for row in facts if 'completion_generation' in row]
    if not present and not tagged:
        return {}
    if present != fields:
        raise ValueError('quantity_completion_overlay_census_missing')
    generations = census['completion_overlay_generations']
    summary = census['completion_overlay_summary']
    completed = sum(str(row.get('status')).upper() == 'COMPLETED' for row in facts)
    if (not isinstance(generations, dict) or not isinstance(summary, dict)
            or len(generations) > 256
            or any(not isinstance(day, str) or day > source_date for day in generations)
            or type(census['as_of_completed_population_count']) is not int
            or census['as_of_completed_population_count'] != completed):
        raise ValueError('quantity_completion_overlay_population_invalid')
    if not summary and not generations and not tagged:
        return {'postclose_as_of_completed_population_count': completed}
    from src.engine.scalping.initial_quantity_source_cache import (
        completion_fact_scope, verify_completion_overlay_generations,
        completion_generation_reference, QUANTITY_FACT_STRATEGIES,
    )
    from src.engine.lifecycle.broker_cost_reconciliation import record_source_projector
    from src.engine.scalping.initial_quantity_policy import _timestamp
    from src.engine.sniper_position_tags import normalize_strategy
    data_root, data_generation = _quantity_data_mount_generation(root)
    terminals = verify_completion_overlay_generations(
        generations, data_dir=data_root, read=read)
    if _quantity_data_mount_generation(root) != (data_root, data_generation):
        raise ValueError('quantity_data_mount_changed_during_read')
    native_by_day = {
        day: {str(row['recommendation_id']): row for row in rows}
        for day, rows in terminals.items()
    }
    completion_references = {day: completion_generation_reference(generation)
                             for day, generation in generations.items()}
    entry_generations = census.get('persisted_fact_generations') or {}
    entry_projectors = {day: record_source_projector(generation['cost_generation'])
        for day, generation in entry_generations.items()
        if isinstance(generation, dict) and isinstance(generation.get('cost_generation'), dict)
        and 'quantity_research_cost_generation' in generation['cost_generation']}
    start = census.get('entry_on_or_after', '2026-06-05')
    if (not isinstance(start, str) or date.fromisoformat(start).isoformat() != start
            or not '2026-06-05' <= start <= source_date):
        raise ValueError('quantity_completion_overlay_entry_window_invalid')
    latest_day, fixed_terminals = {}, {}
    input_ids = {str(row.get('recommendation_id')) for row in facts}
    excluded_native = Counter()
    for day in sorted(native_by_day):
        for rid, native in native_by_day[day].items():
            if not completion_fact_scope(native):
                if rid in input_ids:
                    raise ValueError('quantity_completion_overlay_custody_conflict')
                excluded_native['other_strategy' if native.get('strategy') not in
                                QUANTITY_FACT_STRATEGIES else 'other_custody'] += 1
                continue
            buy, sell = _timestamp(native.get('buy_time')), _timestamp(native.get('sell_time'))
            if buy is None or sell is None or not buy < sell or sell.date().isoformat() > day:
                raise ValueError('quantity_completion_overlay_clock_changed')
            if not start <= buy.date().isoformat() <= source_date:
                excluded_native['outside_actual_entry_window'] += 1
                continue
            fixed = (str(native.get('rec_date')), native.get('stock_code'),
                     normalize_strategy(native.get('strategy')), native.get('position_tag'),
                     native.get('buy_price'), native.get('buy_qty'), buy,
                     native.get('sell_price'), sell)
            if rid in fixed_terminals and fixed_terminals[rid] != fixed:
                raise ValueError('quantity_completion_overlay_terminal_conflict')
            fixed_terminals[rid], latest_day[rid] = fixed, day
    if set(latest_day) != {str(row.get('recommendation_id')) for row in tagged}:
        raise ValueError('quantity_completion_overlay_row_binding_invalid')
    overlaid_ids = []
    for row in tagged:
        day = row.get('completion_source_date')
        native = native_by_day.get(day, {}).get(str(row.get('recommendation_id')))
        entry_day = str(row.get('rec_date'))
        entry_generation = entry_generations.get(entry_day)
        if entry_day in entry_projectors:
            # Entry facts are projected before completion receipts are overlaid;
            # mirror that producer's record-only reference without receipt dates.
            entry_generation = {**entry_generation, 'cost_generation':
                entry_projectors[entry_day](str(row.get('recommendation_id')))}
        if (native is None or latest_day.get(str(row.get('recommendation_id'))) != day
                or row['completion_generation'] != completion_references.get(day)
                or str(row.get('status')).upper() != 'COMPLETED'
                or row.get('original_fact_status') is None
                or not isinstance(row.get('fact_generation'), dict)
                or row['fact_generation'] != entry_generation):
            raise ValueError('quantity_completion_overlay_row_binding_invalid')
        for field in ('rec_date', 'stock_code', 'strategy', 'position_tag', 'status',
                      'buy_price', 'buy_qty', 'sell_price', 'profit_rate',
                      'realized_pnl_krw', 'economics_source_status',
                      'actual_cost_reconciliation_status', 'actual_cost_source_generation',
                      'completion_census_run_id', 'completion_census_projection_sha256',
                      'broker_actual_fees_taxes_krw', 'quantity_research_cost'):
            actual, expected = row.get(field), native.get(field)
            if field == 'rec_date':
                actual, expected = str(actual), str(expected)
            elif field == 'strategy':
                actual, expected = normalize_strategy(actual), normalize_strategy(expected)
            if actual != expected:
                raise ValueError('quantity_completion_overlay_terminal_changed')
        if any(row.get(field) != native[field]
               for field in ('add_count', 'avg_down_count', 'pyramid_count')
               if field in native):
            raise ValueError('quantity_completion_overlay_scale_in_changed')
        count_fields = ('add_count', 'avg_down_count', 'pyramid_count')
        observations = {}
        for observed_day in sorted(native_by_day):
            if observed_day > day:
                continue
            prior = native_by_day[observed_day].get(str(row['recommendation_id']), {})
            for field in count_fields:
                if field in prior:
                    observations[field] = {'source_date': observed_day, 'value': prior[field]}
        if (row.get('completion_observed_scale_in_fields') != sorted(
                field for field in count_fields if field in native)
                or row.get('completion_scale_in_observations') != observations
                or any(row.get(field) != observation['value']
                       for field, observation in observations.items())):
            raise ValueError('quantity_completion_overlay_scale_in_changed')
        if any(_timestamp(row.get(field)) != _timestamp(native.get(field))
               for field in ('buy_time', 'sell_time')):
            raise ValueError('quantity_completion_overlay_clock_changed')
        if str(row['original_fact_status']).upper() != 'COMPLETED':
            overlaid_ids.append(str(row['recommendation_id']))
    original_counts = dict(Counter(str(row.get('original_fact_status', row.get('status')))
                                   for row in facts))
    current_counts = dict(Counter(str(row.get('status')) for row in facts))
    if (not isinstance(summary, dict)
            or summary.get('schema') != 'initial_quantity_completion_overlay_v1'
            or summary.get('as_of') != source_date
            or summary.get('source_scope') != 'entry_day_facts_plus_exact_completion_date_observations'
            or summary.get('entry_day_database_or_source_mutation') is not False
            or summary.get('original_fact_status_counts') != original_counts
            or summary.get('current_fact_status_counts') != current_counts
            or summary.get('overlaid_record_ids') != sorted(overlaid_ids)
            or type(summary.get('overlaid_completed_count')) is not int
            or summary['overlaid_completed_count'] != len(overlaid_ids)
            or type(summary.get('native_terminal_record_count')) is not int
            or summary['native_terminal_record_count'] != len({
                rid for rows in native_by_day.values() for rid in rows})
            or type(summary.get('native_terminal_observation_count')) is not int
            or summary.get('native_terminal_observation_count') != sum(map(len, native_by_day.values()))
            or type(summary.get('applicable_terminal_record_count')) is not int
            or summary.get('applicable_terminal_record_count') != len(tagged)
            or summary.get('excluded_native_terminal_observation_counts') != dict(excluded_native)
            or any(not isinstance(summary.get(field), dict)
                   or any(type(value) is not int or value < 0 for value in summary[field].values())
                   for field in ('original_fact_status_counts', 'current_fact_status_counts',
                                 'excluded_native_terminal_observation_counts'))
            or len({str(row.get('recommendation_id')) for row in tagged}) != len(tagged)):
        raise ValueError('quantity_completion_overlay_summary_invalid')
    return dict(postclose_as_of_completed_population_count=completed,
                postclose_original_fact_status_counts=original_counts,
                postclose_completion_overlay_summary=summary,
                postclose_completion_overlay_generation_count=len(generations))


def _quantity_postclose_stage_observation(root, source_date, stage, report, evaluation, read):
    """Shared seed/refresh census observations; never execution authority."""
    from src.engine.scalping.initial_quantity_policy import _digest
    from src.engine.scalping.initial_quantity_refresh_evaluation import economic_sample_status
    refresh = stage.get('generation_kind') == 'refresh'
    count = stage['all_completed_initial_trades']
    decision = stage.get('decision') if refresh else 'initial_policy_seed'
    census = report['census']
    facts, excluded = census['input_fact_rows'], census['excluded']
    if (not isinstance(facts, list) or not isinstance(excluded, dict)
            or any(not isinstance(row, dict) for row in facts)
            or any(type(n) is not int or n < 0 for n in excluded.values())
            or census['fact_rows_read'] != len(facts)
            or census['all_completed_initial_trades'] != count
            or count != len(report['trades'])
            or len(facts) != count + sum(excluded.values())
            or census.get('input_manifest_sha256') != _digest(facts)
            or report['source_date'] != source_date
            or refresh and (not isinstance(evaluation, dict)
                or evaluation.get('report_content_sha256') != report['report_content_sha256']
                or evaluation.get('source_date') != source_date)
            or not refresh and evaluation is not None):
        raise ValueError('quantity_input_census_binding_invalid')
    observation = _quantity_completion_overlay_observation(root, source_date, census, facts, read)
    benign = {'not_completed', 'other_strategy', 'other_custody', 'scale_in_position',
              'before_refresh_start', 'duplicate_fact', 'date_outside_baseline_or_as_of'}
    gaps = {key:n for key,n in excluded.items() if n and key not in benign}
    economic = economic_sample_status(report)
    binding = evaluation.get('trade_policy_binding_status') if refresh else 'not_required_initial_policy'
    if refresh and (economic not in {'valid_empty', 'cost_eligible', 'source_gap', 'cost_missing'}
            or evaluation.get('economic_sample_status') != economic
            or binding not in {'valid_empty', 'bound', 'partial', 'source_gap'}
            or count == 0 and binding != ('valid_empty' if economic == 'valid_empty' else 'source_gap')
            or count > 0 and binding not in {'bound', 'partial'}):
        raise ValueError('quantity_evaluation_observation_status_invalid')
    source_gap = bool(gaps or economic in {'source_gap', 'cost_missing'} or binding in {'partial', 'source_gap'})
    observation.update(policy_refresh_decision=decision,
        postclose_input_fact_count=len(facts),
        postclose_completed_input_count=sum(str(row.get('status', '')).upper() == 'COMPLETED' for row in facts),
        postclose_exclusion_reasons=excluded, postclose_source_gap_reasons=gaps,
        economic_sample_status=economic, trade_policy_binding_status=binding,
        following_bar_source_status=stage.get('following_bar_source_status'),
        bundle_observation_scope='dedicated_multi_leg_journal_only',
        postclose_stage_status=('source_gap' if source_gap else 'valid_empty'
            if count == 0 and decision == 'carry_parent' else decision),
        postclose_completed_trade_count=count,
        postclose_semantic_findings=['initial_quantity_economic_source_gap'] if source_gap else [])
    return observation


def _initial_quantity_semantics_native(
    root: Path, source_date: str, *, now_epoch: float | None = None, read=None,
) -> dict[str, Any]:
    """Read-only quantity, sequential leg, and post-start timeout checks."""
    if source_date < "2026-09-28":
        return {"status": "not_required_before_introduction", "findings": []}
    from src.engine.scalping.initial_quantity_activation import (
        ENV_FILE, ENV_SHA,
    )
    from src.engine.scalping.initial_quantity_bundle_state import bundle_state_valid
    from src.engine.scalping.initial_quantity_policy import _digest

    current_path = root / "data/runtime/initial_quantity/current.json"
    if not current_path.is_file() or current_path.is_symlink():
        return {"status": "source_invalid", "findings": [
            "initial_quantity_current_missing_or_untrusted"]}
    try:
        if current_path.stat().st_size > 1024 * 1024:
            raise ValueError("current_oversize")
        # Postclose may have selected tomorrow's policy already. Validate that
        # chain, then inspect the ancestor that actually applied on this date.
        seen_current: set[Path] = set()
        while True:
            if current_path in seen_current or len(seen_current) >= 32:
                raise ValueError("current_parent_cycle")
            seen_current.add(current_path)
            current = read(current_path)
            effective = str(current.get("effective_from") or "")
            _quantity_current_observation(current_path, effective, read)
            if effective <= source_date:
                break
            parent = current.get("parent_current_file")
            if not isinstance(parent, str) or not parent:
                raise ValueError("current_parent_missing")
            current_path = Path(parent)
            if (not current_path.is_absolute() or current_path.is_symlink()
                    or not current_path.is_file()
                    or current_path.stat().st_size > 1024 * 1024):
                raise ValueError("current_parent_untrusted")
        env = _quantity_current_observation(current_path, source_date, read)
        policy_path = Path(env[ENV_FILE])
        policy = read(policy_path)
        policy_sha = env[ENV_SHA]
        rows = policy["type_policies"]
        if not isinstance(rows, dict) or not rows:
            raise ValueError("policy_types_missing")
        # Intraday successors do not rewrite policies pinned by earlier BUYs or
        # earlier PIDs. Only the native verified ancestry is admissible.
        verified_policies = {policy_sha: (policy_path, policy)}
        ancestor = current
        ancestors_seen = set()
        while ancestor.get("parent_current_file"):
            ancestor_path = Path(ancestor["parent_current_file"])
            if ancestor_path in ancestors_seen or len(ancestors_seen) >= 32:
                raise ValueError("initial_quantity_ancestor_cycle_or_oversize")
            ancestors_seen.add(ancestor_path)
            ancestor = read(ancestor_path)
            ancestor_env = _quantity_current_observation(ancestor_path, source_date, read)
            ancestor_policy_path = Path(ancestor_env[ENV_FILE])
            ancestor_policy = read(ancestor_policy_path)
            verified_policies[ancestor_env[ENV_SHA]] = (ancestor_policy_path, ancestor_policy)

    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return {"status": "source_invalid", "findings": [
            "initial_quantity_current_binding_invalid:" + type(exc).__name__]}

    details: dict[str, Any] = {
        "status": "policy_selected", "findings": [],
        "policy_file_sha256": policy_sha,
        "quantity_type_count": len(rows),
        "ratio_modes": dict(Counter(
            str(row.get("ratio_mode")) for row in rows.values())),
        "selected_shapes": dict(Counter(
            str(row.get("selected_shape")) for row in rows.values())),
        "timeout_modes": dict(Counter(
            str(row.get("timeout_mode")) for row in rows.values())),
        "runtime_pid_status": "not_observed",
        "runtime_consumption_scope": "pid_env_receipt_only",
        "postclose_stage_status": "not_observed",
        "bundle_count": 0, "terminal_bundle_count": 0,
        "open_bundle_count": 0,
        "quantity_lineage_status": "not_observed",
        "validation_scope": "bounded_issued_generations_and_policy_ancestry",
        "full_source_revalidation_performed": False,
    }
    output_dir = root / 'data/report/initial_entry_quantity_type_policy' / f'refresh_postclose_{source_date}'
    stage_expected_sha = None
    try:
        pointer = output_dir / 'committed_stage.json'
        if pointer.exists() or pointer.is_symlink():
            ref = read(pointer, limit=65536)
            stage_path = Path(ref['stage_path'])
            stage_expected_sha = ref['stage_sha256']
            if (ref.get('schema') != 'initial_quantity_stage_reference_v2'
                    or ref.get('source_date') != source_date or not stage_path.is_absolute()
                    or stage_path.is_symlink()
                    or not stage_path.resolve().is_relative_to(output_dir.resolve() / 'generations')
                    or re.fullmatch(r'[0-9a-f]{64}', str(stage_expected_sha)) is None):
                raise ValueError('quantity_stage_reference_invalid')
        else:
            stage_path = output_dir / f'initial_quantity_refresh_stage_{source_date}.json'
    except (OSError, ValueError, KeyError, TypeError):
        details["findings"].append("initial_quantity_stage_reference_invalid")
        details['status'] = 'source_invalid'
        details["postclose_stage_status"] = "source_invalid"
        return details
    if stage_path.exists() or stage_path.is_symlink():
        try:
            if stage_path.is_symlink() or stage_path.stat().st_size > 1024 * 1024:
                raise ValueError("stage_untrusted_or_oversize")
            stage = read(stage_path, expected_sha=stage_expected_sha)
            observed = _quantity_stage_observation(stage, source_date, read, stage_path=stage_path,
                                                   data_root=(root/'data').resolve())
            observation = (dict(observed['monitor_projection_observation'])
                if 'monitor_projection_observation' in observed else
                _quantity_postclose_stage_observation(root, source_date, stage,
                    observed['report'], observed.get('evaluation'), read))
            details['findings'].extend(observation.pop('postclose_semantic_findings'))
            details.update(observation)
        except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
            details["findings"].append(
                "initial_quantity_stage_invalid:" + type(exc).__name__)
            details["postclose_stage_status"] = "source_invalid"
    elif source_date < datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat():
        details["postclose_stage_status"] = "source_gap"
        details["findings"].append("initial_quantity_stage_missing_after_date")

    archive_dir = (root / "data/runtime/policy_bootstrap" /
                   "verified_initial_quantity_pid" / source_date)
    if archive_dir.is_symlink():
        details["findings"].append("initial_quantity_pid_archive_untrusted")
    if archive_dir.is_dir() and not archive_dir.is_symlink():
        verified = 0
        for index, receipt_path in enumerate(sorted(
                archive_dir.glob("initial_quantity_pid_*.json"))):
            if index >= 64:
                details["findings"].append("initial_quantity_pid_archive_oversize")
                break
            try:
                if (receipt_path.is_symlink()
                        or receipt_path.stat().st_size > 1024 * 1024):
                    raise ValueError("pid_receipt_untrusted_or_oversize")
                receipt = read(receipt_path)
                body = {k: v for k, v in receipt.items()
                        if k != "receipt_content_sha256"}
                digest = hashlib.sha256(json.dumps(
                    body, ensure_ascii=True, allow_nan=False, sort_keys=True,
                    separators=(",", ":")).encode()).hexdigest()
                verification = receipt.get("verification") or {}
                pinned_path, pinned_policy = verified_policies.get(receipt.get("policy_file_sha256"), (None, {}))
                if (receipt.get("schema_version") !=
                        "initial_quantity_pid_verification_v1"
                        or receipt.get("target_date") != source_date
                        or receipt_path.name != (
                            f"initial_quantity_pid_{receipt.get('pid')}_"
                            f"{str(receipt.get('receipt_content_sha256') or '')[:12]}.json")
                        or pinned_path is None
                        or receipt.get("policy_file") != str(pinned_path.resolve())
                        or receipt.get("policy_content_sha256") !=
                        pinned_policy.get("policy_content_sha256")
                        or receipt.get("receipt_content_sha256") != digest
                        or verification.get("target_date") != source_date
                        or verification.get("status") != "pass"
                        or verification.get("passed") is not True
                        or verification.get("pid_passed") is not True
                        or verification.get("pid_env_available") is not True
                        or verification.get("findings") != []
                        or verification.get("pid_mismatches") != []
                        or verification.get("pid") != receipt.get("pid")
                        or verification.get("manifest_sha256") !=
                        receipt.get("manifest_sha256")):
                    raise ValueError("pid_receipt_binding_invalid")
                verified += 1
            except (OSError, ValueError, TypeError, AttributeError):
                details["findings"].append("initial_quantity_pid_receipt_invalid")
        if verified:
            details["runtime_pid_status"] = "verified_receipt"
            details["verified_pid_count"] = verified
    latest_pid_path = (root / "data/runtime/policy_bootstrap" /
                       f"runtime_policy_bootstrap_verify_{source_date}.json")
    if (details["runtime_pid_status"] == "not_observed"
            and latest_pid_path.is_file() and not latest_pid_path.is_symlink()):
        try:
            if latest_pid_path.stat().st_size > 1024 * 1024:
                raise ValueError("pid_verify_oversize")
            latest = read(latest_pid_path)
            if (latest.get("target_date") == source_date
                    and latest.get("pid_passed") is True):
                details["findings"].append("initial_quantity_pid_archive_missing")
        except (OSError, ValueError, TypeError, AttributeError):
            details["findings"].append("initial_quantity_pid_verify_invalid")

    bundle_dir = root / "data/runtime/initial_quantity/bundles"
    if bundle_dir.is_symlink():
        details["findings"].append("initial_quantity_bundle_dir_untrusted")
    if bundle_dir.is_dir() and not bundle_dir.is_symlink():
        now = time.time() if now_epoch is None else now_epoch
        for index, path in enumerate(bundle_dir.glob("*.json")):
            if index >= 5000:
                details["findings"].append("initial_quantity_bundle_inventory_oversize")
                break
            belongs_to_date = False
            try:
                if path.is_symlink() or path.stat().st_size > 1024 * 1024:
                    raise ValueError("bundle_untrusted_or_oversize")
                bundle = read(path)
                schedule = bundle.get("schedule") or {}
                belongs_to_date = (
                    str(schedule.get("order_start_at") or "")[:10] == source_date)
                if not belongs_to_date:
                    if (not schedule.get("order_start_at")
                            and datetime.fromtimestamp(
                                path.stat().st_mtime,
                                ZoneInfo("Asia/Seoul")).date().isoformat()
                            == source_date):
                        raise ValueError("bundle_date_missing")
                    continue
                if (not bundle_state_valid(bundle)
                        or path.name != hashlib.sha256(
                            bundle["attempt_id"].encode()).hexdigest() + ".json"):
                    raise ValueError("bundle_contract_invalid")
                details["bundle_count"] += 1
                details["quantity_lineage_status"] = "journal_conservation_only"
                states = bundle["leg_states"]
                terminal = all(item["state"].startswith("TERMINAL_")
                               for item in states)
                if terminal:
                    details["terminal_bundle_count"] += 1
                else:
                    details["open_bundle_count"] += 1
                    if now > schedule["bundle_deadline_epoch"]:
                        details["findings"].append(
                            "initial_quantity_bundle_terminal_overdue")
                if any(item.get("terminal_confirmed_at_epoch", 0) >
                       schedule["slots"][index]["terminal_confirm_by_epoch"]
                       for index, item in enumerate(states)
                       if item["state"].startswith("TERMINAL_")):
                    details["findings"].append(
                        "initial_quantity_leg_terminal_after_slot")
                bundle_policy = verified_policies.get(bundle["policy_sha256"])
                if bundle_policy is None:
                    details["findings"].append(
                        "initial_quantity_bundle_policy_mismatch")
                else:
                    row = bundle_policy[1]["type_policies"].get(schedule["quantity_type"]) or {}
                    shape = row.get("selected_shape")
                    expected = (2 if str(shape).startswith("two_leg_") else
                                3 if str(shape).startswith("three_leg_") else 0)
                    if (expected == 0 or bundle["requested_qty"] < 2
                            or schedule["leg_count"] !=
                            min(bundle["requested_qty"], expected)
                            or (row.get("timeout_mode") == "selected_total_wait_sec"
                                and row.get("selected_total_wait_sec") !=
                                schedule["total_wait_sec"])):
                        details["findings"].append(
                            "initial_quantity_bundle_policy_mismatch")
            except (OSError, ValueError, TypeError, KeyError, AttributeError):
                try:
                    file_day = datetime.fromtimestamp(
                        path.lstat().st_mtime,
                        ZoneInfo("Asia/Seoul")).date().isoformat()
                except OSError:
                    file_day = None
                if belongs_to_date or file_day == source_date:
                    details["findings"].append("initial_quantity_bundle_invalid")
    if details["findings"]:
        details["status"] = "source_invalid" if any(
            item not in {"initial_quantity_bundle_terminal_overdue",
                         "initial_quantity_leg_terminal_after_slot",
                         "initial_quantity_economic_source_gap",
                         "initial_quantity_stage_missing_after_date"}
            for item in details["findings"]) else (
                "source_gap" if any(item in details['findings'] for item in (
                    "initial_quantity_stage_missing_after_date",
                    "initial_quantity_economic_source_gap")) else "pending_terminal")
    elif details["bundle_count"] == 0 and details["postclose_stage_status"] == "valid_empty":
        details["status"] = "valid_empty"
    elif details["bundle_count"]:
        details["status"] = (
            "journal_terminal_observed" if not details["open_bundle_count"] else
            "pending_terminal")
    return details


def _initial_quantity_semantics(root: Path, source_date: str, *, now_epoch=None):
    references = []
    read_bytes = 0
    cache = {}
    source_identities = {}
    def read(path, *, limit=1024*1024, expected_sha=None):
        nonlocal read_bytes
        path = Path(path)
        actual = existing_or_gzip_path(path)
        if not path.is_absolute() or actual.is_symlink():
            raise ValueError('quantity_semantic_path_invalid')
        metadata = actual.stat()
        before = _observer_file_signature(metadata)
        if metadata.st_size > limit:
            raise ValueError('semantic_artifact_untrusted_path_or_size')
        key = (str(path), str(actual), before)
        identity_key = str(path)
        if identity_key in source_identities and source_identities[identity_key] != key:
            raise ValueError('semantic_generation_changed_during_read')
        source_identities[identity_key] = key
        if key in cache:
            value, sha = cache[key]
            if expected_sha is not None and sha != expected_sha:
                raise ValueError('quantity_semantic_bound_generation_changed')
            return value
        if read_bytes + metadata.st_size > 32 * 1024 * 1024:
            raise ValueError("semantic_read_budget_oversize")
        observed = {}
        value, sha = _semantic_object(path, limit=min(limit, 32*1024*1024-read_bytes), observation=observed)
        read_bytes += observed['logical_bytes']
        if read_bytes > 32 * 1024 * 1024:
            raise ValueError('semantic_read_budget_oversize')
        if (existing_or_gzip_path(path) != actual
                or _observer_file_signature(actual.stat()) != before):
            raise ValueError('semantic_generation_changed_during_read')
        if expected_sha is not None and sha != expected_sha:
            raise ValueError('quantity_semantic_bound_generation_changed')
        references.append((path, actual, sha, before))
        cache[key] = (value, sha)
        return value
    result = _initial_quantity_semantics_native(root, source_date, now_epoch=now_epoch, read=read)
    result.update(source_date=source_date, target_date=source_date,
        artifact=str(root / "data/runtime/initial_quantity/current.json"),
        report_sha256=None, native_validated=False, bounded_contract_validated=False,
        observation_complete=False)
    try:
        for logical, actual, sha, before in references:
            st = actual.stat()
            if existing_or_gzip_path(logical) != actual or before != _observer_file_signature(st):
                raise ValueError("semantic_generation_changed_during_read")
        complete = not any("oversize" in x for x in result.get("findings", []))
        valid_contract = complete and result.get('status') != 'source_invalid'
        result.update(native_validated=False, bounded_contract_validated=valid_contract,
            full_source_revalidation_performed=False, observation_complete=valid_contract,
            observation_generation=hashlib.sha256(json.dumps([(str(p), str(a), sha) for p, a, sha, _ in references], separators=(",", ":")).encode()).hexdigest(),
            source_reference_count=len(references),
            source_references=[dict(artifact=str(p), physical_artifact=str(a), byte_sha256=sha) for p, a, sha, _ in references[:16]])
        if references:
            # The policy pointer bytes are an artifact hash, not the composite digest.
            result["report_sha256"] = references[0][2]
        if not complete:
            result.update(status="unobservable", expected_overdue=True)
    except (OSError, ValueError):
        result.update(status="unobservable", findings=[], generation_changed=True)
    return result


def _semantic_object(path: Path, *, limit: int = 64 * 1024 * 1024,
                     hash_only: bool = False, observation: dict | None = None) -> tuple[dict, str]:
    """Reuse small decoded inputs only within the current validation invocation.

    Validator decisions and external dependencies are always evaluated again.
    Large objects retain the bounded streaming/hash path rather than a cache.
    """
    from copy import deepcopy
    from src.engine.infrastructure.validation_digest_session import ACTIVE, MAX_ENTRIES, identity
    session = ACTIVE.get()
    if session is None or session.invocation_pid != os.getpid():
        return _read_semantic_object(path, limit=limit, hash_only=hash_only, observation=observation)
    actual = existing_or_gzip_path(path)
    before = identity(actual)
    key = (str(actual.absolute()), limit, hash_only)
    entry = session.semantic_objects.get(key)
    if entry and entry[0] == before and time.monotonic() - entry[2] <= session.ttl:
        if observation is not None: observation['logical_bytes'] = entry[3]
        session.stats['semantic_reused_reads'] += 1
        return deepcopy(entry[1])
    details = {}
    result = _read_semantic_object(path, limit=limit, hash_only=hash_only, observation=details)
    if identity(actual) != before:
        raise ValueError('semantic_generation_changed_during_read')
    size = details['logical_bytes']
    if observation is not None: observation.update(details)
    if size <= 1024 * 1024:
        if session.semantic_bytes + size > 4 * 1024 * 1024 or len(session.semantic_objects) >= MAX_ENTRIES:
            session.semantic_objects.clear();session.semantic_bytes = 0
        session.semantic_objects[key] = (before, deepcopy(result), time.monotonic(), size)
        session.semantic_bytes += size
    return result


def _read_semantic_object(path: Path, *, limit: int = 64 * 1024 * 1024,
                     hash_only: bool = False, observation: dict | None = None) -> tuple[dict, str]:
    """Read one bounded, stable generation without following file symlinks."""
    actual = existing_or_gzip_path(path)
    if actual.is_symlink() or actual.stat().st_size > limit:
        raise ValueError("semantic_artifact_untrusted_path_or_size")
    before = actual.stat()
    try:
        with _observer_regular_fd(actual, max_bytes=limit) as fd:
            with os.fdopen(os.dup(fd), 'rb') as physical:
                handle = gzip.GzipFile(fileobj=physical, mode='rb') if actual.suffix == '.gz' else physical
                try:
                    if hash_only:
                        digest, size = hashlib.sha256(), 0
                        while chunk := handle.read(128 * 1024):
                            size += len(chunk)
                            if size > limit:
                                raise ValueError("semantic_artifact_uncompressed_size_exceeded")
                            digest.update(chunk)
                    else:
                        raw = handle.read(limit + 1)
                finally:
                    if handle is not physical: handle.close()
    except (EOFError, gzip.BadGzipFile, zlib.error) as exc:
        raise ValueError('semantic_artifact_compression_invalid') from exc
    except ValueError as exc:
        if str(exc) in {'observer_file_changed_before_read', 'observer_file_changed_during_read'}:
            raise ValueError('semantic_generation_changed_during_read') from exc
        raise
    after = actual.stat()
    if (before.st_ino, before.st_mtime_ns, before.st_ctime_ns, before.st_size) != (
            after.st_ino, after.st_mtime_ns, after.st_ctime_ns, after.st_size):
        raise ValueError("semantic_generation_changed_during_read")
    if hash_only:
        if observation is not None: observation['logical_bytes'] = size
        return {}, digest.hexdigest()
    if len(raw) > limit:
        raise ValueError("semantic_artifact_uncompressed_size_exceeded")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("semantic_artifact_object_invalid")
    if observation is not None: observation['logical_bytes'] = len(raw)
    return value, hashlib.sha256(raw).hexdigest()


def _semantic_failure(exc):
    if str(exc) == "semantic_generation_changed_during_read":
        return {"status": "unobservable", "findings": [], "reason": str(exc)}
    return {"status": "source_invalid", "findings": [str(exc)]}


def _semantic_stage_binding(root, day, stage, *, artifact=None, artifact_sha=None, artifact_path=None):
    path = root / "data/report/postclose_stage_terminal" / day / f"{stage}.json"
    if not (path.exists() or path.is_symlink()):
        return {"status": "not_assessed"}
    value, _ = _semantic_object(path, limit=1024 * 1024)
    body = {k: v for k, v in value.items() if k != "receipt_sha256"}
    digest = hashlib.sha256(json.dumps(body, ensure_ascii=True, sort_keys=True,
                                      separators=(",", ":")).encode()).hexdigest()
    if (value.get("schema") not in ({"postclose_stage_terminal_v3", "postclose_stage_terminal_v2"} if day < "2026-10-06" else {"postclose_stage_terminal_v3"})
        or value.get("source_date") != day or value.get("stage_id") != stage
        or value.get("receipt_sha256") != digest):
        raise ValueError(f"{stage}:terminal_identity_or_hash_invalid")
    if value.get("status") == "succeeded":
        if value.get("exit_code") != 0:
            raise ValueError(f"{stage}:terminal_exit_invalid")
        if artifact is not None:
            source = (value.get("sources") or {}).get(artifact) or {}
            if source.get("sha256") != artifact_sha or not artifact_sha:
                raise ValueError(f"{stage}:completed_report_generation_mismatch")
            if artifact_path is not None and source.get("path") != str(artifact_path.resolve()):
                raise ValueError(f"{stage}:terminal_source_path_invalid")
    if value.get('status') == 'off' and value.get('off_reason') != 'explicit_schedule_disabled':
        raise ValueError(f'{stage}:terminal_off_reason_invalid')
    return {"status": value.get("status"), "receipt_sha256": digest, 'off_reason': value.get('off_reason')}


def _continuous_reversal_result_semantics(root, source_date, component, *, now=None):
    """Consume the native reversal contract, without legacy economics gates."""
    report_path = root / 'data/report/continuous_reversal' / source_date / (component + '.json')
    if not report_path.exists() and not report_path.is_symlink():
        from src.engine.scalping import mechanistic_entry_runtime_policy as native
        dated = native.root(root / 'data') / ('policy_' + native.next_target(source_date) + '.json')
        if not dated.exists() and not dated.is_symlink():
            return None
        try:
            candidate, _ = _semantic_object(dated)
            if not candidate.get('continuous_reversal'):
                return None
        except (OSError, ValueError, TypeError, KeyError):
            return dict(status='source_invalid', findings=['continuous_reversal_dated_policy_invalid'],
                        source_date=source_date, artifact=str(dated))
    report_sha = None
    try:
        from src.engine.scalping import continuous_reversal_postclose as reports
        from src.engine.scalping import continuous_reversal_policy as policy
        from src.engine.scalping import mechanistic_entry_runtime_policy as native
        report, report_sha = _semantic_object(report_path)
        from src.engine.scalping.continuous_reversal_registered_postclose import SCHEMA as registered_schema
        from src.engine.scalping.continuous_reversal_path_postclose import SCHEMA as path_schema
        from src.engine.scalping.continuous_reversal_operating_postclose import SCHEMA as operating_schema
        if report.get('schema') not in {reports.SCHEMA,registered_schema,path_schema,operating_schema}:
            raise ValueError('continuous_reversal_report_schema_invalid')
        if (report != reports.seal(report) or report.get('source_date') != source_date
                or report.get('status') not in {'completed','completed_with_scope_carry'}):
            raise ValueError('continuous_reversal_report_hash_or_date_invalid')
        stage_id = 'main_machine_policy' if component == 'machine' else 'main_auxiliary_policy'
        for required in ('main_machine_policy', 'main_auxiliary_policy'):
            stage = _semantic_stage_binding(root, source_date, required)
            if stage['status'] in {'pending', 'running'}:
                return dict(status='unobservable', findings=[], stage_id=stage_id, execution=stage)
            if stage['status'] == 'not_assessed':
                owner = next(item for item in ARTIFACT_REGISTRY if item['id'] == 'threshold_postclose_status')
                parent = root / owner['path_template'].format(date=source_date)
                if ArtifactFreshnessDetector._is_bounded_postclose_running(
                        owner, parent, source_date, now or datetime.now(ZoneInfo('Asia/Seoul')), root=root):
                    return dict(status='unobservable', findings=[], stage_id=stage_id, execution=stage,
                                reason='native_postclose_stage_not_started')
            if stage['status'] != 'succeeded':
                raise ValueError('continuous_reversal_execution_not_completed:' + required)
        if component == 'machine':
            bound_path = root / 'data/report/ai_decision_action_outcome_calibration' / f'winrate_policy_{source_date}.json'
            artifact = 'machine_policy'
        else:
            bound_path = root / 'data/report/ai_entry_setup_paired_replay_batch' / f'compact_auxiliary_paired_economic_{source_date}.json'
            artifact = 'compact_auxiliary_paired_economic'
        bound, bound_sha = _semantic_object(bound_path)
        _semantic_stage_binding(root, source_date, stage_id, artifact=artifact,
                                artifact_sha=bound_sha, artifact_path=bound_path)
        if component == 'auxiliary':
            bound = reports.seal({k: v for k, v in bound.items() if k not in {'staged', 'artifact_content_sha256'}})
        if bound != report:
            raise ValueError('continuous_reversal_stage_report_mismatch')
        handoff = policy.direct_handoff(root / 'data', source_date)
        bundle = native.load(data_root=root / 'data', target_date=handoff['effective_date'])
        from src.engine.scalping.reversal_policy_status import report_state, current_view
        states=report_state(report)
        semantic={'operator_designated':'operator_initial_registered','carried':'verified_carried','comparison_selected':'cumulative_winrate_selected'}.get(states['adoption_basis'],'published_policy')
        if states['comparison_state']=='source_gap':semantic='source_gap'
        try:runtime=current_view(root/'data')
        except (OSError,ValueError,KeyError,TypeError):runtime={'status':'not_observed'}
        return dict(status=semantic, native_validated=True, observation_complete=True, policy_states=states, current_policy_status=runtime, findings=[], stage_id=stage_id,
                    source_date=source_date, target_date=handoff['effective_date'],
                    artifact=str(report_path), report_sha256=report_sha,
                    selection_metric=handoff['selection_metric'],
                    cells=bundle['continuous_reversal'][component + '_cells'],
                    comparison_complete=report.get('comparison_complete'),
                    component_comparison_complete=report.get('comparison_complete'),
                    joint_comparison_complete=handoff.get('comparison_complete'),
                    scope_pending=report.get('scope_pending',[]),
                    joint_scope_pending=handoff.get('scope_pending',[]),
                    scope_census=report.get('scope_census'),
                    joint_scope_census=handoff.get('scope_census'),
                    bound_target_date=handoff['effective_date'],
                    native_handoff=handoff, realized_profit_assessed=False,
                    runtime_effect=False, actual_pid_consumed=False)
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return dict(_semantic_failure(exc), source_date=source_date,
                    stage_id='main_machine_policy' if component == 'machine' else 'main_auxiliary_policy',
                    artifact=str(report_path), report_sha256=report_sha)


def _machine_result_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """Check exact-date machine economics separately from stage completion."""
    reversal = _continuous_reversal_result_semantics(root, source_date, 'machine')
    if reversal is not None:
        return reversal
    report_path = (root / "data/report/ai_decision_action_outcome_calibration"
                   / f"ai_decision_action_outcome_calibration_{source_date}.json")
    try:
        stage = _semantic_stage_binding(root, source_date, "legacy_machine_report")
        if stage["status"] in {"pending", "running"}:
            return {"status": "unobservable", "findings": [], "execution": stage}
        if stage["status"] in {"failed", "blocked", "source_quality_blocked"}:
            return {"status": "source_invalid", "findings": ["machine_execution_failed"], "execution": stage}
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        return _semantic_failure(exc)
    if not (report_path.exists() or report_path.is_symlink()):
        # A standalone win-rate sidecar is evidence that the machine family
        # ran; do not mark its missing full-evaluation partner unassessed.
        sidecar = report_path.with_name(f"winrate_policy_{source_date}.json")
        if sidecar.exists() or sidecar.is_symlink():
            return {"status": "source_invalid", "findings": [
                "machine_full_report_missing_with_winrate_sidecar"]}
        return {"status": "not_assessed", "findings": []}
    try:
        if report_path.is_symlink() or report_path.stat().st_size > 64 * 1024 * 1024:
            return {"status": "source_invalid", "findings": ["machine_report_untrusted_path_or_size"]}
        report, report_file_sha = _semantic_object(report_path)
        declared = report.get("artifact_content_sha256")
        body = {key: value for key, value in report.items() if key != "artifact_content_sha256"}
        actual = hashlib.sha256(json.dumps(body, ensure_ascii=True, sort_keys=True,
            separators=(",", ":"), default=str).encode("utf-8")).hexdigest()
        if report.get("target_date") != source_date or declared != actual:
            raise ValueError("machine_report_date_or_hash_invalid")
        scopes = (report.get("machine_full_evaluation") or {}).get("scope_evaluations")
        if not isinstance(scopes, dict):
            raise ValueError("machine_scope_evaluations_missing")
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
        return _semantic_failure(exc)
    findings: list[str] = []
    scope_details: dict[str, dict[str, Any]] = {}
    try:
        execution = _semantic_stage_binding(root, source_date, "legacy_machine_report",
            artifact="ai_decision_action_outcome_calibration",
            artifact_sha=report_file_sha, artifact_path=report_path)
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        return _semantic_failure(exc)
    for scope, row in scopes.items():
        if not isinstance(row, dict):
            findings.append("machine_scope_row_invalid")
            continue
        full = row.get("full_population_count")
        eligible = row.get("current_structure_eligible_count")
        paired = row.get("paired_comparable_count")
        exclusions = row.get("row_exclusion_reason_counts") or {}
        if not isinstance(exclusions, dict):
            findings.append("machine_exclusion_counts_invalid")
            continue
        invalid = exclusions.get("source_contract_invalid", 0)
        if (any(type(value) is not int or value < 0 for value in (full, eligible, invalid))
            or eligible > full or (paired is not None and (type(paired) is not int or paired < 0))):
            findings.append("machine_population_count_invalid")
            continue
        if not full and not invalid:
            continue
        scope_details[scope] = {"full": full, "eligible": eligible,
            "operating_paired": paired, "source_contract_invalid": invalid,
            "findings": []}
        start = len(findings)
        if invalid:
            findings.append("machine_source_contract_exclusions")
        if full and not eligible:
            findings.append("machine_current_structure_empty")
        if eligible and not paired:
            findings.append("machine_operating_paired_unbound")
        if eligible and row.get("downstream_operating_evidence_complete") is not True:
            findings.append("machine_operating_economics_incomplete")
        scope_details[scope]["findings"] = findings[start:]
    selections = report.get("strategy_refinements_by_scope") or {}
    if not isinstance(selections, dict):
        findings.append("machine_selection_contract_invalid")
        selections = {}
    from src.engine.scalping import entry_strategy_policy as strategy
    from src.engine.scalping.postclose_entry_validation import NEW_LOGIC_SOURCE_DATE
    if source_date >= NEW_LOGIC_SOURCE_DATE and set(scope_details) - set(selections):
        findings.append("machine_scope_selection_missing")
    for scope, selection in selections.items():
        if not isinstance(selection, dict):
            findings.append("machine_selection_contract_invalid")
            continue
        if source_date >= NEW_LOGIC_SOURCE_DATE:
            diagnostic_hold = (
                selection.get('selection_basis') == strategy.MACHINE_SELECTION_VERSION
                and selection.get('status') in {'source_gap', 'hold_candidate'}
                and selection.get('promotion_pass') is False
                and ((selection.get('status') == 'source_gap' and not selection.get('candidate'))
                     or (selection.get('status') == 'hold_candidate'
                         and selection.get('runtime_effect') is False
                         and selection.get('allowed_runtime_apply') is False)))
            if (selection.get("selection_basis") != strategy.RECOVERY_SELECTION_VERSION
                    and not diagnostic_hold):
                findings.append("machine_selection_version_invalid")
            if selection.get("promotion_pass") is True:
                candidate = selection.get("candidate") or {}
                try:
                    errors = strategy.promotion_errors(candidate, candidate.get("parent_policy"),
                                                        tuple(scope.split("|")))
                except (ValueError, TypeError, KeyError, AttributeError):
                    errors = ["candidate_contract_invalid"]
                if (errors or selection.get("promotion_errors")
                    or candidate.get("selection_score_version") != strategy.RECOVERY_SELECTION_VERSION):
                    findings.append("machine_selected_without_recovery_evidence")
        scope_details.setdefault(scope, {}).update(
            selection_status=selection.get("status"),
            selection_version=selection.get("selection_basis"),
            selection_blocker=selection.get("blocker"),
            promotion_errors=selection.get("promotion_errors"),
            source_excluded_count=len(selection.get("source_exclusions") or []))
    compact_path = (root / "data/report/ai_entry_setup_paired_replay_batch"
                    / f"compact_auxiliary_paired_economic_{source_date}.source.json")
    compact_exclusions: dict[str, int] = {}
    compact_path = existing_or_gzip_path(compact_path)
    if compact_path.exists() or compact_path.is_symlink():
        try:
            if compact_path.is_symlink() or compact_path.stat().st_size > 64 * 1024 * 1024:
                findings.append("compact_projection_untrusted_path_or_size")
            else:
                opener = gzip.open if compact_path.suffix == ".gz" else open
                with opener(compact_path, "rt", encoding="utf-8") as handle:
                    compact_text = handle.read(64 * 1024 * 1024 + 1)
                if len(compact_text) > 64 * 1024 * 1024:
                    raise ValueError("compact_projection_uncompressed_size_exceeded")
                compact = json.loads(compact_text)
                if compact.get("target_date") != source_date or not isinstance(compact.get("rows"), list):
                    raise ValueError("compact_projection_date_or_rows_invalid")
                compact_hash = compact.get("artifact_content_sha256")
                compact_body = {k: v for k, v in compact.items() if k != "artifact_content_sha256"}
                actual_hash = hashlib.sha256(json.dumps(compact_body, ensure_ascii=False,
                    sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                if compact_hash != actual_hash:
                    raise ValueError("compact_projection_hash_invalid")
                if any(not isinstance(row, dict) for row in compact["rows"]):
                    raise ValueError("compact_projection_rows_invalid")
                compact_exclusions = dict(Counter(str(row.get("exclusion_reason"))
                    for row in compact["rows"] if row.get("exclusion_reason")))
                if compact["rows"] and sum(compact_exclusions.values()) == len(compact["rows"]):
                    findings.append("compact_operating_rows_all_excluded")
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
            if str(exc) == 'semantic_generation_changed_during_read':
                return dict(_semantic_failure(exc), source_date=source_date)
            findings.append("compact_projection_invalid")
    winrate_path = (root / 'data/report/ai_decision_action_outcome_calibration'
                    / f'winrate_policy_{source_date}.json')
    if winrate_path.exists() or winrate_path.is_symlink():
        try:
            if winrate_path.is_symlink() or winrate_path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError('winrate_report_untrusted_path_or_size')
            from src.engine.scalping import ai_action_outcome_calibration as calibration
            from src.engine.scalping import mechanistic_entry_runtime_policy as runtime_policy
            winrate, winrate_file_sha = _semantic_object(winrate_path)
            winrate_stage = _semantic_stage_binding(root, source_date, 'main_machine_policy',
                artifact='machine_policy', artifact_sha=winrate_file_sha, artifact_path=winrate_path)
            if winrate_stage['status'] in {'pending', 'running'}:
                return {'status': 'unobservable', 'findings': [], 'execution': winrate_stage}
            if winrate_stage['status'] in {'failed', 'blocked', 'source_quality_blocked'}:
                findings.append('winrate_execution_failed')
            if winrate.get('schema') == 'main_entry_winrate_policy_report_v1':
                if (not calibration._artifact_content_sha256_valid(winrate)
                    or winrate.get('target_date') != source_date
                    or winrate.get('selection_basis') != 'win_rate_only'):
                    findings.append('winrate_report_hash_or_scope_invalid')
                accepted = winrate.get('accepted_attempt_count')
                input_count = winrate.get('input_attempt_count')
                source_excluded = winrate.get('source_contract_excluded_count')
                excluded = winrate.get('excluded_attempt_counts') or {}
                if (type(input_count) is not int or input_count < 0
                    or type(accepted) is not int or accepted < 0
                    or type(source_excluded) is not int or source_excluded < 0
                    or any(type(v) is not int or v < 0 for v in excluded.values())
                    or accepted + source_excluded + sum(excluded.values()) != input_count
                    or sum((winrate.get('situation_attempt_counts') or {}).values()) != accepted):
                    findings.append('winrate_population_denominator_invalid')
                if not runtime_policy.winrate_market_census_valid(winrate):
                    findings.append('winrate_market_denominator_invalid')
                elif any(item['input_attempt_count'] == 0
                    for item in winrate['market_census'].values()):
                    findings.append('winrate_market_source_empty')
                disposition = winrate.get('disposition')
                fixed_pair_report = winrate.get('fixed_pair_contract') is not None
                if (not fixed_pair_report and disposition == 'successor_selected'
                    and not runtime_policy._winrate_successor_hurdles_valid(winrate)):
                    findings.append('winrate_successor_hurdle_invalid')
                if not fixed_pair_report and disposition in {'initial_adopted', 'successor_selected'}:
                    for part in ('train', 'holdout'):
                        metrics = (winrate.get('candidate') or {}).get(part) or {}
                        if (not metrics.get('selected_opportunity_count')
                            or metrics.get('win_rate_pct') is None
                            or metrics.get('support_adjusted_win_rate_pct') is None):
                            findings.append('winrate_selected_zero_or_undefined')
                terminal_path = winrate_path.with_name(f'winrate_policy_terminal_{source_date}.json')
                terminal, terminal_sha = _semantic_object(terminal_path, limit=1024 * 1024)
                _semantic_stage_binding(root, source_date, 'main_machine_policy',
                    artifact='machine_policy_terminal', artifact_sha=terminal_sha, artifact_path=terminal_path)
                target = (terminal.get('staged') or {}).get('target_date')
                if (not calibration._artifact_content_sha256_valid(terminal)
                    or terminal.get('report_sha256') != winrate.get('artifact_content_sha256')
                    or not isinstance(target, str)):
                    raise ValueError('winrate_terminal_binding_invalid')
                bundle = runtime_policy.load(data_root=root / 'data', target_date=target)
                selection = (bundle or {}).get('winrate_selection') or {}
                pending = (terminal.get('staged') or {}).get('status') == 'pending_initial_preserved'
                reused = (terminal.get('staged') or {}).get('status') == 'existing_incumbent_preserved'
                from src.engine.scalping import entry_designated_policy as designated_policy
                designated = selection.get('schema') == designated_policy.PROOF
                if fixed_pair_report and not designated:
                    findings.append('winrate_candidate_bundle_or_scope_mismatch')
                if designated:
                    if (not designated_policy.binding_valid(winrate, bundle, root / 'data')
                        or terminal['staged'].get('bundle_sha256') != bundle['bundle_sha256']):
                        findings.append('winrate_candidate_bundle_or_scope_mismatch')
                    else:
                        # The loader validates the frozen pair, original request,
                        # parent and actual activation receipts. Do not compare an
                        # automatic carry disposition to operator designation.
                        scope_details['designated_fixed_pair'] = {
                            'status': 'bound', 'target_date': target,
                            'disposition': selection.get('disposition'),
                            'pair': bundle.get('designated_pair'),
                            'comparison': winrate.get('fixed_pair_comparison'),
                            'consumption': 'not_assessed_by_postclose_selection'}
                if not pending and not reused and not designated:
                    from src.engine.automation.postclose_summary_handoff import _staged_winrate_generation_preserved
                    if not _staged_winrate_generation_preserved(terminal['staged'], bundle,
                            runtime_policy, root / 'data', generation_only=True):
                        findings.append('winrate_candidate_bundle_or_scope_mismatch')
                if reused:
                    from src.engine.automation.postclose_summary_handoff import _existing_incumbent_winrate_binding_valid
                    previous = runtime_policy.load_effective(data_root=root / 'data', target_date=winrate.get('publication_date'))
                    if not _existing_incumbent_winrate_binding_valid(winrate, terminal['staged'],
                            bundle, previous, runtime_policy, data_root=root / 'data'):
                        findings.append('winrate_candidate_bundle_or_scope_mismatch')
                if (pending and (winrate.get('pending_initial_bundle_sha256') != bundle['bundle_sha256']
                    or winrate.get('pending_initial_target_date') != target
                    or winrate.get('hurdle_errors') != ['initial_policy_pending_activation']
                    or disposition != 'incumbent_carried'
                    or selection.get('disposition') != 'initial_adopted'
                    or selection.get('parent_bundle_sha256') != winrate.get('parent_bundle_sha256')
                    or bundle.get('previous_bundle_sha256') != winrate.get('parent_bundle_sha256'))
                    or not pending and not reused and not designated and (selection.get('report_sha256') != winrate.get('artifact_content_sha256')
                    or selection.get('disposition') != disposition)
                    or selection.get('machine_policy_sha256') != runtime_policy.digest(bundle['machine_policy'])
                    or not pending and not reused and not designated and (bundle.get('scope_policies') or {}).get('KRX|KRX_REGULAR', {}).get('machine_disposition') != disposition):
                    findings.append('winrate_candidate_bundle_or_scope_mismatch')
            else:
                findings.append('winrate_report_schema_invalid')
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
            if str(exc) == 'semantic_generation_changed_during_read':
                return dict(_semantic_failure(exc), source_date=source_date)
            findings.append('winrate_semantic_validation_failed')
    return {"status": "warning" if findings else "pass", "findings": sorted(set(findings)),
        "scopes": scope_details, "compact_exclusions": compact_exclusions,
        "source_date": source_date, "execution": execution,
        "report_sha256": actual, "artifact": str(report_path),
        "publication": "see_winrate_terminal_and_dated_bundle",
        "consumption": "not_assessed_by_postclose_selection"}


def _auxiliary_scope_contract(value, report, source_date, scope):
    """Audit frozen evidence, never rerank candidates or execute a replay."""
    from src.engine.scalping import compact_auxiliary_paired_replay as paired
    from src.engine.scalping.postclose_entry_validation import (
        NEW_LOGIC_SOURCE_DATE, split_manifest_valid, opportunity_identity,
    )
    if source_date < NEW_LOGIC_SOURCE_DATE:
        return []
    errors = []
    version = value.get("selection_rank_version")
    if version not in {"train_top1_frozen_paired_net_ev_holdout_gate_v4", paired.STAGE_SELECTION_VERSION}:
        errors.append("auxiliary_selection_version_invalid")
    manifest = value.get("split_manifest") or {}
    try:
        train = [tuple(row) for row in manifest["train_opportunity_ids"]]
        held = [tuple(row) for row in manifest["holdout_opportunity_ids"]]
        purged = [tuple(row) for row in manifest["purged_opportunity_ids"]]
        for identity in train + held + purged:
            if len(identity) == 5:
                lineage = {'scanner_promotion_id': identity[4]}
            elif len(identity) == 7 and identity[4] == 'MAIN_FIXED_WATCH':
                lineage = dict(zip(('watch_origin', 'watch_admission_id',
                                    'watch_generation_id'), identity[4:]))
            else:
                raise ValueError('opportunity_shape_invalid')
            row = {**dict(zip(('source_date', 'stock_code', 'effective_venue',
                              'session_bucket'), identity[:4])), **lineage}
            if opportunity_identity(row) != identity:
                raise ValueError('opportunity_identity_invalid')
        if (any(len(rows) != len(set(rows)) for rows in (train, held, purged))
            or set(purged) & (set(train) | set(held))
            or (train and held and not split_manifest_valid(manifest, train, held))
            or (value.get("status") == "candidate_selected" and (not train or not held))):
            raise ValueError("split_invalid")
    except (ValueError, TypeError, KeyError):
        errors.append("auxiliary_chronological_split_invalid")
    cost_count = value.get("full_cost_candidate_population_count")
    diagnostic = value.get("cost_incomplete_diagnostic_count")
    if (type(cost_count) is not int or cost_count < 0
        or type(diagnostic) is not int or diagnostic < 0
        or value.get("metric_authority") != "full_cost_fixed_checkpoint_cf_not_owner_portfolio"):
        errors.append("auxiliary_full_cost_census_invalid")
    trials = value.get("candidates")
    if (not isinstance(trials, list) or any(not isinstance(t, dict) for t in trials)
        or value.get("completed_candidate_count") != sum(
            t.get("evaluation_status") == "evaluated" for t in trials)
        or value.get("holdout_selection_candidate_count") != int(bool(value.get("frozen_train_choice")))):
        errors.append("auxiliary_completed_response_census_invalid")
    selected = value.get("selected") or {}
    frozen = value.get("frozen_train_choice")
    if frozen:
        receipt = report.get("auxiliary_train_selection") or {}
        saved = (receipt.get("scopes") or {}).get(scope) or {}
        if (not paired.valid(receipt) or receipt.get("schema") != "auxiliary_train_selection_v1"
            or receipt.get("target_date") != source_date
            or any(not isinstance(value.get(key), str) or len(value[key]) != 64
                   or any(c not in "0123456789abcdef" for c in value[key])
                   for key in ("train_population_sha256", "current_machine_policy_sha256"))
            or saved.get("policy_sha256") != frozen.get("policy_sha256")
            or saved.get("policy") != frozen.get("policy")
            or saved.get("prompt_version") != frozen.get("prompt_version")
            or saved.get("machine_policy_sha256") != value.get("current_machine_policy_sha256")
            or saved.get("parent_prompt_version") not in (value.get("parent_prompt_versions") or [])
            or saved.get("parent_soft_sha256") not in (value.get("parent_soft_policy_sha256s") or [])
            or saved.get("train_population_sha256") != value.get("train_population_sha256")
            or saved.get("split_manifest") != manifest):
            errors.append("auxiliary_frozen_selection_binding_invalid")
    if value.get("status") == "candidate_selected":
        if version == paired.STAGE_SELECTION_VERSION:
            receipt = report.get('auxiliary_train_selection') or {}
            saved = (receipt.get('scopes') or {}).get(scope) or {}
            incumbent = (trials or [{}])[0]
            if any(not paired.auxiliary_winrate_improves(selected, incumbent, part) for part in ('train', 'holdout')):
                errors.append('auxiliary_selected_winrate_not_improved')
            if (receipt.get('selection_rank_version') != paired.STAGE_SELECTION_VERSION
                or saved.get('selection_rank_version') != paired.STAGE_SELECTION_VERSION):
                errors.append('auxiliary_selection_objective_binding_invalid')
        if (not isinstance(frozen, dict) or selected != frozen
            or value.get("holdout_errors") or not cost_count
            or cost_count < selected.get("train_count", 0) + selected.get("holdout_count", 0)
            or selected.get("evaluation_status") != "evaluated"
            or selected.get("policy_sha256") != paired.digest(selected.get("policy"))
            or (selected.get("train_veto_to_pass_count")
                and not selected.get("holdout_veto_to_pass_count"))):
            errors.append("auxiliary_selected_without_frozen_full_cost_evidence")
    return errors


def _compact_diagnostic_price_path_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """A separate observation never upgrades canonical/economic eligibility."""
    from src.engine.scalping import ai_decision_quality as owner
    logical = root / "data/report/ai_decision_outcome_labels" / f"ai_decision_outcome_labels_{source_date}.json"
    path = logical.with_suffix(".compact_diagnostic.json")
    if not path.exists() and not path.is_symlink():
        return dict(status="not_observed", findings=["compact_diagnostic_projection_missing"],
                    artifact=str(path), primary_cohort_eligibility_changed=False)
    try:
        actual = existing_or_gzip_path(logical)
        source_before, projection_before = actual.stat(), path.stat()
        labels, source_sha = _semantic_object(logical)
        projection, sha = _semantic_object(path, limit=8 * 1024 * 1024)
        if (labels.get("target_date") != source_date
                or not owner.validate_compact_diagnostic_price_path(projection, labels, source_file_sha256=source_sha)):
            raise ValueError("compact_diagnostic_projection_contract_invalid")
        if (_observer_file_signature(source_before) != _observer_file_signature(actual.stat())
                or _observer_file_signature(projection_before) != _observer_file_signature(path.stat())
                or existing_or_gzip_path(logical) != actual):
            raise ValueError("compact_diagnostic_projection_generation_changed")
        return dict(status="observed", findings=[], status_counts=projection["status_counts"],
                    original_label_count=projection["original_label_count"],
                    source_label_file_sha256=source_sha, source_label_content_sha256=projection["source_label_content_sha256"],
                    artifact=str(path), report_sha256=sha, metric_role="diagnostic_price_path",
                    primary_cohort_eligibility_changed=False, economic_acceptance_eligible=False,
                    actual_completed_profit=False, runtime_effect=False)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        return dict(status="source_invalid", findings=[str(exc)], artifact=str(path),
                    primary_cohort_eligibility_changed=False, economic_acceptance_eligible=False)


def _auxiliary_result_semantics(root: Path, source_date: str) -> dict[str, Any]:
    """Audit the bounded AI-stage receipt; selection is not live consumption."""
    reversal = _continuous_reversal_result_semantics(root, source_date, 'auxiliary')
    if reversal is not None:
        return {**reversal, "compact_diagnostic_price_path": _compact_diagnostic_price_path_semantics(root, source_date)}
    from src.engine.scalping import compact_auxiliary_paired_replay as paired

    terminal_path = (root / "data/report/postclose_stage_terminal" / source_date
                     / "main_auxiliary_policy.json")
    terminal_source_sha = None
    if terminal_path.exists() or terminal_path.is_symlink():
        try:
            if terminal_path.is_symlink() or terminal_path.stat().st_size > 1024 * 1024:
                raise ValueError("auxiliary_terminal_untrusted_path_or_size")
            terminal, _ = _semantic_object(terminal_path, limit=1024 * 1024)
            receipt = terminal.get("receipt_sha256")
            body = {k: v for k, v in terminal.items() if k != "receipt_sha256"}
            digest = hashlib.sha256(json.dumps(body, ensure_ascii=True,
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            if (terminal.get("schema") not in ({"postclose_stage_terminal_v3", "postclose_stage_terminal_v2"} if source_date < "2026-10-06" else {"postclose_stage_terminal_v3"})
                or terminal.get("stage_id") != "main_auxiliary_policy"
                or terminal.get("source_date") != source_date or receipt != digest):
                raise ValueError("auxiliary_terminal_identity_or_hash_invalid")
            if terminal.get("status") in {"pending", "running"}:
                return {"status": "unobservable", "findings": [], "execution": terminal.get("status")}
            if terminal.get("status") in {"failed", "blocked", "source_quality_blocked"}:
                return {"status": "source_invalid", "findings": ["auxiliary_execution_failed"]}
            if terminal.get("status") == "succeeded" and terminal.get("exit_code") != 0:
                raise ValueError("auxiliary_terminal_exit_invalid")
            if terminal.get("status") == "succeeded" and terminal.get("exit_code") == 0:
                source = ((terminal.get("sources") or {}).get(
                    "compact_auxiliary_paired_economic") or {})
                terminal_source_sha = source.get("sha256")
                if (not isinstance(terminal_source_sha, str)
                    or len(terminal_source_sha) != 64
                    or any(c not in "0123456789abcdef" for c in terminal_source_sha)
                    or source.get("path") != str((root /
                        "data/report/ai_entry_setup_paired_replay_batch" /
                        f"compact_auxiliary_paired_economic_{source_date}.json").resolve())):
                    raise ValueError("auxiliary_terminal_source_binding_missing")
        except (OSError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
            return _semantic_failure(exc)
    path = existing_or_gzip_path(
        root / "data/report/ai_entry_setup_paired_replay_batch"
        / f"compact_auxiliary_paired_economic_{source_date}.json"
    )
    if not (path.exists() or path.is_symlink()):
        if terminal_source_sha:
            return {"status": "source_invalid", "findings": ["auxiliary_completed_report_missing"]}
        return {"status": "not_assessed", "findings": []}
    try:
        report, file_sha = _semantic_object(path)
        if terminal_source_sha and file_sha != terminal_source_sha:
            raise ValueError("auxiliary_completed_report_generation_mismatch")
        stage = report.get("auxiliary_stage") or {}
        if (not paired.valid(report)
            or report.get("schema") != paired.SCHEMA
            or report.get("target_date") != source_date
            or not paired.valid(stage)
            or stage.get("schema") != "auxiliary_ai_stage_evaluation_v1"
            or stage.get("source_date") != source_date
            or stage.get("source_projection_sha256") != report.get("source_projection_sha256")
            or stage.get("source_manifest_sha256") != report.get("source_manifest_sha256")
            or report.get("runtime_effect") is not False
            or stage.get("runtime_effect") is not False
            or stage.get("actual_order_submitted") is not False):
            raise ValueError("auxiliary_stage_report_contract_invalid")
        screened, eligible, excluded = (stage.get(k) for k in
            ("screened_total", "eligible_count", "excluded_count"))
        eligible_keys = stage.get("eligible_keys")
        candidate_keys = stage.get("candidate_population_keys")
        if (any(type(n) is not int or n < 0 for n in (screened, eligible, excluded))
            or screened != eligible + excluded
            or (eligible_keys is not None and (
                not isinstance(eligible_keys, list)
                or any(not isinstance(key, str) or not key for key in eligible_keys)
                or len(eligible_keys) != eligible
                or len(set(eligible_keys)) != eligible))
            or not isinstance(stage.get("scope_results"), dict)):
            raise ValueError("auxiliary_population_denominator_invalid")
        if candidate_keys is not None and (
            not isinstance(candidate_keys, list)
            or any(not isinstance(key, str) or not key for key in candidate_keys)
            or len(set(candidate_keys)) != len(candidate_keys)
            or eligible_keys is None
            or not set(candidate_keys) <= set(eligible_keys)
            or any(not isinstance(v, dict)
                   or type(v.get("eligible_count")) is not int
                   or v["eligible_count"] < 0
                   for v in stage["scope_results"].values())
            or sum(v["eligible_count"] if source_date < "2026-10-02"
                   else v.get("full_cost_candidate_population_count", 0)
                   for v in stage["scope_results"].values())
                != len(candidate_keys)):
            raise ValueError("auxiliary_candidate_population_invalid")
    except (OSError, EOFError, UnicodeError, ValueError, TypeError, AttributeError) as exc:
        return _semantic_failure(exc)
    findings: list[str] = []
    if eligible_keys is None:
        findings.append("auxiliary_eligible_identity_uninstrumented")
    if stage.get("source_tuning_allowed") is not True:
        findings.append("auxiliary_source_tuning_not_allowed")
    economic = report.get("metrics") or {}
    if not isinstance(economic, dict):
        return {"status": "source_invalid", "findings": ["auxiliary_economic_metrics_invalid"]}
    economic_screened = economic.get("screened_total")
    economic_compared = economic.get("paired_comparable_count")
    if report.get("status") == "source_contract_blocked":
        if (type(economic_screened) is not int or economic_screened < 0
            or type(economic_compared) is not int or economic_compared < 0
            or economic_compared > economic_screened):
            return {"status": "source_invalid", "findings": ["auxiliary_economic_denominator_invalid"]}
        if economic_screened and not economic_compared:
            findings.append("auxiliary_primary_economics_source_blocked")
    prospective = report.get("prospective_source_contract") or {}
    if not isinstance(prospective, dict):
        return {"status": "source_invalid", "findings": ["auxiliary_source_lineage_invalid"]}
    lineage = prospective.get("source_lineage_counts") or {}
    if not isinstance(lineage, dict):
        return {"status": "source_invalid", "findings": ["auxiliary_source_lineage_invalid"]}
    first_gap = prospective.get("first_source_gap")
    if (first_gap == "writer_plan_hash_missing"
        and type(lineage.get("prompt_exact_input_present")) is int
        and lineage["prompt_exact_input_present"] > 0
        and lineage.get("writer_trace_plan_joined") == 0):
        findings.append("auxiliary_exact_plan_lineage_missing")
    label_gap_count = 0
    label_hash = report.get("source_label_report_sha256")
    if type(economic_screened) is int and economic_screened > 0 and not label_hash:
        findings.append("auxiliary_outcome_label_binding_missing")
    independent_path_counts = None
    if label_hash:
        label_path = existing_or_gzip_path(
            root / "data/report/ai_decision_outcome_labels"
            / f"ai_decision_outcome_labels_{source_date}.json")
        try:
            if (not isinstance(label_hash, str) or len(label_hash) != 64
                or any(c not in "0123456789abcdef" for c in label_hash)
                or label_path.is_symlink()):
                raise ValueError("auxiliary_label_report_untrusted_path_or_size")
            if not label_path.exists():
                raise ValueError("auxiliary_label_report_missing")
            if label_path.stat().st_size > 64 * 1024 * 1024:
                raise ValueError("auxiliary_label_report_untrusted_path_or_size")
            opener = gzip.open if label_path.suffix == ".gz" else open
            with opener(label_path, "rb") as handle:
                label_raw = handle.read(64 * 1024 * 1024 + 1)
            if len(label_raw) > 64 * 1024 * 1024:
                raise ValueError("auxiliary_label_report_uncompressed_size_exceeded")
            labels = json.loads(label_raw)
            if not isinstance(labels, dict):
                raise ValueError("auxiliary_label_report_binding_invalid")
            counts = labels.get("label_contract_status_counts")
            label_rows = labels.get("labels")
            actual_counts = Counter()
            if isinstance(label_rows, list):
                for row in label_rows:
                    role = row.get("evaluation_label_contract") if isinstance(row, dict) else None
                    price_path = role.get("diagnostic_price_path") if isinstance(role, dict) else None
                    status = price_path.get("status") if isinstance(price_path, dict) else None
                    actual_counts[status] += 1
            if (labels.get("schema") != "ai_decision_outcome_labels_v1"
                or labels.get("target_date") != source_date
                or paired.digest(labels) != label_hash
                or not isinstance(label_rows, list)
                or not isinstance(counts, dict)
                or any(type(n) is not int or n < 0 for n in counts.values())
                or sum(counts.values()) != len(label_rows)
                or dict(actual_counts) != counts):
                raise ValueError("auxiliary_label_report_binding_invalid")
            # Holding/exit labels are not the compact auxiliary population.
            entry_rows = [row for row in label_rows
                          if row.get("decision_stage") in {"entry", "entry_screen"}]
            if source_date >= "2026-10-02" and economic_screened:
                projection, _ = _semantic_object(path.with_name(
                    f"compact_auxiliary_paired_economic_{source_date}.source.json"))
                if (not paired.valid(projection) or projection.get("target_date") != source_date
                    or projection.get("artifact_content_sha256") != report.get("source_projection_sha256")):
                    raise ValueError("auxiliary_label_population_binding_invalid")
                keys = {row["evaluation_key"] for row in projection["rows"]}
                entry_rows = [row for row in entry_rows if row.get("decision_trace_id") in keys]
                if (len(keys) != economic_screened or len(entry_rows) != len(keys)
                    or {row.get("decision_trace_id") for row in entry_rows} != keys):
                    raise ValueError("auxiliary_label_population_binding_invalid")
                label_index = {row['decision_trace_id']: row for row in entry_rows}
                joined = [row for row in projection['rows']
                          if paired.stage_path_label_matches(row, label_index[row['evaluation_key']])]
                independent_path_counts = dict(total=len(keys), exact_price_label_joined=len(joined),
                    net_path_evaluable=sum(paired.auxiliary_stage_net(row) is not None for row in joined),
                    authority='fixed_10m_counterfactual_path_not_operating_or_realized_economics')
            label_gap_count = sum((row.get("evaluation_label_contract") or {}).get(
                "diagnostic_price_path", {}).get("status") == "source_gap" for row in entry_rows)
        except (OSError, EOFError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
            return _semantic_failure(exc)
        if label_gap_count:
            findings.append("auxiliary_outcome_label_source_gap")
    scopes = {}
    for scope, value in stage["scope_results"].items():
        if not isinstance(value, dict):
            findings.append("auxiliary_scope_selection_status_invalid")
            continue
        selected = value.get("selected") or {}
        if not isinstance(selected, dict):
            findings.append("auxiliary_scope_selection_status_invalid")
            continue
        status = value.get("status")
        try:
            scope_findings = _auxiliary_scope_contract(value, report, source_date, scope)
        except (ValueError, TypeError, KeyError, AttributeError):
            scope_findings = ["auxiliary_scope_selection_contract_invalid"]
        findings.extend(scope_findings)
        independent = bool(value.get("holdout_day") or value.get("same_day_holdout_keys"))
        scopes[scope] = {"status": status, "eligible_count": value.get("eligible_count"),
                         "holdout_day": value.get("holdout_day"),
                         "paired_delta_ev_pct": selected.get("paired_delta_ev_pct"),
                         "selection_version": value.get("selection_rank_version"),
                         "selection_blocker": value.get("selection_blocker"),
                         "holdout_errors": value.get("holdout_errors"),
                         "full_cost_count": value.get("full_cost_candidate_population_count"),
                         "cost_incomplete_diagnostic_count": value.get("cost_incomplete_diagnostic_count"),
                         "metric_authority": value.get("metric_authority"),
                         "findings": scope_findings,
                         "actual_fill_or_realized_pnl": False}
        if status not in {"candidate_selected", "incumbent_carry"}:
            findings.append("auxiliary_scope_selection_status_invalid")
        train_delta = selected.get("train_paired_delta_ev_pct")
        holdout_delta = selected.get("holdout_paired_delta_ev_pct")
        if status == "candidate_selected" and (
            stage.get("source_tuning_allowed") is not True
            or candidate_keys is None
            or type(selected.get("paired_delta_ev_pct")) not in (int, float)
            or not math.isfinite(selected["paired_delta_ev_pct"])
            or selected["paired_delta_ev_pct"] <= 0
            or not isinstance(selected.get("policy"), dict)
            or selected.get("policy_sha256") != paired.digest(selected["policy"])
            or not selected.get("prompt_version")
            or type(selected.get("train_count")) is not int or selected["train_count"] < 5
            or type(selected.get("holdout_count")) is not int or selected["holdout_count"] < 3
            or type(value.get("eligible_count")) is not int
            or selected["train_count"] + selected["holdout_count"] != value["eligible_count"]
            or value["eligible_count"] > eligible
            or type(train_delta) not in (int, float) or not math.isfinite(train_delta) or train_delta <= 0
            or type(holdout_delta) not in (int, float) or not math.isfinite(holdout_delta) or holdout_delta < 0
            or any(type(selected.get(key)) is not int or selected[key] < 1 for key in (
                "train_positive_count", "train_negative_count", "holdout_positive_count",
                "holdout_negative_count", "train_pass_count", "holdout_pass_count",
                "holdout_changed_count"))
            or type(selected.get("train_changed_count")) is not int
            or selected["train_changed_count"] < 2
            or selected.get("successful_pass_changed_count") != 0
            or selected.get("prompt_response_missing_count") != 0
            or not independent
        ):
            findings.append("auxiliary_selected_without_independent_evidence")
    if not eligible:
        findings.append("auxiliary_economic_population_empty")
    elif not any(isinstance(value, dict) and (value.get("holdout_day") or value.get("same_day_holdout_keys"))
                 for value in stage["scope_results"].values()):
        findings.append("auxiliary_independent_holdout_missing")
    if any(f.endswith("invalid") or f.startswith("auxiliary_selected_without_")
           for f in findings):
        status = "review_required"
    elif findings:
        status = "source_gap"
    elif any(isinstance(v, dict) and v.get("status") == "candidate_selected"
             for v in stage["scope_results"].values()):
        status = "candidate_selected"
    else:
        status = "incumbent_carry"
    return {"status": status,
            "findings": sorted(set(findings)), "screened_total": screened,
            "eligible_count": eligible, "excluded_count": excluded,
            "economic_screened_total": economic_screened,
            "paired_comparable_count": economic_compared,
            "outcome_label_source_gap_count": label_gap_count,
            "independent_price_path_counts": independent_path_counts,
            "compact_diagnostic_price_path": _compact_diagnostic_price_path_semantics(root, source_date),
            "first_source_gap": first_gap,
            "source_lineage_counts": lineage,
            "source_date": source_date, "report_sha256": report["artifact_content_sha256"],
            "artifact": str(path), "execution": "report_observed",
            "publication": report.get("selection_disposition"),
            "consumption": "not_assessed_by_postclose_selection",
            "scopes": scopes, "runtime_effect": False}


def _cancel_wait_monitor_source_date(root, day, *, data_root=None):
    """Keep a native run's original date over midnight, including holidays."""
    data_root = Path(data_root) if data_root is not None else Path(root)/'data'
    previous = (datetime.fromisoformat(day) - timedelta(days=1)).date().isoformat()
    for source_date in (day, previous):
        path = data_root/'report/threshold_cycle_postclose_status'/f'threshold_cycle_postclose_{source_date}.status.json'
        if path.exists() and not path.is_symlink():
            try:
                state, _ = _semantic_object(path, limit=1024*1024)
                if (state.get('status') in {'running', 'producers_completed', 'succeeded', 'failed'}
                    and state.get('target_date') == source_date and state.get('run_id')):
                    return source_date
            except (OSError, ValueError, TypeError):
                pass
    return day


def _cancel_wait_native_execution(root, data_root, source_date):
    """Read native wrapper receipts; cancel-wait has no launch-owned stage."""
    result = {'status':'not_observed', 'source_date':source_date}
    path = data_root/'report/threshold_cycle_postclose_status'/f'threshold_cycle_postclose_{source_date}.status.json'
    if path.exists() or path.is_symlink():
        state, sha = _semantic_object(path)
        if state.get('target_date') != source_date:
            raise ValueError('cancel_wait_native_run_date_invalid')
        result.update(status=state.get('status'), status_sha256=sha, run_id=state.get('run_id'),
                      code_commit=state.get('code_commit'))
    log = root/'logs/threshold_cycle_postclose_cron.log'
    if log.is_file() and not log.is_symlink():
        before = log.stat()
        with log.open('rb') as handle:
            handle.seek(max(0, before.st_size - 4 * 1024 * 1024))
            rows = handle.read().splitlines()
        after = log.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
            result['command_status'] = 'generation_in_transition'
            return result
        for line in reversed(rows):
            if b'[PERF] ' not in line:
                continue
            try:
                metric = json.loads(line.split(b'[PERF] ', 1)[1])
            except (ValueError, UnicodeError):
                continue
            if (metric.get('schema') != 'postclose_command_metrics_v1'
                or metric.get('producer_module') != 'src.engine.automation.entry_cancel_wait_tuning'
                or metric.get('target_date') != source_date
                or (result.get('run_id') and metric.get('run_id') != result['run_id'])
                or (result.get('code_commit') and metric.get('code_commit') != result['code_commit'])):
                continue
            result['command'] = metric
            result['command_status'] = ('succeeded' if metric.get('measurement_complete') is True
                and type(metric.get('exit_code')) is int and metric['exit_code'] == 0 else 'failed')
            break
    return result


def _entry_cancel_wait_result_semantics(root, source_date, now=None, *, data_root=None):
    from src.engine.automation import entry_cancel_wait_tuning as owner
    root = Path(root)
    data_root = (Path(data_root) if data_root is not None else root/'data').resolve()
    directory = data_root/'report/entry_cancel_wait_tuning'
    path = directory/f'entry_cancel_wait_tuning_{source_date}.json'
    policy_path = directory/f'entry_cancel_wait_policy_{source_date}.json'
    result = {'status':'not_assessed', 'source_date':source_date, 'findings':[],
              'artifact':str(path), 'runtime_effect':False, 'actual_pid_consumed':False,
              'whole_native_chain_done_claimed':False}
    reading_consumers = False
    try:
        execution = _cancel_wait_native_execution(root, data_root, source_date)
        result['execution'] = execution
        if execution.get('command_status') == 'generation_in_transition':
            return {**result, 'status':'unobservable', 'reason':'generation_in_transition'}
        if execution.get('command_status') == 'failed':
            return {**result, 'status':'source_invalid', 'findings':['cancel_wait_execution_failed']}
        if not path.exists() and not path.is_symlink():
            if execution.get('command_status') == 'succeeded':
                return {**result, 'status':'source_invalid', 'findings':['cancel_wait_completed_report_missing']}
            current = now or datetime.now(ZoneInfo('Asia/Seoul'))
            current = current.replace(tzinfo=ZoneInfo('Asia/Seoul')) if current.tzinfo is None else current.astimezone(ZoneInfo('Asia/Seoul'))
            due = source_date < current.date().isoformat() or (source_date == current.date().isoformat() and current.hour >= 20)
            return {**result, 'status':'pending' if due else 'not_yet_due'}
        payload, report_sha = _semantic_object(path)
        result['report_sha256'] = report_sha
        if payload.get('date') != source_date:
            raise ValueError('cancel_wait_report_date_or_hash_invalid')
        if payload.get('reconciliation_contract_version') is None:
            return {**result, **owner.validated_reconciliation_view(payload), 'findings':[]}
        if not policy_path.exists() and execution.get('status') == 'running':
            return {**result, 'status':'pending', 'reason':'policy_publication_pending'}
        policy, policy_sha = _semantic_object(policy_path)
        view = owner.validated_reconciliation_view(payload, policy, data_root=data_root,
                                                    read_object=_semantic_object)
        result.update(view, findings=list(view['findings']), policy_sha256=policy_sha)
        if view.get('status') == 'unobservable':
            return result
        # Recheck the multi-file publication after reading the bound sources.
        if (_semantic_object(path, hash_only=True)[1] != report_sha
            or _semantic_object(policy_path, hash_only=True)[1] != policy_sha):
            return {**result, 'status':'unobservable', 'findings':[], 'reason':'generation_in_transition'}
        if (result['findings'] and execution.get('status') == 'running'
            and execution.get('command_status') != 'succeeded'
            and set(result['findings']) <= {'cancel_wait_stale_source_generation', 'cancel_wait_policy_binding_invalid'}):
            return {**result, 'status':'pending', 'findings':[], 'reason':'producer_generation_pending'}
        reuse_path = path.with_suffix('.reuse-contract.json')
        if reuse_path.exists() or reuse_path.is_symlink():
            reuse, _ = _semantic_object(reuse_path)
            result['reuse'] = {'artifact_sha256':reuse.get('artifact_sha256'),
                               'preflight_fingerprint':reuse.get('preflight_fingerprint')}
            if (reuse.get('artifact_sha256') != report_sha
                or reuse.get('preflight_fingerprint') != payload.get('preflight_fingerprint')):
                result['findings'].append('cancel_wait_reuse_generation_invalid')
        if view.get('findings'):
            result['consumers'] = {'status':'not_assessed'}
            return result
        summary_path = data_root/'report/runtime_approval_summary'/f'runtime_approval_summary_{source_date}.json'
        tower_path = data_root/'report/tuning_performance_control_tower'/f'tuning_performance_control_tower_{source_date}.json'
        checklist = root/'docs/checklists'/f"{policy['effective_date']}-stage2-todo-checklist.md"
        native_path = data_root/'report/threshold_cycle_postclose_status'/f'threshold_cycle_postclose_{source_date}.status.json'
        def stamp(candidate):
            actual = existing_or_gzip_path(candidate)
            try:
                value = actual.lstat()
            except FileNotFoundError:
                return None
            return (str(actual), value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns, actual.is_symlink())
        consumers = (summary_path, tower_path, checklist)
        generation_paths = (*consumers, path, policy_path, native_path, reuse_path)
        consumer_generation = tuple(stamp(candidate) for candidate in generation_paths)
        result['consumers'] = dict(status='pending', summary='pending', tower='pending', checklist='pending')
        reading_consumers = True
        completed = execution.get('status') in {'producers_completed', 'succeeded'} and bool(execution.get('run_id'))
        summary_sha = None
        if summary_path.exists() or summary_path.is_symlink():
            summary, summary_sha = _semantic_object(summary_path)
            source = (summary.get('sources') or {}).get('entry_cancel_wait') or {}
            summary_view = (source.get('economic_evidence') or {}).get('cancel_wait_reconciliation')
            if summary.get('date') == source_date and source.get('sha256') == report_sha and summary_view == view:
                result['consumers']['summary'] = 'verified'
            elif source.get('sha256') == report_sha:
                result['findings'].append('cancel_wait_consumer_projection_invalid')
        expected = owner.handoff_view(payload, policy, policy_path)
        if tower_path.exists() or tower_path.is_symlink():
            tower, _ = _semantic_object(tower_path)
            observed = tower.get('entry_cancel_wait_economic_tuning')
            # Older successor generations are pending during the native chain.
            receipt = tower.get('source_generation_contract') or {}
            sources = receipt.get('sources') or {}
            bound = (receipt.get('schema') == 'postclose_summary_sources_v1'
                and receipt.get('source_date') == source_date
                and (sources.get('entry_cancel_wait_tuning') or sources.get('entry_cancel_wait') or {}).get('sha256') == report_sha
                and (sources.get('entry_cancel_wait_policy') or {}).get('sha256') == policy_sha
                and summary_sha is not None
                and (sources.get('runtime_approval_summary') or {}).get('sha256') == summary_sha)
            if tower.get('date') == source_date and bound and observed == expected:
                result['consumers']['tower'] = 'verified'
            elif bound:
                result['findings'].append('cancel_wait_consumer_projection_invalid')
        if checklist.exists() or checklist.is_symlink():
            if checklist.is_symlink() or checklist.stat().st_size > 8 * 1024 * 1024:
                raise ValueError('cancel_wait_checklist_size_invalid')
            with checklist.open('rb') as handle:
                raw = handle.read(8 * 1024 * 1024 + 1)
            if len(raw) > 8 * 1024 * 1024:
                raise ValueError('cancel_wait_checklist_size_invalid')
            text = raw.decode('utf-8')
            markers = re.findall(r'<!-- POSTCLOSE_SUMMARY_SOURCES (.*?) -->', text)
            receipt = json.loads(markers[0]) if len(markers) == 1 else {}
            sources = receipt.get('sources') or {}
            bound = (receipt.get('schema') == 'postclose_summary_sources_v1'
                and receipt.get('source_date') == source_date
                and (sources.get('entry_cancel_wait_tuning') or {}).get('sha256') == report_sha
                and (sources.get('entry_cancel_wait_policy') or {}).get('sha256') == policy_sha
                and summary_sha is not None
                and (sources.get('runtime_approval_summary') or {}).get('sha256') == summary_sha)
            if (bound and text.count(owner.checklist_handoff(expected)) == 1
                and text.count('<!-- entry_cancel_wait_handoff:start -->') == 1
                and text.count('<!-- entry_cancel_wait_handoff:end -->') == 1):
                result['consumers']['checklist'] = 'verified'
        if all(result['consumers'][stage] == 'verified' for stage in ('summary', 'tower', 'checklist')):
            result['consumers']['status'] = 'verified'
        elif completed:
            result['findings'].append('cancel_wait_consumer_projection_invalid')
        native_sha = (_semantic_object(native_path, hash_only=True)[1]
            if native_path.exists() or native_path.is_symlink() else None)
        if (tuple(stamp(candidate) for candidate in generation_paths) != consumer_generation
            or _semantic_object(path, hash_only=True)[1] != report_sha
            or _semantic_object(policy_path, hash_only=True)[1] != policy_sha
            or native_sha != execution.get('status_sha256')
            or owner.validated_reconciliation_view(payload, policy, data_root=data_root,
                                                  read_object=_semantic_object) != view):
            return {**result, 'status':'unobservable', 'findings':[], 'reason':'generation_in_transition'}
        if result['findings']:
            result['status'] = 'source_invalid'
        result['findings'] = sorted(set(result['findings']))
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        failure = _semantic_failure(exc)
        if reading_consumers and failure['status'] != 'unobservable':
            try:
                changed = tuple(stamp(candidate) for candidate in generation_paths) != consumer_generation
            except OSError:
                changed = False
            if changed:
                failure = _semantic_failure(ValueError('semantic_generation_changed_during_read'))
            else:
                failure['findings'] = sorted(set(result['findings'] + ['cancel_wait_consumer_projection_invalid']))
                failure['error'] = str(exc)[:160]
        result.update(failure)
    return result






def _semantic_due_target(now):
    from src.engine.automation import next_preopen_readiness as readiness
    current = now.replace(tzinfo=ZoneInfo('Asia/Seoul')) if now.tzinfo is None else now.astimezone(ZoneInfo('Asia/Seoul'))
    if is_krx_trading_day(current.date()) and current.hour * 60 + current.minute < 455:
        return current.date().isoformat()
    return readiness._next_trading_day(current.date()).isoformat()


def _completed_semantic_source(root, now):
    """Select a receipt-owned date, never yesterday/last weekday by guesswork.

    The native handoff validator checks the selected controller and prepared
    generation below. Invalid latest receipts must remain visible, not fall back
    to an older PASS. Limit the directory census to the newest 32 dated owners.
    """
    target = _semantic_due_target(now)
    as_of = now.date().isoformat()
    result = {'status': 'not_assessed', 'as_of_date': as_of, 'target_date': target,
              'source_date': None, 'findings': []}
    try:
        folder = root / 'data/report/postclose_done_controller'
        paths = sorted(folder.glob('postclose_done_controller_????-??-??.json'), reverse=True)[:32]
        for path in paths:
            day = path.stem[-10:]
            if day > as_of:
                continue
            result['artifact'] = str(path)
            value, sha = _semantic_object(path, limit=4 * 1024 * 1024)
            if (value.get('date') != day or value.get('report_type') != 'postclose_done_controller'
                or value.get('schema_version') != 2):
                raise ValueError('completed_semantic_controller_date_invalid')
            if value.get('status') not in {'done', 'failed', 'blocked'}:
                continue
            result.update(status='receipt_selected', source_date=day,
                          artifact=str(path), generation=sha)
            break
        index = root / 'data/runtime/policy_bootstrap/prepared' / target / 'latest.json'
        if index.exists() or index.is_symlink():
            pointer, _ = _semantic_object(index, limit=1024 * 1024)
            receipt_path = Path(pointer['receipt_path'])
            if receipt_path.resolve().parent.parent != index.parent.resolve():
                raise ValueError('completed_semantic_prepared_path_invalid')
            receipt, sha = _semantic_object(receipt_path, limit=1024 * 1024)
            if (pointer.get('schema') != 'next_preopen_readiness_index_v1'
                or pointer.get('target_date') != target or pointer.get('receipt_sha256') != sha
                or receipt.get('schema') != 'next_preopen_readiness_v1'
                or receipt.get('target_date') != target or receipt.get('status') != 'prepared_verified'
                or not isinstance(receipt.get('source_date'), str) or receipt['source_date'] > as_of):
                raise ValueError('completed_semantic_prepared_identity_invalid')
            result['prepared_source_date'] = receipt['source_date']
            result['prepared_generation'] = sha
            if result['source_date'] is None:
                result.update(status='receipt_selected', source_date=receipt['source_date'],
                              artifact=str(receipt_path), generation=sha)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result.update(_semantic_failure(exc))
    return result


def _postclose_handoff_semantics(root, source_date, now):
    """Use native read-only closure/readiness checks; never prepare or apply."""
    from src.engine.automation import next_preopen_readiness as readiness
    from src.engine.automation.postclose_done_controller import done_terminal_receipt_issues
    result = {"status": "not_assessed", "source_date": source_date,
              "observation_date": _today_kst_str(now), "bound_target_date": None,
              "next_due_target_date": _semantic_due_target(now),
              "findings": [], "stages": {}, "consumption": "not_observed"}
    try:
        for stage in ("summary_handoff",):
            result["stages"][stage] = _semantic_stage_binding(root, source_date, stage)
            if result["stages"][stage]["status"] == "succeeded":
                from src.engine.automation.postclose_summary_handoff import stage_artifacts
                for name, path in stage_artifacts(root / "data/report", source_date, stage).items():
                    _, sha = _semantic_object(path, hash_only=True)
                    _semantic_stage_binding(root, source_date, stage, artifact=name,
                                            artifact_sha=sha, artifact_path=path)
            if result["stages"][stage]["status"] in {"failed", "blocked", "source_quality_blocked"}:
                result["findings"].append(f"{stage}:execution_failed")
        if any(value['status'] in {'pending', 'running'} for value in result['stages'].values()):
            result.update(status='unobservable', target_date=None,
                prepared=dict(status='unobservable', reason='producer_generation_in_transition'),
                reason='producer_generation_in_transition')
            return result
        controller_path = (root / "data/report/postclose_done_controller"
                           / f"postclose_done_controller_{source_date}.json")
        if controller_path.exists() or controller_path.is_symlink():
            controller, controller_sha = _semantic_object(controller_path)
            result["status"] = controller.get("status", "source_invalid")
            if controller.get("status") in {"failed", "blocked"}:
                result["findings"].append("postclose_handoff_execution_failed")
            if controller.get("status") == "done":
                errors = done_terminal_receipt_issues(controller_path, source_date, started_after_ns=0,
                                                     generation_only=True)
                result["validation_scope"] = "sealed_generation_not_new_full_chain_verification"
                if 'strict_checklist_generation_stale' in errors:
                    from src.engine.automation.intraday_release_handoff import historical_checklist_for_observer
                    try:
                        preserved = historical_checklist_for_observer(root, source_date, now=now)
                        errors = done_terminal_receipt_issues(
                            controller_path, source_date, started_after_ns=0, generation_only=True,
                            checklist_snapshot=Path(preserved['path']))
                        result['historical_generation_validation'] = preserved
                    except (OSError, ValueError, TypeError, KeyError) as exc:
                        result['historical_generation_validation'] = dict(status='invalid', reason=str(exc))
                if errors:
                    result["findings"].append("postclose_handoff_generation_invalid")
                    result["closure_errors"] = errors
                else:
                    result["report_sha256"] = controller_sha
                    result["artifact"] = str(controller_path)
        target = _semantic_due_target(now)
        summary_path = root / 'data/report/runtime_approval_summary' / f'runtime_approval_summary_{source_date}.json'
        if result['stages']['summary_handoff']['status'] == 'succeeded' and summary_path.exists():
            summary, _ = _semantic_object(summary_path)
            bound = summary.get('preopen_consumption_receipt') or {}
            if bound.get('source_date') == source_date:
                result['bound_target_date'] = bound.get('apply_date')
        # Preserve the legacy notifier/fingerprint field during migration.
        # The sealed bound target is explicit and never overwritten by next due.
        result['target_date'] = target
        result['target_date_role'] = 'legacy_next_due_target'
        index = root / "data/runtime/policy_bootstrap/prepared" / target / "latest.json"
        if source_date >= target:
            # Today's unclosed postclose source does not own this morning's
            # prepared generation from the preceding completed session.
            result['prepared'] = {'status': 'future_due', 'target_date': target,
                                  'reason': 'source_not_before_target',
                                  'consumption': 'not_observed'}
        elif index.exists() or index.is_symlink():
            _semantic_object(index, limit=1024 * 1024)
            check = readiness.verify_prepared(target, generation_only=True)
            result["prepared"] = check
            if check.get("status") != "pass":
                result["findings"].append("next_preopen_prepared_contract_invalid")
        else:
            result['prepared'] = {'status': 'future_due', 'target_date': target,
                                  'consumption': 'not_observed'}
        # Actual PREOPEN/PID consumption remains in the startup detectors.
        if result["findings"]:
            result["status"] = "source_invalid"
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        if str(exc) == "semantic_generation_changed_during_read":
            result.update(_semantic_failure(exc))
        else:
            result.update(status="source_invalid", findings=["postclose_handoff_contract_invalid"], error=str(exc))
    return result


def _optional_weakness_semantics(root, now):
    """Bounded native receipt observation, separate from recommendation delivery."""
    from src.engine.automation import main_market_weakness_research as native
    base = native.namespace(root / 'data')
    result = dict(status='off', findings=[], observation_date=_today_kst_str(now),
        source_date=None, target_date=None, observation_complete=False,
        decision_authority='report_only', runtime_effect=False, mandatory_preopen=False,
        recommendation_notifier='main_market_weakness_research_notify',
        common_notifier_scope='execution_and_source_health_only')
    installation = base / 'installation.json'
    if not installation.exists():
        result['reason'] = 'optional_not_installed'
        return result
    try:
        objects, hashes = {}, {}
        for key, name in (('installation','installation.json'), ('attempt','night_summary.json'),
                          ('completed','last_completed_computation.json'), ('cursor','schedule_cursor.json'),
                          ('cumulative','cumulative/current.json'), ('delivery','notification_disposition.json')):
            path = base / name
            if not path.exists():
                continue
            value, sha = _semantic_object(path, limit=1024*1024)
            native.check_seal(value)
            if value.get('runtime_effect') is not False or value.get('allowed_runtime_apply') is not False:
                raise ValueError('optional_research_authority_invalid')
            objects[key], hashes[key] = value, sha
        config = objects['installation']
        result.update(enabled=config.get('enabled'), notify_enabled=config.get('notify_enabled'),
                      installed_calendar_sha256=config.get('calendar_sha256'),
                      calendar_verified_at_install=config.get('calendar_verified'),
                      producer_receipt_hashes=hashes)
        if config.get('enabled') is not True:
            return result
        result['installed_calendar_valid'] = native.verify_installed_calendar(config)
        if not result['installed_calendar_valid']:
            result['findings'].append('optional_research_calendar_unverified')
        attempt, completed, cumulative = (objects.get(k,{}) for k in ('attempt','completed','cumulative'))
        latest = attempt.get('latest_attempt', attempt)
        result.update(status='unobservable', latest_attempt=latest,
            last_completed_computation={k:completed.get(k) for k in (
                'source_date','night_id','cumulative_generation','artifact_content_sha256')},
            source_date=latest.get('source_date') or completed.get('source_date'),
            source_scope=cumulative.get('source_scope'),
            pending_source_dates=cumulative.get('pending_source_dates'),
            invalidated_source_dates=cumulative.get('invalidated_source_dates'),
            notification_status=(objects.get('delivery') or {}).get('status'),
            cursor=objects.get('cursor'), artifact=str(base/'night_summary.json'),
            report_sha256=hashes.get('attempt'), source_generation=cumulative.get('generation'))
        # A delayed attempt neither erases the last computation nor proves a
        # new one. Native admission/window reasons retain their own deadlines.
        result['execution_status'] = latest.get('status', 'not_observed')
        result['execution_reason'] = latest.get('reason')
        result['cumulative_currentness'] = ('same_generation' if cumulative and
            completed.get('cumulative_generation') == cumulative.get('generation') else 'unverified')
        if latest.get('status') in {'failed', 'error', 'source_invalid'}:
            result['findings'].append('optional_research_execution_failed')
        if completed and cumulative and completed.get('cumulative_generation') != cumulative.get('generation'):
            result['findings'].append('optional_research_generation_mismatch')
        if cumulative.get('pending_source_dates') or cumulative.get('invalidated_source_dates'):
            result['source_quality'] = 'incomplete'
        else:
            result['source_quality'] = 'verified_native_scope' if cumulative.get('source_scope') else 'unobservable'
        scope = cumulative.get('source_scope')
        scope_current = False
        if isinstance(scope, dict) and scope.get('through_date'):
            scope_current = (native.research_source_scope(root/'data', through_date=scope['through_date']) == scope
                and native.source_cursor_states(base, scope['source_dates']) == cumulative.get('source_cursor_states'))
        result['source_scope_current'] = scope_current
        result['native_validated'] = bool(result['installed_calendar_valid'] and scope_current)
        result['validation_mode'] = 'bounded_native_receipts_calendar_and_cursor_scope'
        result['raw_source_revalidation'] = 'owned_by_native_research'
        result['observation_complete'] = bool(attempt and cumulative and scope_current and result['installed_calendar_valid'])
        result['status'] = ('source_invalid' if result['findings'] else
            'source_gap' if result['source_quality']=='incomplete' else
            'verified' if result['observation_complete'] else 'unobservable')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result.update(status='source_invalid', findings=['optional_research_receipt_invalid'],
                      error=str(exc), artifact=str(installation), native_validated=False)
    return result


def _current_semantic_owners(root, day):
    """Project unique parsed OPEN stable IDs from one exact checklist."""
    from src.engine.sync_docs_backlog_to_project import parse_checklist_tasks
    owners = Counter()
    path = root / 'docs/checklists' / (day + '-stage2-todo-checklist.md')
    if not path.is_file():
        raise ValueError('current_checklist_missing')
    for task in parse_checklist_tasks(current_path=path):
        if Path(task.source).resolve() != path.resolve():
            continue
        match = re.match(r'^\[([^\]]+)\]', task.title)
        if match:
            owners[match[1]] += 1
    return {key for key, count in owners.items() if count == 1}


def _semantic_owner_context(root, now, selection, observations):
    """Use a future owner only across a verified nontrading-day handoff.

    Reuse this sweep's native closure/readiness checks; do not reread raw
    sources, manufacture a calendar-day checklist, or borrow historical IDs.
    """
    day = _today_kst_str(now)
    context = dict(as_of_date=day, owner_checklist_date=day, basis='current_checklist')
    try:
        return _current_semantic_owners(root, day), context
    except ValueError as exc:
        if str(exc) != 'current_checklist_missing':
            raise
    target = _semantic_due_target(now)
    source = selection.get('source_date')
    handoffs = [item['semantics'] for item in observations
                if item.get('stage') == 'postclose_handoff'
                and item.get('semantics', {}).get('source_date') == source]
    if (is_krx_trading_day(datetime.fromisoformat(day).date())
            or selection.get('status') != 'receipt_selected' or selection.get('findings')
            or not isinstance(source, str) or not source < day < target
            or selection.get('target_date') != target
            or selection.get('prepared_source_date') != source or len(handoffs) != 1):
        raise ValueError('current_checklist_missing')
    handoff = handoffs[0]
    prepared = handoff.get('prepared') or {}
    if (handoff.get('status') != 'done' or handoff.get('findings')
            or not handoff.get('report_sha256')
            or handoff.get('report_sha256') != selection.get('generation')
            or handoff.get('observation_date') != day
            or handoff.get('bound_target_date') != target
            or handoff.get('next_due_target_date') != target
            or prepared.get('status') != 'pass' or prepared.get('findings')
            or prepared.get('source_date') != source or prepared.get('target_date') != target
            or not prepared.get('selected_release_commit')
            or prepared.get('actual_pid_consumed') is not False
            or prepared.get('runtime_effect') is not False):
        raise ValueError('current_checklist_missing')
    owners = _current_semantic_owners(root, target)
    context.update(owner_checklist_date=target, basis='verified_next_session_handoff',
                   source_date=source, controller_sha256=handoff['report_sha256'],
                   selected_release_commit=prepared['selected_release_commit'])
    return owners, context


def _semantic_alerts(name, semantics, source_date, *, current_owners=None, as_of_date=None):
    alerts = _semantic_alert_candidates(name, semantics, source_date)
    for alert in alerts:
        alert.update(observation_date=semantics.get('observation_date', as_of_date),
            bound_target_date=semantics.get('bound_target_date'),
            next_due_target_date=semantics.get('next_due_target_date'))
        if current_owners is not None:
            _project_semantic_owner(alert, current_owners, as_of_date)
    return alerts


def _project_semantic_owner(alert, current_owners, as_of_date):
    mapping = {
        'main_machine_policy': 'DirectFamilySourceRepairMainMechanisticEntry',
        'main_auxiliary_policy': 'DirectFamilySourceRepairCompactAuxiliary',
        'postclose_handoff': 'DirectFamilyPreopenPolicyHandoff',
        'entry_cancel_wait_tuning': 'DirectFamilySourceRepairEntryCancelWait',
        'legacy_machine_report': 'DirectFamilySourceRepairMainMechanisticEntry',
        'holding_profit_exit': 'HoldingProfitExitSourceContractRepair',
        'initial_quantity': 'InitialQuantityProducerConsumerRepair1010',
        'main_stop_confirmation': 'MainStopLossRetirementRuntimeTuning1010',
        'main_market_weakness_research': 'MainMarketWeaknessPostcloseObservation1008',
    }
    owner = mapping.get(alert['stage'])
    if (alert['stage'] == 'main_stop_confirmation' and owner not in current_owners
            and 'DirectFamilyPreopenPolicyHandoff' in current_owners):
        owner = 'DirectFamilyPreopenPolicyHandoff'
    if (alert['stage']=='main_market_weakness_research' and owner not in current_owners
            and 'PreSubmitSemanticCurrentization1016' in current_owners):
        owner = 'PreSubmitSemanticCurrentization1016'
    if alert['stage']=='policy_generation':
        from src.engine.monitoring.policy_generation_contract import OWNERS
        owner=OWNERS.get(alert.get('scope'))
    alert.update(producer_owner=alert['owner'], historical_owner=alert['owner'],
                     owner=owner if owner in current_owners else 'UNRESOLVED_CURRENT_OWNER:' + str(owner),
                     owner_status='current_open' if owner in current_owners else 'unresolved',
                     observation_date=as_of_date, effective_date=alert.get('bound_target_date') or alert.get('target_date'))


def _semantic_alert_candidates(name, semantics, source_date):
    if semantics.get('status') in {'off', 'historical_diagnostic'}:
        return []
    if name in {"holding_profit_exit", "initial_quantity", "main_stop_confirmation", "main_market_weakness_research"}:
        if semantics.get("status") in {"future_due", "not_assessed", "not_required_before_introduction"}:
            return []
        if semantics.get("status") == "unobservable" and not semantics.get("expected_overdue"):
            return []
        return [dict(source_date=source_date, target_date=semantics.get("target_date"),
            stage=name, scope="report", reason=reason, status=semantics.get("status"),
            expected_overdue=semantics.get("expected_overdue", False),
            artifact=semantics.get("artifact"), generation=semantics.get("report_sha256"),
            source_generation=semantics.get("source_generation"),
            source_gap_identity=semantics.get("source_gap_identity") if name == "holding_profit_exit" else None,
            affected=semantics.get("source_gap_count") if name == "holding_profit_exit" and reason == "source_gap" else None,
            observation_generation=semantics.get("observation_generation"),
            policy_hash=semantics.get("policy_file_sha256"),
            owner="holding_exit_sentinel" if name == "holding_profit_exit" else name,
            closure_test="native_complete_exact_date_scope_binding_and_original_reason_resolved")
            for reason in sorted(set(semantics.get("findings") or []))
            if reason != "economics_null"]
    if name == "entry_cancel_wait_tuning":
        if semantics.get("status") != "source_invalid":
            return []
        return [{"source_date":source_date, "stage":name, "scope":"report",
            "reason":reason if reason.startswith("cancel_wait_") else "cancel_wait_reconciliation_ledger_invalid",
            "status":semantics["status"], "artifact":semantics.get("artifact"),
            "generation":semantics.get("report_sha256"),
            "affected":semantics.get("unclassified_submission_count"),
            "eligible":semantics.get("daily_submitted_parent_count"),
            "owner":"EntryCancelWaitSourceReconciliation1002",
            "closure_test":"same_date_original_source_ledger_policy_and_consumer_projection"}
            for reason in semantics.get("findings", [])]
    actionable = set("""
        auxiliary_candidate_population_invalid auxiliary_completed_report_generation_mismatch
        auxiliary_completed_report_missing auxiliary_execution_failed auxiliary_economic_denominator_invalid
        auxiliary_economic_metrics_invalid auxiliary_exact_plan_lineage_missing
        auxiliary_label_population_binding_invalid auxiliary_label_report_binding_invalid
        auxiliary_label_report_missing auxiliary_outcome_label_binding_missing auxiliary_outcome_label_source_gap
        auxiliary_population_denominator_invalid auxiliary_primary_economics_source_blocked
        auxiliary_scope_selection_contract_invalid auxiliary_scope_selection_status_invalid
        auxiliary_selected_without_independent_evidence auxiliary_source_lineage_invalid
        auxiliary_source_tuning_not_allowed auxiliary_stage_report_contract_invalid
        auxiliary_terminal_identity_or_hash_invalid auxiliary_terminal_source_binding_missing
        auxiliary_chronological_split_invalid auxiliary_frozen_selection_binding_invalid
        auxiliary_full_cost_census_invalid auxiliary_completed_response_census_invalid
        auxiliary_selected_without_frozen_full_cost_evidence auxiliary_selection_version_invalid
        auxiliary_eligible_identity_uninstrumented compact_operating_rows_all_excluded compact_projection_invalid
        machine_execution_failed machine_exclusion_counts_invalid machine_full_report_missing_with_winrate_sidecar
        machine_operating_economics_incomplete machine_operating_paired_unbound machine_population_count_invalid
        machine_report_date_or_hash_invalid machine_scope_evaluations_missing machine_scope_row_invalid
        machine_selected_without_recovery_evidence machine_selection_contract_invalid machine_selection_version_invalid
        machine_scope_selection_missing machine_source_contract_exclusions
        winrate_candidate_bundle_or_scope_mismatch winrate_market_denominator_invalid winrate_population_denominator_invalid
        winrate_report_hash_or_scope_invalid winrate_report_schema_invalid winrate_successor_hurdle_invalid
        winrate_selected_zero_or_undefined winrate_semantic_validation_failed winrate_terminal_binding_invalid
        winrate_execution_failed next_preopen_prepared_contract_invalid postclose_handoff_contract_invalid
        continuous_reversal_report_schema_invalid continuous_reversal_report_hash_or_date_invalid
        continuous_reversal_stage_report_mismatch continuous_reversal_dated_policy_invalid
        postclose_handoff_generation_invalid postclose_handoff_execution_failed
        episode_policy:execution_failed
    """.split())
    if semantics.get("status") in {"not_assessed", "unobservable"}:
        return []
    reasons = [reason for reason in semantics.get("findings", [])
               if reason in actionable or reason.startswith('continuous_reversal_execution_not_completed:')]
    if not reasons and semantics.get("status") == "source_invalid":
        reasons = ["postclose_handoff_contract_invalid" if name == "postclose_handoff"
                   else "auxiliary_stage_report_contract_invalid" if name == "main_auxiliary_policy"
                   else "machine_report_date_or_hash_invalid"]
    return [{"source_date": source_date, "target_date": semantics.get('target_date'), "stage": name,
             "scope": scope, "reason": reason, "status": semantics.get("status"),
             "artifact": semantics.get("artifact"), "generation": semantics.get("report_sha256"),
             "affected": (semantics.get("outcome_label_source_gap_count")
                          if reason == "auxiliary_outcome_label_source_gap" else None),
             "eligible": (semantics.get("paired_comparable_count")
                          if reason == "auxiliary_primary_economics_source_blocked"
                          else semantics.get("source_lineage_counts", {}).get("writer_trace_plan_joined")
                          if reason == "auxiliary_exact_plan_lineage_missing"
                          else (semantics["economic_screened_total"] - semantics["outcome_label_source_gap_count"])
                          if reason == "auxiliary_outcome_label_source_gap" and type(semantics.get("economic_screened_total")) is int
                          else semantics.get("scopes", {}).get(scope, {}).get("eligible_count",
                           semantics.get("scopes", {}).get(scope, {}).get("eligible",
                           semantics.get("eligible_count")))),
             "total": (semantics.get("economic_screened_total") if reason in {
                 "auxiliary_primary_economics_source_blocked", "auxiliary_exact_plan_lineage_missing",
                 "auxiliary_outcome_label_source_gap", "auxiliary_outcome_label_binding_missing"}
                 else semantics.get("scopes", {}).get(scope, {}).get("full", semantics.get("screened_total"))),
             "owner": ("continuous_reversal_postclose" if semantics.get('stage_id') in {'main_machine_policy', 'main_auxiliary_policy'}
                       and (semantics.get('selection_metric') == 'cumulative_raw_win_fraction'
                            or str(semantics.get('artifact') or '').find('/continuous_reversal/') >= 0)
                       else "compact_auxiliary_paired_replay" if name == "main_auxiliary_policy"
                       else "next_preopen_readiness" if name == "postclose_handoff"
                       else "ai_action_outcome_calibration"),
             "closure_test": "same_date_scope_source_selection_and_terminal_hashes"}
            for reason in reasons
            for scope in ([key for key, value in (semantics.get("scopes") or {}).items()
                           if reason in value.get("findings", [])] or ["report"])]


def _reconcile_update_kospi_master_difference(
    payload: dict[str, Any],
    details: dict[str, Any],
) -> bool:
    """Accept only a fully verified, non-active eligibility difference.

    ``update_kospi`` deliberately preserves FDR rows even when the official
    ka10099 listing response does not return them.  That is a useful warning
    until the same-date canonical common-stock master proves every omitted
    code is outside the active trading universe.  Keep the reconciliation in
    the detector so the producer's raw warning and missing-code evidence stay
    intact.
    """

    if payload.get("status") != "completed_with_warnings":
        return False
    if payload.get("failed_steps") != []:
        return False
    if payload.get("warning_steps") != ["update_kospi_data"]:
        return False

    target_date_text = str(payload.get("target_date") or "").strip()
    try:
        target_date = date.fromisoformat(target_date_text)
    except ValueError:
        return False

    steps = payload.get("steps")
    if not isinstance(steps, list):
        return False
    update_steps = [
        step
        for step in steps
        if isinstance(step, dict) and step.get("name") == "update_kospi_data"
    ]
    if len(update_steps) != 1:
        return False
    update_step = update_steps[0]
    step_details = update_step.get("details")
    if not isinstance(step_details, dict):
        return False
    eligibility = step_details.get("eligibility")
    if (
        update_step.get("status") != "completed_with_warnings"
        or step_details.get("reason") != "market_eligibility_partial"
        or not isinstance(eligibility, dict)
        or eligibility.get("complete") is not True
        or eligibility.get("status") != "partial"
    ):
        return False

    market_meta = eligibility.get("market_source_meta")
    missing_codes = eligibility.get("missing_codes")
    requested_count = eligibility.get("requested_code_count")
    received_count = eligibility.get("received_code_count")
    if (
        not isinstance(market_meta, list)
        or {str(row.get("market")) for row in market_meta if isinstance(row, dict)}
        != {"0", "10"}
        or any(
            not isinstance(row, dict)
            or row.get("complete") is not True
            or row.get("continuous_next_key_missing") is True
            or row.get("continuous_page_limit_reached") is True
            for row in market_meta
        )
        or not isinstance(missing_codes, list)
        or not missing_codes
        or len({str(code) for code in missing_codes}) != len(missing_codes)
        or any(len(str(code)) != 6 or not str(code).isdigit() for code in missing_codes)
        or not isinstance(requested_count, int)
        or isinstance(requested_count, bool)
        or not isinstance(received_count, int)
        or isinstance(received_count, bool)
        or received_count + len(missing_codes) != requested_count
    ):
        return False

    master_path = existing_or_gzip_path(
        PROJECT_ROOT
        / "data/report/micro_reversion_economic_reference"
        / f"micro_reversion_symbol_master_{target_date_text}.json"
    )
    if not master_path.exists():
        return False

    try:
        from src.engine.scalping.micro_reversion.symbol_master import (
            SymbolLookupStatus,
            VerifiedSymbolMaster,
        )

        master = VerifiedSymbolMaster.from_json_path(
            master_path,
            require_canonical_owner=True,
        )
        allowed_statuses = {
            SymbolLookupStatus.MISSING,
            SymbolLookupStatus.OUTSIDE_EFFECTIVE_WINDOW,
        }
        lookup_statuses = {
            str(code): master.lookup(code, as_of=target_date).status
            for code in missing_codes
        }
    except (OSError, TypeError, ValueError):
        return False

    unresolved = {
        code: status.value
        for code, status in lookup_statuses.items()
        if status not in allowed_statuses
    }
    details["update_kospi_status_master_path"] = str(master_path)
    details["update_kospi_status_master_difference_count"] = len(missing_codes)
    details["update_kospi_status_master_difference_unresolved"] = unresolved
    if unresolved:
        return False
    details["update_kospi_status_warning_reconciliation"] = "benign_master_difference"
    return True


ARTIFACT_SCHEDULE_CONTRACTS: dict[str, dict[str, Any]] = {
    "pattern_lab_currentness_audit_report": {"markers": ["THRESHOLD_CYCLE_POSTCLOSE"], "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE", "parent_default_enabled": False},
    "pattern_lab_propagation_audit_report": {"markers": ["THRESHOLD_CYCLE_POSTCLOSE"], "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE", "parent_default_enabled": False},
    "codebase_performance_workorder_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_CODEBASE_PERFORMANCE_WORKORDER_REPORT",
        "parent_default_enabled": False,
    },
    "codex_workorder_runner_report": {
        "markers": ["POSTCLOSE_DONE_CONTROLLER"],
        "parent_env_key": "POSTCLOSE_DONE_CONTROLLER_RUN_CODEX",
        "parent_default_enabled": False,
    },
    "swing_live_dry_run_status": {"markers": ["SWING_LIVE_DRY_RUN"]},
    "swing_selection_funnel_report": {"markers": ["SWING_LIVE_DRY_RUN"]},
    "swing_lifecycle_audit_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_threshold_ai_review_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_improvement_automation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_runtime_approval_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_pattern_lab_automation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_model_retrain_diagnosis": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_bull_period_ai_review": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_retrain_report": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_retrain_status": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_model_registry_current": {"markers": ["SWING_MODEL_RETRAIN_POSTCLOSE"]},
    "swing_daily_simulation_status": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
    "swing_daily_simulation_report": {
        "markers": ["THRESHOLD_CYCLE_POSTCLOSE"],
        "parent_env_key": "THRESHOLD_CYCLE_RUN_SWING_POSTCLOSE",
        "parent_default_enabled": False,
    },
}

ARTIFACT_TERMINAL_SKIP_CONTRACTS: dict[str, dict[str, str]] = {
    "codebase_performance_workorder_report": {
        "log": "logs/threshold_cycle_postclose_cron.log",
        "step": "codebase_performance_workorder",
    }
}


ARTIFACT_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "pipeline_events",
        "path_template": "data/pipeline_events/pipeline_events_{date}.jsonl",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
        "window_grace_sec": 300,
    },
    {
        "id": "threshold_events",
        "path_template": "data/threshold_cycle/threshold_events_{date}.jsonl",
        "partitioned_compact": {
            "checkpoint_template": "data/threshold_cycle/checkpoints/{date}.json",
            "partition_glob_template": "data/threshold_cycle/date={date}/family=*/part-*.jsonl*",
        },
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
        "window_grace_sec": 300,
    },
    {
        "id": "daily_recommendations_csv",
        "path_template": "data/daily_recommendations_v2.csv",
        "max_staleness_sec": 3600,
        "critical": False,
        "window_start": (7, 20),
        "window_end": (8, 0),
        "trading_day_only": True,
        "content_freshness": {
            "format": "csv",
            "date_field": "date",
            "max_age_days": 7,
            "min_rows": 1,
        },
    },
    {
        "id": "daily_recommendations_diag",
        "path_template": "data/daily_recommendations_v2_diagnostics.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "window_start": (7, 20),
        "window_end": (8, 0),
        "trading_day_only": True,
        "content_freshness": {
            "format": "json",
            "date_field": "latest_date",
            "max_age_days": 7,
            "min_count_field": "selected_count",
            "min_count": 1,
        },
    },
    {
        "id": "runtime_policy_bootstrap",
        "path_template": "data/runtime/policy_bootstrap/runtime_policy_bootstrap_{date}.json",
        "max_staleness_sec": 900,
        "critical": True,
        "window_start": (7, 35),
        "window_end": (7, 50),
        # The producer and the full detector are both installed at 07:35.
        # Allow one detector interval for the producer to replace the previous
        # evening's target-date handoff before treating it as stale.
        "window_grace_sec": 300,
        "trading_day_only": True,
    },
    {
        "id": "threshold_preopen_status",
        "path_template": "data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.status.json",
        "max_staleness_sec": 1800,
        "critical": True,
        "trading_day_only": True,
        "window_start": (7, 50),
        "window_end": (8, 5),
        "json_status_field": "status",
        "json_ok_values": ["succeeded"],
    },
    {
        "id": "submission_bottleneck_monitor",
        "first_required_date": "2026-09-21",
        "path_template": "data/report/buy_funnel_sentinel/submission_bottleneck_monitor_{date}.json",
        "max_staleness_sec": 600,
        "critical": True,
        "trading_day_only": True,
        "window_start": (8, 10),
        "window_end": (20, 0),
        "json_status_field": "notification_status",
        "json_ok_values": ["idle", "sent", "cooldown"],
    },
    {
        "id": "buy_funnel_sentinel_report",
        "path_template": "data/report/buy_funnel_sentinel/buy_funnel_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "bd_fbuy_accum_pre_artifact",
        "path_template": "data/runtime/bd_fbuy_accum_pre/BD_FBUY_ACCUM_PRE_V1_{date}.json",
        "max_staleness_sec": 900,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 20),
        "json_status_field": "schema_version",
        "json_ok_values": ["BD_FBUY_ACCUM_PRE_V1"],
    },
    {
        "id": "holding_exit_sentinel_report",
        "path_template": "data/report/holding_exit_sentinel/holding_exit_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "holding_exit_sentinel_premarket_report",
        "path_template": "data/report/holding_exit_sentinel/holding_exit_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (8, 5),
        "window_end": (8, 55),
        # Producer and detector share the 08:05 cron trigger. Allow its first
        # publication one cadence; this never relaxes an existing receipt.
        "window_grace_sec": 300,
    },
    {
        "id": "holding_exit_sentinel_aftermarket_report",
        "path_template": "data/report/holding_exit_sentinel/holding_exit_sentinel_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (16, 0),
        "window_end": (19, 50),
    },
    {
        "id": "panic_sell_defense_report",
        "path_template": "data/report/panic_sell_defense/panic_sell_defense_{date}.md",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "market_panic_breadth_report",
        "path_template": "data/report/market_panic_breadth/market_panic_breadth_{date}.json",
        "max_staleness_sec": 600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 5),
        "window_end": (15, 30),
    },
    {
        "id": "runtime_approval_summary_report",
        "path_template": "data/report/runtime_approval_summary/runtime_approval_summary_{date}.json",
        "max_staleness_sec": 1800,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "window_grace_sec": 1200,
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
            "process_patterns": [
                "deploy/run_threshold_cycle_postclose.sh",
                "run_threshold_cycle_postclose.sh",
            ],
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "threshold_postclose_status",
        "path_template": "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 40),
        "window_end": (22, 10),
        "json_status_field": "status",
        "json_ok_values": ["succeeded"],
        "running_status_deadline": (23, 20),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
            "process_patterns": [
                "deploy/run_threshold_cycle_postclose.sh",
                "run_threshold_cycle_postclose.sh",
            ],
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "postclose_done_controller_report",
        "path_template": "data/report/postclose_done_controller/postclose_done_controller_{date}.json",
        "max_staleness_sec": 3600,
        "critical": True,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 55),
        "window_grace_sec": 300,
        "json_status_field": "status",
        "json_ok_values": ["done", "dry_run_planned"],
        "suppress_missing_while_cron_in_progress": {
            "id": "postclose_done_controller",
            "log": "logs/postclose_done_controller_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "codex_workorder_runner_report",
        "path_template": "data/report/codex_workorder_runner/codex_workorder_runner_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 55),
        "json_status_field": "status",
        "json_ok_values": ["completed", "dry_run_planned"],
        "suppress_missing_while_cron_in_progress": {
            "id": "postclose_done_controller",
            "log": "logs/postclose_done_controller_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "pipeline_event_verbosity_report",
        "path_template": "data/report/pipeline_event_verbosity/pipeline_event_verbosity_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "observation_source_quality_audit_report",
        "path_template": "data/report/observation_source_quality_audit/observation_source_quality_audit_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "codebase_performance_workorder_report",
        "path_template": "data/report/codebase_performance_workorder/codebase_performance_workorder_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "system_metric_samples",
        "path_template": "logs/system_metric_samples.jsonl",
        "max_staleness_sec": 180,
        "critical": False,
        "trading_day_only": True,
        "window_start": (9, 0),
        "window_end": (15, 30),
    },
    {
        "id": "swing_live_dry_run_status",
        "path_template": "data/report/swing_selection_funnel/status/swing_live_dry_run_{date}.status.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 15),
        "window_end": (20, 35),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_selection_funnel_report",
        "path_template": "data/report/swing_selection_funnel/swing_selection_funnel_{date}.md",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 15),
        "window_end": (20, 35),
    },
    {
        "id": "swing_lifecycle_audit_report",
        "path_template": "data/report/swing_lifecycle_audit/swing_lifecycle_audit_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_threshold_ai_review_report",
        "path_template": "data/report/swing_threshold_ai_review/swing_threshold_ai_review_{date}.md",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_improvement_automation_report",
        "path_template": "data/report/swing_improvement_automation/swing_improvement_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_runtime_approval_report",
        "path_template": "data/report/swing_runtime_approval/swing_runtime_approval_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "swing_pattern_lab_automation_report",
        "path_template": "data/report/swing_pattern_lab_automation/swing_pattern_lab_automation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
    },
    {
        "id": "pattern_lab_currentness_audit_report",
        "path_template": "data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "pattern_lab_propagation_audit_report",
        "path_template": "data/report/pattern_lab_propagation_audit/pattern_lab_propagation_audit_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (20, 10),
        "window_end": (21, 40),
        "suppress_missing_while_cron_in_progress": {
            "id": "threshold_cycle_postclose",
            "log": "logs/threshold_cycle_postclose_cron.log",
        },
        "allow_missing_after_window_while_cron_in_progress": True,
    },
    {
        "id": "swing_model_retrain_diagnosis",
        "path_template": "data/report/swing_model_retrain/diagnosis_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_bull_period_ai_review",
        "path_template": "data/report/swing_model_retrain/bull_period_ai_review_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_model_retrain_report",
        "path_template": "data/report/swing_model_retrain/swing_model_retrain_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_model_retrain_status",
        "path_template": "data/report/swing_model_retrain/status/swing_model_retrain_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_model_registry_current",
        "path_template": "data/model_registry/swing_v2/current.json",
        "max_staleness_sec": 7776000,
        "critical": False,
        "trading_day_only": True,
        "window_start": (17, 30),
        "window_end": (18, 30),
    },
    {
        "id": "swing_daily_simulation_status",
        "path_template": "data/report/swing_daily_simulation/status/swing_daily_simulation_{date}.status.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 0),
        "window_end": (21, 50),
        "json_status_field": "status",
        "json_ok_values": ["succeeded", "skipped"],
    },
    {
        "id": "swing_daily_simulation_report",
        "path_template": "data/report/swing_daily_simulation/swing_daily_simulation_{date}.json",
        "max_staleness_sec": 3600,
        "critical": False,
        "one_shot": True,
        "trading_day_only": True,
        "window_start": (21, 0),
        "window_end": (21, 50),
    },
    {
        "id": "update_kospi_status",
        "path_template": "data/runtime/update_kospi_status/update_kospi_{date}.json",
        "max_staleness_sec": 1800,
        "critical": False,
        "trading_day_only": False,
        "window_start": (20, 5),
        "window_end": (21, 5),
        "json_status_field": "status",
        "json_ok_values": ["completed", "skipped_non_trading_day"],
    },
]


def _postclose_main_absent():
    import subprocess
    try:
        result = subprocess.run(['pgrep','-f',r'(^|[[:space:]/])bot_main[.]py([[:space:]]|$)'],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=2,check=False)
        return result.returncode == 1
    except (OSError,subprocess.TimeoutExpired):
        return False


def _submission_observer_closed_window(payload, root, now, signature, *, window_end, max_staleness_sec):
    """Retain a close-time observation; never turn it into current/full coverage."""
    try:
        from src.engine.error_detectors.process_health import _is_expected_thread_terminal
        if now.tzinfo is None: now = now.replace(tzinfo=ZoneInfo('Asia/Seoul'))
        now = now.astimezone(ZoneInfo('Asia/Seoul'))
        close = now.replace(hour=window_end[0], minute=window_end[1], second=0, microsecond=0)
        generation = payload.get('observer_generation') or {}
        receipt = generation.get('selector_reported_pid_receipt') or {}
        state, _ = _observer_small_object(Path(root)/'tmp/error_detector_heartbeat.json')
        main = state.get('main_loop') or {}
        terminal = (state.get('threads') or {}).get('sniper_engine') or {}
        beat, ended = _observer_clock(main.get('last_beat')), _observer_clock(terminal.get('last_beat'))
        started, completed = _observer_clock(payload.get('as_of')), _observer_clock(generation.get('completed_at'))
        mtime = signature[7]/1_000_000_000
        closed = None
        if _postclose_main_absent():
            from src.engine.automation.intraday_release_handoff import closed_consumption_observation
            closed = closed_consumption_observation(payload.get('date'), now=now)
            if closed['pid_identity'] != dict(pid=receipt.get('pid'), start_ticks=receipt.get('start_ticks'),
                                               cwd=receipt.get('process_cwd')):
                return None
        anchor = max(ended.timestamp(), completed.timestamp(), mtime) if ended and completed else None
        if (payload.get('date') != now.date().isoformat() or now < close
                or type(receipt.get('pid')) is not int or main.get('pid') != receipt['pid']
                or terminal.get('alive') is not False or type(terminal.get('unresolved_scalping_count')) is not int
                or terminal['unresolved_scalping_count'] != 0 or terminal.get('unresolved_scalping_codes') != ''
                or not _is_expected_thread_terminal('sniper_engine', terminal, now_ts=now.timestamp())
                or any(at is None for at in (beat, ended, started, completed))
                or not close <= ended <= beat <= now
                or closed is None and not 0 <= (now-beat).total_seconds() <= max_staleness_sec
                or not started <= completed <= now or mtime > now.timestamp()
                or abs((started-ended).total_seconds()) > max_staleness_sec
                or not 0 <= anchor-completed.timestamp() <= anchor-started.timestamp() <= max_staleness_sec
                or not 0 <= anchor-mtime <= max_staleness_sec):
            return None
        return dict(status='native_market_close_observed', terminal_at=ended.isoformat(),
            main_state='closed_consumption_verified' if closed else 'live',
            report_age_at_close_sec=ended.timestamp()-mtime, as_of_age_at_close_sec=(ended-started).total_seconds(),
            assessment='retained_close_time_observation', current_observation_verified=False,
            full_coverage_proven=False, runtime_effect=False, allowed_runtime_apply=False)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, IndexError):
        return None


def _closed_submission_observer_evidence(payload, root, source_day, current_day):
    """Attest a closed day's retained observation without claiming current coverage."""
    if (not source_day or source_day > current_day or payload.get('date') != source_day
            or payload.get('execution_status') != 'completed'
            or payload.get('semantic_status') not in {'partial', 'validated'}):
        return None
    try:
        closure = None
        if source_day == current_day:
            selected_path=Path(root)/'data/runtime/runtime_release_selection.json'
            selected,selected_sha=_observer_small_object(selected_path,limit=1024*1024)
            eod_path=Path(root)/'data/runtime/update_kospi_status'/f'update_kospi_{source_day}.json'
            eod,eod_sha=_observer_small_object(eod_path,limit=1024*1024)
            finished=_observer_clock(eod.get('finished_at'))
            selected_at=_observer_clock(selected.get('selected_at_kst'))
            next_day=selected.get('next_operating_date')
            if not isinstance(next_day,str) or date.fromisoformat(next_day).isoformat()!=next_day:
                return None
            db=eod.get('db_state') or {}
            if (selected.get('approval_scope')!='after_postclose_deploy_for_next_regular_start'
                    or selected.get('actual_pid_consumed') is not False
                    or selected.get('actual_pid_receipt') is not None
                    or next_day<=source_day
                    or eod.get('target_date')!=source_day
                    or eod.get('status') not in {'completed','completed_with_warnings'}
                    or db.get('latest_quote_date')!=source_day
                    or type(db.get('rows_on_latest_date')) is not int or db['rows_on_latest_date']<=0
                    or finished is None or selected_at is None or selected_at<finished
                    or finished.date().isoformat()!=source_day or not _postclose_main_absent()):
                return None
            closure=dict(status='same_day_eod_closed_next_start_selected',eod_sha256=eod_sha,
                         selection_sha256=selected_sha)
        terminal, _ = _observer_small_object(Path(root) / 'data/report/threshold_cycle_postclose_status' /
            f'threshold_cycle_postclose_{source_day}.status.json', limit=1024 * 1024)
        if terminal.get('target_date') != source_day or terminal.get('status') != 'succeeded':
            return None
        archive = Path(root) / 'data/runtime/postclose_recovery' / source_day
        candidates = sorted(archive.glob('*/selection-before.json'))
        if len(candidates) > 16:
            return None
        for path in candidates:
            if _submission_observer_generation_issue(payload, root, selection_path=path) is None:
                if closure and (_observer_small_object(selected_path,limit=1024*1024)[1]!=selected_sha
                        or _observer_small_object(eod_path,limit=1024*1024)[1]!=eod_sha
                        or not _postclose_main_absent()):
                    return None
                return dict(status='historical_generation_verified', selection_path=str(path),
                    closure=closure,
                    selection_sha256=payload['observer_generation']['selection_sha256'],
                    semantic_status=payload['semantic_status'],
                    source_gap_preserved=payload.get('source_gap_semantics'),
                    current_generation_verified=False, current_observation_verified=False,
                    full_coverage_proven=False, runtime_effect=False, allowed_runtime_apply=False)
    except (OSError, ValueError, TypeError, KeyError):
        pass
    return None


@register_detector
class ArtifactFreshnessDetector(BaseDetector):
    id = "artifact_freshness"
    name = "Artifact Freshness Detector"
    category = "artifact"

    def check(self) -> DetectionResult:
        now_dt = datetime.now()
        now_ts = time.time()
        now_h, now_m = _kst_time_tuple(now_dt)
        now_total = now_h * 60 + now_m
        source_day = getattr(self, "postclose_source_date", None)
        today = source_day or _today_kst_str(now_dt)
        past_source_day = bool(source_day and source_day < _today_kst_str(now_dt))
        if past_source_day:
            now_total = 24 * 60
        trading_day = is_krx_trading_day(datetime.strptime(today, "%Y-%m-%d").date())
        details: dict = {}
        issues: list[str] = []
        warnings: list[str] = []
        installed_crontab = load_installed_crontab()

        observer_id = 'submission_bottleneck_monitor'
        observer_registry = [item for item in ARTIFACT_REGISTRY if item['id'] == observer_id]
        sweep_day = _today_kst_str(now_dt)

        def check_registered_artifacts(registry):
            for artifact in registry:
                aid = artifact["id"]
                if today < artifact.get("first_required_date", "0001-01-01"):
                    details[f"{aid}_status"] = "not_required_before_introduction"
                    continue
                artifact_day = today
                artifact_now_total = now_total
                artifact_past_source_day = past_source_day
                artifact_trading_day = trading_day
                if aid == observer_id and past_source_day:
                    # A closed postclose source date cannot own live PID
                    # observation. Validate today's producer after consumption;
                    # all frozen research/controller inputs retain source_day.
                    artifact_day = sweep_day
                    artifact_past_source_day = False
                    artifact_now_total = now_h * 60 + now_m
                    artifact_trading_day = is_krx_trading_day(date.fromisoformat(sweep_day))
                    details[f'{aid}_historical_source_date'] = today
                    details[f'{aid}_live_observation_date'] = sweep_day
                if aid == "runtime_policy_bootstrap" and past_source_day:
                    prepared = os.environ.get("POSTCLOSE_PREPARED_EFFECTIVE_DATE", "")
                    try:
                        prepared_day = date.fromisoformat(prepared)
                        if prepared <= today or not is_krx_trading_day(prepared_day):
                            raise ValueError("invalid prepared date")
                    except ValueError:
                        details[f"{aid}_status"] = "fail"
                        issues.append(f"{aid}: explicit prepared effective date missing or invalid")
                        continue
                    details[f"{aid}_historical_source_date"] = today
                    details[f"{aid}_prepared_effective_date"] = prepared
                    if prepared > _today_kst_str(now_dt):
                        details[f"{aid}_status"] = "future_due"
                        continue
                    artifact_day = prepared
                    artifact_past_source_day = prepared < _today_kst_str(now_dt)
                    artifact_now_total = 24 * 60 if artifact_past_source_day else now_h * 60 + now_m
                path_str = artifact["path_template"].replace("{date}", artifact_day)
                artifact_path = PROJECT_ROOT / path_str
                artifact_path = existing_or_gzip_path(artifact_path)
                critical = artifact.get("critical", False)
                max_stale = artifact.get("max_staleness_sec", 600)
                trading_day_only = artifact.get("trading_day_only", False)
                ws = artifact.get("window_start")
                we = artifact.get("window_end")

                if trading_day_only and not artifact_trading_day:
                    details[f"{aid}_status"] = "skip_non_trading_day"
                    continue

                schedule_contract = ARTIFACT_SCHEDULE_CONTRACTS.get(aid)
                if schedule_contract:
                    schedule_status, schedule_details = evaluate_schedule_contract(
                        installed_crontab,
                        **schedule_contract,
                    )
                    details[f"{aid}_schedule_contract"] = schedule_details
                    if schedule_status.startswith("disabled_"):
                        details[f"{aid}_status"] = schedule_status
                        continue

                ws_total = ws[0] * 60 + ws[1] if ws else None

                if ws_total is not None and artifact_now_total < ws_total:
                    details[f"{aid}_status"] = "not_yet_due"
                    details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                    continue

                past_window_end = False
                if we is not None:
                    window_end = now_dt.replace(
                        hour=we[0], minute=we[1], second=0, microsecond=0
                    )
                    past_window_end = artifact_past_source_day or now_dt >= window_end
                exists = artifact_path.exists()
                grace_sec = int(artifact.get("window_grace_sec") or 0)
                in_startup_grace = False
                if grace_sec > 0 and ws and not past_window_end:
                    window_start = now_dt.replace(
                        hour=ws[0], minute=ws[1], second=0, microsecond=0
                    )
                    elapsed_from_start = (now_dt - window_start).total_seconds()
                    in_startup_grace = 0 <= elapsed_from_start <= grace_sec
                if not exists and in_startup_grace:
                    details[f"{aid}_status"] = "startup_grace"
                    details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}"
                    details[f"{aid}_grace_sec"] = grace_sec
                    continue

                if not exists:
                    terminal_skip = self._terminal_skip_status(aid, artifact_day)
                    if terminal_skip:
                        details[f"{aid}_status"] = "pass_terminal_skip"
                        details[f"{aid}_terminal_skip"] = terminal_skip
                        continue
                    alternate_status = self._validate_partitioned_compact(
                        artifact,
                        artifact_day,
                        details,
                    )
                    if alternate_status:
                        status, warning = alternate_status
                        details[f"{aid}_status"] = status
                        if warning:
                            warnings.append(warning)
                        continue

                    in_progress_cron = self._is_upstream_cron_in_progress(
                        artifact.get("suppress_missing_while_cron_in_progress"),
                        artifact_day,
                    )
                    if in_progress_cron and not past_window_end:
                        warnings.append(
                            f"{aid}: upstream cron in progress; artifact not generated yet"
                        )
                        details[f"{aid}_status"] = "warning"
                        details[f"{aid}_upstream_status"] = "in_progress"
                        continue
                    if (
                        in_progress_cron
                        and past_window_end
                        and bool(
                            artifact.get(
                                "allow_missing_after_window_while_cron_in_progress"
                            )
                        )
                    ):
                        warnings.append(
                            f"{aid}: upstream cron still in progress after window end"
                        )
                        details[f"{aid}_status"] = "warning"
                        details[f"{aid}_upstream_status"] = "in_progress_after_window"
                        continue
                    if past_window_end:
                        if critical:
                            issues.append(f"{aid}: missing after window end")
                            details[f"{aid}_status"] = "fail"
                        else:
                            warnings.append(f"{aid}: not generated within window")
                            details[f"{aid}_status"] = "warning"
                    else:
                        if critical:
                            issues.append(f"{aid}: {path_str} missing")
                            details[f"{aid}_status"] = "fail"
                        else:
                            warnings.append(f"{aid}: {path_str} not found")
                            details[f"{aid}_status"] = "warning"
                    continue

                # The strict observer snapshot below owns its file clock and
                # handles disappearance/replacement without an unguarded stat.
                mtime = now_ts if aid == observer_id else artifact_path.stat().st_mtime
                age_sec = now_ts - mtime
                details[f"{aid}_age_sec"] = round(age_sec, 1)
                observer_snapshot = None
                if aid == "submission_bottleneck_monitor":
                    try:
                        observer_snapshot = _submission_observer_snapshot(artifact_path)
                        # The file clock and body must belong to this same read.
                        mtime = observer_snapshot[2][7] / 1_000_000_000
                        age_sec = now_ts - mtime
                        details[f"{aid}_age_sec"] = round(age_sec, 1)
                        dimensions = _submission_observer_dimensions(observer_snapshot[0], artifact_path, observer_snapshot[1])
                        dimensions['freshness'] = dict(status='future' if age_sec < 0 else 'stale' if age_sec > max_stale else 'fresh',
                            age_sec=round(age_sec, 1), max_staleness_sec=max_stale, clock='report_file_mtime')
                        body_clock = _observer_clock(observer_snapshot[0].get('as_of'))
                        generation = observer_snapshot[0].get('observer_generation')
                        completed_clock = _observer_clock(generation.get('completed_at')) if isinstance(generation, dict) else None
                        body_age = now_ts - body_clock.timestamp() if body_clock else None
                        completed_age = now_ts - completed_clock.timestamp() if completed_clock else None
                        dimensions['freshness']['body_clock'] = dict(
                            status=('fresh' if body_age is not None and completed_age is not None
                                    and 0 <= completed_age <= body_age <= max_stale else 'future_or_stale_or_unavailable'),
                            as_of_age_sec=body_age, completed_age_sec=completed_age,
                            max_staleness_sec=max_stale, clock='detector_wall_clock')
                        details[f'{aid}_observation_dimensions'] = dimensions
                        if past_window_end:
                            closed = _submission_observer_closed_window(observer_snapshot[0], PROJECT_ROOT,
                                now_dt, observer_snapshot[2], window_end=we, max_staleness_sec=max_stale)
                            if closed is not None:
                                dimensions['closed_window'] = closed
                        json_error = ""
                    except (OSError, ValueError, TypeError) as exc:
                        json_error = str(exc)
                else:
                    json_error = self._validate_json_artifact(artifact_path)
                if json_error:
                    details[f"{aid}_content_status"] = "invalid_json"
                    message = f"{aid}: invalid JSON ({json_error})"
                    if critical:
                        issues.append(message)
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(message)
                        details[f"{aid}_status"] = "warning"
                    continue
                if aid == "submission_bottleneck_monitor":
                    historical = _closed_submission_observer_evidence(observer_snapshot[0], PROJECT_ROOT,
                        source_day or today, _today_kst_str(now_dt))
                    if historical is not None:
                        try:
                            unchanged = _observer_file_signature(artifact_path.lstat()) == observer_snapshot[2]
                        except OSError:
                            unchanged = False
                        if unchanged:
                            details[f'{aid}_status'] = 'historical_observation_only'
                            details[f'{aid}_historical_evidence'] = historical
                            dimensions['generation'] = historical
                            warnings.append(f'{aid}: closed source-day observation retained; '
                                'current coverage and historical source gaps remain unverified')
                            continue
                    pending = _submission_observer_transition_pending(
                        PROJECT_ROOT, artifact_path, now_dt, max_staleness_sec=max_stale,
                        report_snapshot=observer_snapshot)
                    if pending is not None:
                        details[f"{aid}_status"] = "pending_first_current_observer"
                        details[f"{aid}_transition"] = pending
                        dimensions['generation'] = dict(status='pending_first_current_observer', current_observation_verified=False)
                        details[f"{aid}_current_observation_verified"] = False
                        warnings.append(f"{aid}: first current-generation observation pending; prior evidence retained")
                        continue
                status_warning = self._validate_json_status(artifact, artifact_path, details,
                    **({'observer_snapshot': observer_snapshot} if observer_snapshot is not None else {}))
                if (aid == 'submission_bottleneck_monitor' and age_sec > max_stale
                        and not past_window_end and not in_startup_grace):
                    message = f'{aid}: stale ({age_sec:.0f}s > {max_stale}s)'
                    if status_warning:
                        message += '; ' + status_warning.removeprefix(aid + ': ')
                    (issues if critical else warnings).append(message)
                    details[f'{aid}_status'] = 'fail' if critical else 'warning'
                    continue
                if status_warning:
                    observation_health = details.get(f'{aid}_observation_health') or {}
                    if (aid == observer_id and dimensions.get('closed_window')
                            and observation_health.get('reason') == 'bounded_no_applicable_observations'
                            and observation_health.get('status') == 'warning_pending'
                            and observation_health.get('unmet_conditions') == []
                            and details.get(f'{aid}_observation_health_projection_match') is True):
                        details[f'{aid}_status'] = 'closed_window_observation_only'
                        details[f'{aid}_current_observation_verified'] = False
                        warnings.append(f'{aid}: native market close; bounded empty observation retained; '
                            'partial validation and historical source gaps remain unverified')
                        continue
                    if (aid == 'submission_bottleneck_monitor' and 0 <= age_sec <= max_stale
                            and observation_health.get('status') == 'warning_pending'
                            and details.get(f'{aid}_observation_health_projection_match') is True):
                        warnings.append(status_warning)
                        details[f'{aid}_status'] = ('pending_no_applicable_observations'
                            if observation_health.get('reason') == 'bounded_no_applicable_observations'
                            else 'pending_bounded_observation')
                        details[f'{aid}_current_observation_verified'] = False
                        continue
                    if self._is_bounded_postclose_running(
                        artifact, artifact_path, artifact_day, now_dt
                    ):
                        warnings.append(
                            f"{aid}: exact-date postclose still running before deadline"
                        )
                        details[f"{aid}_status"] = "warning"
                        details[f"{aid}_upstream_status"] = "running_before_deadline"
                        details[f"{aid}_running_deadline"] = "23:20"
                        continue
                    if critical:
                        issues.append(status_warning)
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(status_warning)
                        details[f"{aid}_status"] = "warning"
                    continue
                content_warning, content_passed = self._validate_content_freshness(
                    artifact,
                    artifact_path,
                    details,
                    now_dt,
                )
                if content_warning:
                    warnings.append(content_warning)
                    details[f"{aid}_status"] = "warning"
                    continue
                if content_passed:
                    details[f"{aid}_status"] = "pass_content_date"
                    continue

                if artifact.get("one_shot"):
                    details[f"{aid}_status"] = "pass_one_shot"
                    continue

                if past_window_end:
                    details[f"{aid}_status"] = "pass_after_window"
                    continue

                if age_sec > max_stale:
                    if in_startup_grace:
                        details[f"{aid}_status"] = "startup_grace"
                        details[f"{aid}_window"] = f"{ws[0]:02d}:{ws[1]:02d}" if ws else ""
                        details[f"{aid}_grace_sec"] = grace_sec
                        details[f"{aid}_startup_stale_suppressed"] = True
                        continue
                    if critical:
                        issues.append(f"{aid}: stale ({age_sec:.0f}s > {max_stale}s)")
                        details[f"{aid}_status"] = "fail"
                    else:
                        warnings.append(f"{aid}: stale ({age_sec:.0f}s > {max_stale}s)")
                        details[f"{aid}_status"] = "warning"
                else:
                    details[f"{aid}_status"] = "pass"

        check_registered_artifacts([item for item in ARTIFACT_REGISTRY if item['id'] != observer_id])

        cancel_wait_day = _cancel_wait_monitor_source_date(PROJECT_ROOT, today)
        cancel_wait = None
        if trading_day or cancel_wait_day != today:
            cancel_wait = _entry_cancel_wait_result_semantics(PROJECT_ROOT, cancel_wait_day, now_dt)
            details["entry_cancel_wait_result_semantics"] = cancel_wait
            if cancel_wait["findings"]:
                warnings.append("entry_cancel_wait_result_semantics: " + ", ".join(cancel_wait["findings"]))
        if trading_day:
            holding_semantics = _holding_profit_exit_semantics(PROJECT_ROOT, today, now=now_dt)
            details["holding_profit_exit_semantics"] = holding_semantics
            if holding_semantics["findings"]:
                warnings.append("holding_profit_exit_semantics: " + ", ".join(
                    holding_semantics["findings"]))
        selection = _completed_semantic_source(PROJECT_ROOT, now_dt)
        details['completed_semantic_source'] = selection
        semantic_days = list(dict.fromkeys(
            ([today] if trading_day or source_day else []) +
            [d for d in (selection.get('source_date'), selection.get('prepared_source_date')) if d]))
        alerts = []
        bindings = []
        observations = []
        from src.engine.monitoring.policy_generation_contract import observations as generation_observations, retirement_dispositions
        details['policy_generation_retirements']=retirement_dispositions(PROJECT_ROOT)
        details['policy_generation_semantics']=[]
        for semantic_day in semantic_days:
            for observed in generation_observations(PROJECT_ROOT,semantic_day,
                    data_root=(PROJECT_ROOT/'data').resolve()):
                from src.engine.monitoring.policy_generation_code_handoff import current_fixture_observation
                observed = current_fixture_observation(observed, (PROJECT_ROOT/'data').resolve())
                details['policy_generation_semantics'].append(observed)
                observations.append(dict(stage='policy_generation',semantics=observed))
                bindings.append(dict(stage='policy_generation',source_date=semantic_day,
                    target_date=None,as_of_date=_today_kst_str(now_dt),
                    generation=observed.get('report_sha256'),status=observed['status']))
                for reason in observed['findings']:
                    alerts.append(dict(stage='policy_generation',scope=observed['family'],source_date=semantic_day,
                        target_date=None,reason=reason,severity='warning',owner=observed.get('repair_owner') or 'UNRESOLVED_CURRENT_OWNER',
                        artifact=observed['artifact'],generation=observed.get('contract_sha256'),
                        source_generation=observed.get('source_generation'),code_sha256=observed.get('code_sha256'),
                        closure_test=observed.get('closure_test'),decision_authority='report_only'))
                    warnings.append('policy_generation:'+observed['family']+':'+reason)
        details['machine_result_semantics_by_source_date'] = {}
        details['auxiliary_result_semantics_by_source_date'] = {}
        for semantic_day in semantic_days:
            machine_semantics = _machine_result_semantics(PROJECT_ROOT, semantic_day)
            details["machine_result_semantics"] = machine_semantics
            details['machine_result_semantics_by_source_date'][semantic_day] = machine_semantics
            if machine_semantics["findings"]:
                warnings.append("machine_result_semantics: " + ", ".join(machine_semantics["findings"]))
            auxiliary_semantics = _auxiliary_result_semantics(PROJECT_ROOT, semantic_day)
            details["auxiliary_result_semantics"] = auxiliary_semantics
            details['auxiliary_result_semantics_by_source_date'][semantic_day] = auxiliary_semantics
            if auxiliary_semantics["findings"]:
                warnings.append("auxiliary_result_semantics: " + ", ".join(
                    auxiliary_semantics["findings"]))
            handoff = _postclose_handoff_semantics(PROJECT_ROOT, semantic_day, now_dt)
            details["postclose_handoff_semantics"] = handoff
            if handoff["findings"]:
                warnings.append("postclose_handoff_semantics: " + ", ".join(handoff["findings"]))
            family_results = [("main_stop_confirmation", _main_stop_semantics(PROJECT_ROOT, semantic_day, now=now_dt))]
            if not trading_day or semantic_day != today:
                family_results.append(('initial_quantity', _initial_quantity_semantics(
                    PROJECT_ROOT, semantic_day, now_epoch=now_ts)))
            for name, result in family_results:
                details[name + '_semantics'] = result
                if result['findings']:
                    warnings.append(name + '_semantics: ' + ', '.join(result['findings']))
            for name, semantics in (
                (machine_semantics.get('stage_id', "legacy_machine_report"), machine_semantics),
                ("main_auxiliary_policy", auxiliary_semantics),
                ("postclose_handoff", handoff), *family_results):
                semantics.setdefault('target_date', selection['target_date'])
                semantics['due_target_date'] = selection['target_date']
                semantics['observation_date'] = _today_kst_str(now_dt)
                semantics.setdefault('bound_target_date', semantics.get('target_date'))
                semantics['next_due_target_date'] = selection['target_date']
                observations.append(dict(stage=name, semantics=semantics))
                bindings.append({'stage': name, 'source_date': semantic_day,
                    'target_date': semantics.get('target_date'), 'as_of_date': _today_kst_str(now_dt),
                    'generation': semantics.get('report_sha256'), 'status': semantics.get('status')})
                alerts.extend(_semantic_alerts(name, semantics, semantic_day))
        if selection.get('findings'):
            alerts.extend(_semantic_alerts('postclose_handoff', selection, selection.get('source_date') or today))
            bindings.append(dict(stage='postclose_handoff', source_date=selection.get('source_date') or today,
                target_date=selection['target_date'], as_of_date=_today_kst_str(now_dt),
                generation=selection.get('report_sha256'), status=selection['status']))
            warnings.append('completed_semantic_source: ' + ', '.join(selection['findings']))
        if trading_day:
            quantity_semantics = _initial_quantity_semantics(PROJECT_ROOT, today, now_epoch=now_ts)
            details["initial_quantity_semantics"] = quantity_semantics
            for name, semantics in (("holding_profit_exit", holding_semantics), ("initial_quantity", quantity_semantics)):
                observations.append(dict(stage=name, semantics=semantics))
                bindings.append(dict(stage=name, source_date=today, target_date=semantics.get("target_date"),
                    as_of_date=_today_kst_str(now_dt), generation=semantics.get("report_sha256"), status=semantics.get("status")))
                alerts.extend(_semantic_alerts(name, semantics, today))
                if semantics.get("findings"):
                    warnings.append(name + "_semantics: " + ", ".join(sorted(set(semantics["findings"]))))
        optional = _optional_weakness_semantics(PROJECT_ROOT, now_dt)
        details['main_market_weakness_research_semantics'] = optional
        observations.append(dict(stage='main_market_weakness_research', semantics=optional))
        bindings.append(dict(stage='main_market_weakness_research', source_date=optional.get('source_date'),
            target_date=None, as_of_date=_today_kst_str(now_dt), generation=optional.get('report_sha256'), status=optional['status']))
        alerts.extend(_semantic_alerts('main_market_weakness_research', optional, optional.get('source_date')))
        if optional['findings']:
            warnings.append('main_market_weakness_research: '+', '.join(optional['findings']))
        details['semantic_source_bindings'] = bindings
        details['semantic_observations'] = observations
        if cancel_wait is not None:
            alerts.extend(_semantic_alerts('entry_cancel_wait_tuning', cancel_wait, cancel_wait_day))
        details['semantic_alerts'] = alerts
        owner_day = _today_kst_str(now_dt)
        owner_context = dict(as_of_date=owner_day, owner_checklist_date=owner_day,
                             basis='current_checklist')
        try:
            current_owners, owner_context = _semantic_owner_context(
                PROJECT_ROOT, now_dt, selection, observations)
            owner_error = None
        except (OSError, ValueError, TypeError) as exc:
            current_owners, owner_error = set(), type(exc).__name__ + ':' + str(exc)
        for alert in alerts:
            eligible = (owner_context['basis'] == 'current_checklist'
                        or alert.get('source_date') == owner_context.get('source_date'))
            _project_semantic_owner(alert, current_owners if eligible else set(), owner_day)
            alert['owner_checklist_date'] = owner_context['owner_checklist_date']
            alert['owner_projection_basis'] = owner_context['basis']
        details['semantic_owner_projection'] = dict(owner_context, open_ids=sorted(current_owners), error=owner_error)
        from src.engine.monitoring.error_detector_coverage import validate_semantic_coverage
        coverage = validate_semantic_coverage(owner_day, active_alerts=alerts, owner_error=owner_error)
        details['functional_semantic_coverage'] = coverage
        for finding in coverage['findings']:
            (warnings if 'current_owner' in finding else issues).append('semantic_coverage: ' + finding)

        # Semantic/source checks above can take longer than report publication.
        # Read the observer last, then retry its exact existing contract once if
        # publication or selection changed during validation. Never replay the
        # expensive source checks or inherit a verdict from a replaced report.
        for observer_artifact in observer_registry:
            attempts = []
            for attempt in range(2):
                now_dt, now_ts = datetime.now(), time.time()
                if _today_kst_str(now_dt) != sweep_day:
                    issues.append(f'{observer_id}: observer_check_crossed_kst_date_boundary')
                    details[f'{observer_id}_status'] = 'fail'
                    break
                now_h, now_m = _kst_time_tuple(now_dt)
                now_total = 24 * 60 if past_source_day else now_h * 60 + now_m
                observer_path = PROJECT_ROOT / observer_artifact['path_template'].replace('{date}', sweep_day if past_source_day else today)
                before = _submission_observer_input_identity(observer_path, PROJECT_ROOT)
                check_registered_artifacts([observer_artifact])
                after = _submission_observer_input_identity(observer_path, PROJECT_ROOT)
                prefix = observer_id + '_'
                attempts.append(dict(
                    checked_at=now_dt.isoformat(), input_identity=before,
                    stable=before == after,
                    details={key: value for key, value in details.items() if key.startswith(prefix)},
                    issues=[value for value in issues if value.startswith(observer_id + ':')],
                    warnings=[value for value in warnings if value.startswith(observer_id + ':')]))
                if before == after:
                    break
                if attempt == 0:
                    for key in list(details):
                        if key.startswith(prefix):
                            del details[key]
                    issues[:] = [value for value in issues if not value.startswith(observer_id + ':')]
                    warnings[:] = [value for value in warnings if not value.startswith(observer_id + ':')]
                else:
                    issues.append(f'{observer_id}: observer_inputs_changed_during_final_recheck')
                    details[f'{observer_id}_status'] = 'fail'
                    details[f'{observer_id}_current_observation_verified'] = False
            details[f'{observer_id}_publication_recheck'] = dict(
                schema='submission_observer_publication_recheck_v1',
                deferred_until_semantic_checks_complete=True, attempts=attempts,
                stable=bool(attempts and attempts[-1]['stable']),
                runtime_effect=False, allowed_runtime_apply=False)

        severity, summary = self._classify(issues, warnings)
        if (severity == "warning" and not issues and len(warnings) == 1
                and details.get("submission_bottleneck_monitor_status") in {
                    "pending_first_current_observer", "pending_no_applicable_observations", "pending_bounded_observation"}):
            summary = ("Artifact observation pending: first current-generation submission monitor; prior evidence retained"
                       if details['submission_bottleneck_monitor_status'] == 'pending_first_current_observer'
                       else ('Artifact observation pending: '
                             + str((details.get('submission_bottleneck_monitor_observation_health') or {}).get('reason',
                                   'bounded_observation'))[:120]
                             + '; partial validation retained'))
        return DetectionResult(
            detector_id=self.id,
            category=self.category,
            severity=severity,
            summary=summary,
            details=details,
            recommended_action=self._recommend_action(severity, issues),
        )

    @staticmethod
    def _terminal_skip_status(aid: str, today: str) -> dict[str, str] | None:
        contract = ARTIFACT_TERMINAL_SKIP_CONTRACTS.get(aid)
        if not contract:
            return None
        log_path = PROJECT_ROOT / contract["log"]
        if not log_path.exists():
            return None
        try:
            from src.engine.log_archive_service import tail_log_lines
            lines = tail_log_lines(log_path, 5000)
        except OSError:
            return None
        step_token = f"step={contract['step']}"
        for line in reversed(lines):
            if (
                "[SKIP]" in line
                and f"target_date={today}" in line
                and step_token in line
            ):
                return {
                    "log": contract["log"],
                    "step": contract["step"],
                    "marker": line.strip(),
                }
        return None

    @staticmethod
    def _classify(issues: list[str], warnings: list[str]) -> tuple[str, str]:
        if issues:
            return "fail", f"Artifact failures: {'; '.join(issues[:5])}"
        if warnings:
            return "warning", f"Artifact warnings: {'; '.join(warnings[:5])}"
        return "pass", "All critical artifacts fresh."

    @staticmethod
    def _recommend_action(severity: str, issues: list[str]) -> str:
        if severity == "fail":
            return f"Check missing/stale artifacts: {'; '.join(issues[:3])}"
        if severity == "warning":
            return "Non-critical artifacts missing/stale. Monitor next cycle."
        return ""

    @staticmethod
    def _is_bounded_postclose_running(
        artifact: dict[str, Any], artifact_path: Path, today: str, now: datetime, *, root=None
    ) -> bool:
        # Only the postclose owner can be pending here, never a failed status,
        # a prior-day recovery, a generic live process, or an unbounded wait.
        if (
            artifact.get("id") != "threshold_postclose_status"
            or artifact.get("running_status_deadline") != (23, 20)
            or today != now.date().isoformat()
            or (now.hour, now.minute) >= (23, 20)
        ):
            return False
        try:
            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            if (
                not isinstance(payload, dict)
                or type(payload.get("schema_version")) is not int
                or payload.get("schema_version") != 1
                or payload.get("report_type") != "threshold_cycle_postclose_status"
                or payload.get("runtime_effect") is not False
                or payload.get("status") != "running"
                or payload.get("target_date") != today
                or payload.get("reason") != "started"
                or type(payload.get("exit_code")) is not int
                or payload["exit_code"] != 0
            ):
                return False
            started = datetime.fromisoformat(payload["started_at"])
            if (
                started.date().isoformat() != today
                or started.timestamp() > now.timestamp()
            ):
                return False
        except (OSError, ValueError, TypeError, KeyError):
            return False
        config = artifact.get("suppress_missing_while_cron_in_progress")
        if not isinstance(config, dict) or not config.get("log"):
            return False
        # A live PID alone must not hide a newer FAIL/DONE or another date.
        markers = CronCompletionDetector._read_once_markers(
            (root or PROJECT_ROOT) / config["log"], today
        )
        if not (
            ("[START]" in markers.upper() or "[BEGIN]" in markers.upper())
            and CronCompletionDetector._last_terminal_marker(markers) == "none"
        ):
            return False
        return ArtifactFreshnessDetector._has_matching_live_process(
            config, target_date=today
        )

    @staticmethod
    def _is_upstream_cron_in_progress(config: Any, today: str) -> bool:
        if not isinstance(config, dict):
            return False
        if ArtifactFreshnessDetector._has_matching_live_process(config):
            return True
        log_value = str(config.get("log") or "").strip()
        if not log_value:
            return False
        log_path = PROJECT_ROOT / log_value
        if not log_path.exists():
            return False
        # Reuse the cron owner's exact-date, latest-run and rotated-log
        # contract. Verbose JSON must not evict START; prior-day recovery DONE
        # or an older failed attempt must not terminate the current run.
        markers = CronCompletionDetector._read_once_markers(log_path, today)
        has_start = "[START]" in markers.upper() or "[BEGIN]" in markers.upper()
        return (
            has_start
            and CronCompletionDetector._last_terminal_marker(markers) == "none"
        )

    @staticmethod
    def _has_matching_live_process(
        config: dict[str, Any], *, target_date: str | None = None
    ) -> bool:
        patterns_raw = config.get("process_patterns")
        if not isinstance(patterns_raw, list):
            return False
        patterns = [
            str(pattern).strip() for pattern in patterns_raw if str(pattern).strip()
        ]
        if not patterns:
            return False
        proc_root = Path("/proc")
        try:
            proc_entries = list(proc_root.iterdir())
        except OSError:
            return False
        current_pid = os.getpid()
        for entry in proc_entries:
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
            except ValueError:
                continue
            if pid == current_pid:
                continue
            try:
                raw_cmdline = (entry / "cmdline").read_bytes()
            except OSError:
                continue
            if target_date is not None:
                argv = raw_cmdline.decode("utf-8", errors="replace").split("\x00")
                for index, arg in enumerate(argv[:-1]):
                    name = Path(arg).name
                    is_wrapper = name == "run_threshold_cycle_postclose.sh" or (
                        name.startswith(".run_threshold_cycle_postclose.snapshot.")
                        and name.endswith(".sh")
                    )
                    if is_wrapper and argv[index + 1] == target_date:
                        return True
                continue
            cmdline = raw_cmdline.replace(b"\x00", b" ").decode(
                "utf-8", errors="replace"
            )
            if cmdline and any(pattern in cmdline for pattern in patterns):
                return True
        return False

    @staticmethod
    def _validate_partitioned_compact(
        artifact: dict[str, Any],
        today: str,
        details: dict[str, Any],
    ) -> tuple[str, str] | None:
        config = artifact.get("partitioned_compact")
        if not isinstance(config, dict):
            return None

        aid = str(artifact["id"])
        checkpoint_template = str(config.get("checkpoint_template") or "").strip()
        partition_glob_template = str(
            config.get("partition_glob_template") or ""
        ).strip()
        if not checkpoint_template or not partition_glob_template:
            return "warning", f"{aid}: partitioned compact detector config incomplete"

        checkpoint_path = PROJECT_ROOT / checkpoint_template.replace("{date}", today)
        partition_glob = partition_glob_template.replace("{date}", today)
        if Path(partition_glob).is_absolute():
            partition_paths = sorted(Path(path) for path in glob.glob(partition_glob))
        else:
            partition_paths = sorted(PROJECT_ROOT.glob(partition_glob))
        partition_paths = [
            path
            for path in partition_paths
            if path.name.endswith((".jsonl", ".jsonl.gz"))
        ]

        details[f"{aid}_legacy_path_missing"] = True
        details[f"{aid}_partitioned_checkpoint_path"] = str(checkpoint_path)
        details[f"{aid}_partitioned_part_count"] = len(partition_paths)

        if not checkpoint_path.exists():
            return "warning", f"{aid}: partitioned checkpoint missing"
        if not partition_paths:
            return "warning", f"{aid}: partitioned compact parts missing"

        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        except Exception as exc:
            details[f"{aid}_partitioned_checkpoint_status"] = "invalid_json"
            return "warning", f"{aid}: invalid partitioned checkpoint ({exc})"

        completed = bool(checkpoint.get("completed"))
        status = str(checkpoint.get("status") or checkpoint.get("state") or "").strip()
        paused_reason = checkpoint.get("paused_reason")
        written_count = checkpoint.get("written_count", checkpoint.get("written_total"))

        details[f"{aid}_partitioned_checkpoint_status"] = status or "unknown"
        details[f"{aid}_partitioned_completed"] = completed
        details[f"{aid}_partitioned_written_count"] = written_count
        if paused_reason:
            details[f"{aid}_partitioned_paused_reason"] = paused_reason

        if not completed:
            reason = f" paused_reason={paused_reason}" if paused_reason else ""
            return (
                "warning",
                f"{aid}: partitioned compact checkpoint incomplete{reason}",
            )

        latest_mtime = max(path.stat().st_mtime for path in partition_paths)
        details[f"{aid}_age_sec"] = round(time.time() - latest_mtime, 1)
        return "pass_partitioned_checkpoint", ""

    @staticmethod
    def _validate_json_status(
        artifact: dict[str, Any],
        artifact_path: Path,
        details: dict[str, Any],
        *, observer_snapshot=None,
    ) -> str:
        status_field = artifact.get("json_status_field")
        if not status_field:
            return ""

        aid = artifact["id"]
        ok_values = {str(v) for v in artifact.get("json_ok_values", [])}
        try:
            if aid == 'submission_bottleneck_monitor':
                snapshot = observer_snapshot or _submission_observer_snapshot(artifact_path)
                payload, report_sha, signature = snapshot
                if _observer_file_signature(artifact_path.lstat()) != signature:
                    raise ValueError('observer_report_changed_after_snapshot')
            else:
                payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        except Exception as exc:
            details[f"{aid}_content_status"] = "invalid_json"
            return f"{aid}: invalid status JSON ({exc})"

        if aid == 'submission_bottleneck_monitor' and isinstance(payload, dict) and (
                'execution_status' in payload or str(payload.get('date') or '') >= '2026-10-14'):
            dimensions = details.setdefault(f'{aid}_observation_dimensions',
                _submission_observer_dimensions(payload, artifact_path, report_sha))
            details[f'{aid}_execution_status'] = payload.get('execution_status')
            details[f'{aid}_semantic_status'] = payload.get('semantic_status')
            details[f'{aid}_run_id'] = payload.get('run_id')
            generation_issue = _submission_observer_generation_issue(payload, PROJECT_ROOT)
            dimensions['generation'] = dict(status=generation_issue or 'current',
                current_generation_verified=generation_issue is None)
            if generation_issue is None and payload.get('observer_generation') is None:
                dimensions['generation'] = dict(status='legacy_generation_unverified', current_generation_verified=False)
            try:
                report_unchanged = _observer_file_signature(artifact_path.lstat()) == signature
            except OSError:
                report_unchanged = False
            if not report_unchanged:
                dimensions['generation'] = dict(status='observer_report_changed_after_snapshot', current_generation_verified=False)
                return f'{aid}: observer_report_changed_after_snapshot'
            if generation_issue:
                details[f'{aid}_observer_generation_issue'] = generation_issue
                return f'{aid}: {generation_issue}'
            if (not re.fullmatch('[0-9a-f]{32}', str(payload.get('run_id', '')))
                    or payload.get('execution_status') != 'completed'
                    or payload.get('semantic_status') not in {'validated', 'partial'}):
                return f'{aid}: observer execution incomplete or invalid'
            if payload.get('semantic_status') == 'partial':
                # This pure projection never grants full validation. Recompute
                # from the exact report. A current report can retain its
                # close-time empty observation only with the native terminal.
                freshness = dimensions.get('freshness') or {}
                closed = bool(dimensions.get('closed_window'))
                if not closed and freshness.get('status') == 'fresh' and (freshness.get('body_clock') or {}).get('status') != 'fresh':
                    return f'{aid}: observer_report_body_clock_not_current'
                if (dimensions['generation'].get('current_generation_verified') is True
                        and (closed or freshness.get('status') == 'fresh'
                        and 0 <= freshness.get('age_sec', -1) <= freshness.get('max_staleness_sec', -1))):
                    from src.engine.monitoring.submission_bottleneck_monitor import observation_health_projection
                    assessment = observation_health_projection(payload)
                    details[f'{aid}_observation_health'] = assessment
                    dimensions['observation_health'] = assessment
                    declared = payload.get('observation_health')
                    matches = isinstance(declared, dict) and declared == assessment
                    details[f'{aid}_observation_health_projection_match'] = matches
                    if declared is not None and not matches:
                        return f'{aid}: observer_observation_health_projection_mismatch'
                    if assessment.get('status') == 'warning_pending' and not matches:
                        return f'{aid}: observer_observation_health_projection_missing'
                    if assessment.get('status') == 'warning_pending' and matches:
                        actor_issue = _submission_observer_actor_issue(payload)
                        if not actor_issue:
                            try:
                                _, selection_sha = _observer_small_object(
                                    Path(PROJECT_ROOT) / 'data/runtime/runtime_release_selection.json',
                                    limit=1024 * 1024, hash_only=True)
                                if selection_sha != payload['observer_generation']['final_selection_sha256']:
                                    actor_issue = 'observer_generation_changed_after_assessment'
                                elif _observer_file_signature(artifact_path.lstat()) != signature:
                                    actor_issue = 'observer_report_changed_after_snapshot'
                            except (OSError, ValueError, TypeError, KeyError):
                                actor_issue = 'observer_assessment_snapshot_unavailable'
                        dimensions['current_main_actor'] = dict(status=actor_issue or 'verified')
                        if actor_issue:
                            details[f'{aid}_observation_health_projection_match'] = False
                            return f'{aid}: {actor_issue}'
                return (f'{aid}: observer semantic coverage partial; publication is not full validation; '
                        + _submission_observer_partial_reason(dimensions))

        current: Any = payload
        for part in str(status_field).split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                details[f"{aid}_content_status"] = "missing_status_field"
                return f"{aid}: missing JSON status field {status_field}"

        status_value = str(current)
        details[f"{aid}_content_status"] = status_value
        if (
            aid == "update_kospi_status"
            and status_value == "completed_with_warnings"
            and _reconcile_update_kospi_master_difference(payload, details)
        ):
            return ""
        if ok_values and status_value not in ok_values:
            return f"{aid}: JSON status is {status_value}"
        return ""

    @staticmethod
    def _validate_json_artifact(artifact_path: Path) -> str:
        if artifact_path.suffix != ".json":
            return ""
        try:
            json.loads(artifact_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return str(exc)
        return ""

    @staticmethod
    def _validate_content_freshness(
        artifact: dict[str, Any],
        artifact_path: Path,
        details: dict[str, Any],
        now_dt: datetime,
    ) -> tuple[str, bool]:
        config = artifact.get("content_freshness")
        if not isinstance(config, dict):
            return "", False

        aid = artifact["id"]
        data_format = str(config.get("format") or "").strip().lower()
        try:
            payload = ArtifactFreshnessDetector._load_content_payload(
                data_format, artifact_path
            )
        except Exception as exc:
            details[f"{aid}_content_status"] = "invalid_content"
            return f"{aid}: invalid content freshness payload ({exc})", False

        min_rows = config.get("min_rows")
        if (
            min_rows is not None
            and isinstance(payload, list)
            and len(payload) < int(min_rows)
        ):
            details[f"{aid}_content_status"] = "insufficient_rows"
            details[f"{aid}_content_rows"] = len(payload)
            return f"{aid}: insufficient rows ({len(payload)} < {int(min_rows)})", False
        if isinstance(payload, list):
            details[f"{aid}_content_rows"] = len(payload)

        min_count_field = str(config.get("min_count_field") or "").strip()
        if min_count_field:
            count_value = ArtifactFreshnessDetector._resolve_field(
                payload, min_count_field
            )
            try:
                count_int = int(count_value)
            except (TypeError, ValueError):
                details[f"{aid}_content_status"] = "invalid_count"
                return f"{aid}: invalid count field {min_count_field}", False
            details[f"{aid}_{min_count_field}"] = count_int
            min_count = int(config.get("min_count") or 0)
            if count_int < min_count:
                details[f"{aid}_content_status"] = "insufficient_count"
                return (
                    f"{aid}: insufficient {min_count_field} ({count_int} < {min_count})",
                    False,
                )

        date_field = str(config.get("date_field") or "").strip()
        if not date_field:
            details[f"{aid}_content_status"] = "pass"
            return "", True
        raw_date = ArtifactFreshnessDetector._resolve_field(payload, date_field)
        content_date = ArtifactFreshnessDetector._parse_date_value(raw_date)
        if content_date is None:
            details[f"{aid}_content_status"] = "invalid_date"
            return f"{aid}: invalid content date field {date_field}", False

        age_days = (now_dt.date() - content_date.date()).days
        max_age_days = int(config.get("max_age_days") or 0)
        details[f"{aid}_content_date"] = content_date.date().isoformat()
        details[f"{aid}_content_age_days"] = age_days
        if age_days < 0:
            details[f"{aid}_content_status"] = "future_date"
            return (
                f"{aid}: content date is in the future ({content_date.date().isoformat()})",
                False,
            )
        if max_age_days >= 0 and age_days > max_age_days:
            details[f"{aid}_content_status"] = "stale_date"
            return f"{aid}: content date stale ({age_days}d > {max_age_days}d)", False

        details[f"{aid}_content_status"] = "pass"
        return "", True

    @staticmethod
    def _load_content_payload(data_format: str, artifact_path: Path) -> Any:
        if data_format == "json":
            return json.loads(artifact_path.read_text(encoding="utf-8"))
        if data_format == "csv":
            with artifact_path.open("r", encoding="utf-8-sig", newline="") as handle:
                return list(csv.DictReader(handle))
        raise ValueError(f"unsupported content freshness format: {data_format}")

    @staticmethod
    def _resolve_field(payload: Any, field_path: str) -> Any:
        current = payload[0] if isinstance(payload, list) and payload else payload
        for part in field_path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    @staticmethod
    def _parse_date_value(value: Any) -> datetime | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if " " in text and "T" not in text:
            text = text.split(" ", 1)[0]
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            pass
        for fmt in ("%Y%m%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None


def _kst_time_tuple(now_kst: datetime | None = None) -> tuple[int, int]:
    now_kst = now_kst or datetime.now()
    return now_kst.hour, now_kst.minute
