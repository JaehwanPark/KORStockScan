"""Causal typed phases, immutable definitions and legacy contract parity."""
import copy
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
import pytest
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping import reversal_path_runtime as R
from src.engine.scalping import reversal_path_auxiliary as A
from src.engine.scalping import reversal_registered_catalog as OLD
from src.engine.scalping import reversal_registered_runtime as OR
from src.engine.scalping import continuous_reversal_policy_v4 as V4
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import reversal_auxiliary_contract as AUX
from src.tests.test_continuous_reversal_policy_v3 import native,migrated_reports

T=datetime(2026,10,7,9,0,tzinfo=R.K.KST).timestamp()
def row(i,p=100,t=None,valid=1,qty=10,side=1):
    return [T+i if t is None else T+t,1,i+1,p,p,p,qty,side,valid,'005930_AL',0]

def state(alias,monkeypatch):
    bid=C.ALIASES[alias]
    monkeypatch.setattr(C,'matches',lambda b,e,f:True)
    s=R.State(branch_ids=[bid],offline=True,session_anchor=row(0))
    return bid,s

def feed(s,r):return s.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')

def test_exact_definitions_and_finite_compatibility():
    assert len(C.NEW_DEFINITIONS)==8 and C.MANIFEST['parent_registry_sha256']==OLD.SHA256
    expected=['0c606c6f14e9a141a0b6c0eb18fab4bfc82cd530d033b8a18bf600460d7d5cb4','b7ad047d7078aa6f31f2cda12c946a0fcd0ee9502d28ab5c65e13f1392c6208d','11e6c7ac5139956ccb4c5b3c192154cb23d344e78f38a64ac33854214ecc4573','48e2f9b9a40619d0a31ae36d544196fbeb5fd382ac1fbeb7cbdd13bfb6c26dce','e9959c80f296d01824badaddd0d637be563bc7d38a73a015ea9ebd4d71fc6be5','8a44fe1b4cac82fcc092c25dcded036ac9a61aed3eed0506a0a2a68410a87961','5f0b27afa6703df97120b76c18582461a818d8183e627206196044d3e7f1274b','654d2861d52af8505d5fcc4bc17df9178c9fa0cd6795008230b8b2bd905f0c6a']
    assert [C.branch(b)['definition_sha256'] for b in C.ALIASES.values()]==expected
    for k,rs in OLD.PORTFOLIOS.items():
        for route,ps in rs.items():assert C.PORTFOLIOS[k][route][:len(ps)]==ps
    for b in C.NEW_DEFINITIONS:
        d=C.definition(b);assert C.applicable(b,f"{d['symbol_group']}|REGULAR|{d['price_band'] if d['price_band']!='ALL' else 'ALL' if d['symbol_group']=='samsung' else 'LT_20000'}",'SOR')
        assert not C.applicable(b,'samsung|PRE|ALL','SOR')
    with pytest.raises(ValueError):C.validate_payload({'composition':'ANY_MATCH_ONE_INTENT','branches':[None]},'samsung|REGULAR|ALL','SOR')

def test_momentum_unknown_does_not_trigger_then_known_cross(monkeypatch):
    bid,s=state('SA',monkeypatch)
    # First known value is true: no signal. False then true creates one.
    for i in range(60):assert not feed(s,row(i,100))
    assert not feed(s,row(60,100.2))
    assert not feed(s,row(61,100))
    ready=feed(s,row(62,100.2));assert len(ready)==1
    event,source=s.snapshot(ready[0]);signal=event['branch_signals'][bid]
    assert signal['decision_phase']=='MOMENTUM_CROSS' and 'low_price' not in signal
    A.validate_signal(signal)
    inp,prompt,schema=A.production_request(source['branch_inputs'][bid],AUX.ARMS[-1],phase=signal['decision_phase'],event=signal)
    assert 'price_reversal_confirmed' not in inp['mechanistic_entry_assessment']
    assert 'first_price_uptick' not in json.dumps(inp) and prompt.isascii()
    response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],supporting_fact_ids=['observed_machine_signal'],contradicting_fact_ids=[],confidence=60)
    assert A.validate_response(response,inp,arm=AUX.ARMS[-1],phase=signal['decision_phase'])==[]
    assert not feed(s,row(63,100.3))

def test_hold_first_tick_at_one_second_and_breach(monkeypatch):
    bid,s=state('GA',monkeypatch)
    for i in range(62):feed(s,row(i,100))
    assert not feed(s,row(62,100.1))
    assert not feed(s,row(63,100.1,t=62.9))
    ready=feed(s,row(64,100.1,t=63));assert ready[0]['event']['epoch']==T+63
    A.validate_signal(ready[0]['event']['branch_signals'][bid])
    # A fresh false/true root breached before its one-second confirmation ends.
    feed(s,row(65,100,t=63.1));feed(s,row(66,100.1,t=63.2));feed(s,row(67,100,t=63.3))
    assert not feed(s,row(68,100.1,t=64.3)) and s.counts['hold_breached']>=1

def test_breakout_excludes_current_and_requires_known_false(monkeypatch):
    bid,s=state('HB',monkeypatch)
    for i in range(61):assert not feed(s,row(i,100))
    ready=feed(s,row(61,101));assert ready
    A.validate_signal(ready[0]['event']['branch_signals'][bid])
    assert not feed(s,row(62,102)) # still true, no new edge

def test_retest_exact_120_seconds_and_breach(monkeypatch):
    bid,s=state('SB',monkeypatch)
    for r in (row(0,102),row(1,100),row(2,101),row(3,100)):feed(s,r)
    ready=feed(s,row(4,102,t=122));assert ready
    A.validate_signal(ready[0]['event']['branch_signals'][bid])
    bid,s=state('AA',monkeypatch)
    for r in (row(0,102),row(1,100),row(2,101),row(3,99.799)):feed(s,r)
    assert not feed(s,row(4,101)) and s.counts['retest_expired_or_breached']

def test_source_break_censors_roots(monkeypatch):
    _,s=state('GA',monkeypatch)
    for i in range(62):feed(s,row(i))
    feed(s,row(62,100.1));assert s.path_pending
    feed(s,row(63,100.1,valid=0));assert not s.path_pending
    assert not feed(s,row(64,100.2))

def test_old_signals_inputs_and_prompts_unchanged(monkeypatch):
    from src.tests.test_continuous_reversal_branches import rows
    values=rows();bid='legacy_all_v1'
    v4=R.State(branch_ids=[bid],session_anchor=values[0]);v3=OR.State(branch_ids=[bid],session_anchor=values[0])
    for r in values:
        feed(v4,r);feed(v3,r)
    e,s=v4.snapshot(v4.ready[-1]);oe,os=v3.snapshot(v3.ready[-1])
    assert s==os
    for arm in AUX.ARMS:
        assert A.production_request(s['branch_inputs'][bid],arm,event=e['branch_signals'][bid])==A.OLD.production_request(os['branch_inputs'][bid],arm,event=oe['branch_signals'][bid])

def test_v4_native_stage_and_v3_sources_unchanged(native):
    root,parent,_,_=native;m,a=migrated_reports(native)
    m=P.seal(dict(m,schema='continuous_reversal_path_postclose_v1'))
    a=P.seal(dict(a,schema='continuous_reversal_path_postclose_v1',machine_report_sha256=m['artifact_content_sha256']))
    candidate=V4.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-08',release_commit='a'*40)
    V4.validate_sources(candidate,root)
    assert candidate['continuous_reversal']['schema']=='continuous_reversal_policy_v4'

@pytest.fixture
def backend_restore():
    from src.engine.scalping import reversal_policy_backend as D
    attrs={k:copy.deepcopy(getattr(R,k)) for k in ('_STATES','_CLAIMS','_ANCHORS','_RESTORED_DAYS','_EMPTY_PREFIX_DAYS')}
    family,generation,active=R._FAMILY,R._GENERATION,D._ACTIVE
    R._STATES.clear();R._CLAIMS.clear();R._ANCHORS.clear();R._RESTORED_DAYS.clear();R._EMPTY_PREFIX_DAYS.clear()
    yield
    for k,v in attrs.items():setattr(R,k,v)
    R._FAMILY,R._GENERATION,D._ACTIVE=family,generation,active


def issued(native):
    root,parent,_,_=native;m,a=migrated_reports(native)
    m=P.seal(dict(m,schema='continuous_reversal_path_postclose_v1'))
    a=P.seal(dict(a,schema='continuous_reversal_path_postclose_v1',machine_report_sha256=m['artifact_content_sha256']))
    return V4.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-08',release_commit='a'*40)


def test_generation_rewarm_does_not_emit_historical_breakout(native,monkeypatch,backend_restore):
    bid,s=state('HB',monkeypatch)
    for i in range(65):feed(s,row(i))
    R._STATES['test']=s
    R.configure(issued(native)['continuous_reversal'])
    assert s.legacy.segment_start==T+64
    assert not feed(s,row(65,101)) and not s.root_previous[bid]
    assert not feed(s,row(66,102))


def test_unknown_backend_schema_is_rejected():
    from src.engine.scalping import reversal_policy_backend as D
    with pytest.raises(ValueError,match='schema_unsupported'):
        D.configure_bundle({'continuous_reversal':{'schema':'continuous_reversal_policy_v900'}},None,'2026-10-07')


def test_path_claim_survives_normal_lower_price_then_expires(native,monkeypatch,backend_restore):
    bid,s=state('SA',monkeypatch);family=issued(native)['continuous_reversal'];key='samsung|REGULAR|ALL'
    family['machine_cells'][key]['routes']['SOR']['payload']=R.B.payload([C.branch(bid)])
    family['machine_cells'][key]['routes']['SOR']['branch_metrics']={bid:dict(wins=1,resolved=2)}
    R.configure(family);scope=('005930','SOR','005930_AL','REGULAR','2026-10-07');R._STATES[scope]=s
    s.generation=family['family_sha256']
    for i in range(62):feed(s,row(i))
    feed(s,row(62,100.2));claim=R.claim_snapshot('005930','SOR','SOR_REGULAR',now=T+62,item='005930_AL',family_sha256=family['family_sha256'])
    assert claim['backend']=='registered_v4'
    feed(s,row(63,99))
    assert R.validate_claim(claim,family['family_sha256'],now=T+63)==claim['snapshot']
    with pytest.raises(ValueError,match='expired'):
        R.validate_claim(claim,family['family_sha256'],now=T+67.001)
    altered=copy.deepcopy(claim);altered['snapshot'][0]['epoch']+=1
    with pytest.raises(ValueError,match='changed'):R.validate_claim(altered,family['family_sha256'],now=T+63)


def test_same_tick_union_one_opportunity(monkeypatch):
    monkeypatch.setattr(C,'matches',lambda b,e,f:True)
    ids=[C.ALIASES[x] for x in ('SA','JA','HB')]
    s=R.State(branch_ids=ids,session_anchor=row(0),offline=True)
    for i in range(62):feed(s,row(i))
    ready=feed(s,row(62,100.3));assert len(ready)==1 and len(ready[0]['event']['branch_signals'])==3
    assert len({x['event_id'] for x in ready[0]['event']['branch_signals'].values()})==1


def test_live_and_offline_pending_caps_are_distinct(monkeypatch):
    bid,s=state('GA',monkeypatch)
    s.offline=False;s.path_pending={str(i):dict(bid=bid,price=99,epoch=T+62,minimum_price=99) for i in range(R.B.MAX_PENDING)}
    # No lower price resets these roots and less than 1 sec has elapsed.
    for i in range(62):feed(s,row(i))
    feed(s,row(62,100.1))
    assert len(s.path_pending)==R.B.MAX_PENDING and s.counts['path_pending_overload']==1


def test_actual_worker_reserves_durably_and_reuses_completed(tmp_path,monkeypatch):
    from src.engine.scalping import continuous_reversal_path_postclose as PC
    from src.engine.scalping import ai_decision_quality as Q
    bid,s=state('SA',monkeypatch)
    for i in range(62):feed(s,row(i))
    ready=feed(s,row(62,100.2))[0];event,source=s.snapshot(ready);signal=event['branch_signals'][bid]
    point=dict(event_id=event['event_id'],canonical_id=event['canonical_opportunity_id'],phase='MOMENTUM_CROSS',
        event=signal,input=source['branch_inputs'][bid])
    day='2026-10-07';base=tmp_path/'report/continuous_reversal_registered/v4'/day
    P.write(base/'current-run.json',P.seal(dict(run_sha256='a'*64)))
    out=PC.directory(tmp_path,day);P.write(out/'input-census.json',dict(machine_report_sha256='b'*64))
    db=PC.connect_ledger(tmp_path)
    for arm in AUX.ARMS:
        req=PC.request(point,arm);db.execute("INSERT INTO requests(identity,request,state) VALUES (?,?,'planned')",(req['paired_replay_id'],json.dumps(req)))
        db.execute('INSERT INTO owners VALUES (?,?,?,?,?,?)',('b'*64,'comparison',point['canonical_id'],arm,req['paired_replay_id'],'WIN'))
    db.commit();db.close();seen=[]
    def transport(req,timeout_sec):
        check=PC.connect_ledger(tmp_path);status=check.execute('SELECT state FROM requests WHERE identity=?',(req['paired_replay_id'],)).fetchone()[0];check.close()
        assert status=='reserved';assert 'WIN' not in json.dumps(req['candidate_input'])
        seen.append(req['paired_replay_id'])
        return dict(provider_provenance=dict(response_id='actual-fake-transport-'+req['paired_replay_id']),
            candidate_response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],supporting_fact_ids=['observed_machine_signal'],contradicting_fact_ids=[],confidence=50))
    monkeypatch.setattr(Q,'execute_openai_prompt_v2_candidate',transport)
    assert PC.calls(tmp_path,day)['new_calls']==5 and len(seen)==5
    assert PC.calls(tmp_path,day)['new_calls']==0
    assert not (tmp_path/'report/continuous_reversal_registered/request-ledger.sqlite3').exists()


def path_family(native):
    f=issued(native)['continuous_reversal'];key='samsung|REGULAR|ALL';bid=C.ALIASES['SA'];cell=f['machine_cells'][key]['routes']['SOR']
    cell.update(payload=R.B.payload([C.branch(bid)]),local_metrics=dict(wins=1,resolved=2),branch_metrics={bid:dict(wins=1,resolved=2)})
    cell['payload_sha256']=P.digest(cell['payload'])
    arm=AUX.ARMS[-1];policy=dict(arm=arm,binding=A.binding('MOMENTUM_CROSS',arm),local_metrics=dict(pass_wins=1,pass_count=2),actual_response_evidence=[dict(path='fixture-only',sha256='a'*64)])
    aux=f['auxiliary_cells'][key]['routes']['SOR'];aux['payload']=dict(branch_policies={bid:policy});aux['payload_sha256']=P.digest(aux['payload'])
    f['family_sha256']=P.digest({k:v for k,v in f.items() if k!='family_sha256'})
    return f


def path_snapshot(f,monkeypatch):
    bid,s=state('SA',monkeypatch);s.generation=f['family_sha256']
    for i in range(62):feed(s,row(i))
    ready=feed(s,row(62,100.2))[0]
    return s.snapshot(ready)


def test_typed_monitor_replays_current_phase_without_first_facts(native,monkeypatch):
    from src.engine.scalping import ai_decision_trace as trace
    from src.engine.monitoring import submission_bottleneck_monitor as M
    f=path_family(native);snapshot=path_snapshot(f,monkeypatch)
    decision,inp,prompt,schema=V4.assess(f,snapshot,symbol='005930',session='SOR_REGULAR')
    assert decision['price_reversal_confirmed'] is False and decision['machine_signal_confirmed'] is True
    root=native[0];now=datetime.fromtimestamp(T+63,R.K.KST);bundle=dict(target_date='2026-10-07',bundle_sha256='b'*64,continuous_reversal=f)
    raw=dict(stock_code='005930',session_bucket='SOR_REGULAR',effective_venue='SOR',evaluation_attempt_id='typed-attempt',entry_machine_input_as_of=T+62)
    context=dict(family_sha256=f['family_sha256'],source_date=f['source_date'],publication_date=f['publication_date'],effective_date=f['effective_date'],
        machine_component_sha256=P.digest(f['machine_cells']),auxiliary_component_sha256=P.digest(f['auxiliary_cells']),
        arm=AUX.ARMS[-1],snapshot_read_at=T+62.5,snapshot_cutoff=T+62,input_sha256=P.digest(inp),prompt_sha256=P.digest(prompt),response_schema_sha256=P.digest(schema),
        primary_branch=decision['primary_branch'],matched_branches=decision['matched_branches'],signal_id=decision['signal_id'],branch_definition_sha256=decision['branch_definition_sha256'],phase=decision['decision_phase'])
    monkeypatch.setenv('KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED','1');monkeypatch.setattr(trace,'DATA_DIR',root);monkeypatch.setattr(trace,'_now',lambda:now)
    trace.capture_machine_observation(exact_payload=raw,setup_evidence={},assessment=decision,bundle_sha256='b'*64,reversal_context=context,reversal_request=dict(input=inp,prompt=prompt,response_schema=schema))
    observation=json.loads((root/'ai_decision_payloads/ai_decision_payloads_2026-10-07.jsonl').read_text().splitlines()[-1])
    payload,receipt=M._reversal_observation_receipt(bundle,observation)
    assert payload['branches']==[C.branch(C.ALIASES['SA'])]
    forged=copy.deepcopy(inp);forged['observed_signal']['price']+=1
    with pytest.raises(ValueError,match='input_conflict'):A.validate_input_signal(forged,decision['auxiliary_event'])


@pytest.mark.parametrize('change',['bundle','expired','veto'])
def test_typed_compose_rechecks_current_policy_and_claim(native,monkeypatch,change):
    from src.engine.scalping import continuous_reversal_policy as D,mechanistic_entry_runtime_policy as N
    from src.engine.scalping import reversal_policy_backend as backend
    f=path_family(native);snap=path_snapshot(f,monkeypatch)
    decision,inp,_,_=V4.assess(f,snap,symbol='005930',session='SOR_REGULAR')
    policy=dict(continuous_reversal_assessment=decision,continuous_reversal_input=inp,continuous_reversal_arm=AUX.ARMS[-1],machine_bundle_sha256='b'*64,continuous_reversal_claim={})
    monkeypatch.setattr(N,'load_effective',lambda **k:dict(bundle_sha256='c'*64 if change=='bundle' else 'b'*64))
    def validate(*a,**k):
        if change=='expired':raise ValueError('reversal_signal_expired_or_changed')
    monkeypatch.setattr(backend,'validate_any_claim',validate)
    response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],supporting_fact_ids=['observed_machine_signal'],contradicting_fact_ids=[],confidence=50)
    if change=='veto':response.update(risk_verdict='VETO',risk_codes=['EARLY_SIGNAL_FRAGILE'],contradicting_fact_ids=['volume_not_expanding'])
    result=D.compose(response,policy)
    assert result['action']!='BUY' and not result['entry_ai_screen_pass']


def test_unknown_claim_backend_is_rejected():
    from src.engine.scalping.reversal_policy_backend import backend
    with pytest.raises(ValueError,match='backend_unsupported'):backend({'backend':'registered_v900'})


def test_primary_path_event_does_not_keep_another_branches_decline(native,monkeypatch):
    f=path_family(native);snap=path_snapshot(f,monkeypatch)
    # The same native confirmation may have a FIRST branch as another lineage.
    snap[0].update(low_price=90,drop_pct=10,down_steps=4,confirmation_pct=11)
    d,inp,_,_=V4.assess(f,snap,symbol='005930',session='SOR_REGULAR')
    assert not {'low_price','drop_pct','down_steps','confirmation_pct'}.intersection(d['event'])
    assert d['auxiliary_event']['decision_phase']=='MOMENTUM_CROSS'


@pytest.mark.parametrize('alias',['SB','AA'])
@pytest.mark.parametrize('boundary',['equal_breach_floor','below_floor','deadline_after','same_tick_touch'])
def test_retest_boundaries_do_not_shift_confirmation(monkeypatch,alias,boundary):
    bid,s=state(alias,monkeypatch)
    for r in (row(0,102),row(1,100),row(2,101)):feed(s,r)
    touch=99.8 if boundary=='equal_breach_floor' else 99.799 if boundary=='below_floor' else 100
    feed(s,row(3,touch))
    target=102 if alias=='SB' else 101
    ready=feed(s,row(4,target,t=122.001 if boundary=='deadline_after' else 4))
    if boundary in {'below_floor','deadline_after'}:assert not ready
    else:assert ready
    # A touch has to be followed by a distinct later native observation.
    proof=ready[0]['event']['branch_signals'][bid]['signal_proof'] if ready else None
    if proof:assert proof['touch_sequence']<ready[0]['event']['native_sequence']


def test_hold_has_no_extra_ttl_or_confirmation_momentum_floor(monkeypatch):
    bid,s=state('GA',monkeypatch)
    for i in range(62):feed(s,row(i))
    feed(s,row(62,100.1))
    # Keep price equal for 60 sec; confirmation at this first actual later tick
    # has ret60 == 0 although the root was above +0.05. No invented TTL.
    ready=feed(s,row(63,100.1,t=123));assert ready
    signal=ready[0]['event']['branch_signals'][bid]
    assert signal['branch_features']['ret']==0
    A.validate_signal(signal)


def test_reused_first_signal_survives_simultaneous_typed_root(tmp_path,monkeypatch):
    import gzip
    from src.engine.scalping import continuous_reversal_path_postclose as PC
    from src.engine.scalping import continuous_reversal_registered_postclose as PREVIOUS
    values=[row(i) for i in range(61)]+[row(61,99.9),row(62,100.2)]
    # Freeze a real old FIRST point, with no previously stored branch map.
    old=OR.State(branch_ids=['legacy_all_v1'],session_anchor=values[0])
    for r in values:feed(old,r)
    e=copy.deepcopy(old.ready[-1]['event']);signal=e['branch_signals']['legacy_all_v1']
    base={k:v for k,v in e.items() if k not in ('branch_signals','branch_features','anchor_lineage')}
    point=dict(event=base,entry_index=62,branch_hits=['legacy_all_v1'],confirmed_signals={},anchor_lineage=e['anchor_lineage'],canonical_id=e['canonical_opportunity_id'],outcome=dict(status='UNRESOLVED'))
    raw=tmp_path/'ticks.json.gz';raw.write_bytes(gzip.compress(json.dumps(dict(symbols={'005930':values})).encode()))
    part=tmp_path/'old-points.jsonl.gz';part.write_bytes(gzip.compress((json.dumps(point)+'\n').encode()))
    rec=dict(day='2026-10-07',venue='SOR',session='SOR_REGULAR',path=str(raw),sha256=P.file_hash(raw))
    prior=P.seal(dict(registry_sha256=OLD.SHA256,partitions=[dict(normalized_source=rec,path=str(part),sha256=P.file_hash(part),census={})],source_receipts=[]))
    origin=tmp_path/'base-population.json';P.write(origin,prior)
    source=P.seal(dict(normalized_sources=dict(partitions=[rec]),base_population=dict(path=str(origin),sha256=P.file_hash(origin))))
    monkeypatch.setattr(P,'completed_bars',lambda *a,**k:({},[]));monkeypatch.setattr(C,'matches',lambda *a:True)
    PC.begin_run(tmp_path,'2026-10-07','2026-10-07',dict(bundle_sha256='a'*64),source)
    pop,_=PC.population(tmp_path,'2026-10-07',source=source)
    merged=next(p for p in PC.iter_points(pop) if p['canonical_id']==point['canonical_id'])
    assert merged['confirmed_signals']['legacy_all_v1']['low_price']==signal['low_price']
    assert merged['confirmed_signals']['legacy_all_v1']['decision_phase']=='FIRST_UPTICK'
    assert C.ALIASES['SA'] in merged['branch_hits']


@pytest.mark.parametrize('corruption',['missing','wrong_identity'])
def test_expected_population_detects_input_loss_before_ledger(tmp_path,monkeypatch,corruption):
    import gzip
    from src.engine.scalping import continuous_reversal_path_postclose as PC
    bid='legacy_all_v1';key='samsung|REGULAR|ALL';day='2026-10-07'
    cell=dict(payload=R.B.payload([C.branch(bid)]),branch_metrics={bid:dict(wins=1,resolved=1)})
    cells=[dict(key=key,routes=dict(SOR=cell))]
    point=dict(canonical_id='c'*64,event=dict(symbol='005930',market='REGULAR',confirmation_price=100,venue='SOR'),
               branch_hits=[bid],outcome=dict(status='WIN'))
    part=tmp_path/'points.gz';part.write_bytes(gzip.compress((json.dumps(point)+'\n').encode()))
    pop=tmp_path/'population.json';P.write(pop,dict(partitions=[dict(path=str(part))]))
    machine=dict(artifact_content_sha256='b'*64,population_path=str(pop),cells=cells,baseline_cells=cells,
                 applied_history=dict(consumed_versions=[]))
    P.write(tmp_path/'report/continuous_reversal_registered/v4'/day/'current-run.json',P.seal(dict(run_sha256='a'*64)))
    out=PC.directory(tmp_path,day);(out/'frozen').mkdir(parents=True,exist_ok=True)
    declared=list(PC.eligible_population_points(machine,json.loads(pop.read_text())))
    if corruption=='missing':declared=[]
    else:declared[0]['canonical_id']='d'*64
    cached=out/'frozen'/('inputs-'+machine['artifact_content_sha256']+'-'+PC.input_generation()+'.jsonl.gz')
    cached.write_bytes(gzip.compress(''.join(json.dumps(p)+'\n' for p in declared).encode()))
    def forbidden(*args,**kwargs):raise AssertionError('ledger must not open on input loss')
    monkeypatch.setattr(PC,'connect_ledger',forbidden)
    with pytest.raises(ValueError,match='population_input_mismatch'):PC.prepare_inputs(tmp_path,day,machine)
    universe=json.loads((out/'frozen'/('universe-'+machine['artifact_content_sha256']+'.json')).read_text())
    assert universe['eligible_points']==1 and universe['expected_requests']==5


@pytest.mark.parametrize('workers',[0,5,True])
def test_actual_worker_keeps_four_inflight_limit(tmp_path,workers):
    from src.engine.scalping import continuous_reversal_path_postclose as PC
    with pytest.raises(ValueError,match='concurrency_invalid'):PC.calls(tmp_path,'2026-10-07',workers=workers)


def test_interleaved_partition_grouping_preserves_all_values_and_owner_set(tmp_path):
    import gzip
    from src.engine.scalping import continuous_reversal_path_postclose as PC
    points=[dict(event=dict(symbol=s,source_item=s+'_AL'),canonical_id=str(i),branch_id='branch',
                 comparison='comparison',owners=['selected'],outcome=dict(status='WIN'))
            for i,s in enumerate(['005930','034020','005930','034020','005930'])]
    path=tmp_path/'points.gz';path.write_bytes(gzip.compress(''.join(json.dumps(p)+'\n' for p in points).encode()))
    grouped=list(PC.grouped_partition_points(dict(path=str(path)),tmp_path))
    assert [p['canonical_id'] for p in grouped]==['0','2','4','1','3']
    assert sorted(grouped,key=lambda p:p['canonical_id'])==points
    assert PC.input_owner_census(grouped)==PC.input_owner_census(points)
    assert not list(tmp_path.glob('.input-group-*'))


def test_issued_receipt_custody_survives_mutable_census_progress(tmp_path):
    from src.engine.scalping import continuous_reversal_path_postclose as PC
    origin=tmp_path/'input-census.json';P.write(origin,dict(planned=5,completed=0))
    receipt=PC.freeze_receipt(tmp_path,origin);frozen=Path(receipt['path'])
    P.write(origin,dict(planned=0,completed=5))
    assert P.file_hash(frozen)==receipt['sha256'] and json.loads(frozen.read_text())['planned']==5
    later=PC.freeze_receipt(tmp_path,origin)
    assert later['path']!=receipt['path'] and P.file_hash(later['path'])==later['sha256']
    frozen.write_text('{}')
    P.write(origin,dict(planned=5,completed=0))
    with pytest.raises(ValueError,match='snapshot_changed'):PC.freeze_receipt(tmp_path,origin)
