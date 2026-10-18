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
        assert C._sha(ROOT/path)==new
        C._pairs({path:old},{path:new})
        with pytest.raises(ValueError,match='unreviewed'):
            C._pairs({path:old},{path:'0'*64})
    with pytest.raises(ValueError,match='inventory_changed'):
        C._pairs({'owner':'a'*64},{})


@pytest.mark.parametrize('change',['selector','selected_head','candidate_head','request_alias'])
def test_installed_main_context_rechecks_control_generation_per_digest(request_fixture,monkeypatch,change):
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
reused_digest({str(f['raw'])!r})
""")
    finally:
        worker.join(timeout=25)
        if target.is_symlink():target.unlink()
        target.write_bytes(before)
    assert not worker.is_alive() and not errors,errors
    assert result.returncode!=0
    assert 'startup_' in result.stderr,result.stderr


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


def test_nested_native_inventories_keep_distinct_git_origins(tmp_path,tmp_path_factory,monkeypatch):
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
    result=C.bind_main_preparation(r['root'],commit,Path(f['request']['data_root']),intake)
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
