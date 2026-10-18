"""Native source-delta proofs survive only in a real isolated validation child."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest

from src.engine.infrastructure import startup_validation_code_context as C
from src.engine.automation import intraday_release_handoff as H
from src.tests.test_main_policy_native_child import _source_copy

ROOT = Path(__file__).resolve().parents[2]
DAY = '2026-10-19'
RELATIVE = 'src/engine/scalping/pre_submit_delay_tuning.py'


def _git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True,
        stderr=subprocess.PIPE).strip()


def _commit(root, message):
    _git(root, 'add', 'src')
    _git(root, '-c', 'user.name=Validation Fixture', '-c', 'user.email=fixture@example.invalid',
        'commit', '-qm', message)
    return _git(root, 'rev-parse', 'HEAD')


@pytest.fixture(scope='module')
def releases(tmp_path_factory):
    base = tmp_path_factory.mktemp('native-code-context')
    root, selected = base / 'candidate', base / 'selected'
    _source_copy(root)
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    original_commit = _commit(root, 'genuine source origin')
    _git(root, 'worktree', 'add', '--detach', str(selected), original_commit)
    path = root / RELATIVE
    old = path.read_text()
    changed = old.replace('Preserve only a sealed same-day policy through the reviewed entry repair.',
        'Preserve only a sealed same-day policy through this reviewed entry repair.', 1)
    assert changed != old
    path.write_text(changed)
    commit = _commit(root, 'behavior-preserving native accepted docstring change')
    paths = {RELATIVE: RELATIVE}
    expected = C._digest({RELATIVE: C._sha(selected / RELATIVE)})
    actual = C._digest({RELATIVE: C._sha(root / RELATIVE)})
    # Exercise the actual pre-isolation native delta validator, including Git
    # source identity and its allowed AST projection. No fake proof evaluator.
    assert H._verify_entry_code_delta(root, commit, original_commit, paths, expected) == [RELATIVE]
    return dict(root=root, selected=selected, commit=commit, original_commit=original_commit,
        paths=paths, expected=expected, actual=actual)


@pytest.fixture
def request_fixture(tmp_path, releases):
    run = tmp_path / uuid.uuid4().hex
    run.mkdir(mode=0o700)
    data = tmp_path / 'fixture-data'
    selector = data / 'runtime/runtime_release_selection.json'
    selector.parent.mkdir(parents=True)
    selector.write_text(json.dumps(dict(schema='runtime_release_selection_v1',
        release_root=str(releases['selected']), git_commit=releases['original_commit'], workspace=str(tmp_path))))
    policy = dict(schema='fixture_native_code_binding', code_contract_sha256=releases['expected'])
    policy_sha = C._digest(policy)
    origin_sources = {str(selector): C._sha(selector),
        str(releases['selected'] / RELATIVE): C._sha(releases['selected'] / RELATIVE)}
    evidence = run / 'bound-input.json'
    evidence.write_text('{"bound":true}')
    sources = {str(evidence): C._sha(evidence), **origin_sources, str(releases['root'] / RELATIVE): C._sha(releases['root'] / RELATIVE),
        str(releases['root'] / 'src/engine/infrastructure/startup_validation_code_context.py'):
            C._sha(releases['root'] / 'src/engine/infrastructure/startup_validation_code_context.py')}
    origin = dict(origin_commit=releases['original_commit'], basis='selected_exact_code_contract',
        selected_release_root=str(releases['selected']), selected_release_commit=releases['original_commit'],
        original_code_sha256=releases['expected'], selected_runtime_code_sha256=releases['expected'], sources=origin_sources)
    proof = dict(schema=C.PROOF_SCHEMA, status='verified', target_date=DAY, family='pre_submit_delay',
        policy_sha256=policy_sha, original_code_sha256=releases['expected'], runtime_code_contract_sha256=releases['actual'],
        paths=releases['paths'], execution_release_root=str(releases['root']), execution_release_commit=releases['commit'],
        policy_effect='unchanged', source_hashes=sources, origin=origin)
    request = dict(schema=C.REQUEST_SCHEMA, run_id=run.name, run_directory=str(run), target_date=DAY,
        execution_release_root=str(releases['root']), execution_release_commit=releases['commit'], data_root=str(data),
        source_hashes=sources, candidate_code_handoffs={'pre_submit_delay': proof},
        manifest={'target_date': DAY, 'pre_submit_delay_handoff': {'target_date': DAY, 'policy_sha256': policy_sha}})
    request['request_sha256'] = C._digest(request)
    path = run / 'request.json'
    path.write_text(json.dumps(request))
    return dict(run=run, path=path, request=request, **releases)


def _write_request(fixture, request):
    request.pop('request_sha256', None)
    request['request_sha256'] = C._digest(request)
    fixture['path'].write_text(json.dumps(request))


def _child(fixture, body, *, isolated=True):
    root, run = fixture['root'], fixture['run']
    code = """import json, os, pathlib, sys
sys.path.insert(0, sys.argv[1])
from src.engine.infrastructure.startup_validation_isolation import install_validation_isolation, assert_no_forbidden_attempts
from src.engine.infrastructure.startup_validation_code_context import install_validation_code_context, verify_validation_consumer_code
run = pathlib.Path(sys.argv[2])
request = json.loads((run / 'request.json').read_text())
"""
    if isolated:
        code += "install_validation_isolation(run, run / 'audit.jsonl')\n"
    code += body
    return subprocess.run([sys.executable, '-I', '-B', '-c', code, str(root), str(run)],
        cwd=root, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'OPENBLAS_NUM_THREADS': '1',
            'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}, start_new_session=True,
        close_fds=True, capture_output=True, text=True, timeout=40)


CALL = """p = request['candidate_code_handoffs']['pre_submit_delay']
result = verify_validation_consumer_code(request['target_date'], family='pre_submit_delay',
    policy_sha=p['policy_sha256'], expected=p['original_code_sha256'], paths=p['paths'], actual=p['runtime_code_contract_sha256'])
"""


def test_no_context_leaves_normal_native_guard_untouched():
    assert C.verify_validation_consumer_code(DAY, family='pre_submit_delay', policy_sha='a'*64,
        expected='b'*64, paths={'source': RELATIVE}, actual='c'*64) is None


def test_install_outside_real_os_isolation_is_refused(request_fixture):
    result = _child(request_fixture, 'install_validation_code_context(request)\n', isolated=False)
    assert result.returncode != 0
    assert 'validation_isolation_not_complete' in result.stderr


def test_native_legacy_handoff_hook_imports_and_verifies_under_real_isolation(request_fixture):
    result = _child(request_fixture, """install_validation_code_context(request)
assert 'src.engine.automation.intraday_release_handoff' not in sys.modules
from src.engine.automation.intraday_release_handoff import verify_entry_consumer_code
p = request['candidate_code_handoffs']['pre_submit_delay']
result = verify_entry_consumer_code(request['target_date'], family='pre_submit_delay', policy_sha=p['policy_sha256'],
    expected=p['original_code_sha256'], paths=p['paths'], actual=p['runtime_code_contract_sha256'])
assert result['status'] == 'verified_intraday_consumer_repair', result
assert result['basis'] == 'main_startup_validation_code_context_v1', result
assert result['actual_pid_consumed'] is result['execution_authority'] is False
assert result['policy_effect'] == 'unchanged'
assert_no_forbidden_attempts()
print(json.dumps(result))
""")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['runtime_code_contract_sha256'] == request_fixture['actual']
    assert (request_fixture['run'] / 'audit.jsonl').read_bytes() == b''
    assert not list(request_fixture['run'].glob('*handoff*.json'))


@pytest.mark.parametrize('field,value', [('target_date', '2026-10-20'), ('policy_sha256', 'd'*64),
    ('original_code_sha256', 'd'*64), ('runtime_code_contract_sha256', 'd'*64),
    ('execution_release_commit', 'd'*40), ('policy_effect', 'changed'), ('status', 'pending')])
def test_bad_or_unbound_proof_never_installs(request_fixture, field, value):
    request = request_fixture['request']
    request['candidate_code_handoffs']['pre_submit_delay'][field] = value
    _write_request(request_fixture, request)
    result = _child(request_fixture, 'install_validation_code_context(request)\n')
    assert result.returncode != 0
    assert 'startup_code_context_' in result.stderr


@pytest.mark.parametrize('change', ['day', 'family', 'policy', 'expected', 'actual', 'paths'])
def test_native_call_arguments_must_match_exact_prevalidated_proof(request_fixture, change):
    code = "install_validation_code_context(request)\np = request['candidate_code_handoffs']['pre_submit_delay']\n"
    code += "args = dict(day=request['target_date'], family='pre_submit_delay', policy_sha=p['policy_sha256'], expected=p['original_code_sha256'], paths=p['paths'], actual=p['runtime_code_contract_sha256'])\n"
    value = {'day': repr('2026-10-20'), 'family': repr('main_stop'), 'policy': repr('d'*64),
        'expected': repr('d'*64), 'actual': repr('d'*64), 'paths': repr({'unexpected': RELATIVE})}[change]
    key = 'policy_sha' if change == 'policy' else change
    code += 'args[' + repr(key) + '] = ' + value + '\nverify_validation_consumer_code(**args)\n'
    result = _child(request_fixture, code)
    assert result.returncode != 0
    assert 'consumer_binding_invalid' in result.stderr


def test_request_mutation_after_install_invalidates_even_caught_lookup(request_fixture):
    code = """install_validation_code_context(request)
request['target_date'] = '2026-10-20'
(run / 'request.json').write_text(json.dumps(request))
""" + CALL
    result = _child(request_fixture, code)
    assert result.returncode != 0
    assert 'execution_changed' in result.stderr


def test_corrupt_source_and_origin_inventory_fail_even_with_fresh_request_digest(request_fixture):
    request = request_fixture['request']
    proof = request['candidate_code_handoffs']['pre_submit_delay']
    proof['origin']['selected_runtime_code_sha256'] = 'e' * 64
    _write_request(request_fixture, request)
    result = _child(request_fixture, 'install_validation_code_context(request)\n')
    assert result.returncode != 0
    assert 'selected_contract_changed' in result.stderr


def test_source_bytes_mutation_after_context_install_fails_lookup(request_fixture):
    result = _child(request_fixture, """install_validation_code_context(request)
(run / 'bound-input.json').write_text('{"bound":false}')
""" + CALL)
    assert result.returncode != 0
    assert 'startup_code_context_source_changed' in result.stderr


def test_caught_bad_install_poisoned_context_cannot_fall_through_to_live(request_fixture):
    result = _child(request_fixture, """request['run_directory'] = str(run.parent)
try:
    install_validation_code_context(request)
except ValueError:
    pass
""" + CALL)
    assert result.returncode != 0
    assert 'startup_code_context_invalid' in result.stderr
