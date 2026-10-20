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
    assert C.validate_preparation_delay_selection(None, None) is False


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


def _main_fixture(f, monkeypatch):
    """Small native closure; economic schema is owned by native policy tests.

    Git, exact-pair checks, digest hashing and the OS child are real. A native
    CLI collection test separately proves these closure fields have a producer.
    """
    import time
    from src.engine.infrastructure.validation_digest_session import DigestSession, identity
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import continuous_reversal_postclose as P
    req = f['request']; data = Path(req['data_root']); selected = f['selected']; root = f['root']
    owner = 'src/engine/scalping/reversal_path_runtime.py'
    original = C._sha(selected / owner)
    bundle = dict(bundle_sha256='b'*64, target_date=DAY,
        continuous_reversal=dict(schema='continuous_reversal_policy_v4', family_sha256='c'*64,
            release_commit=f['original_commit'], contract_file_sha256={'reversal_path_runtime.py': original}))
    path = data / 'runtime/mechanistic_entry_policy/candidates' / ('policy_' + DAY + '.json')
    path.parent.mkdir(parents=True); path.write_text(json.dumps(bundle))
    raw = data / 'raw.bin'; raw.write_bytes(b'a' * (2 * 1024 * 1024))
    digest = hashlib.sha256(raw.read_bytes()).hexdigest()
    metadata = data / 'metadata.sqlite3'; metadata.write_bytes(b'private-ledger')
    frozen_path = selected / owner
    source = data / 'source.json'; source.write_text('{}')
    original_bundle = data / 'old-bundle.json'; original_bundle.write_text('{}')
    from src.engine.scalping import reversal_auxiliary_next_session as A
    manifest = P.seal(dict(base_bundle_sha256=bundle['bundle_sha256'],
        source_manifest={'path': str(source), 'sha256': C._sha(source)},
        source_bundle={'path': str(original_bundle), 'sha256': C._sha(original_bundle)},
        frozen_validator_root=str(selected), frozen_validator_commit=f['original_commit'],
        frozen_inventory={str(frozen_path): original}, frozen_validation={'native': 'fixture'},
        semantic_code_hashes={'reversal_path_runtime.py':original}, next_session_code_hashes={}, reader_code_hashes={},
        ledger_pack_paths=[], baseline_dependency_paths=[],
        sources=[{'path': str(v), 'sha256': C._sha(v)} for v in (source, original_bundle, frozen_path, raw)]))
    manifest_path = data / 'transition.json'; manifest_path.write_text(json.dumps(manifest))
    observed = dict(path=str(manifest_path), sha256=C._sha(manifest_path),
        target_date=DAY, bundle_sha256=bundle['bundle_sha256'], database=None,
        dependencies=[[v['path'], json.loads(json.dumps(N._signature(v['path'])))] for v in manifest['sources']])
    session = DigestSession(data, '2026-10-16', role='postclose', generation={})
    closure = dict(schema='startup_native_machine_closure_v1',run_id=req['run_id'],
        digest_binding=session.binding, digest_entries={str(raw): dict(identity=identity(raw),digest=digest,created=time.time())},
        bundles={bundle['bundle_sha256']: {'target_date': DAY,'family_sha256':'c'*64}},
        manifests={manifest['artifact_content_sha256']: observed},
        frozen_inventories={str(selected):manifest['frozen_inventory']},
        frozen_validations={str(source):dict(root=str(selected),bundle_path=str(original_bundle),result=manifest['frozen_validation'],
            invocation=dict(executable=str(selected/'.venv/bin/python'),arguments=['-B','-c'],
                script_sha256=hashlib.sha256(A._FROZEN_SCRIPT.encode()).hexdigest(),cwd=str(selected),
                source_manifest=str(source),source_bundle=str(original_bundle),
                environment=dict(PYTHONPATH=str(selected),PYTHONDONTWRITEBYTECODE='1'),
                parent_environment='sanitized_p5_native_verification'))})
    native = dict(status='pass',findings=[],validation_scope='current_full_contract',target_date=DAY,
        selected_release_commit=f['original_commit'],source_date='2026-10-16',
        native_validation_io=dict(stats={'pid':os.getpid()},remaining_entries=0))
    code = {owner: original}
    sources={str(path):C._sha(path),str(manifest_path):C._sha(manifest_path),
        str(data/'runtime/runtime_release_selection.json'):C._sha(data/'runtime/runtime_release_selection.json'),
        str(selected/owner):original,str(root/owner):C._sha(root/owner)}
    # This helper's exact origin set is a unit seam. The real reviewed table
    # has separate Git/source-pair tests; this genuine unchanged byte is not a
    # manufactured PASS for a changed source.
    proof=dict(schema=C.MAIN_PROOF_SCHEMA,target_date=DAY,policy_path=str(path),
        policy_sha256=bundle['bundle_sha256'],policy_file_sha256=C._sha(path),
        execution_release_root=str(root),execution_release_commit=f['commit'],
        selected_release_root=str(selected),selected_release_commit=f['original_commit'],
        original_code_hashes=code,runtime_code_hashes=code,inventories=C._main_inventories(bundle),
        inventory_git_attestations={bundle['bundle_sha256']:dict(origin_commit=f['original_commit'],code_hashes=code)},
        source_hashes=sources,closure=closure,native_verification=native,
        historical_semantic_code_sources={manifest['artifact_content_sha256']:{owner:dict(path=str(frozen_path),sha256=original)}},
        delegation_basis='same_invocation_selected_native_full_verification',policy_effect='unchanged',
        runtime_effect=False,allowed_runtime_apply=False,actual_pid_consumed=False)
    req.update(main_preparation_code_handoff=proof,expected_policy_hashes=dict.fromkeys(('main_machine','main_auxiliary'),bundle['bundle_sha256']))
    req['source_hashes'].update(sources)
    _write_request(f,req)
    return dict(raw=raw, bundle=bundle, proof=proof, manifest=manifest)


# Fixtures below isolate the native-closure data model only. Real isolation,
# code-source byte/Git identity and digest generation checks remain active.
MAIN_CHILD_SETUP = """from src.engine.infrastructure import startup_validation_code_context as C
from src.engine.scalping import reversal_auxiliary_next_session as A
C.REVIEWED_PREPARATION_SOURCES = {}
A._database_signature = lambda manifest: None
install_validation_code_context(request)
"""


def test_main_preparation_digest_reuses_only_exact_parent_bytes_in_real_isolation(request_fixture, monkeypatch):
    f=_main_fixture(request_fixture,monkeypatch)
    result=_child(request_fixture,MAIN_CHILD_SETUP+f"""
from src.engine.infrastructure.validation_digest_session import reused_digest
assert reused_digest({str(f['raw'])!r}) == {C._sha(f['raw'])!r}
assert reused_digest(run/'bound-input.json') is None
p=request['main_preparation_code_handoff']; bundle=json.loads(pathlib.Path(p['policy_path']).read_text())
assert C.verify_validation_main_code(bundle,{{'reversal_path_runtime.py':str(C.ROOT/'src/engine/scalping/reversal_path_runtime.py')}},bundle['continuous_reversal']['contract_file_sha256'])
r=C.validation_delegation_receipt()
assert r['digest_reused_reads']==1 and r['digest_reused_bytes']==2097152
assert r['allowed_runtime_apply'] is False
assert_no_forbidden_attempts()
""")
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('change',['selector','request','selected_commit','source_same_size','source_alias','parent_pid','wrong_run','wrong_data_root','wrong_frozen_arguments','missing_inventory'])
def test_main_preparation_rejects_changed_generation_without_full_read(request_fixture,monkeypatch,change):
    f=_main_fixture(request_fixture,monkeypatch)
    # Changes outside the child's private root occur before installation; the
    # parent never grants those writes to the actual isolated child.
    req=request_fixture['request']; proof=f['proof']
    if change=='parent_pid': proof['closure']['digest_binding']['pid']+=1
    elif change=='wrong_run': proof['closure']['run_id']='f'*32
    elif change=='wrong_data_root': proof['closure']['digest_binding']['resolved_root']=str(f['raw'].parent.parent)
    elif change=='wrong_frozen_arguments': next(iter(proof['closure']['frozen_validations'].values()))['invocation']['arguments']=['-c']
    elif change=='missing_inventory': proof['original_code_hashes']={}
    elif change=='source_same_size': f['raw'].write_bytes(b'b'*f['raw'].stat().st_size)
    elif change=='source_alias':
        target=f['raw'].with_suffix('.replacement'); target.write_bytes(f['raw'].read_bytes())
        f['raw'].unlink(); f['raw'].symlink_to(target)
    elif change=='selector':
        target=Path(req['data_root'])/'runtime/runtime_release_selection.json'
        value=json.loads(target.read_text()); value['git_commit']='d'*40; target.write_text(json.dumps(value))
    elif change=='selected_commit': proof['selected_release_commit']='d'*40
    elif change=='request': proof['policy_sha256']='d'*64
    _write_request(request_fixture,req)
    result=_child(request_fixture,MAIN_CHILD_SETUP)
    assert result.returncode!=0
    assert 'startup_' in result.stderr,result.stderr


def test_reviewed_main_code_pairs_are_exact_and_origin_is_not_relabelled():
    assert len(C.REVIEWED_PREPARATION_SOURCES)>=13
    for path,(old,new) in C.REVIEWED_PREPARATION_SOURCES.items():
        # The cold-preparation registration belongs to this immutable parent;
        # later dependency generations are checked by their own native closure.
        raw = subprocess.check_output(['git', '-C', str(ROOT), 'show',
            '8940ea4ad0d3b64d30f67f986a75715ee24c1d95:'+path])
        assert hashlib.sha256(raw).hexdigest()==new
        C._pairs({path:old},{path:new})
        with pytest.raises(ValueError,match='unreviewed'):
            C._pairs({path:old},{path:'0'*64})
    with pytest.raises(ValueError,match='inventory_changed'):
        C._pairs({'owner':'a'*64},{})


@pytest.mark.parametrize('change',['selector','selected_head','candidate_head','request_alias'])
@pytest.mark.parametrize('consumer', ['digest', 'delay_selection'])
def test_installed_main_context_rechecks_control_generation_per_digest(request_fixture,monkeypatch,change,consumer):
    import threading,time
    f=_main_fixture(request_fixture,monkeypatch); run=request_fixture['run']
    if change=='selector':
        target=Path(request_fixture['request']['data_root'])/'runtime/runtime_release_selection.json'
    elif change=='request_alias': target=request_fixture['path']
    else:
        root=request_fixture['selected' if change=='selected_head' else 'root']
        meta=root/'.git'
        directory=(root/meta.read_text().strip()[8:]).resolve() if meta.is_file() else meta
        target=directory/'HEAD'
    before=target.read_bytes(); errors=[]
    def mutate():
        try:
            deadline=time.monotonic()+20
            while not (run/'ready').exists():
                if time.monotonic()>deadline: raise TimeoutError('isolated child did not install')
                time.sleep(.01)
            if change=='request_alias':
                replacement=run/'replacement.json'; replacement.write_bytes(before)
                target.unlink(); target.symlink_to(replacement)
            elif change=='selector':
                v=json.loads(before);v['git_commit']='d'*40;target.write_text(json.dumps(v))
            else: target.write_text('d'*40+'\n')
            (run/'continue').write_text('ready')
        except BaseException as exc: errors.append(exc)
    worker=threading.Thread(target=mutate);worker.start()
    try:
        result=_child(request_fixture,MAIN_CHILD_SETUP+f"""
import time
(run/'ready').write_text('installed')
while not (run/'continue').exists(): time.sleep(.01)
from src.engine.infrastructure.validation_digest_session import reused_digest
{'reused_digest(' + repr(str(f['raw'])) + ')' if consumer == 'digest' else 'C.validate_preparation_delay_selection(None, None)'}
""")
    finally:
        worker.join(timeout=25)
        if target.is_symlink():target.unlink()
        target.write_bytes(before)
    assert not worker.is_alive() and not errors,errors
    assert result.returncode!=0
    assert 'startup_' in result.stderr,result.stderr


@pytest.mark.parametrize('damage', [None, 'missing_shard', 'corrupt_shard', 'membership', 'selection', 'unobserved'])
def test_native_sharded_delay_preparation_delegates_observed_rebuild_in_real_isolation(
        request_fixture, monkeypatch, damage):
    from src.engine.automation import pre_submit_delay_partitioned_research as P
    from src.engine.scalping import pre_submit_delay_initial_policy as I
    from src.tests.test_pre_submit_delay_partitioned_research import fixture
    main = _main_fixture(request_fixture, monkeypatch)
    data = Path(request_fixture['request']['data_root'])
    reference, _ = fixture(data, monkeypatch)
    from src.engine.automation.pre_submit_delay_source_ledger import seal
    from src.engine.lifecycle.holding_window_generation import byte_generation
    from src.engine.scalping.pre_submit_delay_tuning import family_source_ledger_path
    for directory in sorted((data/'threshold_cycle').glob('date=*/family=pre_submit_delay')):
        day = directory.parent.name.removeprefix('date=')
        rows = [json.loads(line) for path in directory.glob('part-execution-*.jsonl')
            for line in path.read_text().splitlines()]
        raw = data/'pipeline_events'/('pipeline_events_'+day+'.jsonl')
        raw.parent.mkdir(exist_ok=True)
        raw.write_text(''.join(json.dumps({**row, 'event_type': 'pipeline_event'})+'\n' for row in rows))
        seal(data, day)
        reference['source_receipt']['ledger_generations'][day] = byte_generation(family_source_ledger_path(data, day))
    report, policy = P.build(reference['qualified_projection'], reference['census'],
        output_root=data/'producer-evidence', source_date=reference['source_date'],
        publication_date='2026-10-18', effective_date=DAY,
        source_sha256=reference['source_sha256'], code_contract_sha256=I.code_contract(request_fixture['root']),
        source_receipt=reference['source_receipt'])
    pointer = I.publish(data, report, policy, expected_incumbent=None)
    report_path, policy_path, _, manifest = I.committed_paths(data, reference['source_date'])
    expected_lookup = I.PreparedPolicy.from_artifacts(policy, report, target_date=DAY).lookup(
        target_date=DAY, market='REGULAR')
    # Execute the exact collection hook embedded in the parent subprocess.
    # Its original validator is the real SQL whole-population implementation;
    # the small Main closure fixture is independent of this delay verdict.
    import ast
    from src.engine.automation import main_startup_validation as V
    tree = ast.parse(Path(V.__file__).read_text())
    native = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_native_preparation_check')
    script = next(n.value.value for n in ast.walk(native) if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == 'script' for t in n.targets))
    hook = next(n for n in ast.walk(ast.parse(script)) if isinstance(n, ast.FunctionDef) and n.name == 'delay')
    namespace = dict(I=I, Path=Path, hashlib=hashlib, json=json, original_delay=P.validate,
        run_id=request_fixture['run'].name, closure=main['proof']['closure'])
    namespace['closure']['delay_selections'] = {}
    exec(compile(ast.Module(body=[hook], type_ignores=[]), '<actual native delay collector>', 'exec'), namespace)
    durable_policy, durable_report = I._read(policy_path), I._read(report_path)
    namespace['delay'](durable_policy, durable_report, target_date=DAY)
    collected = next(iter(namespace['closure']['delay_selections'].values()))
    assert collected['parent_full_selection_recomputed'] is True
    if damage is None:
        from copy import deepcopy
        original = namespace['original_delay']
        saved = deepcopy(namespace['closure']['delay_selections'])
        namespace['closure']['delay_selections'] = {}
        namespace['original_delay'] = lambda *a, **kw: False
        with pytest.raises(ValueError, match='startup_native_delay_result_invalid'):
            namespace['delay'](durable_policy, durable_report, target_date=DAY)
        assert namespace['closure']['delay_selections'] == {}
        def failed(*a, **kw): raise ValueError('native_rebuild_failed')
        namespace['original_delay'] = failed
        with pytest.raises(ValueError, match='native_rebuild_failed'):
            namespace['delay'](durable_policy, durable_report, target_date=DAY)
        assert namespace['closure']['delay_selections'] == {}
        namespace['original_delay'] = original
        namespace['closure']['delay_selections'] = deepcopy(saved)
        next(iter(namespace['closure']['delay_selections'].values()))['documents_sha256'] = '0'*64
        with pytest.raises(ValueError, match='startup_native_delay_selection_conflict'):
            namespace['delay'](durable_policy, durable_report, target_date=DAY)
        assert next(iter(namespace['closure']['delay_selections'].values()))['documents_sha256'] == '0'*64
        namespace['closure']['delay_selections'] = saved
    # Snapshot actual selected release code, which is byte-identical to the
    # native hook's delay inventory (the candidate changes only one docstring).
    for name, sha in collected['native_code_inventory'].items():
        path = request_fixture['selected']/name
        assert C._sha(path) == sha
        main['proof']['source_hashes'][str(path)] = sha
    for ref in collected['artifacts'].values():
        main['proof']['source_hashes'][ref['path']] = ref['sha256']
    main['proof']['delay_inventory_git_attestation'] = C._attest_delay_inventory(
        request_fixture['selected'], request_fixture['original_commit'],
        namespace['closure']['delay_selections'], main['proof']['source_hashes'])
    req = request_fixture['request']
    req['source_hashes'].update(main['proof']['source_hashes'])
    req['candidate_code_handoffs']['pre_submit_delay']['policy_sha256'] = policy['policy_sha256']
    req['manifest']['pre_submit_delay_handoff']['policy_sha256'] = policy['policy_sha256']
    req['manifest']['pre_submit_delay_handoff']['policy_path'] = str(policy_path)
    if damage == 'unobserved': namespace['closure']['delay_selections'] = {}
    _write_request(request_fixture, req)
    native_env = dict(KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ENABLED='true',
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_FILE=str(policy_path),
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_MANIFEST_SHA256=manifest['manifest_sha256'],
        KORSTOCKSCAN_PRE_SUBMIT_DELAY_POLICY_ACTIVE_DATE=DAY)
    if damage in {'missing_shard', 'corrupt_shard', 'membership'}:
        shard = report_path.parent/report['qualified_projection_ref']['path']
        if damage == 'membership':
            from src.engine.lifecycle import research_storage as S
            partition = next(S.iter_tree(report_path.parent, report['partitions_ref']))
            shard = report_path.parent/partition['membership']['path']
        if damage == 'missing_shard': shard.unlink()
        else: shard.write_text('{}')
    before = {str(path): (C._sha(path), path.stat().st_mtime_ns, path.stat().st_ctime_ns)
        for path in data.rglob('*') if path.is_file()}
    result = _child(request_fixture, MAIN_CHILD_SETUP + f"""
from src.engine.scalping import pre_submit_delay_tuning as T
from src.engine.scalping import pre_submit_delay_initial_policy as I
from src.engine.automation import pre_submit_delay_partitioned_research as P
out = T.prepare_runtime_policy(target_date={DAY!r}, env={native_env!r}, data_root=pathlib.Path({str(data)!r}))
if {damage!r} in ('missing_shard', 'corrupt_shard', 'membership', 'unobserved'):
    assert out['status'] == 'preparation_invalid', out
    assert T._PREPARED_DELAY_POLICY is None
else:
    assert out['status'] == 'prepared', out
    assert out['policy_sha256'] == {policy['policy_sha256']!r}
    selected = T._PREPARED_DELAY_POLICY.lookup(target_date={DAY!r}, market='REGULAR')
    assert selected == {expected_lookup!r}, selected
    if {damage!r} == 'selection':
        report, policy = I._read(pathlib.Path({str(report_path)!r})), I._read(pathlib.Path({str(policy_path)!r}))
        report['price_ready_pair_n'] += 1
        policy['report_sha256'] = I.digest({{k:v for k,v in report.items() if k!='policy_sha256'}})
        policy['policy_sha256'] = I.digest({{k:v for k,v in policy.items() if k!='policy_sha256'}})
        report['policy_sha256'] = policy['policy_sha256']
        try: I.validate(policy, report, target_date={DAY!r})
        except ValueError as exc:
            assert str(exc) == 'startup_delay_request_binding_invalid', str(exc)
        else: raise AssertionError('native selection recomputation was bypassed')
    receipt = C.validation_delegation_receipt()
    checked = receipt['delay_selections'][{policy['policy_sha256']!r}]
    assert checked['parent_full_selection_recomputed'] is True
    assert checked['child_recomputed'] is False
    assert checked['child_headers_and_physical_logical_trees_reverified'] is True
    for path, sha in C.preparation_delay_source_hashes().items():
        assert out['source_hashes'].setdefault(path, sha) == sha
    (run/'delay-result.json').write_text(json.dumps(dict(delegation=receipt,
        consumer=dict(status='loaded', source_hashes=out['source_hashes']))))
assert not list(run.glob('.verify-*'))
assert_no_forbidden_attempts()
""")
    assert result.returncode == 0, result.stderr
    assert (request_fixture['run']/'audit.jsonl').read_bytes() == b''
    after = {str(path): (C._sha(path), path.stat().st_mtime_ns, path.stat().st_ctime_ns)
        for path in data.rglob('*') if path.is_file()}
    assert before == after
    assert pointer.exists()
    assert not list(data.rglob('.verify-*'))
    if damage is None:
        from copy import deepcopy
        result = json.loads((request_fixture['run']/'delay-result.json').read_text())
        C.verify_preparation_delay_delegation(main['proof'], result['delegation'], req, result['consumer'])
        sources = result['consumer']['source_hashes']
        assert len(sources) > 2
        for change in ('missing', 'unknown', 'child_recomputed', 'source_missing'):
            value = deepcopy(result)
            if change == 'missing': value['delegation']['delay_selections'] = {}
            elif change == 'unknown': value['delegation']['delay_selections']['0'*64] = {}
            elif change == 'child_recomputed':
                value['delegation']['delay_selections'][policy['policy_sha256']]['child_recomputed'] = True
            else:
                shard = next(iter(value['delegation']['delay_selections'][policy['policy_sha256']]['source_hashes']))
                value['consumer']['source_hashes'].pop(shard)
            with pytest.raises(ValueError, match='startup_delay_child_selection_'):
                C.verify_preparation_delay_delegation(main['proof'], value['delegation'], req, value['consumer'])
        shard = next(iter(result['delegation']['delay_selections'][policy['policy_sha256']]['source_hashes']))
        Path(shard).write_bytes(b'{}')
        with pytest.raises(ValueError, match='research_shard_generation_changed'):
            C.verify_preparation_delay_delegation(main['proof'], result['delegation'], req, result['consumer'])
        with pytest.raises(ValueError, match='startup_source_changed'):
            V._recheck(sources)


@pytest.mark.parametrize('damage', ['pid', 'invalid_context'])
def test_delegated_delay_selection_rejects_stale_context(request_fixture, monkeypatch, damage):
    _main_fixture(request_fixture, monkeypatch)
    result = _child(request_fixture, MAIN_CHILD_SETUP + f"""
if {damage!r} == 'pid': C._CONTEXT['pid'] += 1
else: C._CONTEXT['valid'] = False
C.validate_preparation_delay_selection(None, None)
""")
    assert result.returncode != 0
    assert 'startup_code_context_' in result.stderr
    assert not list(request_fixture['run'].glob('.verify-*'))


def test_delay_physical_source_collection_obeys_claim_and_rejects_alias_generations(tmp_path, monkeypatch):
    from src.engine.lifecycle import research_storage as S, research_input_budget as B
    ref = S.write_tree(tmp_path, iter(()))
    path = tmp_path/ref['path']; raw = path.read_bytes(); replacement = raw+b' '
    changed = {**ref, 'sha256':hashlib.sha256(replacement).hexdigest(), 'size':len(replacement)}
    # Isolate the second physical-source/CAS walk. End-to-end tests above run
    # the actual logical/physical native reader and all nested membership rows.
    def rows(root, reference):
        if reference is changed: path.write_bytes(replacement)
        return iter(())
    monkeypatch.setattr(S, 'iter_tree', rows)
    report = dict(qualified_projection_ref=ref, partitions_ref=changed, cells_ref=ref)
    used = B.health()['used_bytes']
    with monkeypatch.context() as limits:
        limits.setattr(B, 'LIMIT_BYTES', used+1)
        with pytest.raises(ValueError, match='shared_research_budget_partition_resume_required'):
            C._delay_tree_sources(tmp_path, report)
    assert B.health()['used_bytes'] == used
    with pytest.raises(ValueError, match='startup_delay_shard_reference_conflict'):
        C._delay_tree_sources(tmp_path, report)
    assert B.health()['used_bytes'] == used


def test_ordinary_digest_session_does_not_opt_in_new_reporting_consumers(tmp_path,monkeypatch):
    from src.engine.infrastructure import validation_digest_session as D
    from src.engine.infrastructure import main_policy_loading as M
    from src.engine.automation import auxiliary_reader_readiness as A
    path=tmp_path/'raw.bin';path.write_bytes(b'a'*1048576)
    class Unrelated:
        def digest(self,path):raise AssertionError('generic session was incorrectly consumed')
    token=D.ACTIVE.set(Unrelated())
    try:
        assert M._sources(path)=={str(path):C._sha(path)}
        assert A._sha(path)==C._sha(path)
    finally:D.ACTIVE.reset(token)


@pytest.mark.parametrize('reader_generation', ['original', 'reviewed', 'unreviewed'])
def test_nested_native_inventories_keep_distinct_git_origins(tmp_path,tmp_path_factory,monkeypatch,reader_generation):
    """Parent native semantics are isolated; actual two-generation Git bytes
    and per-bundle validation stay real, including an old embedded V4 parent.
    """
    from src.engine.scalping import continuous_reversal_postclose as P
    r=releases.__wrapped__(tmp_path_factory)
    f=request_fixture.__wrapped__(tmp_path,r)
    fixture=_main_fixture(f,monkeypatch)
    owner='src/engine/scalping/reversal_path_runtime.py'
    source=r['root']/owner
    old=C._sha(source)
    source.write_bytes(source.read_bytes()+b'\n# Exact private code-origin fixture.\n')
    commit=_commit(r['root'],'distinct current native source generation')
    new=C._sha(source)
    parent=fixture['bundle']
    bundle=dict(bundle_sha256='d'*64,target_date=DAY,continuous_reversal=dict(
        schema='continuous_reversal_policy_v6',family_sha256='e'*64,release_commit=commit,
        contract_file_sha256={'reversal_path_runtime.py':new},native_parent_bundle=parent))
    proof=fixture['proof']; policy=Path(proof['policy_path']);policy.write_text(json.dumps(bundle))
    previous=fixture['manifest']; manifest=P.seal({**previous,'base_bundle_sha256':bundle['bundle_sha256'],
        'semantic_code_hashes':{'reversal_path_runtime.py':old}})
    if reader_generation != 'original':
        reader_hash = new if reader_generation == 'reviewed' else 'f'*64
        manifest = P.seal({**manifest, 'reader_code_hashes': {Path(owner).name:reader_hash}})
        monkeypatch.setattr(C, 'REVIEWED_PREPARATION_HISTORY', {owner:{(new, old)}})
    observed=next(iter(proof['closure']['manifests'].values()))
    Path(observed['path']).write_text(json.dumps(manifest))
    observed.update(bundle_sha256=bundle['bundle_sha256'],sha256=C._sha(observed['path']))
    closure=proof['closure'];closure['manifests']={manifest['artifact_content_sha256']:observed}
    closure['bundles'][bundle['bundle_sha256']]=dict(target_date=DAY,family_sha256='e'*64)
    native={**proof['native_verification'],'native_machine_closure':closure}
    intake=dict(selected_root=r['selected'],selected_commit=r['original_commit'],
        manifest={'target_date':DAY},receipt={'activation_candidate':{'bundle_sha256':bundle['bundle_sha256']}},
        native_verification=native)
    monkeypatch.setattr(C,'REVIEWED_PREPARATION_SOURCES',{owner:(old,new)})
    monkeypatch.setattr(C,'ROOT',r['root'])
    # SQLite metadata semantics are exercised by native auxiliary tests.
    from src.engine.scalping import reversal_auxiliary_next_session as A
    monkeypatch.setattr(A,'_database_signature',lambda manifest:None)
    if reader_generation == 'unreviewed':
        with pytest.raises(ValueError, match='origin_inventory_conflict'):
            C.bind_main_preparation(r['root'],commit,Path(f['request']['data_root']),intake)
        return
    result=C.bind_main_preparation(r['root'],commit,Path(f['request']['data_root']),intake)
    if reader_generation == 'reviewed':
        assert manifest['reader_code_hashes'][Path(owner).name] == new
        assert result['original_code_hashes'][owner] == old
    assert result['inventories'][0]['expected']['reversal_path_runtime.py']==new
    assert result['inventories'][1]['expected']['reversal_path_runtime.py']==old
    assert result['inventory_git_attestations'][parent['bundle_sha256']]['origin_commit']==r['original_commit']
    assert result['historical_semantic_code_sources'][manifest['artifact_content_sha256']][owner]['sha256']==old
    monkeypatch.setattr(C,'_main_context',lambda:result)
    for value in (bundle,parent):
        assert C.verify_validation_main_code(value,{'reversal_path_runtime.py':str(source)},
            {'reversal_path_runtime.py':new})
    import copy
    wrong=copy.deepcopy(parent);wrong['continuous_reversal']['contract_file_sha256']['reversal_path_runtime.py']='f'*64
    with pytest.raises(ValueError,match='inventory_unbound'):
        C.verify_validation_main_code(wrong,{'reversal_path_runtime.py':str(source)},{'reversal_path_runtime.py':new})
    bundle['continuous_reversal']['native_parent_bundle']['continuous_reversal']['release_commit']=commit
    policy.write_text(json.dumps(bundle))
    with pytest.raises(ValueError,match='inventory_git_origin_changed'):
        C.bind_main_preparation(r['root'],commit,Path(f['request']['data_root']),intake)


def _logical_fixture(f,monkeypatch):
    from src.engine.ai import offline_comparison_store as S
    from src.engine.scalping import reversal_auxiliary_input_transition as J
    from src.engine.scalping import reversal_auxiliary_next_session as A
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.infrastructure.validation_digest_session import identity
    value=_main_fixture(f,monkeypatch);proof=value['proof'];data=Path(f['request']['data_root'])
    metadata=dict(object_ids=[],request_ids=[],generations=[])
    with S.Store(data) as store:
        metadata['fingerprint_sha256']=J._ledger_fingerprint(store,metadata)
    manifest=P.seal({**value['manifest'],'policy_data_root':str(data),
        'ledger_data_root':str(data),'ledger_metadata':metadata})
    closure=proof['closure'];old=next(iter(closure['manifests']))
    observed=closure['manifests'][old];path=Path(observed['path']);path.write_text(json.dumps(manifest))
    database=json.loads(json.dumps(A._database_signature(manifest)))
    observed.update(sha256=C._sha(path),database=database,
        database_source_identities={v[0]:identity(v[0]) for v in database if v is not None})
    ident=manifest['artifact_content_sha256'];closure['manifests']={ident:observed}
    proof['historical_semantic_code_sources']={ident:proof['historical_semantic_code_sources'][old]}
    proof['source_hashes'][str(path)]=observed['sha256'];f['request']['source_hashes'][str(path)]=observed['sha256']
    _write_request(f,f['request']);value.update(manifest=manifest,database=Path(database[0][0]))
    return value


def test_native_logical_database_has_separate_exact_receipt_and_no_fullbyte_read(request_fixture,monkeypatch):
    f=_logical_fixture(request_fixture,monkeypatch)
    setup=MAIN_CHILD_SETUP.replace('A._database_signature = lambda manifest: None\n','')
    result=_child(request_fixture,setup+f"""
from src.engine.infrastructure import main_policy_loading as M
database=pathlib.Path({str(f['database'])!r})
original=pathlib.Path.open
def reject_db_bytes(path,*args,**kwargs):
    if path==database: raise AssertionError('global DB byte hash is not a logical receipt')
    return original(path,*args,**kwargs)
pathlib.Path.open=reject_db_bytes
logical={{}}
assert M._sources(database,logical_source_receipts=logical)=={{}}
assert set(logical)=={{str(database)}}
assert logical[str(database)]['source_kind']=='sqlite_ledger_container'
assert logical[str(database)]['manifest_proofs']
assert M._sources(run/'bound-input.json',logical_source_receipts={{}})
(run/'logical.json').write_text(json.dumps(logical))
assert_no_forbidden_attempts()
""")
    assert result.returncode==0,result.stderr
    receipts=json.loads((request_fixture['run']/'logical.json').read_text())
    # Fresh finite native rows, independent from the expired large-file cache.
    for entry in f['proof']['closure']['digest_entries'].values():entry['created']=0
    assert C.verify_preparation_logical_sources(f['proof'],receipts)==receipts
    with pytest.raises(ValueError,match='source_set_changed'):
        C.verify_preparation_logical_sources(f['proof'],{})
    bad=json.loads(json.dumps(receipts));next(iter(bad.values()))['manifest_proofs']={}
    with pytest.raises(ValueError,match='source_set_changed'):
        C.verify_preparation_logical_sources(f['proof'],bad)
    changed=f['database'].with_suffix('.replacement');changed.write_bytes(f['database'].read_bytes())
    changed.replace(f['database'])
    with pytest.raises(ValueError,match='database_changed|identity_changed'):
        C.verify_preparation_logical_sources(f['proof'],receipts)


def test_logical_source_rechecks_native_selected_rows_and_unknown_db_keeps_full_read(request_fixture,monkeypatch):
    from src.engine.scalping import reversal_auxiliary_input_transition as J
    from src.engine.infrastructure import main_policy_loading as M
    f=_logical_fixture(request_fixture,monkeypatch)
    receipts=C._native_logical_sources(f['proof'])
    monkeypatch.setattr(J,'_ledger_fingerprint',lambda *a:'0'*64)
    with pytest.raises(ValueError,match='ledger_changed'):
        C.verify_preparation_logical_sources(f['proof'],receipts)
    unrelated=request_fixture['run']/'unknown.sqlite3';unrelated.write_bytes(b'unregistered database')
    logical={}
    assert M._sources(unrelated,logical_source_receipts=logical)=={str(unrelated):C._sha(unrelated)}
    assert logical=={}


@pytest.fixture(scope='module')
def delay_contract_origins(tmp_path_factory):
    """Exact historical/current Git bytes, committed into private checkouts.

    These are source-inventory fixtures, not native selection/P5 verdicts.
    """
    result = {}
    for label, revision, count in (('original', '900234d791b0bf31797cd4e823d0ae40296f790b', 27),
                                   ('current', 'HEAD', 28)):
        root = tmp_path_factory.mktemp('delay-origin-' + label)
        raw = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + C._DELAY_CONTRACT_OWNER])
        paths = C._delay_contract_paths(raw)
        assert len(paths) == count
        inventory = {}
        for relative in paths:
            value = subprocess.check_output(['git', '-C', str(ROOT), 'show', revision + ':' + relative])
            path = root/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(value)
            inventory[relative] = hashlib.sha256(value).hexdigest()
        _git(root, 'init', '-q')
        commit = _commit(root, 'Exact ' + label + ' delay inventory bytes')
        records = {str(target): {'native_code_inventory':dict(inventory)} for target in (None, DAY)}
        result[label] = dict(root=root, commit=commit, inventory=inventory, paths=paths, records=records)
    assert set(result['current']['paths']) - set(result['original']['paths']) == {
        'src/engine/infrastructure/main_policy_loading.py'}
    return result


@pytest.mark.parametrize('label', ['original', 'current'])
def test_delay_inventory_attests_exact_origin_declaration_not_current_keys(delay_contract_origins, label):
    case = delay_contract_origins[label]
    sources = {}
    proof = C._attest_delay_inventory(case['root'], case['commit'], case['records'], sources)
    assert proof['contract_paths'] == case['paths']
    assert proof['code_hashes'] == case['inventory']
    assert proof['origin_commit'] == case['commit']
    assert proof['declaration_sha256'] == case['inventory'][C._DELAY_CONTRACT_OWNER]
    assert sources == {str(case['root']/path): sha for path, sha in case['inventory'].items()}


@pytest.mark.parametrize('damage', ['missing', 'extra', 'digest', 'mixed_old_new',
                                   'mixed_new_old', 'origin_commit', 'source_conflict'])
def test_delay_inventory_rejects_unknown_or_mixed_origin(delay_contract_origins, damage):
    from copy import deepcopy
    case = delay_contract_origins['current' if damage == 'mixed_new_old' else 'original']
    records = deepcopy(case['records']); commit = case['commit']; sources = {}
    first = next(iter(records.values()))['native_code_inventory']
    if damage == 'missing': first.pop(next(iter(first)))
    elif damage == 'extra': first['src/engine/infrastructure/main_policy_loading.py'] = '0'*64
    elif damage == 'digest': first[next(iter(first))] = '0'*64
    elif damage == 'mixed_old_new': first.update(delay_contract_origins['current']['inventory'])
    elif damage == 'mixed_new_old': records[next(iter(records))]['native_code_inventory'] = delay_contract_origins['original']['inventory']
    elif damage == 'origin_commit': commit = '0'*40
    else: sources[str(case['root']/C._DELAY_CONTRACT_OWNER)] = '0'*64
    with pytest.raises(ValueError, match='startup_delay_native_'):
        C._attest_delay_inventory(case['root'], commit, records, sources)


@pytest.mark.parametrize('damage', ['dirty', 'symlink', 'unknown_committed'])
def test_delay_inventory_requires_actual_files_and_exact_git_objects(delay_contract_origins, tmp_path, damage):
    import shutil
    case = delay_contract_origins['original']
    root = tmp_path/'source'; shutil.copytree(case['root'], root)
    path = root/C._DELAY_CONTRACT_OWNER
    if damage == 'symlink':
        saved = path.with_suffix('.saved'); path.rename(saved); path.symlink_to(saved)
        commit = case['commit']
    else:
        path.write_bytes(path.read_bytes() + b'\n# Changed origin file.\n')
        commit = _commit(root, 'Unknown new source bytes') if damage == 'unknown_committed' else case['commit']
    with pytest.raises(ValueError, match='startup_delay_native_'):
        C._attest_delay_inventory(root, commit, case['records'], {})


@pytest.mark.parametrize('expression', ["('src/unknown.py',)", "(OWNER,)",
    "('src/../bad.py', OWNER)", "(OWNER, OWNER)", "[OWNER]", "(False, OWNER)"])
def test_delay_inventory_declaration_is_literal_unique_and_canonical(expression):
    declaration = expression.replace('OWNER', repr(C._DELAY_CONTRACT_OWNER))
    if expression == '(OWNER,)': declaration = '(dynamic_path,)'
    with pytest.raises(ValueError):
        C._delay_contract_paths(('CONTRACT_PATHS = ' + declaration).encode())


@pytest.mark.parametrize('fault', [None, 'source', 'target', 'path'])
def test_cleanup_ai_preparation_pair_is_exact(fault):
    relative = 'src/engine/ai_engine_openai.py'
    old = '194f9dcd748a0c94fe49c12618c3c5eb9f3d81b07de494f0b59ddc349aa43584'
    current = 'bdcf09bf1f19e4cb649c01105c7aa363b04bddcb8749793a8f701cc06cc8d185'
    assert C._sha(Path(C.__file__).resolve().parents[3]/relative) == current
    if fault == 'source': old = '0'*64
    elif fault == 'target': current = '0'*64
    elif fault == 'path': relative = 'src/engine/kiwoom_sniper_v2.py'
    assert C.reviewed_preparation_pair(relative, old, current) is (fault is None)


@pytest.mark.parametrize('fault', [None, 'custody', 'pid', 'manifest', 'authority', 'date', 'prepared_metadata', 'env_change'])
@pytest.mark.parametrize('closed', [False, True])
def test_intraday_origin_is_rebound_inside_real_os_isolation(request_fixture, fault, closed):
    f = request_fixture
    request = f['request']
    proof = request['candidate_code_handoffs']['pre_submit_delay']
    origin = proof['origin']
    data = Path(request['data_root']); commit = origin['selected_release_commit']
    manifest = request['manifest']
    manifest['selected_release_sha'] = origin['origin_commit']
    manifest['manifest_sha256'] = C._digest(manifest)
    mp = data/'runtime/policy_bootstrap'/('runtime_policy_bootstrap_'+DAY+'.json')
    mp.parent.mkdir(parents=True); mp.write_text(json.dumps(manifest))
    folder = data/'runtime/policy_bootstrap/intraday_handoff'/DAY; folder.mkdir(parents=True)
    hp, cp = folder/(commit+'.json'), folder/(commit+'.consumed.json')
    identity = dict(pid=123, start_ticks='456', cwd=str(f['selected']/'src'))
    common = dict(target_date=DAY, selected_release_commit=commit, release_root=str(f['selected']),
                  manifest_sha256=manifest['manifest_sha256'])
    handoff = dict(**common, schema='intraday_policy_preserving_release_handoff_v1',
        authority='APPROVED_INTRADAY_POLICY_PRESERVING_RELEASE_HANDOFF', status='prepared_verified',
        actual_pid_consumed=False, policy_effect='unchanged', frozen_files={str(mp):C._sha(mp)})
    if fault == 'authority': handoff['authority'] = 'unapproved'
    hp.write_text(json.dumps(handoff))
    consumed = dict(**common, schema='intraday_policy_preserving_consumption_v1',status='pass',
        actual_pid_consumed=True,handoff_sha256=C._sha(hp),pid_identity=identity)
    if fault == 'custody': consumed['handoff_sha256'] = '0'*64
    if fault == 'pid': consumed['pid_identity'] = {**identity, 'start_ticks':'999'}
    if fault == 'date': consumed['target_date'] = '2026-10-16'
    cp.write_text(json.dumps(consumed))
    extra = {str(p):C._sha(p) for p in (mp,hp,cp)}
    origin.update(basis='verified_selected_intraday_code_handoff', pid_identity=identity,
        intraday_handoff_path=str(hp),intraday_handoff_sha256=C._sha(hp),
        intraday_consumed_path=str(cp),intraday_consumed_sha256=C._sha(cp))
    if closed:
        origin.update(basis='verified_closed_intraday_code_handoff', closed_observation=dict(
            schema='intraday_closed_consumption_observation_v1', target_date=DAY, release_commit=commit,
            pid_identity=identity, source_hashes=extra, runtime_effect=False,
            current_observation_verified=False, new_pid_consumption_claimed=False))
    origin['sources'].update(extra);proof['source_hashes'].update(extra);request['source_hashes'].update(extra)
    if fault == 'manifest': request['manifest'] = {**manifest, 'manifest_sha256':'0'*64}
    elif fault in {'prepared_metadata', 'env_change'}:
        prepared = json.loads(json.dumps(manifest))
        prepared.update(generated_at='2026-10-19T07:39:45+09:00', env_file='prepared/original.env')
        if fault == 'env_change': prepared['env_overrides'] = {'UNAPPROVED': 'true'}
        prepared['manifest_sha256'] = C._digest({k:v for k,v in prepared.items() if k!='manifest_sha256'})
        request['manifest'] = prepared
    _write_request(f, request)
    result = _child(f, 'install_validation_code_context(request)\n'+CALL)
    assert (result.returncode == 0) is (fault in {None, 'prepared_metadata'}), result.stderr


@pytest.mark.parametrize('fault', [None, 'missing_bundle', 'unknown_scope', 'origin', 'basis'])
def test_intraday_main_closure_requires_fresh_full_native_evidence(request_fixture, monkeypatch, fault):
    f = request_fixture
    main = _main_fixture(f, monkeypatch)
    request = f['request']; proof = main['proof']; native = proof['native_verification']
    native.update(validation_scope='intraday_preserved_historical_generation',
        preserved_preopen_commit=f['original_commit'],
        handoff_basis='intraday_preserved_preopen_generation_current_postclose_resealed')
    proof['delegation_basis'] = 'same_invocation_selected_intraday_native_validation'
    request['manifest']['selected_release_sha'] = f['original_commit']
    if fault == 'missing_bundle': proof['closure']['bundles'] = {}
    if fault == 'unknown_scope': native['validation_scope'] = 'sealed_generation'
    if fault == 'origin': native['preserved_preopen_commit'] = '0'*40
    if fault == 'basis': proof['delegation_basis'] = 'same_invocation_selected_native_full_verification'
    _write_request(f, request)
    result = _child(f, MAIN_CHILD_SETUP+'\nassert_no_forbidden_attempts()\n')
    assert (result.returncode == 0) is (fault is None), result.stderr



def test_reviewed_sor_scope_keeps_original_code_pin_and_rejects_other_bytes():
    name='src/trading/market/session_contract.py'
    old='3a4b68c7d8d613d6ab60e611b5b61f498be0b525b1e35e2bdf3d9d1d396b56a0'
    current=C._sha(ROOT/name)
    C._pairs({name:old},{name:current})
    with pytest.raises(ValueError,match='unreviewed'):
        C._pairs({name:old},{name:'0'*64})



@pytest.mark.parametrize('fault', [None, 'missing', 'outside', 'signature'])
def test_native_reader_dependencies_bind_selected_code_inside_isolation(request_fixture, monkeypatch, fault):
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    f=request_fixture; main=_main_fixture(f,monkeypatch);proof=main['proof'];request=f['request']
    relative='src/engine/scalping/ai_decision_quality.py';path=f['selected']/relative
    digest=C._sha(path)
    observed=next(iter(proof['closure']['manifests'].values()))
    observed['dependencies'].append([str(path),json.loads(json.dumps(N._signature(path)))])
    proof['native_reader_code_sources']={relative:digest}
    proof['source_hashes'][str(path)]=digest;request['source_hashes'][str(path)]=digest
    if fault=='missing':proof['native_reader_code_sources']={}
    elif fault=='outside':proof['native_reader_code_sources']={'../outside.py':digest}
    elif fault=='signature':observed['dependencies'][-1][1]=['changed']
    _write_request(f,request)
    result=_child(f,MAIN_CHILD_SETUP+'\nassert_no_forbidden_attempts()\n')
    assert (result.returncode==0) is (fault is None),result.stderr


@pytest.mark.parametrize('fault', [None, 'past', 'partial', 'source_date', 'no_policy'])
def test_isolated_stop_future_snapshot_preserves_native_tail_validation(request_fixture, monkeypatch, fault):
    import copy
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from src.engine.ai.holding_exit_vote import path_vote_store_path
    f=request_fixture;_main_fixture(f,monkeypatch);request=f['request'];data=Path(request['data_root'])
    stop=copy.deepcopy(request['candidate_code_handoffs']['pre_submit_delay']);stop['family']='main_stop'
    request['candidate_code_handoffs']['main_stop']=stop
    request['manifest']['main_stop_confirmation_receipt']=dict(target_date=DAY,source_date='2026-10-16',policy_sha256=stop['policy_sha256'])
    if fault=='source_date':request['manifest']['main_stop_confirmation_receipt']['source_date']='2026-10-15'
    if fault=='no_policy':request['candidate_code_handoffs'].pop('main_stop')
    day='2026-10-16' if fault=='past' else DAY
    row=dict(schema='holding_path_vote_v10',position_key='record:91',session_key=day,
        requested_at=datetime.fromisoformat(day+'T10:00:00').replace(tzinfo=ZoneInfo('Asia/Seoul')).timestamp())
    path=path_vote_store_path(data,'record:91');path.parent.mkdir(parents=True)
    raw=json.dumps(row).encode()+(b'' if fault=='partial' else b'\n');path.write_bytes(raw)
    _write_request(f,request)
    result=_child(f,MAIN_CHILD_SETUP+f"""
from pathlib import Path
from src.engine.automation import main_stop_postclose as post
post._future_unconsumed_vote_tail(Path(request['data_root']), '2026-10-16', Path({str(path)!r}), None)
assert_no_forbidden_attempts()
""")
    assert (result.returncode==0) is (fault is None),result.stderr
    if fault:
        reason={'past':'stop_vote_future_tail_scope_invalid','partial':'stop_vote_future_tail_invalid',
                'source_date':'startup_stop_snapshot_scope_invalid','no_policy':'startup_stop_snapshot_policy_required'}[fault]
        assert reason in result.stderr,result.stderr
    assert path.read_bytes()==raw and not Path(str(path)+'.lock').exists()


def test_auxiliary_inventory_keeps_reviewed_manifest_reader_origin(request_fixture, monkeypatch):
    from src.engine.scalping import continuous_reversal_postclose as P
    f=request_fixture;main=_main_fixture(f,monkeypatch);proof=main['proof'];request=f['request']
    relative='src/engine/scalping/reversal_auxiliary_next_session.py';name=Path(relative).name
    old='c32689f592a5f6558d3404bd9b5495330aefc45715feddf8e579c171d74901c1'
    current=C._sha(f['selected']/relative)
    manifest=P.seal({**main['manifest'],'next_session_code_hashes':{name:old}})
    original=next(iter(proof['closure']['manifests']));observed=proof['closure']['manifests'].pop(original)
    Path(observed['path']).write_text(json.dumps(manifest));observed['sha256']=C._sha(observed['path'])
    ident=manifest['artifact_content_sha256'];proof['closure']['manifests'][ident]=observed
    proof['historical_semantic_code_sources'][ident]=proof['historical_semantic_code_sources'].pop(original)
    proof['original_code_hashes']={**proof['original_code_hashes'],relative:current}
    proof['runtime_code_hashes']={**proof['runtime_code_hashes'],relative:current}
    for p in (f['selected']/relative,f['root']/relative,Path(observed['path'])):
        proof['source_hashes'][str(p)]=C._sha(p);request['source_hashes'][str(p)]=C._sha(p)
    _write_request(f,request)
    result=_child(f,MAIN_CHILD_SETUP+f"""
from pathlib import Path
manifest=json.loads(Path({observed['path']!r}).read_bytes())
bundle=json.loads(Path(request['main_preparation_code_handoff']['policy_path']).read_bytes())
proof=C.validation_auxiliary_preparation(manifest,bundle,Path(request['data_root']))
assert A._validation_code_inventory(manifest['next_session_code_hashes'], {{{name!r}:{current!r}}}, proof)
assert not A._validation_code_inventory({{{name!r}:'0'*64}}, {{{name!r}:{current!r}}}, proof)
assert_no_forbidden_attempts()
""")
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('fault', [None,'missing','scope','date','release','consumed','full',
    'source','bootstrap','activation','source_date','native_pid','prepared_manifest','live_as_prepared'])
def test_isolated_preserved_native_closure_requires_consumption_full_bootstrap_and_exact_sources(request_fixture,monkeypatch,fault):
    f=request_fixture;main=_main_fixture(f,monkeypatch);proof=main['proof'];request=f['request']
    data=Path(request['data_root']);commit=f['original_commit'];selected=str(f['selected'])
    native=proof['native_verification'];native.update(validation_scope='intraday_preserved_historical_generation',
        handoff_basis='intraday_preserved_preopen_generation_current_postclose_resealed',preserved_preopen_commit='a'*40)
    proof['delegation_basis']=C._native_main_basis(native)
    request['manifest']['selected_release_sha']='a'*40
    closure=proof['closure'];closure['manifests']={};proof['historical_semantic_code_sources']={}
    prepared=data/'runtime/policy_bootstrap/prepared'/DAY/'original'/'receipt.json'
    prepared.parent.mkdir(parents=True)
    prepared.write_text(json.dumps(dict(status='prepared_verified',target_date=DAY,source_date=native['source_date'],
        manifest_content_sha256='b'*64,activation_candidate={'bundle_sha256':proof['policy_sha256']})))
    bootstrap=prepared.parent/('runtime_policy_bootstrap_'+DAY+'.json');bootstrap.write_text(json.dumps({'manifest_sha256':'b'*64}))
    path=data/'runtime/policy_bootstrap/intraday_handoff'/DAY/(commit+'.json');path.parent.mkdir(parents=True)
    consumed=path.with_name(commit+'.consumed.json')
    handoff=dict(schema='intraday_policy_preserving_release_handoff_v1',status='prepared_verified',target_date=DAY,
        selected_release_commit=commit,release_root=selected,actual_pid_consumed=False,manifest_sha256='d'*64,
        prepared_receipt_path=str(prepared),prepared_receipt_sha256=C._sha(prepared),frozen_files={str(prepared):C._sha(prepared)})
    path.write_text(json.dumps(handoff));sha=C._sha(path)
    receipt=dict(schema='intraday_policy_preserving_consumption_v1',status='pass',actual_pid_consumed=True,
        handoff_sha256=sha,manifest_sha256='d'*64,target_date=DAY,selected_release_commit=commit,release_root=selected,
        pid_identity={'pid':123,'start_ticks':'456','cwd':selected+'/src'})
    consumed.write_text(json.dumps(receipt))
    record=dict(schema='startup_native_preserved_preopen_closure_v1',target_date=DAY,selected_release_commit=commit,
        handoff_path=str(path),consumed_path=str(consumed),manifest_sha256='d'*64,prepared_manifest_sha256='b'*64,
        sources={**handoff['frozen_files'],str(path):sha,str(consumed):C._sha(consumed)},
        full_bootstrap=dict(path=str(bootstrap),sha256=C._sha(bootstrap),write=False,full_native_verification=True,
            result=dict(status='pass',findings=[],target_date=DAY,manifest_sha256='b'*64)))
    closure['preserved_generations']={sha:record}
    proof['source_hashes'].update(C._preserved_native_sources(proof));request['source_hashes'].update(proof['source_hashes'])
    if fault=='missing':closure['preserved_generations']={}
    elif fault=='scope':native['validation_scope']='current_full_contract'
    elif fault=='date':record['target_date']='2026-10-20'
    elif fault=='release':record['selected_release_commit']='e'*40
    elif fault=='consumed':record['sources'][str(consumed)]='e'*64
    elif fault=='full':record['full_bootstrap']=None
    elif fault=='prepared_manifest':record['prepared_manifest_sha256']='e'*64
    elif fault=='live_as_prepared':record['full_bootstrap']['result']['manifest_sha256']=record['manifest_sha256']
    elif fault=='source':prepared.write_text('{}')
    elif fault=='bootstrap':bootstrap.write_text('{}')
    elif fault=='activation':proof['policy_sha256']='e'*64
    elif fault=='source_date':native['source_date']='2026-10-15'
    elif fault=='native_pid':closure['digest_binding']['pid']+=1
    _write_request(f,request)
    result=_child(f,MAIN_CHILD_SETUP+'''
proof=request['main_preparation_code_handoff']
assert proof['closure']['manifests']=={}
assert C.preparation_logical_sources()=={}
assert C.validation_raw_vote_sources(request['data_root'],request['main_preparation_code_handoff']['native_verification']['source_date'])
from src.engine.infrastructure.validation_digest_session import ACTIVE
from src.engine.automation.main_trailing_completed_store import admit_window
assert ACTIVE.get().binding['role']=='startup_validation'
assert admit_window(request['data_root'],request['target_date'])==0
assert_no_forbidden_attempts()
''')
    assert (result.returncode==0) is (fault is None),result.stderr
