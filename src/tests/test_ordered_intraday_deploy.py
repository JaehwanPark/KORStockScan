"""Deployment automation contracts; no real processes, flags or policy calls."""
import json
from pathlib import Path

import pytest

from src.engine.automation import ordered_intraday_deploy as D


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
    monkeypatch.setattr(D.R,'make_plan',lambda *a:dict(command=['no_launch'],cwd=str(d.workspace)))
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
