"""Successor membership, independent detection, native carry and durable replay."""
import copy
import gzip
import json
from pathlib import Path
import pytest
from src.engine.scalping import continuous_reversal_policy_v5 as V
from src.engine.scalping import continuous_reversal_policy_v4 as OLD
from src.engine.scalping import continuous_reversal_operating_postclose as PC
from src.engine.scalping import reversal_operating_auxiliary as A
from src.engine.scalping import reversal_operating_evaluation as E
from src.engine.scalping import reversal_operating_runtime as R
from src.engine.scalping import reversal_operating_outbox as O
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.ai import offline_comparison_store as S
from src.tests.test_reversal_path_policy import C,row,T
from src.tests.test_continuous_reversal_policy_v3 import native,migrated_reports
from src.tests.test_offline_comparison_store import activate


@pytest.fixture
def parent(native,monkeypatch):
    root,_,_,_=native
    m,a=migrated_reports(native)
    bundle=OLD.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-08',release_commit='a'*40)
    monkeypatch.setattr(OLD,'transition_parent',lambda *a:bundle)
    with S.Store(root) as store:activate(store)
    return root,bundle


@pytest.fixture
def replay(parent,monkeypatch):
    root,bundle=parent
    # This fixture exercises ownership/comparison, not threshold economics.
    monkeypatch.setattr(C,'matches',lambda *a:True)
    values=[row(i) for i in range(62)]+[row(62,100.3),row(63,100),row(64,100.3)]
    raw=root/'native.gz';raw.write_bytes(gzip.compress(json.dumps(dict(symbols={'005930':values})).encode()))
    rec=dict(path=str(raw),sha256=P.file_hash(raw),day='2026-10-07',session='SOR_REGULAR',venue='SOR')
    source=P.seal(dict(normalized_sources=dict(partitions=[rec])))
    monkeypatch.setattr(PC.K,'label',lambda *a,**kw:dict(status='WIN'))
    machine=PC.machine_report(root,'2026-10-07','2026-10-07',bundle,source=source)
    return root,bundle,machine


def transport(req,timeout_sec):
    inp=req['candidate_input']
    if inp['schema']==A.VERSION:
        response=dict(schema=A.VERSION,decision_scope='COMMON_OPPORTUNITY',
            assessed_signal_refs=[s['ref'] for s in inp['signals']],risk_verdict='PASS',
            risk_codes=['NO_BLOCKING_RISK'],supporting_fact_ids=['observed_machine_signal'],
            contradicting_fact_ids=[],confidence=60)
    else:
        phase=inp.get('observation_phase',{}).get('stage','FIRST_UPTICK')
        ids=['first_price_uptick','observed_price_decline']
        if phase=='CONFIRMED_UPTICK':ids.append('additional_higher_trade')
        response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],
            supporting_fact_ids=ids,contradicting_fact_ids=[],confidence=60)
    return dict(provider_provenance=dict(response_id='fixture-'+req['paired_replay_id']),candidate_response=response)


def test_initial_manifest_is_incumbent_plus_exact_eight(parent):
    _,b=parent;m=V.detector_manifest(b,effective_date='2026-10-08')
    assert len(m['scopes'])==128
    for alias,bid in C.ALIASES.items():
        exact=[sid for sid,ids in m['scopes'].items() if bid in ids]
        assert exact and all('|REGULAR|' in s and s.endswith('|SOR') for s in exact)
    changed=V.detector_manifest(b,effective_date='2026-10-12')
    assert changed['detector_manifest_hash']==m['detector_manifest_hash']


def test_dispatch_configuration_accepts_existing_runtime_call_signature(monkeypatch,tmp_path):
    from src.engine.scalping import reversal_operating_backend as D
    seen=[]
    monkeypatch.setattr(D,'_ACTIVE',D.OLD)
    monkeypatch.setattr(D.OLD,'configure_bundle',lambda b,data_root,day:seen.append((b,data_root,day)))
    D.configure_bundle({},data_root=tmp_path,day='2026-10-08')
    assert seen==[({},tmp_path,'2026-10-08')]
    # Both production callers must bind successfully; their defensive catch
    # must not silently turn a signature mismatch into an idle detector.
    import ast
    import inspect
    root=Path(__file__).resolve().parents[1]
    for relative in ('engine/ai_engine_openai.py','engine/sniper_state_handlers.py'):
        calls=[n for n in ast.walk(ast.parse((root/relative).read_text()))
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='configure_bundle']
        assert calls
        for call in calls:
            inspect.signature(D.configure_bundle).bind(*[None for _ in call.args],
                **{k.arg:None for k in call.keywords})


@pytest.mark.parametrize('damage',['none','quantity','side','gap','epoch'])
def test_final_feature_projection_is_exact_native_prefix(damage):
    import math
    values=[row(i,100+math.sin(i/11)) for i in range(420)]
    if damage=='quantity':values[411][6]=None
    if damage=='side':values[411][7]=0
    if damage=='gap':values[400][8]=0
    if damage=='epoch':
        for r in values[400:]:r[1]+=1
    for n in (1,9,10,31,61,121,420):
        prefix=values[max(0,n-305):n]
        arrays=PC.K.build_features(prefix,earliest_segment_epoch=values[0][0])
        expected={k:float(v[-1]) if math.isfinite(v[-1]) else None for k,v in arrays.items()}
        assert R._latest_features(prefix,values[0][0])==expected


def test_shared_operating_snapshot_matches_native_bytes(parent):
    import math
    from src.engine.scalping import reversal_path_runtime as native_runtime
    _,bundle=parent
    ids=V.wanted(bundle)['samsung|REGULAR|ALL|SOR']
    values=[row(i,100+math.sin(i/8)) for i in range(650)]
    state=native_runtime.State(branch_ids=ids,session_anchor=values[0],offline=True)
    compared=0
    for r in values:
        for ready in state.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR'):
            expected=state.snapshot(ready)
            actual=R.snapshot(state,ready)
            assert S.encode(actual)==S.encode(expected)
            compared+=1
        state.ready.clear()
    assert compared>10


def test_contribution_unknown_and_zero_percent_tie():
    points=[dict(opportunity_key='1',outcome='WIN',truth={'a':'TRUE','b':'UNKNOWN'}),
            dict(opportunity_key='2',outcome='FAIL_TIMEOUT',truth={'a':'FALSE','b':'TRUE'})]
    result=E.summarize(points,['a','b'],['a'])
    assert result['exclusive']['a']['resolved']==0
    assert result['exclusive_unproven']['a']['wins']==1
    assert result['excluded_baseline']['wins']==1
    assert result['common_baseline']['win_rate'] is None
    assert E.recommendation(dict(wins=0,resolved=1),dict(wins=0,resolved=2))=='keep_current'
    assert E.recommendation(dict(wins=8,resolved=10),dict(wins=16,resolved=20))=='equal_fraction_additional_resolved_success'


def test_shared_store_complete_carry_and_loader(replay):
    root,b,m=replay
    census=PC.prepare_inputs(root,'2026-10-07',m,b)
    assert census['census']['expected_owner_requests']>0
    calls=PC.calls(root,'2026-10-07',transport=transport)
    assert calls['new_calls']>0
    assert PC.calls(root,'2026-10-07',transport=transport)['new_calls']==0
    aux=PC.auxiliary_report(root,'2026-10-07','2026-10-07',b,publish_policy=False)
    assert aux['scope_census']['new_ready']>=1
    assert aux['scope_census']['native_carried']>0
    issued=json.loads((PC.directory(root,'2026-10-07')/'machine.json').read_text())
    bundle=V.stage(root,'2026-10-07','2026-10-07',issued,aux,target_date='2026-10-08',release_commit='a'*40)
    V.validate_sources(bundle,root)
    from src.engine.scalping import mechanistic_entry_runtime_policy as N
    N.validate(bundle,target_date='2026-10-08')
    f=bundle['continuous_reversal'];key='samsung|REGULAR|ALL'
    assert f['machine_cells'][key]['routes']['SOR']['backend']=='union_v5'
    assert f['machine_cells'][key]['routes']['KRX']['backend']=='registered_v4'
    # Mutable comparison state cannot invalidate the frozen publication.
    P.write(PC.directory(root,'2026-10-07')/'shared-ledger/input-census.json',dict(changed=True))
    V.validate_sources(bundle,root)


def test_incomplete_comparison_preserves_exact_native_pair(replay):
    root,b,m=replay;PC.prepare_inputs(root,'2026-10-07',m,b)
    aux=PC.auxiliary_report(root,'2026-10-07','2026-10-07',b,publish_policy=False)
    assert aux['scope_census']['new_ready']==0 and aux['scope_census']['native_carried']==128
    issued=json.loads((PC.directory(root,'2026-10-07')/'machine.json').read_text())
    for cell in issued['cells']:
        for route,value in cell['routes'].items():
            assert value['payload']==b['continuous_reversal']['machine_cells'][cell['key']]['routes'][route]['payload']


def test_invalid_one_arm_cannot_rank_other_arms(replay):
    root,b,m=replay;PC.prepare_inputs(root,'2026-10-07',m,b)
    def invalid(req,timeout_sec):
        r=transport(req,timeout_sec)
        if req['micro_reversion_replay_arm']==PC.V1.ARMS[0]:r['candidate_response']={}
        return r
    PC.calls(root,'2026-10-07',transport=invalid)
    aux=PC.auxiliary_report(root,'2026-10-07','2026-10-07',b,publish_policy=False)
    assert aux['scope_census']['new_ready']==0
    assert all(status in {'incomplete','source_gap','valid_empty'} for status in aux['comparison_statuses'].values())


def test_repeated_prepare_has_no_new_requests(replay):
    root,b,m=replay;first=PC.prepare_inputs(root,'2026-10-07',m,b)
    with S.Store(root) as store:count=store.db.execute('SELECT count(*) FROM requests').fetchone()[0]
    second=PC.prepare_inputs(root,'2026-10-07',m,b)
    assert first==second
    with S.Store(root) as store:assert store.db.execute('SELECT count(*) FROM requests').fetchone()[0]==count


def test_union_schema_exact_coverage_and_no_future_fields(replay):
    root,b,m=replay
    with S.Store(root) as store:
        points=store.get(m['partitions'][0]['records_object'])
        snap=store.get(points[0]['snapshot_obj'])
    snap[0]['future_label']='WIN'
    req=PC.request(snap,PC.V1.ARMS[-1]);inp=req['candidate_input']
    assert 'future_label' not in json.dumps(inp) and req['candidate']['system_prompt'].isascii()
    good=transport(req,30)['candidate_response']
    assert not A.validate_response(good,inp,arm=PC.V1.ARMS[-1])
    good['assessed_signal_refs']=[]
    assert A.validate_response(good,inp,arm=PC.V1.ARMS[-1])
    changed=copy.deepcopy(snap);first=next(iter(changed[0]['branch_signals'].values()));first['entry_ask']+=1
    with pytest.raises(ValueError,match='same_tick_source_conflict'):PC.request(changed,PC.V1.ARMS[-1])


def test_outbox_uncertainty_blocks_restart_and_new_generation(tmp_path):
    a=dict(opportunity_key='a'*64,scope_execution_hash='b'*64,signal_set_hash='c'*64,
           matched_policy_refs=['x'],signal_id='source:1')
    O.reserve(tmp_path,a,'request1')
    a['scope_execution_hash']='d'*64
    with pytest.raises(ValueError,match='already_reserved'):O.reserve(tmp_path,a,'request2')
    O.advance(tmp_path,a['opportunity_key'],'response_received',binding=dict(response_id='actual'))
    O.advance(tmp_path,a['opportunity_key'],'intent_assigned')
    O.advance(tmp_path,a['opportunity_key'],'submission_reconciliation')
    with pytest.raises(ValueError):O.advance(tmp_path,a['opportunity_key'],'reserved')


def configured_family(replay):
    root,b,m=replay
    PC.prepare_inputs(root,'2026-10-07',m,b)
    aux=PC.auxiliary_report(root,'2026-10-07','2026-10-07',b,publish_policy=False)
    issued=json.loads((PC.directory(root,'2026-10-07')/'machine.json').read_text())
    bundle=V.stage(root,'2026-10-07','2026-10-07',issued,aux,target_date='2026-10-08',release_commit='a'*40)
    f=copy.deepcopy(bundle['continuous_reversal']);key='403870|REGULAR|LT_20000';route='SOR'
    ids=f['operating_manifest']['scopes'][V.scope_id(key,route)]
    payload=PC.B.payload([C.branch(b) for b in ids]);ap=dict(arm=PC.V1.ARMS[-1],binding=A.binding(PC.V1.ARMS[-1]))
    f['machine_cells'][key]['routes'][route]=dict(payload=payload,payload_sha256=P.digest(payload),backend='union_v5',
        scope_execution_hash=V.scope_hash(ids,ap,'union_v5',f['execution_code_sha256']))
    f['auxiliary_cells'][key]['routes'][route]=dict(payload=ap,payload_sha256=P.digest(ap),actual_response_evidence=[dict(path='fixture',sha256='a'*64)])
    reseal_family(f)
    return root,f


def reseal_family(f):
    f['execution_manifest_hash']=P.digest({V.scope_id(k,r):f['machine_cells'][k]['routes'][r]['scope_execution_hash'] for k,r in V.scopes()})
    f['family_sha256']=P.digest({k:v for k,v in f.items() if k!='family_sha256'})


def envelope(i,p,symbol='403870'):
    return dict(observed_epoch=T+i,provider_trade_epoch=T+i,trade_price=p,transport_epoch=1,route_sequence=i+1,
        market_route='krx_nxt_integrated',effective_venue='SOR',inline_best_bid=p,inline_best_ask=p,
        trade_qty=10,aggressor_side='BUY',item=symbol+'_AL')


def test_first_invalidation_keeps_independent_breakout_and_common_ttl(replay,monkeypatch):
    root,f=configured_family(replay)
    monkeypatch.setattr(R.R,'restore_session_anchors',lambda *a:None)
    R._STATES.clear();R._CLAIMS.clear();R.R._STATES.clear()
    R.configure(f,root,'2026-10-07')
    for i in range(61):R.observe_normalized('403870','SOR_REGULAR',envelope(i,100))
    R.observe_normalized('403870','SOR_REGULAR',envelope(61,99))
    R.observe_normalized('403870','SOR_REGULAR',envelope(62,101))
    claim=R.claim_snapshot('403870','SOR','SOR_REGULAR',now=T+62,item='403870_AL',family_sha256=f['family_sha256'])
    assert claim and C.ALIASES['HB'] in claim['snapshot'][0]['branch_signals']
    assert C.ALIASES['HA'] in claim['snapshot'][0]['branch_signals']
    R.observe_normalized('403870','SOR_REGULAR',envelope(63,100))
    remaining=R.validate_claim(claim,f['family_sha256'],now=T+63)
    assert C.ALIASES['HB'] in remaining[0]['branch_signals'] and C.ALIASES['HA'] not in remaining[0]['branch_signals']
    with pytest.raises(ValueError,match='expired'):R.validate_claim(claim,f['family_sha256'],now=T+67.001)
    # Reporting and other-scope revisions do not reset this scope's FSM.
    keys=list(R._STATES);before={k:id(v) for k,v in R._STATES.items()}
    f['machine_report_sha256']='e'*64;reseal_family(f);R.configure(f,root,'2026-10-07')
    assert {k:id(v) for k,v in R._STATES.items()}==before
    assert R.validate_claim(claim,f['family_sha256'],now=T+63)
    k='403870|REGULAR|LT_20000';cell=f['machine_cells'][k]['routes']['SOR']
    ap=dict(arm=PC.V1.ARMS[0],binding=A.binding(PC.V1.ARMS[0]))
    f['auxiliary_cells'][k]['routes']['SOR'].update(payload=ap,payload_sha256=P.digest(ap))
    cell['scope_execution_hash']=V.scope_hash([b['branch_id'] for b in cell['payload']['branches']],ap,'union_v5',f['execution_code_sha256'])
    reseal_family(f);R.configure(f,root,'2026-10-07')
    with pytest.raises(ValueError):R.validate_claim(claim,f['family_sha256'],now=T+63)


def test_samsung_native_all_cell_and_callback_has_no_file_io(parent,monkeypatch):
    root,b=parent;R.R.configure(b['continuous_reversal']);R.R._STATES.clear()
    monkeypatch.setattr('builtins.open',lambda *a,**kw: (_ for _ in ()).throw(AssertionError('callback disk IO')))
    for i,p in enumerate([102,100,101]):R.observe_native('005930','SOR_REGULAR',envelope(i,p,'005930'))
    assert len(R.R._STATES)==1
    assert next(iter(R.R._STATES.values())).ready


def test_membership_corruption_blocks_calls_before_transport(replay):
    root,b,m=replay;PC.prepare_inputs(root,'2026-10-07',m,b)
    with S.Store(root) as store:
        mid=next(store.owners(m['artifact_content_sha256']))[-1]
        store.db.execute('DELETE FROM partition_members WHERE member_id=?',(mid,));store.commit()
    with pytest.raises(ValueError,match='membership'):
        PC.calls(root,'2026-10-07',transport=lambda *a:(_ for _ in ()).throw(AssertionError('provider called')))


def test_explicit_membership_change_requires_parent_receipt(parent):
    _,b=parent;sid='samsung|REGULAR|ALL|SOR';bid=C.ALIASES['SA']
    with pytest.raises(ValueError,match='receipt'):
        V.detector_manifest(b,effective_date='2026-10-08',changes=dict(kind='RETIRE'))
    receipt=dict(kind='RETIRE',parent_bundle_sha256=b['bundle_sha256'],operator_receipt='fixture-approval',scopes={sid:dict(remove=[bid])})
    m=V.detector_manifest(b,effective_date='2026-10-08',changes=receipt)
    assert bid not in m['scopes'][sid] and m['change_receipt']==receipt


def test_machine_stage_consumes_successor_48_cells(replay):
    root,_,m=replay
    from src.engine.automation import postclose_summary_handoff as H
    P.write(P.directory(root,'2026-10-07')/'source.json',P.seal(dict(schema=P.SCHEMA,source_date='2026-10-07')))
    assert not H._stage_output_issues(root/'report','2026-10-07','main_machine_policy')


def test_execution_code_hash_cannot_be_unbound(replay):
    _,f=configured_family(replay)
    f['execution_code_sha256']='0'*64;reseal_family(f)
    with pytest.raises(ValueError,match='family_contract'):V.validate_family(f)


def test_source_clock_loss_does_not_become_false():
    bid='legacy_all_v1';s=PC.R.State(branch_ids=[bid],offline=True,session_anchor=row(0))
    s.observe(row(0),symbol='005930',venue='SOR',session='SOR_REGULAR')
    broken=row(1);broken[1]=2
    s.observe(broken,symbol='005930',venue='SOR',session='SOR_REGULAR')
    assert E.coverage(s,broken,[bid],set(),previous=row(0))[bid]=='UNKNOWN'


def test_real_machine_capture_is_consumed_by_union_monitor(replay,monkeypatch):
    from datetime import datetime
    from src.engine.scalping import ai_decision_trace as trace
    root,f=configured_family(replay)
    monkeypatch.setattr(R.R,'restore_session_anchors',lambda *a:None)
    R._STATES.clear();R._CLAIMS.clear();R.R._STATES.clear()
    R.configure(f,root,'2026-10-07')
    for i in range(61):R.observe_normalized('403870','SOR_REGULAR',envelope(i,100))
    R.observe_normalized('403870','SOR_REGULAR',envelope(61,99))
    R.observe_normalized('403870','SOR_REGULAR',envelope(62,101))
    claim=R.claim_snapshot('403870','SOR','SOR_REGULAR',now=T+62,item='403870_AL',family_sha256=f['family_sha256'])
    assessment,inp,prompt,schema=V.assess(f,claim['snapshot'],symbol='403870',session='SOR_REGULAR')
    records=[]
    monkeypatch.setattr(trace,'trace_enabled',lambda:True)
    monkeypatch.setattr(trace,'_now',lambda:datetime.fromtimestamp(T+62.1,PC.K.KST))
    monkeypatch.setattr(trace,'_append_jsonl',lambda path,record:records.append(record))
    context=dict(family_sha256=f['family_sha256'],source_date=f['source_date'],publication_date=f['publication_date'],
        effective_date=f['effective_date'],machine_component_sha256=P.digest(f['machine_cells']),
        auxiliary_component_sha256=P.digest(f['auxiliary_cells']),snapshot_read_at=T+62,
        input_sha256=P.digest(inp),prompt_sha256=P.digest(prompt),response_schema_sha256=P.digest(schema),
        arm=assessment['auxiliary_arm'])
    result=trace.capture_machine_observation(exact_payload=dict(stock_code='403870',session_bucket='SOR_REGULAR',
        evaluation_attempt_id='fixture-actual-capture',entry_machine_input_as_of=T+62),setup_evidence=inp['entry_setup_evidence_v1'],
        assessment=assessment,bundle_sha256='b'*64,reversal_context=context,
        reversal_request=dict(input=inp,prompt=prompt,response_schema=schema))
    assert result['machine_capture_status']=='captured'
    bundle=dict(bundle_sha256='b'*64,continuous_reversal=f)
    _,receipt=V.audit_observation(bundle,records[0])
    assert receipt['new_scope_consumption'] is True
    records[0]['source']['auxiliary_request']['input']['signals'].pop()
    with pytest.raises(ValueError,match='request_hash_mismatch'):V.audit_observation(bundle,records[0])


def test_historical_envelope_validation_preserves_native_parent_commit(replay,monkeypatch):
    from src.engine.infrastructure import runtime_release_router as router
    root,b,m=replay
    PC.prepare_inputs(root,'2026-10-07',m,b)
    aux=PC.auxiliary_report(root,'2026-10-07','2026-10-07',b,publish_policy=False)
    issued=json.loads((PC.directory(root,'2026-10-07')/'machine.json').read_text())
    bundle=V.stage(root,'2026-10-07','2026-10-07',issued,aux,target_date='2026-10-08',release_commit='b'*40)
    calls=[]
    def attest(workspace,cwd,unit,commit):
        calls.append(commit)
        return dict(source_integrity='git_commit_and_clean_runtime_source')
    monkeypatch.setattr(router,'_release_identity',attest)
    # Real separate-process reader; only immutable Git origin attestation is
    # fixture supplied. The nested parent remains its original a*40 commit.
    assert V.validate_sources(bundle,root,code_root=Path(V.__file__).parents[3])==bundle
    assert calls==['b'*40]
    assert bundle['continuous_reversal']['native_parent_bundle']['continuous_reversal']['release_commit']=='a'*40
