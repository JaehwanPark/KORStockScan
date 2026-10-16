import copy
import math
from pathlib import Path

import pytest
from src.engine.scalping import reversal_cumulative_catalog as Q
from src.engine.scalping import reversal_cumulative_registration as R
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping import reversal_extended_auxiliary as A
from src.engine.scalping import reversal_extended_union as U
from src.engine.scalping.continuous_reversal_postclose import digest, seal
from src.engine.scalping.reversal_cumulative_runtime import ProgressWindow, hold_breached
from src.engine.scalping.reversal_extended_state import State
from src.tests.test_reversal_cumulative_policy import rows, request as legacy_request

SCOPE='other_non_fixed|PRE|LT_20000|NXT'
GROUP=Q.PROGRESS['groups'][SCOPE]


def test_progress_registry_reaches_current_typed_auxiliary_request(monkeypatch):
    from src.engine.scalping import continuous_reversal_operating_postclose as O
    from src.engine.scalping import reversal_auxiliary_registry as G
    event = dict(registry_sha256=C.PROGRESS_SHA256, event_id='2026-10-15:NXT:PRE:000001:1:2',
        epoch=1792022400., symbol='000001', market='PRE', venue='NXT', source_item='000001_NX',
        native_epoch=1, native_sequence=2)
    monkeypatch.setattr(U, 'production_request', lambda *args, **kwargs:
        (dict(schema=U.VERSION), 'Current typed prompt', {'type':'object'}))
    monkeypatch.setattr(O.UNION, 'production_request', lambda *args, **kwargs:
        pytest.fail('Progress must not use the older v2 projector'))
    registry = G.definition(U.V1.ARMS[1], input_version=U.VERSION)
    request = G.request([event,{}], registry)
    assert request['candidate_input']['schema'] == U.VERSION
    assert request['candidate']['schema_name'] == U.VERSION
    assert request['actual_order_submitted'] is False


def fixture():
    source=rows([100]*125+[100,99,100,100]+[101]*11)
    for row in source:
        row[4:6]=[99,100] if row[2]<=129 else [100,101]
    return source


def replay(source,addition='A17',clear=True):
    state=State(branch_ids=[GROUP['additions'][addition]],session_anchor=source[0],offline=True)
    events=[]
    for row in source:
        ready=state.observe(row,symbol='000001',venue='NXT',session='NXT_PREMARKET')
        if ready:events.append(copy.deepcopy(ready[0]['event']))
        if clear:state.ready.clear()
    return state,events


def test_old_catalog_hash_and_definitions_survive():
    assert C.CUMULATIVE_SHA256=='2d94b2f9dbf86b722ad3fa06d87636b23dc8b80eb74aff484e5bcc5291c7d22f'
    R.validate_request(legacy_request(),check_sources=False)
    assert len(Q.PROGRESS['groups'])==48
    for sid,g in Q.PROGRESS['groups'].items():
        assert len(g['additions'])==20 and len(g['refinements'])==30
        for bid in Q.membership(sid,Q.PROGRESS['recommendations'][sid],Q.PROGRESS_RESULT):
            assert C.applicable(bid,*sid.rsplit('|',1))
    assert all(Q.DEFINITIONS[b]==d for b,d in Q.LEGACY_DEFINITIONS.items())


@pytest.mark.parametrize('change', ['none','quote','sequence','epoch','invalid','zero_spread'])
def test_incremental_features_match_independent_prefix(change):
    source=rows([100+i%4 for i in range(75)])
    if change=='quote':source[35][4]=None
    if change=='sequence':source[35][2]+=5
    if change=='epoch':source[35][1]+=5
    if change=='invalid':source[35][8]=0
    if change=='zero_spread':source[35][4]=source[35][5]
    window=ProgressWindow()
    for i,row in enumerate(source):
        f=window.observe(row)
        assert f==window.observe(row)
        start=i
        while start>0 and source[start-1][8] and source[start][8] and source[start-1][1]==source[start][1] and source[start-1][2]+1==source[start][2]:
            start-=1
        if row[8] and i-start>=9:
            assert f['return10_pct']==100*(row[3]/source[i-9][3]-1)
        else:assert f['return10_pct'] is None
        qstart=i
        good=lambda r:bool(r[8] and r[4] and r[5] and 0<r[4]<=r[5])
        while qstart>start and good(source[qstart-1]) and good(source[qstart]):qstart-=1
        if good(row) and i-qstart>=9:
            assert f['bid_return10_pct']==100*(row[4]/source[i-9][4]-1)
        else:assert f['bid_return10_pct'] is None
        anchors=[j for j in range(qstart,i+1) if source[j][0]<=row[0]-30]
        if good(row) and anchors:assert f['bid_return30_pct']==100*(row[4]/source[anchors[-1]][4]-1)
        else:assert f['bid_return30_pct'] is None


def test_quote_break_preserves_price_feature():
    source=rows([100]*40);source[35][4]=None
    w=ProgressWindow()
    for r in source:f=w.observe(r)
    assert f['return10_pct']==0 and f['range_spread10']==0
    assert f['bid_return10_pct'] is None and f['bid_return30_pct'] is None


@pytest.mark.parametrize('addition,sequence',[('A17',131),('A18',133)])
def test_bid_root_confirms_first_hold_and_builds_existing_auxiliary_input(addition,sequence):
    state,events=replay(fixture(),addition)
    assert len(events)==1
    e=events[0];signal=next(iter(e['branch_signals'].values()))
    assert signal['native_sequence']==sequence
    A.validate_signal(signal)
    assert signal['signal_proof']['turn_sequence']==128
    assert signal['signal_proof']['bid_at_root']==100
    from src.engine.scalping import reversal_extended_runtime as LIVE
    source=fixture()[:sequence];s=State(branch_ids=[GROUP['additions'][addition]],session_anchor=source[0],offline=True)
    for row in source:ready=s.observe(row,symbol='000001',venue='NXT',session='NXT_PREMARKET')
    event,inp=LIVE.snapshot(s,ready[0]);typed,prompt,_=U.production_request(inp,U.V1.ARMS[1],event=event)
    assert prompt.isascii() and len(typed['signals'])==1


@pytest.mark.parametrize('change',['no_advance','bid_fade','price_fade','quote_gap','epoch_gap','low_breach','expired'])
def test_bid_attempt_cannot_resurrect_after_failure(change):
    source=fixture()
    if change=='no_advance':
        for row in source:row[4:6]=[99,101]
    elif change=='bid_fade':source[130][4]=99
    elif change=='price_fade':source[130][3]=100
    elif change=='quote_gap':source[130][4]=None
    elif change=='epoch_gap':source[130][1]+=1
    elif change=='low_breach':source[128][3]=98
    else:
        for row in source[129:]:row[0]+=31
    _,events=replay(source,'A18')
    assert not events


def test_bid_hold_ready_is_removed_when_quote_fades_after_confirmation():
    source=fixture()[:131]
    state,events=replay(source,clear=False)
    assert events and state.ready
    row=fixture()[131];row[4]=99
    state.observe(row,symbol='000001',venue='NXT',session='NXT_PREMARKET')
    assert not state.ready


def test_confirmation_proof_rejects_bid_and_turn_tampering():
    _,events=replay(fixture());signal=next(iter(events[0]['branch_signals'].values()))
    for field,value in [('minimum_bid',99),('quote_contiguous',False),('turn_sequence',signal['native_sequence']),('bid_at_root',99)]:
        wrong=copy.deepcopy(signal);wrong['signal_proof'][field]=value
        with pytest.raises(ValueError):A.validate_signal(wrong)


def progress_request():
    d=Q.PROGRESS;batch=Q.PROGRESS_RESULT;r=legacy_request()
    r.update(research_batch_sha256=batch,registry_sha256=Q.registry(batch),variant_groups=R.groups(batch),
             definition_hashes={b:digest(v) for b,v in d['definitions'].items()})
    members={s:Q.membership(s,d['recommendations'][s],batch) for s in d['groups']}
    r.update(initial_memberships=members,scopes={s:dict(remove=sorted(set(g['baseline'])-set(members[s])),
            add=sorted(set(members[s])-set(g['baseline']))) for s,g in d['groups'].items()})
    r['source_receipts']=[dict(path='/fixture/'+name,name=name,sha256=sha) for name,sha in [
        ('result.json',batch),('manifest.json',d['research_manifest_sha256']),('validation.json','a'*64),
        ('native-parity.json','b'*64),('baseline-bundle.json','c'*64)]]
    return seal(r)


def test_new_registration_is_exact_batch_and_rejects_old_approval_relabeling():
    r=progress_request();R.validate_request(r,check_sources=False)
    wrong=legacy_request();wrong['research_batch_sha256']=Q.PROGRESS_RESULT
    with pytest.raises(ValueError):R.validate_request(seal(wrong),check_sources=False)
    wrong=copy.deepcopy(r);wrong['variant_groups'].pop(next(iter(wrong['variant_groups'])))
    with pytest.raises(ValueError):R.validate_request(seal(wrong),check_sources=False)


def test_cached_catalog_hashes_cannot_be_changed_by_prepared_request():
    original=R.definition_hashes(Q.PROGRESS_RESULT)
    altered=R.definition_hashes(Q.PROGRESS_RESULT);altered[next(iter(altered))]='0'*64
    assert R.definition_hashes(Q.PROGRESS_RESULT)==original
    r=progress_request();r['definition_hashes']=altered
    with pytest.raises(ValueError):R.validate_request(seal(r),check_sources=False)


def test_price_progress_filters_preserve_unknown_and_original_or_branch():
    sid='other_non_fixed|PRE|20000_TO_100000|NXT';g=Q.PROGRESS['groups'][sid]
    rule=Q.DEFINITIONS[next(iter(g['refinements']['F26'].values()))]['filters']
    assert Q.condition({},rule) is None
    assert Q.condition(dict(price_progress_spreads10=0),rule) is False
    ids=Q.membership(sid,'J:A09+F25@legacy_dd5_0_8_vol_up_v1',Q.PROGRESS_RESULT)
    assert 'legacy_dd5_0_8_vol_up_v1' not in ids
    assert set(g['baseline'])-{'legacy_dd5_0_8_vol_up_v1'}<=set(ids)
    assert Q.valid_membership(sid,ids,Q.PROGRESS_RESULT)


def test_new_manifest_cannot_or_a_filtered_original_back_in():
    r=progress_request()
    manifest=dict(scopes=copy.deepcopy(r['initial_memberships']),
                  definitions={b:C.definition(b) for ids in r['initial_memberships'].values() for b in ids},
                  cumulative_variant_groups=r['variant_groups'],cumulative_selection_authority=R.SELECTION_AUTHORITY,
                  registration_receipts=[r])
    assert R.validate_manifest(manifest)
    sid='034020|AFTER|20000_TO_100000|SOR'
    manifest['scopes'][sid]=sorted(set(manifest['scopes'][sid])|set(Q.PROGRESS['groups'][sid]['baseline']))
    with pytest.raises(ValueError,match='membership'):R.validate_manifest(manifest)


def test_extra_future_rows_do_not_change_confirmation_or_prefix_features():
    prefix=fixture()[:133]
    _,short=replay(prefix,'A18')
    suffix=rows([500,10,500,10])
    for i,row in enumerate(suffix,start=len(prefix)):
        row[0]=prefix[0][0]+i;row[2]=i+1
    _,long=replay(prefix+suffix,'A18')
    assert short==[e for e in long if e['native_sequence']<=len(prefix)]


@pytest.mark.parametrize('sid',list(Q.PROGRESS['groups']))
def test_registered_scope_has_the_frozen_route_without_cross_route_alias(sid):
    key,route=sid.rsplit('|',1);g=Q.PROGRESS['groups'][sid]
    for name in ('A17','A18','A19','A20'):
        bid=g['additions'][name]
        assert C.applicable(bid,key,route)
        for other in C.ROUTES[key.split('|')[1]]:
            if other!=route:assert not C.applicable(bid,key,other)


def test_new_initial_auxiliary_carry_keeps_all_128_scopes_and_provider_zero(tmp_path,monkeypatch):
    from src.engine.scalping import reversal_cumulative_postclose as CP
    from src.engine.scalping import reversal_auxiliary_intraday as I,reversal_auxiliary_registry as AR
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    from src.tests.test_reversal_cumulative_policy import postclose_fixture
    parent,manifest=postclose_fixture(monkeypatch);r=progress_request()
    manifest.update(cumulative_variant_groups=r['variant_groups'],registration_receipts=[r])
    manifest['scopes'].update(r['initial_memberships'])
    for sid,g in Q.PROGRESS['groups'].items():
        key,route=sid.rsplit('|',1)
        parent['continuous_reversal']['operating_manifest']['scopes'][sid]=g['baseline']
        parent['continuous_reversal']['machine_cells'][key]['routes'][route]['payload']=dict(
            composition='ANY_MATCH_ONE_INTENT',branches=[C.branch(b) for b in g['baseline']])
    original=copy.deepcopy(parent)
    ident=AR.register(tmp_path,AR.definition(U.V1.ARMS[1],input_version=U.VERSION))
    bindings={V.scope_id(k,route):ident for k,route in V.scopes()}
    monkeypatch.setattr(R,'_receipts',lambda *a,**kw:None)
    monkeypatch.setattr(I,'effective_bindings',lambda *a,**kw:bindings)
    monkeypatch.setattr(I,'current',lambda *a,**kw:{})
    monkeypatch.setattr(I,'lineage_sources',lambda *a:[])
    monkeypatch.setattr(I,'independent_scopes',lambda *a:set())
    machine=dict(registration_change=r,operating_manifest=manifest,source_receipts=[],execution_code_sha256='a'*64)
    out=CP.initial_reports(tmp_path,'2026-10-14','2026-10-15',parent,machine,publish_policy=False)
    assert len(out['auxiliary_registry_bindings'])==128 and out['actual_provider_calls']==0
    assert parent==original
    assert all(route['initial_binding']['research_batch_sha256']==Q.PROGRESS_RESULT
               for cell in out['cells'] for route in cell['routes'].values())


def test_new_intake_preserves_existing_pending_batch_on_conflict(tmp_path,monkeypatch):
    from src.engine.scalping import continuous_reversal_postclose as P
    from src.engine.scalping import continuous_reversal_policy_v6 as V
    r=progress_request();receipts=[]
    for item in r['source_receipts']:
        path=tmp_path/item['name'];path.write_text('{}')
        receipts.append(dict(item,path=str(path),sha256=P.file_hash(path)))
    prepared=P.seal(dict(r,schema=R.PREPARED,status='prepared_waiting_deployment',operator_receipt=None,
                        source_receipts=receipts,
                        contract_file_sha256={Path(m.__file__).name:P.file_hash(m.__file__) for m in V.contract_modules()}))
    path=tmp_path/'prepared.json';P.write(path,prepared);data=tmp_path/'private'
    P.write(R.N.root(data)/'current.json',dict(bundle_sha256=Q.PARENT))
    old=legacy_request();P.write(R.pending_path(data),old);before=R.pending_path(data).read_bytes()
    monkeypatch.setattr(R,'_receipts',lambda *a,**kw:None)
    monkeypatch.setattr(V,'_attested_activation_parent',lambda *a,**kw:dict(bundle_sha256=Q.PARENT))
    with pytest.raises(ValueError,match='pending_request_conflict'):
        R.intake(data,path,confirm=R.AUTHORITY,origin_root=tmp_path,origin_commit='a'*40)
    assert R.pending_path(data).read_bytes()==before
    assert R.N._read(R.N.root(data)/'current.json')==dict(bundle_sha256=Q.PARENT)


def _diagnostic_backend(monkeypatch, addition='A18', count=131):
    from types import SimpleNamespace
    from src.engine.scalping import reversal_source_diagnostics as D
    from src.engine.scalping import reversal_extended_runtime as E, reversal_current_backend as B
    from src.trading.market import session_contract
    from datetime import datetime
    source=fixture()[:count];bid=GROUP['additions'][addition]
    state=State(branch_ids=[bid],session_anchor=source[0],offline=True)
    for row in source:
        state.observe(row,symbol='000001',venue='NXT',session='NXT_PREMARKET')
        state.ready.clear()
    key=SCOPE.rsplit('|',1)[0];day=datetime.fromtimestamp(source[-1][0],D.K.KST).date().isoformat()
    family=dict(family_sha256='a'*64,machine_cells={key:dict(routes={'NXT':dict(
        scope_execution_hash=state.generation,backend='extended_v5',payload=dict(branches=[C.branch(bid)]))})},
        native_parent_bundle=dict(continuous_reversal=dict(family_sha256='b'*64)))
    monkeypatch.setattr(B,'backend',lambda:E)
    monkeypatch.setattr(E,'_FAMILY',family);monkeypatch.setattr(E,'_GENERATION','a'*64)
    monkeypatch.setattr(E,'_STATES',{('000001','NXT','000001_NX','PRE',day,key):state})
    monkeypatch.setattr(E.R,'_STATES',{})
    monkeypatch.setattr(session_contract,'resolve_market_session',lambda *a:SimpleNamespace(session_regime='NXT_PREMARKET'))
    candidate=SimpleNamespace(code='000001',route='nxt_only',discovery_price=source[-1][3])
    return D,state,source,bid,candidate


def test_native_diagnostics_keep_bid_hold_pending_and_do_not_consume(monkeypatch):
    from src.engine.scalping.zero_base_probe import native_wait_result
    D,state,source,bid,candidate=_diagnostic_backend(monkeypatch)
    assert state.cumulative.pending
    pending=copy.deepcopy(state.cumulative.pending);now=source[-1][0]+.1
    requirements=D.residence_requirements(candidate,now)
    readiness=D.branch_readiness(candidate,now=now,deadline=now+5,original_requirements=requirements)
    snapshot,receipt=D.observe_snapshot('000001','NXT','NXT_PREMARKET',now=now,
        item='000001_NX',family_sha256='a'*64)
    assert snapshot is None and receipt['selected_pending_count']>0
    assert native_wait_result(receipt,readiness)==('observation_incomplete','confirmation_pending_at_residence_end')
    assert readiness['branch_descriptors'][bid]['pending_confirmation_epoch'] is not None
    assert readiness['branch_descriptors'][bid]['hold_seconds']==3
    assert state.cumulative.pending==pending and not state.ready


def test_native_diagnostics_project_progress_features_and_stale_boundary(monkeypatch):
    D,state,source,bid,candidate=_diagnostic_backend(monkeypatch,'A19',120)
    now=source[-1][0]+.1;requirements=D.residence_requirements(candidate,now)
    readiness=D.branch_readiness(candidate,now=now,deadline=now+5,original_requirements=requirements)
    desc=readiness['branch_descriptors'][bid]
    expected=state.cumulative.progress.values
    assert 'bid_return10_pct' in desc['feature_fields']
    assert desc['minimum_trade_count']==10
    for name in set(expected)&set(desc['feature_fields']):
        assert desc['feature_values'][name]==expected[name]
        assert name not in desc['missing_inputs']
    stale=D.branch_readiness(candidate,now=now+4,deadline=now+5,original_requirements=requirements)
    assert 'continuous_source_interval' in stale['branch_descriptors'][bid]['missing_inputs']
    assert stale['branch_descriptors'][bid]['detector_truth']=='UNKNOWN'


@pytest.mark.parametrize('bad_quote', ['missing', 'crossed', 'stale'])
def test_native_readiness_discloses_unusable_quote_without_changing_detector(monkeypatch, bad_quote):
    D, state, source, bid, candidate = _diagnostic_backend(monkeypatch, 'A19', 120)
    row = list(source[-1]); row[0] += 1; row[2] += 1
    if bad_quote == 'missing': row[4] = None
    elif bad_quote == 'crossed': row[4], row[5] = 102, 101
    else: row[10] = 5001
    state.observe(row, symbol='000001', venue='NXT', session='NXT_PREMARKET')
    before = (dict(state.coverage_snapshot), copy.deepcopy(state.ready), copy.deepcopy(state.cumulative.pending))
    now = row[0] + .1
    readiness = D.branch_readiness(candidate, now=now, deadline=now+5)
    descriptor = readiness['branch_descriptors'][bid]
    assert descriptor['native_quote_usable'] is False
    assert descriptor['feature_availability'] == 'incomplete'
    assert 'executable_quote' in descriptor['missing_inputs']
    assert descriptor['detector_truth'] == 'UNKNOWN'
    assert before == (dict(state.coverage_snapshot), state.ready, state.cumulative.pending)


def test_cumulative_refinement_descriptor_keeps_original_requirements_optional():
    from src.engine.scalping import reversal_source_diagnostics as D
    original,next_id=next(iter(GROUP['refinements']['F29'].items()))
    base=D._branch_descriptor(C.PROGRESS_SHA256,original)
    refined=D._branch_descriptor(C.PROGRESS_SHA256,next_id)
    assert refined['minimum_seconds']==base['minimum_seconds']
    assert refined['feature_fields']==base['feature_fields']
    assert refined['optional_refinement_fields']
