"""Real native capture/queue/reader measurement never certifies unrun Main."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest

from src.engine.automation import main_stop_performance as perf
from src.engine.scalping import main_stop_policy as policy
from src.tests.test_main_stop_policy import baseline


def scenario():
    at=1792112400.
    depth=dict(item='005930',market_route='krx_only',transport_epoch=1,observed_epoch=at,
               best_bid=9700,best_bid_qty=20,orderbook={'bids':[{'price':9700,'volume':20}]})
    quote={**depth,'source_type':'0D','depth_receipt':depth}
    stock=dict(id=1,code='005930',name='OFFLINE_STOP_TEST',strategy='SCALPING',position_tag='SCANNER',
               buy_qty=10,buy_price=10000.,status='HOLDING',
               _trailing_entry_cost_model=dict(buy_krw=10.,sell_rate=.001,known_at=at-1,source_sha256='a'*64))
    inputs=dict(snapshot={'realtime_type_snapshots_by_route':{'krx_only':{'0D':depth}}},
        quote_receipt=quote,executable_bid=9700,bid_source='fresh_ws_executable_bid',rest_snapshot=None,
        quality={'quote_consistency_state':'consistent'},nxt_quality={},quote_received_at=at,bid_received_at=at,
        market_type='REGULAR',exit_allowed_by_clock=True,price_usable=True,now_ts=at,
        evaluator='normal',holding_profit_rate_at_eval=-3.)
    return dict(stock=stock,quote_inputs=inputs,role='SCANNER',target_date='2026-10-16')


def measured(tmp_path):
    return perf.measure_capture_pair(tmp_path/'performance.json',scenarios=[scenario()],
        baseline=baseline(),candidate=replace(baseline(),grace_sec=0),source_sha256='a'*64)


def test_real_native_capture_pair_has_same_calls_and_readback_with_explicit_scope(tmp_path):
    body,ref=measured(tmp_path)
    assert json.loads((tmp_path/'performance.json').read_text())==body
    assert ref['sha256']
    assert body['execution_order']==['baseline','candidate','candidate','baseline','baseline','candidate']
    assert len(body['arms']['candidate'])==3
    assert all(run['queue']['append_confirmed']==run['decoded_rows']==2
               for runs in body['arms'].values() for run in runs)
    assert body['arms']['baseline'][0]['decision_sha256']!=body['arms']['candidate'][0]['decision_sha256']
    assert body['full_runtime_gate_status']=='blocked'
    assert body['allowed_runtime_apply'] is False
    assert perf.validate_receipt(body,code_sha=policy.implementation_sha(),source_sha='a'*64,require_full=False)==body
    with pytest.raises(ValueError,match='full_runtime_unmeasured'):
        perf.validate_receipt(body,code_sha=policy.implementation_sha(),source_sha='a'*64,require_full=True)


@pytest.mark.parametrize('fault',['pass','population','summary','context','code'])
def test_resealed_claim_cannot_widen_coverage_or_change_measured_population(tmp_path,fault):
    body,_=measured(tmp_path)
    if fault=='pass':body.update(status='pass',scope='runtime_and_postclose',unresolved_findings=[])
    elif fault=='population':body['arms']['candidate'][0]['decoded_rows']=3
    elif fault=='summary':body['arms']['candidate'][0]['capture']['p95_ns']=0
    elif fault=='context':body['arms']['candidate'][0]['context_sha256']='b'*64
    elif fault=='code':body['code_sha256']='b'*64
    body['performance_sha256']=policy.digest({k:v for k,v in body.items() if k!='performance_sha256'})
    with pytest.raises(ValueError,match='stop_performance_'):
        perf.validate_receipt(body,code_sha=policy.implementation_sha(),source_sha='a'*64,require_full=False)


def test_capture_failure_restores_sink_and_never_creates_success_receipt(tmp_path):
    bad=deepcopy(scenario());bad['stock']['buy_qty']=0
    old=policy._SOURCE_SINK
    with pytest.raises(ValueError,match='capture_rejected'):
        perf.measure_capture_pair(tmp_path/'performance.json',scenarios=[bad],baseline=baseline(),
            candidate=baseline(),source_sha256='a'*64)
    assert policy._SOURCE_SINK is old
    assert not (tmp_path/'performance.json').exists()


def request_fixture(source_sha256='a'*64,repeats=3):
    """Reproducible offline request; full/unknown quantity and caller ordering."""
    from dataclasses import asdict
    from src.tests.test_main_stop_quantity_source import native_stock
    cases=[]
    for index,sequence in enumerate((
        [['fast','preset_safety'],['normal','preset_safety'],['normal','common_soft']],
        [['normal','preset_safety'],['normal','common_soft'],['fast','preset_safety']],
        [['normal','preset_safety'],['normal','common_soft']])):
        case=scenario();case['role']='SCALP_PRESET_TP'
        if index<2:
            native=native_stock(filled=10,ordered=10)
            case['stock'].update(native)
            case['stock'].update(id=index+1,status='HOLDING',exit_mode='SCALP_PRESET_TP')
        case['evaluation_sequence']=sequence
        case['stock']['id']=index+1
        cases.append(case)
    return dict(scenarios=cases,baseline=asdict(baseline()),candidate=asdict(replace(baseline(),grace_sec=0)),
                source_sha256=source_sha256,repeats=repeats)


def test_fast_normal_shared_quote_and_unknown_quantity_are_measured_without_loss(tmp_path):
    request=request_fixture()
    body,_=perf.measure_capture_pair(tmp_path/'performance.json',scenarios=request['scenarios'],
        baseline=baseline(),candidate=replace(baseline(),grace_sec=0),source_sha256='a'*64)
    for runs in body['arms'].values():
        for run in runs:
            assert run['calls']['native_capture']==3
            assert run['calls']['native_stage_receipts']==8
            assert run['decoded_rows']==run['queue']['append_confirmed']==11
            assert run['quantity_census']=={'full_fill':6,'unknown':2}
