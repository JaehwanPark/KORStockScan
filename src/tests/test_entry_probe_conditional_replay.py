"""Exact probe source, causal reconstruction and observation authority tests."""
from copy import deepcopy
from datetime import datetime
from types import SimpleNamespace

import pytest

from src.engine.scalping import entry_probe_conditional_replay as C
from src.engine.scalping import strategy_owner_replay as R
from src.engine.scalping.strategy_owner_components import digest


def seed_fixture():
    stamp = '2026-10-06T10:00:00+09:00'
    plan = dict(valid=True, blockers=[], total_qty=10, immediate_qty=1,
        deferred_probe_residual_qty=9, action_receipt_id='attempt', scanner_promotion_id='promotion',
        policy_bundle_hash='a'*64, price_policy_sha256='b'*64, effective_venue='KRX',
        market_session_bucket='KRX_REGULAR', observed_machine_action='ENTER_NOW', observation_only=True,
        legs=[dict(qty=1, numeric_price=10000, execution_phase='immediate'),
              dict(qty=5, numeric_price=None, execution_phase='after_verified_probe_fill'),
              dict(qty=4, numeric_price=None, execution_phase='after_verified_probe_fill')])
    context = dict(schema=R.ENTRY_OPERATING_SCHEMA, frozen_at=stamp, broker_route='KRX', budget_krw=120000.,
                   cost_policy_version='original', initial_fill_exit_state={'stop_rule':'original'},
                   policy_snapshot={'rules':{'SCALPING_ENTRY_PRICE_RESOLVER_ENABLED':True,
                       'SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS':80}})
    context['sha256'] = digest(context)
    continuation = dict(requested_qty=10, residual_qty=9, residual_quantities=[5,4],
                        common_fields={}, base_order={})
    order = dict(entry_split_order_probe_continuation=continuation,
        price=10000,
        entry_split_order_probe_timeout_sec=10., entry_split_order_probe_max_slippage_bps=20.,
        entry_split_order_probe_anchor_mode='original')
    diagnostic={}
    seed=C.freeze_conditional_plan(plan, stock_code='005930',
        observed_at=datetime.fromisoformat(stamp).timestamp(), operating_context=context,
        probe_order=order, source_identity={'evaluation_attempt_id':'attempt'}, diagnostic=diagnostic)
    assert C.valid_seed(seed), diagnostic
    return seed


def receipt(seed, kind, sequence, seconds, **fields):
    at=datetime.fromisoformat(seed['observed_at']).timestamp()+seconds
    original = (dict(order_no=fields.get('broker_order_no'), fill_qty=fields.get('cumulative_qty'),
                     fill_price=fields.get('fill_price')) if kind == 'probe_fill' else
        dict(quote={source:fields.get(field) for field,source in (
            ('quote_route','market_route'), ('quote_transport_epoch','transport_epoch'),
            ('quote_received_at','observed_epoch'), ('best_bid','best_bid'), ('best_ask','best_ask'))},
             account_guard={'account_guard_allowed':fields.get('capital_allowed')},
             quantity={'allowed':fields.get('quantity_allowed')},
             continuation_action=fields.get('continuation_action'),
             guard_allowed=fields.get('guard_allowed'), fresh_mark_price=fields.get('fresh_mark_price'),
             native_residual_orders=fields.get('native_residual_orders')))
    return C.seal(dict(kind=kind, sequence=sequence, available_at=at, event_at=at,
        evaluation_attempt_id=seed['evaluation_attempt_id'], plan_sha256=seed['plan_sha256'],
        stock_code=seed['stock_code'], effective_venue=seed['effective_venue'],
        session_bucket=seed['session_bucket'], source_sha256=digest(original), native_source=original,
        runtime_pid=seed['runtime_pid'], **fields), 'sha256')


def receipts(seed):
    return [receipt(seed,'probe_fill',1,1, broker_receipt_verified=True,
            broker_order_no='B1', cumulative_qty=1, fill_price=10000),
            receipt(seed,'residual_decision',2,2,continuation_action='ALLOW_NORMAL',
            guard_allowed=True, capital_allowed=True, quantity_allowed=True,
            quote_route='KRX', transport_epoch=1, quote_transport_epoch=1,
            quote_received_at=datetime.fromisoformat(seed['observed_at']).timestamp()+1.9,
            quote_freshness_limit_sec=.5,best_bid=9990,best_ask=10010,fresh_mark_price=10000,
            native_residual_orders=[{'qty':5,'price':10000},{'qty':4,'price':9970}])]


def test_known_plan_keeps_unknown_prices_and_does_not_claim_paired_economics():
    seed=seed_fixture(); before=deepcopy(seed)
    result=C.reconstruct_prices(seed, receipts(seed))
    assert result['status']=='reconstructed_prices',result
    assert sum(o['qty'] for o in result['residual_orders'])==9
    assert seed==before and seed['atomic_plan']['legs'][1]['numeric_price'] is None
    assert result['paired_economic_eligible'] is False
    assert result['net_pnl_krw'] is None and result['actual_order_submitted'] is False


@pytest.mark.parametrize('damage',['attempt','hash','scope','future_quote','epoch','guard','capital','quantity','late','sequence','future_fill','action','mark'])
def test_inexact_or_future_receipts_never_reconstruct_prices(damage):
    seed=seed_fixture(); rows=receipts(seed); row=rows[1]
    changes={'attempt':{'evaluation_attempt_id':'other'},'hash':{'plan_sha256':'f'*64},
        'scope':{'session_bucket':'NXT'},'future_quote':{'quote_received_at':row['event_at']+1},
        'epoch':{'quote_transport_epoch':2},'guard':{'guard_allowed':False},
        'capital':{'capital_allowed':False},'quantity':{'quantity_allowed':False},
        'action':{'continuation_action':'BLOCK'},'mark':{'fresh_mark_price':20000},
        'late':{'event_at':row['event_at']+20,'available_at':row['available_at']+20},
        'sequence':{'sequence':1},'future_fill':{'event_at':rows[0]['available_at']-1}}
    rows[1]=C.seal({**row,**changes[damage]},'sha256')
    result=C.reconstruct_prices(seed, rows)
    assert result['status']=='source_gap' and result['residual_orders'] is None


def test_missing_fill_is_a_gap_and_residual_abort_retains_probe_inventory():
    seed=seed_fixture()
    assert C.reconstruct_prices(seed,[])['blocker']=='exact_probe_fill_receipt_missing_or_conflicting'
    rows=receipts(seed)
    rows[1]=receipt(seed,'residual_decision',2,seed['probe_timeout_sec']+2,
        continuation_action='BLOCK', native_residual_orders=[], capital_allowed=False, quantity_allowed=False)
    result=C.reconstruct_prices(seed,rows)
    assert result['held_probe_qty']==1 and result['residual_orders']==[]
    assert result['net_pnl_krw'] is None


def test_original_kernel_change_never_reuses_current_prices(monkeypatch):
    seed=seed_fixture()
    monkeypatch.setattr(C,'kernel_identity',lambda:{'new':'f'*64})
    assert C.reconstruct_prices(seed,receipts(seed))['blocker']=='conditional_original_price_kernel_unavailable'


def test_conditional_seed_reaches_existing_report_without_market_reads():
    seed=seed_fixture()
    event=SimpleNamespace(stage='entry_ai_economic_plan_observed', code='005930', fields={
        'entry_opportunity_replay_seed':seed,'entry_execution_sizing_plan_sha256':seed['plan_sha256']})
    def forbidden(*args,**kwargs):raise AssertionError('No market read for unobserved probe execution')
    result=R.build_entry_opportunity_replays('2026-10-06',[event], source_stage=event.stage,micro_loader=forbidden)
    assert result['conditional_probe_source_census']['unique_plan_count']==1
    assert result['conditional_probe_source_census']['paired_economic_eligible_count']==0
    assert result['conditional_probe_replays'][0]['seed']==seed
    assert result['conditional_probe_replays'][0]['status']=='source_gap'


def test_conditional_plan_writer_trace_and_capsule_binding():
    from src.engine.scalping import auxiliary_source_contract as A
    from src.engine.monitoring.submission_bottleneck_monitor import economic_evidence
    seed=seed_fixture()
    row=dict(stock_code='005930',evaluation_attempt_id='attempt',scanner_promotion_id='promotion',
        effective_venue='KRX',session_bucket='KRX_REGULAR',entry_economic_conditional_seed=seed,
        entry_economic_plan_sha256=seed['plan_sha256'],entry_economic_writer_plan_sha256=seed['plan_sha256'],
        entry_execution_sizing_plan_sha256=seed['plan_sha256'],entry_opportunity_replay_seed=seed,
        entry_economic_source_status='recorded_source_only')
    assert A.plan_state(row)['state']=='conditional_plan_preserved'
    assert economic_evidence(row,'005930')['status']=='recorded_conditional_source_only'
    row['evaluation_attempt_id']='other'
    assert A.plan_state(row)['errors']
    assert economic_evidence(row,'005930')['status']=='source_gap'


def test_original_rules_are_used_without_mutating_live_rules(monkeypatch):
    from src.engine import sniper_entry_latency as latency
    seed=seed_fixture()
    live=SimpleNamespace(SCALPING_ENTRY_PRICE_RESOLVER_ENABLED=False,
                         SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS=99)
    monkeypatch.setattr(latency,'TRADING_RULES',live)
    result=C.reconstruct_prices(seed,receipts(seed))
    assert result['status']=='reconstructed_prices'
    assert latency.TRADING_RULES is live


def test_wire_loader_and_duplicate_conflict_conserve_source_population():
    import json
    from src.engine.sniper_missed_entry_counterfactual import _load_entry_events
    seed=seed_fixture()
    event=dict(pipeline='ENTRY_PIPELINE', emitted_at=seed['observed_at'],
        stock_code='005930', emitted_date='2026-10-06', stage='entry_execution_sizing_plan',
        fields={'entry_opportunity_replay_seed':json.dumps(seed),
                'entry_execution_sizing_plan_sha256':seed['plan_sha256']})
    events=[event,deepcopy(event)]
    for row in receipts(seed):
        events.append({**event,'stage':'entry_probe_conditional_receipt_observed',
            'fields':{'entry_probe_conditional_receipt':json.dumps(row)}})
    output=R.build_entry_opportunity_replays('2026-10-06',_load_entry_events('2026-10-06',rows=events))
    assert output['conditional_probe_replays'][0]['status']=='reconstructed_prices'
    assert output['conditional_probe_source_census']['duplicate_plan_rows']==1
    changed=C.seal({**seed,'anchor_mode':'different'})
    events[1]['fields']['entry_opportunity_replay_seed']=json.dumps(changed)
    output=R.build_entry_opportunity_replays('2026-10-06',_load_entry_events('2026-10-06',rows=events))
    census=output['conditional_probe_source_census']
    assert census['conflicting_plan_rows']==2 and census['duplicate_plan_rows']==0
    assert output['conditional_probe_replays'][0]['blocker']=='conditional_original_seed_conflict'


def test_native_fill_observer_emits_original_plan_and_never_changes_inventory(monkeypatch):
    import json
    from src.engine import sniper_execution_receipts as native
    seed=seed_fixture(); stock={'entry_split_initial_entry_seed':seed,
        'entry_split_probe_filled_at':datetime.fromisoformat(seed['observed_at']).timestamp()+1}
    before=deepcopy(stock); emitted=[]
    monkeypatch.setattr(native,'emit_pipeline_event',lambda *args,**kwargs:emitted.append((args,kwargs)))
    monkeypatch.setattr(native,'pipeline_lifecycle_fields_safe',lambda *args,**kwargs:{})
    monkeypatch.setattr(native,'entry_opportunity_recheck_attribution_fields',lambda *args,**kwargs:{})
    native._log_holding_pipeline_impl('test','005930',1,'probe_filled',candidate_stock=stock,
        observe_candidate_lifecycle=False,order_no='B1',fill_qty=1,fill_price=10000,
        actual_order_submitted=True,broker_order_forbidden=False)
    assert stock==before and len(emitted)==2
    receipt=json.loads(emitted[-1][1]['fields']['entry_probe_conditional_receipt'])
    assert receipt['plan_sha256']==seed['plan_sha256']
    assert receipt['source_sha256']==digest(receipt['native_source'])


@pytest.mark.parametrize('damage',['boolean_fill','unbound_source','native_price','scope'])
def test_additional_contract_gaps_never_claim_reconstruction(damage):
    seed=seed_fixture(); rows=receipts(seed)
    if damage=='boolean_fill': rows[0]['cumulative_qty']=True
    elif damage=='unbound_source': rows[0]['fill_price']=10001
    elif damage=='native_price': rows[1]['native_residual_orders'][0]['price']=9990
    else: seed=C.seal({**seed,'session_bucket':'NXT_AFTERMARKET'})
    rows=[C.seal(r,'sha256') for r in rows]
    assert C.reconstruct_prices(seed,rows)['status']=='source_gap'


def test_full_pre_ai_probe_producer_preserves_total_and_original_operating_inputs(monkeypatch,tmp_path):
    from src.tests.test_entry_execution_sizing_plan import test_runtime_pre_ai_producer_freezes_owner_inputs_without_submit as run
    run(monkeypatch,tmp_path,True,'KRX','KRX','KRX_REGULAR','ENTER_NOW',None,probe_first=True)


def test_completed_receipt_accepts_only_submitted_conditional_seed():
    from src.engine.trade_profit import get_trade_cost_rate
    seed=seed_fixture()
    stamp=datetime.fromisoformat(seed['observed_at'])
    context=seed['operating_contract']
    context['cost_policy_version']='trade_profit_net_realized_pnl:rate='+str(get_trade_cost_rate())
    decision=dict(evaluation_attempt_id=seed['evaluation_attempt_id'],
        machine_bundle_sha256=seed['policy_bundle_sha256'],machine_policy_version='machine-v1',
        machine_policy_sha256='1'*64,compact_prompt_version='compact-v1',compact_prompt_sha256='2'*64,
        decision_trace_id='original-trace',runtime_pid=seed['runtime_pid'])
    context['entry_decision_version_receipt']=C.seal(decision,'sha256')
    context['sha256']=digest({k:v for k,v in context.items() if k!='sha256'})
    seed=C.seal(seed)
    stock=dict(entry_split_initial_entry_seed=seed,realized_pnl_krw=177,
        sell_execution_receipt_economics_complete=True,sell_execution_receipt_quantity_contract_complete=True)
    kwargs=dict(buy_price=10000,buy_qty=10,profit_rate=1.7654,completion_at=stamp)
    assert R.entry_split_actual_economic_receipt(stock,**kwargs) is None
    plan=deepcopy(seed['atomic_plan']);plan['observation_only']=False
    stock['entry_split_initial_entry_seed']=C.seal({**seed,'atomic_plan':plan,'plan_sha256':digest(plan)})
    result=R.entry_split_actual_economic_receipt(stock,**kwargs)
    assert result['cost_complete'] and result['exact_lineage'] and result['entry_qty']==10
    stock['sell_execution_receipt_economics_complete']=False
    assert R.entry_split_actual_economic_receipt(stock,**kwargs)['cost_complete'] is False
