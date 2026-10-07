"""Registered scope, causal feature, migration and durable comparison contracts."""
import copy
from collections import Counter
import json
from datetime import datetime
from pathlib import Path
import pytest
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import continuous_reversal_postclose as P
from src.engine.scalping import continuous_reversal_policy_v2 as V2
from src.engine.scalping import continuous_reversal_policy_v3 as V3
from src.engine.scalping import reversal_registered_catalog as C
from src.engine.scalping import reversal_registered_runtime as R
from src.engine.scalping import continuous_reversal_registered_postclose as PC
from src.engine.scalping import mechanistic_entry_runtime_policy as N
from src.engine.scalping import reversal_auxiliary_phases as A
from src.engine.scalping import reversal_auxiliary_contract as AUX
from src.tests.test_continuous_reversal_policy_v2 import native
from src.tests.test_continuous_reversal_branches import rows


@pytest.fixture(autouse=True)
def globals_restore():
    old=(R._FAMILY,R._GENERATION,dict(R._STATES),dict(R._CLAIMS),dict(R._ANCHORS),set(R._RESTORED_DAYS),set(R._EMPTY_PREFIX_DAYS))
    R._FAMILY=None;R._GENERATION=None;R._STATES.clear();R._CLAIMS.clear()
    yield
    R._FAMILY,R._GENERATION,states,claims,anchors,days,empty=old
    for dest,src in ((R._STATES,states),(R._CLAIMS,claims),(R._ANCHORS,anchors)):
        dest.clear();dest.update(src)
    R._RESTORED_DAYS.clear();R._RESTORED_DAYS.update(days);R._EMPTY_PREFIX_DAYS.clear();R._EMPTY_PREFIX_DAYS.update(empty)


def migrated_reports(native):
    root,parent,m,a=native
    candidate=V2.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday')
    machine,aux=V3.migrate(candidate['continuous_reversal'])
    common=dict(schema=PC.SCHEMA,source_date='2026-10-07',publication_date='2026-10-07',status='completed')
    m=P.seal(dict(common,cells=list(machine.values()),parent_bundle_sha256=parent['bundle_sha256'],source_manifest_sha256='a'*64,label_contract=C.LABEL,source_receipts=[]))
    a=P.seal(dict(common,cells=list(aux.values()),machine_report_sha256=m['artifact_content_sha256'],results_sources=[]))
    return m,a


def family(native):
    root,_,_,_=native;m,a=migrated_reports(native)
    return V3.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday')['continuous_reversal']


def test_registry_48_cells_routes_and_finite_manifest():
    assert len(C.cells())==48
    assert all(C.group(s)!='other_non_fixed' for s in C.FIXED)
    assert C.group('000001')=='other_non_fixed'
    assert C.band(19999)=='LT_20000' and C.band(20000)=='20000_TO_100000' and C.band(100000)=='GE_100000'
    assert len(C.PORTFOLIOS['samsung|REGULAR|ALL']['SOR'])==111
    assert max(len(p['branch_ids']) for p in C.PORTFOLIOS['samsung|REGULAR|ALL']['SOR'])==4
    for key in C.cells():
        for route,ps in C.PORTFOLIOS[key].items():
            for p in ps:C.validate_payload(B.payload([C.branch(b) for b in p['branch_ids']]),key,route)
    assert not C.applicable('S1','samsung|PRE|ALL','SOR')
    assert not C.applicable('D1','034020|REGULAR|LT_20000','KRX')
    assert not C.applicable('G1','403870|REGULAR|20000_TO_100000','SOR')
    with pytest.raises(ValueError):C.validate_payload(B.payload([C.branch('S1')]*2),'samsung|REGULAR|ALL','SOR')


def test_v2_migration_preserves_all_branches_and_phase_bytes(native):
    f=family(native);V3.validate_family(f)
    assert len(f['machine_cells'])==48
    sor=f['machine_cells']['samsung|REGULAR|ALL']['routes']['SOR']
    assert [b['branch_id'] for b in sor['payload']['branches']]==[B.legacy_branch('ALL')['branch_id'],B.BRANCH]
    assert all(m is None for m in sor['branch_metrics'].values()) and sor['local_metrics'] is None
    assert f['machine_cells']['samsung|REGULAR|ALL']['routes']['KRX']['payload']['branches']==[B.legacy_branch('ALL')]
    for g in ('034020','403870','196170','036930','other_non_fixed'):
        for market in C.ROUTES:
            for band in C.BANDS:
                for v in f['machine_cells'][f'{g}|{market}|{band}']['routes'].values():
                    assert v['payload']['branches']==[B.legacy_branch('ALL')]
    values=rows();s=R.State(branch_ids=[B.BRANCH],session_anchor=values[0])
    for r in values:s.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')
    snap=s.snapshot(s.ready[-1]);assessment,inp,prompt,schema=V3.assess(f,snap,symbol='005930',session='SOR_REGULAR')
    assert assessment['action']=='ENTER_NOW' and assessment['primary_branch']==B.BRANCH
    old=B.BranchState(session_anchor=values[0])
    for r in values:old.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')
    event,source=old.snapshot(old.ready[-1])
    assert (inp,prompt,schema)==A.production_request(source,AUX.ARMS[-1],phase=B.CONFIRMED,event=event)


def test_stage_is_preparation_not_activation_and_source_tamper(native):
    root,parent,_,_=native;m,a=migrated_reports(native)
    candidate=V3.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-08',release_commit='a'*40)
    assert N.load(data_root=root,target_date='2026-10-08')==candidate
    assert N.load_effective(data_root=root,target_date='2026-10-08')['bundle_sha256']==parent['bundle_sha256']
    with pytest.raises(ValueError,match='route_coverage'):
        bad=copy.deepcopy(candidate['continuous_reversal']);bad['machine_cells']['samsung|REGULAR|ALL']['routes'].pop('NXT')
        bad['family_sha256']=P.digest({k:v for k,v in bad.items() if k!='family_sha256'});V3.validate_family(bad)
    path=N.root(root)/'sources'/f"reversal-{m['artifact_content_sha256']}.json";path.write_text('{}')
    with pytest.raises(ValueError):V3.validate_sources(candidate,root)


def test_features_boundaries_missing_and_future_prefix():
    base=1791331200.;rs=[[base+t,1,i+1,p,p-.01,p+.01,10,1,1,'000001_AL',0]
        for i,(t,p) in enumerate([(0,100),(29,99),(30,101),(59,102),(60,103),(61,104)])]
    s=R.State(branch_ids=[],session_anchor=rs[0]);before=[]
    for r in rs:
        s.observe(r,symbol='000001',venue='SOR',session='SOR_REGULAR');before.append(s.features(r))
    f=before[-2]
    assert f['ret']==pytest.approx(3.) and f['structure']=='RISING' and f['buy10'] is None
    prefix=copy.deepcopy(before)
    future=rs[-1][:];future[0]+=1;future[2]+=1;future[3]=9999
    s.observe(future,symbol='000001',venue='SOR',session='SOR_REGULAR')
    assert before==prefix
    gap=future[:];gap[2]+=2;s.observe(gap,symbol='000001',venue='SOR',session='SOR_REGULAR')
    assert s.features(gap)['structure'] is None


def test_decline_boundary_is_frozen_and_unknown_is_not_mixed():
    e=dict(symbol='000001',market='REGULAR',venue='SOR',source_item='000001_AL',confirmation_price=100001,drawdown_5m_pct=.8,drop_pct=.3,volume_ratio_60s=1,spread_pct=.05)
    f=dict(ret=.2,session=-.4,session_trend='DOWN',structure='MIXED')
    assert C.matches('G2',e,f) is False
    e['drawdown_5m_pct']=.80001;assert C.matches('G2',e,f) is True
    e['drawdown_5m_pct']=1.2;assert C.matches('G2',e,f) is False
    e['drawdown_5m_pct']=1.;f['structure']=None;assert C.matches('G2',e,f) is None


def test_multi_branch_single_tick_claim_duplicate_ttl_and_generation(native):
    f=family(native);R.configure(f);values=rows();state=R.State(branch_ids=[B.legacy_branch('ALL')['branch_id'],B.BRANCH,'S1'],session_anchor=values[0],generation=f['family_sha256'])
    for r in values:state.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')
    key=('005930','SOR','005930_AL','REGULAR','2026-10-07');R._STATES[key]=state
    # Expired earlier FIRST cannot occupy the queue in front of confirmation.
    claim=R.claim_snapshot('005930','SOR','SOR_REGULAR',now=values[-1][0],item='005930_AL',family_sha256=f['family_sha256'])
    assert claim and B.legacy_branch('ALL')['branch_id'] in claim['snapshot'][0]['branch_signals']
    confirmed=R.claim_snapshot('005930','SOR','SOR_REGULAR',now=values[-1][0],item='005930_AL',family_sha256=f['family_sha256'])
    assert confirmed and B.BRANCH in confirmed['snapshot'][0]['branch_signals']
    assert R.validate_claim(claim,f['family_sha256'],now=values[-1][0])==claim['snapshot']
    with pytest.raises(ValueError):R.validate_claim(claim,'changed',now=values[-1][0])
    with pytest.raises(ValueError):R.validate_claim(claim,f['family_sha256'],now=values[-1][0]+5.01)
    tamper=copy.deepcopy(claim);tamper['snapshot'][0]['entry_ask']=1
    with pytest.raises(ValueError):R.validate_claim(tamper,f['family_sha256'],now=values[-1][0])


def test_raw_fraction_union_and_incumbent_tie():
    old=dict(payload_sha256='inc')
    candidates=[dict(payload_sha256='inc',metrics=dict(wins=274,resolved=274)),dict(payload_sha256='hpsp_union',metrics=dict(wins=305,resolved=305))]
    assert PC.select(candidates,old)['payload_sha256']=='inc'
    candidates[0]['metrics']=dict(wins=0,resolved=0)
    assert PC.select(candidates,old)['payload_sha256']=='hpsp_union'
    assert PC.metric(Counter(WIN=2,FAIL_STOP=1,UNRESOLVED=8))['resolved']==3


def test_request_reuse_excludes_comparison_owner_and_preserves_phase(native):
    f=family(native);values=rows();s=R.State(branch_ids=[B.BRANCH],session_anchor=values[0])
    for r in values:s.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')
    snap=s.snapshot(s.ready[-1]);e=snap[0]['branch_signals'][B.BRANCH];source=snap[1]['branch_inputs'][B.BRANCH]
    p=dict(event=e,event_id=e['event_id'],input=source,phase=B.CONFIRMED,comparison='one')
    req=PC.request(p,AUX.ARMS[-1]);p['comparison']='two';assert PC.request(p,AUX.ARMS[-1])==req
    p['phase']=B.FIRST;assert PC.request(p,AUX.ARMS[-1])['paired_replay_id']!=req['paired_replay_id']


def test_durable_ledger_same_request_multiple_owners_and_reservation(tmp_path):
    db=PC.connect_ledger(tmp_path)
    db.execute("INSERT INTO requests(identity,request,state,reserved_at) VALUES ('one','{}','reserved','now')")
    for comparison in ('a','b'):db.execute('INSERT INTO owners VALUES (?,?,?,?,?,?)',('generation',comparison,'tick','arm','one','WIN'))
    db.commit();db.close();db=PC.connect_ledger(tmp_path)
    assert db.execute('SELECT count(*) FROM requests').fetchone()[0]==1
    assert db.execute('SELECT count(*) FROM owners').fetchone()[0]==2
    assert db.execute('SELECT state FROM requests').fetchone()[0]=='reserved'
    db.close()


def test_streaming_daily_producer_calls_carry_and_native_handoff(native,monkeypatch):
    import gzip
    from src.engine.scalping import ai_decision_quality as provider
    from src.engine.scalping import continuous_reversal_policy as dispatch
    root,parent,_,_=native
    m,a=migrated_reports(native)
    # The next-day preparation remains independent of active parent selection.
    rs=rows();last=rs[-1][:];last[0]+=10;last[2]+=1;last[3]=last[5]=105.;last[4]=104.99;rs.append(last)
    path=root/'normalized.json.gz';path.write_bytes(gzip.compress(json.dumps(dict(symbols={'005930':rs})).encode()))
    source=P.seal(dict(schema=P.SCHEMA,source_date='2026-10-07',normalized_sources=dict(partitions=[dict(day='2026-10-07',venue='SOR',session='SOR_REGULAR',path=str(path),sha256=P.file_hash(path))])))
    monkeypatch.setattr(P,'completed_bars',lambda *args,**kwargs:({},[]));P.write(P.directory(root,'2026-10-07')/'source.json',source)
    machine=PC.machine_report(root,'2026-10-07','2026-10-07',parent,source=source)
    original=(P.directory(root,'2026-10-07')/'machine.json').read_bytes()
    from src.engine.automation.postclose_summary_handoff import _stage_output_issues
    assert _stage_output_issues(root/'report','2026-10-07','main_machine_policy')==[]
    census=PC.prepare_inputs(root,'2026-10-07',machine);assert census['census']['eligible_points']>0
    # Uncalled new branches cannot be married to an unrelated baseline screen.
    pending=PC.auxiliary_report(root,'2026-10-07','2026-10-07',parent,publish_policy=False)
    assert pending['comparison_complete'] is False
    calls=[]
    def actual(req,**kwargs):
        calls.append(req['paired_replay_id']);phase=req['candidate_input']['observation_phase']['stage']
        assert 'outcome' not in req['candidate_input']
        return dict(candidate_response=dict(schema='entry_setup_risk_adjudication_v1',risk_verdict='PASS',risk_codes=['NO_BLOCKING_RISK'],
            supporting_fact_ids=['first_price_uptick','observed_price_decline']+(['additional_higher_trade'] if phase==B.CONFIRMED else []),
            contradicting_fact_ids=[],confidence=70),provider_provenance=dict(response_id=req['paired_replay_id']))
    monkeypatch.setattr(provider,'execute_openai_prompt_v2_candidate',actual)
    assert PC.calls(root,'2026-10-07')['status']=='completed';count=len(calls)
    PC.calls(root,'2026-10-07');assert len(calls)==count
    import subprocess
    monkeypatch.setattr(subprocess,'check_output',lambda *args,**kwargs:'a'*40+'\n')
    auxiliary=PC.auxiliary_report(root,'2026-10-07','2026-10-07',parent)
    assert auxiliary['comparison_complete'] is True
    issued=json.loads((PC.directory(root,'2026-10-07')/'machine.json').read_text())
    for cell in issued['cells']:
        for route,value in cell['routes'].items():
            if (value.get('local_metrics') is None and value.get('carry_source',{}).get('cell_key')!=cell['key']
                    and 'lossless' not in value.get('carry_source',{}).get('reason','')):
                policy=next(c for c in auxiliary['cells'] if c['key']==cell['key'])['routes'][route]['payload']['branch_policies']
                assert all(p.get('carry_source',{}).get('reason')=='no_sample_compatible_regular_selected' for p in policy.values())
    assert (P.directory(root,'2026-10-07')/'machine.json').read_bytes()==original
    handoff=dispatch.direct_handoff(root,'2026-10-07');assert handoff['machine_cell_count']==48
    candidate=N.load(data_root=root,target_date='2026-10-08');V3.validate_sources(candidate,root)
    assert _stage_output_issues(root/'report','2026-10-07','main_auxiliary_policy')==[]
    assert N.load_effective(data_root=root,target_date='2026-10-08')['bundle_sha256']==parent['bundle_sha256']


@pytest.mark.parametrize('mode',['confirmed','missing_quote','no_signal'])
def test_v3_native_monitor_trace_replay(native,monkeypatch,mode):
    from src.engine.scalping import ai_decision_trace as trace
    from src.engine.monitoring import submission_bottleneck_monitor as monitor
    root,_,_,_=native;m,a=migrated_reports(native)
    bundle=V3.stage(root,'2026-10-07','2026-10-07',m,a,target_date='2026-10-07',release_commit='a'*40,effective_mode='intraday');f=bundle['continuous_reversal']
    rs=rows();s=R.State(branch_ids=[B.BRANCH],session_anchor=rs[0])
    if mode=='missing_quote':rs[-1][5]=None
    for r in rs:s.observe(r,symbol='005930',venue='SOR',session='SOR_REGULAR')
    snapshot=s.snapshot(s.ready[-1]) if mode!='no_signal' else None
    assessment,inp,prompt,schema=V3.assess(f,snapshot,symbol='005930',session='SOR_REGULAR')
    clock=rs[-1][0]+.2;now=datetime.fromtimestamp(clock,N.KST)
    raw=dict(stock_code='005930',session_bucket='SOR_REGULAR',effective_venue='INTEGRATED',evaluation_attempt_id='v3-attempt',entry_machine_input_as_of=clock-.1)
    receipt=dict(family_sha256=f['family_sha256'],source_date=f['source_date'],publication_date=f['publication_date'],effective_date=f['effective_date'],
        machine_component_sha256=P.digest(f['machine_cells']),auxiliary_component_sha256=P.digest(f['auxiliary_cells']),arm=assessment.get('auxiliary_arm'),
        phase=assessment.get('decision_phase',B.FIRST),primary_branch=assessment.get('primary_branch'),matched_branches=assessment.get('matched_branches'),
        signal_id=assessment.get('signal_id'),branch_definition_sha256=assessment.get('branch_definition_sha256'),snapshot_read_at=clock-.05,
        input_sha256=P.digest(inp) if inp else None,prompt_sha256=P.digest(prompt) if inp else None,response_schema_sha256=P.digest(schema) if inp else None)
    monkeypatch.setenv('KORSTOCKSCAN_AI_DECISION_TRACE_ENABLED','1');monkeypatch.setattr(trace,'DATA_DIR',root);monkeypatch.setattr(trace,'_now',lambda:now)
    trace.capture_machine_observation(exact_payload=raw,setup_evidence={},assessment=assessment,bundle_sha256=bundle['bundle_sha256'],reversal_context=receipt,
                                     reversal_request=dict(input=inp,prompt=prompt,response_schema=schema) if inp else None)
    observation=json.loads((root/'ai_decision_payloads/ai_decision_payloads_2026-10-07.jsonl').read_text().splitlines()[-1])
    monitor._reversal_observation_receipt(bundle,observation)


def test_registered_duplicate_conflict_isolated(monkeypatch):
    from src.engine.scalping import continuous_reversal_registered_postclose as PC
    points=[dict(canonical_id='a',value=1),dict(canonical_id='a',value=1),
            dict(canonical_id='b',value=2),dict(canonical_id='b',value=3),dict(canonical_id='c',value=4)]
    monkeypatch.setattr(PC,'iter_points',lambda population:iter(points))
    census={}
    assert list(PC.unique_points({},census))==[points[0],points[-1]]
    assert census==dict(duplicate_rows=2,quarantined_identities=['b'])


def test_mixed_tick_offline_primary_keeps_own_first_decline(native,monkeypatch):
    import gzip
    root,parent,_,_=native
    rs=rows();last=rs.pop();dip=last[:];dip[0]-=.5;dip[3:6]=[103.35,103.34,103.36]
    rs.append(dip);last[2]+=1;rs.append(last)
    points,_=PC.replay(rs,symbol='005930',venue='SOR',session='SOR_REGULAR')
    mixed=next(p for p in points if p['entry_index']==len(rs)-1)
    assert mixed['first_signal']['low_price']==103.35
    assert mixed['confirmed_signals'][B.BRANCH]['low_price']==103.3
    future=last[:];future[0]+=10;future[2]+=1;future[3:6]=[105.,104.99,105.01];rs.append(future)
    path=root/'normalized.json.gz';path.write_bytes(gzip.compress(json.dumps(dict(symbols={'005930':rs})).encode()))
    source=P.seal(dict(schema=P.SCHEMA,source_date='2026-10-07',normalized_sources=dict(partitions=[dict(day='2026-10-07',venue='SOR',session='SOR_REGULAR',path=str(path),sha256=P.file_hash(path))])))
    monkeypatch.setattr(P,'completed_bars',lambda *args,**kwargs:({},[]))
    machine=PC.machine_report(root,'2026-10-07','2026-10-07',parent,source=source,publish_outputs=False)
    cell=next(c for c in machine['cells'] if c['key']=='samsung|REGULAR|ALL')['routes']['SOR']
    cell.update(payload=B.payload([B.pattern_branch()]),branch_metrics={B.BRANCH:dict(wins=1,resolved=1)})
    cell['payload_sha256']=P.digest(cell['payload']);machine=P.seal(machine)
    census=PC.prepare_inputs(root,'2026-10-07',machine)
    with gzip.open(census['input_path'],'rt') as handle:
        inputs=[json.loads(line) for line in handle if json.loads(line)['canonical_id']==mixed['canonical_id']]
    assert {p['phase'] for p in inputs}=={B.FIRST,B.CONFIRMED}
    facts={p['phase']:p['input']['entry_setup_evidence_v1']['facts'] for p in inputs}
    assert facts[B.FIRST]['low_price']==103.35 and facts[B.CONFIRMED]['low_price']==103.3
