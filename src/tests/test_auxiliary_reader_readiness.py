import copy
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime as real_datetime

import pytest

from src.engine.automation import auxiliary_reader_readiness as gate
from src.engine.scalping import continuous_reversal_postclose as policy
from src.engine.scalping import mechanistic_entry_runtime_policy as native
from src.engine.scalping import reversal_auxiliary_compatibility as compatibility
from src.engine.scalping import reversal_auxiliary_intraday as reader
from src.engine.scalping import reversal_auxiliary_registry as registry


def _sealed(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(policy.seal(body)))


@pytest.fixture
def source_pair(tmp_path, monkeypatch):
    data = tmp_path / 'data'
    old = tmp_path / 'old' / Path(reader.__file__).name
    old.parent.mkdir()
    old.write_text('reviewed original reader\n')
    old_hashes = {old.name: policy.file_hash(old)}
    new_hashes = {old.name: policy.file_hash(reader.__file__)}
    refs = {'scope-one|krx_nxt_integrated': 'c' * 64}
    source = native.root(data) / 'sources' / ('reversal-' + 's' * 64 + '.json')
    _sealed(source, dict(auxiliary_registry_bindings=refs, auxiliary_reader_code_hashes=old_hashes))
    bundle = dict(bundle_sha256='b' * 64, continuous_reversal=dict(
        schema='continuous_reversal_policy_v6', auxiliary_report_sha256='s' * 64,
        report_file_sha256=dict(auxiliary=policy.file_hash(source))))
    definition = registry.directory(data) / ('c' * 64 + '.json')
    _sealed(definition, dict(input_version='fixture'))
    evidence = tmp_path / 'evidence.json'
    _sealed(evidence, dict(status='pass', new_reader_hashes=new_hashes,
                          base_bundle_sha256=bundle['bundle_sha256'],
                          source_sha256=policy.file_hash(source),
                          v1_bindings_sha256=policy.digest(refs)))
    compatibility.issue(data, bundle, source, old_hashes, new_hashes,
                        evidence=evidence, frozen_readers=[dict(path=str(old))])
    inherited_calls = []
    monkeypatch.setattr(reader, 'code_hashes', lambda: new_hashes)
    monkeypatch.setattr(reader, 'inherited', lambda *_: inherited_calls.append(True) or copy.deepcopy(refs))
    monkeypatch.setattr(registry, 'load', lambda data, ident: json.loads(
        (registry.directory(data) / (ident + '.json')).read_text()))
    return dict(data=data, bundle=bundle, source=source, refs=refs, evidence=evidence,
                old=old, new_hashes=new_hashes, inherited_calls=inherited_calls,
                receipt=compatibility.path(data, bundle, source, new_hashes))


def test_preflight_validates_exact_compatibility_and_freezes_dependencies(source_pair):
    f = source_pair
    result = gate.verify_auxiliary_reader('2026-10-12', data_root=f['data'], bundle=f['bundle'])
    assert result['status'] == 'pass'
    assert result['scope_count'] == 1
    assert result['compatibility_status'] == 'verified'
    assert result['compatibility_path'] == str(f['receipt'])
    assert result['provider_called'] is result['broker_called'] is result['order_submitted'] is False
    gate.verify_bound_sources(result)
    f['receipt'].unlink()
    with pytest.raises(ValueError, match='source_changed'):
        gate.verify_bound_sources(result)


@pytest.mark.parametrize('damage', [
    'missing_receipt', 'missing_source', 'source_hash', 'receipt_hash', 'bundle_binding',
    'evidence_hash', 'missing_evidence', 'frozen_reader', 'reader_hashes',
])
def test_preflight_rejects_missing_or_changed_native_proof_before_inheritance(source_pair, damage):
    f = source_pair
    if damage == 'missing_receipt':
        f['receipt'].unlink()
    elif damage == 'missing_source':
        f['source'].unlink()
    elif damage == 'source_hash':
        f['bundle']['continuous_reversal']['report_file_sha256']['auxiliary'] = 'x' * 64
    elif damage == 'receipt_hash':
        f['receipt'].write_text('{}')
    elif damage == 'bundle_binding':
        receipt = json.loads(f['receipt'].read_text())
        receipt['base_bundle_sha256'] = 'x' * 64
        _sealed(f['receipt'], receipt)
    elif damage == 'evidence_hash':
        f['evidence'].write_text('{}')
    elif damage == 'missing_evidence':
        f['evidence'].unlink()
    elif damage == 'frozen_reader':
        f['old'].write_text('changed reader\n')
    elif damage == 'reader_hashes':
        f['new_hashes'][f['old'].name] = 'x' * 64
    with pytest.raises((OSError, ValueError)):
        gate.verify_auxiliary_reader('2026-10-12', data_root=f['data'], bundle=f['bundle'])
    assert not f['inherited_calls']


def test_same_readers_do_not_require_a_compatibility_receipt(source_pair):
    f = source_pair
    report = json.loads(f['source'].read_text())
    report['auxiliary_reader_code_hashes'] = f['new_hashes']
    _sealed(f['source'], report)
    f['bundle']['continuous_reversal']['report_file_sha256']['auxiliary'] = policy.file_hash(f['source'])
    f['receipt'].unlink()
    result = gate.verify_auxiliary_reader('2026-10-12', data_root=f['data'], bundle=f['bundle'])
    assert result['status'] == 'pass'
    assert result['compatibility_path'] is None


@pytest.fixture
def target_overlay(source_pair, monkeypatch):
    f = source_pair
    ident = 'd' * 64
    parent = 'e' * 64
    original = 'f' * 64
    day = '2026-10-19'
    value = policy.seal(dict(schema=reader.SCHEMA, authority=reader.AUTHORITY,
        day=day, base_bundle_sha256=f['bundle']['bundle_sha256'],
        evaluation_sha256='1' * 64, previous_overlay_sha256=None,
        bindings={'future-scope|nxt': ident}))
    path = reader.root(f['data']) / 'days' / day / (f['bundle']['bundle_sha256'] + '.json')
    _sealed(path, value)
    generation = reader.root(f['data']) / 'generations' / (value['artifact_content_sha256'] + '.json')
    _sealed(generation, value)
    proof = f['data'] / 'proof.json'
    proof.write_text('original immutable provider/source proof\n')
    manifest = f['data'] / 'transition.json'
    _sealed(manifest, dict(sources=[dict(path=str(proof), sha256=policy.file_hash(proof))]))
    definitions = {
        ident: dict(production_parent_registry_sha256=parent, research_registry_sha256=original),
        parent: dict(research_registry_sha256=original), original: {}, 'c' * 64: {},
    }
    for key, body in definitions.items():
        _sealed(registry.directory(f['data']) / (key + '.json'), body)
    calls = []
    monkeypatch.setattr(reader, 'current', lambda data, bundle, *, day=None: copy.deepcopy(value))
    monkeypatch.setattr(reader, 'validate_record', lambda *a, **k: calls.append(k))
    monkeypatch.setattr(reader, 'rollback_bindings', lambda *a, **k: {})
    monkeypatch.setattr(reader, 'lineage_sources', lambda *a, **k: [
        dict(path=str(p), sha256=policy.file_hash(p)) for p in (generation, manifest, proof)])
    monkeypatch.setattr(registry, 'load', lambda data, key: copy.deepcopy(definitions[key]))
    return {**f, 'day': day, 'overlay': value, 'day_path': path, 'proof': proof,
            'manifest': manifest, 'generation': generation, 'definitions': definitions,
            'validated': calls, 'production_parent': registry.directory(f['data']) / (parent + '.json')}


def test_target_overlay_is_checked_and_all_effective_definition_parents_are_sealed(target_overlay):
    f = target_overlay
    result = gate.verify_auxiliary_reader(f['day'], data_root=f['data'], preparation=True, bundle=f['bundle'])
    assert result['scope_count'] == 2
    assert result['target_overlay'] == dict(path=str(f['day_path']), sha256=policy.file_hash(f['day_path']),
        artifact_content_sha256=f['overlay']['artifact_content_sha256'])
    assert f['validated'] == [dict(check_definitions=True)]
    for path in (f['proof'], f['manifest'], f['generation'], f['production_parent']):
        assert result['source_hashes'][str(path)] == policy.file_hash(path)
    assert result['actual_pid_consumed'] is result['provider_called'] is result['order_submitted'] is False
    gate.verify_bound_sources(result)


@pytest.mark.parametrize('dependency', ['day_path', 'proof', 'manifest', 'generation', 'production_parent'])
def test_sealed_target_overlay_rejects_changed_proof_or_registry_parent(target_overlay, dependency):
    f = target_overlay
    result = gate.verify_auxiliary_reader(f['day'], data_root=f['data'], bundle=f['bundle'])
    f[dependency].write_text('changed after preparation\n')
    with pytest.raises(ValueError, match='source_changed|overlay_changed'):
        gate.verify_bound_sources(result)


def test_target_overlay_sources_changing_during_native_validation_fail(target_overlay, monkeypatch):
    f = target_overlay
    monkeypatch.setattr(reader, 'validate_record', lambda *a, **k: f['proof'].write_text('raced proof\n'))
    with pytest.raises(ValueError, match='source_changed'):
        gate.verify_auxiliary_reader(f['day'], data_root=f['data'], bundle=f['bundle'])


def test_target_overlay_seals_original_reader_compatibility_dependencies(target_overlay, monkeypatch):
    f = target_overlay
    ancestor_record = policy.seal({**f['overlay'],
        'code_hashes': {f['old'].name: policy.file_hash(f['old'])}})
    ancestor = reader.root(f['data']) / 'generations' / (ancestor_record['artifact_content_sha256'] + '.json')
    _sealed(ancestor, ancestor_record)
    updated = policy.seal({**f['overlay'], 'previous_overlay_sha256': ancestor_record['artifact_content_sha256']})
    f['overlay'].clear()
    f['overlay'].update(updated)
    generation = reader.root(f['data']) / 'generations' / (updated['artifact_content_sha256'] + '.json')
    _sealed(generation, updated)
    _sealed(f['day_path'], updated)
    monkeypatch.setattr(reader, 'lineage_sources', lambda *a: [
        dict(path=str(p), sha256=policy.file_hash(p)) for p in (generation, ancestor, f['manifest'], f['proof'])])
    # The source report and overlay generation have separately bound receipts.
    overlay_proof = f['data'] / 'overlay-reader-compatibility.json'
    _sealed(overlay_proof, dict(status='pass'))
    validate = compatibility.validate
    path = compatibility.path
    monkeypatch.setattr(compatibility, 'path', lambda data, bundle, source, hashes:
        overlay_proof if source == ancestor else path(data, bundle, source, hashes))
    monkeypatch.setattr(compatibility, 'validate', lambda data, bundle, source, old, new:
        dict(evidence_path=str(f['evidence']), frozen_readers=[dict(path=str(f['old']))])
        if source == ancestor else validate(data, bundle, source, old, new))
    result = gate.verify_auxiliary_reader(f['day'], data_root=f['data'], bundle=f['bundle'])
    assert result['source_hashes'][str(overlay_proof)] == policy.file_hash(overlay_proof)
    overlay_proof.unlink()
    with pytest.raises(ValueError, match='source_changed'):
        gate.verify_bound_sources(result)


def _historical_source_generation(f, monkeypatch, *, linked=False, wrong_bundle=False):
    historical = policy.seal({**f['overlay'], 'day': f['day'] if wrong_bundle else '2026-10-16',
        'base_bundle_sha256': '0' * 64 if wrong_bundle else f['bundle']['bundle_sha256'],
        'code_hashes': {f['old'].name: policy.file_hash(f['old'])}})
    path = reader.root(f['data']) / 'generations' / (historical['artifact_content_sha256'] + '.json')
    _sealed(path, historical)
    original = reader.lineage_sources
    monkeypatch.setattr(reader, 'lineage_sources', lambda *a: original(*a) + [
        dict(path=str(path), sha256=policy.file_hash(path))])
    if linked:
        updated = policy.seal({**f['overlay'], 'previous_overlay_sha256': historical['artifact_content_sha256']})
        f['overlay'].clear()
        f['overlay'].update(updated)
        _sealed(f['day_path'], updated)
        _sealed(reader.root(f['data']) / 'generations' / (updated['artifact_content_sha256'] + '.json'), updated)
    return path


@pytest.mark.parametrize('damage', [False, True])
def test_flat_historical_source_is_hash_bound_without_cross_date_current_compatibility(target_overlay, monkeypatch, damage):
    f = target_overlay
    historical = _historical_source_generation(f, monkeypatch)
    validate = compatibility.validate
    def exact_owner(data, bundle, source, old, new):
        assert Path(source) != historical, 'historical source assigned to target-day runtime compatibility'
        return validate(data, bundle, source, old, new)
    monkeypatch.setattr(compatibility, 'validate', exact_owner)
    result = gate.verify_auxiliary_reader(f['day'], data_root=f['data'], preparation=True, bundle=f['bundle'])
    assert result['source_hashes'][str(historical)] == policy.file_hash(historical)
    if damage:
        historical.write_text('changed original research generation\n')
        with pytest.raises(ValueError, match='source_changed'):
            gate.verify_bound_sources(result)
    else:
        gate.verify_bound_sources(result)


@pytest.mark.parametrize('wrong_bundle', [False, True])
def test_foreign_generation_cannot_be_hidden_inside_actual_runtime_previous_chain(target_overlay, monkeypatch, wrong_bundle):
    f = target_overlay
    _historical_source_generation(f, monkeypatch, linked=True, wrong_bundle=wrong_bundle)
    with pytest.raises(ValueError, match='overlay_ancestry_invalid'):
        gate.verify_auxiliary_reader(f['day'], data_root=f['data'], bundle=f['bundle'])


def test_target_overlay_must_match_its_exact_day_pointer(target_overlay):
    f = target_overlay
    _sealed(f['day_path'], dict(bindings={}))
    with pytest.raises(ValueError, match='overlay_changed'):
        gate.verify_auxiliary_reader(f['day'], data_root=f['data'], bundle=f['bundle'])


def test_target_overlay_change_during_validation_is_not_relabelled_as_current(target_overlay, monkeypatch):
    f = target_overlay
    observations = iter([f['overlay'], policy.seal(dict(bindings={}))])
    monkeypatch.setattr(reader, 'current', lambda *a, **k: next(observations))
    with pytest.raises(ValueError, match='overlay_changed'):
        gate.verify_auxiliary_reader(f['day'], data_root=f['data'], bundle=f['bundle'])


def test_legacy_no_overlay_absence_is_sealed_without_registration(source_pair, monkeypatch):
    f = source_pair
    monkeypatch.setattr(registry, 'register', lambda *a, **k: pytest.fail('registered during readiness'))
    result = gate.verify_auxiliary_reader('2026-10-19', data_root=f['data'], bundle=f['bundle'])
    assert result['target_overlay']['sha256'] is None
    gate.verify_bound_sources(result)
    _sealed(Path(result['target_overlay']['path']), dict(bindings={}))
    with pytest.raises(ValueError, match='overlay_changed'):
        gate.verify_bound_sources(result)


def test_no_overlay_still_seals_inherited_compact_original_registry_parent(source_pair):
    f = source_pair
    parent = registry.directory(f['data']) / ('e' * 64 + '.json')
    _sealed(parent, dict(input_version='fixture'))
    _sealed(registry.directory(f['data']) / ('c' * 64 + '.json'),
        dict(research_registry_sha256='e' * 64, input_version='fixture'))
    result = gate.verify_auxiliary_reader('2026-10-19', data_root=f['data'], bundle=f['bundle'])
    assert result['source_hashes'][str(parent)] == policy.file_hash(parent)
    parent.write_text('changed original parent\n')
    with pytest.raises(ValueError, match='source_changed'):
        gate.verify_bound_sources(result)


def test_relative_data_root_is_frozen_before_a_later_consumer_changes_cwd(source_pair, monkeypatch):
    f = source_pair
    monkeypatch.chdir(f['data'].parent)
    result = gate.verify_auxiliary_reader('2026-10-19', data_root=Path('data'), bundle=f['bundle'])
    assert result['data_root'] == str(f['data'])
    assert all(Path(name).is_absolute() for name in result['source_hashes'])
    monkeypatch.chdir(f['data'].parent.parent)
    gate.verify_bound_sources(result)


def test_overlay_appearing_after_no_overlay_read_cannot_be_sealed_as_absent(source_pair, monkeypatch):
    f = source_pair
    path = reader.root(f['data']) / 'days/2026-10-19' / (f['bundle']['bundle_sha256'] + '.json')
    def appeared(*a, **k):
        _sealed(path, dict(bindings={}))
        return None
    monkeypatch.setattr(reader, 'current', appeared)
    with pytest.raises(ValueError, match='overlay_changed'):
        gate.verify_auxiliary_reader('2026-10-19', data_root=f['data'], bundle=f['bundle'])


def _runtime_successor(f, monkeypatch, *, ancestor=True):
    result = gate.verify_auxiliary_reader(f['day'], data_root=f['data'], bundle=f['bundle'])
    if not ancestor:
        result['target_overlay'].update(sha256=None, artifact_content_sha256=None)
    class TargetDay:
        @classmethod
        def now(cls, zone):
            return real_datetime(2026, 10, 19, 10, 0, tzinfo=zone)
    monkeypatch.setattr(gate, 'datetime', TargetDay)
    active = native.root(f['data']) / 'current.json'
    _sealed(active, dict(bundle_sha256=f['bundle']['bundle_sha256'], effective_date=f['day']))
    monkeypatch.setattr(native, 'load_effective', lambda **kwargs: f['bundle'])
    next_record = policy.seal({**f['overlay'], 'previous_overlay_sha256':
        f['overlay']['artifact_content_sha256'] if ancestor else None, 'change_note': 'native successor'})
    generation = reader.root(f['data']) / 'generations' / (next_record['artifact_content_sha256'] + '.json')
    _sealed(generation, next_record)
    _sealed(f['day_path'], next_record)
    monkeypatch.setattr(reader, 'current', lambda *args, **kwargs: copy.deepcopy(next_record))
    return result, next_record, generation, active


@pytest.mark.parametrize('ancestor', [True, False])
def test_real_target_day_native_descendant_or_first_publication_preserves_readiness(target_overlay, monkeypatch, ancestor):
    result, _, _, _ = _runtime_successor(target_overlay, monkeypatch, ancestor=ancestor)
    gate.verify_bound_sources(result)


@pytest.mark.parametrize('damage', ['not_activated', 'other_bundle', 'other_day', 'missing_parent',
                                  'not_descendant', 'missing_proof', 'root_rollback_without_proof',
                                  'invalid_parent', 'active_pointer_race'])
def test_same_day_overlay_changes_cannot_bypass_activation_ancestry_or_native_proof(target_overlay, monkeypatch, damage):
    f = target_overlay
    result, successor, generation, active = _runtime_successor(f, monkeypatch)
    if damage == 'not_activated':
        _sealed(active, dict(bundle_sha256='0' * 64, effective_date=f['day']))
    elif damage in {'other_bundle', 'other_day', 'missing_parent', 'not_descendant', 'missing_proof',
                    'root_rollback_without_proof', 'invalid_parent'}:
        updated = dict(successor)
        if damage == 'other_bundle':
            updated['base_bundle_sha256'] = '0' * 64
        elif damage == 'other_day':
            updated['day'] = '2026-10-18'
        elif damage == 'missing_parent':
            updated['previous_overlay_sha256'] = '0' * 64
        elif damage == 'not_descendant':
            updated['previous_overlay_sha256'] = None
        elif damage == 'missing_proof':
            updated.pop('evaluation_sha256')
        elif damage == 'root_rollback_without_proof':
            updated.pop('evaluation_sha256')
            updated.update(rollback_reason='unproven root', previous_overlay_sha256=None)
        elif damage == 'invalid_parent':
            updated['previous_overlay_sha256'] = '../outside-generation'
        updated = policy.seal(updated)
        _sealed(reader.root(f['data']) / 'generations' / (updated['artifact_content_sha256'] + '.json'), updated)
        _sealed(f['day_path'], updated)
        monkeypatch.setattr(reader, 'current', lambda *a, **k: copy.deepcopy(updated))
    elif damage == 'active_pointer_race':
        monkeypatch.setattr(reader, 'validate_record', lambda *a, **k: _sealed(active, dict(changed=True)))
    with pytest.raises((OSError, ValueError), match='overlay|No such file'):
        gate.verify_bound_sources(result)


def test_active_machine_from_previous_date_cannot_authorize_new_overlay(target_overlay, monkeypatch):
    f = target_overlay
    result, _, _, active = _runtime_successor(f, monkeypatch)
    _sealed(active, dict(bundle_sha256=f['bundle']['bundle_sha256'], effective_date='2026-10-16'))
    with pytest.raises(ValueError, match='not_activated'):
        gate.verify_bound_sources(result)


def test_same_day_native_rollback_retains_proven_ancestor_without_new_evaluation(target_overlay, monkeypatch):
    f = target_overlay
    result, successor, _, _ = _runtime_successor(f, monkeypatch)
    changed = dict(successor)
    changed.pop('evaluation_sha256')
    changed['rollback_reason'] = 'approved native rollback'
    changed = policy.seal(changed)
    _sealed(reader.root(f['data']) / 'generations' / (changed['artifact_content_sha256'] + '.json'), changed)
    _sealed(f['day_path'], changed)
    monkeypatch.setattr(reader, 'current', lambda *a, **k: copy.deepcopy(changed))
    gate.verify_bound_sources(result)


@pytest.mark.parametrize('dependency', ['receipt', 'evidence', 'old', 'definition'])
def test_preflight_detects_dependency_change_during_native_validation(source_pair, monkeypatch, dependency):
    f = source_pair
    path = (registry.directory(f['data']) / ('c' * 64 + '.json')
            if dependency == 'definition' else f[dependency])
    def changed(*_):
        path.write_text('changed during native validation')
        return f['refs']
    monkeypatch.setattr(reader, 'inherited', changed)
    with pytest.raises(ValueError, match='source_changed'):
        gate.verify_auxiliary_reader('2026-10-12', data_root=f['data'], bundle=f['bundle'])


def test_preparation_uses_candidate_and_runtime_uses_effective_bundle(source_pair, monkeypatch):
    f = source_pair
    calls = []
    monkeypatch.setattr(native, 'load', lambda **kwargs: calls.append('candidate') or f['bundle'])
    monkeypatch.setattr(native, 'load_effective', lambda **kwargs: calls.append('effective') or f['bundle'])
    assert gate.verify_auxiliary_reader('2026-10-12', data_root=f['data'], preparation=True)['phase'] == 'preparation'
    assert gate.verify_auxiliary_reader('2026-10-12', data_root=f['data'])['phase'] == 'runtime'
    assert calls == ['candidate', 'effective']


def test_preflight_does_not_restore_absent_or_legacy_registered_consumer(monkeypatch, tmp_path):
    monkeypatch.setattr(native, 'load_effective', lambda **_: None)
    assert gate.verify_auxiliary_reader('2026-10-12', data_root=tmp_path)['status'] == 'not_required'
    assert gate.verify_auxiliary_reader('2026-10-12', data_root=tmp_path, bundle={})['status'] == 'not_required'


def test_cli_reports_failure_and_never_claims_consumption(monkeypatch, capsys):
    def missing(*args, **kwargs):
        raise FileNotFoundError('native compatibility receipt missing')
    monkeypatch.setattr(gate, 'verify_auxiliary_reader', missing)
    assert gate.main(['--target-date', '2026-10-12']) == 1
    result = json.loads(capsys.readouterr().out)
    assert result['status'] == 'fail'
    assert result['actual_pid_consumed'] is False
    assert result['provider_called'] is False


def test_preparation_cannot_substitute_current_proof_for_a_future_bundle(source_pair, monkeypatch):
    f = source_pair
    future = copy.deepcopy(f['bundle'])
    future['bundle_sha256'] = 'd' * 64
    monkeypatch.setattr(native, 'load', lambda **_: future)
    monkeypatch.setattr(native, 'load_effective', lambda **_: pytest.fail('current bundle substituted'))
    with pytest.raises(FileNotFoundError):
        gate.verify_auxiliary_reader('2026-10-13', data_root=f['data'], preparation=True)


def test_preopen_rejects_missing_compatibility_before_writing_a_bootstrap(monkeypatch, tmp_path):
    from src.engine.automation import next_preopen_readiness as readiness
    monkeypatch.setattr(readiness, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(readiness, 'target_after_postclose', lambda *a, **k: '2026-10-13')
    monkeypatch.setattr(readiness, '_selected_release', lambda: ({}, tmp_path / 'selection', 'a' * 40))
    monkeypatch.setattr(readiness, '_activation_candidate_receipt', lambda *_: None)
    def missing(*args, **kwargs):
        assert kwargs['preparation'] is True
        raise FileNotFoundError('compatibility receipt missing')
    monkeypatch.setattr(readiness, 'verify_auxiliary_reader', missing)
    monkeypatch.setattr(readiness.bootstrap, 'write_bootstrap', lambda *a, **k: pytest.fail('bootstrap written'))
    with pytest.raises(FileNotFoundError):
        readiness.prepare('2026-10-12', target_date='2026-10-13')


@pytest.mark.parametrize('gate_exit', [0, 1])
def test_actual_launcher_guard_prevents_child_spawn_when_auxiliary_preflight_fails(tmp_path, gate_exit):
    source = (Path(__file__).parents[1] / 'run_bot.sh').read_text()
    start = source.index('    PYTHONPATH=.. ../.venv/bin/python -m src.engine.scalping.mechanistic_entry_runtime_policy')
    end = source.index('    wait "$BOT_PID"', start) + len('    wait "$BOT_PID"')
    venv = tmp_path / '.venv/bin'
    venv.mkdir(parents=True)
    fake_python = venv / 'python'
    fake_python.write_text('''#!/bin/bash
if [[ "$*" == *"src.engine.automation.auxiliary_reader_readiness"* ]]; then
  exit "$AUXILIARY_TEST_GATE_EXIT"
fi
if [[ "$*" == "bot_main.py" ]]; then
  touch "$AUXILIARY_TEST_CHILD_MARKER"
fi
exit 0
''')
    fake_python.chmod(0o755)
    (tmp_path / 'src').mkdir()
    (tmp_path / 'data').mkdir()
    deploy = tmp_path / 'deploy'
    deploy.mkdir()
    routed = deploy / 'run_runtime_release.sh'
    routed.write_text('#!/bin/bash\nexit 0\n')
    script = '''set -e
RUNTIME_TARGET_DATE=2026-10-12
DEFAULT_BOT_CPU_AFFINITY=""
KORSTOCKSCAN_RUNTIME_GIT_COMMIT=test
PROJECT_DIR="$(cd .. && pwd)"
export_runtime_source_provenance() { :; }
record_threshold_runtime_env_pid_handoff() { :; }
korstockscan_nproc() { echo 1; }
''' + source[start:end]
    marker = tmp_path / 'child-spawned'
    result = subprocess.run(['bash', '-c', script], cwd=tmp_path / 'src',
                            env={**os.environ, 'AUXILIARY_TEST_GATE_EXIT': str(gate_exit),
                                 'AUXILIARY_TEST_CHILD_MARKER': str(marker)},
                            capture_output=True, text=True)
    assert result.returncode == gate_exit
    assert marker.exists() is (gate_exit == 0)
