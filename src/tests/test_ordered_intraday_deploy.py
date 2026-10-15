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


@pytest.mark.parametrize('damage', [None, 'missing', 'malformed', 'symlink', 'future', 'failed', 'date', 'oversize', 'schema', 'run_id', 'duplicate', 'nonfinite', 'overflow', 'as_of_date', 'fifo'])
def test_predecessor_observer_captures_only_exact_bounded_completed_source(tmp_path, damage):
    day = '2026-10-12'
    path = tmp_path / 'data/report/buy_funnel_sentinel' / ('submission_bottleneck_monitor_' + day + '.json')
    path.parent.mkdir(parents=True)
    value = dict(schema='submission_bottleneck_monitor_v1', date=day, as_of='2026-10-12T10:00:00+09:00', run_id='a' * 32,
                 execution_status='completed', semantic_status='partial')
    if damage == 'future': value['as_of'] = '2099-10-12T10:00:00+09:00'
    if damage == 'failed': value['execution_status'] = 'failed'
    if damage == 'date': value['date'] = '2026-10-11'
    if damage == 'as_of_date': value['as_of'] = '2026-10-11T10:00:00+09:00'
    if damage == 'schema': value['schema'] = 'unknown'
    if damage == 'run_id': value['run_id'] = 1
    if damage != 'missing':
        path.write_bytes(D._json_bytes(value))
    if damage == 'malformed': path.write_bytes(b'{')
    if damage == 'duplicate': path.write_bytes(D._json_bytes(value).replace(b'"run_id":', b'"run_id":"extra", "run_id":'))
    if damage == 'nonfinite': path.write_bytes(D._json_bytes(value).replace(b'"run_id":', b'"extra":NaN, "run_id":'))
    if damage == 'overflow': path.write_bytes(D._json_bytes(value).replace(b'"run_id":', b'"extra":1e999, "run_id":'))
    if damage == 'oversize':
        with path.open('wb') as out: out.truncate(8 * 1024 * 1024 + 1)
    if damage == 'fifo':
        path.unlink(); D.os.mkfifo(path)
    if damage == 'symlink':
        other = path.with_suffix('.old'); path.rename(other); path.symlink_to(other)
    result = D._predecessor_observer(tmp_path, day)
    if damage is not None:
        assert result['status'] == 'unavailable'
    else:
        assert result['status'] == 'captured'
        assert result['sha256'] == D._digest(path.read_bytes())
        assert result['mtime_ns'] == path.stat().st_mtime_ns
        assert result['path'] == str(path)
        assert result['as_of'] == value['as_of']
        assert result['semantic_status'] == 'partial'


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


def test_start_uses_real_router_after_releasing_only_owned_hold(driver, monkeypatch):
    d=driver;d.acquire_hold();d.phase='drained'
    monkeypatch.setattr(D,'_main_pids',lambda:[]);d.publish();d.phase='prepared'
    calls=[]
    def launch(plan):
        assert not d.hold.exists()
        assert plan['cwd']==str(d.candidate/'src')
        assert 'KORSTOCKSCAN_VALIDATION_SESSION_ID='+d.validation_session in plan['command'][-1]
        calls.append(plan)
    monkeypatch.setattr(D,'_launch',launch)
    d.start()
    assert d.phase=='starting' and len(calls)==1


def test_router_planning_failure_restores_owned_hold_through_failure_handler(driver, monkeypatch):
    d=driver;d.acquire_hold();d.phase='drained'
    monkeypatch.setattr(D,'_main_pids',lambda:[]);d.publish();d.phase='prepared'
    def fail(*a):
        assert not d.hold.exists()
        raise ValueError('native_router_failure')
    monkeypatch.setattr(D.R,'make_plan',fail)
    monkeypatch.setattr(D,'_launch',lambda *a:pytest.fail('planning failure cannot launch'))
    with pytest.raises(ValueError,match='native_router_failure'):d.start()
    d.fail(ValueError('native_router_failure'))
    assert d.hold.read_bytes()==d.hold_bytes and d.state['failed_phase']=='prepared'


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


@pytest.mark.parametrize('family', ['delay', 'stop', 'holding'])
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
    monkeypatch.setattr(D.H, 'verify_candidate_stop_code', incompatible if family=='stop' else lambda *a:dict(status='pass'))
    monkeypatch.setattr(D.H, 'verify_candidate_holding_vote_code', incompatible)
    with pytest.raises(ValueError, match='entry_consumer_unreviewed_change'):
        D.execute(d)
    assert d.state['failed_phase'] == 'preflight'
    assert not d.hold.exists() and not d.flag.exists()
    assert d.selection.read_bytes() == d.before and d.checklist.read_bytes() == d.document_before


def _failed_hold_fixture(d, monkeypatch):
    older = d.workspace / "older"
    old_identity = dict(pid=111, start_ticks="111", cwd=str(older / "src"))
    prior = dict(schema="runtime_release_selection_v1", git_commit="c" * 40,
        release_root=str(older), actual_pid_consumed=True, actual_pid_receipt={"pid": 111})
    failed_path = d.workspace / "data/runtime/release_transitions" / d.day / d.previous_commit / "status.json"
    failed_path.parent.mkdir(parents=True)
    prior_path = failed_path.with_name("selection-before.json"); prior_path.write_bytes(D._json_bytes(prior))
    failed = dict(schema="ordered_intraday_deployment_v1", authority=D.CONFIRM,
        target_date=d.day, candidate_commit=d.previous_commit, candidate_root=str(d.previous),
        previous_commit=prior["git_commit"], previous_root=prior["release_root"],
        predecessor_identity=old_identity, original_selection_sha256=D._digest(prior_path.read_bytes()),
        policy_effect="unchanged", phase="failed", status="fail", failed_phase="starting",
        error="deployment_pid_attestation_timeout")
    failed_path.write_bytes(D._json_bytes(failed))
    hold = dict(schema="ordered_deployment_startup_hold_v1", authority=D.CONFIRM,
        transition=str(failed_path), target_date=d.day, candidate_commit=d.previous_commit,
        old_pid_identity=old_identity)
    d.hold.write_bytes(D._json_bytes(hold))
    d.old.update(schema="runtime_release_selection_v1", deployment_transition=str(failed_path),
        previous_selection_backup=str(prior_path), previous_git_commit=prior["git_commit"], previous_release_root=prior["release_root"])
    d.before = D._json_bytes(d.old); d.selection.write_bytes(d.before)
    d.selection.with_suffix(".lock").write_text("")
    d.adopt_failed_hold = True; d.failed_hold_adoption = None; d._preflight_native_verified = True
    monkeypatch.setattr(D.H, "_identity", lambda pid: dict(d.identity))
    monkeypatch.setattr(D, "_main_pids", lambda: [d.identity["pid"]])
    return hold, failed, failed_path, prior_path


def test_failed_owned_hold_transfer_is_atomic_and_preserves_native_history(driver, monkeypatch):
    d = driver; hold, failed, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    original = {path: path.read_bytes() for path in (d.hold, failed_path, prior_path, d.selection, d.checklist)}
    d.capture_failed_hold_adoption()
    assert d.hold.read_bytes() == original[d.hold]
    assert d.state["failed_hold_adoption"]["transfer_status"] == "verified_not_transferred"
    replace = D.os.replace
    def held_replace(source, target):
        if Path(target) == d.hold:
            assert d.hold.exists() and d.hold.read_bytes() == original[d.hold]
        return replace(source, target)
    monkeypatch.setattr(D.os, "replace", held_replace)
    unlink = Path.unlink
    def preserve_hold(path, *args, **kwargs):
        if path == d.hold: pytest.fail("hold transfer must not unlink")
        return unlink(path, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", preserve_hold)
    d.acquire_hold()
    assert d.hold.read_bytes() == d.hold_bytes
    assert json.loads(d.hold_bytes)["old_pid_identity"] == d.identity
    assert d.state["failed_hold_adoption"]["transfer_status"] == "transferred_exact_owned_hold"
    for path in (failed_path, prior_path, d.selection, d.checklist): assert path.read_bytes() == original[path]
    assert (d.directory / "failed-startup-hold-before.json").read_bytes() == original[d.hold]
    assert (d.directory / "failed-transition-before.json").read_bytes() == original[failed_path]
    # The live hold intentionally changed, but the original failed terminal
    # remains a separate frozen source, outside native family frozen_files.
    d.assert_unchanged()
    d.assert_hold()


@pytest.mark.parametrize("damage", ["operator_hold", "hold_schema", "hold_authority", "hold_day", "hold_commit", "hold_transition",
    "hold_old_pid", "failed_status", "failed_phase", "failed_error", "failed_root", "failed_authority", "failed_candidate",
    "failed_source_hash", "failed_source_commit", "selector_root", "selector_commit", "selector_unconsumed", "selector_pid",
    "pid_changed", "extra_main", "native_preflight"])
def test_failed_hold_adoption_rejects_foreign_or_unproven_ownership(driver, monkeypatch, damage):
    d = driver; hold, failed, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    if damage == "operator_hold": hold = {"schema": "operator_manual_veto", "authority": "OPERATOR"}
    elif damage == "hold_schema": hold["schema"] = "unknown"
    elif damage == "hold_authority": hold["authority"] = "unapproved"
    elif damage == "hold_day": hold["target_date"] = "2026-10-11"
    elif damage == "hold_commit": hold["candidate_commit"] = d.commit
    elif damage == "hold_transition": hold["transition"] = str(d.directory / "status.json")
    elif damage == "hold_old_pid": hold["old_pid_identity"] = d.identity
    elif damage == "failed_status": failed["status"] = "pass"
    elif damage == "failed_phase": failed["failed_phase"] = "prepared"
    elif damage == "failed_error": failed["error"] = "real_policy_failure"
    elif damage == "failed_root": failed["candidate_root"] = str(d.candidate)
    elif damage == "failed_authority": failed["authority"] = "unapproved"
    elif damage == "failed_candidate": failed["candidate_commit"] = d.commit
    elif damage == "failed_source_hash": failed["original_selection_sha256"] = "0" * 64
    elif damage == "failed_source_commit":
        old = json.loads(prior_path.read_text()); old["git_commit"] = "d" * 40
        prior_path.write_bytes(D._json_bytes(old))
    elif damage == "selector_root": d.old["release_root"] = str(d.candidate)
    elif damage == "selector_commit": d.old["git_commit"] = d.commit
    elif damage == "selector_unconsumed": d.old["actual_pid_consumed"] = False
    elif damage == "selector_pid": d.old["actual_pid_receipt"] = {"pid": 999}
    elif damage == "pid_changed": monkeypatch.setattr(D.H, "_identity", lambda pid: {**d.identity, "start_ticks": "reused"})
    elif damage == "extra_main": monkeypatch.setattr(D, "_main_pids", lambda: [d.identity["pid"], 999])
    elif damage == "native_preflight": d._preflight_native_verified = False
    d.hold.write_bytes(D._json_bytes(hold)); failed_path.write_bytes(D._json_bytes(failed))
    before = {path: path.read_bytes() for path in (d.hold, d.selection, d.checklist, failed_path, prior_path)}
    with pytest.raises(ValueError): d.capture_failed_hold_adoption()
    assert {path: path.read_bytes() for path in before} == before


@pytest.mark.parametrize("damage", ["hold", "same_bytes_replaced", "failed_terminal", "original_selection", "selector", "source"])
def test_failed_hold_compare_exchange_aborts_later_mutation(driver, monkeypatch, damage):
    d = driver; _, _, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    d.capture_failed_hold_adoption()
    if damage == "hold": d.hold.write_text('{"operator":"new veto"}')
    elif damage == "same_bytes_replaced":
        replacement = d.hold.with_name("replacement"); replacement.write_bytes(d.hold.read_bytes()); D.os.replace(replacement, d.hold)
    elif damage == "failed_terminal": failed_path.write_bytes(failed_path.read_bytes() + b" ")
    elif damage == "original_selection": prior_path.write_bytes(prior_path.read_bytes() + b" ")
    elif damage == "selector": d.selection.write_bytes(d.selection.read_bytes() + b" ")
    elif damage == "source": d.checklist.write_bytes(b"changed")
    before = {path: path.read_bytes() for path in (d.hold, failed_path, prior_path, d.selection, d.checklist)}
    with pytest.raises(ValueError): d.acquire_hold()
    assert {path: path.read_bytes() for path in before} == before
    assert d.phase == "preflight"


def test_failed_hold_cannot_be_adopted_without_explicit_flag(driver, monkeypatch):
    d = driver; _failed_hold_fixture(d, monkeypatch); d.adopt_failed_hold = False
    before = d.hold.read_bytes()
    with pytest.raises(ValueError, match="native_preflight_required"): d.capture_failed_hold_adoption()
    with pytest.raises(FileExistsError): d.acquire_hold()
    assert d.hold.read_bytes() == before


def test_unverified_failed_hold_adoption_cannot_acquire(driver, monkeypatch):
    d = driver; _failed_hold_fixture(d, monkeypatch)
    before = d.hold.read_bytes()
    with pytest.raises(ValueError, match="adoption_unverified"): d.acquire_hold()
    assert d.hold.read_bytes() == before


def _mock_adoption_preflight(d, monkeypatch, reject=None):
    monkeypatch.setattr(D.H, "DATA_DIR", d.workspace / "data")
    prior_handoff, _ = D.H._paths(d.day, d.previous_commit)
    prior_handoff.parent.mkdir(parents=True, exist_ok=True)
    prior_handoff.write_text(json.dumps({"frozen_files": d.frozen}))
    monkeypatch.setattr(D, "__file__", str(d.candidate / "src/engine/automation/ordered_intraday_deploy.py"))
    monkeypatch.setattr(D.R, "selected_release", lambda workspace: (d.previous, d.previous_commit))
    monkeypatch.setattr(D.R, "git", lambda *args: d.commit)
    monkeypatch.setattr(D.R, "validate_release", lambda *args: (d.candidate, d.commit))
    text, raw = Path.read_text, Path.read_bytes
    def proc_stat(path, *args, **kwargs):
        if str(path) in ("/proc/123/stat", "/proc/124/stat"):
            return "123 (python) " + " ".join(["S", "124"] + ["0"] * 17 + ["456"])
        return text(path, *args, **kwargs)
    def proc_command(path, *args, **kwargs):
        if str(path) == "/proc/124/cmdline":
            return b"/bin/bash\0" + str(d.previous / "src/run_bot.sh").encode() + b"\0"
        return raw(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", proc_stat)
    monkeypatch.setattr(Path, "read_bytes", proc_command)
    checklist = d.workspace / "docs/checklists" / (d.day + "-stage2-todo-checklist.md")
    checklist.parent.mkdir(parents=True); checklist.write_bytes(b"original current checklist")
    monkeypatch.setattr(D.subprocess, "check_output", lambda *args, **kwargs: b"reviewed candidate checklist")
    calls = []
    def native(root, module, *args, **kwargs):
        calls.append(module)
        assert d.hold.exists()
        if reject is not None and reject in module: raise ValueError("native_validation_rejected")
        return {"status": "pass", "basis": "intraday_policy_preserving_handoff"}
    d.run_json = native
    def code(family):
        def check(*args):
            calls.append(family)
            assert len([name for name in calls if name.startswith("src.engine")]) == 2
            if reject == family: raise ValueError("candidate_validation_rejected")
            return {"status": "pass"}
        return check
    monkeypatch.setattr(D.H, "verify_candidate_delay_code", code("delay"))
    monkeypatch.setattr(D.H, "verify_candidate_stop_code", code("stop"))
    monkeypatch.setattr(D.H, "verify_candidate_holding_vote_code", code("holding"))
    d._preflight_native_verified = False
    return calls


@pytest.mark.parametrize("rejected", ["intraday_release_handoff", "runtime_policy_bootstrap", "delay", "stop", "holding"])
def test_adoption_native_preflight_failure_never_replaces_old_hold(driver, monkeypatch, rejected):
    d = driver; _, _, failed_path, prior_path = _failed_hold_fixture(d, monkeypatch)
    original = {path: path.read_bytes() for path in (d.hold, failed_path, prior_path, d.selection, d.checklist)}
    _mock_adoption_preflight(d, monkeypatch, rejected)
    with pytest.raises(ValueError, match="validation_rejected"): d.preflight()
    assert d._preflight_native_verified is False
    assert d.failed_hold_adoption is None
    assert {path: path.read_bytes() for path in original} == original


def test_adoption_preflight_native_checks_precede_capture_and_acquire(driver, monkeypatch):
    d = driver; _failed_hold_fixture(d, monkeypatch)
    hold_before = d.hold.read_bytes()
    calls = _mock_adoption_preflight(d, monkeypatch)
    d.preflight()
    assert calls == ["src.engine.automation.intraday_release_handoff", "src.engine.automation.runtime_policy_bootstrap", "delay", "stop", "holding"]
    assert d._preflight_native_verified is True
    assert d.hold.read_bytes() == hold_before
    d.acquire_hold()
    d.assert_hold(); d.assert_unchanged()
    assert d.hold.read_bytes() != hold_before and d.phase == "startup_held"


@pytest.mark.parametrize('damage', [None, 'native_source', 'pid', 'candidate', 'runtime_effect', 'consumed'])
def test_repaired_predecessor_requires_full_bound_read_before_any_mutation(driver, monkeypatch, damage):
    d = driver
    _failed_hold_fixture(d, monkeypatch)
    _mock_adoption_preflight(d, monkeypatch)
    d.adopt_failed_hold = False
    d.hold.unlink()
    d.preserve_editable_checklist = True
    before = {p: p.read_bytes() for p in (d.selection, d.checklist)}
    calls = []
    def native(root, module, *args, **kwargs):
        calls.append((root, args))
        if root == d.previous:
            (d.directory/'preflight-intraday_release_handoff.log').write_text('old failure')
            raise ValueError('intraday_preserved_generation_changed')
        assert args == ('--verify-predecessor', '--target-date', d.day, '--pid', '123')
        if damage == 'native_source': raise ValueError('actual_native_source_changed')
        result = dict(status='pass', schema='intraday_pid_consumption_verification_v1',
            target_date=d.day, manifest_sha256='a'*64, verification_code_commit=d.commit,
            verification_code_root=str(d.candidate), selected_release_commit=d.previous_commit,
            release_root=str(d.previous), pid_identity=d.identity, actual_pid_consumed=True,
            candidate_pid_consumed=False, runtime_effect=False)
        if damage == 'pid': result['pid_identity'] = dict(d.identity, start_ticks='changed')
        if damage == 'candidate': result['verification_code_commit'] = 'c'*40
        if damage == 'runtime_effect': result['runtime_effect'] = True
        if damage == 'consumed': result['actual_pid_consumed'] = False
        return result
    d.run_json = native
    for name in ('verify_candidate_delay_code', 'verify_candidate_stop_code', 'verify_candidate_holding_vote_code'):
        monkeypatch.setattr(D.H, name, lambda *args: dict(status='pass'))
    if damage:
        with pytest.raises(ValueError): d.preflight()
        assert d._preflight_native_verified is False
    else:
        d.preflight()
        assert d._preflight_native_verified is True
        assert d.state['predecessor_revalidation']['actual_pid_consumed'] is True
        assert d.document_after == b'original current checklist'
        assert (d.directory/'preflight-previous-intraday_release_handoff.log').read_text() == 'old failure'
    assert len(calls) == 2
    assert not d.hold.exists()
    assert {p: p.read_bytes() for p in before} == before


def test_adopted_hold_continues_through_ordinary_native_drain(driver, monkeypatch):
    d = driver; _, _, failed_path, _ = _failed_hold_fixture(d, monkeypatch)
    failed_before = failed_path.read_bytes()
    d.capture_failed_hold_adoption(); d.acquire_hold()
    d.launcher = 124; d.launcher_stat = "456"
    text = Path.read_text
    def stat(path, *args, **kwargs):
        if str(path) == "/proc/124/stat": return "124 (bash) " + " ".join(["S"] + ["0"] * 18 + ["456"])
        return text(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", stat)
    exists = Path.exists; alive = {"123": True, "124": True}
    monkeypatch.setattr(Path, "exists", lambda path: alive[path.name] if str(path) in ("/proc/123", "/proc/124") else exists(path))
    waits = []
    def wait(predicate, timeout, reason):
        waits.append(reason); assert not predicate()
        alive["123" if len(waits) == 1 else "124"] = False
        assert predicate()
        if len(waits) == 2: d.flag.unlink()
    monkeypatch.setattr(D, "_wait", wait)
    monkeypatch.setattr(D, "_session_absent", lambda: True)
    monkeypatch.setattr(D, "_main_pids", lambda: [])
    d.drain()
    assert d.phase == "drained" and len(waits) == 2
    assert failed_path.read_bytes() == failed_before
    d.assert_hold(); d.assert_unchanged()


def test_hold_transfer_postrename_io_failure_preserves_truthful_owned_hold(driver, monkeypatch):
    d = driver; _, _, failed_path, _ = _failed_hold_fixture(d, monkeypatch)
    failed_before = failed_path.read_bytes()
    d.capture_failed_hold_adoption()
    atomic = D._atomic
    def publication_failure(path, raw, **kwargs):
        atomic(path, raw, **kwargs)
        if Path(path) == d.hold: raise OSError("postrename directory sync failure")
    monkeypatch.setattr(D, "_atomic", publication_failure)
    with pytest.raises(OSError, match="postrename"): d.acquire_hold()
    assert d.hold.read_bytes() == d.hold_bytes
    assert d.state["failed_hold_adoption"]["transfer_status"] == "transferred_but_publication_failed"
    assert failed_path.read_bytes() == failed_before


@pytest.mark.parametrize("which", ["hold", "failed", "selector_lock"])
def test_failed_hold_adoption_rejects_special_files_without_replacement(driver, monkeypatch, which):
    d = driver; _, _, failed_path, _ = _failed_hold_fixture(d, monkeypatch)
    original = d.hold.read_bytes()
    if which == "selector_lock":
        d.capture_failed_hold_adoption()
        target = d.selection.with_suffix(".lock"); target.unlink(); os.mkfifo(target)
        with pytest.raises(ValueError, match="regular_file_required"): d.acquire_hold()
        assert d.hold.read_bytes() == original
    else:
        target = d.hold if which == "hold" else failed_path
        target.unlink(); os.mkfifo(target)
        with pytest.raises(ValueError, match="regular_file_required"): d.capture_failed_hold_adoption()
        assert target.is_fifo()
        if which != "hold": assert d.hold.read_bytes() == original


def test_publish_preserves_concurrent_work_checklist(driver,monkeypatch):
    d=driver;d.preserve_editable_checklist=True;d.frozen={}
    d.hold_bytes=b'owned';d.hold.write_bytes(d.hold_bytes);d.phase='drained'
    monkeypatch.setattr(D,'_main_pids',lambda:[])
    d.checklist.write_bytes(b'other session changed its approved plan')
    before=d.checklist.read_bytes()
    d.publish()
    assert d.checklist.read_bytes()==before
    assert d.state['checklist_sha256']==D._digest(before)
    assert d.selection.read_bytes()==d.published
