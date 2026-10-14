"""Adversarial auxiliary CAS, scope rollback, historical and cold inheritance tests."""
import copy
from datetime import datetime
from pathlib import Path
import pytest
from src.engine.scalping import reversal_auxiliary_intraday as I,reversal_auxiliary_registry as G,reversal_auxiliary_transition as X
from src.engine.scalping import reversal_auxiliary_research_wire as OLD,reversal_extended_union as U
from src.engine.scalping import continuous_reversal_postclose as P,continuous_reversal_policy_v5 as V,mechanistic_entry_runtime_policy as N


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    old=G.definition(U.V1.ARMS[1],input_version=U.VERSION);oldid=G.register(tmp_path,old)
    candidate=G.definition(U.V1.ARMS[1],input_version=U.VERSION,prompt=old['prompt']+'Use only observed evidence.\n');G.register(tmp_path,candidate)
    new=G.compact_definition(candidate,research_wire_contract=OLD.contract());newid=G.register(tmp_path,new)
    mc={};ac={}
    for key,route in V.scopes():
        mc.setdefault(key,dict(routes={}));ac.setdefault(key,dict(routes={}))
        mc[key]['routes'][route]=dict(backend='union_v6')
        ac[key]['routes'][route]=dict(payload=dict(arm=old['base_arm'],binding=U.binding(old['base_arm'])))
    b=dict(bundle_sha256='b'*64,target_date='2026-10-08',continuous_reversal=dict(family_sha256='f'*64,
        operating_manifest={'detector_manifest_hash':'d'*64},machine_cells=mc,auxiliary_cells=ac,
        auxiliary_report_sha256='a'*64,report_file_sha256={}))
    monkeypatch.setattr(N,'load_effective',lambda **kw:b)
    N.root(tmp_path).mkdir(parents=True,exist_ok=True)
    refs=I.effective_bindings(tmp_path,b,day='2026-10-08')
    scopes=['samsung|AFTER|ALL|SOR','other_non_fixed|AFTER|LT_20000|SOR']
    points=[dict(outcome='WIN',verdicts={'current':'PASS','candidate':'PASS'}),dict(outcome='FAIL_TIMEOUT',verdicts={'current':'PASS','candidate':'CAUTION'})]
    m=dict(current=X.T.matrix([(p['outcome'],p['verdicts']['current']) for p in points]),
        candidate=X.T.matrix([(p['outcome'],p['verdicts']['candidate']) for p in points]),paired_points=2)
    evaluation=P.seal(dict(scopes={s:m for s in scopes},parent_bundle_sha256=b['bundle_sha256'],research={'purpose':'evaluation'}))
    ep=tmp_path/'evaluations'/'proof.json';P.write(ep,evaluation)
    research=P.seal(dict(research_complete=True,observed_current_pointer={'bundle_sha256':b['bundle_sha256']},
        selected_research_candidates=[dict(scope=s,current_registry=oldid,candidate_registry=candidate['registry_sha256'],evaluation_sha256=evaluation['artifact_content_sha256'],compact_wire=OLD.contract()) for s in scopes]))
    rp=tmp_path/'research.json';P.write(rp,research)
    body=P.seal(dict(schema=X.SCHEMA,base_bundle_sha256=b['bundle_sha256'],operating_day='2026-10-08',expected_parent=None,
        base_bindings_sha256=P.digest(refs),comparison_baseline_kind=X.BASELINE,changes={s:newid for s in scopes},rollback_bindings={s:oldid for s in scopes},
        scopes={s:dict(evaluation_sha256=evaluation['artifact_content_sha256'],before=oldid,after=newid,metrics=m,points=points) for s in scopes},
        sources=[X.reference(p) for p in (rp,ep,G.directory(tmp_path)/(newid+'.json'))],reader_code_hashes=I.code_hashes(),wire_contract=X.W.contract()))
    P.write(X.folder(tmp_path)/(body['artifact_content_sha256']+'.json'),body)
    return tmp_path,b,body,scopes,oldid,newid


def test_atomic_multiple_scopes_idempotent_and_cas(prepared):
    root,b,m,scopes,old,new=prepared;clock=datetime(2026,10,8,15,1,tzinfo=I.K.KST)
    r=X.publish(root,m,confirm=I.AUTHORITY,now=clock)
    assert sum(v==new for v in r['bindings'].values())==2
    assert X.publish(root,m,confirm=I.AUTHORITY,now=clock)==r
    broken=P.seal(dict(m,expected_parent='c'*64))
    with pytest.raises(ValueError,match='cas'):X.publish(root,broken,confirm=I.AUTHORITY,now=clock)
    assert I.current(root,b,day='2026-10-08')==r


@pytest.fixture
def wire_repair_prepared(prepared, monkeypatch):
    """Isolate the auxiliary publisher; native bundle tests own machine validation."""
    root, bundle, *_ = prepared
    manifest = bundle['continuous_reversal']['operating_manifest']
    manifest.update(scopes=[V.scope_id(k, r) for k, r in V.scopes()], definitions={})
    N._atomic_write_json(N.root(root)/'current.json', {'bundle_sha256': bundle['bundle_sha256']})
    P.write(N.root(root)/'generations'/(bundle['bundle_sha256']+'.json'), bundle)
    report = P.seal(dict(auxiliary_registry_bindings=I.effective_bindings(root, bundle, day='2026-10-08'),
                        auxiliary_reader_code_hashes=I.code_hashes()))
    path = N.root(root)/'sources'/('reversal-'+bundle['continuous_reversal']['auxiliary_report_sha256']+'.json')
    P.write(path, report)
    bundle['continuous_reversal']['report_file_sha256']['auxiliary'] = P.file_hash(path)
    P.write(N.root(root)/'generations'/(bundle['bundle_sha256']+'.json'), bundle)
    monkeypatch.setattr(N, 'validate', lambda *args, **kwargs: None)
    clock = datetime(2026, 10, 8, 15, 1, tzinfo=I.K.KST)
    prompt_repair = I.prepare_contract_repair(root, bundle, expected_parent=None, now=clock)
    parent = I.publish_contract_repair(root, prompt_repair, expected_parent=None,
                                      confirm=I.CONTRACT_REPAIR_AUTHORITY, now=clock)
    return root, bundle, clock, parent


def test_wire_contract_repair_preserves_incumbent_policy_and_frozen_prompt_history(wire_repair_prepared):
    from datetime import timedelta
    from src.engine.scalping import reversal_auxiliary_wire as W
    from src.tests.test_reversal_extended_policy import FIXTURES
    root, bundle, clock, parent = wire_repair_prepared
    before = {str(p):p.read_bytes() for p in root.rglob('*.json')}
    args = dict(expected_parent=parent['artifact_content_sha256'], now=clock+timedelta(seconds=1),
                repair_schema=I.WIRE_REPAIR_SCHEMA)
    repair = I.prepare_contract_repair(root, bundle, **args)
    assert before == {str(p):p.read_bytes() for p in root.rglob('*.json')}
    assert repair['scope_count'] == 128 and repair['old_bindings'] == parent['bindings']
    assert repair['clarification'] == I.WIRE_SUPPORT_CONTRACT
    overlay = I.publish_contract_repair(root, repair, expected_parent=args['expected_parent'],
                                       confirm=I.CONTRACT_REPAIR_AUTHORITY, now=args['now'])
    assert all(Path(p).read_bytes() == content for p, content in before.items()
               if not p.endswith('/current.json') and '/days/' not in p)
    assert (N.root(root)/'current.json').read_bytes() == before[str(N.root(root)/'current.json')]
    fixture = next(iter(FIXTURES.values()))
    snap = fixture['event'], fixture['source']
    for old_id, replacement in repair['registry_mapping'].items():
        old = G.load(root, old_id)
        new = G.load(root, replacement['registry_sha256'])
        assert new['schema'] == G.SCHEMA_V2
        assert new['research_registry_sha256'] == old_id
        assert new['research_wire_contract']['research_executed'] is False
        for key in ('prompt', 'model', 'base_arm', 'max_output_tokens', 'reasoning_effort',
                    'input_version', 'validator_version', 'projector_sha256'):
            assert new[key] == old[key]
        logical, prompt, schema = G.production_request(snap, new)
        assert G.production_request(snap, old) == (logical, prompt, schema)
        env = G.envelope(logical, new)
        pass_schema = env['wire_schema']['properties']['screen']['anyOf'][0]
        assert pass_schema['properties']['fact']['enum'] == [env['citation_map']['observed_machine_signal']]
        raw = dict(assessed={env['citation_map'][s['ref']]:True for s in logical['signals']},
                   screen=dict(verdict='PASS', risk='NO_BLOCKING_RISK', fact=env['citation_map']['observed_machine_signal']),
                   confidence=50)
        frozen = copy.deepcopy(raw)
        assert G.decode_response(raw, logical, new)['supporting_fact_ids'] == ['observed_machine_signal']
        assert raw == frozen
        assert G.request(snap, new)['candidate']['schema_name'] == W.VERSION
    assert I.at_confirmation(root, bundle, clock.timestamp()+.5) == parent
    assert I.at_confirmation(root, bundle, clock.timestamp()+1) == overlay
    assert I.publish_contract_repair(root, repair, expected_parent=args['expected_parent'],
        confirm=I.CONTRACT_REPAIR_AUTHORITY, now=args['now']) == overlay
    reverted = I.rollback(root, expected_parent=overlay['artifact_content_sha256'], reason='wire repair regression',
                          confirm=I.AUTHORITY, now=clock+timedelta(seconds=2))
    assert reverted['bindings'] == parent['bindings']
    assert overlay['artifact_content_sha256'] in reverted['revoked_overlays']


@pytest.mark.parametrize('defect', ['prompt', 'model', 'wire_contract', 'research_claim', 'scope', 'source', 'parent'])
def test_wire_contract_repair_rejects_mutation_before_pointer_write(wire_repair_prepared, defect):
    root, bundle, clock, parent = wire_repair_prepared
    repair = I.prepare_contract_repair(root, bundle, expected_parent=parent['artifact_content_sha256'],
                                      now=clock, repair_schema=I.WIRE_REPAIR_SCHEMA)
    bad = copy.deepcopy(repair)
    replacement = next(iter(bad['registry_mapping'].values()))
    if defect in {'prompt', 'model'}: replacement[defect] = 'changed'
    elif defect == 'wire_contract': replacement['wire_contract']['version'] = 'changed'
    elif defect == 'research_claim': replacement['research_wire_contract']['research_executed'] = True
    elif defect == 'scope': bad['new_bindings'].pop(next(iter(bad['new_bindings'])))
    elif defect == 'source': bad['source_hashes'][next(iter(bad['source_hashes']))] = '0'*64
    elif defect == 'parent': bad['expected_parent'] = '0'*64
    with pytest.raises(ValueError):
        I.publish_contract_repair(root, P.seal(bad), expected_parent=parent['artifact_content_sha256'],
                                  confirm=I.CONTRACT_REPAIR_AUTHORITY, now=clock)
    assert I.current(root, bundle, day='2026-10-08') == parent


def test_original_confirmation_selects_wire_and_scope_revoke_is_local(prepared):
    root,b,m,scopes,old,new=prepared
    clock=datetime(2026,10,8,15,1,tzinfo=I.K.KST)
    r=X.publish(root,m,confirm=I.AUTHORITY,now=clock)
    def assessment(scope,epoch):
        key,route=scope.rsplit('|',1)
        return dict(policy_version=V.SCHEMA,action='ENTER_NOW',cell_key=key,route=route,event={'epoch':epoch})
    before=assessment(scopes[0],clock.timestamp()-.1)
    assert I.selected_definition(root,b,before)==(None,None)
    I.validate_decision(root,{'continuous_reversal_assessment':before},b,now=clock.timestamp()+.1)
    pending=[]
    for scope in scopes:
        a=assessment(scope,clock.timestamp()+.1)
        definition,overlay=I.selected_definition(root,b,a)
        assert definition['registry_sha256']==new and definition['schema']==G.SCHEMA_V2
        a.update(auxiliary_registry_sha256=new,auxiliary_binding=G.binding(definition),
                 auxiliary_base_bundle_sha256=b['bundle_sha256'],auxiliary_overlay_sha256=overlay['artifact_content_sha256'])
        pending.append({'continuous_reversal_assessment':a})
        I.validate_decision(root,pending[-1],b,now=clock.timestamp()+.2)
    I.rollback(root,expected_parent=r['artifact_content_sha256'],reason='scoped test',confirm=I.AUTHORITY,
               now=datetime.fromtimestamp(clock.timestamp()+1,I.K.KST),scopes=[scopes[0]])
    with pytest.raises(ValueError,match='generation_revoked'):
        I.validate_decision(root,pending[0],b,now=clock.timestamp()+1.1)
    I.validate_decision(root,pending[1],b,now=clock.timestamp()+1.1)


def test_scope_rollback_preserves_other_scope_and_newer_generation(prepared):
    root,b,m,scopes,old,new=prepared;clock=datetime(2026,10,8,15,1,tzinfo=I.K.KST)
    r=X.publish(root,m,confirm=I.AUTHORITY,now=clock)
    reverted=I.rollback(root,expected_parent=r['artifact_content_sha256'],reason='scope test',confirm=I.AUTHORITY,now=clock,scopes=[scopes[0]])
    assert reverted['bindings'][scopes[0]]==old and reverted['bindings'][scopes[1]]==new
    assert reverted['revoked_scope_overlays'][r['artifact_content_sha256']]==[scopes[0]]
    with pytest.raises(ValueError,match='cas'):X.publish(root,m,confirm=I.AUTHORITY,now=clock)


def test_changed_source_with_same_size_and_warm_cache_is_rejected(prepared):
    root,b,m,*_=prepared;X.validate_manifest(root,m,b)
    p=Path(m['sources'][0]['path']);text=p.read_text();p.write_text(text.replace('true','null',1))
    with pytest.raises(ValueError,match='source_changed'):X.validate_manifest(root,m,b)


def test_resealed_scope_metrics_and_registry_tampering_rejected(prepared):
    root,b,m,scopes,old,new=prepared
    bad=copy.deepcopy(m);bad['scopes'][scopes[0]]['metrics']['candidate']['TP']=10;bad=P.seal(bad)
    with pytest.raises(ValueError,match='evidence_binding'):X.validate_manifest(root,bad,b)
    bad=copy.deepcopy(m);bad['changes']['other_non_fixed|PRE|LT_20000|NXT']=new;bad['scopes']['other_non_fixed|PRE|LT_20000|NXT']=bad['scopes'][scopes[0]];bad=P.seal(bad)
    with pytest.raises(ValueError,match='scope_unqualified'):X.validate_manifest(root,bad,b)


def test_crash_after_pointer_write_retries_same_generation(prepared,monkeypatch):
    root,b,m,*_=prepared;clock=datetime(2026,10,8,15,1,tzinfo=I.K.KST);original=I.current;calls=0
    def readback(*args,**kwargs):
        nonlocal calls
        calls+=1
        result=original(*args,**kwargs)
        if calls==3:raise OSError('crash after pointer')
        return result
    monkeypatch.setattr(I,'current',readback)
    with pytest.raises(OSError):X.publish(root,m,confirm=I.AUTHORITY,now=clock)
    monkeypatch.setattr(I,'current',original)
    persisted=I.read(I.root(root)/'current.json')
    assert X.publish(root,m,confirm=I.AUTHORITY,now=clock)==persisted


def test_historical_day_and_cold_inherited_scope_rollback(prepared,monkeypatch):
    root,b,m,scopes,old,new=prepared;clock=datetime(2026,10,8,15,1,tzinfo=I.K.KST)
    r=X.publish(root,m,confirm=I.AUTHORITY,now=clock)
    aux=P.seal(dict(auxiliary_registry_bindings=r['bindings'],auxiliary_reader_code_hashes=I.code_hashes(),
        auxiliary_rollback_bindings=r['rollback_bindings'],auxiliary_independent_scopes=scopes,
        evaluated_base_bundle=b['bundle_sha256'],operating_day='2026-10-08',evaluated_overlay_parent=r['artifact_content_sha256']))
    p=N.root(root)/'sources'/('reversal-'+aux['artifact_content_sha256']+'.json');P.write(p,aux)
    next_b=copy.deepcopy(b);next_b.update(bundle_sha256='e'*64,target_date='2026-10-12')
    next_b['continuous_reversal'].update(auxiliary_report_sha256=aux['artifact_content_sha256'],report_file_sha256={'auxiliary':P.file_hash(p)})
    I._INHERITED.clear();monkeypatch.setattr(N,'load_effective',lambda **kw:next_b)
    assert I.inherited(root,next_b)[scopes[0]]==new
    restored=I.rollback(root,expected_parent=None,reason='inherited failure',confirm=I.AUTHORITY,
        now=datetime(2026,10,12,8,1,tzinfo=I.K.KST),scopes=[scopes[0]])
    assert restored['bindings'][scopes[0]]==old and restored['bindings'][scopes[1]]==new
    assert I.current(root,b,day='2026-10-08')==r
    I.validate_inheritance_cutoff(root,next_b)
    revised=P.seal(dict(r,rollback_reason='late source change'))
    I.write_day_pointer(root,revised)
    with pytest.raises(ValueError,match='prepared_overlay_generation_changed'):I.validate_inheritance_cutoff(root,next_b)
