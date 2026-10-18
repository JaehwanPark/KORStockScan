"""Future auxiliary carry preserves source evidence and exact stopped CAS."""
import copy
import subprocess
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_auxiliary_next_session as B
from src.engine.scalping import reversal_auxiliary_input_transition as J
from src.engine.scalping import reversal_auxiliary_intraday as I
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_auxiliary_transition as X
from src.engine.scalping import reversal_auxiliary_research_wire as OLD_W
from src.engine.ai import offline_comparison_store as S

SIDS = ['034020|PRE|20000_TO_100000|NXT', '196170|PRE|GE_100000|NXT']
VERIFY_FROZEN = B._verify_frozen
SEMANTIC_CODE_PARITY = B._semantic_code_parity


@pytest.fixture
def carry(tmp_path, monkeypatch):
    data = tmp_path / 'data'; ledger = tmp_path / 'ledger'; frozen = tmp_path / 'frozen'
    frozen.mkdir()
    base = G.definition(J.M.U.V1.ARMS[1], input_version=J.M.U.VERSION)
    current = G.compact_definition(base, research_wire_contract=OLD_W.contract())
    bindings = {J.V.scope_id(k, r): current['registry_sha256'] for k, r in J.V.scopes()}
    base_values = [base, current]
    definitions = {v['registry_sha256']: v for v in base_values}
    changes = {}; details = {}
    for sid in SIDS:
        candidate = G.production_definition(current, scope_ids=[sid])
        changes[sid] = candidate['registry_sha256']; definitions[candidate['registry_sha256']] = candidate
        details[sid] = dict(before=current['registry_sha256'], after=candidate['registry_sha256'])
    for value in base_values:
        G.register(data, value)
    old = dict(bundle_sha256='a'*64, source_date='2026-10-15', target_date='2026-10-16',
        continuous_reversal=dict(schema='continuous_reversal_policy_v6', family_sha256='f'*64,
            parent_bundle_sha256='p'*64, release_commit='1'*40, effective_mode='next_session',
            machine_cells={}, auxiliary_cells={}, operating_manifest=dict(detector_manifest_hash='d'*64, scopes={}, definitions={})))
    for sid in bindings:
        key, route = sid.rsplit('|', 1)
        old['continuous_reversal']['machine_cells'].setdefault(key, dict(routes={}))['routes'][route] = dict(
            backend='union_v6', payload=dict(branches=[dict(branch_id='branch')]), payload_sha256='e'*64, scope_execution_hash='c'*64)
        old['continuous_reversal']['auxiliary_cells'].setdefault(key, dict(routes={}))['routes'][route] = dict(
            payload=dict(arm=base['base_arm'], binding=J.M.U.binding(base['base_arm'])))
        old['continuous_reversal']['operating_manifest']['scopes'][sid] = ['branch']
    old['continuous_reversal']['operating_manifest']['definitions']['branch'] = dict(root='FIRST', filters={'dd': .4})
    target = copy.deepcopy(old); target.update(bundle_sha256='b'*64, source_date='2026-10-16', target_date='2026-10-19')
    target['continuous_reversal'].update(parent_bundle_sha256=old['bundle_sha256'], family_sha256='9'*64, release_commit='2'*40)
    target['continuous_reversal']['operating_manifest']['detector_manifest_hash'] = '8'*64
    for cell in target['continuous_reversal']['machine_cells'].values():
        for route in cell['routes'].values(): route['scope_execution_hash'] = '7'*64
    inherited = P.seal(dict(auxiliary_registry_bindings=bindings, auxiliary_reader_code_hashes=I.code_hashes()))
    inherited_path = N.root(data) / 'sources' / ('reversal-' + inherited['artifact_content_sha256'] + '.json')
    P.write(inherited_path, inherited)
    for value in (old, target):
        value['continuous_reversal'].update(auxiliary_report_sha256=inherited['artifact_content_sha256'],
            report_file_sha256={'auxiliary': P.file_hash(inherited_path)})
    old_path = tmp_path / 'source-bundle.json'; P.write(old_path, old)
    target_path = N.root(data) / 'generations' / (target['bundle_sha256'] + '.json'); P.write(target_path, target)
    candidate_path = N.root(data) / 'candidates/policy_2026-10-19.json'; P.write(candidate_path, target)
    P.write(N.root(data) / 'current.json', dict(bundle_sha256=old['bundle_sha256']))
    P.write(data / 'runtime/runtime_release_selection.json', dict(approved_by='user', actual_pid_consumed=False))
    index = data / 'runtime/policy_bootstrap/prepared/2026-10-19/latest.json'; P.write(index, dict(fixture=True))
    prepared = tmp_path / 'preserved-prepared.json'; P.write(prepared, dict(schema='next_preopen_readiness_v1',
        status='prepared_verified', source_date='2026-10-16', target_date='2026-10-19',
        selected_release_commit='2'*40, activation_candidate={'bundle_sha256': target['bundle_sha256']}))
    with S.Store(ledger) as store:
        metadata = dict(object_ids=[], request_ids=[], generations=[])
        metadata['fingerprint_sha256'] = J._ledger_fingerprint(store, metadata)
    source = P.seal(dict(schema=J.SCHEMA, status='prepared', base_bundle_sha256=old['bundle_sha256'],
        bundle_target_date=old['target_date'], verified_pairs=50, verified_raw_responses=100,
        changes=changes, rollback_bindings={s:bindings[s] for s in SIDS}, base_bindings=bindings,
        registry_definitions=definitions, scopes=details, input_transition_code_hashes={}, reader_code_hashes={},
        ledger_data_root=str(ledger), ledger_pack_paths=[], ledger_metadata=metadata, sources=[]))
    source_path = tmp_path / 'source-proof.json'; P.write(source_path, source)
    calls = []
    def verify(*args):
        calls.append(args)
        return dict(schema='frozen_auxiliary_input_validation_v1', source_manifest_sha256=source['artifact_content_sha256'],
            source_bundle_sha256=old['bundle_sha256'], verified_pairs=50, verified_raw_responses=100,
            input_transition_code_hashes={}, network_forbidden=True, provider_called=False, policy_published=False)
    monkeypatch.setattr(B, '_verify_frozen', verify)
    monkeypatch.setattr(B, '_frozen_inventory', lambda *a: {})
    monkeypatch.setattr(B, '_semantic_code_parity', lambda *a: {})
    monkeypatch.setattr(B, '_bindings', lambda *a: (copy.deepcopy(bindings), [], []))
    monkeypatch.setattr(N, 'validate', lambda *a, **k: None)
    monkeypatch.setattr(I, 'independent_scopes', lambda *a: set())
    from src.engine.automation import ordered_intraday_deploy as ordered
    from src.engine.infrastructure import runtime_release_router as router
    monkeypatch.setattr(ordered, '_main_pids', lambda: [])
    monkeypatch.setattr(ordered, '_session_absent', lambda: True)
    monkeypatch.setattr(router, 'selected_release', lambda *a: (Path(B.__file__).resolve().parents[3], '2'*40))
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None): return cls(2026, 10, 17, 17, tzinfo=I.K.KST)
    monkeypatch.setattr(B, 'datetime', Clock)
    B._VERIFIED.clear()
    return SimpleNamespace(data=data, ledger=ledger, frozen=frozen, old=old, target=target, old_path=old_path,
        target_path=target_path, source=source, source_path=source_path, prepared=prepared, bindings=bindings,
        calls=calls, candidate_path=candidate_path, index=index)


def prepare(f):
    return B.prepare(f.data, source_manifest_path=f.source_path, source_bundle_path=f.old_path,
        frozen_root=f.frozen, target_bundle_path=f.target_path, prepared_path=f.prepared)


def test_prepare_is_readonly_and_cross_parent_scope_equivalence(carry):
    f = carry; before = {p:p.read_bytes() for p in f.data.rglob('*') if p.is_file()}
    manifest = prepare(f)
    assert manifest['base_bundle_sha256'] != f.source['base_bundle_sha256']
    assert manifest['changes'] == f.source['changes'] and manifest['verified_raw_responses'] == 100
    assert all(p['source'] == p['target'] for p in manifest['scope_behavior'].values())
    assert before == {p:p.read_bytes() for p in f.data.rglob('*') if p.is_file()}
    assert X.validate_manifest(f.data, manifest, f.target) == manifest


@pytest.mark.parametrize('field', ['backend', 'payload', 'payload_sha256', 'definition', 'branch', 'auxiliary'])
def test_behavior_change_rejected(carry, field):
    f = carry; key, route = SIDS[0].rsplit('|',1); fam=f.target['continuous_reversal']
    if field == 'definition': fam['operating_manifest']['definitions']['branch']['root']='CHANGED'
    elif field == 'branch': fam['operating_manifest']['scopes'][SIDS[0]]=[]
    elif field == 'auxiliary': fam['auxiliary_cells'][key]['routes'][route]['payload']['arm']='CHANGED'
    else: fam['machine_cells'][key]['routes'][route][field]='CHANGED'
    P.write(f.target_path,f.target)
    with pytest.raises(ValueError,match='scope_behavior_changed'): prepare(f)


def test_any_baseline_binding_change_rejected(carry):
    f=carry; f.bindings[next(k for k in f.bindings if k not in SIDS)]='z'*64
    with pytest.raises(ValueError,match='baseline_changed'): prepare(f)


@pytest.mark.parametrize('field',['source','root','target','code','metrics','scope'])
def test_resealed_proof_mutation_rejected(carry,field):
    f=carry;m=prepare(f);bad=copy.deepcopy(m)
    if field=='source': bad['source_manifest']['sha256']='0'*64
    if field=='root': bad['policy_data_root']=str(f.ledger)
    if field=='target': bad['bundle_target_date']='2026-10-20'
    if field=='code': bad['next_session_code_hashes']={}
    if field=='metrics': bad['scopes'][SIDS[0]]['before']='0'*64
    if field=='scope': bad['changes']['samsung|PRE|ALL|NXT']='0'*64
    with pytest.raises(ValueError): B.validate_manifest(f.data,P.seal(bad),f.target)


def test_warm_cache_and_unrelated_ledger_write_do_not_replay(carry):
    f=carry;m=prepare(f);B.validate_manifest(f.data,m,f.target);cold=len(f.calls)
    assert B.validate_manifest(f.data,m,f.target)==m and len(f.calls)==cold
    with S.Store(f.ledger) as store: store.put({'unrelated':True})
    assert B.validate_manifest(f.data,m,f.target)==m and len(f.calls)==cold
    assert B.validate_manifest(f.data,m,f.target,cached_only=True)==m


def test_locked_cache_invalidation_never_replays(carry):
    f=carry;m=prepare(f);B.validate_manifest(f.data,m,f.target);cold=len(f.calls)
    with S.Store(f.ledger) as store: store.put({'unrelated':True})
    with pytest.raises(ValueError,match='cache_changed_before_publish'):
        B.validate_manifest(f.data,m,f.target,cached_only=True)
    assert len(f.calls)==cold


def test_publish_only_future_day_and_preserves_current_and_source(carry):
    f=carry;m=prepare(f);before=(N.root(f.data)/'current.json').read_bytes();source=f.source_path.read_bytes()
    body=B.publish_future(f.data,m,confirm=I.AUTHORITY,reason='User approved next session research adoption')
    assert I.current(f.data,f.target,day='2026-10-19')==body
    assert X.validate_published(f.data,body,f.target)==m
    assert (N.root(f.data)/'current.json').read_bytes()==before and f.source_path.read_bytes()==source
    assert not (I.root(f.data)/'current.json').exists()
    assert body['effective_from'].startswith('2026-10-19T00:00:00')
    assert body['prepared_at_kst'].startswith('2026-10-17T17:00:00')
    assert len([sid for sid,ident in body['bindings'].items() if ident!=f.bindings[sid]])==2


def test_native_reader_readiness_consumes_future_overlay_and_proof_closure(carry):
    from src.engine.automation import auxiliary_reader_readiness as A
    f=carry;m=prepare(f)
    body=B.publish_future(f.data,m,confirm=I.AUTHORITY,reason='User approved next session research adoption')
    receipt=A.verify_auxiliary_reader('2026-10-19',data_root=f.data,preparation=True,bundle=f.target)
    assert receipt['status']=='pass' and receipt['target_overlay']['artifact_content_sha256']==body['artifact_content_sha256']
    assert str(f.source_path) in receipt['source_hashes']
    A.verify_bound_sources(receipt)


def test_future_publication_retry_returns_original_generation(carry):
    f=carry;m=prepare(f)
    first=B.publish_future(f.data,m,confirm=I.AUTHORITY,reason='approved')
    assert B.publish_future(f.data,m,confirm=I.AUTHORITY,reason='retry')==first
    assert len(list((I.root(f.data)/'generations').glob('*.json')))==1


@pytest.mark.parametrize('field',['bindings','changes','rollback_bindings','previous_overlay_sha256','effective_mode',
                                 'effective_from','revoked_overlays','revoked_scope_overlays'])
def test_idempotent_retry_rejects_resealed_extra_behavior(carry,field):
    f=carry;m=prepare(f);first=B.publish_future(f.data,m,confirm=I.AUTHORITY,reason='approved')
    bad=copy.deepcopy(first)
    if field=='bindings': bad[field][next(s for s in f.bindings if s not in SIDS)]=m['changes'][SIDS[0]]
    elif field in {'changes','rollback_bindings'}: bad[field]={}
    elif field=='previous_overlay_sha256': bad[field]='0'*64
    elif field=='effective_from': bad[field]='2026-10-19T23:00:00+09:00'
    elif field=='revoked_overlays': bad[field]=['0'*64]
    elif field=='revoked_scope_overlays': bad[field]={'0'*64:[SIDS[0]]}
    else: bad[field]='intraday'
    path=I.root(f.data)/'days/2026-10-19'/(f.target['bundle_sha256']+'.json');P.write(path,P.seal(bad))
    with pytest.raises(ValueError,match='existing_target_overlay_behavior_changed'):
        B.publish_future(f.data,m,confirm=I.AUTHORITY,reason='retry')
    with pytest.raises(ValueError,match='existing_target_overlay_behavior_changed'):
        I.current(f.data,f.target,day='2026-10-19')


def test_source_change_inside_publisher_lock_never_writes_day_pointer(carry,monkeypatch):
    f=carry;m=prepare(f);original=B.fcntl.flock;calls=[]
    def lock(fd, operation):
        calls.append(1)
        if len(calls)==3:
            P.write(f.source_path,P.seal(dict(f.source,verified_pairs=49)))
        return original(fd,operation)
    monkeypatch.setattr(B.fcntl,'flock',lock)
    with pytest.raises(ValueError,match='cache_changed_before_publish'):
        B.publish_future(f.data,m,confirm=I.AUTHORITY,reason='approved')
    assert not list((I.root(f.data)/'days').glob('**/*.json'))


@pytest.mark.parametrize('kind',['authority','selector','candidate','prepared_index','preopen','pid'])
def test_publication_guards_fail_before_policy_write(carry,monkeypatch,kind):
    f=carry;m=prepare(f)
    if kind=='selector': P.write(f.data/'runtime/runtime_release_selection.json',dict(changed=True))
    if kind=='candidate': P.write(f.candidate_path,dict(changed=True))
    if kind=='prepared_index': P.write(f.index,dict(changed=True))
    if kind=='preopen': P.write(f.data/'report/threshold_cycle_preopen_status/threshold_cycle_preopen_2026-10-19.status.json',{})
    if kind=='pid':
        from src.engine.automation import ordered_intraday_deploy as ordered
        monkeypatch.setattr(ordered,'_main_pids',lambda:[123])
    with pytest.raises(ValueError):
        B.publish_future(f.data,m,confirm='invalid' if kind=='authority' else I.AUTHORITY,reason='approved')
    assert not list((I.root(f.data)/'days').glob('**/*.json'))


def test_normal_monday_parent_and_selector_changes_do_not_invalidate_proof(carry):
    f=carry;m=prepare(f);B.validate_manifest(f.data,m,f.target);B._VERIFIED.clear()
    P.write(N.root(f.data)/'current.json',dict(bundle_sha256=f.target['bundle_sha256']))
    P.write(f.data/'runtime/runtime_release_selection.json',dict(actual_pid_consumed=True))
    assert B.validate_manifest(f.data,m,f.target)==m


def test_native_scope_rollback_keeps_original_transition_as_lineage(carry):
    f=carry;m=prepare(f);body=B.publish_future(f.data,m,confirm=I.AUTHORITY,reason='approved')
    rollback=copy.deepcopy(body);rollback['rollback_reason']='operator rollback'
    rollback['bindings'][SIDS[0]]=m['rollback_bindings'][SIDS[0]]
    rollback=P.seal(rollback)
    assert X.validate_published(f.data,rollback,f.target)==m


def test_failed_frozen_proof_has_no_policy_side_effect(carry,monkeypatch):
    f=carry;before={p:p.read_bytes() for p in f.data.rglob('*') if p.is_file()}
    def failure(*args): raise ValueError('original frozen proof failed')
    monkeypatch.setattr(B,'_verify_frozen',failure)
    with pytest.raises(ValueError,match='frozen proof failed'):prepare(f)
    assert before=={p:p.read_bytes() for p in f.data.rglob('*') if p.is_file()}


def test_identical_source_in_another_release_preserves_historical_paths(carry,monkeypatch,tmp_path):
    import importlib.util
    f=carry;m=prepare(f)
    path=tmp_path/'other-release/src/engine/scalping/reversal_auxiliary_next_session.py'
    path.parent.mkdir(parents=True);path.write_bytes(Path(B.__file__).read_bytes())
    spec=importlib.util.spec_from_file_location('copied_auxiliary_next_session',path)
    copied=importlib.util.module_from_spec(spec);spec.loader.exec_module(copied)
    for name in ['_verify_frozen','_frozen_inventory','_semantic_code_parity','_bindings']:
        monkeypatch.setattr(copied,name,getattr(B,name))
    assert copied.validate_manifest(f.data,m,f.target)==m


def test_frozen_script_blocks_network_and_writers(carry,monkeypatch):
    f=carry;seen={}
    def run(command,**kwargs):
        seen.update(command=command,**kwargs)
        return SimpleNamespace(stdout='{"ok":true}\n')
    monkeypatch.setattr(B.subprocess,'run',run)
    assert VERIFY_FROZEN(f.frozen,f.source_path,f.old_path)=={'ok':True}
    assert 'network_forbidden' in seen['command'][3] and 'sys.addaudithook' in seen['command'][3]
    assert 'P.write = N._atomic_write_json = G.register = denied' in seen['command'][3]
    assert seen['env']['PYTHONDONTWRITEBYTECODE']=='1' and seen['cwd']==f.frozen


@pytest.mark.parametrize('failure',[subprocess.CalledProcessError(1,['fixture'],stderr='source mismatch'),
    subprocess.TimeoutExpired(['fixture'],180),OSError('unavailable'),'','not-json'])
def test_frozen_validation_errors_remain_controlled_source_gaps(carry,monkeypatch,failure):
    f=carry
    def run(*args,**kwargs):
        if isinstance(failure,Exception): raise failure
        return SimpleNamespace(stdout=failure)
    monkeypatch.setattr(B.subprocess,'run',run)
    with pytest.raises(ValueError,match='auxiliary_next_session_frozen_validation_failed') as caught:
        VERIFY_FROZEN(f.frozen,f.source_path,f.old_path)
    assert caught.value.__cause__ is not None


def test_os_delegation_rebuilds_native_semantics_without_relaunching_frozen_process(carry, monkeypatch):
    from src.engine.infrastructure import startup_validation_code_context as context
    f=carry; manifest=prepare(f)
    proof=dict(manifest=manifest,frozen_inventory=manifest['frozen_inventory'],
        frozen_validation=manifest['frozen_validation'],original_code_hashes={},runtime_code_hashes={})
    # Only the OS proof is isolated here; its real-kernel binding has a separate
    # suite. Native prepare still rebuilds scope, registry, sources and ledger.
    def verified(value,bundle,data):
        assert value==manifest and bundle==f.target and Path(data)==f.data
        return proof
    monkeypatch.setattr(context,'validation_auxiliary_preparation',verified)
    def forbidden(*args):raise AssertionError('delegated frozen process/Git was relaunched')
    monkeypatch.setattr(B,'_frozen_inventory',forbidden)
    monkeypatch.setattr(B,'_verify_frozen',forbidden)
    B._VERIFIED.clear()
    assert B.validate_manifest(f.data,manifest,f.target)==manifest
    B._VERIFIED.clear()
    f.bindings[next(k for k in f.bindings if k not in SIDS)]='z'*64
    with pytest.raises(ValueError,match='baseline_changed'):
        B.validate_manifest(f.data,manifest,f.target)


def test_validation_manifest_argument_without_real_context_does_not_bypass_frozen_proof(carry):
    f=carry;manifest=prepare(f)
    with pytest.raises(ValueError,match='validation_delegation_arguments_changed'):
        B.prepare(f.data,source_manifest_path=f.source_path,source_bundle_path=f.old_path,
            frozen_root=f.frozen,target_bundle_path=f.target_path,prepared_path=f.prepared,
            _validation_manifest=manifest)


@pytest.mark.parametrize('changed',['handoff','original_source'])
def test_formal_source_handoff_connects_prepare_cold_and_warm_native_consumers(carry,tmp_path,monkeypatch,changed):
    """Private Git/code-shape fixture; frozen economic replay stays isolated.

    The real source-pair algorithm, H producer/validator, A native preparation,
    sealed source/dependency inventory and warm-cache invalidation are exercised.
    This is not an operational research or publication PASS.
    """
    from src.tests.test_reversal_auxiliary_source_handoff import source as source_fixture
    from src.engine.scalping import reversal_auxiliary_source_handoff as H
    f=source_fixture.__wrapped__(carry,tmp_path,monkeypatch)
    monkeypatch.setattr(B,'__file__',str(H._code_path(f.current,'reversal_auxiliary_next_session.py')))
    monkeypatch.setattr(X,'__file__',str(H._code_path(f.current,'reversal_auxiliary_transition.py')))
    monkeypatch.setattr(I,'code_hashes',lambda:dict(f.source['reader_code_hashes']))
    monkeypatch.setattr(B,'_semantic_code_parity',SEMANTIC_CODE_PARITY)
    calls=[]
    def frozen(*args):
        calls.append(args)
        return dict(schema='frozen_auxiliary_input_validation_v1',source_manifest_sha256=f.source['artifact_content_sha256'],
            source_bundle_sha256=N._read(f.original_path)['bundle_sha256'],verified_pairs=50,verified_raw_responses=100,
            input_transition_code_hashes=f.source['input_transition_code_hashes'],network_forbidden=True,
            provider_called=False,policy_published=False)
    monkeypatch.setattr(B,'_verify_frozen',frozen)
    value=H.build(f.data,previous_manifest_path=f.previous_path,previous_overlay_path=f.overlay_path,
        target_bundle_path=f.target_path)
    path=tmp_path/'source-code-handoff.json';P.write(path,value)
    prepared=tmp_path/'new-prepared.json';P.write(prepared,dict(schema='next_preopen_readiness_v1',
        status='prepared_verified',source_date=f.target['source_date'],target_date=f.target['target_date'],
        selected_release_commit=f.current_commit,activation_candidate={'bundle_sha256':f.target['bundle_sha256']}))
    args=dict(source_manifest_path=f.source_path,source_bundle_path=f.original_path,frozen_root=f.frozen,
        target_bundle_path=f.target_path,prepared_path=prepared)
    with pytest.raises(ValueError,match='current_semantic_code_changed'):
        B.prepare(f.data,**args)
    manifest=B.prepare(f.data,**args,source_code_handoff_path=path)
    assert len(calls)==1
    assert manifest['source_code_handoff']=={**B._reference(path),'artifact_content_sha256':value['artifact_content_sha256']}
    assert manifest['semantic_code_hashes']==f.previous['semantic_code_hashes']
    assert {r['path']:r['sha256'] for r in manifest['sources']}.items()>=value['source_hashes'].items()
    assert str(path) in dict(B._dependencies(manifest))
    B._VERIFIED.clear()
    assert B.validate_manifest(f.data,manifest,f.target)==manifest
    assert len(calls)==2
    def unexpected(*args,**kwargs):raise AssertionError('warm cache rebuilt immutable handoff')
    monkeypatch.setattr(H,'validate',unexpected)
    assert B.validate_manifest(f.data,manifest,f.target)==manifest
    modified=path if changed=='handoff' else f.source_path
    modified.write_bytes(modified.read_bytes()+b' ')
    with pytest.raises(ValueError,match='source_changed'):
        B.validate_manifest(f.data,manifest,f.target)
