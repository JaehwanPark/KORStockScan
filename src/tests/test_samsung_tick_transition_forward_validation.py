from copy import deepcopy
from datetime import datetime, timedelta
import json
from pathlib import Path

import pytest

from src.engine.scalping import samsung_tick_transition_forward_validation as V
from src.tests.test_entry_strategy_policy import raw as raw_fixture, setup, policy
from src.tests.test_entry_admission_analysis import row_and_prices


def registered(tmp_path):
    evidence=tmp_path/'discovery.json';evidence.write_text('{}')
    base=tmp_path/'samsung-frozen.json';V.A.write(base,V.A.freeze(policy(),[evidence]))
    frozen=tmp_path/'frozen-candidate.json'
    V.A.write(frozen,dict(**V.C.AUTHORITY,result=dict(candidate_id=V.CANDIDATE,rule=V.RULE,
        base_action='absorption_p60_v10',later_source_after_date='2026-10-05',recommendation_scope='all_origins',
        source_seals={str(base):V.H.file_sha(base)},evidence={evidence.name:V.H.file_sha(evidence)})))
    return V.registration(tmp_path,frozen)


def capture(day='2026-10-06'):
    row,bars=row_and_prices()
    start=datetime.fromisoformat(day+'T09:10:00+09:00').timestamp()
    payload=raw_fixture();payload.update(stock_code='005930',session_bucket='krx_regular',entry_machine_input_as_of=start,
        quote=dict(best_bid=99.,best_ask=100.))
    payload['current'].update(price=100,fluctuation_pct=1)
    payload['features'].update(curr_vs_micro_vwap_bp=-5,curr_vs_ma5_bp=0,micro_vwap_available=True,
        buy_pressure_10t=100.,net_aggressive_delta_10t=29,price_change_10t_pct=0.,tick_aggressor_trusted_count=10)
    payload['entry_candle_context'].update(request_code='005930_AL',ws_route='krx_nxt_integrated')
    evidence=setup(payload)
    row.update(source_date=day,decision_ts=day+'T09:10:00+09:00',stock_code='005930',outcome_request_code='005930_AL',
        bundle_sha256='b'*64,setup_evidence=evidence,source_provenance_verified=True,machine_observation_hash_verified=True)
    row['comparison']['entry_cost_contract']['source_date']=day
    row['machine_action']=V.F.E.mechanistic_entry_policy_decision(evidence,policy=policy())['action']
    ticks=[dict(t=start-2+i*.05,ex=start-2,ep=101,seq=i+1,continuous=True,p=100.,
        q=20 if i<10 or i==19 else 1,side='SELL' if i<10 else 'BUY',valid=True,flow_valid=True) for i in range(20)]
    bars=[dict(b,t=start+(i+1)*60) for i,b in enumerate(bars)]
    return row,ticks,bars


def test_registration_waiting_without_rewriting_original_or_calling_sources(tmp_path):
    contract=registered(tmp_path);original=Path(contract['frozen_path']).read_bytes()
    result=V.prepare(tmp_path,'2026-10-06',contract,tmp_path/'result')
    assert result['status']=='waiting_new_source_date'
    assert set(result['missing_source_paths'])=={'capture','prices','trades'}
    assert result['observations']==[] and result['comparisons'] is None
    assert not result['runtime_effect'] and not result['candidate_reselection'] and not result['data_collected']
    assert Path(contract['frozen_path']).read_bytes()==original


@pytest.mark.parametrize('day',['2026-10-05','2026-10-02','20261006','invalid'])
def test_discovery_dates_and_invalid_dates_are_rejected(tmp_path,day):
    with pytest.raises(ValueError):V.prepare(tmp_path,day,registered(tmp_path),tmp_path/'out')


@pytest.mark.parametrize('field,value',[('candidate_id','other'),('later_source_after_date','2026-10-02'),
    ('rule',dict(V.RULE,offset=10)),('runtime_effect',True),('source_contract','unsealed')])
def test_consumer_contract_is_pinned(tmp_path,field,value):
    contract=registered(tmp_path);contract[field]=value;contract=V.A.seal(contract)
    with pytest.raises(ValueError,match='consumer_contract_changed'):
        V.validate_registration(tmp_path,contract)


def test_changed_original_frozen_and_evidence_are_rejected(tmp_path):
    contract=registered(tmp_path);p=Path(contract['frozen_path']);frozen=V.read(p)
    frozen['result']['rule']['pressure_boundary']=50
    p.write_text(json.dumps(V.A.seal(frozen)))
    with pytest.raises(ValueError):V.validate_registration(tmp_path,contract)


def test_feature_clock_fallback_preserves_original_priority_and_unknown():
    row,ticks,_=capture();raw=row['setup_evidence']['strategy_raw_input']
    old_clock=ticks[-1]['t'];extra=dict(ticks[-1],t=old_clock+.1,seq=21,q=999,side='SELL')
    raw['entry_machine_input_trace']={'entry_machine_input_quote_clock_comparison':{'feature_receipt':{
        'observed_epoch':old_clock,'item':'005930_AL','market_route':'krx_nxt_integrated'}}}
    proof,owner=V.current_receipt(raw,ticks+[extra],[r['t'] for r in ticks+[extra]],'a'*64)
    assert owner=='machine_refresh_clock' and V.F.valid_receipt(raw,proof)
    assert proof['window_cutoff']==old_clock
    raw['entry_machine_input_trace']['entry_machine_input_quote_clock_comparison']['feature_receipt']['observed_epoch']=raw['entry_machine_input_as_of']+1
    proof,owner=V.current_receipt(raw,ticks+[extra],[r['t'] for r in ticks+[extra]],'a'*64)
    assert owner=='source_clock_missing' and not V.F.valid_receipt(raw,proof)


@pytest.mark.parametrize('field,value',[('item','000660_AL'),('item',None),('market_route','nxt_only'),('market_route',None)])
def test_foreign_or_unproven_fallback_clock_cannot_bind_samsung_ticks(field,value):
    row,ticks,_=capture();raw=row['setup_evidence']['strategy_raw_input']
    extra=dict(ticks[-1],t=ticks[-1]['t']+.1,seq=21,q=999,side='SELL')
    receipt=dict(observed_epoch=ticks[-1]['t'],item='005930_AL',market_route='krx_nxt_integrated')
    receipt[field]=value
    raw['entry_machine_input_trace']={'entry_machine_input_quote_clock_comparison':{'feature_receipt':receipt}}
    proof,owner=V.current_receipt(raw,ticks+[extra],[r['t'] for r in ticks+[extra]],'a'*64)
    assert owner=='source_clock_missing' and not V.F.valid_receipt(raw,proof)


def test_source_guards_clock_and_unknown_have_no_label_selection():
    row,ticks,bars=capture();before=deepcopy(row)
    prices={(row['source_date'],'005930','KRX','KRX_REGULAR','005930_AL'):bars}
    validate=lambda r:None
    rows,excluded=V.evaluate_captures([row],ticks,'a'*64,prices,policy(),validate_source=validate)
    assert not excluded and row==before
    assert rows[0]['tick_conditions'][V.CANDIDATE]['condition'] is True
    assert rows[0]['path']['status']=='timeout'
    assert rows[0]['path']['net_pct']==pytest.approx(-.3)
    bars[19]['high']=101.
    changed,_=V.evaluate_captures([row],ticks,'a'*64,prices,policy(),validate_source=validate)
    assert changed[0]['path']['status']=='target'
    for field in ('parent_action','absorption_action','candidate_action','tick_conditions','current_receipt'):
        assert rows[0][field]==changed[0][field]
    ticks=ticks[-10:]
    unknown,_=V.evaluate_captures([row],ticks,'a'*64,prices,policy(),validate_source=validate)
    assert unknown[0]['tick_conditions'][V.CANDIDATE]['reason']=='prior_ticks_missing'
    assert unknown[0]['candidate_action']==unknown[0]['absorption_action']


def test_original_parent_replay_and_raw_changes_fail(tmp_path):
    row,ticks,bars=capture();row['machine_action']='not_the_parent_action'
    with pytest.raises(ValueError,match='parent_replay_changed'):
        V.evaluate_captures([row],ticks,'a'*64,{},policy(),validate_source=lambda r:None)
    row,ticks,bars=capture();row['setup_evidence']['strategy_raw_input']['features']['buy_pressure_10t']=1
    rows,excluded=V.evaluate_captures([row],ticks,'a'*64,{},policy(),validate_source=lambda r:None)
    assert not rows and excluded[0]['reason']=='original_scope_or_raw_invalid'


def test_invalid_rows_are_isolated_duplicates_are_not_counted():
    row,ticks,bars=capture()
    with pytest.raises(ValueError,match='duplicate_or_missing_trace'):
        V.evaluate_captures([row,row],ticks,'a'*64,{},policy(),validate_source=lambda r:None)
    def broken(row):raise ValueError('invalid_source')
    rows,excluded=V.evaluate_captures([row],ticks,'a'*64,{},policy(),validate_source=broken)
    assert not rows and excluded[0]['reason']=='invalid_source'


def test_report_has_only_frozen_candidate_and_three_controls():
    row,ticks,bars=capture()
    rows,_=V.evaluate_captures([row],ticks,'a'*64,{},policy(),validate_source=lambda r:None)
    report=V.summarize(rows)
    assert set(report['all_origins']['arms'])=={'baseline','absorption','H2',V.CANDIDATE}
    assert report['all_origins']['comparisons']['absorption']['positive_path_rate_pct']['status']=='not_identifiable'
    assert report['fixed_watch']['observations']==0


def local_sources(tmp_path,row,ticks):
    paths=V.source_paths(tmp_path,row['source_date'])
    for p in paths.values():p.parent.mkdir(parents=True,exist_ok=True)
    paths['capture'].write_text(json.dumps({'rows':[row]}));paths['prices'].write_text('{}')
    shard=paths['trades'].parent/'market_stream.jsonl'
    records=[]
    tz=datetime.fromisoformat(row['decision_ts']).tzinfo
    for tick in ticks:
        records.append(dict(schema='scalp_micro_reversion_market_stream_point_v3',symbol='005930',source_item='005930_AL',
            venue='SOR',session_bucket='SOR_REGULAR',sequence_epoch=tick['ep'],series_sequence=tick['seq'],
            local_receive_timestamp=datetime.fromtimestamp(tick['t'],tz).isoformat(),
            exchange_timestamp=datetime.fromtimestamp(tick['ex'],tz).isoformat(),
            path_consumer_eligible=True,path_order_status='accept',trade_price=tick['p'],trade_qty=tick['q'],aggressor_side=tick['side']))
    shard.write_text(''.join(json.dumps(r)+'\n' for r in records))
    paths['trades'].write_text(json.dumps({'shards':[{'file':shard.name}]}))
    generation=tmp_path/'data/runtime/mechanistic_entry_policy/generations'/('b'*64+'.json')
    generation.parent.mkdir(parents=True);generation.write_text('{}')
    return paths


def test_full_normalized_source_intake_and_empty_excluded_states(tmp_path,monkeypatch):
    contract=registered(tmp_path);row,ticks,bars=capture()
    assert V.Q._machine_source_contract_valid(row)
    paths=local_sources(tmp_path,row,ticks)
    # Bundle loader is separately tested with real sealed policy migrations.
    monkeypatch.setattr(V.K,'source_bundle',lambda *a: {})
    monkeypatch.setattr(V.H,'price_index',lambda *a: ({('2026-10-06','005930','KRX','KRX_REGULAR','005930_AL'):bars},[],[]))
    result=V.prepare(tmp_path,'2026-10-06',contract,tmp_path/'observed')
    assert result['status']=='evaluated' and result['source_quality']['condition_identifiable']==1
    assert result['observations'][0]['path']['net_pct']==pytest.approx(-.3)
    paths['capture'].write_text(json.dumps({'rows':[]}))
    assert V.prepare(tmp_path,'2026-10-06',contract,tmp_path/'empty')['status']=='valid_empty'
    row['source_provenance_verified']=False
    paths['capture'].write_text(json.dumps({'rows':[row]}))
    assert V.prepare(tmp_path,'2026-10-06',contract,tmp_path/'excluded')['status']=='source_quality_excluded_all'


def test_changed_source_during_price_read_is_rejected(tmp_path,monkeypatch):
    contract=registered(tmp_path);row,ticks,bars=capture();paths=local_sources(tmp_path,row,ticks)
    monkeypatch.setattr(V.K,'source_bundle',lambda *a: {})
    def changed(*args):
        paths['capture'].write_text(json.dumps({'rows':[]}))
        return {},[],[]
    monkeypatch.setattr(V.H,'price_index',changed)
    with pytest.raises(ValueError,match='source_changed'):
        V.prepare(tmp_path,'2026-10-06',contract,tmp_path/'changed')
