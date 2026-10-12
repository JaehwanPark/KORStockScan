import copy
import json
import os
from pathlib import Path
import subprocess

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
