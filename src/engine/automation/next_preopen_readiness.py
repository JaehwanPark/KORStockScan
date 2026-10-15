"""Prepare and verify the next trading day's isolated PREOPEN bootstrap.

The prepared files are never sourced by the bot. The exact-date PREOPEN owner
still activates dated policies and writes the live bootstrap on the target day.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import fcntl
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.engine.automation import runtime_policy_bootstrap as bootstrap
from src.engine.automation.auxiliary_reader_readiness import verify_auxiliary_reader, verify_bound_sources
from src.engine.automation.postclose_done_controller import done_terminal_receipt_issues
from src.engine.infrastructure.runtime_release_router import selected_release
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = ZoneInfo("Asia/Seoul")
PREPARED_DIR = DATA_DIR / "runtime" / "policy_bootstrap" / "prepared"
PREOPEN_START = time(7, 35)
RECOVERY_AUTHORITY = 'APPROVED_FAILED_PREOPEN_POLICY_PRESERVING_RECOVERY'
_RECOVERY = ContextVar('failed_preopen_recovery', default=None)


def stopped_postclose_candidate_rebind(
    source_date: str, target_date: str, *, publication_date: str,
    expected_bundle_sha256: str, expected_candidate_sha256: str,
    expected_current_pointer_sha256: str, expected_selection_sha256: str,
    origin_root: Path, activation_parent_origin_root: Path,
    activation_parent_origin_commit: str, release_commit: str,
    reason: str, confirm: str,
) -> dict:
    """Rebind an unchanged policy after midnight while Main remains stopped.

    This owns release, PREOPEN, producer and publisher locks. Callers must not
    hold those locks themselves. The normal policy publisher's future-only
    and failed-PREOPEN contracts remain unchanged; no clock override is exposed.
    """
    from src.engine.infrastructure import runtime_release_router as router
    from src.engine.automation import ordered_intraday_deploy as ordered
    from src.engine.automation.postclose_summary_handoff import (
        active_stage_names, stage_path, stage_receipt_issues,
    )
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    from src.engine.scalping import continuous_reversal_policy_v6 as policy

    def require(ok, detail):
        if not ok:
            raise ValueError('stopped_postclose_rebind_' + detail)

    def clock():
        current = datetime.now(KST)
        require(current.tzinfo is not None
                and target_date == current.astimezone(KST).date().isoformat()
                and is_krx_trading_day(current.date())
                and current.time().replace(tzinfo=None) < PREOPEN_START,
                'window_closed')
        return current

    def read(path):
        path = Path(path)
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_size <= 16 * 1024 * 1024,
                'regular_bounded_receipt_required')
        identity = lambda value: (value.st_dev, value.st_ino, value.st_size,
                                  value.st_mtime_ns, value.st_ctime_ns)
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
            require(identity(os.fstat(stream.fileno())) == identity(before), 'receipt_changed')
            raw = stream.read(16 * 1024 * 1024 + 1)
            require(identity(os.fstat(stream.fileno())) == identity(before), 'receipt_changed')
        after = path.lstat()
        require(stat.S_ISREG(after.st_mode) and identity(after) == identity(before)
                and len(raw) == before.st_size, 'receipt_changed')
        value = json.loads(raw)
        require(isinstance(value, dict), 'receipt_object_required')
        return value, raw

    require(confirm == policy.CODE_REFRESH_AUTHORITY and bool(str(reason).strip()), 'authority_required')
    for value in (expected_bundle_sha256, expected_candidate_sha256,
                  expected_current_pointer_sha256, expected_selection_sha256):
        require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'digest_invalid')
    for value in (release_commit, activation_parent_origin_commit):
        require(isinstance(value, str) and re.fullmatch('[0-9a-f]{40}', value), 'commit_invalid')
    require(date.fromisoformat(source_date).isoformat() == source_date
            and publication_date == source_date
            and source_date < target_date
            and _next_trading_day(date.fromisoformat(source_date)).isoformat() == target_date,
            'source_session_mismatch')
    clock()
    data = DATA_DIR.resolve()
    workspace = data.parent
    root = native.root(data)
    candidate_path = root / 'candidates' / f'policy_{target_date}.json'
    pointer_path = root / 'current.json'
    selection_path = data / 'runtime/runtime_release_selection.json'
    controller_path = data / 'report/postclose_done_controller' / f'postclose_done_controller_{source_date}.json'
    isolation_path = workspace / 'tmp/postclose_bot_isolation.json'
    hold_path = data / 'runtime/operator_startup_hold.json'
    stages = active_stage_names(source_date)
    frozen = {}
    held_locks = []

    def lock_identity(path):
        value = path.lstat()
        require(stat.S_ISREG(value.st_mode), 'lock_not_regular')
        return value.st_dev, value.st_ino

    def verify_locks():
        for path, identity, handle in held_locks:
            require(lock_identity(path) == identity, 'lock_replaced')
            if handle is not None:
                value = os.fstat(handle.fileno())
                require((value.st_dev, value.st_ino) == identity, 'lock_replaced')

    def bind(path, *, expected=None, optional=False):
        path = Path(path)
        if optional and not path.exists() and not path.is_symlink():
            require(path not in frozen or frozen[path] is None, 'absent_custody_changed')
            frozen[path] = None
            return None
        value, raw = read(path)
        require(expected is None or hashlib.sha256(raw).hexdigest() == expected, 'generation_changed')
        require(path not in frozen or frozen[path] == raw, 'frozen_receipt_changed')
        frozen[path] = raw
        return value

    def guard():
        clock()
        verify_locks()
        selected, commit = router.selected_release(workspace)
        require(selected == Path(__file__).resolve().parents[3]
                and selected == Path.cwd().resolve() and commit == release_commit,
                'selected_release_changed')
        selection = bind(selection_path, expected=expected_selection_sha256)
        require(selection.get('approved_by') == 'user'
                and selection.get('approval_scope') == 'after_postclose_deploy_for_next_regular_start'
                and selection.get('actual_pid_consumed') is False
                and not selection.get('deployment_transition') and not selection.get('actual_pid_receipt'),
                'stopped_selection_required')
        require(not ordered._main_pids() and ordered._session_absent(), 'main_or_supervisor_running')
        restart = workspace / 'restart.flag'
        bootstrap_dir = data / 'runtime/policy_bootstrap'
        live_bootstrap = (bootstrap_dir / f'runtime_policy_bootstrap_{target_date}.env',
                          bootstrap_dir / f'runtime_policy_bootstrap_{target_date}.json',
                          bootstrap_dir / f'runtime_policy_bootstrap_verify_{target_date}.json')
        require(not restart.exists() and not restart.is_symlink()
                and all(not path.exists() and not path.is_symlink() for path in live_bootstrap),
                'startup_or_live_env_present')
        for path in live_bootstrap:
            require(bind(path, optional=True) is None, 'live_bootstrap_artifact_present')
        status_path = data / 'report/threshold_cycle_preopen_status' / f'threshold_cycle_preopen_{target_date}.status.json'
        require(not status_path.exists() and not status_path.is_symlink(), 'preopen_already_attempted')
        isolation = bind(isolation_path)
        require(isolation.get('target_date') == source_date and isolation.get('active') is True
                and isolation.get('action') == 'stop' and isolation.get('session') == 'bot', 'isolation_invalid')
        bind(hold_path, optional=True)
        pointer = bind(pointer_path, expected=expected_current_pointer_sha256)
        require(pointer.get('effective_date') == source_date, 'parent_already_activated_or_wrong_session')
        candidate = bind(candidate_path, expected=expected_candidate_sha256)
        native.validate(candidate, target_date=target_date)
        family = candidate.get('continuous_reversal') or {}
        require(candidate.get('bundle_sha256') == expected_bundle_sha256
                and family.get('schema') == policy.SCHEMA
                and family.get('source_date') == source_date
                and family.get('publication_date') == publication_date
                and family.get('effective_date') == target_date
                and family.get('effective_mode') == 'next_session'
                and family.get('parent_bundle_sha256') == pointer.get('bundle_sha256')
                and family.get('release_commit') != release_commit, 'candidate_contract_invalid')
        controller = bind(controller_path)
        require(not done_terminal_receipt_issues(controller_path, source_date, started_after_ns=0),
                'whole_source_not_closed')
        strict = Path(str(controller.get('verification_attempt_path') or ''))
        bind(strict, expected=controller.get('verification_attempt_sha256'))
        for stage in stages:
            bind(stage_path(data / 'report', source_date, stage))
            require(not stage_receipt_issues(data / 'report', source_date, stage), 'producer_not_closed:' + stage)
        for path, raw in frozen.items():
            if raw is None:
                require(not path.exists() and not path.is_symlink(), 'absent_custody_changed')
            else:
                require(read(path)[1] == raw, 'frozen_receipt_changed')
        clock()
        return candidate, pointer

    release_lock_path = data / 'runtime' / router.RELEASE_SET_LOCK
    # A stopped managed release has already used this native lock. Requiring
    # its existing inode also binds the router's non-yielded descriptor.
    release_lock_before = lock_identity(release_lock_path)
    with router.runtime_release_set_lock(workspace), ExitStack() as locks:
        release_lock_after = lock_identity(release_lock_path)
        require(release_lock_before == release_lock_after, 'lock_replaced')
        held_locks.append((release_lock_path, release_lock_after, None))
        for path in (workspace / 'logs/runtime_policy_preopen.lock',
                     *(stage_path(data / 'report', source_date, stage).with_suffix('.lock') for stage in sorted(stages)),
                     root / 'publisher.lock'):
            require(path.parent.resolve() == path.parent, 'lock_parent_not_canonical')
            before = lock_identity(path) if path.exists() or path.is_symlink() else None
            lock = locks.enter_context(os.fdopen(os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o666), 'a'))
            opened = os.fstat(lock.fileno())
            require(stat.S_ISREG(opened.st_mode), 'lock_not_regular')
            identity = opened.st_dev, opened.st_ino
            require((before is None or before == identity) and lock_identity(path) == identity, 'lock_replaced')
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held_locks.append((path, identity, lock))
            verify_locks()
        original, pointer = guard()
        origin = Path(origin_root).resolve()
        original_commit = original['continuous_reversal']['release_commit']
        require(router.validate_release(workspace, dict(schema='runtime_release_selection_v1',
                    workspace=str(workspace), release_root=str(origin), git_commit=original_commit))
                == (origin, original_commit), 'original_release_unattested')
        native._validate_bundle_sources(original, data, historical_code_root=origin_root)
        parent = policy._attested_activation_parent(data, target_date,
            origin_root=activation_parent_origin_root, origin_commit=activation_parent_origin_commit)
        require(parent is not None and parent['bundle_sha256'] == pointer['bundle_sha256'], 'parent_changed')
        generation = root / 'generations' / (expected_bundle_sha256 + '.json')
        require(bind(generation) == original, 'original_generation_missing')
        guard()
        proof = dict(schema='main_identical_policy_code_refresh_v1', authority=confirm,
            source_bundle_sha256=expected_bundle_sha256, origin_root=str(Path(origin_root).resolve()),
            activation_parent_origin_root=str(Path(activation_parent_origin_root).resolve()),
            activation_parent_origin_commit=activation_parent_origin_commit,
            reason=reason, policy_reselected=False, provider_called=False,
            stopped_postclose_preparation=dict(source_date=source_date, publication_date=publication_date,
                target_date=target_date, verified_at_kst=clock().isoformat(),
                source_sha256={str(path): hashlib.sha256(raw).hexdigest() if raw is not None else None
                               for path, raw in frozen.items()}))
        successor = policy._write_refreshed_bundle(original, data, release_commit=release_commit, proof=proof)
        require(policy._behavioral_family(original['continuous_reversal'])
                == policy._behavioral_family(successor['continuous_reversal']), 'policy_changed')
        policy._validate_code_refresh(successor, data)
        guard()
        native._atomic_write_json(candidate_path, successor)
        try:
            require(read(candidate_path)[0] == successor, 'publication_readback_changed')
            for path, raw in frozen.items():
                if path == candidate_path:
                    continue
                require((not path.exists() and not path.is_symlink()) if raw is None else read(path)[1] == raw,
                        'publication_source_changed')
            verify_locks()
            clock()
        except (OSError, ValueError) as exc:
            # The candidate CAS has committed. Preserve that generation and
            # report partial completion explicitly; never restore stale bytes.
            raise ValueError('stopped_postclose_rebind_candidate_published_postcheck_failed:'
                             + successor['bundle_sha256'] + ':' + str(exc)) from exc
        return successor


@contextmanager
def failed_preopen_recovery(target_date, *, confirm, now=None):
    """Lease an unactivated failed PREOPEN; never fabricate its completion."""
    current = (now or datetime.now(KST)).astimezone(KST)
    if (confirm != RECOVERY_AUTHORITY or target_date != current.date().isoformat()
            or not is_krx_trading_day(current.date())
            or not PREOPEN_START <= current.time().replace(tzinfo=None) < time(8, 40)):
        raise ValueError('failed_preopen_recovery_window_or_authority_invalid')
    data = DATA_DIR.resolve()
    with (data.parent / 'logs/runtime_policy_preopen.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        path = data / 'report/threshold_cycle_preopen_status' / f'threshold_cycle_preopen_{target_date}.status.json'
        status = _read(path)
        updated = datetime.fromisoformat(status.get('updated_at', ''))
        if (status.get('status') != 'failed' or status.get('target_date') != target_date
                or not isinstance(status.get('exit_code'), int) or status['exit_code'] == 0
                or updated.tzinfo is None or updated.astimezone(KST).date() != current.date()
                or updated > current or status.get('runtime_env_exists') is not False
                or (data / 'runtime/policy_bootstrap' / f'runtime_policy_bootstrap_{target_date}.env').exists()):
            raise ValueError('failed_preopen_recovery_not_unactivated_failure')
        from src.engine.scalping import mechanistic_entry_runtime_policy as native
        active = _read(native.root(data) / 'current.json')
        if active.get('effective_date', '') >= target_date:
            raise ValueError('failed_preopen_recovery_policy_already_activated')
        for proc in Path('/proc').iterdir():
            if not proc.name.isdecimal():
                continue
            try:
                argv = (proc / 'cmdline').read_bytes().split(b'\0')
            except FileNotFoundError:
                continue
            if any(arg.endswith(b'bot_main.py') for arg in argv):
                raise ValueError('failed_preopen_recovery_main_running')
        receipt = dict(data_root=str(data), target_date=target_date,
                       status_path=str(path), status_sha256=_sha(path))
        token = _RECOVERY.set(receipt)
        try:
            yield receipt
        finally:
            _RECOVERY.reset(token)


def require_failed_preopen_recovery(data_root, target_date, *, now=None):
    receipt = _RECOVERY.get()
    current = (now or datetime.now(KST)).astimezone(KST)
    if (not receipt or receipt['data_root'] != str(Path(data_root).resolve())
            or receipt['target_date'] != target_date or target_date != current.date().isoformat()
            or current.time().replace(tzinfo=None) >= time(8, 40)
            or _sha(Path(receipt['status_path'])) != receipt['status_sha256']):
        raise ValueError('failed_preopen_recovery_lease_invalid')
    return receipt


def _activation_candidate_receipt(target_date, commit, *, generation_only=False):
    from src.engine.scalping import mechanistic_entry_runtime_policy as native
    path = native.preparation_path(DATA_DIR, target_date)
    if not path.is_file():
        return None
    bundle = native._read(path)
    family = bundle.get('continuous_reversal') or {}
    if family.get('schema') != 'continuous_reversal_policy_v6':
        return None
    if family.get('release_commit') != commit:
        raise ValueError('prepared_activation_release_mismatch')
    native.validate(bundle, target_date=target_date)
    if not generation_only:
        native._validate_bundle_sources(bundle, DATA_DIR)
    return dict(path=str(path), sha256=_sha(path), bundle_sha256=bundle['bundle_sha256'],
                release_commit=commit)


def _next_trading_day(day: date) -> date:
    for offset in range(1, 15):
        candidate = day + timedelta(days=offset)
        if is_krx_trading_day(candidate):
            return candidate
    raise ValueError("next_krx_trading_day_unresolved")


def target_after_postclose(source_date: str, *, now: datetime | None = None) -> str:
    source = date.fromisoformat(source_date)
    current = (now or datetime.now(KST)).astimezone(KST)
    if source > current.date():
        raise ValueError("future_postclose_source_date")
    first = _next_trading_day(source)
    if current.date() < first:
        return first.isoformat()
    # Late closure/release preparation retains today's still-unopened session,
    # even when the sealed source predates the immediately preceding day.
    if current.time() < PREOPEN_START and is_krx_trading_day(current.date()):
        return current.date().isoformat()
    return _next_trading_day(current.date()).isoformat()


def finalization_preparation_disposition(
    source_date: str, effective_date: str, *, recovery: bool = False,
    now: datetime | None = None,
) -> str:
    """A historical finalizer closes its source, never rolls it into a new day."""
    source = date.fromisoformat(source_date)
    effective = date.fromisoformat(effective_date)
    current = (now or datetime.now(KST)).astimezone(KST)
    if (source.isoformat() != source_date or effective.isoformat() != effective_date
            or source > current.date() or _next_trading_day(source) != effective):
        raise ValueError("preopen_source_session_mismatch")
    if (current.date() > effective
            or (current.date() == effective and current.time() >= PREOPEN_START)):
        if recovery:
            return "historical_recovery_no_prepare"
        raise ValueError("preopen_source_session_already_opened")
    return "prepare_exact_effective_date"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"object_required:{path}")
    return value


def _selected_release(*, require_selected_cwd: bool = True) -> tuple[dict[str, Any], Path, str]:
    path = DATA_DIR / "runtime" / "runtime_release_selection.json"
    selection = _read(path)
    release, commit = selected_release(DATA_DIR.parent)
    if (selection.get("git_commit") != commit
            or (require_selected_cwd and release != Path.cwd().resolve())):
        raise ValueError("selected_release_identity_mismatch")
    return selection, path, commit


def _source_receipts(source_date: str, target_date: str, *, generation_only: bool = False, checklist_snapshot: Path | None = None) -> dict[str, Any]:
    controller_path = (DATA_DIR / "report" / "postclose_done_controller"
                       / f"postclose_done_controller_{source_date}.json")
    if checklist_snapshot is not None and not generation_only:
        raise ValueError("historical_checklist_requires_sealed_generation")
    issues = done_terminal_receipt_issues(controller_path, source_date, started_after_ns=0,
                                        **({"generation_only": True} if generation_only else {}),
                                        **({"checklist_snapshot": checklist_snapshot} if checklist_snapshot is not None else {}))
    if issues:
        raise ValueError("postclose_controller_not_closed:" + ",".join(issues))
    summary_path = (DATA_DIR / "report" / "runtime_approval_summary"
                    / f"runtime_approval_summary_{source_date}.json")
    summary = _read(summary_path)
    if summary.get("date") != source_date:
        raise ValueError("postclose_summary_date_mismatch")
    policy_receipts = []
    for family in ("main_mechanistic_entry", "compact_auxiliary"):
        row = (summary.get("sources") or {}).get(family) or {}
        receipt = row.get("policy_receipt") or {}
        path = Path(str(receipt.get("path") or ""))
        from src.engine.scalping.mechanistic_entry_runtime_policy import preparation_path
        if (receipt.get("valid") is not True
                or receipt.get("target_date_matches") is not True
                or path != preparation_path(DATA_DIR,target_date)
                or not path.is_file() or _sha(path) != receipt.get("sha256")):
            raise ValueError(f"{family}_target_policy_receipt_invalid")
        policy_receipts.append({"family": family, "path": str(path), "sha256": receipt["sha256"]})
    return {
        "controller_path": str(controller_path), "controller_sha256": _sha(controller_path),
        "summary_path": str(summary_path), "summary_sha256": _sha(summary_path),
        "policy_receipts": policy_receipts,
    }


def _generation_dir(source_date: str, target_date: str, controller_sha: str, commit: str) -> Path:
    return (PREPARED_DIR / target_date
            / f"{source_date}_{controller_sha[:16]}_{commit[:16]}")


def prepare(source_date: str, *, target_date: str | None = None,
            now: datetime | None = None, recover_failed_preopen: bool = False) -> dict[str, Any]:
    expected = target_after_postclose(source_date, now=now)
    if recover_failed_preopen:
        require_failed_preopen_recovery(DATA_DIR, target_date, now=now)
        if _next_trading_day(date.fromisoformat(source_date)).isoformat() != target_date:
            raise ValueError('failed_preopen_recovery_source_target_invalid')
        expected = target_date
    target_date = target_date or expected
    if target_date != expected:
        raise ValueError("preopen_target_not_next_operating_day")
    _, selection_path, commit = _selected_release()
    activation_candidate = _activation_candidate_receipt(target_date, commit)
    auxiliary_reader = verify_auxiliary_reader(target_date, data_root=DATA_DIR, preparation=True)
    source = _source_receipts(source_date, target_date)
    output_dir = _generation_dir(source_date, target_date, source["controller_sha256"], commit)
    manifest = bootstrap.write_bootstrap(target_date, output_dir=output_dir)
    verification = bootstrap.verify_bootstrap(target_date, output_dir=output_dir)
    if (verification.get("status") != "pass"
            or manifest.get("selected_release_sha") != commit
            or manifest.get("source_incumbent_target_date", "") >= target_date):
        raise ValueError("prepared_bootstrap_verification_failed:" + ",".join(verification.get("findings") or []))
    manifest_file = bootstrap.manifest_path(target_date, output_dir=output_dir)
    env_file = bootstrap.env_path(target_date, output_dir=output_dir)
    verify_file = bootstrap.verify_path(target_date, output_dir=output_dir)
    receipt = {
        "schema": "next_preopen_readiness_v1",
        "status": "prepared_verified",
        "source_date": source_date,
        "target_date": target_date,
        "prepared_at_kst": (now or datetime.now(KST)).astimezone(KST).isoformat(),
        "selected_release_commit": commit,
        "selection_path": str(selection_path),
        "selection_sha256": _sha(selection_path),
        **source,
        "manifest_path": str(manifest_file), "manifest_file_sha256": _sha(manifest_file),
        "manifest_content_sha256": manifest["manifest_sha256"],
        "env_path": str(env_file), "env_sha256": _sha(env_file),
        "verification_path": str(verify_file), "verification_sha256": _sha(verify_file),
        "actual_pid_consumed": False,
        "runtime_effect": False,
        "day_of_activation_required": True,
        "activation_candidate": activation_candidate,
        "auxiliary_reader_readiness": auxiliary_reader,
    }
    receipt_file = output_dir / "readiness.json"
    if auxiliary_reader is not None:
        verify_bound_sources(auxiliary_reader)
    bootstrap._publish(receipt_file, json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    index = {
        "schema": "next_preopen_readiness_index_v1",
        "target_date": target_date,
        "receipt_path": str(receipt_file),
        "receipt_sha256": _sha(receipt_file),
    }
    bootstrap._publish(PREPARED_DIR / target_date / "latest.json",
                       json.dumps(index, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
    return receipt


def verify_prepared(target_date: str, *, require_today: bool = False,
                    now: datetime | None = None, generation_only: bool = False) -> dict[str, Any]:
    findings = []
    handoff_basis = ""
    current = (now or datetime.now(KST)).astimezone(KST)
    if require_today and target_date != current.date().isoformat():
        findings.append("preopen_target_not_today")
    try:
        index = _read(PREPARED_DIR / target_date / "latest.json")
        receipt_path = Path(str(index["receipt_path"]))
        if (receipt_path.resolve().parent.parent != (PREPARED_DIR / target_date).resolve()
                or _sha(receipt_path) != index["receipt_sha256"]):
            raise ValueError("prepared_receipt_path_or_hash_invalid")
        receipt = _read(receipt_path)
        if (index.get("target_date") != target_date
                or receipt.get("schema") != "next_preopen_readiness_v1"
                or receipt.get("status") != "prepared_verified"
                or receipt.get("target_date") != target_date
                or receipt.get("actual_pid_consumed") is not False
                or receipt.get("runtime_effect") is not False):
            raise ValueError("prepared_receipt_contract_invalid")
        # Read-only monitor consumers run from Main src/ or a report release.
        # Router identity/shared mounts and exact source hashes remain required;
        # only prepare() admits mutation from the selected release root.
        _, selection_path, commit = _selected_release(require_selected_cwd=False)
        release_changed = (receipt["selected_release_commit"] != commit
                           or receipt["selection_sha256"] != _sha(selection_path))
        expected_source = receipt
        if release_changed:
            from src.engine.automation.intraday_release_handoff import verify as verify_intraday
            handoff = verify_intraday(target_date, commit, now=now)
            preserved = handoff.get("handoff") or {}
            if (handoff["status"] != "pass" or preserved.get("prepared_receipt_path") != str(receipt_path)
                    or preserved.get("prepared_receipt_sha256") != _sha(receipt_path)):
                raise ValueError("prepared_source_or_release_changed")
            handoff_basis = "intraday_preserved_preopen_generation"
            reseal = preserved.get('postclose_source_reseal')
            if reseal is not None:
                expected_source = reseal['current_source_receipts']
                handoff_basis = 'intraday_preserved_preopen_generation_current_postclose_resealed'
        snapshot = ((preserved.get('postclose_source_reseal') or {}).get('historical_checklist')
                    if release_changed else None)
        source = _source_receipts(receipt["source_date"], target_date,
            **({"generation_only": True} if generation_only or snapshot else {}),
            **({"checklist_snapshot": Path(snapshot['path'])} if snapshot else {}))
        if any(expected_source.get(key) != value for key, value in source.items()):
            raise ValueError("prepared_source_or_release_changed")
        if not release_changed and 'activation_candidate' in receipt:
            if receipt['activation_candidate'] != _activation_candidate_receipt(
                    target_date, commit, generation_only=generation_only):
                raise ValueError('prepared_activation_candidate_changed')
        output_dir = receipt_path.parent
        auxiliary_reader = receipt.get('auxiliary_reader_readiness')
        if auxiliary_reader is not None:
            if auxiliary_reader.get('target_date') != target_date:
                raise ValueError('prepared_auxiliary_reader_target_mismatch')
            verify_bound_sources(auxiliary_reader)
        if not generation_only:
            verify_auxiliary_reader(target_date, data_root=DATA_DIR, preparation=not release_changed)
        for key, path in (
            ("manifest_file_sha256", bootstrap.manifest_path(target_date, output_dir=output_dir)),
            ("env_sha256", bootstrap.env_path(target_date, output_dir=output_dir)),
            ("verification_sha256", bootstrap.verify_path(target_date, output_dir=output_dir)),
        ):
            if receipt.get(key) != _sha(path):
                raise ValueError(f"prepared_{key}_changed")
        if generation_only:
            # Reuse the sealed full PASS; no policy/economics re-evaluation.
            manifest = _read(bootstrap.manifest_path(target_date, output_dir=output_dir))
            check = _read(bootstrap.verify_path(target_date, output_dir=output_dir))
            errors = bootstrap.bootstrap_source_receipt_issues(manifest, max_source_bytes=64 * 1024 * 1024)
            quantity = manifest.get("initial_quantity_policy_receipt")
            if quantity:
                current_path = Path(quantity["current_file"])
                if _sha(current_path) != quantity["current_file_sha256"]:
                    errors.append("prepared_initial_quantity_generation_changed")
                else:
                    current_quantity = _read(current_path)
                    for key in ("policy_file", "stage_file", "parent_policy_file", "parent_current_file"):
                        if current_quantity.get(key) and (Path(current_quantity[key]).stat().st_size > 64 * 1024 * 1024
                                or _sha(Path(current_quantity[key])) != current_quantity[key + "_sha256"]):
                            errors.append("prepared_initial_quantity_source_changed")
            elif bootstrap.INITIAL_QUANTITY_CURRENT.exists():
                errors.append("prepared_initial_quantity_generation_changed")
            if (manifest.get("target_date") != target_date
                or check.get("target_date") != target_date
                or manifest.get("manifest_sha256") != receipt["manifest_content_sha256"]
                or check.get("findings") or errors):
                raise ValueError("prepared_sealed_generation_changed:" + ",".join(errors))
        else:
            check = bootstrap.verify_bootstrap(target_date, output_dir=output_dir, write=False)
        if (check.get("status") != "pass"
                or check.get("manifest_sha256") != receipt["manifest_content_sha256"]):
            raise ValueError("prepared_bootstrap_changed:" + ",".join(check.get("findings") or []))
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        findings.append(str(exc))
        receipt = {}
    return {
        "schema": "next_preopen_readiness_verification_v1",
        "target_date": target_date,
        "status": "pass" if not findings else "fail",
        "findings": findings,
        "source_date": receipt.get("source_date"),
        "selected_release_commit": commit if handoff_basis and not findings else receipt.get("selected_release_commit"),
        "preserved_preopen_commit": receipt.get("selected_release_commit") if handoff_basis else None,
        "handoff_basis": handoff_basis,
        "actual_pid_consumed": False,
        "runtime_effect": False,
        "validation_scope": ("intraday_preserved_historical_generation" if handoff_basis and not findings
                             else "sealed_generation" if generation_only else "current_full_contract"),
    }


def verify_preopen_completion(
    target_date: str, selected_release_commit: str, *, now: datetime | None = None,
) -> dict[str, Any]:
    path = (DATA_DIR / "report" / "threshold_cycle_preopen_status"
            / f"threshold_cycle_preopen_{target_date}.status.json")
    findings = []
    current = (now or datetime.now(KST)).astimezone(KST)
    try:
        receipt = _read(path)
        updated = datetime.fromisoformat(str(receipt.get("updated_at") or ""))
        if (receipt.get("target_date") != target_date
                or receipt.get("status") != "succeeded"
                or receipt.get("exit_code") != 0
                or receipt.get("runtime_env_exists") is not True
                or updated.tzinfo is None
                or updated.astimezone(KST).date().isoformat() != target_date
                or current.date().isoformat() != target_date):
            findings.append("exact_preopen_status_not_succeeded_on_selected_release")
        elif receipt.get("selected_release_commit") != selected_release_commit:
            from src.engine.automation.intraday_release_handoff import verify as verify_intraday
            return verify_intraday(target_date, selected_release_commit, now=now)
    except (OSError, ValueError, TypeError):
        findings.append("exact_preopen_status_missing_or_invalid")
    return {"status": "pass" if not findings else "fail", "target_date": target_date,
            "findings": findings, "actual_pid_consumed": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--verify", action="store_true")
    group.add_argument("--verify-completion", action="store_true")
    parser.add_argument("--source-date")
    parser.add_argument("--target-date")
    parser.add_argument("--require-today", action="store_true")
    parser.add_argument("--selected-release-commit")
    args = parser.parse_args(argv)
    if args.prepare and not args.source_date:
        parser.error("--prepare requires --source-date")
    if (args.verify or args.verify_completion) and not args.target_date:
        parser.error("verification requires --target-date")
    if args.verify_completion and not args.selected_release_commit:
        parser.error("--verify-completion requires --selected-release-commit")
    try:
        if args.prepare:
            from src.engine.infrastructure.validation_digest_session import postclose_session
            with postclose_session(DATA_DIR, args.source_date) as session:
                result = prepare(args.source_date, target_date=args.target_date)
            result = {**result, 'validation_io': session.stats}
        else:
            result = (verify_prepared(args.target_date, require_today=args.require_today)
                      if args.verify else verify_preopen_completion(
                          args.target_date, args.selected_release_commit))
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        result = {"status": "fail", "reason": str(exc), "actual_pid_consumed": False}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] in {"prepared_verified", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
