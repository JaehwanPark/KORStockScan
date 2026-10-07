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


def _json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


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


@pytest.mark.parametrize('tamper', ['none', 'policy', 'controller', 'checklist'])
def test_intraday_current_document_reseal_preserves_original_preopen_generation(fixture, monkeypatch, tamper):
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
                            now=NOW, reseal_postclose_source=True)
        return
    prepared = handoff.prepare(DAY, old_pid=1, previous_root=previous, confirm=handoff.CONFIRM,
                               now=NOW, reseal_postclose_source=True)
    assert prepared['status'] == 'pass' and receipt.read_bytes() == original
    if tamper != 'none':
        (controller if tamper == 'controller' else checklist).write_text('changed')
    result = handoff.verify(DAY, NEW, now=NOW)
    assert result['status'] == ('pass' if tamper=='none' else 'fail')
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
        from src.engine.automation import low_price_two_leg_auto_expansion_policy as episode
        monkeypatch.setattr(machine, 'load_effective', lambda **kw: {'valid': True})
        monkeypatch.setattr(episode, 'load_policy', lambda *a, **kw: {'valid': True})
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
    monkeypatch.setattr(readiness, "_selected_release", lambda: ({}, selection, NEW))
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
