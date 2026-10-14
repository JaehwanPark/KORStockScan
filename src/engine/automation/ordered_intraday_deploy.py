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
import subprocess
import tempfile
import uuid
import shlex
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


def _atomic(path, raw):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        os.chmod(name, path.stat().st_mode & 0o777 if path.exists() else 0o644)
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
    def __init__(self, workspace, candidate, day, confirm):
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
                raise ValueError('deployment_existing_operator_hold')
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
        check = self.run_json(self.previous, 'src.engine.automation.intraday_release_handoff',
                              '--verify', '--target-date', self.day, '--pid', str(self.identity['pid']))
        self.run_json(self.previous, 'src.engine.automation.runtime_policy_bootstrap',
                      '--verify', '--target-date', self.day, '--pid', str(self.identity['pid']))
        if check.get('basis') == 'native_preopen':
            self.seal_native_predecessor(check)
        else:
            path, _ = H._paths(self.day, self.previous_commit)
            self.frozen = H._read(path)['frozen_files']
        code_check = H.verify_candidate_delay_code(self.day, self.candidate, self.commit)
        _atomic(self.directory / 'candidate-delay-code.json', _json_bytes(code_check))
        stop_check = H.verify_candidate_stop_code(self.day, self.candidate, self.commit)
        _atomic(self.directory / 'candidate-stop-code.json', _json_bytes(stop_check))
        self.checklist = self.workspace / 'docs/checklists' / (self.day + '-stage2-todo-checklist.md')
        self.document_before = self.checklist.read_bytes()
        self.document_after = subprocess.check_output(['git', '-C', str(self.candidate), 'show',
            self.commit + ':docs/checklists/' + self.checklist.name], timeout=10)
        _atomic(self.directory / 'checklist-before.md', self.document_before)
        self.assert_unchanged()

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
        if self.selection.read_bytes() != self.before:
            raise ValueError('deployment_selection_changed')
        if any(H._sha(path) != sha for path, sha in self.frozen.items()):
            raise ValueError('deployment_predecessor_generation_changed')

    def acquire_hold(self):
        self.assert_unchanged()
        self.hold_bytes = _json_bytes(dict(schema='ordered_deployment_startup_hold_v1',
            authority=CONFIRM, transition=str(self.directory / 'status.json'),
            target_date=self.day, candidate_commit=self.commit, old_pid_identity=self.identity))
        with self.hold.open('xb') as out:
            out.write(self.hold_bytes)
            out.flush()
            os.fsync(out.fileno())
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
            _atomic(self.checklist, self.document_after)
        self.checkpoint('selected', selected_at=value['selected_at_kst'],
                        checklist_sha256=_digest(self.document_after))

    def prepare(self):
        self.assert_hold()
        self.run_json(self.candidate, 'src.engine.automation.intraday_release_handoff', '--prepare',
            '--target-date', self.day, '--old-pid', str(self.identity['pid']),
            '--previous-root', str(self.previous), '--previous-stopped', '--reseal-postclose-source',
            '--confirm', H.CONFIRM)
        self.run_json(self.candidate, 'src.engine.automation.runtime_policy_bootstrap',
                      '--verify', '--target-date', self.day)
        self.run_json(self.candidate, 'src.engine.automation.auxiliary_reader_readiness',
                      '--target-date', self.day)
        self.checkpoint('prepared')

    def start(self):
        self.assert_hold()
        if self.phase != 'prepared' or self.selection.read_bytes() != self.published or _main_pids():
            raise ValueError('deployment_start_generation_changed')
        plan = R.make_plan(self.workspace, self.candidate, self.commit, 'start', self.day)
        child = shlex.split(plan['command'][-1])
        if child[0] != '/usr/bin/env':
            raise ValueError('deployment_launcher_environment_contract_changed')
        child.insert(1, 'KORSTOCKSCAN_VALIDATION_SESSION_ID=' + self.validation_session)
        plan['command'][-1] = shlex.join(child)
        self.hold.unlink()
        _launch(plan)
        self.checkpoint('starting')

    def attest(self):
        def consumed():
            value = H._read(self.selection)
            if value.get('git_commit') != self.commit:
                raise ValueError('deployment_selection_changed_during_start')
            return value.get('actual_pid_consumed') is True
        _wait(consumed, 150, 'deployment_pid_attestation_timeout')
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
