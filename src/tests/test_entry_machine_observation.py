"""Local-only source selection, receipt and report-recipe safety regressions."""
from copy import deepcopy
from datetime import datetime, timezone
from types import SimpleNamespace
import pytest

from src.engine.scalping import entry_machine_observation as O
from src.engine.scalping import entry_flat_buy_flow_research as F
from src.engine.scalping_feature_packet import extract_scalping_feature_packet as build_scalping_feature_packet

NOW=1790913562.0
KEY='_AL|krx_nxt_integrated'


def fixture():
    orderbook=dict(asks=[dict(price=275500,volume=500)]*3,bids=[dict(price=275500,volume=500)]*3)
    common=dict(item='005930_AL',market_route='krx_nxt_integrated',market_suffix='_AL',
                transport_epoch=1,observed_epoch=NOW-.1,effective_venue='KRX_NXT_INTEGRATED')
    ticks=[dict(item='005930_AL',market_route='krx_nxt_integrated',transport_epoch=1,
        received_at_ms=int((NOW-.1-i*.1)*1000),route_sequence=30-i,
        time=datetime.fromtimestamp(NOW-.1-i*.1).strftime('%H%M%S'),
        price=275500,volume=10,volume_source='15_abs',aggressor_side='BUY',
        aggressor_source='kiwoom_0b_signed_trade_volume',aggressor_quality='signed_trade_volume_positive') for i in range(10)]
    ws=dict(curr=275500,orderbook=orderbook,market_data_transport_epoch=1,last_ws_update_ts=NOW-.1,
        realtime_type_snapshots_by_route={KEY:{'0B':dict(common,current_price=275500),
            '0D':dict(common,orderbook=orderbook,ask_total=1500,bid_total=1500)}},
        recent_trade_ticks_by_route={KEY:ticks})
    context=dict(ws_suffix='_AL',ws_route='krx_nxt_integrated',ai_market_snapshot_v1=dict(
        stock_code='005930',effective_venue='KRX',session_bucket='KRX_REGULAR',
        sources={k:dict(freshness_limit_ms=3000) for k in ('current_price','bbo','tape')}))
    return ws,context


def select(ws,context):
    return O.select_local_observation(dict(market_data_transport_epoch=1,last_ws_update_ts=NOW-2),
        ws,context,now=NOW,max_age_ms=3000)


def test_locked_observation_is_exact_and_does_not_relabel_execution():
    ws,c=fixture();before=deepcopy((ws,c));result,receipt=select(ws,c)
    assert receipt['quote_state']=='locked' and receipt['executable_quote_verified'] is False
    assert result['entry_machine_exact_tick_source']==KEY
    assert result['recent_trade_ticks']==ws['recent_trade_ticks_by_route'][KEY]
    assert (ws,c)==before


def test_short_tape_remains_short_not_backfilled_or_global_ten_tick_veto():
    ws,c=fixture();ws['recent_trade_ticks_by_route'][KEY]=ws['recent_trade_ticks_by_route'][KEY][:3]
    selected,_=select(ws,c)
    assert len(selected['recent_trade_ticks'])==3
    packet=dict(_feature_tick_diagnostic_window=selected['recent_trade_ticks'])
    assert O.build_receipt(selected,packet,{},cutoff=NOW)['usable'] is False


def test_newer_aggregate_clock_does_not_override_selected_route_clock():
    ws,c=fixture();ws['last_ws_update_ts']=NOW-.01
    selected,_=O.select_local_observation(ws,ws,c,now=NOW,max_age_ms=3000)
    assert selected['last_ws_update_ts']==NOW-.1


@pytest.mark.parametrize('damage',['scope','epoch','bool_epoch','future','stale','route','symbol','crossed','tick_future','tick_epoch','missing_route'])
def test_bad_source_is_not_recovered_by_observation_exception(damage):
    ws,c=fixture()
    if damage=='scope':c['ai_market_snapshot_v1']['stock_code']='000660'
    elif damage=='epoch':ws['market_data_transport_epoch']=2
    elif damage=='bool_epoch':ws['market_data_transport_epoch']=True
    elif damage=='future':ws['realtime_type_snapshots_by_route'][KEY]['0B']['observed_epoch']=NOW+1
    elif damage=='stale':ws['realtime_type_snapshots_by_route'][KEY]['0D']['observed_epoch']=NOW-5
    elif damage=='route':ws['realtime_type_snapshots_by_route'][KEY]['0B']['market_route']='krx_only'
    elif damage=='symbol':ws['realtime_type_snapshots_by_route'][KEY]['0D']['item']='000660_AL'
    elif damage=='crossed':ws['orderbook']['asks'][0]['price']=275000
    elif damage=='tick_future':ws['recent_trade_ticks_by_route'][KEY][0]['received_at_ms']=(NOW+1)*1000
    elif damage=='tick_epoch':ws['recent_trade_ticks_by_route'][KEY][0]['transport_epoch']=2
    elif damage=='missing_route':ws['realtime_type_snapshots_by_route']={}
    with pytest.raises(ValueError):select(ws,c)


def test_receipt_binds_actual_window_and_no_future_result():
    ws,c=fixture();selected,_=select(ws,c)
    ticks=selected['recent_trade_ticks']
    packet=dict(_feature_tick_diagnostic_window=ticks,feature_tick_source='ws_exact_route',
        tick_aggressor_pressure_usable=True,tick_aggressor_trusted_count=10,
        buy_pressure_10t=100,net_aggressive_delta_10t=100,price_change_10t_pct=0)
    raw=dict(stock_code='005930',effective_venue='KRX',session_bucket='KRX_REGULAR',entry_machine_input_as_of=NOW,
        features={k:packet.get(k) for k in ('buy_pressure_10t','net_aggressive_delta_10t','price_change_10t_pct',
            'curr_vs_micro_vwap_bp','micro_vwap_available')})
    receipt=O.build_receipt(selected,packet,raw,cutoff=NOW)
    assert F.valid_receipt(raw,receipt)
    assert not F.valid_receipt(dict(raw,stock_code='000660'),receipt)
    broken=deepcopy(receipt);broken['window'][0]['received_at_ms']=(NOW+1)*1000
    broken['window_sha256']=O.digest(broken['window']);broken['receipt_sha256']=O.digest({k:v for k,v in broken.items() if k!='receipt_sha256'})
    assert not F.valid_receipt(raw,broken)


def test_feature_producer_receipt_same_window_for_runtime_and_replay():
    ws,c=fixture();selected,_=select(ws,c)
    now=datetime.fromtimestamp(NOW,timezone.utc)
    live=build_scalping_feature_packet(selected,[],[],now=now)
    replay=build_scalping_feature_packet(deepcopy(selected),[],[],now=now)
    # The producer intentionally issues a fresh diagnostic context ID.
    assert {k:v for k,v in live.items() if k!='microstructure_reaction_context_id'} == {
        k:v for k,v in replay.items() if k!='microstructure_reaction_context_id'}
    assert live['feature_tick_source']=='ws_exact_route'
    assert live['_feature_tick_diagnostic_window'][0]['route_sequence']==30


@pytest.mark.parametrize('damage', ['route', 'route_key', 'bool_epoch', 'clock_order', 'row_type'])
def test_receipt_consumer_rechecks_window_instead_of_trusting_flags(damage):
    ws,c=fixture();selected,_=select(ws,c)
    packet=dict(_feature_tick_diagnostic_window=selected['recent_trade_ticks'],
        feature_tick_source='ws_exact_route',tick_aggressor_pressure_usable=True,
        tick_aggressor_trusted_count=10)
    raw=dict(stock_code='005930',effective_venue='KRX',session_bucket='KRX_REGULAR',
        entry_machine_input_as_of=NOW)
    receipt=O.build_receipt(selected,packet,raw,cutoff=NOW)
    assert F.valid_receipt(raw,receipt)
    if damage=='route':receipt['window'][0]['market_route']='nxt_only'
    elif damage=='route_key':receipt['source_route']='_NX|nxt_only'
    elif damage=='bool_epoch':receipt['window'][0]['transport_epoch']=True
    elif damage=='clock_order':receipt['window'][1]['received_at_ms']=(NOW-.05)*1000
    elif damage=='row_type':receipt['window'][0]=None
    receipt['window_sha256']=O.digest(receipt['window'])
    receipt['receipt_sha256']=O.digest({k:v for k,v in receipt.items() if k!='receipt_sha256'})
    assert not F.valid_receipt(raw,receipt)


def test_submit_refresh_remains_strict_and_other_symbol_not_opted_in(monkeypatch):
    from src.engine import sniper_state_handlers as H
    ws,c=fixture();monkeypatch.setattr(H.time,'time',lambda:NOW)
    monkeypatch.setattr(H,'WS_MANAGER',SimpleNamespace(get_latest_data=lambda code:ws))
    monkeypatch.setenv('KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED','true')
    _,fields=H._pre_submit_refresh_real_ws_snapshot('005930',ws,'SCALPING',refresh_even_if_input_fresh=True)
    assert fields['pre_submit_ws_snapshot_refresh_applied'] is False
    assert fields['pre_submit_ws_snapshot_refresh_reason']=='latest_best_levels_invalid'
    assert not O.samsung_scope('000660',c)


def test_prepared_consumer_uses_same_pure_selector(monkeypatch):
    from src.engine import sniper_state_handlers as H
    ws,c=fixture();monkeypatch.setattr(H.time,'time',lambda:NOW)
    monkeypatch.setattr(H,'WS_MANAGER',SimpleNamespace(get_latest_data=lambda code:deepcopy(ws)))
    monkeypatch.setenv('KORSTOCKSCAN_SCALP_PRE_SUBMIT_QUOTE_REFRESH_ENABLED','true')
    monkeypatch.setattr(H,'revalidate_entry_candle_snapshot',lambda context,ws,now_ts:deepcopy(context))
    result,ticks,context,fields=H._refresh_prepared_entry_inputs('005930',ws,[],c)
    assert fields['entry_ai_final_ws_snapshot_refresh_reason']=='latest_locked_observation_only'
    assert ticks==result['recent_trade_ticks']
    assert result['entry_machine_exact_tick_source']==KEY


def historical_case():
    raw=dict(stock_code='005930',effective_venue='KRX',session_bucket='krx_regular',
        entry_candle_context=dict(request_code='005930_AL',ws_route='krx_nxt_integrated'),
        entry_machine_input_as_of=NOW,features=dict(buy_pressure_10t=100,net_aggressive_delta_10t=100,
            price_change_10t_pct=0,curr_vs_micro_vwap_bp=-5,micro_vwap_available=True,
            tick_aggressor_pressure_usable=True,tick_aggressor_trusted_count=10,
            tick_context_stale=False,quote_stale=False))
    window=[dict(t=NOW-1+i*.1,ep=987654,seq=i+1,p=275500,q=10,side='BUY',
        valid=True,flow_valid=True,continuous=True) for i in range(10)]
    proof=F.historical_receipt(raw,window,archive_sha256='a'*64,window_cutoff=NOW)
    return raw,window,proof


def test_historical_proof_is_distinct_from_main_identity_and_source_gap():
    raw,window,proof=historical_case()
    assert F.valid_receipt(raw,proof)
    assert proof['main_epoch_equivalence'] is False and proof['native_promotion_support'] is False
    window[4]['seq']=99
    damaged=F.historical_receipt(raw,window,archive_sha256='a'*64,window_cutoff=NOW)
    assert damaged['usable'] is False and not F.valid_receipt(raw,damaged)
    assert not F.valid_receipt(raw,dict(proof,payload_sha256='b'*64))


@pytest.mark.parametrize('extra_risk',[None,'unknown_program_fact','liquidity_adverse','hard_blocker'])
def test_recipe_requires_every_fact_and_preserves_parent_setup(monkeypatch,extra_risk):
    raw,_,proof=historical_case()
    setup=dict(strategy_raw_input=raw,strategy_raw_sha256=F.S.digest(raw),setup_family='NO_VALID_SETUP',
        setup_state='UNCONFIRMED',local_breakout=dict(recheck_required=True),
        micro_recovery_observation=dict(price_response=False))
    baseline=dict(action='RECHECK',liquidity_inputs_complete=True,liquidity_threshold_pass=True)
    if extra_risk=='hard_blocker':baseline['action']='BLOCK'
    risks=[dict(risk_code='ADVERSE_TAPE',risk_fact_ids=['supportive_micro_tape_vs_program_net_sell'],required_counterweight_fact_ids=[]),
           dict(risk_code='CONFIRMATION_MISSING',risk_fact_ids=['trigger_confirmation_missing','no_supported_setup'],required_counterweight_fact_ids=[])]
    if extra_risk:risks.append(dict(risk_code='LIQUIDITY_FRAGILE' if extra_risk=='liquidity_adverse' else 'ADVERSE_TAPE',risk_fact_ids=[extra_risk],required_counterweight_fact_ids=[]))
    monkeypatch.setattr(F.E,'mechanistic_entry_policy_decision',lambda *a,**k:deepcopy(baseline))
    monkeypatch.setattr(F.S,'rebuild',lambda *a: (deepcopy(setup),{},dict(effective_thresholds=dict(micro_confirmation_recipe=0))))
    monkeypatch.setattr(F.E,'entry_action_counterweight_bindings',lambda setup:dict(bindings=deepcopy(risks)))
    original=deepcopy(setup)
    result=F.evaluate(setup,{},source_receipt=proof)
    assert result['proposed_action']==('ENTER_NOW' if extra_risk is None else baseline['action'])
    assert result['original_micro_price_response'] is False
    assert setup==original and result['runtime_effect'] is False and result['allowed_runtime_apply'] is False
    assert len(result['fact_ledger'])==3+(extra_risk is not None)


def test_offline_recipe_cannot_validate_as_live_policy():
    assert F.E.validate_mechanistic_entry_threshold_policy(dict(schema=F.RECIPE))


@pytest.mark.parametrize('symbol,expected',[('005930','RECHECK'),('000660','ENTER_NOW')])
def test_replacement_mode_has_no_incumbent_success_preservation_requirement(monkeypatch,symbol,expected):
    raw,_,proof=historical_case();raw['stock_code']=symbol;raw['features']['buy_pressure_10t']=10
    setup=dict(strategy_raw_input=raw,strategy_raw_sha256=F.S.digest(raw))
    baseline=dict(action='ENTER_NOW',liquidity_inputs_complete=True,liquidity_threshold_pass=True)
    monkeypatch.setattr(F.E,'mechanistic_entry_policy_decision',lambda *a,**k:deepcopy(baseline))
    monkeypatch.setattr(F.S,'rebuild',lambda *a:(setup,{},dict(effective_thresholds=dict(micro_confirmation_recipe=0))))
    monkeypatch.setattr(F.E,'entry_action_counterweight_bindings',lambda s:dict(bindings=[]))
    assert F.evaluate(setup,{},source_receipt=proof,admission_mode='replace')['proposed_action']==expected
