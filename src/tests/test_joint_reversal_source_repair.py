"""Real causal detector/reader contracts for the joint operating successor."""
import copy
from datetime import datetime
from types import SimpleNamespace
import pytest
from src.engine.scalping import reversal_joint_catalog as J
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_state as S
from src.engine.scalping import reversal_extended_auxiliary as A
from src.engine.scalping import continuous_reversal as K

T=datetime(2026,10,13,16,20,tzinfo=K.KST).timestamp()
def row(i,p=110000,qty=1):return [T+i,1,i+1,p,p,p+1,qty,1,1,'036930_AL',0]
def feed(state,values):
    result=[]
    for value in values:result+=state.observe(value,symbol='036930',venue='SOR',session='KRX_NXT_AFTERMARKET')
    return result

@pytest.mark.parametrize('warm,vwap_truth',[(20,'UNKNOWN'),(121,'TRUE')])
def test_composed_confirmation_keeps_original_and_never_emits_dependency(warm,vwap_truth):
    bid=J.ALIASES['jusung_after_refined'];base='legacy_dd5_ge_0_4_v1'
    values=[row(i) for i in range(warm)]+[row(warm,109300,100000),row(warm+1,109400),row(warm+2,109500)]
    original=S.State(branch_ids=[base],offline=True,session_anchor=values[0])
    candidate=S.State(branch_ids=[bid],offline=True,session_anchor=values[0])
    old=feed(original,values);new=feed(candidate,values)
    assert old and new
    originals={r['event']['event_id']:r['event']['branch_signals'][base] for r in old}
    for ready in new:
        assert set(ready['event']['branch_signals'])=={bid}
        e=ready['event']['branch_signals'][bid];A.validate_signal(e)
        assert e['epoch']==originals[e['event_id']]['epoch']
        assert e['entry_ask']==originals[e['event_id']]['entry_ask']
        assert e['signal_proof']['refinement_truth']==vwap_truth
    assert all(base not in r['event']['branch_signals'] for r in candidate.ready)

def test_refinement_false_consumes_confirmation_without_later_refinement_root():
    bid=J.ALIASES['jusung_after_refined']
    state=S.State(branch_ids=[bid],offline=True,session_anchor=row(0))
    values=[row(i) for i in range(121)]+[row(121,109300),row(122,109400),row(123,109500)]
    assert not feed(state,values)
    assert not state.ready
    # Price at/above VWAP alone cannot invent a new original confirmation.
    assert not feed(state,[row(124,109500,100000)])

def test_independent_breakout_has_no_first_turn_dependency():
    bid=J.ALIASES['jusung_after_breakout'];state=S.State(branch_ids=[bid],offline=True,session_anchor=row(0))
    result=feed(state,[row(i) for i in range(61)]+[row(61,110100)])
    assert result and bid in result[-1]['event']['branch_signals']
    e=result[-1]['event']['branch_signals'][bid];A.validate_signal(e)
    assert e['decision_phase']=='HIGH_BREAKOUT'
    assert 'anchor_event_id' not in e['signal_proof']

def test_diagnostic_rolling_dd_is_bound_without_overwriting_base_cache():
    state=S.State(branch_ids=['legacy_dd5_ge_0_4_v1'],offline=True,session_anchor=row(0))
    feed(state,[row(i) for i in range(61)]+[row(61,109300)])
    assert 'dd' not in state._feature_values
    assert state.diagnostic_rolling['identity']==tuple(row(61,109300)[:3])
    assert state.diagnostic_rolling['values']['dd']>0

def test_content_addressed_policy_ref_preserves_version_and_detects_tampering(tmp_path):
    from src.engine.lifecycle.policy_snapshot_reference import persist,resolve
    from src.engine.lifecycle.avg_down_policy_replay import snapshot_version
    snapshot={'schema':'avg_down_full_policy_snapshot_v1','rules':{'LIMIT':5},'files':{'original':'x'*20000}}
    ref=persist(snapshot,tmp_path)
    assert resolve(ref)==snapshot and snapshot_version(ref)==snapshot_version(snapshot)
    assert len(str(ref))<len(str(snapshot))/10
    again=persist(snapshot,tmp_path);assert again==ref
    from pathlib import Path
    Path(ref['path']).write_text('{}')
    with pytest.raises(ValueError,match='source_changed'):resolve(ref)


def test_policy_components_reuse_static_source_bytes_when_only_one_file_changes(tmp_path):
    from src.engine.lifecycle.policy_snapshot_reference import persist,resolve
    from pathlib import Path
    snapshot={'schema':'avg_down_full_policy_snapshot_v1','rules':{'LIMIT':5},
        'files':{'constant':'x'*200000,'moving':{'peak':100}},'loaded_code':{'static':'f'*200000}}
    ref=persist(snapshot,tmp_path);assert resolve(ref)==snapshot
    folder=Path(ref['path']).parent
    before={p.name:p.stat().st_size for p in folder.rglob('*.json')}
    newer=copy.deepcopy(snapshot);newer['files']['moving']['peak']=101
    second=persist(newer,tmp_path);assert resolve(second)==newer
    after={p.name:p.stat().st_size for p in folder.rglob('*.json')}
    assert sum(size for name,size in after.items() if name not in before)<3000


def test_anchor_writer_coalesces_new_streams_and_catches_up_during_write(tmp_path,monkeypatch):
    import threading
    from src.engine.scalping import reversal_anchor_index as I
    callbacks=[];writes=[]
    monkeypatch.setattr(I,'_VERSIONS',{});monkeypatch.setattr(I,'_PENDING',set())
    monkeypatch.setattr(I,'_SINK',lambda callback,**kw:(callbacks.append(callback) or {'status':'queued'}))
    owner=SimpleNamespace(_LOCK=threading.RLock(),_ANCHORS={},_ANCHOR_CURSORS={})
    def save(root,day,anchors,cursors,**kwargs):
        writes.append(anchors)
        if len(writes)==1:
            owner._ANCHORS[('123456','SOR','123456_AL','REGULAR',day)]=[T,1,1,10000]
            assert I.enqueue(root,day,owner)
        return dict(structured_append_succeeded=True)
    monkeypatch.setattr(I,'save',save)
    for _ in range(100):assert I.enqueue(tmp_path,'2026-10-13',owner)
    assert len(callbacks)==1
    assert callbacks.pop()()['structured_append_succeeded']
    assert len(writes)==2 and len(writes[-1])==1 and not I._PENDING

def test_new_stream_anchor_is_initialized_after_nonempty_day_restore(monkeypatch):
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from pathlib import Path
    import json
    bundle=json.loads((Path(__file__).resolve().parents[2]/'data/runtime/mechanistic_entry_policy/generations'/f'{J.PARENT}.json').read_text())
    # This is a frozen read, never configure or mutate a runtime policy file.
    f=bundle['continuous_reversal']['native_parent_bundle']['continuous_reversal']
    monkeypatch.setattr(R,'_FAMILY',f);monkeypatch.setattr(R,'_GENERATION',f['family_sha256'])
    monkeypatch.setattr(R,'_STATES',{});monkeypatch.setattr(R,'_ANCHORS',{})
    day='2026-10-13';monkeypatch.setattr(R,'_RESTORED_DAYS',{day});monkeypatch.setattr(R,'_EMPTY_PREFIX_DAYS',set())
    stamp=datetime(2026,10,13,10,tzinfo=K.KST).timestamp()
    envelope=dict(observed_epoch=stamp,provider_trade_epoch=stamp,trade_price=10000,
        transport_epoch=1,route_sequence=1,inline_best_bid=10000,inline_best_ask=10001,
        trade_qty=1,aggressor_side='BUY',item='123456_AL',market_route='krx_nxt_integrated')
    R.observe_normalized('123456','KRX_REGULAR',envelope)
    key=('123456','SOR','123456_AL','REGULAR',day)
    assert R._ANCHORS[key]==[stamp,1,1,10000.]
    R.observe_normalized('123456','KRX_REGULAR',dict(envelope,observed_epoch=stamp+1,provider_trade_epoch=stamp+1,trade_price=10100,route_sequence=2))
    assert R._ANCHORS[key][3]==10000


def test_anchor_index_incremental_restore_preserves_first_fact_and_partial_line(tmp_path,monkeypatch):
    import json
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import reversal_anchor_index as I
    from src.engine.scalping import continuous_reversal_source as source
    day='2026-10-13';path=tmp_path/'raw.jsonl'
    def raw(i,p=10000):
        return dict(schema='scalp_micro_reversion_market_stream_point_v3',symbol='123456',venue='SOR',
            session_bucket='KRX_REGULAR',source_item='123456_AL',trade_price=p,
            local_receive_timestamp=K.iso(T+i),exchange_timestamp=K.iso(T+i),
            sequence_epoch=99,series_sequence=i+1,native_transport_epoch=7,native_route_sequence=i+1,
            path_consumer_eligible=True,path_order_status='accept')
    line=json.dumps(raw(0))+'\n';path.write_text(line+json.dumps(raw(1))[:30])
    monkeypatch.setattr(source,'discover',lambda *a:[dict(files=[dict(path=str(path))])])
    for field,value in [('_RESTORED_DAYS',set()),('_EMPTY_PREFIX_DAYS',set()),('_ANCHORS',{}),
                        ('_ANCHOR_CURSORS',{}),('_ANCHOR_ROOTS',{}),('_STATES',{})]:monkeypatch.setattr(R,field,value)
    assert R.restore_session_anchors(tmp_path,day)['status']=='prefix_incomplete'
    key=('123456','SOR','123456_AL','REGULAR',day)
    assert R._ANCHORS[key]==[T,7,1,10000]
    path.write_text(line+json.dumps(raw(1,10500))+'\n')
    assert R.restore_session_anchors(tmp_path,day)['status']=='restored'
    monkeypatch.setattr(R,'_RESTORED_DAYS',set());monkeypatch.setattr(R,'_ANCHORS',{})
    assert R.restore_session_anchors(tmp_path,day)['bytes_read']==0
    assert R._ANCHORS[key][3]==10000
    body=I.load(tmp_path,day);assert body[0][key][1]==7
    saved=I.location(tmp_path,day);corrupt=json.loads(saved.read_text());corrupt['anchors'][0]['row'][3]=99999
    saved.write_text(json.dumps(corrupt))
    with pytest.raises(ValueError,match='contract_invalid'):I.load(tmp_path,day)


def test_incomplete_restore_resumes_on_existing_preparation_cadence(tmp_path,monkeypatch):
    import json
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import reversal_anchor_index as I
    from src.engine.scalping import continuous_reversal_source as source
    p=tmp_path/'raw.jsonl';day='2026-10-13'
    rows=[dict(schema='scalp_micro_reversion_market_stream_point_v3',symbol=f'{i:06d}',venue='SOR',
        session_bucket='KRX_REGULAR',source_item=f'{i:06d}_AL',trade_price=10000,
        local_receive_timestamp=K.iso(T+i),exchange_timestamp=K.iso(T+i),sequence_epoch=1,series_sequence=i+1,
        path_consumer_eligible=True,path_order_status='accept') for i in range(10)]
    p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    monkeypatch.setattr(source,'discover',lambda *a:[dict(files=[dict(path=str(p))])])
    monkeypatch.setattr(I,'LIMIT',2048)
    for field,value in [('_RESTORED_DAYS',set()),('_EMPTY_PREFIX_DAYS',set()),('_ANCHORS',{}),
                        ('_ANCHOR_CURSORS',{}),('_ANCHOR_ROOTS',{}),('_STATES',{}),('_FAMILY',{})]:monkeypatch.setattr(R,field,value)
    assert R.restore_session_anchors(tmp_path,day,max_bytes=500)['status']=='prefix_incomplete'
    monkeypatch.setattr(I,'LIMIT',16*1024*1024)
    assert R.prepare_anchor_source_step(tmp_path,day)['status']=='restored'
    assert len(R._ANCHORS)==10


def test_union_state_receives_late_restored_anchor_without_replaying_old_confirmations(monkeypatch):
    from src.engine.scalping import reversal_extended_runtime as E
    from src.engine.scalping import reversal_path_runtime as R
    from pathlib import Path
    import json
    f=json.loads((Path(__file__).resolve().parents[2]/'data/runtime/mechanistic_entry_policy/generations'/(J.PARENT+'.json')).read_text())['continuous_reversal']
    monkeypatch.setattr(E,'_FAMILY',f);monkeypatch.setattr(E,'_STATES',{});monkeypatch.setattr(E,'observe_native',lambda *a:None)
    monkeypatch.setattr(R,'_ANCHORS',{})
    def envelope(seq,price):return dict(observed_epoch=T+seq,provider_trade_epoch=T+seq,trade_price=price,
        transport_epoch=1,route_sequence=seq,inline_best_bid=price,inline_best_ask=price+1,trade_qty=10,
        aggressor_side='BUY',item='123456_AL',market_route='krx_nxt_integrated')
    E.observe_normalized('123456','KRX_REGULAR',envelope(1,10000))
    stream=('123456','SOR','123456_AL','REGULAR','2026-10-13')
    state=E._STATES[stream+('other_non_fixed|REGULAR|LT_20000',)]
    assert state.session_anchor is None
    R._ANCHORS[stream]=[T-1,1,1,9990]
    E.observe_normalized('123456','KRX_REGULAR',envelope(2,10010))
    assert state.session_anchor[3]==9990 and state.features(state.legacy.last)['session'] is not None


def test_identifiable_lost_first_fact_is_not_replaced_by_a_later_price(tmp_path,monkeypatch):
    import json
    from src.engine.scalping import reversal_path_runtime as R
    from src.engine.scalping import continuous_reversal_source as source
    from src.engine.scalping import reversal_anchor_index as I
    p=tmp_path/'raw.jsonl';day='2026-10-13'
    first=dict(schema='scalp_micro_reversion_market_stream_point_v3',symbol='123456',venue='SOR',
        session_bucket='KRX_REGULAR',source_item='123456_AL',trade_price=None,
        local_receive_timestamp=K.iso(T),exchange_timestamp=K.iso(T),sequence_epoch=1,series_sequence=1,
        path_consumer_eligible=True,path_order_status='accept')
    later=dict(first,trade_price=10100,local_receive_timestamp=K.iso(T+1),exchange_timestamp=K.iso(T+1),series_sequence=2)
    p.write_text(json.dumps(first)+'\n'+json.dumps(later)+'\n')
    monkeypatch.setattr(source,'discover',lambda *a:[dict(files=[dict(path=str(p))])])
    for field,value in [('_RESTORED_DAYS',set()),('_EMPTY_PREFIX_DAYS',set()),('_ANCHORS',{}),
                        ('_ANCHOR_CURSORS',{}),('_ANCHOR_ROOTS',{}),('_STATES',{}),('_ANCHOR_GAPS',set())]:monkeypatch.setattr(R,field,value)
    assert R.restore_session_anchors(tmp_path,day)['status']=='restored'
    key=('123456','SOR','123456_AL','REGULAR',day)
    assert key in R._ANCHOR_GAPS and key not in R._ANCHORS
    assert key in I.load(tmp_path,day)[2]


@pytest.mark.parametrize('receipt,expected',[
    ({'native_source_current':False},'source_unavailable'),
    ({'selected_pending_count':1},'observation_incomplete'),
    ({'selected_branch_truth':{'a':'FALSE'}},'observation_incomplete'),
    ({'selected_branch_truth':{'a':'FALSE'},'selected_lifecycle_counts':{'a':{'FALSE':10}}},'pattern_not_matched'),
    ({'selected_branch_truth':{'a':'FALSE'},'selected_lifecycle_counts':{'a':{'TRUE':1,'FALSE':10}}},'observation_incomplete'),
    ({'selected_branch_truth':{'a':'FALSE'},'source_censored_count':1},'source_unavailable'),
])
def test_native_terminal_distinguishes_lifecycle_from_last_false(receipt,expected):
    from src.engine.scalping.zero_base_probe import native_wait_result
    assert native_wait_result(receipt,{})[0]==expected


@pytest.mark.parametrize('gap',['epoch','sequence','clock'])
def test_fresh_disconnected_print_cannot_become_complete_no_match(gap):
    from src.engine.scalping.zero_base_probe import native_wait_result
    bid='legacy_dd5_ge_0_4_v1'
    state=S.State(branch_ids=[bid],offline=True,session_anchor=row(0))
    feed(state,[row(0),row(1)])
    assert state.coverage_source_censored==0
    following=[row(2),row(3)]
    if gap=='epoch':
        for value in following:value[1]=2
    elif gap=='sequence':
        for value in following:value[2]+=1
    else:
        for value in following:value[0]-=2
    feed(state,following)
    assert state.coverage_source_censored==1
    receipt=dict(native_source_current=True,selected_branch_truth=dict(state.coverage_snapshot),
        selected_lifecycle_counts=state.coverage_counts,source_censored_count=state.coverage_source_censored)
    assert native_wait_result(receipt,{})[0]=='source_unavailable'


def test_partial_source_wait_uses_original_residence_and_event_wakeup(monkeypatch):
    from src.engine.scalping import zero_base_probe as Z
    from src.engine.scalping import reversal_source_diagnostics as D
    clock=[100.];waits=[]
    monkeypatch.setattr(Z.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(Z.time,'sleep',lambda sec:clock.__setitem__(0,clock[0]+sec))
    monkeypatch.setattr(D,'observation_sequence',lambda item:0)
    def wait(item,seq,sec):waits.append(sec);clock[0]+=sec
    monkeypatch.setattr(D,'wait_observation',wait)
    monkeypatch.setattr(Z,'probe_ws_snapshot',lambda *a,**kw:{'market_data_transport_epoch':3})
    monkeypatch.setattr(Z,'exact_probe_ws_data',lambda *a,**kw:({'curr':10000},'ready'))
    monkeypatch.setattr(Z,'probe_ws_observation',lambda *a,**kw:dict(exact_0b_count=5 if clock[0]>=121 else 3,
        exact_0d_count=6,latest_0b_ms=1,latest_0d_ms=1,first_0b_ms=0))
    data,obs,_=Z.wait_for_exact_probe_ws_data(SimpleNamespace(_market_data_transport_epoch=3),
        code='123456',route='krx_nxt_integrated',after_epoch=100,now=lambda:clock[0],
        timeout_sec=15,empty_timeout_sec=10,min_exact_0b_count=5,
        residence_deadline_epoch=250,required_window_sec=120)
    assert data and obs['residence_wait_applied'] and 21<=clock[0]-100<23
    assert waits and max(waits)<=1 and obs['effective_wait_budget_ms']==150000


def test_approved_selector_uses_own_whole_opportunity_denominator_and_carries_incomplete():
    from src.engine.scalping import reversal_joint_registration as R
    sid='036930|AFTER|GE_100000|SOR'
    old=['legacy_dd5_ge_0_4_v1','manual_extended_27bebc59a6315682']
    groups=R.variant_groups({'continuous_reversal':{'operating_manifest':{'scopes':{
        sid:old,'other_non_fixed|PRE|LT_20000|NXT':['legacy_dd5_0_8_vol_up_v1','manual_extended_f74502b35a4fae1f',
            'manual_residual_29b499784843baed','manual_residual_bac0e83e966ed3ea']}}}})
    current=groups[sid]['alternatives']['JOINT_BALANCED']
    def metric(w,f):return dict(counts={'WIN':w,'FAIL_STOP':f},source_complete=True,
        comparison_complete=True,source_universe_sha256='a'*64)
    metrics={'CURRENT_NATIVE':metric(7,3),'PREVIOUS_BASELINE':metric(6,4),
        'ADD_A_ONLY':metric(80,20),'REPLACE_F_ONLY':metric(8,2)}
    result=R.select_variant(groups,sid,current,metrics,authority=R.SELECTION_AUTHORITY)
    assert result['variant']=='ADD_A_ONLY' and result['branch_ids']==groups[sid]['alternatives']['ADD_A_ONLY']
    metrics['CURRENT_NATIVE']['source_complete']=False
    assert R.select_variant(groups,sid,current,metrics,authority=R.SELECTION_AUTHORITY)['branch_ids']==current


def test_registration_exact_delta_native_publisher_and_dated_handoff(tmp_path,monkeypatch):
    import json
    from pathlib import Path
    from src.engine.scalping import reversal_joint_registration as R
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.engine.scalping import continuous_reversal_policy as dispatch
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_auxiliary_registry as G
    from src.engine.scalping import reversal_auxiliary_intraday as I
    repo=Path(__file__).resolve().parents[2];original_root=N.root(repo/'data')
    parent=json.loads((original_root/'generations'/(J.PARENT+'.json')).read_text())
    evidence=repo/'tmp/main-machine-joint-research-20261013/operating-application-plan-evidence.json'
    frozen=tmp_path/'evidence.json';frozen.write_bytes(evidence.read_bytes())
    result_source=tmp_path/'frontier.json';result_source.write_bytes((evidence.parent/'opportunity-frontier-result.json').read_bytes())
    request=P.seal(dict(schema=R.SCHEMA,kind='REPLACE',operator_receipt=R.AUTHORITY,
        parent_bundle_sha256=J.PARENT,research_batch_sha256=J.RESEARCH_RESULT,
        registry_sha256=C.JOINT_SHA256,scopes=J.changes(),
        definition_hashes={b:P.digest(d) for b,d in J.DEFINITIONS.items()},
        variant_groups=R.variant_groups(parent),selection_authority=R.SELECTION_AUTHORITY,
        comparison_result_required=False,source_receipts=[dict(path=str(p),sha256=P.file_hash(p)) for p in (frozen,result_source)],
        publication_date='2026-10-13',target_date='2026-10-14'))
    R.validate_request(request)
    manifest=V.detector_manifest(parent,effective_date='2026-10-14',changes=request)
    before=parent['continuous_reversal']['operating_manifest']['scopes']
    assert {s for s in before if before[s]!=manifest['scopes'][s]}==set(J.changes())
    assert [len(manifest['scopes'][s]) for s in J.changes()]==[3,5]
    # Real registry/projection writes use the fixture root only. Provider/store
    # comparison is forbidden by this initial registration contract.
    bindings={}
    for key,route in V.scopes():
        arm=parent['continuous_reversal']['auxiliary_cells'][key]['routes'][route]['payload']['arm']
        bindings[V.scope_id(key,route)]=G.register(tmp_path,G.definition(arm,input_version=V.A.VERSION))
    monkeypatch.setattr(I,'effective_bindings',lambda *a,**kw:bindings)
    monkeypatch.setattr(I,'current',lambda *a,**kw:None)
    monkeypatch.setattr(I,'lineage_sources',lambda *a:[])
    code={Path(m.__file__).name:P.file_hash(m.__file__) for m in V.contract_modules()}
    machine=P.seal(dict(schema='fixture',source_date='2026-10-13',target_date='2026-10-13',publication_date='2026-10-13',
        parent_bundle_sha256=J.PARENT,registration_change=request,operating_manifest=manifest,
        execution_code_sha256=P.digest(code),source_receipts=[],source_manifest_sha256=parent['continuous_reversal']['source_manifest_sha256']))
    out=tmp_path/'typed';aux=R.initial_reports(tmp_path,'2026-10-13','2026-10-13',parent,machine,output_directory=out,publish_policy=False)
    issued=json.loads((out/'machine.json').read_text())
    assert aux['actual_provider_calls']==0 and aux['comparison_complete'] is False
    assert aux['scope_census']['new_ready']==128 and not aux['scope_pending']
    root=N.root(tmp_path);root.mkdir(parents=True,exist_ok=True)
    native=parent['continuous_reversal']['native_parent_bundle']
    for name in ('machine','auxiliary'):
        filename='reversal-'+native['continuous_reversal'][name+'_report_sha256']+'.json'
        dest=root/'sources'/filename;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((original_root/'sources'/filename).read_bytes())
    monkeypatch.setattr(N,'load_effective',lambda **kw:parent)
    # Old immutable source validation belongs to intake's attested origin.
    # This test exercises new native serialization, family validation and reader.
    monkeypatch.setattr(N,'_validate_bundle_sources',lambda b,r:V.validate_family(b['continuous_reversal'])
        if b['continuous_reversal']['schema']==V.SCHEMA else V.V4.validate_family(b['continuous_reversal']))
    bundle=V.stage(tmp_path,'2026-10-13','2026-10-13',issued,aux,target_date='2026-10-14',release_commit='a'*40)
    V.validate_family(bundle['continuous_reversal']);N.validate(bundle,target_date='2026-10-14')
    assert bundle['continuous_reversal']['contract_file_sha256']==code
    assert bundle['continuous_reversal']['native_parent_bundle']['bundle_sha256']!=native['bundle_sha256']
    assert parent['bundle_sha256']==J.PARENT  # Frozen predecessor not relabelled.
    monkeypatch.setattr(N,'load',lambda **kw:bundle)
    handoff=dispatch.direct_handoff(tmp_path,'2026-10-13')
    assert handoff['scope_census']['new_ready']==128 and not handoff['current_pid_consumption_claimed']
    bad=copy.deepcopy(bundle['continuous_reversal']);sid=next(iter(J.changes()))
    bad['operating_manifest']['scopes'][sid]=[J.ALIASES['jusung_after_breakout']]
    bad['family_sha256']=P.digest({k:v for k,v in bad.items() if k!='family_sha256'})
    with pytest.raises(ValueError):V.validate_family(bad)

    # Tomorrow's actual activation must dispatch the joint receipt validator,
    # even when today's unchanged parent still has the previous code hashes.
    from src.engine.infrastructure import runtime_release_router as router
    request['activation_parent_origin']=dict(root=str(tmp_path/'old'),commit='b'*40)
    request=P.seal(request)
    bf=copy.deepcopy(bundle['continuous_reversal'])
    bf['registration_code_transition']=request
    bf['operating_manifest']['change_receipt']=request
    bf['family_sha256']=P.digest({k:v for k,v in bf.items() if k!='family_sha256'})
    activated=copy.deepcopy(bundle);activated['continuous_reversal']=bf
    activated['bundle_sha256']=N.digest({k:v for k,v in activated.items() if k!='bundle_sha256'})
    N._atomic_write_json(root/'candidates/policy_2026-10-14.json',activated)
    monkeypatch.setattr(N,'validate',lambda *a,**kw:None)
    monkeypatch.setattr(V,'validate_sources',lambda *a,**kw:None)
    calls=[]
    def current(**kwargs):
        calls.append(True)
        if len(calls)==1:raise ValueError('v4_contract_code_changed:reversal_path_runtime.py')
        return activated
    monkeypatch.setattr(N,'load_effective',current)
    monkeypatch.setattr(V,'_attested_activation_parent',lambda *a,**kw:parent)
    monkeypatch.setattr(router,'selected_release',lambda *a:(tmp_path/'new','a'*40))
    receipt=V.activate(tmp_path,'2026-10-14',now=datetime(2026,10,14,7,35,tzinfo=K.KST))
    assert receipt['status']=='activated' and receipt['previous_bundle_sha256']==J.PARENT


@pytest.mark.parametrize('damage',[None,'code','source','pointer','date','authority','members','seal','selector','absent'])
def test_active_code_handoff_is_exact_and_never_reselects_policy(tmp_path,monkeypatch,damage):
    from pathlib import Path
    from src.engine.scalping import reversal_code_handoff as H, continuous_reversal_policy_v6 as V
    from src.engine.scalping import mechanistic_entry_runtime_policy as N,continuous_reversal_postclose as P
    from src.engine.infrastructure import runtime_release_router as router
    root=tmp_path/'release';data=tmp_path/'data';day=datetime.now(P.KST).date().isoformat();commit='b'*40
    code=root/'src/engine/scalping/reversal_code_handoff.py';code.parent.mkdir(parents=True);code.write_text('reviewed code')
    old=data/'source.json';old.parent.mkdir();old.write_text('frozen source')
    pointer=N.root(data)/'current.json';pointer.parent.mkdir(parents=True);pointer.write_text('{"bundle_sha256":"bundle"}')
    selector=data/'runtime/runtime_release_selection.json';selector.write_text(__import__('json').dumps(dict(git_commit=commit,release_root=str(root))))
    monkeypatch.setattr(H,'__file__',str(code));monkeypatch.setattr(V,'contract_modules',lambda:[SimpleNamespace(__file__=str(code))])
    monkeypatch.setattr(router,'selected_release',lambda *a:(root,commit))
    receipt=P.seal(dict(schema=H.SCHEMA,authority=H.AUTHORITY,target_date=day,release_root=str(root),
        release_commit=commit,bundle_sha256='bundle',current_pointer_sha256=P.file_hash(pointer),
        code_hashes={str(code):P.file_hash(code)},source_hashes={str(old):P.file_hash(old)},policy_reselected=False,provider_called=False))
    if damage=='date':receipt['target_date']='2026-10-01'
    if damage=='authority':receipt['authority']='unapproved'
    if damage=='members':receipt['code_hashes']={str(old):P.file_hash(old)}
    receipt=P.seal(receipt)
    if damage=='seal':receipt['policy_reselected']=True
    dest=H.path(data,day,commit,'bundle');N._atomic_write_json(dest,receipt)
    if damage=='code':code.write_text('unreviewed code')
    if damage=='source':old.write_text('changed source')
    if damage=='pointer':pointer.write_text('{"bundle_sha256":"other"}')
    if damage=='selector':selector.write_text('{}')
    if damage=='absent':dest.unlink()
    frozen={p:p.read_bytes() for p in (code,old,pointer,selector)};bundle={'bundle_sha256':'bundle'}
    if damage:
        with pytest.raises(ValueError):H.validate(bundle,data,original_error=ValueError('v4_contract_code_changed:test'))
    else:assert H.validate(bundle,data,original_error=ValueError('v4_contract_code_changed:test')) is bundle
    assert frozen=={p:p.read_bytes() for p in frozen}


@pytest.mark.parametrize('anchor,expected',[(10200,'TRUE'),(9900,'FALSE'),(None,'UNKNOWN')])
def test_general_pre_refinement_applies_only_at_original_volume_confirmation(anchor,expected):
    base='legacy_dd5_0_8_vol_up_v1';bid=J.ALIASES['general_pre_refined']
    values=[row(i,10200,1) for i in range(121)]+[row(121,10100,20000),row(122,10110)]
    if anchor is not None:values[0][3:6]=[anchor,anchor,anchor+1]
    for r in values:r[9]='123456_NX'
    initial=values[0] if anchor is not None else None
    original=S.State(branch_ids=[base],session_anchor=initial,offline=True)
    candidate=S.State(branch_ids=[bid],session_anchor=initial,offline=True)
    def run(state):
        hits=[]
        for r in values:hits+=state.observe(r,symbol='123456',venue='NXT',session='NXT_PREMARKET')
        return hits
    old=run(original);new=run(candidate);assert old
    if expected=='FALSE':assert not new
    else:
        assert new
        e=new[-1]['event']['branch_signals'][bid];A.validate_signal(e)
        assert e['signal_proof']['refinement_truth']==expected
        assert e['epoch']==old[-1]['event']['epoch'] and e['entry_ask']==old[-1]['event']['entry_ask']


@pytest.mark.parametrize('case',['empty','cannot_fit','generation'])
def test_source_wait_never_resets_original_deadline_or_waits_through_generation(case,monkeypatch):
    from src.engine.scalping import zero_base_probe as Z
    from src.engine.scalping import reversal_source_diagnostics as D
    clock=[100.]
    monkeypatch.setattr(Z.time,'monotonic',lambda:clock[0])
    monkeypatch.setattr(Z.time,'sleep',lambda sec:clock.__setitem__(0,clock[0]+sec))
    monkeypatch.setattr(D,'observation_sequence',lambda item:0)
    monkeypatch.setattr(D,'wait_observation',lambda item,seq,sec:clock.__setitem__(0,clock[0]+sec))
    monkeypatch.setattr(Z,'probe_ws_snapshot',lambda *a,**kw:{'market_data_transport_epoch':3})
    monkeypatch.setattr(Z,'exact_probe_ws_data',lambda *a,**kw:({},'0B_missing'))
    monkeypatch.setattr(Z,'probe_ws_observation',lambda *a,**kw:dict(exact_0b_count=0 if case=='empty' else 3,
        exact_0d_count=0 if case=='empty' else 6,latest_0b_ms=None if case=='empty' else 1,
        latest_0d_ms=None if case=='empty' else 1,first_0b_ms=None if case=='empty' else 0))
    _,obs,reason=Z.wait_for_exact_probe_ws_data(SimpleNamespace(_market_data_transport_epoch=3),
        code='123456',route='krx_nxt_integrated',after_epoch=100,now=lambda:clock[0],
        timeout_sec=15,empty_timeout_sec=10,min_exact_0b_count=5,
        residence_deadline_epoch=120 if case=='cannot_fit' else 250,required_window_sec=120,
        readiness_guard=lambda:'consumer_readiness_generation_changed' if case=='generation' and clock[0]>=117 else '')
    assert clock[0]<=(118 if case=='generation' else 110.01 if case=='empty' else 115.01)
    assert obs['residence_wait_applied'] is (case=='generation')
    if case=='generation':assert reason=='consumer_readiness_generation_changed'
