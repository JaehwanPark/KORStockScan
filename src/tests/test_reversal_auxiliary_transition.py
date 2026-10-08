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
