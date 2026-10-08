"""Exact research prefix fixtures and versioned PRE/AFTER contract regressions."""
import copy
import json
from pathlib import Path
import pytest
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_state as R
from src.engine.scalping import reversal_extended_auxiliary as A
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping import continuous_reversal_policy_v6 as V
from src.engine.scalping import continuous_reversal_policy_v5 as V5
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_registry as G
from src.engine.scalping import reversal_policy_status as STATUS
from src.engine.scalping import reversal_operating_evaluation as E
from src.tests.test_reversal_path_policy import row,T

FIXTURES=json.loads((Path(__file__).parent/'fixtures/reversal_extended/signals.json').read_text())


@pytest.mark.parametrize('bid',list(C.NEW_DEFINITIONS))
def test_exact_research_definition_scope_and_typed_request(bid,tmp_path):
    d=C.definition(bid);assert P.digest(d)==bid.removeprefix('manual_extended_')+P.digest(d)[16:]
    snap=FIXTURES[bid];event=snap['event'];source=snap['source'];arm=U.V1.ARMS[1]
    assert C.matches(bid,event,event['branch_features']) is True
    inp,prompt,schema=U.production_request(source,arm,event=event)
    signal=next(s for s in inp['signals'] if s['policy_id']==bid)
    assert signal['phase']==C.PHASES[bid]
    assert signal['observed_signal']['root_contract']==d['root_contract']
    assert event['source_item'].endswith('_NX' if d['market']=='PRE' else '_AL')
    assert prompt.isascii()
    registry=G.definition(arm,input_version=U.VERSION);G.register(tmp_path,registry)
    assert G.production_request((event,source),registry)==(inp,prompt,schema)
    request=G.request((event,source),registry)
    assert request['candidate_input']==inp and request['candidate']['response_schema']==schema
    response=dict(schema=U.VERSION,decision_scope='COMMON_OPPORTUNITY',assessed_signal_refs=[s['ref'] for s in inp['signals']],
        risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],supporting_fact_ids=['observed_machine_signal'],contradicting_fact_ids=[],confidence=50)
    assert U.validate_response(response,inp,arm=arm)==[]
    response['assessed_signal_refs']=[]
    assert U.validate_response(response,inp,arm=arm)
    wrong=copy.deepcopy(event['branch_signals'][bid]);wrong['signal_proof']['root_contract']['unsupported']=True
    with pytest.raises(ValueError,match='definition_invalid'):A.validate_signal(wrong)


def test_peak_proof_never_fabricates_touch_and_retest_bounds_are_exact():
    for bid in C.NEW_DEFINITIONS:
        event=copy.deepcopy(FIXTURES[bid]['event']['branch_signals'][bid]);root=C.definition(bid)['root_contract']
        A.validate_signal(event)
        if root.get('confirmation')=='PEAK':
            assert 'touch_sequence' not in event['signal_proof']
            event['signal_proof']['touch_sequence']=event['native_sequence']-1
            with pytest.raises(ValueError,match='proof_invalid'):A.validate_signal(event)
        elif root.get('confirmation','').startswith('RETEST'):
            event['signal_proof']['root_contract']['maximum_wait_seconds']+=1
            with pytest.raises(ValueError,match='definition_invalid'):A.validate_signal(event)


def test_extended_catalog_keeps_old_registry_and_exact_route_scope():
    assert len(C.NEW_DEFINITIONS)==13
    for bid in C.OLD.DEFINITIONS:assert C.branch(bid)==C.OLD.branch(bid)
    for bid,d in C.NEW_DEFINITIONS.items():
        key='|'.join((d['symbol_group'],d['market'],d['price_band']))
        assert C.applicable(bid,key,d['route'])
        assert not C.applicable(bid,key,'SOR' if d['route']=='NXT' else 'NXT')
        assert C.OLD.SHA256!=C.SHA256


def test_old_confirmation_and_ask_unchanged_with_coverage_snapshot():
    from src.engine.scalping import reversal_path_runtime as OLD
    bid='legacy_dd5_ge_0_4_v1'
    old=OLD.State(branch_ids=[bid],offline=True);new=R.State(branch_ids=[bid],offline=True)
    values=[row(i,100) for i in range(121)]+[row(121,99.7),row(122,99.8),row(123,99.9)]
    previous=None
    for r in values:
        expected=old.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')
        actual=new.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')
        assert expected==actual
        cover=E.coverage(new,r,[bid],{},previous=previous)
        if r[0]==T+122:assert cover[bid]=='FALSE' # known low-based DD below .4
        previous=r


def test_status_registration_comparison_and_loaded_scopes_are_independent():
    r=dict(status='completed',cells=[dict(routes={'SOR':dict(status='operator_initial_registered')})],comparison_complete=False)
    state=STATUS.report_state(r)
    assert state['registration_state']=='registered'
    assert state['adoption_basis']=='operator_designated' and state['comparison_state']=='incomplete'
    assert sum(STATUS.operating_scope(V.scope_id(k,r)) for k,r in V.scopes())==48
    assert len(V.scopes())==128


def test_native_opportunity_namespace_unchanged_across_registry_version():
    from src.engine.scalping import reversal_operating_auxiliary as OLD
    for fixture in FIXTURES.values():assert U.opportunity(fixture['event'])==OLD.opportunity(fixture['event'])

from src.tests.test_continuous_reversal_policy_v3 import native
from src.tests.test_reversal_operating_policy import parent,replay,transport,authorize_initial


def test_v6_stage_keeps_old_versions_and_adds_exact_thirteen(replay,monkeypatch):
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import reversal_extended_registration as ER
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_tuning as AT
    root,base,machine=replay
    O.prepare_inputs(root,'2026-10-07',machine,base)
    O.L.calls(O,root,'2026-10-07',transport=transport,call_limit=5)
    authorize_initial(root,base)
    aux=O.auxiliary_report(root,'2026-10-07','2026-10-07',base,publish_policy=False)
    issued=json.loads((O.directory(root,'2026-10-07')/'machine.json').read_text())
    old=V5.stage(root,'2026-10-07','2026-10-07',issued,aux,target_date='2026-10-08',release_commit='a'*40)
    before=P.digest(old);V5.validate_sources(old,root)
    changes=P.seal(dict(schema='main_extended_registration_request_v1',kind='ADD',parent_bundle_sha256=old['bundle_sha256'],
        operator_receipt=ER.AUTHORITY,research_batch_sha256=C.RESEARCH_BATCH_SHA256,target_date='2026-10-12',
        source_receipts=[],scopes={d['symbol_group']+'|'+d['market']+'|'+d['price_band']+'|'+d['route']:dict(add=[b],remove=[]) for b,d in C.NEW_DEFINITIONS.items()},
        definition_hashes={b:P.digest(C.definition(b)) for b in C.NEW_DEFINITIONS}))
    P.write(ER.pending_path(root),changes)
    monkeypatch.setattr(N,'load_effective',lambda **kw:old)
    source=dict(normalized_sources=dict(partitions=[]));source=P.seal(source)
    m=O.machine_report(root,'2026-10-08','2026-10-08',old,source=source,publish_outputs=False)
    assert m['policy_schema']==V.SCHEMA and m['registration_change']==changes
    candidate=G.register(root,G.definition(U.V1.ARMS[1]))
    AT.configure(root,candidate=candidate,scopes=['samsung|PRE|ALL|NXT'],seed='extended-test')
    O.prepare_inputs(root,'2026-10-08',m,old)
    out=O.auxiliary_report(root,'2026-10-08','2026-10-08',old,publish_policy=True)
    assert out['comparison_complete'] is False and out['registration_state']=='registered'
    assert out['scope_census']['new_ready']==128
    assert (P.directory(root,'2026-10-08')/'call-freeze.json').exists()
    assert (P.directory(root,'2026-10-08')/'provider-results.jsonl').read_text()==''
    issued=json.loads((O.directory(root,'2026-10-08')/'machine.json').read_text())
    new=V.stage(root,'2026-10-08','2026-10-08',issued,out,target_date='2026-10-12',release_commit='a'*40)
    V.validate_sources(new,root)
    N.validate(new,target_date='2026-10-12')
    assert P.digest(old)==before
    V5.validate_sources(old,root)
    assert ER.pending(root,new,'2026-10-13') is None
    for sid,ids in old['continuous_reversal']['operating_manifest']['scopes'].items():
        added=set(new['continuous_reversal']['operating_manifest']['scopes'][sid])-set(ids)
        assert added==set(changes['scopes'].get(sid,{}).get('add',[]))
    for bid,d in C.NEW_DEFINITIONS.items():
        snapshot=FIXTURES[bid]
        # Actual held prefixes are old research dates; assessment itself has
        # no clock override or provider/order side effect.
        result=V.assess(new['continuous_reversal'],(snapshot['event'],snapshot['source']),symbol=snapshot['event']['symbol'],session=snapshot['event']['session'])
        assert result[0]['action']=='ENTER_NOW'
    changed=copy.deepcopy(new['continuous_reversal']);key,route=next(iter(changes['scopes'])).rsplit('|',1)
    changed['operating_manifest']['definitions'][next(iter(C.NEW_DEFINITIONS))]['filters']={}
    changed['family_sha256']=P.digest({k:v for k,v in changed.items() if k!='family_sha256'})
    with pytest.raises(ValueError):V.validate_family(changed)
    # Exercise the production callback, native claim receipt and same-tick
    # union before any provider or durable intent is allowed.
    from src.engine.scalping import reversal_current_backend as D
    from src.engine.scalping import reversal_source_diagnostics as DIAG
    runtime=D.V6
    monkeypatch.setattr(D,'_ACTIVE',D.OLD)
    monkeypatch.setattr(runtime.R,'restore_session_anchors',lambda *a:None)
    monkeypatch.setattr(runtime,'_STATES',{});monkeypatch.setattr(runtime,'_CLAIMS',{})
    D.configure_bundle(new,data_root=root,day='2026-10-07')
    for i,price in [(i,100) for i in range(121)]+[(121,98),(122,98.1)]:
        D.observe_normalized('005930','NXT_PREMARKET',dict(observed_epoch=T+i,provider_trade_epoch=T+i,
            trade_price=price,transport_epoch=1,route_sequence=i+1,inline_best_bid=price-.01,inline_best_ask=price+.01,
            trade_qty=10,aggressor_side='BUY',item='005930_NX',market_route='nxt',effective_venue='NXT'))
    monkeypatch.setattr(DIAG.time,'time',lambda:T+122)
    claim=DIAG.claim_snapshot_with_receipt('005930','NXT','NXT_PREMARKET',now=T+122,item='005930_NX',family_sha256=new['continuous_reversal']['family_sha256'])
    assert claim['backend']=='operating_v6'
    assert 'manual_extended_f9a43c88911fdc0b' in claim['snapshot'][0]['branch_signals']
    assert DIAG.verified_registration(claim,claim['source_registration_receipt'])
    assert D.validate_any_claim(claim,new['continuous_reversal']['family_sha256'],now=T+122)==claim['snapshot']
    assert DIAG.claim_snapshot_with_receipt('005930','NXT','NXT_PREMARKET',now=T+122,item='005930_NX',family_sha256=new['continuous_reversal']['family_sha256']) is None
    # The subsequent publication must use the v6 bounded tuning consumer,
    # carrying membership even when the registered v2 challenger is incompatible.
    monkeypatch.setattr(N,'load_effective',lambda **kw:new)
    following=O.machine_report(root,'2026-10-12','2026-10-12',new,source=source,publish_outputs=False)
    O.prepare_inputs(root,'2026-10-12',following,new)
    carried=O.auxiliary_report(root,'2026-10-12','2026-10-12',new,publish_policy=False)
    assert carried['comparison_contract']==AT.SCHEMA
    assert all(r['payload']['binding']['input_version']==U.VERSION for c in carried['cells'] for r in c['routes'].values())


@pytest.mark.parametrize('alive,invalid,reused',[(False,False,False),(True,True,False),(True,False,True)])
def test_current_projection_never_turns_prepared_into_pid_consumption(tmp_path,monkeypatch,alive,invalid,reused):
    from src.engine.automation import intraday_release_handoff as H
    N=STATUS.N;day='2026-10-08';identity=dict(pid=42,start_ticks=10,cwd='/release/src');commit='a'*40
    selector=dict(git_commit=commit,release_root='/release',actual_pid_receipt=dict(pid=42))
    pointer=dict(bundle_sha256='b'*64)
    bundle=dict(bundle_sha256='b'*64,continuous_reversal=dict(source_date='2026-10-07',machine_cells={'samsung|PRE|ALL':dict(routes={'NXT':{}})}))
    P.write(tmp_path/'runtime/runtime_release_selection.json',selector);P.write(N.root(tmp_path)/'current.json',pointer)
    P.write(N.root(tmp_path)/'generations'/('b'*64+'.json'),bundle)
    receipt=dict(pid_identity=dict(identity,start_ticks=9 if reused else 10),bundle_sha256='b'*64,release_commit=commit,planned_scopes=1)
    receipt['receipt_sha256']=P.digest(receipt);P.write(N.root(tmp_path)/'consumed'/day/'42.json',receipt)
    def identity_reader(pid):
        if not alive:raise OSError('gone')
        return identity
    def loader(**kw):
        if invalid:raise ValueError('source_changed')
        return bundle
    monkeypatch.setattr(H,'_identity',identity_reader);monkeypatch.setattr(H,'DATA_DIR',tmp_path)
    monkeypatch.setattr(H,'verify',lambda *a,**kw:dict(status='pass'));monkeypatch.setattr(N,'load_effective',loader)
    result=STATUS.current_view(tmp_path,day=day)
    assert result['prepared_state']=='verified'
    assert result['pid_consumption_state']==('not_started' if not alive else 'mismatch' if reused else 'consumed_exact')
    assert result['policy_validation_state']==('invalid' if invalid else 'valid')
    assert result['observed_decision_scope_count']==(0 if alive else None)
    if alive:
        calls=[]
        def dies(pid):
            calls.append(pid)
            if len(calls)>1:raise OSError('gone during read')
            return identity
        monkeypatch.setattr(H,'_identity',dies)
        assert STATUS.current_view(tmp_path,day=day)['status']=='changed_during_read'
