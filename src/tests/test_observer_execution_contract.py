import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

from src.engine.monitoring import submission_bottleneck_monitor as M
from src.engine.monitoring.observation_budget import ObservationDeadline


def test_detector_and_monitor_use_one_reader_owner():
    from src.engine.error_detectors import artifact_freshness as detector
    from src.engine.monitoring import observer_artifact_io as io
    assert detector.observer_io is M.observer_io is io
    for name in ('file_signature', 'regular_fd', 'regular_bytes', 'json_object'):
        assert getattr(io, name).__module__ == io.__name__
        assert not hasattr(detector, '_observer_' + name)
        assert not hasattr(M, '_observer_' + name)


@pytest.mark.parametrize('encoded,reason', [
    ('{"x":{"key":1,"key":2}}', 'observer_json_duplicate_key'),
    ('{"x":NaN}', 'observer_json_nonfinite'),
    ('{"x":Infinity}', 'observer_json_nonfinite'),
    ('{"x":-Infinity}', 'observer_json_nonfinite'),
    ('{"x":1e999}', 'observer_json_nonfinite'),
    ('[]', 'observer_json_object_required'),
    ('null', 'observer_json_object_required'),
    ('"value"', 'observer_json_object_required'),
])
def test_shared_observer_json_rejections(encoded, reason):
    with pytest.raises(ValueError, match=reason):
        M.observer_io.json_object(encoded)


@pytest.mark.parametrize('kind', ['missing', 'symlink', 'fifo', 'oversize'])
def test_shared_observer_file_admission(tmp_path, kind):
    path = tmp_path/'artifact'
    expected = 'observer_regular_file_required'
    if kind == 'symlink':
        target = tmp_path/'target'; target.write_text('{}'); path.symlink_to(target)
    elif kind == 'fifo':
        os.mkfifo(path)
    elif kind == 'oversize':
        path.write_text('12345'); expected = 'observer_file_size_limit'
    if kind == 'missing':
        with pytest.raises(FileNotFoundError):
            M.observer_io.regular_bytes(path, limit=4)
    else:
        with pytest.raises(ValueError, match=expected):
            M.observer_io.regular_bytes(path, limit=4)


@pytest.mark.parametrize('when', ['before_open', 'during_read', 'growth'])
def test_shared_observer_races_close_descriptor(tmp_path, monkeypatch, when):
    io = M.observer_io
    path = tmp_path/'artifact'; path.write_bytes(b'{}')
    real_open, real_read = io.os.open, io.os.read
    descriptors = []
    def opening(selected, flags, *args, **kwargs):
        if Path(selected) == path and when == 'before_open':
            path.rename(tmp_path/'original'); path.write_bytes(b'{}')
        fd = real_open(selected, flags, *args, **kwargs)
        if Path(selected) == path: descriptors.append(fd)
        return fd
    changed = []
    def reading(fd, size):
        raw = real_read(fd, size)
        if raw and not changed:
            changed.append(True)
            if when == 'during_read':
                path.rename(tmp_path/'original'); path.write_bytes(b'{}')
            elif when == 'growth':
                with path.open('ab') as out: out.write(b'1234')
        return raw
    monkeypatch.setattr(io.os, 'open', opening)
    monkeypatch.setattr(io.os, 'read', reading)
    expected = {'before_open':'changed_before_read', 'during_read':'changed_during_read',
                'growth':'file_size_limit'}[when]
    with pytest.raises(ValueError, match=expected):
        io.regular_bytes(path, limit=4)
    assert len(descriptors) == 1
    with pytest.raises(OSError): os.fstat(descriptors[0])


@pytest.fixture
def observer(monkeypatch, tmp_path):
    monkeypatch.setattr(M, 'PROJECT_ROOT', tmp_path)
    (tmp_path/'data').mkdir()
    runtime = tmp_path/'data/runtime'
    runtime.mkdir()
    (runtime/'runtime_release_selection.lock').write_bytes(b'')
    # These tests isolate execution/publication. Generation identity and safe
    # selector IO have dedicated adversarial tests in the monitor suite.
    monkeypatch.setattr(M, '_observer_generation_snapshot', lambda project, **kw: dict(
        run_id=kw['run_id'], target_date=kw['target_date'], started_at=kw['started_at'].isoformat(),
        generation_current=True, status='current', selection_sha256='a'*64,
        release_root=str(tmp_path), git_commit='b'*40, observer_code_sha256='c'*64))
    today = datetime.now(M.KST).date().isoformat()
    monkeypatch.setattr(M, 'evaluate', lambda report,state,now: dict(
        schema=M.SCHEMA, as_of=now.isoformat(), date=today, status='observed',
        incidents=dict(state.get('incidents',{})), notification_pending=[], notification_status='idle'))
    monkeypatch.setattr(M, 'source_gap_semantics', lambda *a:dict(status='observed',issues={}))
    monkeypatch.setattr(M, 'attach_source_gap_semantics', lambda r,s:r.update(source_gap_semantics=s))
    monkeypatch.setattr(M, 'entry_execution_tuning_semantics', lambda *a:dict(status='observed',issues={}))
    monkeypatch.setattr(M, 'machine_semantics', lambda *a, **kw:dict(status='observed_receipts_match',issues={}))
    return tmp_path,today


def test_execution_receipts_same_run_and_no_telegram(observer, capsys, monkeypatch):
    root,day = observer
    monkeypatch.setattr(M,'notify',lambda *a:pytest.fail('unexpected Telegram'))
    assert M.main(['--report',str(root/'source.json'),'--reuse-validation-digests']) == 0
    terminal = json.loads(capsys.readouterr().out)
    assert terminal['execution_status'] == 'completed'
    assert terminal['semantic_status'] == 'validated'
    latest = json.loads((root/'data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json').read_text())
    state = json.loads((root/'tmp/submission_bottleneck_monitor_state.json').read_text())
    dated = json.loads((root/f'data/report/buy_funnel_sentinel/submission_bottleneck_monitor_{day}.json').read_text())
    assert latest == dated
    assert state['persistence_schema'] == 'submission_monitor_continuation_v1'
    for key in ('schema', 'date', 'as_of', 'run_id', 'incidents'):
        assert state[key] == latest[key]
    assert 'source_gap_semantics' not in state
    assert terminal['run_id'] == state['run_id']
    assert terminal['publication'] == dict(state=True,latest=True,dated=True)


def test_deadline_preserves_old_pending_and_publishes_deferred(observer,monkeypatch,capsys):
    root,day=observer
    key='machine_policy_receipt_contract'
    old=dict(status='pending',first_seen=day+'T08:00:00+09:00',last_seen=day+'T08:01:00+09:00')
    path=root/'tmp/submission_bottleneck_monitor_state.json';path.parent.mkdir()
    path.write_text(json.dumps(dict(schema=M.SCHEMA, incidents={key:old})))
    def expired(*a, **kw):raise ObservationDeadline('validation_deferred:deadline')
    monkeypatch.setattr(M,'machine_semantics',expired)
    assert M.main(['--report',str(root/'source.json')]) == 75
    terminal=json.loads(capsys.readouterr().out)
    assert terminal['execution_status']=='deferred'
    state=json.loads(path.read_text())
    assert state['incidents'][key]==old
    report=json.loads((root/'data/report/buy_funnel_sentinel/submission_bottleneck_monitor_latest.json').read_text())
    assert report['source_gap_semantics']['status']=='observed'


def test_partial_publication_is_nonzero(observer, monkeypatch, capsys):
    root,_=observer
    write=M._write_state
    def broken(path,value):
        if path.name.endswith('_latest.json'):raise OSError('disk full')
        write(path,value)
    monkeypatch.setattr(M,'_write_state',broken)
    assert M.main(['--report',str(root/'source.json')]) == 1
    terminal=json.loads(capsys.readouterr().out)
    assert terminal['publication']=={'state':True}
    assert terminal['execution_status']=='failed'


def test_source_only_does_not_wait_for_machine_digest_store(observer,monkeypatch,capsys):
    from src.engine.infrastructure.validation_digest_session import DigestSession
    root,_=observer
    monkeypatch.setattr(DigestSession,'activate',lambda *a:pytest.fail('independent source blocked by cache'))
    assert M.main(['--report',str(root/'source.json'),'--source-only','--reuse-validation-digests'])==0
    assert json.loads(capsys.readouterr().out)['semantic_status']=='validated'


def test_known_gap_does_not_hide_unobserved_other_source():
    assert M._incomplete_semantics(dict(status='gap_observed',issues={'known':1},
                                       sources={'probe':{'status':'complete'},'trace':{'status':'unobservable'}}))


@pytest.mark.parametrize('execution,semantic,warning',[
    ('completed','validated',False),('completed','partial',True),
    ('deferred','partial',True),('failed','unobservable',True)])
def test_freshness_does_not_treat_notification_idle_as_validation(tmp_path,execution,semantic,warning):
    from src.engine.error_detectors.artifact_freshness import ArtifactFreshnessDetector,ARTIFACT_REGISTRY
    artifact=next(x for x in ARTIFACT_REGISTRY if x['id']=='submission_bottleneck_monitor')
    path=tmp_path/'receipt.json'
    path.write_text(json.dumps(dict(notification_status='idle',execution_status=execution,
                                   semantic_status=semantic,run_id='a'*32)))
    assert bool(ArtifactFreshnessDetector._validate_json_status(artifact,path,{})) is warning


@pytest.mark.parametrize('sentinel_exit,monitor_exit,expected',[(0,0,0),(0,75,75),(7,0,7),(7,1,7)])
def test_wrapper_priorities_fallback_and_real_terminal(tmp_path,sentinel_exit,monitor_exit,expected):
    repo=Path(__file__).resolve().parents[2]
    (tmp_path/'deploy').mkdir()
    for name in ['run_buy_funnel_sentinel_intraday.sh','cpu_affinity_profile.sh']:
        shutil.copyfile(repo/'deploy'/name,tmp_path/'deploy'/name)
    python=tmp_path/'.venv/bin/python';python.parent.mkdir(parents=True)
    python.write_text('''#!/bin/bash
echo "$*" >> "$PROJECT_DIR/calls"
if [[ "$*" == *submission_bottleneck_monitor* ]]; then
  echo '{"schema":"submission_monitor_execution_v1","execution_status":"completed"}'
  exit "$MONITOR_EXIT"
fi
exit "$SENTINEL_EXIT"
''');python.chmod(0o755)
    nice=tmp_path/'fake_nice';nice.write_text('''#!/bin/bash
echo "$*" >> "$PROJECT_DIR/priorities"
shift 2
exec "$@"
''');nice.chmod(0o755)
    env=dict(os.environ,PROJECT_DIR=str(tmp_path),SENTINEL_EXIT=str(sentinel_exit),
             MONITOR_EXIT=str(monitor_exit),BUY_FUNNEL_SENTINEL_NICE_COMMAND=str(nice),
             KORSTOCKSCAN_NPROC_OVERRIDE='1')
    result=subprocess.run(['bash',str(tmp_path/'deploy/run_buy_funnel_sentinel_intraday.sh'),'2026-10-14'],
                          env=env,capture_output=True,text=True,timeout=10)
    assert result.returncode==expected,result.stdout+result.stderr
    calls=(tmp_path/'calls').read_text()
    assert '--reuse-validation-digests' in calls
    assert ('--source-only' in calls)==bool(sentinel_exit)
    assert len((tmp_path/'priorities').read_text().splitlines())==2
    assert ('[DONE]' in result.stdout)==(expected==0)
    assert (tmp_path/'tmp/run_buy_funnel_sentinel_success.state').exists()==(expected==0)
