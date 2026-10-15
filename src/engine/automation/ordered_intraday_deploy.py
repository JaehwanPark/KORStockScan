"""Authorized Main deployment: drain, select, prepare, then start and attest.

Startup automation owns this transition. It never changes trading policies,
forces process termination, resets monitor cursors or regenerates postclose work.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
import shlex
import stat
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from src.engine.automation import intraday_release_handoff as H
from src.engine.infrastructure import runtime_release_router as R

CONFIRM = 'APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART'


@contextmanager
def detector_transition_lock(workspace, timeout=60):
    """Drain the existing detector before any deployment mutation.

    Share the wrapper's inode, including publication/notification time. Never
    unlink it; release automatically on success, timeout or failed deployment.
    Python descriptors are non-inheritable so a launched Main cannot keep it.
    """
    path = Path(workspace) / 'tmp/run_error_detection.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as lock:
        def acquire():
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return False
            return True
        _wait(acquire, timeout, 'deployment_error_detector_drain_timeout')
        yield


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _metadata_signature(path):
    info = Path(path).lstat()
    return tuple(getattr(info, "st_" + name) for name in (
        "dev", "ino", "mode", "nlink", "uid", "gid", "size", "mtime_ns", "ctime_ns"))


def _owned_metadata(path):
    """Reuse the startup owner's bounded, strict, no-follow regular reader."""
    value, raw = R._startup_receipt(Path(path))
    return value, raw, _metadata_signature(path)



@contextmanager
def _existing_selector_lock(path):
    """Open the existing writer lock without following links or blocking on FIFO."""
    before = _metadata_signature(path)
    if not stat.S_ISREG(before[2]):
        raise ValueError("deployment_selector_lock_regular_file_required")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    try:
        info = os.fstat(fd)
        opened = tuple(getattr(info, "st_" + name) for name in (
            "dev", "ino", "mode", "nlink", "uid", "gid", "size", "mtime_ns", "ctime_ns"))
        if not stat.S_ISREG(info.st_mode) or opened != before:
            raise ValueError("deployment_selector_lock_changed")
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
        if _metadata_signature(path) != opened:
            raise ValueError("deployment_selector_lock_changed")
    finally:
        os.close(fd)

def _atomic(path, raw, *, expected=None):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(name, path.stat().st_mode & 0o777 if path.exists() else 0o644)
        if expected is not None:
            _, current, signature = _owned_metadata(path)
            if current != expected["raw"] or signature != expected["signature"]:
                raise ValueError("deployment_failed_hold_compare_exchange_changed")
        os.replace(name, path)
        directory = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        Path(name).unlink(missing_ok=True)


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def _predecessor_observer(workspace, day):
    """Freeze a small, exact old observation; never grant validation or trading authority."""
    path = (Path(workspace) / 'data/report/buy_funnel_sentinel'
            / ('submission_bottleneck_monitor_' + day + '.json')).absolute()
    try:
        expected_parent = ((Path(workspace) / 'data').resolve()
                           / 'report/buy_funnel_sentinel')
        if path.is_symlink() or path.parent.resolve() != expected_parent:
            raise ValueError('observer_symlink')
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > 8 * 1024 * 1024:
            raise ValueError('observer_size_limit')
        descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        with os.fdopen(descriptor, 'rb') as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise ValueError('observer_not_regular')
            raw = handle.read(8 * 1024 * 1024 + 1)
        after = path.stat()
        signature = lambda item: (item.st_dev, item.st_ino, item.st_mtime_ns, item.st_ctime_ns, item.st_size)
        if (len(raw) > 8 * 1024 * 1024 or signature(before) != signature(opened)
                or signature(opened) != signature(after)):
            raise ValueError('observer_changed_during_capture')
        def unique_object(pairs):
            result = {}
            for key, item in pairs:
                if key in result:
                    raise ValueError('observer_duplicate_key')
                result[key] = item
            return result
        def invalid_constant(_):
            raise ValueError('observer_non_finite')
        value = json.loads(raw, object_pairs_hook=unique_object, parse_constant=invalid_constant)
        # parse_constant does not see an overflowing JSON exponent (1e999).
        json.dumps(value, allow_nan=False)
        stamp = datetime.fromisoformat(value['as_of'])
        if (value.get('schema') != 'submission_bottleneck_monitor_v1'
                or value.get('date') != day
                or not isinstance(value.get('run_id'), str)
                or not re.fullmatch(r'[0-9a-f]{32}', value['run_id'])
                or value.get('execution_status') != 'completed'
                or value.get('semantic_status') not in {'partial', 'validated'}
                or stamp.tzinfo is None or stamp.astimezone(H.KST).date().isoformat() != day
                or stamp > datetime.now(H.KST)):
            raise ValueError('observer_identity_invalid')
        return dict(schema='startup_observer_predecessor_v1', status='captured',
                    path=str(path), sha256=_digest(raw), mtime_ns=after.st_mtime_ns,
                    **{key:value[key] for key in ('date', 'as_of', 'run_id',
                                                  'execution_status', 'semantic_status')})
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return dict(schema='startup_observer_predecessor_v1', status='unavailable',
                    path=str(path), reason=type(exc).__name__)


def _main_pids():
    result = subprocess.run(['pgrep', '-f', '[/]python bot_main[.]py$'], capture_output=True, text=True)
    if result.returncode not in (0, 1):
        raise ValueError('deployment_process_inventory_failed')
    return [int(value) for value in result.stdout.split()]


def _session_absent():
    result = subprocess.run(['tmux', 'has-session', '-t', '=bot'], capture_output=True)
    if result.returncode not in (0, 1):
        raise ValueError('deployment_supervisor_inventory_failed')
    return result.returncode == 1


def _launch(plan):
    for attempt in range(3):
        if _main_pids() or not _session_absent():
            raise ValueError('deployment_supervisor_or_main_appeared')
        result = subprocess.run(plan['command'], cwd=plan['cwd'], capture_output=True, timeout=15)
        if result.returncode == 0:
            return
        if attempt == 2:
            raise ValueError('deployment_supervisor_launch_failed')
        # The tmux server can outlive the drained final session briefly.
        time.sleep(1)


def _wait(predicate, timeout, reason):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() >= deadline:
            raise ValueError(reason)
        time.sleep(0.25)


def execute(driver):
    """Order is deliberate: no selection or shared document write before drain."""
    try:
        driver.preflight()
        driver.acquire_hold()
        driver.drain()
        driver.publish()
        driver.prepare()
        driver.start()
        return driver.attest()
    except BaseException as exc:
        driver.fail(exc)
        raise


class Deployment:
    def __init__(self, workspace, candidate, day, confirm, *, adopt_failed_hold=False):
        if confirm != CONFIRM:
            raise ValueError('ordered_deployment_explicit_approval_required')
        H._today(day, None)
        self.workspace = Path(workspace).resolve(strict=True)
        self.candidate = Path(candidate).resolve(strict=True)
        self.day = day
        self.selection = self.workspace / 'data/runtime/runtime_release_selection.json'
        self.hold = self.workspace / 'data/runtime/operator_startup_hold.json'
        self.flag = self.workspace / 'restart.flag'
        self.phase = 'new'
        self.hold_bytes = None
        self.validation_session = uuid.uuid4().hex
        # Explicit embedding-only recovery; the ordinary CLI never adopts holds.
        if type(adopt_failed_hold) is not bool:
            raise ValueError("deployment_failed_hold_adoption_flag_invalid")
        self.adopt_failed_hold = adopt_failed_hold
        self.failed_hold_adoption = None
        self._preflight_native_verified = False
        self.preserve_editable_checklist = True

    def run_json(self, root, module, *args, timeout=120):
        # Predecessors may predate this opt-in CLI. Their native full path stays.
        if root == self.candidate and module in {
                'src.engine.automation.intraday_release_handoff',
                'src.engine.automation.runtime_policy_bootstrap'}:
            args = (*args, '--validation-session', self.validation_session)
        result = subprocess.run([str(root / '.venv/bin/python'), '-B', '-m', module, *args],
            cwd=root, env={**os.environ, 'PYTHONPATH': str(root)}, capture_output=True, text=True, timeout=timeout)
        if hasattr(self, 'directory'):
            name = self.phase + '-' + module.rsplit('.', 1)[-1] + '.log'
            _atomic(self.directory / name, (result.stdout + result.stderr).encode())
        if result.returncode:
            raise ValueError('deployment_validation_failed:' + module)
        value = json.loads(result.stdout)
        if value.get('status') != 'pass':
            raise ValueError('deployment_validation_not_pass:' + module)
        return value

    def checkpoint(self, phase, **values):
        self.phase = phase
        self.state.update(phase=phase, updated_at=datetime.now(H.KST).isoformat(), **values)
        _atomic(self.directory / 'status.json', _json_bytes(self.state))

    def preflight(self):
        self.before = self.selection.read_bytes()
        self.old = json.loads(self.before)
        self.previous, self.previous_commit = R.selected_release(self.workspace)
        commit = R.git(self.candidate, 'rev-parse', 'HEAD')
        self.candidate, self.commit = R.validate_release(self.workspace, {
            'schema': 'runtime_release_selection_v1', 'workspace': str(self.workspace),
            'release_root': str(self.candidate), 'git_commit': commit})
        if Path(__file__).resolve().parents[3] != self.candidate:
            raise ValueError('deployment_must_execute_reviewed_candidate_code')
        if self.candidate == self.previous:
            raise ValueError('deployment_candidate_already_selected')
        for name in ('operator_startup_hold.json',):
            p = self.workspace / 'data/runtime' / name
            if p.exists() or p.is_symlink():
                if not getattr(self, "adopt_failed_hold", False):
                    raise ValueError('deployment_existing_operator_hold')
            elif getattr(self, "adopt_failed_hold", False):
                raise ValueError("deployment_failed_hold_required")
        if self.flag.exists() or self.flag.is_symlink():
            raise ValueError('deployment_existing_restart_request')
        receipt = self.old.get('actual_pid_receipt') or {}
        self.identity = H._identity(receipt.get('pid'))
        if (self.old.get('actual_pid_consumed') is not True
                or self.identity['cwd'] != str(self.previous / 'src')
                or _main_pids() != [self.identity['pid']]):
            raise ValueError('deployment_predecessor_not_current_singleton')
        parent = Path('/proc', str(self.identity['pid']), 'stat').read_text().rsplit(')', 1)[1].split()[1]
        self.launcher = int(parent)
        self.launcher_stat = Path('/proc', parent, 'stat').read_text().rsplit(')', 1)[1].split()[19]
        if str(self.previous / 'src/run_bot.sh').encode() not in Path('/proc', parent, 'cmdline').read_bytes().split(b'\0'):
            raise ValueError('deployment_predecessor_supervisor_unrecognized')
        self.directory = self.workspace / 'data/runtime/release_transitions' / self.day / self.commit
        self.directory.mkdir(parents=True, exist_ok=False)
        self.state = dict(schema='ordered_intraday_deployment_v1', authority=CONFIRM,
            target_date=self.day, previous_root=str(self.previous), previous_commit=self.previous_commit,
            candidate_root=str(self.candidate), candidate_commit=self.commit,
            predecessor_identity=self.identity, runtime_effect='authorized_code_restart_only',
            predecessor_launcher=dict(pid=self.launcher, start_ticks=self.launcher_stat),
            policy_effect='unchanged', original_selection_sha256=_digest(self.before))
        _atomic(self.directory / 'selection-before.json', self.before)
        self.checkpoint('preflight')
        try:
            check = self.run_json(self.previous, 'src.engine.automation.intraday_release_handoff',
                                  '--verify', '--target-date', self.day, '--pid', str(self.identity['pid']))
            self.run_json(self.previous, 'src.engine.automation.runtime_policy_bootstrap',
                          '--verify', '--target-date', self.day, '--pid', str(self.identity['pid']))
        except ValueError:
            if not getattr(self, 'preserve_editable_checklist', False):
                raise
            for module in ('intraday_release_handoff', 'runtime_policy_bootstrap'):
                log = self.directory/('preflight-'+module+'.log')
                if log.exists(): log.rename(log.with_name('preflight-previous-'+module+'.log'))
            # A repaired reader must revalidate the entire live predecessor;
            # the old failure is retained and never converted to a receipt.
            check = self.run_json(self.candidate, 'src.engine.automation.intraday_release_handoff',
                '--verify-predecessor', '--target-date', self.day, '--pid', str(self.identity['pid']))
            if (check.get('status') != 'pass'
                    or check.get('schema') != 'intraday_pid_consumption_verification_v1'
                    or check.get('target_date') != self.day or not check.get('manifest_sha256')
                    or check.get('verification_code_commit') != self.commit
                    or check.get('verification_code_root') != str(self.candidate)
                    or check.get('selected_release_commit') != self.previous_commit
                    or check.get('release_root') != str(self.previous)
                    or check.get('pid_identity') != self.identity
                    or check.get('actual_pid_consumed') is not True
                    or check.get('candidate_pid_consumed') is not False
                    or check.get('runtime_effect') is not False):
                raise ValueError('deployment_predecessor_revalidation_unbound')
            self.state['predecessor_revalidation'] = check
        if check.get('basis') == 'native_preopen':
            self.seal_native_predecessor(check)
        else:
            path, _ = H._paths(self.day, self.previous_commit)
            self.frozen = H._read(path)['frozen_files']
        code_check = H.verify_candidate_delay_code(self.day, self.candidate, self.commit)
        _atomic(self.directory / 'candidate-delay-code.json', _json_bytes(code_check))
        stop_check = H.verify_candidate_stop_code(self.day, self.candidate, self.commit)
        _atomic(self.directory / 'candidate-stop-code.json', _json_bytes(stop_check))
        holding_check = H.verify_candidate_holding_vote_code(self.day, self.candidate, self.commit)
        _atomic(self.directory / 'candidate-holding-vote-code.json', _json_bytes(holding_check))
        self.checklist = self.workspace / 'docs/checklists' / (self.day + '-stage2-todo-checklist.md')
        self.document_before = self.checklist.read_bytes()
        self.document_after = subprocess.check_output(['git', '-C', str(self.candidate), 'show',
            self.commit + ':docs/checklists/' + self.checklist.name], timeout=10)
        if getattr(self, 'preserve_editable_checklist', False):
            self.state['candidate_checklist_sha256'] = _digest(self.document_after)
            self.document_after = self.document_before
            # Policy/source receipts remain frozen. The live PID proof above
            # independently validated its consumed historical document.
            self.frozen = dict(self.frozen)
            self.frozen.pop(str(self.checklist), None)
        _atomic(self.directory / 'checklist-before.md', self.document_before)
        self.assert_unchanged()
        self._preflight_native_verified = True
        if getattr(self, "adopt_failed_hold", False):
            # All native predecessor, policy/code and source checks above stay
            # mandatory. No shared hold bytes change during this inspection.
            self.capture_failed_hold_adoption()
            self.assert_unchanged()

    def capture_failed_hold_adoption(self):
        if (getattr(self, "adopt_failed_hold", False) is not True
                or getattr(self, "_preflight_native_verified", False) is not True):
            raise ValueError("deployment_failed_hold_native_preflight_required")
        hold, raw, signature = _owned_metadata(self.hold)
        expected_transition = (self.workspace / "data/runtime/release_transitions" / self.day
                               / self.previous_commit / "status.json")
        selected_transition = self.old.get("deployment_transition")
        if (selected_transition != str(expected_transition)
                or hold.get("schema") != "ordered_deployment_startup_hold_v1"
                or hold.get("authority") != CONFIRM or hold.get("target_date") != self.day
                or hold.get("candidate_commit") != self.previous_commit
                or hold.get("transition") != str(expected_transition)):
            raise ValueError("deployment_failed_hold_identity_invalid")
        if expected_transition.resolve(strict=True) != expected_transition:
            raise ValueError("deployment_failed_transition_path_invalid")
        failed, failed_raw, failed_signature = _owned_metadata(expected_transition)
        old_identity = hold.get("old_pid_identity")
        if (failed.get("schema") != "ordered_intraday_deployment_v1"
                or failed.get("authority") != CONFIRM or failed.get("target_date") != self.day
                or failed.get("candidate_commit") != self.previous_commit
                or failed.get("candidate_root") != str(self.previous)
                or failed.get("policy_effect") != "unchanged"
                or failed.get("status") != "fail" or failed.get("phase") != "failed"
                or failed.get("failed_phase") != "starting"
                or failed.get("error") != "deployment_pid_attestation_timeout"
                or not isinstance(old_identity, dict)
                or old_identity != failed.get("predecessor_identity")
                or type(old_identity.get("pid")) is not int or old_identity["pid"] <= 0
                or not isinstance(old_identity.get("start_ticks"), str)
                or not old_identity["start_ticks"].isdigit()
                or not isinstance(old_identity.get("cwd"), str) or not Path(old_identity["cwd"]).is_absolute()):
            raise ValueError("deployment_failed_transition_not_adoptable")
        prior_path = expected_transition.with_name("selection-before.json")
        prior, prior_raw, prior_signature = _owned_metadata(prior_path)
        if (prior.get("schema") != "runtime_release_selection_v1"
                or prior.get("actual_pid_consumed") is not True
                or failed.get("original_selection_sha256") != _digest(prior_raw)
                or prior.get("git_commit") != failed.get("previous_commit")
                or prior.get("release_root") != failed.get("previous_root")
                or old_identity.get("cwd") != str(Path(prior["release_root"]) / "src")
                or (prior.get("actual_pid_receipt") or {}).get("pid") != old_identity["pid"]
                or self.old.get("previous_selection_backup") != str(prior_path)
                or self.old.get("previous_git_commit") != prior.get("git_commit")
                or self.old.get("previous_release_root") != prior.get("release_root")):
            raise ValueError("deployment_failed_transition_source_invalid")
        if (self.old.get("schema") != "runtime_release_selection_v1"
                or self.old.get("actual_pid_consumed") is not True
                or self.old.get("git_commit") != self.previous_commit
                or self.old.get("release_root") != str(self.previous)
                or (self.old.get("actual_pid_receipt") or {}).get("pid") != self.identity["pid"]
                or H._identity(self.identity["pid"]) != self.identity
                or _main_pids() != [self.identity["pid"]]):
            raise ValueError("deployment_failed_hold_current_pid_unverified")
        self.failed_hold_adoption = dict(raw=raw, signature=signature,
            transition_path=str(expected_transition), transition_raw=failed_raw,
            transition_signature=failed_signature, prior_path=str(prior_path),
            prior_raw=prior_raw, prior_signature=prior_signature)
        proof = dict(schema="ordered_failed_startup_hold_adoption_v1", authority=CONFIRM,
            target_date=self.day, previous_commit=self.previous_commit,
            candidate_commit=self.commit, previous_hold_path=str(self.hold),
            previous_hold_sha256=_digest(raw), failed_transition_path=str(expected_transition),
            failed_transition_sha256=_digest(failed_raw),
            failed_original_selection_path=str(prior_path), failed_original_selection_sha256=_digest(prior_raw),
            source_failure="deployment_pid_attestation_timeout", previous_hold_identity=old_identity,
            verified_current_pid_identity=self.identity, original_selection_sha256=_digest(self.before),
            transfer_status="verified_not_transferred", runtime_effect="authorized_code_restart_only",
            policy_effect="unchanged")
        _atomic(self.directory / "failed-startup-hold-before.json", raw)
        _atomic(self.directory / "failed-transition-before.json", failed_raw)
        _atomic(self.directory / "failed-original-selection-before.json", prior_raw)
        self.checkpoint("preflight", failed_hold_adoption=proof)

    def _assert_failed_transition_unchanged(self):
        adoption = getattr(self, "failed_hold_adoption", None)
        if adoption is None: return
        _, raw, signature = _owned_metadata(adoption["transition_path"])
        if raw != adoption["transition_raw"] or signature != adoption["transition_signature"]:
            raise ValueError("deployment_failed_transition_changed")
        _, raw, signature = _owned_metadata(adoption["prior_path"])
        if raw != adoption["prior_raw"] or signature != adoption["prior_signature"]:
            raise ValueError("deployment_failed_transition_source_changed")

    def seal_native_predecessor(self, check):
        """Capture verified LIVE native consumption before requesting drain."""
        if (check.get('schema') != 'intraday_pid_consumption_verification_v1'
                or check.get('status') != 'pass' or check.get('basis') != 'native_preopen'
                or check.get('actual_pid_consumed') is not True
                or check.get('target_date') != self.day
                or check.get('selected_release_commit') != self.previous_commit
                or check.get('release_root') != str(self.previous)
                or check.get('pid_identity') != self.identity
                or not check.get('manifest_sha256')):
            raise ValueError('deployment_native_predecessor_unverified')
        index = H.DATA_DIR / 'runtime/policy_bootstrap/prepared' / self.day / 'latest.json'
        ref = H._read(index)
        receipt = Path(ref['receipt_path'])
        if receipt.resolve().parent.parent != index.parent.resolve() or H._sha(receipt) != ref['receipt_sha256']:
            raise ValueError('deployment_native_prepared_generation_invalid')
        paths = [H.bootstrap.env_path(self.day), H.bootstrap.manifest_path(self.day),
                 H._preopen_path(self.day), index, receipt]
        self.frozen = {str(p): H._sha(p) for p in paths}
        self.assert_unchanged()
        if H._identity(self.identity['pid']) != self.identity:
            raise ValueError('deployment_native_predecessor_changed')
        # PREOPEN can generate today's checklist after this release's Git
        # commit. Preserve its strict-bound bytes before document publication.
        checklist_snapshot = H.preserve_checklist(self.day)
        self.native_path = self.directory / 'native-predecessor.json'
        _atomic(self.native_path, _json_bytes(dict(
            schema='native_preopen_predecessor_v1', authority=CONFIRM,
            candidate_commit=self.commit, verification=check, frozen_files=self.frozen,
            original_checklist_snapshot=checklist_snapshot,
            prepared_receipt_path=str(receipt), prepared_receipt_sha256=ref['receipt_sha256'],
            selection_before_sha256=_digest(self.before))))
        self.native_sha = H._sha(self.native_path)
        self.frozen[str(self.native_path)] = self.native_sha

    def assert_unchanged(self):
        self._assert_failed_transition_unchanged()
        if self.selection.read_bytes() != self.before:
            raise ValueError('deployment_selection_changed')
        if any(H._sha(path) != sha for path, sha in self.frozen.items()):
            raise ValueError('deployment_predecessor_generation_changed')

    def acquire_hold(self):
        self.assert_unchanged()
        self.hold_bytes = _json_bytes(dict(schema='ordered_deployment_startup_hold_v1',
            authority=CONFIRM, transition=str(self.directory / 'status.json'),
            target_date=self.day, candidate_commit=self.commit, old_pid_identity=self.identity))
        adoption = getattr(self, "failed_hold_adoption", None)
        if getattr(self, "adopt_failed_hold", False) and (
                adoption is None or getattr(self, "_preflight_native_verified", False) is not True):
            raise ValueError("deployment_failed_hold_adoption_unverified")
        if adoption is None:
            with self.hold.open('xb') as out:
                out.write(self.hold_bytes)
                out.flush()
                os.fsync(out.fileno())
        else:
            # Existing release-set serialization remains required by execute's
            # caller. The same selector lock also excludes native PID writers.
            with _existing_selector_lock(self.workspace / "data/runtime/runtime_release_selection.lock"):
                self.assert_unchanged()
                try:
                    _atomic(self.hold, self.hold_bytes, expected=adoption)
                except BaseException:
                    # A directory fsync can fail after rename. Preserve the
                    # actually observed owner in failure evidence; never roll
                    # back over a hold another operator may have published.
                    transfer = "transfer_outcome_unobservable"
                    try:
                        _, observed, _ = _owned_metadata(self.hold)
                        transfer = ("transferred_but_publication_failed" if observed == self.hold_bytes
                                    else "not_transferred" if observed == adoption["raw"]
                                    else "hold_ownership_changed")
                    except (OSError, ValueError, TypeError, KeyError):
                        pass
                    self.state["failed_hold_adoption"]["transfer_status"] = transfer
                    raise
            self.state["failed_hold_adoption"]["transfer_status"] = "transferred_exact_owned_hold"
        self.checkpoint('startup_held')

    def assert_hold(self):
        if self.hold.is_symlink() or self.hold.read_bytes() != self.hold_bytes:
            raise ValueError('deployment_hold_ownership_changed')

    def drain(self):
        self.assert_hold()
        if H._identity(self.identity['pid']) != self.identity:
            raise ValueError('deployment_predecessor_identity_changed')
        if Path('/proc', str(self.launcher), 'stat').read_text().rsplit(')', 1)[1].split()[19] != self.launcher_stat:
            raise ValueError('deployment_supervisor_identity_changed')
        self.assert_unchanged()
        with self.flag.open('x') as out:
            out.write('source=ordered_intraday_deploy old_pid=' + str(self.identity['pid']) + '\n')
            out.flush()
            os.fsync(out.fileno())
        self.checkpoint('draining')
        _wait(lambda: not Path('/proc', str(self.identity['pid'])).exists(), 90,
              'deployment_graceful_stop_timeout')
        _wait(lambda: not Path('/proc', str(self.launcher)).exists() and _session_absent(), 20,
              'deployment_supervisor_stop_timeout')
        if _main_pids() or self.flag.exists():
            raise ValueError('deployment_drain_not_complete')
        self.checkpoint('drained', drained_at=datetime.now(H.KST).isoformat())

    def publish(self):
        self.assert_hold()
        self.assert_unchanged()
        if self.phase != 'drained' or _main_pids():
            raise ValueError('deployment_publish_requires_drained_main')
        predecessor_observer = _predecessor_observer(self.workspace, self.day)
        value = dict(self.old)
        value.pop('actual_pid_receipt', None)
        value.update(release_root=str(self.candidate), git_commit=self.commit,
            source_commit=self.previous_commit,
            previous_release_root=str(self.previous), previous_git_commit=self.previous_commit,
            previous_selection_backup=str(self.directory / 'selection-before.json'),
            preserved_main_pid_receipt=self.old['actual_pid_receipt'],
            selected_at_kst=datetime.now(H.KST).isoformat(), approved_by='user',
            approval_scope='ordered_intraday_deploy_and_restart', actual_pid_consumed=False,
            actual_pid_consumption_status='drained_awaiting_verified_start',
            deployment_transition=str(self.directory / 'status.json'))
        value.pop('source_validation', None)
        if hasattr(self, 'native_path'):
            value.update(native_predecessor_path=str(self.native_path),
                         native_predecessor_sha256=self.native_sha)
        else:
            value.pop('native_predecessor_path', None)
            value.pop('native_predecessor_sha256', None)
        self.published = _json_bytes(value)
        with (self.workspace / 'data/runtime/runtime_release_selection.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assert_unchanged()
            _atomic(self.selection, self.published)
            if getattr(self, 'preserve_editable_checklist', False):
                self.document_after = self.checklist.read_bytes()
            else:
                _atomic(self.checklist, self.document_after)
        self.checkpoint('selected', selected_at=value['selected_at_kst'],
                        checklist_sha256=_digest(self.document_after),
                        predecessor_observer=predecessor_observer)

    def prepare(self):
        self.assert_hold()
        self.run_json(self.candidate, 'src.engine.automation.intraday_release_handoff', '--prepare',
            '--target-date', self.day, '--old-pid', str(self.identity['pid']),
            '--previous-root', str(self.previous), '--previous-stopped', '--reseal-postclose-source',
            '--freeze-operating-checklist', '--confirm', H.CONFIRM)
        self.run_json(self.candidate, 'src.engine.automation.runtime_policy_bootstrap',
                      '--verify', '--target-date', self.day)
        self.run_json(self.candidate, 'src.engine.automation.auxiliary_reader_readiness',
                      '--target-date', self.day)
        self.checkpoint('prepared')

    def start(self):
        self.assert_hold()
        if self.phase != 'prepared' or self.selection.read_bytes() != self.published or _main_pids():
            raise ValueError('deployment_start_generation_changed')
        # The native router rejects every startup hold, including ours. The
        # release-set lock still serializes launch; execute() restores this
        # exact owned hold on any planning/launch failure before attestation.
        self.hold.unlink()
        plan = R.make_plan(self.workspace, self.candidate, self.commit, 'start', self.day)
        child = shlex.split(plan['command'][-1])
        if child[0] != '/usr/bin/env':
            raise ValueError('deployment_launcher_environment_contract_changed')
        child.insert(1, 'KORSTOCKSCAN_VALIDATION_SESSION_ID=' + self.validation_session)
        plan['command'][-1] = shlex.join(child)
        _launch(plan)
        self.checkpoint('starting')

    def attest(self):
        def consumed():
            value = H._read(self.selection)
            if value.get('git_commit') != self.commit:
                raise ValueError('deployment_selection_changed_during_start')
            return value.get('actual_pid_consumed') is True
        _wait(consumed, R.STARTUP_CONSUMPTION_TIMEOUT_SEC, 'deployment_pid_attestation_timeout')
        value = H._read(self.selection)
        identity = H._identity(value['actual_pid_receipt']['pid'])
        if identity['cwd'] != str(self.candidate / 'src') or _main_pids() != [identity['pid']]:
            raise ValueError('deployment_successor_identity_invalid')
        self.run_json(self.candidate, 'src.engine.automation.runtime_policy_bootstrap', '--verify',
                      '--target-date', self.day, '--pid', str(identity['pid']))
        self.run_json(self.candidate, 'src.engine.automation.intraday_release_handoff',
                      '--verify', '--target-date', self.day, '--pid', str(identity['pid']))
        if (H._identity(identity['pid']) != identity or _main_pids() != [identity['pid']]
                or H._read(self.selection) != value):
            raise ValueError('deployment_successor_changed_during_attestation')
        if any(H._sha(path) != sha for path, sha in self.frozen.items() if path != str(self.checklist)):
            raise ValueError('deployment_original_policy_generation_changed')
        self.checkpoint('complete', successor_identity=identity, status='pass')
        return self.state

    def fail(self, exc):
        # Never switch back while a new Main may exist, erase another operator's
        # hold, or force-stop a child. Preserve the exact phase for recovery.
        if not hasattr(self, 'state'):
            return
        if self.phase in {'prepared', 'starting'} and self.hold_bytes is not None:
            try:
                with self.hold.open('xb') as out:
                    out.write(self.hold_bytes)
                    out.flush()
                    os.fsync(out.fileno())
            except FileExistsError:
                pass  # Never replace an operator's intervening hold.
        self.checkpoint('failed', failed_phase=self.phase, status='fail', error=str(exc),
                        recovery='inspect_transition_and_preserve_startup_hold')


class StoppedDeploymentRecovery(Deployment):
    """Explicit embedding-only recovery of a failed selected native transition.

    The caller holds both ordinary deployment locks. Reuse the live-captured
    native proof, never infer consumption from an absent process. The failed
    attempt remains immutable; only its exact owned hold may transfer.
    """

    def assert_stopped(self):
        if (_main_pids() or not _session_absent() or self.flag.exists()
                or self.flag.is_symlink()
                or Path('/proc', str(self.identity['pid'])).exists()
                or Path('/proc', str(self.launcher)).exists()):
            raise ValueError('deployment_recovery_requires_stopped_main_and_supervisor')

    def preflight(self):
        self.before = self.selection.read_bytes()
        selected = json.loads(self.before)
        failed_root, failed_commit = R.selected_release(self.workspace)
        failed_path = (self.workspace / 'data/runtime/release_transitions' / self.day
                       / failed_commit / 'status.json')
        hold, hold_raw, hold_sig = _owned_metadata(self.hold)
        failed, failed_raw, failed_sig = _owned_metadata(failed_path)
        prior_path = failed_path.with_name('selection-before.json')
        prior, prior_raw, prior_sig = _owned_metadata(prior_path)
        identity = failed.get('predecessor_identity') or {}
        if (selected.get('deployment_transition') != str(failed_path)
                or selected.get('actual_pid_consumed') is not False
                or selected.get('approval_scope') != 'ordered_intraday_deploy_and_restart'
                or selected.get('approved_by') != 'user'
                or failed.get('schema') != 'ordered_intraday_deployment_v1'
                or failed.get('authority') != CONFIRM or failed.get('target_date') != self.day
                or failed.get('candidate_commit') != failed_commit
                or failed.get('candidate_root') != str(failed_root)
                or failed.get('phase') != 'failed' or failed.get('status') != 'fail'
                or failed.get('failed_phase') != 'selected'
                or failed.get('error') != 'deployment_validation_failed:src.engine.automation.intraday_release_handoff'
                or failed.get('policy_effect') != 'unchanged'
                or hold != dict(schema='ordered_deployment_startup_hold_v1', authority=CONFIRM,
                    transition=str(failed_path), target_date=self.day,
                    candidate_commit=failed_commit, old_pid_identity=identity)
                or failed.get('original_selection_sha256') != _digest(prior_raw)
                or prior.get('actual_pid_consumed') is not True
                or prior.get('schema') != 'runtime_release_selection_v1'
                or prior.get('git_commit') != failed.get('previous_commit')
                or prior.get('release_root') != failed.get('previous_root')
                or selected.get('previous_selection_backup') != str(prior_path)
                or selected.get('previous_git_commit') != prior.get('git_commit')
                or selected.get('previous_release_root') != prior.get('release_root')
                or type(identity.get('pid')) is not int
                or identity['pid'] <= 0 or not isinstance(identity.get('start_ticks'), str)
                or not identity['start_ticks'].isdigit()
                or type((failed.get('predecessor_launcher') or {}).get('pid')) is not int
                or failed['predecessor_launcher']['pid'] <= 0
                or not isinstance(failed['predecessor_launcher'].get('start_ticks'), str)
                or not failed['predecessor_launcher']['start_ticks'].isdigit()
                or (prior.get('actual_pid_receipt') or {}).get('pid') != identity['pid']
                or identity.get('cwd') != str(Path(prior['release_root']) / 'src')):
            raise ValueError('deployment_stopped_recovery_source_invalid')
        if failed_path.resolve(strict=True) != failed_path or prior_path.resolve(strict=True) != prior_path:
            raise ValueError('deployment_stopped_recovery_path_invalid')
        self.identity = identity
        self.launcher = failed['predecessor_launcher']['pid']
        self.assert_stopped()
        self.previous, self.previous_commit = R.validate_release(self.workspace, prior)
        commit = R.git(self.candidate, 'rev-parse', 'HEAD')
        self.candidate, self.commit = R.validate_release(self.workspace, dict(
            schema='runtime_release_selection_v1', workspace=str(self.workspace),
            release_root=str(self.candidate), git_commit=commit))
        if (self.candidate in {failed_root, self.previous}
                or Path(__file__).resolve().parents[3] != self.candidate):
            raise ValueError('deployment_recovery_requires_new_reviewed_candidate')
        native = H._native_predecessor(self.day, failed_commit, self.previous,
            self.previous_commit, identity, selected.get('native_predecessor_path'),
            selected.get('native_predecessor_sha256'))
        native_value = H._read(native['path'])
        checks = dict(delay=H.verify_candidate_delay_code(self.day, self.candidate, self.commit),
            stop=H.verify_candidate_stop_code(self.day, self.candidate, self.commit),
            holding=H.verify_candidate_holding_vote_code(self.day, self.candidate, self.commit))
        self.directory = self.workspace / 'data/runtime/release_transitions' / self.day / self.commit
        self.directory.mkdir(parents=True, exist_ok=False)
        self.old = prior
        self.frozen = dict(native['frozen_files'])
        self.checklist = self.workspace / 'docs/checklists' / (self.day + '-stage2-todo-checklist.md')
        self.document_before = self.document_after = self.checklist.read_bytes()
        self.state = dict(schema='ordered_intraday_deployment_v1', authority=CONFIRM,
            target_date=self.day, previous_root=str(self.previous), previous_commit=self.previous_commit,
            candidate_root=str(self.candidate), candidate_commit=self.commit,
            predecessor_identity=identity, predecessor_launcher=failed['predecessor_launcher'],
            original_selection_sha256=_digest(prior_raw), runtime_effect='authorized_code_restart_only',
            policy_effect='unchanged', stopped_recovery_selection_sha256=_digest(self.before),
            failed_hold_adoption=dict(source_failure=failed['error'],
                failed_transition_path=str(failed_path), failed_transition_sha256=_digest(failed_raw),
                failed_selected_root=str(failed_root), failed_selected_commit=failed_commit,
                previous_hold_sha256=_digest(hold_raw), native_predecessor_sha256=native['sha256'],
                transfer_status='verified_not_transferred'))
        self.failed_hold_adoption = dict(raw=hold_raw, signature=hold_sig,
            transition_path=str(failed_path), transition_raw=failed_raw, transition_signature=failed_sig,
            prior_path=str(prior_path), prior_raw=prior_raw, prior_signature=prior_sig)
        for name, raw in [('selection-before.json', prior_raw), ('failed-selection-before.json', self.before),
                ('failed-startup-hold-before.json', hold_raw), ('failed-transition-before.json', failed_raw),
                ('checklist-before.md', self.document_before)]:
            _atomic(self.directory/name, raw)
        self.native_path = self.directory/'native-predecessor.json'
        _atomic(self.native_path, _json_bytes(dict(native_value, candidate_commit=self.commit)))
        self.native_sha = H._sha(self.native_path)
        H._native_predecessor(self.day, self.commit, self.previous, self.previous_commit,
                             identity, self.native_path, self.native_sha)
        self.frozen[str(self.native_path)] = self.native_sha
        self.frozen.update({native['path']: native['sha256'], str(failed_path): _digest(failed_raw),
                            str(prior_path): _digest(prior_raw)})
        for name, check in checks.items():
            _atomic(self.directory/('candidate-'+name+'-code.json'), _json_bytes(check))
        self.assert_unchanged()
        self.assert_stopped()
        self.checkpoint('preflight')

    def drain(self):
        self.assert_hold()
        self.assert_unchanged()
        self.assert_stopped()
        self.checkpoint('drained', drained_at=datetime.now(H.KST).isoformat(),
                        drain_basis='verified_original_native_predecessor_already_stopped')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=H.DATA_DIR.parent)
    parser.add_argument('--release-root', type=Path, required=True)
    parser.add_argument('--target-date', required=True)
    parser.add_argument('--confirm', required=True)
    args = parser.parse_args(argv)
    try:
        with R.runtime_release_set_lock(args.workspace):
            with detector_transition_lock(args.workspace):
                result = execute(Deployment(args.workspace, args.release_root, args.target_date, args.confirm))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'status': 'fail', 'findings': [str(exc)]}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
