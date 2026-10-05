from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from src.engine.scalping import samsung_continuous_tick_transition_research as C
from src.engine.scalping import entry_flat_buy_flow_research as F


def source():
    raw = dict(stock_code='005930', effective_venue='KRX', session_bucket='KRX_REGULAR',
        entry_machine_input_as_of=100., entry_candle_context=dict(request_code='005930_AL',ws_route='krx_nxt_integrated'),
        features=dict(buy_pressure_10t=100., net_aggressive_delta_10t=29., price_change_10t_pct=0.))
    ticks = [dict(t=98+i*.05,ex=98.,ep=1,seq=i+1,continuous=True,p=100.,
        q=20 if i<10 or i==19 else 1,side='SELL' if i<10 else 'BUY',valid=True,flow_valid=True) for i in range(20)]
    proof = F.historical_receipt(raw,ticks[-10:],archive_sha256='a'*64,window_cutoff=100.)
    assert F.valid_receipt(raw,proof)
    return raw,proof,ticks


def calculate(raw,proof,ticks,offset=1):
    return C.transition(raw,proof,ticks,C.archive_index(ticks),'a'*64,offset)


@pytest.mark.parametrize('offset',[1,10])
def test_exact_windows_and_pressure_rounding(offset):
    raw,proof,ticks=source(); result=calculate(raw,proof,ticks,offset)
    assert result['condition'] is True
    assert result['previous_pressure']==(31.03 if offset==1 else 0.)
    assert result['archive_index_range']==[10-offset,20]
    assert result['source_epoch_domain']=='independent_archive_collector'
    assert result['main_epoch_equivalence'] is False


@pytest.mark.parametrize('offset',[1,10])
def test_minimum_ticks_and_current_window_exactness(offset):
    raw,proof,ticks=source()
    truncated=ticks[-(9+offset):]
    assert calculate(raw,proof,truncated,offset)['reason']=='prior_ticks_missing'
    changed=deepcopy(ticks); changed[-1]['q']+=1
    assert calculate(raw,proof,changed,offset)['reason']=='current_window_not_exact'


@pytest.mark.parametrize('change,reason',[
    ({'seq':99},'epoch_or_sequence_gap'),({'ep':2},'epoch_or_sequence_gap'),
    ({'continuous':False},'epoch_or_sequence_gap'),
    ({'q':-1},'quantity_or_side_invalid'),({'q':0},'quantity_or_side_invalid'),
    ({'q':True},'quantity_or_side_invalid'),({'q':float('inf')},'quantity_or_side_invalid'),
    ({'p':0},'quantity_or_side_invalid'),({'side':'UNKNOWN'},'quantity_or_side_invalid'),
    ({'flow_valid':False},'quantity_or_side_invalid'),({'valid':False},'quantity_or_side_invalid'),
    ({'t':101},'clock_unproven'),({'ex':101},'clock_unproven'),({'ex':90},'clock_unproven'),
    ({'ex':None},'clock_unproven'),({'t':98.9},'epoch_or_sequence_gap'),
])
def test_invalid_prior_tick_remains_unknown(change,reason):
    raw,proof,ticks=source(); ticks[9].update(change)
    assert calculate(raw,proof,ticks)['reason']==reason


def test_duplicate_identity_and_epoch_crossing_are_not_merged():
    raw,proof,ticks=source()
    ticks.insert(0,deepcopy(ticks[9]))
    assert calculate(raw,proof,ticks)['condition'] is None
    raw,proof,ticks=source(); ticks[9]['ep']=2
    assert calculate(raw,proof,ticks)['reason']=='epoch_or_sequence_gap'


@pytest.mark.parametrize('field,value',[('stock_code','000000'),('effective_venue','NXT'),('session_bucket','NXT_REGULAR_OVERLAP')])
def test_scope_and_route_remain_bound(field,value):
    raw,proof,ticks=source();raw[field]=value
    assert calculate(raw,proof,ticks)['reason']=='current_receipt_invalid'


def test_route_receipt_hash_and_nonregistered_offset():
    raw,proof,ticks=source(); proof['archive_sha256']='b'*64
    assert calculate(raw,proof,ticks)['condition'] is None
    raw,proof,ticks=source(); raw['entry_candle_context']['request_code']='005930_NX'
    assert calculate(raw,proof,ticks)['condition'] is None
    with pytest.raises(ValueError,match='unregistered'):
        calculate(raw,proof,ticks,2)


def test_historical_lowercase_session_matches_absorption_scope_without_raw_mutation():
    raw,proof,ticks=source()
    raw['session_bucket']='krx_regular'
    proof=F.historical_receipt(raw,ticks[-10:],archive_sha256='a'*64,window_cutoff=100.)
    before=deepcopy(raw)
    assert calculate(raw,proof,ticks)['condition'] is True
    assert raw==before and proof['payload_sha256']==C.S.digest(raw)


def test_stale_prior_endpoint_and_long_window_start_are_distinct():
    raw,proof,ticks=source()
    for i in range(10): ticks[i].update(t=94+i*.01,ex=94.)
    assert calculate(raw,proof,ticks,10)['reason']=='prior_endpoint_stale'
    ticks[0].update(t=90.,ex=90.)
    for i in range(1,10): ticks[i].update(t=95+i*.01,ex=95.)
    result=calculate(raw,proof,ticks,10)
    assert result['condition'] is True and result['oldest_tick_age_sec']==10


def test_equal_receive_times_use_sequence_and_future_prefix_invariance():
    raw,proof,ticks=source()
    for tick in ticks:tick.update(t=99.,ex=99.)
    proof=F.historical_receipt(raw,ticks[-10:],archive_sha256='a'*64,window_cutoff=100.)
    expected=calculate(raw,proof,ticks)
    future=deepcopy(ticks[-1]);future.update(seq=21,t=101.,ex=101.)
    assert calculate(raw,proof,ticks+[future])==expected
    assert expected['condition'] is True


@pytest.mark.parametrize('parent',['BLOCK','RECHECK','ENTER_NOW'])
@pytest.mark.parametrize('condition',[None,True,False])
def test_action_uses_no_labels_and_preserves_nonenter(parent,condition):
    row=dict(absorption_action=parent,tick_conditions={C.IDS[0]:dict(condition=condition)})
    expected='RECHECK' if parent=='ENTER_NOW' and condition is False else parent
    assert C.action(row,C.IDS[0])==expected
    assert C.action(dict(row,path=dict(status='target',net_pct=100)),C.IDS[0])==expected


def observation(day,index,*,path=None,native=None):
    return dict(trace=f'{day}:{index}',ts=(datetime.fromisoformat(day+'T09:00:00+09:00')+timedelta(minutes=index)).isoformat(),
        day=day,symbol='005930',group='samsung',source_bundle_sha256='s',outcome_request_code='005930_AL',
        parent_action='ENTER_NOW',absorption_action='ENTER_NOW',candidate_action='ENTER_NOW',
        archive_epoch=1,native_provenance=native,source_lane='capture',conditions={'H2':None},
        tick_conditions={k:dict(condition=None,reason='current_receipt_invalid') for k in C.IDS},
        path=path or dict(status='stop',delay_sec=60,net_pct=-1.))


def test_watch_event_boundaries_and_missing_path_occupancy():
    day='2026-10-02'
    native=lambda watch:[day,'005930','KRX','KRX_REGULAR','MAIN_FIXED_WATCH',watch,'epoch']
    first=observation(day,0,path=dict(status='same_bar_ambiguous',net_pct=None),native=native('watch1'))
    next_row=observation(day,2,native=native('watch2'))
    assert C.event_key(first)!=C.event_key(next_row)
    results=C.compare([first,next_row])['fixed_watch']
    assert results['absorption']['selected_ids']==[first['trace']]
    assert results['absorption']['complete_path_count']==0
    assert C.recommend(C.compare([first,next_row]),[first,next_row])['status']=='not_identifiable'


def test_unknown_is_included_and_no_success_retention_veto():
    rows=[]
    for day in C.DAYS:
        # Separate observed runs. Filter one win and two losses; retain two wins.
        for i,status in enumerate(['target','stop','stop','target','target']):
            r=observation(day,i*3,path=dict(status=status,delay_sec=60,net_pct=.1 if status=='target' else -1))
            r['archive_epoch']=i+1
            r['tick_conditions']={k:dict(condition=i>=3,reason='observed') for k in C.IDS}
            rows.append(r)
    recommendation=C.recommend(C.compare(rows),rows)
    assert recommendation['recommended_candidate']==C.IDS[0]
    assert recommendation['scopes']['all_origins']['hypotheses'][C.IDS[0]]['positive_path_uplift_pp']==40


def test_source_changed_is_rejected(tmp_path):
    path=tmp_path/'original';path.write_text('exact')
    seals={str(path):C.H.file_sha(path)};C.verify_seals(seals)
    path.write_text('changed')
    with pytest.raises(ValueError,match='source_changed'):C.verify_seals(seals)


def test_abstention_date_does_not_require_preserving_baseline_entries():
    rows=[]
    for day in C.DAYS:
        for i,status in enumerate(['stop','target','target']):
            row=observation(day,i*3,path=dict(status=status,delay_sec=60,net_pct=.1 if status=='target' else -1))
            row['archive_epoch']=i+1
            row['tick_conditions']={k:dict(condition=(day!=C.DAYS[1] and i>0),reason='observed') for k in C.IDS}
            rows.append(row)
    result=C.recommend(C.compare(rows),rows)
    details=result['scopes']['all_origins']['hypotheses'][C.IDS[0]]
    assert details['comparable_dates']==[C.DAYS[0],C.DAYS[2]]
    assert details['candidate_abstention_dates']==[C.DAYS[1]]
    assert details['common_complete_counts'][C.IDS[0]]==4
    assert result['recommended_candidate']==C.IDS[0]
    # With only one comparable day the predeclared two-date floor still applies.
    smaller=[r for r in rows if r['day']!=C.DAYS[2]]
    assert C.recommend(C.compare(smaller),smaller)['status']=='insufficient_support'
