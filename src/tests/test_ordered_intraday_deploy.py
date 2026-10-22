"""Deployment automation contracts; no real processes, flags or policy calls."""
import json
import fcntl
import os
import subprocess
from pathlib import Path

import pytest

from src.engine.automation import ordered_intraday_deploy as D


@pytest.fixture(autouse=True)
def _summary_preflight_contract(monkeypatch):
    from src.engine.monitoring import sentinel_summary_contract as summary
    monkeypatch.setattr(summary, 'check_pending_migration', lambda *_:dict(status='current_contract'))


@pytest.fixture
def stopped_recovery(tmp_path, monkeypatch):
    day = '2026-10-12'
    candidate = Path(D.__file__).resolve().parents[3]
    old_root, failed_root = tmp_path/'old', tmp_path/'failed'
    old_commit, failed_commit, new_commit = 'a'*40, 'b'*40, 'c'*40
    directory = tmp_path/'data/runtime/release_transitions'/day/failed_commit
    directory.mkdir(parents=True)
    identity = dict(pid=2147483601, start_ticks='123', cwd=str(old_root/'src'))
    prior = dict(schema='runtime_release_selection_v1', workspace=str(tmp_path),
        release_root=str(old_root), git_commit=old_commit, actual_pid_consumed=True,
        actual_pid_receipt={'pid':identity['pid']})
    prior_path = directory/'selection-before.json';prior_path.write_bytes(D._json_bytes(prior))
    status_path = directory/'status.json'
    status = dict(schema='ordered_intraday_deployment_v1', authority=D.CONFIRM,
        target_date=day, candidate_commit=failed_commit, candidate_root=str(failed_root),
        previous_root=str(old_root), previous_commit=old_commit, predecessor_identity=identity,
        predecessor_launcher=dict(pid=2147483602,start_ticks='124'), phase='failed',status='fail',
        failed_phase='selected', error='deployment_validation_failed:src.engine.automation.intraday_release_handoff',
        policy_effect='unchanged', original_selection_sha256=D._digest(prior_path.read_bytes()))
    status_path.write_bytes(D._json_bytes(status))
    native_path = directory/'native-predecessor.json'
    policy = tmp_path/'policy.json';policy.write_text('original policy')
    native_value = dict(candidate_commit=failed_commit, frozen_files={str(policy):D.H._sha(policy)})
    native_path.write_bytes(D._json_bytes(native_value))
    selected = dict(schema='runtime_release_selection_v1',workspace=str(tmp_path),
        release_root=str(failed_root),git_commit=failed_commit, actual_pid_consumed=False,
        deployment_transition=str(status_path),approval_scope='ordered_intraday_deploy_and_restart',
        approved_by='user',previous_selection_backup=str(prior_path),
        previous_git_commit=old_commit,previous_release_root=str(old_root),
        native_predecessor_path=str(native_path),native_predecessor_sha256=D.H._sha(native_path))
    selection = tmp_path/'data/runtime/runtime_release_selection.json';selection.write_bytes(D._json_bytes(selected))
    hold = selection.with_name('operator_startup_hold.json')
    hold.write_bytes(D._json_bytes(dict(schema='ordered_deployment_startup_hold_v1',authority=D.CONFIRM,
        transition=str(status_path),target_date=day,candidate_commit=failed_commit,old_pid_identity=identity)))
    selection.with_suffix('.lock').touch()
    checklist = tmp_path/'docs/checklists'/(day+'-stage2-todo-checklist.md')
    checklist.parent.mkdir(parents=True);checklist.write_text('editable original')
    monkeypatch.setattr(D.H,'_today',lambda *a:None)
    monkeypatch.setattr(D.R,'selected_release',lambda *a:(failed_root,failed_commit))
    monkeypatch.setattr(D.R,'git',lambda *a:new_commit)
    monkeypatch.setattr(D.R,'validate_release',lambda w,v:(Path(v['release_root']),v['git_commit']))
    monkeypatch.setattr(D,'_main_pids',lambda:[])
    monkeypatch.setattr(D,'_session_absent',lambda:True)
    def native(day,commit,previous,previous_commit,old_identity,path,sha):
        assert D.H._sha(path)==sha
        value=D.H._read(path)
        assert value['candidate_commit']==commit and old_identity==identity
        assert all(D.H._sha(p)==s for p,s in value['frozen_files'].items())
        return dict(path=str(path),sha256=sha,frozen_files=value['frozen_files'])
    monkeypatch.setattr(D.H,'_native_predecessor',native)
    for name in ('delay','stop','holding_vote'):
        monkeypatch.setattr(D.H,'verify_candidate_'+name+'_code',lambda *a:dict(status='pass'))
    monkeypatch.setattr(D,'verify_candidate_active_policy',lambda *a:dict(status='pass',
        receipt_path=str(policy),receipt_sha256=D.H._sha(policy),
        pointer_path=str(policy),pointer_sha256=D.H._sha(policy)))
    monkeypatch.setattr(D, 'verify_candidate_report_currentness', lambda *a:dict(status='pass'), raising=False)
    d=D.StoppedDeploymentRecovery(tmp_path,candidate,day,D.CONFIRM)
    return d, status_path, policy


def test_stopped_recovery_requires_active_policy_before_hold_transfer(stopped_recovery, monkeypatch):
    d,status,policy=stopped_recovery
    before=d.selection.read_bytes(),d.hold.read_bytes(),status.read_bytes()
    def reject(*args):raise ValueError('active source changed')
    monkeypatch.setattr(D,'verify_candidate_active_policy',reject)
    with pytest.raises(ValueError,match='active source changed'):d.preflight()
    assert before==(d.selection.read_bytes(),d.hold.read_bytes(),status.read_bytes())


def test_stopped_recovery_freezes_prepared_origin_and_uses_native_inheritance(stopped_recovery, monkeypatch, tmp_path):
    d,status,policy=stopped_recovery
    source=tmp_path/'prepared-origin.json';source.write_text('immutable origin')
    check=dict(status='pass',prepared_code_origin=dict(sources={str(source):D.H._sha(source)}))
    monkeypatch.setattr(D,'verify_candidate_delay_code',lambda *a:check)
    d.preflight()
    assert d.prepared_delay_check==check and d.frozen[str(source)]==D.H._sha(source)
    assert str(d.selection) not in d.frozen
    source.write_text('different generation')
    with pytest.raises(ValueError,match='generation_changed'):d.acquire_hold()


@pytest.mark.parametrize('damage',[None,'phase','error','date','hold','selection','original','native',
    'main','supervisor','flag','delay','stop','holding_vote','changed_hold','changed_status','changed_policy'])
def test_stopped_recovery_preserves_failed_attempt_and_requires_native_sources(stopped_recovery,monkeypatch,damage):
    d,status_path,policy=stopped_recovery
    if damage in {'phase','error','date'}:
        value=D.H._read(status_path)
        value[{'phase':'failed_phase','error':'error','date':'target_date'}[damage]]='foreign'
        status_path.write_bytes(D._json_bytes(value))
    if damage=='hold':d.hold.write_text('{"operator":"another"}')
    if damage in {'selection','original'}:
        path=d.selection if damage=='selection' else status_path.with_name('selection-before.json')
        value=D.H._read(path);value['actual_pid_consumed']=False if damage=='original' else True
        path.write_bytes(D._json_bytes(value))
    if damage=='native':
        monkeypatch.setattr(D.H,'_native_predecessor',lambda *a:(_ for _ in ()).throw(ValueError('native invalid')))
    if damage=='main':monkeypatch.setattr(D,'_main_pids',lambda:[1])
    if damage=='supervisor':monkeypatch.setattr(D,'_session_absent',lambda:False)
    if damage=='flag':d.flag.write_text('other request')
    if damage in {'delay','stop','holding_vote'}:
        monkeypatch.setattr(D.H,'verify_candidate_'+damage+'_code',lambda *a:(_ for _ in ()).throw(ValueError('code invalid')))
    before=d.selection.read_bytes(),d.hold.read_bytes(),status_path.read_bytes()
    if damage and not damage.startswith('changed_'):
        with pytest.raises((ValueError,AssertionError)):d.preflight()
        assert before==(d.selection.read_bytes(),d.hold.read_bytes(),status_path.read_bytes())
        return
    d.preflight()
    assert before==(d.selection.read_bytes(),d.hold.read_bytes(),status_path.read_bytes())
    if damage=='changed_hold':d.hold.write_text('{"new_owner":true}')
    if damage=='changed_status':status_path.write_text('{}')
    if damage=='changed_policy':policy.write_text('changed policy')
    if damage:
        current=d.selection.read_bytes(),d.hold.read_bytes(),status_path.read_bytes()
        with pytest.raises(ValueError):d.acquire_hold()
        assert current==(d.selection.read_bytes(),d.hold.read_bytes(),status_path.read_bytes())
        return
    d.acquire_hold();d.drain();d.publish()
    assert status_path.read_bytes()==before[2]
    assert d.checklist.read_text()=='editable original'
    assert D.H._read(d.selection)['previous_release_root']==str(d.previous)
    assert D.H._read(d.native_path)['candidate_commit']==d.commit
    assert (d.directory/'failed-selection-before.json').read_bytes()==before[0]
    assert d.state['failed_hold_adoption']['transfer_status']=='transferred_exact_owned_hold'


def _assert_detector_lock_held(workspace):
    with (workspace / 'tmp/run_error_detection.lock').open('a') as other:
        with pytest.raises(BlockingIOError):
            fcntl.flock(other, fcntl.LOCK_EX | fcntl.LOCK_NB)


@pytest.mark.parametrize('chain',[False,True,'two','three'])
@pytest.mark.parametrize('damage', [None, 'proof_pid', 'proof_basis', 'consumed', 'handoff', 'policy', 'preopen', 'manifest','parent_hash','parent_path','parent_proof','depth'])
def test_stopped_intraday_recovery_requires_original_consumption_and_every_frozen_byte(tmp_path, monkeypatch, damage,chain):
    if not chain and damage in ('parent_hash','parent_path','parent_proof','depth'):return
    day, commit = '2026-10-16', 'a'*40
    old = tmp_path/'old';identity=dict(pid=2147483601,start_ticks='123',cwd=str(old/'src'))
    policy=tmp_path/'policy.json';policy.write_text('original')
    preopen=tmp_path/'preopen.json';preopen.write_text('original preopen')
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps({'manifest_sha256':'b'*64}))
    origin=tmp_path/('b'*40)/'status.json' if chain else tmp_path/'status.json'
    origin.parent.mkdir(parents=True,exist_ok=True)
    proof_path=origin.with_name('preflight-intraday_release_handoff.log')
    proof=dict(schema='intraday_pid_consumption_verification_v1',status='pass',findings=[],
        basis='intraday_policy_preserving_handoff',actual_pid_consumed=True,target_date=day,
        selected_release_commit=commit,release_root=str(old),pid_identity=identity,manifest_sha256='b'*64)
    handoff_path=tmp_path/'handoff.json';consumed_path=tmp_path/'consumed.json'
    handoff=dict(schema='intraday_policy_preserving_release_handoff_v1',status='prepared_verified',
        authority=D.H.CONFIRM,target_date=day,selected_release_commit=commit,release_root=str(old),
        preopen_sha256=D.H._sha(preopen),frozen_files={str(policy):D.H._sha(policy),str(manifest):D.H._sha(manifest)})
    handoff_path.write_bytes(D._json_bytes(handoff))
    consumed=dict(schema='intraday_policy_preserving_consumption_v1',status='pass',target_date=day,
        selected_release_commit=commit,release_root=str(old),actual_pid_consumed=True,
        pid_identity=identity,handoff_sha256=D.H._sha(handoff_path),manifest_sha256='b'*64)
    if damage=='proof_pid':proof['pid_identity']={**identity,'start_ticks':'456'}
    elif damage=='proof_basis':proof['basis']='native_preopen'
    elif damage=='consumed':consumed['actual_pid_consumed']=False
    elif damage=='handoff':handoff_path.write_text('{}')
    elif damage=='policy':policy.write_text('changed')
    elif damage=='preopen':preopen.write_text('changed')
    elif damage=='manifest':manifest.write_text(json.dumps({'manifest_sha256':'c'*64}))
    proof_path.write_bytes(D._json_bytes(proof));consumed_path.write_bytes(D._json_bytes(consumed))
    failed_path=origin
    depth=0
    if chain:
        origin.write_bytes(D._json_bytes(dict(predecessor_identity=identity,previous_commit=commit,candidate_commit='b'*40)))
        parent=dict(failed_transition_path=str(origin),failed_selected_commit='b'*40,
            failed_transition_sha256=D.H._sha(origin),intraday_predecessor_proof_sha256=D.H._sha(proof_path),
            transfer_status='transferred_exact_owned_hold')
        if damage=='parent_hash':parent['failed_transition_sha256']='0'*64
        if damage=='parent_path':parent['failed_transition_path']=str(tmp_path/'foreign.json')
        if damage=='parent_proof':parent['intraday_predecessor_proof_sha256']='0'*64
        if damage=='depth':depth=3
        failed_path=tmp_path/('c'*40)/'status.json';failed_path.parent.mkdir()
        failed_path.write_bytes(D._json_bytes(dict(failed_hold_adoption=parent,predecessor_identity=identity,
            previous_commit=commit,candidate_commit='c'*40)))
        if chain in ('two','three'):
            parent=dict(failed_transition_path=str(failed_path),failed_selected_commit='c'*40,
                failed_transition_sha256=D.H._sha(failed_path),intraday_predecessor_proof_sha256=D.H._sha(proof_path),
                transfer_status='transferred_exact_owned_hold')
            failed_path=tmp_path/('d'*40)/'status.json';failed_path.parent.mkdir()
            failed_path.write_bytes(D._json_bytes(dict(failed_hold_adoption=parent,predecessor_identity=identity,
                previous_commit=commit,candidate_commit='d'*40)))
            if chain=='three':
                parent=dict(failed_transition_path=str(failed_path),failed_selected_commit='d'*40,
                    failed_transition_sha256=D.H._sha(failed_path),intraday_predecessor_proof_sha256=D.H._sha(proof_path),
                    transfer_status='transferred_exact_owned_hold')
                failed_path=tmp_path/('e'*40)/'status.json';failed_path.parent.mkdir()
                failed_path.write_bytes(D._json_bytes(dict(failed_hold_adoption=parent)))
    monkeypatch.setattr(D.H,'_paths',lambda *a:(handoff_path,consumed_path))
    monkeypatch.setattr(D.H,'_preopen_path',lambda *a:preopen)
    monkeypatch.setattr(D.H.bootstrap,'manifest_path',lambda *a:manifest)
    before={p:p.read_bytes() for p in (proof_path,handoff_path,consumed_path,policy,preopen,manifest)}
    if damage:
        with pytest.raises(ValueError,match='stopped_(intraday_predecessor|predecessor)_'):
            D._stopped_intraday_predecessor(day,old,commit,identity,failed_path,_depth=depth)
    else:
        result=D._stopped_intraday_predecessor(day,old,commit,identity,failed_path,_depth=depth)
        assert result['frozen_files'][str(consumed_path)]==D.H._sha(consumed_path)
        assert result['frozen_files'][str(proof_path)]==D.H._sha(proof_path)
    assert all(p.read_bytes()==raw for p,raw in before.items())


def test_stopped_recovery_from_intraday_does_not_fabricate_native_receipt(stopped_recovery, monkeypatch):
    d,status_path,policy=stopped_recovery
    selected=D.H._read(d.selection);selected.pop('native_predecessor_path');selected.pop('native_predecessor_sha256')
    d.selection.write_bytes(D._json_bytes(selected))
    proof=status_path.with_name('preflight-intraday_release_handoff.log');proof.write_text('verified original proof')
    monkeypatch.setattr(D,'_stopped_intraday_predecessor',lambda *a:dict(path=str(proof),sha256=D.H._sha(proof),frozen_files={str(policy):D.H._sha(policy)}))
    monkeypatch.setattr(D.H,'_native_predecessor',lambda *a:pytest.fail('intraday consumption relabeled native'))
    d.preflight();d.acquire_hold();d.drain();d.publish()
    assert not hasattr(d,'native_path')
    assert 'native_predecessor_path' not in D.H._read(d.selection)
    assert d.state['failed_hold_adoption']['intraday_predecessor_proof_sha256']==D.H._sha(proof)


@pytest.mark.parametrize('failure', [None, 'preflight', 'publish', 'attest'])
def test_cli_holds_detector_lock_through_attestation_and_failure(tmp_path, monkeypatch, failure):
    (tmp_path/'data').mkdir(exist_ok=True)
    calls = []
    class Driver:
        workspace=tmp_path;day='2026-10-12'
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
def test_transition_does_not_advance_past_failed_phase(tmp_path, failure):
    (tmp_path/'data').mkdir()
    calls = []
    steps = ['preflight', 'acquire_hold', 'drain', 'publish', 'prepare', 'start', 'attest']
    class Driver:
        workspace=tmp_path;day='2026-10-12'
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


@pytest.mark.parametrize('failure', [None, 'drain', 'attest'])
def test_source_epoch_keeps_native_readers_across_the_actual_transition(tmp_path, monkeypatch, failure):
    import sqlite3
    from src.engine.automation import main_trailing_source_store as store
    data=tmp_path/'data';data.mkdir()
    target=store._index_path(data,'holding_path_votes','2026-10-20')
    target.parent.mkdir(parents=True)
    native=store._open_database(target,readonly=False,writer=True)
    native.close()
    opened=[];original=store._open_database
    def observe(*args,**kwargs):
        db=original(*args,**kwargs)
        assert kwargs['readonly'] is True and not db.in_transaction
        opened.append(db);return db
    monkeypatch.setattr(store,'_open_database',observe)
    class Driver:
        workspace=tmp_path;day='2026-10-20'
        def preflight(self):assert not opened
        def __getattr__(self,name):
            def step(*args):
                if name=='fail':return
                assert len(opened)==1 and not opened[0].in_transaction
                assert opened[0].execute('PRAGMA user_version').fetchone()[0]==1
                if name==failure:raise ValueError(name)
                return dict(status='pass')
            return step
    if failure:
        with pytest.raises(ValueError,match=failure):D.execute(Driver())
    else:assert D.execute(Driver())==dict(status='pass')
    assert len(opened)==1
    with pytest.raises(sqlite3.ProgrammingError,match='closed'):opened[0].execute('SELECT 1')
    assert sorted(p.name for p in target.parent.glob('*.sqlite'))==['holding_path_votes.sqlite']


def test_source_epoch_failure_cannot_acquire_hold_or_drain(tmp_path):
    data=tmp_path/'data';data.mkdir()
    target=data/'report/main_trailing_source_index/holding_path_votes.sqlite'
    target.parent.mkdir(parents=True);target.write_bytes(b'not sqlite');target.chmod(0o600)
    called=[]
    class Driver:
        workspace=tmp_path;day='2026-10-20'
        def preflight(self):called.append('preflight')
        def fail(self,exc):called.append('fail')
        def __getattr__(self,name):return lambda *a:called.append(name)
    with pytest.raises(__import__('sqlite3').DatabaseError):D.execute(Driver())
    assert called==['preflight','fail']


@pytest.fixture
def driver(tmp_path, monkeypatch):
    monkeypatch.setattr(D, "verify_candidate_report_currentness", lambda *a:dict(status="pass"), raising=False)
    monkeypatch.setattr(D, "pin_collector_shutdown", lambda *a: dict(pid=123, start_ticks="123"))
    monkeypatch.setattr(D, "verify_collector_shutdown", lambda *a: dict(status="verified"))
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
    d.collector_shutdown_pin = dict(pid=123, start_ticks='123')
    d.checklist = tmp_path / 'checklist.md'; d.checklist.write_text('original')
    d.document_before = b'original'; d.document_after = b'reviewed candidate'
    d.frozen = {str(d.checklist): D._digest(d.document_before)}
    return d


@pytest.mark.parametrize('damage', [None, 'proof', 'main', 'supervisor', 'flag', 'hold', 'source'])
def test_closed_predecessor_drain_rechecks_native_closure_without_stop_mutation(driver, monkeypatch, damage):
    d=driver
    proof=dict(schema='intraday_closed_consumption_observation_v1', pid_identity=d.identity)
    d.closed_predecessor=dict(closed_observation=proof)
    d.hold_bytes=b'owned'; d.hold.write_bytes(d.hold_bytes)
    monkeypatch.setattr(D.H,'closed_consumption_observation',lambda *a: {} if damage=='proof' else proof)
    monkeypatch.setattr(D,'_main_pids',lambda: [456] if damage=='main' else [])
    monkeypatch.setattr(D,'_session_absent',lambda: damage!='supervisor')
    if damage=='flag': d.flag.write_text('another owner')
    if damage=='hold': d.hold.write_text('another owner')
    if damage=='source': d.checklist.write_text('changed')
    before={p:p.read_bytes() for p in (d.selection,d.hold,d.checklist)}
    if damage:
        with pytest.raises(ValueError): d.drain()
        assert not (d.directory/'status.json').exists()
    else:
        d.drain()
        assert d.state['drain_basis']=='native_postclose_stopped_consumption_verified'
        assert d.phase=='drained' and not d.flag.exists()
    assert {p:p.read_bytes() for p in before}==before


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
    def active(*args):
        calls.append('active_policy')
        if reject == 'active_policy': raise ValueError('candidate_validation_rejected')
        return dict(status='pass',receipt_path=str(prior_handoff),receipt_sha256=D.H._sha(prior_handoff),
                    pointer_path=str(d.selection),pointer_sha256=D.H._sha(d.selection))
    monkeypatch.setattr(D, 'verify_candidate_active_policy', active)
    def reports(*args):
        calls.append('reports')
        if reject == 'reports': raise ValueError('candidate_validation_rejected')
        return {'status':'pass'}
    monkeypatch.setattr(D, 'verify_candidate_report_currentness', reports, raising=False)
    d._preflight_native_verified = False
    return calls


@pytest.mark.parametrize("rejected", ["intraday_release_handoff", "runtime_policy_bootstrap", "delay", "stop", "holding", "active_policy", "reports"])
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
    assert calls == ["src.engine.automation.intraday_release_handoff", "src.engine.automation.runtime_policy_bootstrap", "delay", "stop", "holding", "active_policy", "reports"]
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


@pytest.mark.parametrize('module',['src.engine.automation.intraday_release_handoff',
    'src.engine.automation.runtime_policy_bootstrap'])
@pytest.mark.parametrize('damage',[None,'reviewed_pair','other_code','cache','missing','symlink','oversize','flag'])
def test_predecessor_digest_session_requires_same_reviewed_cli_and_cache(tmp_path,module,damage):
    previous,candidate=tmp_path/'old',tmp_path/'new'
    relative=module.replace('.','/')+'.py'
    cache='src/engine/infrastructure/validation_digest_session.py'
    raw="REVIEWED_OVERNIGHT_SELL_RECEIPT_SOURCES = {'path': ('old','new')}\ndef main():\n    return '--validation-session'\n"
    for root in (previous,candidate):
        (root/relative).parent.mkdir(parents=True,exist_ok=True);(root/relative).write_text(raw)
        (root/cache).parent.mkdir(parents=True,exist_ok=True);(root/cache).write_text('DIGEST_CONTRACT=1\n')
    if damage=='reviewed_pair':(previous/relative).write_text(raw.replace("('old','new')","('old','reviewed')"))
    elif damage=='other_code':(previous/relative).write_text(raw+'OTHER_VALIDATION=1\n')
    elif damage=='cache':(previous/cache).write_text('DIGEST_CONTRACT=2\n')
    elif damage=='missing':(previous/relative).unlink()
    elif damage=='symlink':(previous/relative).unlink();(previous/relative).symlink_to(candidate/relative)
    elif damage=='oversize':(previous/relative).write_text('#'*(2*1024*1024+1))
    elif damage=='flag':
        for root in (previous,candidate):(root/relative).write_text(raw.replace('--validation-session','--unsupported'))
    expected=damage is None or damage=='reviewed_pair' and module.endswith('.intraday_release_handoff')
    before={p:p.read_bytes() for root in (previous,candidate) for p in root.rglob('*.py') if p.exists()}
    assert D._compatible_validation_session(previous,candidate,module) is expected
    assert all(p.read_bytes()==value for p,value in before.items())


@pytest.mark.parametrize('compatible',[False,True])
def test_run_json_uses_predecessor_session_only_when_compatible_and_keeps_timeout(tmp_path,monkeypatch,compatible):
    d=object.__new__(D.Deployment);d.candidate=tmp_path/'new';d.validation_session='a'*32
    previous=tmp_path/'old';calls=[]
    monkeypatch.setattr(D,'_compatible_validation_session',lambda *a:compatible)
    def run(argv,**kwargs):
        calls.append((argv,kwargs));return subprocess.CompletedProcess(argv,0,'{"status":"pass"}','')
    monkeypatch.setattr(D.subprocess,'run',run)
    assert d.run_json(previous,'src.engine.automation.runtime_policy_bootstrap','--verify',timeout=17)=={'status':'pass'}
    argv,options=calls[0]
    assert ('--validation-session' in argv) is compatible
    if compatible:assert argv[-2:]==['--validation-session',d.validation_session]
    assert options['timeout']==17 and options['cwd']==previous


@pytest.mark.parametrize('damage',[None,'phase','error','date','hold','selection','original','main','supervisor','flag','native','ancestry','race'])
def test_stopped_policy_code_handoff_uses_only_proven_original_ancestry(stopped_recovery,monkeypatch,damage):
    from src.engine.scalping import reversal_code_handoff as C
    d,status_path,policy=stopped_recovery
    selected=D.H._read(d.selection); failed_root=Path(selected['release_root']); failed_commit=selected['git_commit']
    prior=D.H._read(status_path.with_name('selection-before.json'))
    monkeypatch.setattr(D,'_stopped_intraday_predecessor',lambda *a: dict(frozen_files={str(policy):D.H._sha(policy)}))
    def ancestry(data,day,origin,commit,bundle,pointer):
        assert str(origin)==prior['release_root'] and commit==prior['git_commit']
        if damage=='race':d.hold.write_text('{}')
        return None if damage=='ancestry' else dict(bundle_sha256=bundle,source_hashes={})
    monkeypatch.setattr(C,'_validated_origin_receipt',ancestry)
    if damage in {'phase','error','date'}:
        row=D.H._read(status_path);row[{'phase':'failed_phase','error':'error','date':'target_date'}[damage]]='foreign';status_path.write_bytes(D._json_bytes(row))
    if damage=='hold':d.hold.write_text('{}')
    if damage in {'selection','original'}:
        p=d.selection if damage=='selection' else status_path.with_name('selection-before.json')
        row=D.H._read(p);row['actual_pid_consumed']=True if damage=='selection' else False;p.write_bytes(D._json_bytes(row))
    if damage=='main':monkeypatch.setattr(D,'_main_pids',lambda:[1])
    if damage=='supervisor':monkeypatch.setattr(D,'_session_absent',lambda:False)
    if damage=='flag':d.flag.write_text('restart')
    if damage=='native':monkeypatch.setattr(D,'_stopped_intraday_predecessor',lambda *a:(_ for _ in ()).throw(ValueError('native invalid')))
    before=(d.selection.read_bytes(),status_path.read_bytes(),policy.read_bytes())
    if damage:
        with pytest.raises(ValueError):C._stopped_origin_receipt(d.workspace/'data',d.day,failed_root,failed_commit,'bundle','pointer')
    else:
        result=C._stopped_origin_receipt(d.workspace/'data',d.day,failed_root,failed_commit,'bundle','pointer')
        assert result['source_hashes'][str(policy)]==D.H._sha(policy)
        assert str(d.hold) not in result['source_hashes'] and str(d.selection) not in result['source_hashes']
        assert str(status_path) in result['source_hashes']
    assert before==(d.selection.read_bytes(),status_path.read_bytes(),policy.read_bytes())


@pytest.mark.parametrize('damage', [None, 'missing', 'seal', 'pointer', 'origin', 'code', 'source', 'race'])
def test_candidate_active_policy_preflight_is_source_bound_and_read_only(tmp_path, monkeypatch, damage):
    from src.engine.scalping import reversal_code_handoff as C, mechanistic_entry_runtime_policy as N
    data=tmp_path/'data';root=data/'runtime/mechanistic_entry_policy';root.mkdir(parents=True)
    pointer=root/'current.json';pointer.write_text(json.dumps({'bundle_sha256':'b'*64}))
    selection=data/'runtime/runtime_release_selection.json'
    selection.write_text(json.dumps(dict(release_root='/old',git_commit='a'*40)))
    monkeypatch.setattr(N,'root',lambda data:root)
    monkeypatch.setattr(N,'validate',lambda *a,**k:None)
    (root/'generations').mkdir();(root/'generations'/('b'*64+'.json')).write_text(json.dumps(dict(bundle_sha256='b'*64,target_date='2026-10-16')))
    code=tmp_path/'code.py';code.write_text('reviewed code')
    source=tmp_path/'source.json';source.write_text('sealed source')
    codes={str(code):D.H._sha(code)};monkeypatch.setattr(C,'code_hashes',lambda:codes)
    receipt=C.P.seal(dict(schema=C.SCHEMA,authority=C.AUTHORITY,target_date='2026-10-16',release_commit='c'*40,
        release_root=str(tmp_path),bundle_sha256='b'*64,current_pointer_sha256=D.H._sha(pointer),
        origin_root='/old',origin_commit='a'*40,origin_selection_sha256=D.H._sha(selection),
        policy_reselected=False,provider_called=False,actual_pid_consumed=False,
        code_hashes=codes,source_hashes={str(source):D.H._sha(source)}))
    if damage=='pointer':receipt['current_pointer_sha256']='x'
    if damage=='origin':receipt['origin_commit']='foreign'
    if damage=='code':receipt['code_hashes']={str(code):'0'*64}
    receipt=C.P.seal(receipt)
    if damage=='seal':receipt['artifact_content_sha256']='0'*64
    dest=C.path(data,'2026-10-16','c'*40,'b'*64);dest.parent.mkdir(parents=True);dest.write_text(json.dumps(receipt))
    if damage=='missing':dest.unlink()
    if damage=='source':source.write_text('tampered')
    def matches(ref,**kwargs):
        if damage=='race':pointer.write_text('{}')
        return D.H._sha(ref['path'])==ref['sha256']
    monkeypatch.setattr(N,'source_receipt_matches',matches)
    before=selection.read_bytes()
    if damage:
        with pytest.raises((ValueError,OSError)):
            D.verify_candidate_active_policy(tmp_path,tmp_path,'c'*40,'2026-10-16')
    else:
        result=D.verify_candidate_active_policy(tmp_path,tmp_path,'c'*40,'2026-10-16')
        assert result['status']=='pass' and result['receipt_sha256']==D.H._sha(dest)
    assert selection.read_bytes()==before
    assert not (data/'runtime/operator_startup_hold.json').exists()
    assert not (tmp_path/'restart.flag').exists()


@pytest.mark.parametrize('fault',[None,'other_failure','unverified_origin','changed_manifest','changed_candidate'])
def test_prepared_delay_origin_preflight_remains_read_only(tmp_path,monkeypatch,fault):
    from src.engine.automation import prepared_policy_code_handoff as P
    from src.engine.scalping import pre_submit_delay_initial_policy as delay
    data=tmp_path/'data';data.mkdir();manifest=tmp_path/'manifest.json'
    manifest.write_text(json.dumps(dict(pre_submit_delay_handoff=dict(policy_sha256='policy',code_contract_sha256='original'))))
    monkeypatch.setattr(D.H.bootstrap,'manifest_path',lambda _:manifest)
    monkeypatch.setattr(D.H,'DATA_DIR',data)
    def original(*a):raise ValueError('other_failure' if fault=='other_failure' else 'entry_consumer_original_code_contract_invalid')
    monkeypatch.setattr(D.H,'verify_candidate_delay_code',original)
    monkeypatch.setattr(D.R,'selected_release',lambda _:(tmp_path/'previous','previous'))
    monkeypatch.setattr(delay,'CONTRACT_PATHS',('source.py',))
    calls=[]
    def resolve(*a,**kw):
        calls.append(kw)
        return dict(basis='wrong' if fault=='unverified_origin' else 'verified_selected_prepared_code_handoff',
                    origin_commit='origin',sources={})
    monkeypatch.setattr(P,'resolve_prepared_code_origin',resolve)
    def delta(*args):
        assert args==(tmp_path/'candidate','candidate','origin',{'source.py':'source.py'},'original')
        if fault=='changed_manifest':manifest.write_text('{}')
        if fault=='changed_candidate':raise ValueError('candidate_dirty')
        return ['source.py']
    monkeypatch.setattr(D.H,'_verify_entry_code_delta',delta)
    monkeypatch.setattr(P,'issue',lambda *a,**kw:pytest.fail('preflight must not publish'))
    if fault:
        with pytest.raises(ValueError):D.verify_candidate_delay_code('day',tmp_path/'candidate','candidate')
    else:
        result=D.verify_candidate_delay_code('day',tmp_path/'candidate','candidate')
        assert result['status']=='pass' and result['actual_pid_consumed'] is False
        assert result['prepared_code_origin']['origin_commit']=='origin'
        assert calls[0]['selected_commit']=='previous' and calls[0]['policy_sha']=='policy'


@pytest.mark.parametrize('changed',[False,True])
def test_prepared_delay_inheritance_preserves_native_issuer_and_source_cas(tmp_path,monkeypatch,changed):
    from src.engine.automation import prepared_policy_code_handoff as P
    source=tmp_path/'source';source.write_text('original')
    original=tmp_path/'prepared';original.write_text(json.dumps(dict(verification_path='original-verification')))
    previous=tmp_path/'previous';previous.write_text(json.dumps(dict(prepared_receipt=str(original),
        original_prepared_receipt='original-prepared',policy_sha256='policy',original_code_sha256='code',paths={'key':'source.py'})))
    check=dict(prepared_code_origin=dict(sources={str(source):D.H._sha(source)},code_handoff_receipt_path=str(previous)))
    calls=[];monkeypatch.setattr(P,'issue',lambda *a,**kw:calls.append((a,kw)) or {'verified':True})
    if changed:
        source.write_text('changed')
        with pytest.raises(ValueError,match='source_changed'):D.inherit_prepared_delay_code(tmp_path,'day',tmp_path/'candidate',check)
        assert calls==[]
    else:
        assert D.inherit_prepared_delay_code(tmp_path,'day',tmp_path/'candidate',check)=={'verified':True}
        assert calls[0][1]['previous_handoff']==previous
        assert calls[0][1]['origin_verification']=='original-verification'
        assert calls[0][1]['confirm']==P.AUTHORITY


@pytest.mark.parametrize('fail',[False,True])
def test_prepared_inheritance_happens_after_drain_before_selection(driver,monkeypatch,fail):
    d=driver;d.acquire_hold();d.phase='drained'
    monkeypatch.setattr(D,'_main_pids',lambda:[])
    before=d.selection.read_bytes();d.prepared_delay_check={'prepared_code_origin':{'test':'bound'}}
    calls=[]
    def inherit(workspace,day,candidate,check):
        assert d.phase=='drained' and d.hold.read_bytes()==d.hold_bytes
        assert d.selection.read_bytes()==before and check==d.prepared_delay_check
        calls.append(True)
        if fail:raise ValueError('native_issuer_refused')
    monkeypatch.setattr(D,'inherit_prepared_delay_code',inherit)
    if fail:
        with pytest.raises(ValueError,match='native_issuer_refused'):d.publish()
        assert d.selection.read_bytes()==before and d.phase=='drained'
    else:
        d.publish();assert d.phase=='selected' and d.selection.read_bytes()!=before
    assert calls==[True]


@pytest.mark.parametrize('phase,error,valid', [
    ('starting','deployment_pid_attestation_timeout',True),
    ('starting','deployment_validation_failed:src.engine.automation.intraday_release_handoff',False),
    ('selected','deployment_pid_attestation_timeout',False)])
def test_stopped_startup_timeout_recovery_keeps_exact_phase_and_error(stopped_recovery,phase,error,valid):
    d,path,_=stopped_recovery
    value=D.H._read(path);value.update(failed_phase=phase,error=error);path.write_bytes(D._json_bytes(value))
    before=path.read_bytes(),d.hold.read_bytes()
    if valid:
        d.preflight()
        assert d.state['failed_hold_adoption']['source_failure']==error
    else:
        with pytest.raises(ValueError,match='stopped_recovery_source_invalid'):d.preflight()
    assert before==(path.read_bytes(),d.hold.read_bytes())


@pytest.mark.parametrize('fault', [None, 'code', 'source', 'quantity_incomplete', 'quantity_missing', 'missing_after_date'])
def test_report_preflight_reuses_native_currentness_and_preserves_economic_gaps(tmp_path, monkeypatch, fault):
    from src.engine.monitoring import main_trailing_currentness as trailing
    from src.engine.error_detectors import artifact_freshness as artifacts
    day, source = '2026-10-20', '2026-10-19'
    monkeypatch.setattr(D.H, 'preserve_checklist', lambda target: {'source_date':source})
    monkeypatch.setattr(D.H, '_read', lambda path: {'original':'holding'})
    monkeypatch.setattr(trailing, 'observe', lambda data, held, target_date:
        {'status':'code_changed' if fault=='code' else 'generation_current'})
    quantity=dict(status='source_gap', findings=['initial_quantity_economic_source_gap'],
        bounded_contract_validated=fault!='source', observation_complete=fault!='quantity_incomplete',
        postclose_stage_status='not_observed' if fault=='quantity_missing' else 'source_gap')
    if fault=='missing_after_date':quantity['findings']=['initial_quantity_stage_missing_after_date']
    seen=[]
    def observe(root, date):
        seen.append((root,date))
        return quantity
    monkeypatch.setattr(artifacts, '_initial_quantity_semantics', observe)
    if fault:
        with pytest.raises(ValueError, match='deployment_.*report_not_current'):
            D.verify_candidate_report_currentness(tmp_path,tmp_path/'candidate',day)
    else:
        result=D.verify_candidate_report_currentness(tmp_path,tmp_path/'candidate',day)
        assert result['status']=='pass' and result['source_date']==source
        assert result['quantity']['findings']==['initial_quantity_economic_source_gap']
        assert result['runtime_effect'] is False and result['policy_effect']=='unchanged'
    assert seen==([] if fault=='code' else [(tmp_path/'candidate',source)])


@pytest.mark.parametrize('failure', [False, True])
def test_prepare_binds_native_source_window_before_start(monkeypatch, tmp_path, failure):
    from src.engine.monitoring import sentinel_source_window as window
    driver = object.__new__(D.Deployment)
    driver.workspace = tmp_path
    driver.candidate = tmp_path/'candidate'
    driver.previous = tmp_path/'previous'
    driver.day = '2026-10-21'
    driver.identity = {'pid':123}
    calls = []
    driver.assert_hold = lambda: calls.append('hold')
    driver.run_json = lambda root, module, *args: calls.append(module)
    driver.checkpoint = lambda phase, **kw: calls.append((phase, kw))
    proof = {'schema':'sentinel_source_window_preparation_v1','runtime_effect':False}
    def prepare(data):
        assert data == tmp_path/'data' and calls[-1].endswith('auxiliary_reader_readiness')
        calls.append('source_window')
        if failure: raise ValueError('source_window_cache_unverified')
        return proof
    monkeypatch.setattr(window, 'prepare', prepare)
    from src.engine import buy_funnel_sentinel as buy
    (tmp_path/'tmp').mkdir()
    def summary(day):
        assert day == driver.day and calls[-1] == 'source_window'
        calls.append('native_summary')
        return [], {'status':'ok'}
    monkeypatch.setattr(buy, 'load_pipeline_event_summaries', summary)
    if failure:
        with pytest.raises(ValueError, match='source_window_cache_unverified'): driver.prepare()
        assert calls[-1] == 'source_window'
    else:
        driver.prepare()
        assert calls[-1] == ('prepared', {'sentinel_source_window':proof,
                                        'sentinel_summary':{'status':'ok'}})


@pytest.mark.parametrize('damage', [None, 'pid', 'start', 'old_generation', 'stale'])
def test_collector_pin_rejects_unproven_incumbent_without_stop_request(tmp_path, damage):
    identity = dict(pid=123, start_ticks='456')
    snapshot = dict(process_pid=123, process_start_ticks='456', collector_lifecycle='running',
                    sequence_epoch=9, enqueued_count=1, source_contract='main_market_source_v1')
    payload = dict(collector_snapshot=snapshot, valid_until_epoch=D.time.time()+30)
    if damage == 'pid': snapshot['process_pid'] = 124
    if damage == 'start': snapshot['process_start_ticks'] = '999'
    if damage == 'old_generation': snapshot.pop('process_pid');snapshot.pop('process_start_ticks')
    if damage == 'stale': payload['valid_until_epoch'] = 0
    path = tmp_path/'data/runtime/scalp_micro_reversion_forward_collector/latest.json'
    path.parent.mkdir(parents=True);path.write_text(json.dumps(payload))
    if damage:
        with pytest.raises(ValueError, match='actor_unproven'):D.pin_collector_shutdown(tmp_path, identity)
    else:
        assert D.pin_collector_shutdown(tmp_path, identity)['sequence_epoch'] == 9
    assert not (tmp_path/'restart.flag').exists()


@pytest.mark.parametrize('damage', [None, 'missing', 'foreign', 'unclosed', 'prior_epoch', 'loss'])
def test_ordered_drain_consumes_exact_native_closed_epoch(tmp_path, damage):
    from src.tests.test_micro_reversion_forward_collector import _closed_main_rejection_source
    _, payload, receipt = _closed_main_rejection_source(tmp_path)
    c = payload['collector_snapshot']
    latest = receipt.parent.parent/'latest.json'
    pin = dict(path=str(latest), pid=c['process_pid'], start_ticks=c['process_start_ticks'],
               sequence_epoch=c['sequence_epoch'], enqueued_count=1)
    if damage == 'missing': receipt.unlink()
    elif damage == 'foreign': pin['start_ticks'] = 'foreign'
    elif damage == 'prior_epoch': pin['sequence_epoch'] = 1
    elif damage:
        if damage == 'unclosed': c['collector_lifecycle'] = 'running'
        if damage == 'loss': c['writer_dropped_envelope_count'] = 1
        latest.write_text(json.dumps(payload))
        closed = json.loads(receipt.read_bytes());closed['collector_snapshot'] = c
        receipt.write_text(json.dumps(closed))
    if damage:
        with pytest.raises((ValueError, FileNotFoundError)):D.verify_collector_shutdown(pin)
    else:
        assert D.verify_collector_shutdown(pin)['status'] == 'verified'


@pytest.fixture
def market_closed_collector(tmp_path, monkeypatch):
    from datetime import datetime
    from src.tests.test_micro_reversion_forward_collector import _closed_main_rejection_source
    _, payload, receipt = _closed_main_rejection_source(tmp_path, count=0)
    snapshot = payload['collector_snapshot']
    # Native legacy receipt: actor comes from the existing WS producer, not
    # from adding missing fields to an operational closed receipt.
    snapshot.pop('process_pid'); snapshot.pop('process_start_ticks')
    identity = dict(pid=123, start_ticks='456', cwd=str(tmp_path/'old/src'))
    selection = dict(release_root=str(tmp_path/'old'), git_commit='a'*40, actual_pid_consumed=True,
        actual_pid_receipt=dict(pid=123, start_ticks='456', process_cwd=identity['cwd'],
                               recorded_at_kst='2026-08-08T10:00:00+09:00'))
    frame = dict(generated_at_epoch=datetime.fromisoformat('2026-08-08T19:59:59+09:00').timestamp(),
        shared_transport_producer=dict(schema='shared_ws_transport_producer_v1',
            process=dict(pid=123, start_ticks=456,
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip()),
            source_root=selection['release_root'], source_commit=selection['git_commit'],
            completed_bar_integrity=dict(observer_epoch=snapshot['sequence_epoch'])))
    heartbeat = dict(main_loop=dict(pid=123), ai_circuit=dict(pid=123, process_start_ticks='456'),
        threads=dict(sniper_engine=dict(alive=False, terminal_reason='market_close',
            last_beat='2026-08-08T20:00:00+09:00', unresolved_scalping_count=0, unresolved_scalping_codes='')))
    values = {receipt: payload, receipt.parent.parent/'latest.json': payload,
        tmp_path/'data/runtime/runtime_release_selection.json': selection,
        tmp_path/'data/runtime/kiwoom_ws_snapshot/latest.json': frame,
        tmp_path/'tmp/error_detector_heartbeat.json': heartbeat}
    def persist():
        for path, value in values.items():
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
    persist()
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):return datetime.fromisoformat('2026-08-08T20:01:00+09:00').astimezone(tz)
    monkeypatch.setattr(D, 'datetime', Clock)
    return identity, payload, receipt, selection, frame, heartbeat, persist


@pytest.mark.parametrize('damage', [None, 'running', 'pid', 'start', 'boot', 'commit', 'root',
    'epoch', 'future_frame', 'future_close', 'previous_day', 'terminal_reason', 'unresolved',
    'alive', 'heartbeat_actor', 'conflicting_collector_actor', 'loss', 'missing_closed',
    'closed_symlink', 'closed_changed', 'missing_frame', 'unaccounted_rejections'])
def test_legacy_first_transition_requires_native_closure_before_any_stop(tmp_path, market_closed_collector, damage):
    identity, payload, receipt, selection, frame, heartbeat, persist = market_closed_collector
    c = payload['collector_snapshot']; producer = frame['shared_transport_producer']
    terminal = heartbeat['threads']['sniper_engine']
    if damage == 'running': c['collector_lifecycle'] = 'running'
    if damage == 'pid': producer['process']['pid'] = 124
    if damage == 'start': producer['process']['start_ticks'] = 457
    if damage == 'boot': producer['process']['boot_id'] = 'another-boot'
    if damage == 'commit': producer['source_commit'] = 'b'*40
    if damage == 'root': producer['source_root'] = str(tmp_path/'other')
    if damage == 'epoch': producer['completed_bar_integrity']['observer_epoch'] += 1
    if damage == 'future_frame': frame['generated_at_epoch'] += 600
    if damage == 'future_close': payload['generated_at'] = '2026-08-08T20:02:00+09:00'
    if damage == 'previous_day': selection['actual_pid_receipt']['recorded_at_kst'] = '2026-08-07T10:00:00+09:00'
    if damage == 'terminal_reason': terminal['terminal_reason'] = 'crash'
    if damage == 'unresolved': terminal['unresolved_scalping_count'] = 1
    if damage == 'alive': terminal['alive'] = True
    if damage == 'heartbeat_actor': heartbeat['ai_circuit']['process_start_ticks'] = '457'
    if damage == 'conflicting_collector_actor': c['process_pid'] = 124
    if damage == 'loss': c['writer_dropped_envelope_count'] = 1
    if damage == 'unaccounted_rejections':
        c['timestamp_rejection_sample_total'] = 65
        payload['canary_guard']['raw_row_exclusion_required'] = True
    persist()
    if damage == 'missing_closed': receipt.unlink()
    if damage == 'closed_symlink':
        other = receipt.with_suffix('.original'); receipt.rename(other); receipt.symlink_to(other)
    if damage == 'closed_changed':
        changed = json.loads(receipt.read_bytes()); changed['collector_snapshot']['enqueued_count'] += 1
        receipt.write_text(json.dumps(changed))
    if damage == 'missing_frame': (tmp_path/'data/runtime/kiwoom_ws_snapshot/latest.json').unlink()
    if damage:
        with pytest.raises((ValueError, FileNotFoundError)):
            D.pin_collector_shutdown(tmp_path, identity)
    else:
        pin = D.pin_collector_shutdown(tmp_path, identity)
        assert pin['basis'] == 'native_market_close'
        assert D.verify_collector_shutdown(pin)['status'] == 'verified'
        # This is actor binding only; never rewrite the legacy producer bytes.
        assert 'process_pid' not in json.loads(receipt.read_bytes())['collector_snapshot']
    assert not (tmp_path/'restart.flag').exists()
    assert not (tmp_path/'data/runtime/operator_startup_hold.json').exists()


@pytest.mark.parametrize('changed', ['frame', 'latest', 'closed'])
def test_first_transition_rechecks_closed_proof_after_process_exit(tmp_path, market_closed_collector, changed):
    identity, payload, receipt, selection, frame, heartbeat, persist = market_closed_collector
    pin = D.pin_collector_shutdown(tmp_path, identity)
    path = {'frame': tmp_path/'data/runtime/kiwoom_ws_snapshot/latest.json',
            'latest': receipt.parent.parent/'latest.json', 'closed': receipt}[changed]
    value = json.loads(path.read_bytes())
    if changed == 'closed': value['collector_snapshot']['writer_dropped_envelope_count'] = 1
    else: value['changed_generation'] = True
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError): D.verify_collector_shutdown(pin)


@pytest.mark.parametrize('failure',[None,'prepare'])
def test_execute_reserves_sentinel_before_drain_releases_before_start(tmp_path,failure):
    (tmp_path/'data').mkdir()
    calls=[]
    class Driver:
        workspace=tmp_path;day='2026-10-12'
        def __getattr__(self,name):
            def step(*args):
                calls.append(name)
                if name in ('drain','publish','prepare','start','attest'):
                    with (tmp_path/'tmp/run_buy_funnel_sentinel.lock').open('a') as lock:
                        if name in ('drain','publish','prepare'):
                            with pytest.raises(BlockingIOError):fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                        else:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                if name==failure:raise ValueError(name)
                return {'status':'pass'}
            return step
    if failure:
        with pytest.raises(ValueError,match=failure):D.execute(Driver())
        assert 'start' not in calls
    else:assert D.execute(Driver())=={'status':'pass'}
    with (tmp_path/'tmp/run_buy_funnel_sentinel.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)


@pytest.mark.parametrize('prepared',[False,True,'published_comparison'])
@pytest.mark.parametrize('damage',[None,'missing','status','date','pid','changed_after_preflight','window','summary'])
def test_stopped_lock_recovery_requires_all_native_preparations(stopped_recovery,damage,prepared):
    d,path,_=stopped_recovery;value=D.H._read(path)
    value['error']='[Errno 11] Resource temporarily unavailable'
    if prepared:
        value.update(failed_phase='prepared',error=('deployment_selection_changed' if prepared=='published_comparison' else 'tuple indices must be integers or slices, not str'),
            sentinel_source_window=dict(schema='sentinel_source_window_preparation_v1',target_date=d.day,runtime_effect=False),
            sentinel_summary=dict(status='ok',runtime_effect=False))
    if damage in ('window','summary'):
        if not prepared:return
        value['sentinel_source_window' if damage=='window' else 'sentinel_summary']['runtime_effect']=True
    path.write_bytes(D._json_bytes(value))
    logs=[]
    for module in ('intraday_release_handoff','runtime_policy_bootstrap','auxiliary_reader_readiness'):
        p=path.with_name('selected-'+module+'.log');logs.append(p)
        p.write_bytes(D._json_bytes(dict(status='pass',target_date=d.day,actual_pid_consumed=False,findings=[])))
    last=logs[-1]
    if damage=='missing':last.unlink()
    elif damage in ('status','date','pid'):
        body=D.H._read(last);body[{'status':'status','date':'target_date','pid':'actual_pid_consumed'}[damage]]={
            'status':'fail','date':'2020-01-01','pid':True}[damage];last.write_bytes(D._json_bytes(body))
    original=path.read_bytes(),d.hold.read_bytes()
    if damage in ('missing','status','date','pid','window','summary'):
        with pytest.raises((OSError,ValueError)):d.preflight()
    else:
        d.preflight();assert all(d.frozen[str(p)]==D.H._sha(p) for p in logs)
        if damage=='changed_after_preflight':
            last.write_bytes(last.read_bytes()+b' ')
            with pytest.raises(ValueError,match='generation_changed'):d.acquire_hold()
    assert original==(path.read_bytes(),d.hold.read_bytes())


@pytest.mark.parametrize('damage',[None,'whitespace','conflict','date','root','commit','status','finding','missing','changed_after_preflight'])
@pytest.mark.parametrize('short_reference', [False, True])
def test_stopped_prestart_failure_is_bound_to_original_native_p5(stopped_recovery,damage,short_reference):
    d,path,_=stopped_recovery;failed=D.H._read(path)
    intake=dict(status='pass',findings=[],target_date=d.day,selected_release_commit=failed['candidate_commit'],
        verification_code_commit=failed['candidate_commit'],verification_code_root=failed['candidate_root'])
    result=dict(schema='main_policy_load_exit_validation_v1',run_id='1'*32,status='failed',failure_phase='intake',
        target_date=d.day,findings=['ValueError:startup_main_code_pair_unreviewed:src/engine/scalping/reversal_code_handoff.py'],
        runtime_effect=False,actual_pid_consumed=False,allowed_runtime_apply=False,native_preparation_checks=dict(intake=intake))
    if short_reference:
        result['findings'] = ['ValueError:prepared_code_intraday_custody_invalid']
    failed.update(failed_phase='prepared',error=repr(result),
        sentinel_source_window=dict(schema='sentinel_source_window_preparation_v1',target_date=d.day,runtime_effect=False),
        sentinel_summary=dict(status='ok',runtime_effect=False))
    native=d.workspace/'data/report/main_startup_validation'/d.day/result['run_id']/'final.json';native.parent.mkdir(parents=True)
    native.write_bytes(D._json_bytes(result))
    if damage in ('date','root','commit','status','finding'):
        if damage=='date':result['target_date']='2000-01-01'
        elif damage=='root':intake['verification_code_root']='foreign'
        elif damage=='commit':intake['verification_code_commit']='d'*40
        elif damage=='status':result['status']='passed'
        else:result['findings']=['unknown']
        failed['error']=repr(result);native.write_bytes(D._json_bytes(result))
    elif damage=='whitespace':native.write_bytes(native.read_bytes()+b' ') # same semantics remains exact native bytes frozen
    if damage=='conflict':
        native.write_bytes(D._json_bytes(dict(result,status='passed')))
    if short_reference:
        failed['error'] = 'selected_p5_failed:' + str(native)
    path.write_bytes(D._json_bytes(failed))
    for module in ('intraday_release_handoff','runtime_policy_bootstrap','auxiliary_reader_readiness'):
        path.with_name('selected-'+module+'.log').write_bytes(D._json_bytes(dict(status='pass',target_date=d.day,actual_pid_consumed=False,findings=[])))
    if damage=='missing':native.unlink()
    original=path.read_bytes(),d.hold.read_bytes()
    if damage in ('conflict','date','root','commit','status','finding','missing'):
        with pytest.raises((OSError,ValueError)):d.preflight()
    else:
        d.preflight();assert d.frozen[str(native)]==D.H._sha(native)
        if damage=='changed_after_preflight':
            native.write_bytes(native.read_bytes()+b' ')
            with pytest.raises(ValueError,match='generation_changed'):d.acquire_hold()
    assert original==(path.read_bytes(),d.hold.read_bytes())


@pytest.mark.parametrize('reject',[False,True])
def test_execute_owns_start_after_prepared_validation(tmp_path,monkeypatch,reject):
    from contextlib import nullcontext
    calls=[]
    monkeypatch.setattr(D,'_source_database_epoch',lambda *a:nullcontext())
    monkeypatch.setattr(D,'sentinel_preparation_lock',lambda *a:nullcontext())
    class Driver:
        workspace=tmp_path;day='2026-10-22'
        def __getattr__(self,name):
            def step(*args):
                calls.append(name)
                if name=='attest':return {'status':'pass'}
            return step
    def validate(driver):
        assert calls==['preflight','acquire_hold','drain','publish','prepare']
        calls.append('validate_prepared')
        if reject:raise ValueError('native P5 failed')
    if reject:
        with pytest.raises(ValueError,match='native P5 failed'):D.execute(Driver(),validate_prepared=validate)
        assert calls[-1]=='fail' and 'start' not in calls
    else:
        assert D.execute(Driver(),validate_prepared=validate)=={'status':'pass'}
        assert calls[-3:]==['validate_prepared','start','attest']
