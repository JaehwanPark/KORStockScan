"""Deployment automation contracts; no real processes, flags or policy calls."""
import json
import fcntl
import os
import subprocess
from pathlib import Path

import pytest

from src.engine.automation import ordered_intraday_deploy as D


def _assert_detector_lock_held(workspace):
    with (workspace / 'tmp/run_error_detection.lock').open('a') as other:
        with pytest.raises(BlockingIOError):
            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize('failure', [None, 'preflight', 'publish', 'attest'])
def test_cli_holds_detector_lock_through_attestation_and_failure(tmp_path, monkeypatch, failure):
    calls = []
    class Driver:
        def __getattr__(self, name):
            def step(*args):
                _assert_detector_lock_held(tmp_path)
                calls.append(name)
                if name == failure:
                    raise ValueError(name)
                return {'status': 'pass'}
            return step
    monkeypatch.setattr(D, 'Deployment', lambda *args: Driver())
    rc = D.main(['--workspace', str(tmp_path), '--release-root', str(tmp_path),
                 '--target-date', '2026-10-12', '--confirm', D.CONFIRM])
    assert rc == (1 if failure else 0)
    assert calls[-1] == ('fail' if failure else 'attest')
    with D.detector_transition_lock(tmp_path, timeout=0):
        _assert_detector_lock_held(tmp_path)


def test_busy_detector_times_out_before_deployment_preflight(tmp_path, monkeypatch):
    (tmp_path / 'tmp').mkdir()
    lock_path = tmp_path / 'tmp/run_error_detection.lock'
    with lock_path.open('a') as running:
        fcntl.flock(running, fcntl.LOCK_EX | fcntl.LOCK_NB)
        inode = lock_path.stat().st_ino
        monkeypatch.setattr(D, 'Deployment', lambda *a: pytest.fail('no deployment mutation'))
        ticks = iter([0, 61])
        monkeypatch.setattr(D.time, 'monotonic', lambda: next(ticks))
        assert D.main(['--workspace', str(tmp_path), '--release-root', str(tmp_path),
                       '--target-date', '2026-10-12', '--confirm', D.CONFIRM]) == 1
        assert lock_path.stat().st_ino == inode
        _assert_detector_lock_held(tmp_path)
        assert not (tmp_path / 'data/runtime/operator_startup_hold.json').exists()
        assert not (tmp_path / 'restart.flag').exists()


def test_wait_for_existing_detector_completion_then_acquire(tmp_path, monkeypatch):
    (tmp_path / 'tmp').mkdir()
    with (tmp_path / 'tmp/run_error_detection.lock').open('a') as running:
        fcntl.flock(running, fcntl.LOCK_EX | fcntl.LOCK_NB)
        waits = []
        def finish_detector(seconds):
            waits.append(seconds)
            fcntl.flock(running, fcntl.LOCK_UN)
        monkeypatch.setattr(D.time, 'sleep', finish_detector)
        with D.detector_transition_lock(tmp_path):
            assert waits == [0.25]
            _assert_detector_lock_held(tmp_path)


@pytest.mark.parametrize('explicit_source,expected_rc', [(False, 0), (True, 75)])
def test_actual_detector_wrapper_yields_during_deployment(tmp_path, explicit_source, expected_rc):
    project = Path(__file__).resolve().parents[2]
    args = ['bash', str(project / 'deploy/run_error_detection.sh'), 'full']
    if explicit_source:
        args.append('2026-10-08')
    with D.detector_transition_lock(tmp_path):
        result = subprocess.run(args, env={**os.environ, 'PROJECT_DIR': str(tmp_path)},
                                capture_output=True, text=True, timeout=10)
        _assert_detector_lock_held(tmp_path)
    assert result.returncode == expected_rc, result.stderr
    assert 'ordered deployment holds lock' in result.stdout
    assert '[START]' not in result.stdout
    assert not (tmp_path / 'data').exists()


@pytest.mark.parametrize('guard_rc,explicit_source,expected_rc', [(75, False, 0), (75, True, 75), (1, False, 1)])
def test_wrapper_stale_reader_and_invalid_selection_never_publish(tmp_path, guard_rc, explicit_source, expected_rc):
    project = Path(__file__).resolve().parents[2]
    python = tmp_path / '.venv/bin/python'
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nexit {guard_rc}\n')
    python.chmod(0o755)
    args = ['bash', str(project / 'deploy/run_error_detection.sh'), 'full']
    if explicit_source:
        args.append('2026-10-08')
    result = subprocess.run(args, env={**os.environ, 'PROJECT_DIR': str(tmp_path)},
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == expected_rc, result.stderr
    assert '[START]' not in result.stdout
    assert not (tmp_path / 'data').exists()
    assert not list((tmp_path / 'tmp').glob('error_detection_*.json'))


@pytest.mark.parametrize('failure', [None, 'preflight', 'acquire_hold', 'drain', 'publish', 'prepare', 'start', 'attest'])
def test_transition_does_not_advance_past_failed_phase(failure):
    calls = []
    steps = ['preflight', 'acquire_hold', 'drain', 'publish', 'prepare', 'start', 'attest']
    class Driver:
        def __getattr__(self, name):
            def step(*args):
                calls.append(name)
                if name == failure:
                    raise ValueError(name)
                return {'status': 'pass'}
            return step
    if failure:
        with pytest.raises(ValueError, match=failure):
            D.execute(Driver())
        assert calls == steps[:steps.index(failure) + 1] + ['fail']
    else:
        assert D.execute(Driver()) == {'status': 'pass'}
        assert calls == steps


@pytest.fixture
def driver(tmp_path):
    d = object.__new__(D.Deployment)
    d.workspace = tmp_path
    runtime = tmp_path / 'data/runtime'; runtime.mkdir(parents=True)
    d.selection = runtime / 'runtime_release_selection.json'
    d.hold = runtime / 'operator_startup_hold.json'
    d.flag = tmp_path / 'restart.flag'
    d.previous = tmp_path / 'old'; d.candidate = tmp_path / 'new'
    d.previous_commit = 'a' * 40; d.commit = 'b' * 40; d.day = '2026-10-12'
    d.identity = dict(pid=123, start_ticks='123', cwd=str(d.previous/'src'))
    d.old = dict(actual_pid_receipt={'pid':123}, actual_pid_consumed=True,
                 release_root=str(d.previous), git_commit=d.previous_commit)
    d.before = D._json_bytes(d.old); d.selection.write_bytes(d.before)
    d.directory = runtime / 'transition'; d.directory.mkdir()
    d.state = {}; d.phase = 'preflight'; d.hold_bytes = None
    d.validation_session = '1' * 32
    d.checklist = tmp_path / 'checklist.md'; d.checklist.write_text('original')
    d.document_before = b'original'; d.document_after = b'reviewed candidate'
    d.frozen = {str(d.checklist): D._digest(d.document_before)}
    return d


@pytest.mark.parametrize('damage', ['running', 'phase', 'selection', 'source', 'hold'])
def test_publication_refuses_unfinished_or_changed_predecessor(driver, monkeypatch, damage):
    d=driver; d.acquire_hold(); d.phase='drained'
    monkeypatch.setattr(D, '_main_pids', lambda: [123] if damage=='running' else [])
    if damage=='phase': d.phase='draining'
    if damage=='selection': d.selection.write_text('changed')
    if damage=='source': d.checklist.write_text('changed')
    if damage=='hold': d.hold.write_text('operator hold')
    before=(d.selection.read_bytes(),d.checklist.read_bytes())
    with pytest.raises(ValueError): d.publish()
    assert before==(d.selection.read_bytes(),d.checklist.read_bytes())


@pytest.mark.parametrize('damage', [None, 'missing_consumption', 'pid_changed', 'selector_changed'])
def test_completion_requires_exact_successor_consumption(driver, monkeypatch, damage):
    d = driver
    d.phase = 'starting'
    identity = dict(pid=456, start_ticks='456', cwd=str(d.candidate / 'src'))
    selected = dict(git_commit=d.commit, actual_pid_consumed=True, actual_pid_receipt={'pid': 456})
    d.selection.write_text(json.dumps(selected))
    monkeypatch.setattr(D.H, '_identity', lambda pid: dict(identity))
    monkeypatch.setattr(D, '_main_pids', lambda: [456])
    calls = []
    def verify(root, module, *args):
        calls.append((module, args))
        if module.endswith('intraday_release_handoff'):
            assert args == ('--verify', '--target-date', d.day, '--pid', '456')
            if damage == 'missing_consumption':
                raise ValueError('intraday_consumption_current_pid_not_bound')
            if damage == 'pid_changed':
                identity['start_ticks'] = '457'
            if damage == 'selector_changed':
                d.selection.write_text(json.dumps(dict(selected, git_commit='c' * 40)))
        return {'status': 'pass'}
    d.run_json = verify
    if damage:
        with pytest.raises(ValueError):
            d.attest()
        assert d.phase != 'complete'
    else:
        assert d.attest()['status'] == 'pass'
        assert d.phase == 'complete'
        assert d.state['successor_identity'] == identity
    assert len(calls) == 2


def test_drained_publication_preserves_policy_files_and_records_pending_consumption(driver, monkeypatch):
    d=driver; d.acquire_hold(); d.phase='drained'
    monkeypatch.setattr(D, '_main_pids', lambda: [])
    policy=d.workspace/'policy.json'; policy.write_text('immutable policy')
    d.publish()
    selected=json.loads(d.selection.read_text())
    assert selected['actual_pid_consumed'] is False and 'actual_pid_receipt' not in selected
    assert selected['preserved_main_pid_receipt']==d.old['actual_pid_receipt']
    assert selected['git_commit']==d.commit and selected['previous_git_commit']==d.previous_commit
    assert d.checklist.read_bytes()==d.document_after
    assert d.hold.read_bytes()==d.hold_bytes and policy.read_text()=='immutable policy'
    assert d.state['phase']=='selected'


def test_existing_operator_hold_is_never_overwritten(driver):
    d=driver; d.hold.write_text('operator_owned')
    with pytest.raises(FileExistsError): d.acquire_hold()
    d.fail(ValueError('existing_hold'))
    assert d.hold.read_text()=='operator_owned'


@pytest.mark.parametrize('damage', [None, 'status', 'identity', 'manifest', 'generation'])
def test_native_predecessor_seal_requires_live_verified_consumption(driver, monkeypatch, damage):
    d=driver; data=d.workspace/'data'
    monkeypatch.setattr(D.H,'DATA_DIR',data)
    monkeypatch.setattr(D.H.bootstrap,'env_path',lambda day:data/'bootstrap.env')
    monkeypatch.setattr(D.H.bootstrap,'manifest_path',lambda day:data/'manifest.json')
    monkeypatch.setattr(D.H,'_preopen_path',lambda day:data/'preopen.json')
    for p in [data/'bootstrap.env',data/'manifest.json',data/'preopen.json']:p.write_text('{}')
    index=data/'runtime/policy_bootstrap/prepared'/d.day/'latest.json'
    receipt=index.parent/'generation/readiness.json';receipt.parent.mkdir(parents=True)
    receipt.write_text('{}');index.write_text(json.dumps(dict(receipt_path=str(receipt),receipt_sha256=D.H._sha(receipt))))
    check=dict(schema='intraday_pid_consumption_verification_v1',status='pass',basis='native_preopen',
        actual_pid_consumed=True,target_date=d.day,selected_release_commit=d.previous_commit,
        release_root=str(d.previous),pid_identity=d.identity,manifest_sha256='verified')
    if damage=='status':check['status']='fail'
    if damage=='identity':check['pid_identity']=dict(d.identity,start_ticks='reused')
    if damage=='manifest':check['manifest_sha256']=None
    if damage=='generation':receipt.write_text('changed')
    monkeypatch.setattr(D.H,'_identity',lambda pid:dict(d.identity))
    monkeypatch.setattr(D.H,'preserve_checklist',lambda day:dict(path='strict-bound',sha256='original'))
    if damage:
        with pytest.raises(ValueError):d.seal_native_predecessor(check)
        assert not (d.directory/'native-predecessor.json').exists()
    else:
        d.seal_native_predecessor(check)
        assert d.native_sha==D.H._sha(d.native_path)
        assert d.frozen[str(d.native_path)]==d.native_sha
        assert json.loads(d.native_path.read_text())['verification']==check
    assert not d.hold.exists() and not d.flag.exists()


@pytest.mark.parametrize('damage', ['phase','selection','running','hold'])
def test_start_refuses_unprepared_or_changed_generation(driver, monkeypatch, damage):
    d=driver; d.acquire_hold(); d.phase='drained'
    monkeypatch.setattr(D,'_main_pids',lambda:[]);d.publish();d.phase='prepared'
    if damage=='phase':d.phase='selected'
    if damage=='selection':d.selection.write_text('other')
    if damage=='running':monkeypatch.setattr(D,'_main_pids',lambda:[99])
    if damage=='hold':d.hold.write_text('other')
    monkeypatch.setattr(D.subprocess,'run',lambda *a,**kw:pytest.fail('must not launch'))
    with pytest.raises(ValueError):d.start()
    assert d.hold.exists()


def test_launch_failure_restores_only_own_startup_hold(driver, monkeypatch):
    d=driver; d.acquire_hold();d.phase='drained'
    monkeypatch.setattr(D,'_main_pids',lambda:[]);d.publish();d.phase='prepared'
    monkeypatch.setattr(D.R,'make_plan',lambda *a:dict(command=['tmux','/usr/bin/env /bin/bash no_launch'],cwd=str(d.workspace)))
    monkeypatch.setattr(D,'_session_absent',lambda:True)
    def fail(*a,**kw):raise OSError('launch_failed')
    monkeypatch.setattr(D.subprocess,'run',fail)
    with pytest.raises(OSError):d.start()
    assert not d.hold.exists()
    selected=d.selection.read_bytes()
    d.fail(OSError('launch_failed'))
    assert d.hold.read_bytes()==d.hold_bytes and d.selection.read_bytes()==selected
    assert d.state['failed_phase']=='prepared'


def test_failed_validation_keeps_selected_generation_held_without_false_success(driver, monkeypatch):
    d=driver;d.acquire_hold();d.phase='drained'
    monkeypatch.setattr(D,'_main_pids',lambda:[]);d.publish()
    calls=[]
    def reject(root,module,*args,**kwargs):
        calls.append((module,args));raise ValueError('invalid_policy')
    d.run_json=reject
    with pytest.raises(ValueError):d.prepare()
    d.fail(ValueError('invalid_policy'))
    assert '--previous-stopped' in calls[0][1]
    assert d.hold.exists() and d.state['status']=='fail'
    assert json.loads(d.selection.read_text())['actual_pid_consumed'] is False


def test_atomic_document_replacement_keeps_reader_permissions(tmp_path):
    p=tmp_path/'receipt';p.write_bytes(b'old');p.chmod(0o640)
    D._atomic(p,b'new')
    assert p.read_bytes()==b'new' and p.stat().st_mode&0o777==0o640
    assert list(tmp_path.iterdir())==[p]


@pytest.mark.parametrize('damage',[None,'main_identity','launcher_identity','stop_timeout','new_main'])
def test_drain_requires_exact_predecessor_exit_and_never_changes_selector(driver, monkeypatch, damage):
    d=driver;d.acquire_hold();d.launcher=124;d.launcher_stat='456'
    monkeypatch.setattr(D,'_session_absent',lambda:True)
    monkeypatch.setattr(D.H,'_identity',lambda pid:
        {**d.identity,'start_ticks':'changed'} if damage=='main_identity' else d.identity)
    read=Path.read_text
    def stat(p,*a,**kw):
        if str(p)=='/proc/124/stat':
            values=['S']+['0']*18+['changed' if damage=='launcher_identity' else '456']
            return '124 (bash) '+' '.join(values)
        return read(p,*a,**kw)
    monkeypatch.setattr(Path,'read_text',stat)
    exists=Path.exists;alive={'123':True,'124':True}
    monkeypatch.setattr(Path,'exists',lambda p:
        alive[p.name] if str(p) in ('/proc/123','/proc/124') else exists(p))
    waits=[]
    def wait(predicate,timeout,reason):
        assert d.selection.read_bytes()==d.before and d.checklist.read_bytes()==d.document_before
        assert d.flag.exists() and d.hold.read_bytes()==d.hold_bytes
        waits.append(reason)
        if damage=='stop_timeout':raise ValueError(reason)
        assert not predicate()
        alive['123' if len(waits)==1 else '124']=False
        assert predicate()
        if len(waits)==2:d.flag.unlink()
    monkeypatch.setattr(D,'_wait',wait)
    monkeypatch.setattr(D,'_main_pids',lambda:[999] if damage=='new_main' else [])
    if damage:
        with pytest.raises(ValueError):d.drain()
        assert d.phase!='drained'
    else:
        d.drain();assert d.phase=='drained' and len(waits)==2
    assert d.selection.read_bytes()==d.before and d.checklist.read_bytes()==d.document_before


def test_wait_is_bounded(monkeypatch):
    ticks=iter([0,0,0.5,1])
    monkeypatch.setattr(D.time,'monotonic',lambda:next(ticks))
    monkeypatch.setattr(D.time,'sleep',lambda _:None)
    with pytest.raises(ValueError,match='not_drained'):
        D._wait(lambda:False,1,'not_drained')


@pytest.mark.parametrize('damage',[None,'new_main','new_session','all_fail'])
def test_supervisor_retry_only_while_session_and_child_absent(monkeypatch,damage):
    from types import SimpleNamespace
    calls=[]
    monkeypatch.setattr(D,'_main_pids',lambda:[10] if damage=='new_main' and calls else [])
    monkeypatch.setattr(D,'_session_absent',lambda: not(damage=='new_session' and calls))
    def launch(*a,**kw):
        calls.append(a)
        return SimpleNamespace(returncode=1 if damage=='all_fail' or len(calls)==1 else 0)
    monkeypatch.setattr(D.subprocess,'run',launch)
    monkeypatch.setattr(D.time,'sleep',lambda _:None)
    if damage:
        with pytest.raises(ValueError):D._launch(dict(command=['tmux'],cwd='/unused'))
        assert len(calls)==(3 if damage=='all_fail' else 1)
    else:
        D._launch(dict(command=['tmux'],cwd='/unused'));assert len(calls)==2


@pytest.mark.parametrize('family', ['delay', 'stop'])
def test_incompatible_candidate_is_rejected_before_hold_or_restart(driver, monkeypatch, family):
    d = driver
    monkeypatch.setattr(D.H, 'DATA_DIR', d.workspace/'data')
    prior, _ = D.H._paths(d.day, d.previous_commit)
    prior.parent.mkdir(parents=True)
    prior.write_text(json.dumps({'frozen_files': d.frozen}))
    monkeypatch.setattr(D, '__file__', str(d.candidate/'src/engine/automation/ordered_intraday_deploy.py'))
    monkeypatch.setattr(D.R, 'selected_release', lambda workspace: (d.previous, d.previous_commit))
    monkeypatch.setattr(D.R, 'git', lambda *a: d.commit)
    monkeypatch.setattr(D.R, 'validate_release', lambda *a: (d.candidate, d.commit))
    monkeypatch.setattr(D.H, '_identity', lambda pid: d.identity)
    monkeypatch.setattr(D, '_main_pids', lambda: [123])
    read_text, read_bytes = Path.read_text, Path.read_bytes
    def stat(path, *args, **kwargs):
        if str(path) in ('/proc/123/stat', '/proc/124/stat'):
            return '123 (python) ' + ' '.join(['S', '124'] + ['0']*17 + ['456'])
        return read_text(path, *args, **kwargs)
    def command(path, *args, **kwargs):
        if str(path) == '/proc/124/cmdline':
            return b'/bin/bash\0' + str(d.previous/'src/run_bot.sh').encode() + b'\0'
        return read_bytes(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', stat)
    monkeypatch.setattr(Path, 'read_bytes', command)
    calls = []
    def incumbent(root, module, *args, **kwargs):
        calls.append(module)
        return {'status': 'pass', 'handoff': {'frozen_files': d.frozen}}
    d.run_json = incumbent
    def incompatible(day, root, commit):
        assert len(calls) == 2 and root == d.candidate and commit == d.commit
        assert not d.hold.exists() and not d.flag.exists()
        assert d.selection.read_bytes() == d.before
        raise ValueError('entry_consumer_unreviewed_change:producer')
    monkeypatch.setattr(D.H, 'verify_candidate_delay_code', incompatible if family=='delay' else lambda *a:dict(status='pass'))
    monkeypatch.setattr(D.H, 'verify_candidate_stop_code', incompatible)
    with pytest.raises(ValueError, match='entry_consumer_unreviewed_change'):
        D.execute(d)
    assert d.state['failed_phase'] == 'preflight'
    assert not d.hold.exists() and not d.flag.exists()
    assert d.selection.read_bytes() == d.before and d.checklist.read_bytes() == d.document_before
