"""Startup automation: policy preservation, launcher admission and PID custody."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from src.engine.automation import intraday_release_handoff as handoff
from src.engine.automation import next_preopen_readiness as readiness

NOW = datetime(2026, 10, 2, 10, 0, tzinfo=ZoneInfo("Asia/Seoul"))
DAY = "2026-10-02"
OLD = "a" * 40
NEW = "b" * 40
NATIVE_SELECTION = handoff._selection


@pytest.mark.parametrize('name', ['src/engine/kiwoom_sniper_v2.py',
                                  'src/engine/monitoring/submission_bottleneck_monitor.py',
                                  'src/engine/sniper_state_handlers.py',
                                  'src/engine/scalping/scanner_async_eval.py',
                                  'src/engine/ai_engine_openai.py',
                                  'src/engine/scalping/main_stop_policy.py',
                                  'src/engine/automation/main_stop_postclose.py',
                                  'src/engine/automation/runtime_policy_bootstrap.py',
                                  'src/engine/lifecycle/holding_window_generation.py'])
@pytest.mark.parametrize('review_map', ['REVIEWED_ENTRY_CONSUMER_SOURCES',
                                     'REVIEWED_ENTRY_LATENCY_SOURCES',
                                     'REVIEWED_ENTRY_BOUNDARY_SOURCES',
                                     'REVIEWED_ENTRY_RESPONSE_SOURCES',
                                     'REVIEWED_ENTRY_STORAGE_SOURCES',
                                     'REVIEWED_JOINT_CONSUMER_SOURCES',
                                     'REVIEWED_REST_REDUCTION_SOURCES',
                                     'REVIEWED_IO_OBSERVER_SOURCES',
                                     'REVIEWED_IO_DIGEST_SOURCES',
                                     'REVIEWED_STOP_CONSUMER_SOURCES',
                                     'REVIEWED_NONFIXED_SUBMIT_SOURCES',
                                     'REVIEWED_SUBMISSION_TIMEOUT_SOURCES',
                                     'REVIEWED_OBSERVER_TERMINAL_SESSION_SOURCES',
                                     'REVIEWED_PREMARKET_OBSERVER_SOURCES',
                                     'REVIEWED_ACTIVE_OBSERVER_SOURCES',
                                     'REVIEWED_CURRENT_OBSERVER_SOURCES',
                                     'REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES',
                                     'REVIEWED_OBSERVER_STATE_READER_SOURCES',
                                     'REVIEWED_NATIVE_INCOMPLETE_OBSERVER_SOURCES',
                                     'REVIEWED_ORDERED_PUBLICATION_SOURCES',
                                     'REVIEWED_OPPORTUNITY_CUSTODY_SOURCES',
                                     'REVIEWED_NATIVE_ARM_COMPLETION_SOURCES',
                                     'REVIEWED_CARRIED_SOURCE_BINDING_SOURCES'])
@pytest.mark.parametrize('damage', [None, 'after', 'before', 'dirty', 'origin_digest'])
def test_reviewed_consumer_source_pair_is_exact_and_read_only(tmp_path, monkeypatch, damage, name, review_map):
    import hashlib
    own = 'src/engine/automation/intraday_release_handoff.py'
    before, after = b'def runtime(): return 1\n', b'def runtime(): return 2\n'
    pair = (hashlib.sha256(before).hexdigest(), hashlib.sha256(after).hexdigest())
    monkeypatch.setattr(handoff, 'REVIEWED_ENTRY_CONSUMER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_ENTRY_LATENCY_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_ENTRY_BOUNDARY_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_ENTRY_RESPONSE_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_ENTRY_STORAGE_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_JOINT_CONSUMER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_REST_REDUCTION_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_IO_OBSERVER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_IO_DIGEST_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_STOP_CONSUMER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_NONFIXED_SUBMIT_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_SUBMISSION_TIMEOUT_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_OBSERVER_TERMINAL_SESSION_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_PREMARKET_OBSERVER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_ACTIVE_OBSERVER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_CURRENT_OBSERVER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_NATIVE_HANDOFF_INTEGRATION_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_OBSERVER_STATE_READER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_NATIVE_INCOMPLETE_OBSERVER_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_ORDERED_PUBLICATION_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_OPPORTUNITY_CUSTODY_SOURCES', {})
    monkeypatch.setattr(handoff, 'REVIEWED_NATIVE_ARM_COMPLETION_SOURCES', {})
    monkeypatch.setattr(handoff, review_map, {name: pair})
    expected = hashlib.sha256(json.dumps({name: pair[0]}, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if damage == 'before': before += b'# altered baseline\n'
    if damage == 'after': after += b'# unreviewed successor\n'
    for path, body in ((name, after), (own, b'# verified verifier\n')):
        p = tmp_path/path; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(body)
    monkeypatch.setattr(handoff.subprocess, 'check_output', lambda command, **kw:
        b'# verified verifier\n' if command[-1].endswith(':'+own)
        else before if command[-1].startswith(OLD+':') else after)
    if damage == 'dirty': (tmp_path/name).write_bytes(after+b'# dirty\n')
    if damage == 'origin_digest': expected = '0'*64
    frozen = {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}
    if damage:
        with pytest.raises(ValueError):
            handoff._verify_entry_code_delta(tmp_path, NEW, OLD, {name: name}, expected)
    else:
        assert handoff._verify_entry_code_delta(tmp_path, NEW, OLD, {name: name}, expected) == [name]
    assert frozen == {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file()}


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.mark.parametrize('damage', [None, 'proof_hash', 'authority', 'source', 'pid',
                                   'still_alive', 'selection', 'outside_transition'])
def test_first_native_preopen_can_drain_into_exact_consumed_handoff(fixture, monkeypatch, damage):
    data, previous, selected, _ = fixture
    monkeypatch.setattr(handoff, '_today', lambda *a: NOW)
    manifest = dict(selected_release_sha=OLD, target_date=DAY, manifest_sha256='policy-unchanged')
    _json(handoff.bootstrap.manifest_path(DAY), manifest)
    index = data/'runtime/policy_bootstrap/prepared'/DAY/'latest.json'
    ref = handoff._read(index); receipt = Path(ref['receipt_path'])
    paths = [handoff.bootstrap.env_path(DAY), handoff.bootstrap.manifest_path(DAY),
             handoff._preopen_path(DAY), index, receipt]
    identity = handoff._identity(1)
    original = dict(schema='runtime_release_selection_v1', actual_pid_consumed=True,
        release_root=str(previous), git_commit=OLD, actual_pid_receipt={'pid': 1})
    transition = data/'runtime/release_transitions'/DAY/NEW
    before = transition/'selection-before.json'; _json(before, original)
    proof_path = transition/'native-predecessor.json'
    proof = dict(schema='native_preopen_predecessor_v1',
        authority='APPROVED_ORDERED_INTRADAY_DEPLOY_AND_RESTART', candidate_commit=NEW,
        verification=dict(schema='intraday_pid_consumption_verification_v1', status='pass',
            basis='native_preopen', actual_pid_consumed=True, target_date=DAY,
            selected_release_commit=OLD, release_root=str(previous),
            pid_identity=identity, manifest_sha256='policy-unchanged'),
        frozen_files={str(p): handoff._sha(p) for p in paths},
        prepared_receipt_path=str(receipt), prepared_receipt_sha256=ref['receipt_sha256'],
        selection_before_sha256=handoff._sha(before))
    if damage=='authority': proof['authority']='unapproved'
    if damage=='pid': proof['verification']['pid_identity']=dict(identity,pid=99)
    if damage=='selection': before.write_text('{}')
    if damage=='outside_transition': proof_path=data/'wrong.json'
    _json(proof_path, proof)
    sha=handoff._sha(proof_path)
    if damage=='proof_hash': proof_path.write_text(proof_path.read_text()+' ')
    if damage=='source': handoff.bootstrap.env_path(DAY).write_text('changed')
    _json(data/'runtime/runtime_release_selection.json',dict(approved_by='user',
        approval_scope='ordered_intraday_deploy_and_restart', git_commit=NEW,
        previous_git_commit=OLD, previous_release_root=str(previous),
        native_predecessor_path=str(proof_path),native_predecessor_sha256=sha))
    exists=Path.exists
    monkeypatch.setattr(Path,'exists',lambda p: damage=='still_alive' if str(p)=='/proc/1' else exists(p))
    before_sources={str(p):p.read_bytes() for p in paths}
    assert not handoff._paths(DAY,OLD)[0].exists()
    if damage:
        with pytest.raises(ValueError):
            handoff.prepare(DAY,old_pid=1,previous_root=previous,confirm=handoff.CONFIRM,
                            previous_stopped=True)
        assert not handoff._paths(DAY,NEW)[0].exists()
    else:
        result=handoff.prepare(DAY,old_pid=1,previous_root=previous,confirm=handoff.CONFIRM,
                               previous_stopped=True)
        assert result['status']=='pass'
        value=handoff._read(handoff._paths(DAY,NEW)[0])
        assert value['previous_process_state']=='stopped_native_preopen_consumption_verified'
        assert value['old_pid_identity']==identity
        assert value['frozen_files'][str(proof_path)]==sha
        consumed=handoff.consume(DAY,pid=2,now=NOW)
        assert consumed['actual_pid_consumed'] is True
        assert consumed['pid_identity']==handoff._identity(2)
        proof_path.write_text(proof_path.read_text()+' ')
        assert handoff.verify(DAY,NEW,now=NOW)['status']=='fail'
    assert handoff._NATIVE_PREDECESSOR.get() is None
    assert handoff._STOPPED_PREPARATION.get() is None
    assert not handoff._paths(DAY,OLD)[1].exists()
    assert before_sources=={str(p):p.read_bytes() for p in paths}


@pytest.fixture
def fixture(tmp_path, monkeypatch):
    data = tmp_path / "workspace/data"
    managed = tmp_path / "workspace-runtime-releases"
    previous, selected = managed / "old", managed / "new"
    previous.mkdir(parents=True)
    selected.mkdir()
    monkeypatch.setattr(handoff, "DATA_DIR", data)
    monkeypatch.setattr(readiness, "DATA_DIR", data)
    monkeypatch.setattr(handoff.bootstrap, "BOOTSTRAP_DIR", data / "runtime/policy_bootstrap")
    monkeypatch.setattr(handoff, "_selection", lambda **kwargs: (selected, NEW))
    monkeypatch.setattr(handoff, "is_krx_trading_day", lambda day: day.weekday() < 5)
    monkeypatch.setattr(handoff.bootstrap, "env_path", lambda day: data / f"{day}.env")
    monkeypatch.setattr(handoff.bootstrap, "manifest_path", lambda day: data / f"{day}.manifest.json")
    monkeypatch.setattr(handoff.bootstrap, "verify_bootstrap", lambda day, **kwargs:
                        {"status": "pass", "findings": [], "manifest_sha256": "policy-unchanged"})
    monkeypatch.setattr(handoff.subprocess, "check_output", lambda command, **kwargs:
                        OLD + "\n" if "rev-parse" in command else "")
    monkeypatch.setattr(handoff, "_identity", lambda pid:
                        {"pid": pid, "start_ticks": "42", "cwd": str((previous if pid == 1 else selected) / "src")})
    _json(handoff._preopen_path(DAY), {"target_date": DAY, "status": "succeeded", "exit_code": 0,
                                      "runtime_env_exists": True, "selected_release_commit": OLD,
                                      "updated_at": NOW.isoformat()})
    handoff.bootstrap.env_path(DAY).write_text("export POLICY=unchanged\n")
    _json(handoff.bootstrap.manifest_path(DAY), {"policy": "unchanged"})
    prepared_root = data / "runtime/policy_bootstrap/prepared" / DAY
    receipt = prepared_root / "generation/readiness.json"
    _json(receipt, {"status": "prepared_verified"})
    _json(prepared_root / "latest.json", {"receipt_path": str(receipt), "receipt_sha256": handoff._sha(receipt)})
    def prepare():
        return handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=handoff.CONFIRM, now=NOW)
    return data, previous, selected, prepare


def test_intraday_handoff_preserves_preopen_and_policy_files_then_binds_new_pid(fixture):
    data, _, _, prepare = fixture
    before = {str(path): path.read_bytes() for path in data.rglob("*") if path.is_file()}
    assert prepare()["status"] == "pass"
    assert all(Path(path).read_bytes() == content for path, content in before.items())
    result = readiness.verify_preopen_completion(DAY, NEW, now=NOW)
    assert result["status"] == "pass" and result["basis"] == "intraday_policy_preserving_handoff"
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    assert consumed["actual_pid_consumed"] is True
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(hours=2))["status"] == "pass"


@pytest.mark.parametrize('damage', [None, 'absent', 'schema', 'status', 'pid', 'start_ticks',
                                  'cwd', 'manifest', 'handoff', 'date', 'commit', 'root', 'actual'])
def test_exact_pid_consumption_verifier_rejects_unbound_receipts(fixture, damage):
    data, _, _, prepare = fixture
    assert prepare()['status'] == 'pass'
    receipt = handoff.consume(DAY, pid=2, now=NOW)
    path = handoff._paths(DAY, NEW)[1]
    if damage == 'absent':
        path.unlink()
    elif damage:
        keys = {'manifest': 'manifest_sha256', 'handoff': 'handoff_sha256',
                'date': 'target_date', 'commit': 'selected_release_commit',
                'root': 'release_root', 'actual': 'actual_pid_consumed'}
        if damage in {'pid', 'start_ticks', 'cwd'}:
            receipt['pid_identity'][damage] = 3 if damage == 'pid' else 'wrong'
        else:
            receipt[keys.get(damage, damage)] = 'wrong'
        _json(path, receipt)
    before = {p: p.read_bytes() for p in data.rglob('*') if p.is_file()}
    result = handoff.verify_pid_consumption(DAY, pid=2, now=NOW)
    assert result['status'] == ('fail' if damage else 'pass'), result
    if not damage:
        assert result['pid_identity'] == handoff._identity(2)
        assert result['actual_pid_consumed'] is True
    assert before == {p: p.read_bytes() for p in data.rglob('*') if p.is_file()}


@pytest.mark.parametrize('change', ['identity', 'selection', 'receipt', 'manifest', 'preopen', 'env'])
def test_exact_pid_verifier_rechecks_generation_after_bootstrap(fixture, monkeypatch, change):
    _, _, selected, prepare = fixture
    prepare(); handoff.consume(DAY, pid=2, now=NOW)
    checked = handoff._checked_bootstrap
    def mutate(day, pid):
        result = checked(day, pid)
        if change == 'identity':
            monkeypatch.setattr(handoff, '_identity', lambda pid:
                                dict(pid=pid, start_ticks='43', cwd=str(selected / 'src')))
        elif change == 'selection':
            monkeypatch.setattr(handoff, '_selection', lambda **kw: (selected, OLD))
        else:
            p = {'receipt': handoff._paths(DAY, NEW)[1],
                 'manifest': handoff.bootstrap.manifest_path(DAY),
                 'env': handoff.bootstrap.env_path(DAY),
                 'preopen': handoff._preopen_path(DAY)}[change]
            p.write_bytes(p.read_bytes() + b'\n')
        return result
    monkeypatch.setattr(handoff, '_checked_bootstrap', mutate)
    result = handoff.verify_pid_consumption(DAY, pid=2, now=NOW)
    assert result['status'] == 'fail'
    assert result['findings'] == ['intraday_consumption_generation_changed']


@pytest.mark.parametrize('native_commit', [OLD, NEW])
def test_native_preopen_pid_verification_never_substitutes_for_code_handoff(fixture, native_commit):
    data, _, _, _ = fixture
    status = handoff._read(handoff._preopen_path(DAY))
    _json(handoff._preopen_path(DAY), dict(status, selected_release_commit=native_commit))
    before = {p: p.read_bytes() for p in data.rglob('*') if p.is_file()}
    result = handoff.verify_pid_consumption(DAY, pid=2, now=NOW)
    assert result['status'] == ('pass' if native_commit == NEW else 'fail')
    assert before == {p: p.read_bytes() for p in data.rglob('*') if p.is_file()}


def test_verify_cli_with_pid_uses_consumption_contract(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(handoff, 'verify_pid_consumption', lambda day, **kw:
                        calls.append((day, kw['pid'])) or dict(status='fail', findings=['missing']))
    assert handoff.main(['--verify', '--target-date', DAY, '--pid', '2']) == 1
    assert calls == [(DAY, 2)]
    assert json.loads(capsys.readouterr().out)['findings'] == ['missing']


@pytest.mark.parametrize('damage', [None, 'alive', 'wrong_pid', 'changed_consumption'])
def test_stopped_handoff_requires_prior_exact_consumption(fixture, monkeypatch, damage):
    data, _, selected, prepare = fixture
    assert prepare()['status'] == 'pass'
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    successor = selected.parent / 'successor'; successor.mkdir()
    commit = 'c' * 40
    monkeypatch.setattr(handoff, '_selection', lambda **kw: (successor, commit))
    monkeypatch.setattr(handoff.subprocess, 'check_output', lambda command, **kw:
                        NEW + '\n' if 'rev-parse' in command else '')
    exists = Path.exists
    monkeypatch.setattr(Path, 'exists', lambda p: damage == 'alive' if str(p) == '/proc/2' else exists(p))
    if damage == 'wrong_pid':
        consumed['pid_identity']['pid'] = 99
        _json(handoff._paths(DAY, NEW)[1], consumed)
    if damage in {'alive', 'wrong_pid'}:
        with pytest.raises(ValueError, match='intraday_'):
            handoff.prepare(DAY, old_pid=2, previous_root=selected, confirm=handoff.CONFIRM,
                            now=NOW, previous_stopped=True)
        return
    result = handoff.prepare(DAY, old_pid=2, previous_root=selected, confirm=handoff.CONFIRM,
                             now=NOW, previous_stopped=True)
    assert result['status'] == 'pass', result
    assert result['actual_pid_consumed'] is False
    assert result['handoff']['previous_process_state'] == 'stopped_historical_consumption_verified'
    if damage == 'changed_consumption':
        _json(handoff._paths(DAY, NEW)[1], dict(consumed, status='changed'))
        assert handoff.verify(DAY, commit, now=NOW)['status'] == 'fail'


@pytest.mark.parametrize('freeze', [False, True])
@pytest.mark.parametrize('tamper', ['none', 'policy', 'controller', 'checklist', 'snapshot'])
def test_intraday_current_document_reseal_preserves_original_preopen_generation(fixture, monkeypatch, tamper, freeze):
    data, previous, _, _ = fixture
    source_day = '2026-10-01'
    index_path = data/'runtime/policy_bootstrap/prepared'/DAY/'latest.json'
    index = json.loads(index_path.read_text()); receipt = Path(index['receipt_path'])
    policies = [dict(family='main', path='/policy.json', sha256='d'*64)]
    _json(receipt, dict(schema='next_preopen_readiness_v1', status='prepared_verified',
        source_date=source_day, target_date=DAY, actual_pid_consumed=False,
        policy_receipts=policies, controller_sha256='a'*64, summary_sha256='b'*64))
    _json(index_path, dict(receipt_path=str(receipt), receipt_sha256=handoff._sha(receipt)))
    controller = data/'report/postclose_done_controller'/f'postclose_done_controller_{source_day}.json'
    summary = data/'report/runtime_approval_summary'/f'runtime_approval_summary_{source_day}.json'
    checklist = data.parent/'docs/checklists'/f'{DAY}-stage2-todo-checklist.md'
    _json(controller, {'status':'done'});_json(summary, {'status':'verified'})
    checklist.parent.mkdir(parents=True);checklist.write_text('current owner')
    source = dict(controller_path=str(controller), controller_sha256=handoff._sha(controller),
        summary_path=str(summary), summary_sha256=handoff._sha(summary),
        policy_receipts=[dict(policies[0],sha256='e'*64)] if tamper=='policy' else policies)
    monkeypatch.setattr(readiness, '_source_receipts', lambda *a, **k: source)
    original = receipt.read_bytes()
    if tamper == 'policy':
        with pytest.raises(ValueError,match='policy_generation_changed'):
            handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=handoff.CONFIRM,
                            now=NOW, reseal_postclose_source=True, freeze_operating_checklist=freeze)
        return
    prepared = handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=handoff.CONFIRM,
                               now=NOW, reseal_postclose_source=True, freeze_operating_checklist=freeze)
    assert prepared['status'] == 'pass' and receipt.read_bytes() == original
    if tamper == 'snapshot' and freeze:
        Path(prepared['handoff']['postclose_source_reseal']['operating_checklist']['path']).write_text('changed')
    elif tamper not in {'none','snapshot'}:
        (controller if tamper == 'controller' else checklist).write_text('changed')
    result = handoff.verify(DAY, NEW, now=NOW)
    assert result['status'] == ('pass' if tamper=='none' or (tamper=='checklist' and freeze) or (tamper=='snapshot' and not freeze) else 'fail')
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(days=1))["status"] == "fail"


def test_read_only_selection_does_not_relax_prepare_or_consume_cwd(fixture, monkeypatch):
    data, _, selected, prepare = fixture
    assert prepare()['status'] == 'pass'
    assert handoff.consume(DAY, pid=2, now=NOW)['status'] == 'pass'
    frozen = {str(path): path.read_bytes() for path in data.rglob('*') if path.is_file()}
    monkeypatch.setattr(handoff, '_selection', NATIVE_SELECTION)
    monkeypatch.setattr(handoff, 'selected_release', lambda workspace: (selected, NEW))
    monkeypatch.chdir(data.parent)
    with pytest.raises(ValueError, match='selected_root_required'):
        prepare()
    with pytest.raises(ValueError, match='selected_root_required'):
        handoff.consume(DAY, pid=2, now=NOW)
    assert handoff.verify(DAY, NEW, now=NOW + timedelta(hours=2))['status'] == 'pass'
    assert all(Path(path).read_bytes() == value for path, value in frozen.items())


@pytest.mark.parametrize('damage', [None, 'status', 'schema', 'pid', 'start_ticks',
                                  'root', 'date', 'commit', 'not_consumed', 'handoff',
                                  'manifest_binding', 'env', 'prepared'])
def test_second_same_day_handoff_requires_exact_live_predecessor_and_sealed_generation(fixture, monkeypatch, damage):
    data, previous, selected, prepare = fixture
    index_file = data / 'runtime/policy_bootstrap/prepared' / DAY / 'latest.json'
    index = handoff._read(index_file)
    receipt = Path(index['receipt_path'])
    policies = [dict(family='main', path=str(handoff.bootstrap.env_path(DAY)),
                     sha256=handoff._sha(handoff.bootstrap.env_path(DAY)))]
    _json(receipt, dict(schema='next_preopen_readiness_v1', status='prepared_verified',
                       source_date='2026-10-01', target_date=DAY,
                       actual_pid_consumed=False, policy_receipts=policies))
    _json(index_file, dict(index, receipt_sha256=handoff._sha(receipt)))
    assert prepare()['status'] == 'pass'
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    prior_consumed = handoff._paths(DAY, NEW)[1]
    if damage in ('status', 'schema', 'root', 'date', 'commit', 'not_consumed', 'handoff', 'manifest_binding'):
        field, value = {
            'status': ('status', 'fail'), 'schema': ('schema', 'wrong'),
            'root': ('release_root', '/wrong'), 'date': ('target_date', '2026-10-01'),
            'commit': ('selected_release_commit', OLD), 'not_consumed': ('actual_pid_consumed', False),
            'handoff': ('handoff_sha256', 'wrong'), 'manifest_binding': ('manifest_sha256', 'wrong'),
        }[damage]
        _json(prior_consumed, dict(consumed, **{field: value}))
    elif damage in ('pid', 'start_ticks'):
        identity = dict(consumed['pid_identity'])
        identity['pid' if damage == 'pid' else 'start_ticks'] = 99 if damage == 'pid' else '99'
        _json(prior_consumed, dict(consumed, pid_identity=identity))
    elif damage == 'env':
        handoff.bootstrap.env_path(DAY).write_text('changed')
    elif damage == 'prepared':
        receipt.write_text(receipt.read_text() + ' ')
    new_root = selected.parent / 'second'
    new_root.mkdir()
    second_commit = 'c' * 40
    monkeypatch.setattr(handoff, '_selection', lambda **kwargs: (new_root, second_commit))
    monkeypatch.setattr(handoff.subprocess, 'check_output', lambda command, **kwargs:
                        NEW + '\n' if 'rev-parse' in command else '')
    monkeypatch.setattr(handoff, '_identity', lambda pid:
                        dict(pid=pid, start_ticks='42', cwd=str((selected if pid == 2 else new_root) / 'src')))
    controller = data / 'report/postclose_done_controller/postclose_done_controller_2026-10-01.json'
    summary = data / 'report/runtime_approval_summary/runtime_approval_summary_2026-10-01.json'
    _json(controller, dict(status='done')); _json(summary, dict(status='verified'))
    checklist = data.parent / 'docs/checklists' / f'{DAY}-stage2-todo-checklist.md'
    checklist.parent.mkdir(parents=True); checklist.write_text('same current owner')
    calls = []
    def sealed_source(source_day, target, *, generation_only=False):
        # The full dynamic selector cannot consume the second PID before it
        # launches. Reuse its unchanged native whole-chain generation instead.
        assert generation_only is True
        calls.append((source_day, target))
        return dict(controller_path=str(controller), controller_sha256=handoff._sha(controller),
                    summary_path=str(summary), summary_sha256=handoff._sha(summary), policy_receipts=policies)
    monkeypatch.setattr(readiness, '_source_receipts', sealed_source)
    before = {str(path): path.read_bytes() for path in (receipt, index_file,
              handoff.bootstrap.env_path(DAY), handoff.bootstrap.manifest_path(DAY), handoff._preopen_path(DAY))}
    if damage is not None:
        with pytest.raises(ValueError, match='intraday_'):
            handoff.prepare(DAY, old_pid=2, previous_root=selected, confirm=handoff.CONFIRM,
                            now=NOW + timedelta(minutes=2), reseal_postclose_source=True)
        assert not handoff._paths(DAY, second_commit)[0].exists()
        return
    result = handoff.prepare(DAY, old_pid=2, previous_root=selected, confirm=handoff.CONFIRM,
                            now=NOW + timedelta(minutes=2), reseal_postclose_source=True)
    assert result['status'] == 'pass' and calls == [('2026-10-01', DAY)]
    assert handoff.consume(DAY, pid=3, now=NOW + timedelta(minutes=3))['actual_pid_consumed'] is True
    assert all(Path(path).read_bytes() == content for path, content in before.items())


@pytest.mark.parametrize('damage', [None, 'summary', 'consumption', 'policy'])
def test_resealed_postclose_accepts_actual_new_pid_without_rewriting_original_summary(fixture, monkeypatch, damage):
    from src.engine.automation import postclose_summary_handoff as postclose

    data, previous, selected, _ = fixture
    bootstrap = handoff.bootstrap
    monkeypatch.setattr(bootstrap, 'DATA_DIR', data)
    source_day = '2026-10-01'
    original_env = bootstrap.env_path(DAY).read_bytes()
    root = data/'runtime/policy_bootstrap'
    root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(bootstrap, 'env_path', lambda day: root/f'runtime_policy_bootstrap_{day}.env')
    monkeypatch.setattr(bootstrap, 'manifest_path', lambda day: root/f'runtime_policy_bootstrap_{day}.json')
    bootstrap.env_path(DAY).write_bytes(original_env)
    manifest_file, env_file = bootstrap.manifest_path(DAY), bootstrap.env_path(DAY)
    # Keep real dated manifest/env validation and the native consumed-PID
    # binding; only process identity and the preexisting DONE source fixture
    # are substituted by the surrounding startup fixture.
    manifest = dict(target_date=DAY, selected_release_sha=OLD,
        source_incumbent_target_date=source_day, selected_families=[],
        direct_family_receipts=[], env_file=str(env_file), env_sha256=handoff._sha(env_file))
    manifest['manifest_sha256'] = bootstrap._digest_json(manifest)
    _json(manifest_file, manifest)
    monkeypatch.setattr(bootstrap, 'verify_bootstrap', lambda *a, **k:
        dict(status='pass', passed=True, findings=[], manifest_sha256=manifest['manifest_sha256']))
    selection_file = data/'runtime/runtime_release_selection.json'
    _json(selection_file, dict(schema='runtime_release_selection_v1', git_commit=NEW, release_root=str(selected)))
    verification_file = bootstrap.verify_path(DAY)
    verification = dict(target_date=DAY, status='pass', passed=True, pid=1,
        pid_passed=True, pid_env_available=True, manifest_sha256=manifest['manifest_sha256'])
    _json(verification_file, verification)
    controller = data/'report/postclose_done_controller'/f'postclose_done_controller_{source_day}.json'
    summary_file = data/'report/runtime_approval_summary'/f'runtime_approval_summary_{source_day}.json'
    _json(controller, dict(status='done'))
    summary = dict(date=source_day, preopen_consumption_state='verified',
        preopen_consumption_receipt=dict(source_date=source_day, apply_date=DAY,
            manifest_path=str(manifest_file), manifest_sha256=handoff._sha(manifest_file),
            verification_path=str(verification_file), verification_sha256=handoff._sha(verification_file),
            release_selection_sha256='old', selected_release_commit=OLD))
    _json(summary_file, summary)
    checklist = data.parent/'docs/checklists'/f'{DAY}-stage2-todo-checklist.md'
    checklist.parent.mkdir(parents=True); checklist.write_text('current owner')
    policies = [dict(family='main', path=str(manifest_file), sha256=handoff._sha(manifest_file))]
    source = dict(controller_path=str(controller), controller_sha256=handoff._sha(controller),
        summary_path=str(summary_file), summary_sha256=handoff._sha(summary_file), policy_receipts=policies)
    monkeypatch.setattr(readiness, '_source_receipts', lambda *a, **k: source)
    index_file = data/'runtime/policy_bootstrap/prepared'/DAY/'latest.json'
    receipt = Path(json.loads(index_file.read_text())['receipt_path'])
    _json(receipt, dict(schema='next_preopen_readiness_v1', status='prepared_verified',
        source_date=source_day, target_date=DAY, actual_pid_consumed=False, policy_receipts=policies))
    _json(index_file, dict(receipt_path=str(receipt), receipt_sha256=handoff._sha(receipt)))
    before = {str(p): p.read_bytes() for p in (summary_file, controller, manifest_file, env_file, receipt)}
    handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=handoff.CONFIRM,
                    now=NOW, reseal_postclose_source=True)
    _json(verification_file, {**verification, 'pid': 2})
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    check = handoff.verify
    monkeypatch.setattr(handoff, 'verify', lambda day, commit: check(day, commit, now=NOW))
    # Launcher attestation legitimately changes selector bytes after consume.
    _json(selection_file, dict(schema='runtime_release_selection_v1', git_commit=NEW,
        release_root=str(selected), actual_pid_consumed=True))
    if damage == 'summary':
        summary_file.write_text(summary_file.read_text() + ' ')
    elif damage == 'consumption':
        _json(handoff._paths(DAY, NEW)[1], {**consumed, 'handoff_sha256': 'changed'})
    elif damage == 'policy':
        env_file.write_text('changed')
    result = postclose.inspect_future_handoff(summary, source_day, report_dir=data/'report')
    if damage is None:
        assert result['status'] == 'intraday_preserved_generation_pid_receipt_unconfirmed', result
        assert result['pid_receipt_present'] is True and result['actual_pid_consumed'] is False
        assert all(Path(p).read_bytes() == value for p, value in before.items())
        assert not (data/'runtime/policy_bootstrap/future_handoff_transitions').exists()
        from src.engine.scalping import mechanistic_entry_runtime_policy as machine
        monkeypatch.setattr(machine, 'load_effective', lambda **kw: {'valid': True})
        assert postclose.stage_overview(data/'report', source_day)['next_session_policy_ready'] is True
    else:
        assert result['status'] == 'stale', result


@pytest.mark.parametrize('damage', [
    None, 'manifest', 'env', 'verification', 'pid', 'consumption', 'missing_consumption', 'next_day',
])
def test_postclose_generation_accepts_only_native_preserved_intraday_pid(fixture, monkeypatch, damage):
    data, _, selected, prepare = fixture
    bootstrap = handoff.bootstrap
    monkeypatch.setattr(bootstrap, 'DATA_DIR', data)
    manifest = {'target_date': DAY, 'selected_release_sha': OLD,
                'manifest_sha256': 'policy-unchanged'}
    _json(bootstrap.manifest_path(DAY), manifest)
    assert prepare()['status'] == 'pass'
    consumed = handoff.consume(DAY, pid=2, now=NOW)
    assert consumed['actual_pid_consumed'] is True
    selection = {'schema': 'runtime_release_selection_v1', 'git_commit': NEW,
                 'release_root': str(selected)}
    _json(data / 'runtime/runtime_release_selection.json', selection)
    verification = {'target_date': DAY, 'status': 'pass', 'passed': True,
                    'pid': 2, 'pid_passed': True, 'pid_env_available': True}
    _json(bootstrap.verify_path(DAY), verification)
    check = handoff.verify
    clock = NOW + timedelta(days=1) if damage == 'next_day' else NOW
    monkeypatch.setattr(handoff, 'verify', lambda day, commit: check(day, commit, now=clock))
    if damage == 'manifest':
        _json(bootstrap.manifest_path(DAY), {**manifest, 'changed': True})
    elif damage == 'env':
        bootstrap.env_path(DAY).write_text('POLICY=changed\n')
    elif damage == 'verification':
        _json(bootstrap.verify_path(DAY), {**verification, 'pid': 1})
    elif damage == 'pid':
        verification['pid'] = 1
        _json(bootstrap.verify_path(DAY), verification)
    elif damage == 'consumption':
        _json(handoff._paths(DAY, NEW)[1], {**consumed, 'handoff_sha256': 'changed'})
    elif damage == 'missing_consumption':
        handoff._paths(DAY, NEW)[1].unlink()
    result = bootstrap.release_selection_for_generation(data, manifest, verification)
    if damage is None:
        assert result['status'] == 'intraday_preserved', result
        assert result['selection']['git_commit'] == NEW
        assert result['original_manifest_release_commit'] == OLD
    else:
        assert result['status'] == 'invalid', result


@pytest.mark.parametrize("mutation", ["env", "manifest", "preopen", "prepared", "commit", "ttl", "consumption"])
def test_intraday_handoff_rejects_changed_generation_identity_and_expired_launch(fixture, mutation):
    data, _, _, prepare = fixture
    assert prepare()["status"] == "pass"
    current = NOW
    commit = NEW
    if mutation == "env":
        handoff.bootstrap.env_path(DAY).write_text("export POLICY=changed\n")
    elif mutation == "manifest":
        _json(handoff.bootstrap.manifest_path(DAY), {"policy": "changed"})
    elif mutation == "preopen":
        _json(handoff._preopen_path(DAY), {"status": "failed"})
    elif mutation == "prepared":
        _json(data / "runtime/policy_bootstrap/prepared" / DAY / "latest.json", {})
    elif mutation == "commit":
        commit = OLD
    elif mutation == "ttl":
        current += timedelta(minutes=16)
    elif mutation == "consumption":
        _json(handoff._paths(DAY, NEW)[1], {"actual_pid_consumed": True})
    assert handoff.verify(DAY, commit, now=current)["status"] == "fail"


@pytest.mark.parametrize("fault", ["authority", "native_fail", "old_pid", "preopen_fail", "next_day", "dirty"])
def test_intraday_prepare_rejects_missing_authority_or_native_custody(fixture, monkeypatch, fault):
    _, previous, _, _ = fixture
    confirm, current = handoff.CONFIRM, NOW
    if fault == "authority":
        confirm = ""
    elif fault == "native_fail":
        monkeypatch.setattr(handoff.bootstrap, "verify_bootstrap", lambda *args, **kwargs:
                            {"status": "fail", "findings": ["source_receipt_hash_mismatch"]})
    elif fault == "old_pid":
        monkeypatch.setattr(handoff, "_identity", lambda pid: {"pid": pid, "cwd": "/other/src"})
    elif fault == "preopen_fail":
        _json(handoff._preopen_path(DAY), {"status": "failed"})
    elif fault == "next_day":
        current += timedelta(days=1)
    elif fault == "dirty":
        monkeypatch.setattr(handoff.subprocess, "check_output", lambda command, **kwargs:
                            OLD if "rev-parse" in command else " M src/runtime.py")
    with pytest.raises((ValueError, KeyError)):
        handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=confirm, now=current)
    assert not handoff._paths(DAY, NEW)[0].exists()


def test_intraday_receipt_immutable_and_old_pid_cannot_claim_new_consumption(fixture):
    _, _, _, prepare = fixture
    prepare()
    with pytest.raises(FileExistsError):
        prepare()
    with pytest.raises(ValueError, match="new_pid_root_invalid"):
        handoff.consume(DAY, pid=1, now=NOW)


def test_changed_commit_without_intraday_receipt_does_not_admit_launcher(fixture):
    assert readiness.verify_preopen_completion(DAY, NEW, now=NOW)["status"] == "fail"
    assert readiness.verify_preopen_completion(DAY, OLD, now=NOW)["status"] == "pass"


def test_prepared_verifier_preserves_original_receipt_and_checks_sources(fixture, monkeypatch):
    data, _, selected, prepare = fixture
    prepared_root = data / "runtime/policy_bootstrap/prepared" / DAY
    monkeypatch.setattr(readiness, "PREPARED_DIR", prepared_root.parent)
    source = {"source_proof": "unchanged"}
    monkeypatch.setattr(readiness, "_source_receipts", lambda *args, **kwargs: source)
    selection = data / "runtime/runtime_release_selection.json"
    _json(selection, {"git_commit": NEW, "release_root": str(selected)})
    monkeypatch.setattr(readiness, "_selected_release", lambda **kwargs: ({}, selection, NEW))
    live_env = handoff.bootstrap.env_path(DAY)
    live_manifest = handoff.bootstrap.manifest_path(DAY)
    monkeypatch.setattr(handoff.bootstrap, "env_path", lambda day, output_dir=None:
                        Path(output_dir) / "env" if output_dir else live_env)
    monkeypatch.setattr(handoff.bootstrap, "manifest_path", lambda day, output_dir=None:
                        Path(output_dir) / "manifest" if output_dir else live_manifest)
    receipt_path = prepared_root / "generation/readiness.json"
    output = receipt_path.parent
    for path in (output / "env", output / "manifest", handoff.bootstrap.verify_path(DAY, output_dir=output)):
        _json(path, {})
    receipt = {"schema": "next_preopen_readiness_v1", "status": "prepared_verified", "target_date": DAY,
               "source_date": "2026-09-30", "selected_release_commit": OLD, "selection_sha256": "old",
               "actual_pid_consumed": False, "runtime_effect": False, "manifest_content_sha256": "policy-unchanged",
               "manifest_file_sha256": handoff._sha(output / "manifest"), "env_sha256": handoff._sha(output / "env"),
               "verification_sha256": handoff._sha(handoff.bootstrap.verify_path(DAY, output_dir=output)), **source}
    _json(receipt_path, receipt)
    _json(prepared_root / "latest.json", {"target_date": DAY, "receipt_path": str(receipt_path),
                                          "receipt_sha256": handoff._sha(receipt_path)})
    prepare()
    result = readiness.verify_prepared(DAY, require_today=True, now=NOW)
    assert result["status"] == "pass"
    assert result["selected_release_commit"] == NEW and result["preserved_preopen_commit"] == OLD
    assert result["actual_pid_consumed"] is False
    monkeypatch.setattr(readiness, "_source_receipts", lambda *args, **kwargs: {"source_proof": "changed"})
    assert readiness.verify_prepared(DAY, now=NOW)["status"] == "fail"


def test_main_policy_activation_requires_actual_code_pid_and_new_authority(fixture,monkeypatch):
 _,_,_,prepare=fixture
 prepare();handoff.consume(DAY,pid=2,now=NOW)
 from src.engine.scalping import continuous_reversal_policy_v2 as policy
 calls=[]
 monkeypatch.setattr(policy,'activate',lambda *args,**kwargs:calls.append(kwargs) or dict(status='activated'))
 with pytest.raises(ValueError,match='explicit_authority'):
  handoff.activate_main_v2(DAY,pid=2,confirm=handoff.CONFIRM,now=NOW)
 assert not calls
 with pytest.raises(ValueError,match='pid_release'):
  handoff.activate_main_v2(DAY,pid=1,confirm='APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION',now=NOW)
 assert not calls
 result=handoff.activate_main_v2(DAY,pid=2,confirm='APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION',now=NOW)
 assert result['status']=='pass' and result['actual_policy_pid_consumption'] is False
 assert calls[0]['intraday_evidence']['pid_identity']['pid']==2


def test_v5_next_session_candidate_cannot_fall_through_to_intraday_v2(fixture,monkeypatch):
 data,_,_,prepare=fixture
 prepare();handoff.consume(DAY,pid=2,now=NOW)
 from src.engine.scalping import continuous_reversal_policy_v2 as policy
 monkeypatch.setattr(policy,'activate',lambda *a,**kw:pytest.fail('v5 reached v2 activation'))
 _json(data/'runtime/mechanistic_entry_policy/candidates'/f'policy_{DAY}.json',
       {'continuous_reversal':{'schema':'continuous_reversal_policy_v5'}})
 with pytest.raises(ValueError,match='requires_next_session_activation'):
  handoff.activate_main_v2(DAY,pid=2,confirm='APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION',now=NOW)

@pytest.mark.parametrize('damage', [None, 'git_bytes', 'snapshot', 'postclose_generated', 'generated_corrupt',
                                   'git_missing', 'git_missing_without_snapshot', 'git_missing_corrupt_snapshot'])
def test_authorized_intraday_historical_checklist_is_exact_git_bound_snapshot(fixture, monkeypatch, damage):
    data, previous, _, _ = fixture
    source_day='2026-10-01'
    original=b'original verified checklist\n'
    checklist=data.parent/'docs/checklists'/f'{DAY}-stage2-todo-checklist.md'
    checklist.parent.mkdir(parents=True); checklist.write_text('current work added\n')
    strict=data/'strict.json'
    _json(strict, {'checklist_handoff':{'path':str(checklist)},
                  'generation_binding':{'checklist_sha256':__import__('hashlib').sha256(original).hexdigest()}})
    controller=data/'report/postclose_done_controller'/f'postclose_done_controller_{source_day}.json'
    summary=data/'report/runtime_approval_summary'/f'runtime_approval_summary_{source_day}.json'
    _json(controller, {'verification_attempt_path':str(strict)});_json(summary, {'date':source_day})
    index_file=data/'runtime/policy_bootstrap/prepared'/DAY/'latest.json'
    index=handoff._read(index_file);receipt=Path(index['receipt_path'])
    policies=[{'family':'main','path':'/unchanged.json','sha256':'d'*64}]
    _json(receipt, {'schema':'next_preopen_readiness_v1','status':'prepared_verified','target_date':DAY,
                   'source_date':source_day,'actual_pid_consumed':False,'policy_receipts':policies})
    _json(index_file, {'receipt_path':str(receipt),'receipt_sha256':handoff._sha(receipt)})
    if damage in {'postclose_generated','generated_corrupt','git_missing','git_missing_corrupt_snapshot'}:
        checklist.write_bytes(original)
        preserved=handoff.preserve_checklist(DAY)
        checklist.write_text('current work added\n')
        if damage in {'generated_corrupt','git_missing_corrupt_snapshot'}:Path(preserved['path']).write_text('corrupt')
    def output(command, **kwargs):
        if 'show' in command and str(damage).startswith('git_missing'):
            raise handoff.subprocess.CalledProcessError(128,command)
        if 'show' in command:return b'wrong' if damage in {'git_bytes','postclose_generated','generated_corrupt'} else original
        return OLD+'\n' if 'rev-parse' in command else ''
    monkeypatch.setattr(handoff.subprocess,'check_output',output)
    def source(*args, **kwargs):
        assert kwargs['generation_only'] is True
        assert Path(kwargs['checklist_snapshot']).read_bytes()==original
        return {'controller_path':str(controller),'controller_sha256':handoff._sha(controller),
                'summary_path':str(summary),'summary_sha256':handoff._sha(summary),'policy_receipts':policies}
    monkeypatch.setattr(readiness,'_source_receipts',source)
    if damage in {'git_bytes','generated_corrupt','git_missing_without_snapshot','git_missing_corrupt_snapshot'}:
        with pytest.raises(ValueError,match='git_generation_missing'):
            handoff.prepare(DAY,old_pid=1,previous_root=previous,confirm=handoff.CONFIRM,now=NOW,reseal_postclose_source=True)
        return
    result=handoff.prepare(DAY,old_pid=1,previous_root=previous,confirm=handoff.CONFIRM,now=NOW,reseal_postclose_source=True)
    assert result['status']=='pass'
    snap=Path(result['handoff']['postclose_source_reseal']['historical_checklist']['path'])
    if damage=='snapshot':
        snap.write_text('changed')
        assert handoff.verify(DAY,NEW,now=NOW)['status']=='fail'
    assert checklist.read_text()=='current work added\n'


@pytest.mark.parametrize('damage', [None, 'snapshot', 'consumed', 'git_bytes', 'predecessor_binding',
                                  'env_after_consumption', 'controller_after_consumption',
                                  'summary_after_consumption', 'snapshot_after_consumption',
                                  'consumption_missing_after_edit', 'removed_original_release',
                                  'removed_original_release_corrupt_snapshot'])
def test_second_handoff_carries_original_git_snapshot_with_consumed_custody(fixture, monkeypatch, damage):
    data, previous, selected, _ = fixture
    original = b'original sealed generation\n'
    checklist = data.parent/'docs/checklists'/f'{DAY}-stage2-todo-checklist.md'
    checklist.parent.mkdir(parents=True); checklist.write_text('new current owners\n')
    strict = data/'strict.json'
    expected = __import__('hashlib').sha256(original).hexdigest()
    original_path = checklist
    if damage in {'removed_original_release', 'removed_original_release_corrupt_snapshot'}:
        original_path = previous/'docs/checklists'/checklist.name
        original_path.parent.mkdir(parents=True)
        original_path.write_bytes(checklist.read_bytes())
    _json(strict, {'checklist_handoff': {'path': str(original_path)},
                  'generation_binding': {'checklist_sha256': expected}})
    controller = data/'report/postclose_done_controller/postclose_done_controller_2026-10-01.json'
    summary = data/'report/runtime_approval_summary/runtime_approval_summary_2026-10-01.json'
    _json(controller, {'verification_attempt_path': str(strict)}); _json(summary, {})
    index = data/'runtime/policy_bootstrap/prepared'/DAY/'latest.json'
    receipt = Path(handoff._read(index)['receipt_path']); policies = [{'family': 'main'}]
    _json(receipt, dict(schema='next_preopen_readiness_v1', status='prepared_verified', target_date=DAY,
        source_date='2026-10-01', actual_pid_consumed=False, policy_receipts=policies))
    _json(index, dict(receipt_path=str(receipt), receipt_sha256=handoff._sha(receipt)))
    def source(*args, **kwargs):
        assert Path(kwargs['checklist_snapshot']).read_bytes() == original
        return dict(controller_path=str(controller), controller_sha256=handoff._sha(controller),
                    summary_path=str(summary), summary_sha256=handoff._sha(summary), policy_receipts=policies)
    monkeypatch.setattr(readiness, '_source_receipts', source)
    monkeypatch.setattr(handoff.subprocess, 'check_output', lambda command, **kwargs:
        original if 'show' in command else OLD+'\n' if 'rev-parse' in command else '')
    handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=handoff.CONFIRM,
                    now=NOW, reseal_postclose_source=True)
    handoff.consume(DAY, pid=2, now=NOW)
    prior_path, consumed_path = handoff._paths(DAY, NEW)
    snapshot = prior_path.parent/(NEW+'.historical-checklist.md')
    if damage in {'removed_original_release', 'removed_original_release_corrupt_snapshot'}:
        original_path.unlink()
    if damage == 'removed_original_release_corrupt_snapshot': snapshot.write_text('changed')
    if damage == 'snapshot': snapshot.write_text('changed')
    if damage == 'consumed':
        _json(consumed_path, {**handoff._read(consumed_path), 'actual_pid_consumed': False})
    second = selected.parent/'second'; second.mkdir(); commit = 'c'*40
    monkeypatch.setattr(handoff, '_selection', lambda **kwargs: (second, commit))
    monkeypatch.setattr(handoff, '_identity', lambda pid:
        dict(pid=pid, start_ticks='42', cwd=str((selected if pid == 2 else second)/'src')))
    def git_output(command, **kwargs):
        if 'show' in command:
            # NEW contains the edited checklist, so only the original OLD
            # Git object is valid evidence for a repeated handoff.
            assert command[-1].startswith(OLD+':')
            return b'wrong bytes' if damage == 'git_bytes' else original
        return NEW+'\n' if 'rev-parse' in command else ''
    monkeypatch.setattr(handoff.subprocess, 'check_output', git_output)
    if damage in {'snapshot', 'consumed', 'git_bytes', 'removed_original_release_corrupt_snapshot'}:
        with pytest.raises(ValueError, match='intraday_'):
            handoff.prepare(DAY, old_pid=2, previous_root=selected, confirm=handoff.CONFIRM,
                            now=NOW+timedelta(minutes=2), reseal_postclose_source=True)
        assert not handoff._paths(DAY, commit)[0].exists()
        return
    result = handoff.prepare(DAY, old_pid=2, previous_root=selected, confirm=handoff.CONFIRM,
                            now=NOW+timedelta(minutes=2), reseal_postclose_source=True)
    historical = result['handoff']['postclose_source_reseal']['historical_checklist']
    assert historical['git_commit'] == OLD
    assert Path(historical['path']).read_bytes() == original
    if damage == 'predecessor_binding':
        _json(consumed_path, {**handoff._read(consumed_path), 'handoff_sha256': 'wrong'})
        assert handoff.verify(DAY, commit, now=NOW+timedelta(minutes=2))['status'] == 'fail'
    else:
        assert handoff.consume(DAY, pid=3, now=NOW+timedelta(minutes=2))['status'] == 'pass'
        # Current work can change after launch. It cannot invalidate the sealed
        # historical DONE, or grant permission to launch/apply a fresh policy.
        checklist.write_text('additional current intraday work\n')
        assert handoff.verify(DAY, commit, now=NOW+timedelta(minutes=3))['status'] == 'fail'
        assert handoff.consume(DAY, pid=3, now=NOW+timedelta(minutes=3))['status'] == 'fail'
        with pytest.raises(ValueError, match='intraday_main_policy_code_consumption_missing'):
            handoff.activate_main_v2(DAY, pid=3, confirm='APPROVED_INTRADAY_MAIN_POLICY_ACTIVATION',
                                    now=NOW+timedelta(minutes=3))
        damaged_path = {
            'env_after_consumption': handoff.bootstrap.env_path(DAY),
            'controller_after_consumption': controller,
            'summary_after_consumption': summary,
            'snapshot_after_consumption': Path(historical['path']),
            'consumption_missing_after_edit': handoff._paths(DAY, commit)[1],
        }.get(damage)
        if damaged_path:
            if damage == 'consumption_missing_after_edit': damaged_path.unlink()
            else: damaged_path.write_text('changed')
            with pytest.raises(ValueError, match='intraday_observer_'):
                handoff.historical_checklist_for_observer(
                    data.parent, '2026-10-01', now=NOW+timedelta(minutes=3))
            return
        observer = handoff.historical_checklist_for_observer(
            data.parent, '2026-10-01', now=NOW+timedelta(minutes=3))
        assert observer['path'] == historical['path']
        assert observer['pid_identity']['pid'] == 3
        assert observer['runtime_effect'] is False and observer['new_finalization_claimed'] is False
        for project, source in [(data.parent.parent, '2026-10-01'), (data.parent, DAY)]:
            with pytest.raises(ValueError, match='intraday_observer_'):
                handoff.historical_checklist_for_observer(project, source, now=NOW+timedelta(minutes=3))
        consumed_path = handoff._paths(DAY, commit)[1]
        consumed = handoff._read(consumed_path)
        for field, value in [('status', 'fail'), ('schema', 'wrong'), ('manifest_sha256', 'changed')]:
            _json(consumed_path, {**consumed, field: value})
            with pytest.raises(ValueError, match='intraday_observer_'):
                handoff.historical_checklist_for_observer(data.parent, '2026-10-01', now=NOW+timedelta(minutes=3))
        _json(consumed_path, consumed)
        handoff_path = handoff._paths(DAY, commit)[0]
        original_handoff = handoff_path.read_bytes()
        original_bootstrap = handoff._checked_bootstrap
        def changing_bootstrap(*args):
            checked = original_bootstrap(*args)
            handoff_path.write_bytes(original_handoff + b' ')
            return checked
        monkeypatch.setattr(handoff, '_checked_bootstrap', changing_bootstrap)
        with pytest.raises(ValueError, match='intraday_observer_pid_generation_changed'):
            handoff.historical_checklist_for_observer(data.parent, '2026-10-01', now=NOW+timedelta(minutes=3))
        handoff_path.write_bytes(original_handoff)
        monkeypatch.setattr(handoff, '_checked_bootstrap', original_bootstrap)
        monkeypatch.setattr(handoff, '_identity', lambda pid:
            dict(pid=pid, start_ticks='reused-pid', cwd=str(second/'src')))
        with pytest.raises(ValueError, match='intraday_observer_current_pid_not_bound'):
            handoff.historical_checklist_for_observer(data.parent, '2026-10-01', now=NOW+timedelta(minutes=3))


@pytest.mark.parametrize('consumer,approval', [('sniper_state_handlers.py','machine_auxiliary_path_repair_deploy_and_restart'), ('ai_engine_openai.py','entry_input_deadline_repair_deploy_and_restart'), ('monitoring/submission_bottleneck_monitor.py','ordered_intraday_deploy_and_restart')])
@pytest.mark.parametrize('identity_mode', ['live', 'stopped', 'unbound_stopped', 'stopped_still_alive'])
@pytest.mark.parametrize('fault', [None, 'authority', 'consumed', 'pid', 'manifest', 'policy', 'producer', 'other_function', 'verifier'])
def test_entry_consumer_repair_can_verify_before_own_handoff_without_relaxing_sources(fixture, monkeypatch, fault, consumer, approval, identity_mode):
    import hashlib
    data, previous, selected, _ = fixture
    monkeypatch.setattr(handoff, '_today', lambda *a: NOW)
    name = 'src/engine/' + consumer
    own = 'src/engine/automation/intraday_release_handoff.py'
    function = {'sniper_state_handlers.py': '_get_live_entry_arm',
                'ai_engine_openai.py': '_final_entry_machine_inputs',
                'monitoring/submission_bottleneck_monitor.py': '_reversal_lifecycle_diagnostic'}[consumer]
    original = ('def '+function+'():\n return 1\ndef hard_guard():\n return False\n').encode()
    revised = original.replace(b'return 1', b'return 2')
    if fault == 'other_function': revised = revised.replace(b'return False', b'return True')
    if fault == 'producer': name = 'src/engine/producer.py'
    for n, raw in [(name, revised), (own, b'# reviewed verifier\n')]:
        p = selected/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    monkeypatch.setattr(handoff, '__file__', str(selected/own))
    if fault == 'verifier':(selected/own).write_bytes(b'# dirty verifier\n')
    def git(cmd, **kw):
        rev, path = cmd[-1].split(':',1)
        return b'# reviewed verifier\n' if path == own else original if rev == OLD else revised
    monkeypatch.setattr(handoff.subprocess, 'check_output', git)
    expected = hashlib.sha256(json.dumps({name: hashlib.sha256(original).hexdigest()},
        sort_keys=True,separators=(',',':')).encode()).hexdigest()
    manifest = dict(selected_release_sha=OLD, manifest_sha256='sealed-manifest',
        pre_submit_delay_handoff=dict(policy_sha256='policy',code_contract_sha256=expected,target_date=DAY))
    _json(handoff.bootstrap.manifest_path(DAY), manifest)
    selection = dict(previous_git_commit=OLD,previous_release_root=str(previous),approved_by='user',
        approval_scope='wrong' if fault=='authority' else approval)
    _json(data/'runtime/runtime_release_selection.json',selection)
    prior_path, consumed_path=handoff._paths(DAY,OLD)
    prior=dict(schema='intraday_policy_preserving_release_handoff_v1',status='prepared_verified',authority=handoff.CONFIRM,
        target_date=DAY,selected_release_commit=OLD,release_root=str(previous),frozen_files={str(p):handoff._sha(p)
            for p in [handoff.bootstrap.manifest_path(DAY),handoff.bootstrap.env_path(DAY),handoff._preopen_path(DAY)]})
    _json(prior_path,prior)
    consumed=dict(schema='intraday_policy_preserving_consumption_v1',status='pass',actual_pid_consumed=fault!='consumed',
        target_date=DAY,selected_release_commit=OLD,release_root=str(previous),manifest_sha256='sealed-manifest',
        handoff_sha256=handoff._sha(prior_path),pid_identity=handoff._identity(1))
    if fault=='pid':consumed['pid_identity']['pid']=99
    _json(consumed_path,consumed)
    if fault=='manifest':handoff.bootstrap.env_path(DAY).write_text('mutated')
    kwargs=dict(family='pre_submit_delay',policy_sha='wrong' if fault=='policy' else 'policy',
        expected=expected,paths={name:name},actual='new')
    token = handoff._STOPPED_PREPARATION.set(
        (DAY, 1, str(previous)) if identity_mode in {'stopped', 'stopped_still_alive'} else None)
    exists=Path.exists
    monkeypatch.setattr(Path,'exists',lambda p:
        identity_mode=='stopped_still_alive' if str(p)=='/proc/1' else exists(p))
    if identity_mode != 'live':
        def dead(pid):raise ValueError('predecessor_not_live')
        monkeypatch.setattr(handoff,'_identity',dead)
    try:
        if fault or identity_mode in {'unbound_stopped','stopped_still_alive'}:
            with pytest.raises(ValueError):handoff.verify_entry_consumer_code(DAY,**kwargs)
        else:
            proof=handoff.verify_entry_consumer_code(DAY,**kwargs)
            assert proof['policy_effect']=='unchanged' and proof['changed_consumer_paths']==[name]
            assert not handoff._paths(DAY,NEW)[0].exists()
    finally:
        handoff._STOPPED_PREPARATION.reset(token)


def test_stopped_preparation_context_cannot_escape_success_or_failure(fixture, monkeypatch):
    _, previous, _, _=fixture
    def check(*args,**kw):
        assert handoff._STOPPED_PREPARATION.get()==(DAY,1,str(previous))
        return {'status':'pass'}
    monkeypatch.setattr(handoff,'_prepare',check)
    assert handoff.prepare(DAY,old_pid=1,previous_root=previous,confirm=handoff.CONFIRM,
                           previous_stopped=True)['status']=='pass'
    assert handoff._STOPPED_PREPARATION.get() is None
    def reject(*args,**kw):
        check();raise ValueError('prepare_failure')
    monkeypatch.setattr(handoff,'_prepare',reject)
    with pytest.raises(ValueError,match='prepare_failure'):
        handoff.prepare(DAY,old_pid=1,previous_root=previous,confirm=handoff.CONFIRM,previous_stopped=True)
    assert handoff._STOPPED_PREPARATION.get() is None


def test_observer_context_never_relaxes_public_launch_verification(fixture, monkeypatch):
    calls=[]
    def verify(*a,**kw):
        calls.append(kw.get('historical_observer',False));return {'status':'fail'}
    monkeypatch.setattr(handoff,'_verify_handoff',verify)
    token=handoff._OBSERVER_CUSTODY.set((DAY,NEW))
    try:
        assert handoff.verify(DAY,NEW)['status']=='fail'
        assert calls==[False]
    finally:handoff._OBSERVER_CUSTODY.reset(token)


def test_cli_and_nested_policy_readers_share_canonical_context(monkeypatch):
    import runpy
    import sys
    called=[]
    monkeypatch.setattr(sys,'argv',['intraday-release-handoff'])
    monkeypatch.setattr(handoff,'main',lambda:called.append('canonical') or 0)
    with pytest.warns(RuntimeWarning,match='found in sys.modules'):
        with pytest.raises(SystemExit) as result:
            runpy.run_module(handoff.__name__,run_name='__main__')
    assert result.value.code==0 and called==['canonical']


@pytest.mark.parametrize('fault', [None, 'other_function', 'producer', 'dirty', 'verifier',
                                   'hash', 'date', 'origin'])
def test_candidate_delay_code_is_checked_without_selection_or_runtime_mutation(fixture, monkeypatch, fault):
    import hashlib
    from src.engine.scalping import pre_submit_delay_initial_policy as policy
    data, _, selected, _ = fixture
    monkeypatch.setattr(handoff, '_today', lambda *a: NOW)
    name = 'src/engine/monitoring/submission_bottleneck_monitor.py'
    own = 'src/engine/automation/intraday_release_handoff.py'
    original = b'def _reversal_lifecycle_diagnostic(row):\n return None\ndef qualify_delay(row):\n return False\n'
    revised = original.replace(b'return None', b'return "diagnostic"')
    if fault == 'other_function': revised = revised.replace(b'return False', b'return True')
    if fault == 'producer': name = 'src/engine/scalping/pre_submit_delay_initial_policy.py'
    for path, content in ((name, revised), (own, b'# reviewed\n')):
        f = selected/path; f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(content)
    monkeypatch.setattr(handoff, '__file__', str(selected/own))
    monkeypatch.setattr(policy, 'CONTRACT_PATHS', (name,))
    monkeypatch.setattr(handoff, '_selection', lambda **kw: pytest.fail('must not select candidate'))
    monkeypatch.setattr(handoff, '_identity', lambda *a: pytest.fail('must not touch process'))
    monkeypatch.setattr(handoff.subprocess, 'check_output', lambda command, **kw:
        b'# reviewed\n' if command[-1].endswith(':'+own) else original if command[-1].startswith(OLD+':') else revised)
    expected = hashlib.sha256(json.dumps({name: hashlib.sha256(original).hexdigest()},
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    _json(handoff.bootstrap.manifest_path(DAY), dict(selected_release_sha=NEW if fault=='origin' else OLD,
        pre_submit_delay_handoff=dict(status='verified_initial_timing_policy',
            target_date='wrong' if fault=='date' else DAY, code_contract_sha256='wrong' if fault=='hash' else expected)))
    if fault == 'dirty': (selected/name).write_bytes(revised+b'# uncommitted\n')
    if fault == 'verifier': (selected/own).write_bytes(b'# uncommitted\n')
    before = {p: p.read_bytes() for p in data.parent.parent.rglob('*') if p.is_file()}
    if fault:
        with pytest.raises(ValueError): handoff.verify_candidate_delay_code(DAY, selected, NEW)
    else:
        result = handoff.verify_candidate_delay_code(DAY, selected, NEW)
        assert result['status'] == 'pass' and result['actual_pid_consumed'] is False
        assert result['changed_consumer_paths'] == [name]
    assert before == {p: p.read_bytes() for p in data.parent.parent.rglob('*') if p.is_file()}


@pytest.mark.parametrize('fault', [None, 'root', 'origin', 'date', 'bundle', 'path', 'successor', 'unreviewed', 'absent_receipt'])
def test_candidate_holding_vote_pin_is_checked_before_selection(fixture, monkeypatch, fault):
    from src.engine.scalping import holding_path_vote_policy as V, holding_vote_experiment as E
    data, _, selected, _ = fixture
    monkeypatch.setattr(handoff, '_today', lambda *a: NOW)
    monkeypatch.setattr(handoff, '__file__', str(selected/'src/engine/automation/intraday_release_handoff.py'))
    monkeypatch.setattr(handoff, '_selection', lambda **kw: pytest.fail('no selector mutation or dependency'))
    bundle=dict(schema=V.SUCCESSOR_SCHEMA,bundle_sha256='b'*64,code_sha256='c'*64,
                selection_mode='validated_successor' if fault=='successor' else 'incumbent_carry')
    def load(root, day, *, require_current_code):
        assert root==data and day==DAY and require_current_code is False
        return bundle
    monkeypatch.setattr(V,'load_bundle',load)
    monkeypatch.setattr(E,'code_sha',lambda:'d'*64)
    checked=[]
    def check(root, commit, origin, paths, expected):
        assert root==selected and commit==NEW and origin==OLD and expected=='c'*64
        assert paths['lifecycle/holding_window_generation.py']=='src/engine/lifecycle/holding_window_generation.py'
        checked.append(True)
        if fault=='unreviewed':raise ValueError('entry_consumer_producer_changed')
        return ['src/engine/lifecycle/holding_window_generation.py']
    monkeypatch.setattr(handoff,'_verify_entry_code_delta',check)
    bound=dict(allowed_runtime_apply=True,target_date='wrong' if fault=='date' else DAY,
               bundle_sha256='wrong' if fault=='bundle' else 'b'*64,
               path='/wrong' if fault=='path' else str(V.policy_path(data,DAY)))
    _json(handoff.bootstrap.manifest_path(DAY),dict(selected_release_sha=NEW if fault=='origin' else OLD,
          holding_path_vote_policy_receipt={} if fault=='absent_receipt' else bound))
    before={p:p.read_bytes() for p in data.rglob('*') if p.is_file()}
    if fault:
        with pytest.raises(ValueError):handoff.verify_candidate_holding_vote_code(DAY,data if fault=='root' else selected,NEW)
    else:
        result=handoff.verify_candidate_holding_vote_code(DAY,selected,NEW)
        assert result['status']=='pass' and result['actual_pid_consumed'] is False and checked
    assert before=={p:p.read_bytes() for p in data.rglob('*') if p.is_file()}


@pytest.mark.parametrize('damage',[None,'status','schema','pid','manifest','handoff','policy'])
def test_existing_consumption_proof_is_live_and_immutable(fixture,monkeypatch,damage):
    data,_,_,prepare=fixture
    assert prepare()['status']=='pass'
    assert handoff.consume(DAY,pid=2,now=NOW)['status']=='pass'
    path,consumed_path=handoff._paths(DAY,NEW);body=handoff._read(consumed_path)
    if damage=='status':body['status']='fail'
    elif damage=='schema':body['schema']='foreign'
    elif damage=='pid':body['pid_identity']['start_ticks']='reused'
    elif damage=='manifest':body['manifest_sha256']='changed'
    elif damage=='handoff':body['handoff_sha256']='changed'
    elif damage=='policy':handoff.bootstrap.env_path(DAY).write_text('changed')
    _json(consumed_path,body)
    checked=handoff._verify_consumed_handoff(DAY,NEW,now=NOW)
    assert checked['status']==('pass' if damage is None else 'fail')


@pytest.mark.parametrize('raises',[False,True])
def test_candidate_predecessor_review_context_cannot_escape(fixture,monkeypatch,raises):
    from src.engine.infrastructure import runtime_release_router as router
    data,previous,candidate,_=fixture
    monkeypatch.setattr(handoff,'__file__',str(candidate/'src/engine/automation/intraday_release_handoff.py'))
    monkeypatch.setattr(handoff,'_selection',lambda **kw:(previous,OLD))
    monkeypatch.setattr(router,'git',lambda *args:NEW)
    monkeypatch.setattr(router,'validate_release',lambda *args:(candidate,NEW))
    def read(day,*,pid):
        scope=handoff._PREDECESSOR_REVIEW.get()
        assert scope['root']==previous and scope['commit']==OLD and scope['code_root']==candidate
        assert scope['identity']==handoff._identity(pid)
        if raises:raise ValueError('unverified_native_source')
        return dict(status='pass')
    monkeypatch.setattr(handoff,'verify_pid_consumption',read)
    if raises:
        with pytest.raises(ValueError,match='unverified_native_source'):
            handoff.verify_predecessor_consumption(DAY,pid=1)
    else:
        result=handoff.verify_predecessor_consumption(DAY,pid=1)
        assert result['runtime_effect'] is False and result['candidate_pid_consumed'] is False
        assert result['verification_code_commit']==NEW
    assert handoff._PREDECESSOR_REVIEW.get() is None
