"""Offline research: past-only joins, source gaps and honest denominators."""
from copy import deepcopy
import gzip
import json
from datetime import datetime, timedelta

import pytest

from src.engine.scalping import samsung_continuous_recovery_research as R


def raw(at='2026-10-02T09:00:00+09:00', admission='fixed-watch'):
    return dict(decision_ts=at,watch_admission_id=admission,setup_evidence={
        'strategy_raw_input': {'features': dict(tick_aggressor_pressure_usable=True,
            tick_context_stale=False,quote_stale=False,tick_aggressor_trusted_count=30,
            large_sell_print_detected=True,buy_pressure_10t=25.,net_aggressive_delta_10t=-500.,
            price_change_10t_pct=-.2,tick_acceleration_ratio=.9,same_price_buy_absorption=2)},
        'mechanistic_context': {'flow': {'source_quality': {'status':'fresh_consistent'},
            'execution_context': {'program_net_qty':100}}}})


def bars(lows):
    return [dict(day='2026-10-02',t=i*60,o=x+500,c=x+1000,h=x+2000,l=x,v=100,
        volume_known_at=i*60+60) for i,x in enumerate(lows)]


def streams():
    trades=[dict(t=float(i),ex=float(i),ep=7,seq=i+1,continuous=True,
        p=270000.,q=100,side='BUY',valid=True,flow_valid=True) for i in range(81)]
    depths=[dict(t=float(i),ep=7,seq=i+1,continuous=True,bid=270000.,ask=270500.,
        bq=100,aq=100,valid=True) for i in range(81)]
    return trades,depths


def exposure(t, outcome, *, episode=None, parent=None, recoverable=False, feature=True):
    return dict(t=t,day='2026-10-02',trace=str(t),episode=episode,parent=parent,
        recoverable=recoverable,native=None,features={'x':feature},
        label={'binary':outcome,'net':.1 if outcome==1 else None,
            'status':'target_first' if outcome==1 else 'neither'})


def test_adverse_values_are_restored_without_mutating_source_or_execution_guard():
    original=raw();saved=deepcopy(original)
    value=R.restore_features(original)
    assert value['raw:net_aggressive_delta_10t']==-500
    assert value['raw_quality'] and value['large_sell']
    assert original==saved
    original['setup_evidence']['strategy_raw_input']['features']['quote_stale']=True
    value=R.restore_features(original)
    assert not value['raw_quality'] and value['raw:buy_pressure_10t'] is None


def test_missing_or_cross_admission_does_not_produce_program_change():
    old=raw(admission=None);previous=dict(t=R.epoch(old['decision_ts']),identity=None,features=R.restore_features(old))
    new=raw('2026-10-02T09:01:00+09:00',None)
    assert R.restore_features(new,previous)['program_change'] is None
    previous['identity']='other'
    new['watch_admission_id']='current'
    assert R.restore_features(new,previous)['program_change'] is None


def test_pivot_is_confirmed_after_two_complete_bars_and_prefix_invariant():
    source=bars([270000,269500,268000,269000,269500,269000,268500,269500])
    full,events=R.episode_features(source)
    assert all(not r['features']['episode_active'] for r in full[:4])
    assert events[0]['at']==300 and events[0]['pivot_at']==120
    for end in range(1,len(source)+1):
        prefix,_=R.episode_features(source[:end])
        assert prefix==full[:end]


def test_gap_clears_episode_and_past_resistance_window():
    source=bars([270000,269500,268000,269000,269500,269000])
    source[-1]['t']+=600
    rows,_=R.episode_features(source)
    assert rows[4]['episode'] is not None
    assert rows[5]['episode'] is None and rows[5]['features']['range_location'] is None


def test_volume_asof_requires_entire_window_receipt():
    source=bars([270000]*8);source[2]['volume_known_at']=9999
    rows,_=R.episode_features(source)
    assert rows[5]['volume_known_at']==9999


def test_main_volume_uses_own_completed_capture_and_no_future_bar():
    item=raw('2026-10-02T09:06:10+09:00')
    start=datetime.fromisoformat('2026-10-02T09:00:00+09:00')
    source=[dict(dt=(start+timedelta(minutes=i)).isoformat(),o=101 if i<3 else 100,
        c=100 if i<3 else 101,v=100 if i<3 else 200,forming=False,partial_volume=False)
        for i in range(6)]
    context={'request_code':'005930_AL','strategy_completed_bars':{'body':{'bars':source}}}
    item['setup_evidence']['strategy_raw_input']['entry_candle_context']=context
    assert R.captured_volume_ratio(item)==2
    source.append(dict(source[-1],dt='2026-10-02T09:07:00+09:00',v=99999))
    assert R.captured_volume_ratio(item)==2
    context['request_code']='005930_NX'
    assert R.captured_volume_ratio(item) is None


def test_future_stream_data_does_not_change_past_features():
    trades,depths=streams()
    before=R.market_features(deepcopy(trades[:61]),deepcopy(depths[:61]),[60])[0]
    trades[-1].update(q=100000,p=300000,side='SELL')
    depths[-1].update(bid=300000,ask=300500)
    after=R.market_features(trades,depths,[60])[0]
    assert before==after and after['stream_valid'] and after['depth_valid']
    assert after['stream_source_max_at']<=60


@pytest.mark.parametrize('defect',['sequence','epoch','stale','flow_invalid'])
def test_stream_defects_are_not_imputed(defect):
    trades,depths=streams();trades=trades[:61]
    if defect=='sequence':trades[40]['continuous']=False
    if defect=='epoch':trades[40]['ep']=8
    if defect=='stale':trades=trades[:58]
    if defect=='flow_invalid':trades[40]['flow_valid']=False
    value=R.market_features(trades,depths,[60])[0]
    assert not value['stream_valid'] and value['buy_share10'] is None


def test_depth_other_epoch_and_future_quotes_cannot_satisfy_join():
    trades,depths=streams()
    for r in depths:r['ep']=8
    value=R.market_features(trades,depths,[60])[0]
    assert value['stream_valid'] and not value['depth_valid']
    assert not R.market_features(trades,[dict(depths[-1],ep=7)],[60])[0]['depth_valid']


def test_burst_threshold_uses_only_previous_trades_then_actual_recovery():
    trades,depths=streams()
    trades[50].update(side='SELL',q=1000,p=269000.)
    trades[51].update(p=269500.)
    result=R.market_features(trades,depths,[49,50,51])
    assert result[0]['burst_recovery_ticks'] is None
    assert result[1]['burst_recovery_ticks'] is None
    assert result[2]['burst_recovery_ticks']==1


def test_price_labels_cost_ambiguity_gap_and_neither():
    source=[dict(t=i*60,h=100.2,l=99.9,c=100.) for i in range(10)]
    result=R.price_label(source,0,100,.33)
    assert result['binary'] is None and result['status']=='neither'
    assert result['net']==pytest.approx(-.33)
    source[2]['h']=100.5
    assert R.price_label(source,0,100,.33)['binary']==1
    assert R.price_label(source[:3],0,100,.33)['binary']==1
    source[2]['l']=99.
    assert R.price_label(source,0,100,.33)['status']=='same_bar_ambiguous'
    assert R.price_label(source[1:],0,100,.33)['status']=='price_coverage_gap'


def test_missing_outcome_reserves_episode_and_overlap_instead_of_cherry_pick():
    rows=[exposure(0,None,episode='a'),exposure(60,1,episode='a'),
        exposure(500,1,episode='b'),exposure(600,1,episode='b')]
    result=R.summary(rows,[True]*4)
    assert result['traces']==['0','600'] and result['win_rate']==1
    assert result['coverage']==.5 and result['native_groups']==0


def test_recovery_cannot_override_other_guards_and_filter_may_drop_winner():
    rows=[exposure(0,1,parent='ENTER_NOW',feature=False),
        exposure(600,0,parent='BLOCK',feature=True),
        exposure(1200,1,parent='RECHECK',recoverable=True,feature=True)]
    rule={'conditions':[('x','is',True)]}
    assert R.actions(rows,rule,'filter')==[False,False,False]
    assert R.actions(rows,rule,'recover')==[True,False,True]


def test_fit_is_training_only_and_has_no_success_retention_veto():
    rows=[exposure(i*600,1,parent='ENTER_NOW',feature=i>0) for i in range(4)]
    candidate={'id':'drops_one_success','conditions':[('x','is',True)]}
    fitted=R.fit(rows,[candidate],'filter')
    assert fitted['rule']==candidate and fitted['train']['wins']==3
    held=[exposure(0,0,feature=True)]
    R.summary(held,R.actions(held,candidate,'market'))
    assert R.fit(rows,[candidate],'filter')==fitted


def test_rule_grammar_keeps_only_strongest_duplicate_bound():
    rows=[dict(features={'past_up':True,'range_location':.3,'drawdown_pct':-.5})]*3
    rules=R.definitions(rows,'price')
    for rule in rules:
        keys=[(k,op) for k,op,v in rule['conditions']]
        assert len(keys)==len(set(keys))


@pytest.mark.parametrize('compressed',[False,True])
def test_stream_loader_excludes_wrong_schema_route_and_marks_sequence_gap(tmp_path,compressed):
    base=tmp_path/'data/observations/scalp_micro_reversion_forward/trade_date=2026-10-02/venue=SOR/session=SOR_REGULAR'
    base.mkdir(parents=True)
    row=dict(symbol='005930',schema='scalp_micro_reversion_market_stream_point_v3',source_item='005930_AL',
        venue='SOR',session_bucket='SOR_REGULAR',sequence_epoch=1,series_sequence=1,
        local_receive_timestamp='2026-10-02T09:00:01.100+09:00',exchange_timestamp='2026-10-02T09:00:01+09:00',
        trade_price=270000,trade_qty=10,aggressor_side='BUY',path_consumer_eligible=True,path_order_status='accept')
    lines=[row,dict(row,source_item='005930_NX'),dict(row,schema='unknown'),dict(row,series_sequence=3)]
    content='\n'.join(json.dumps(x) for x in lines)+'\n'
    name='market_stream.jsonl.gz' if compressed else 'market_stream.jsonl'
    if compressed:
        with gzip.open(base/name,'wt') as out:out.write(content)
    else:(base/name).write_text(content)
    (base/'market_stream.manifest.json').write_text(json.dumps({'shards':[{'file':name}]}))
    output,census=R.stream_rows(tmp_path,'2026-10-02','trade',{})
    assert len(output)==2 and not output[1]['continuous']
    assert census['issues']=={'route_mismatch':1,'schema_mismatch':1,'sequence_or_receive_discontinuity':1}
