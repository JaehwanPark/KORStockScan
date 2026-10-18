"""Real stage receipts preserve evaluator, price, clock and quantity ownership."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
import json

import pytest

from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping.main_stop_runtime_source import evaluation_source
from src.engine.scalping.position_peak_ledger import position_cycle_id
from src.tests.test_main_stop_quantity_source import native_stock


def stage_stock(*, record=101, quantity=10, role='SCANNER', target='2026-10-12'):
    stock = native_stock(filled=quantity, ordered=quantity)
    stock.update(id=record, status='HOLDING', position_tag=role)
    values = policy.StopValues(-3., 60, 20, 8, 3, .67, 1., -5., -4., -2., -.3)
    stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
        role=role, market='REGULAR', target=target, baseline=values)
    return stock


def stage_inputs(cost=None):
    return dict(grace_enabled=True, after_add=False, handoff_enabled=False,
        protect_enabled=True, vote_max_worsen_pct=.8, holding_ai_required=False,
        holding_vote_source=None, cost_model=cost, soft_stop_micro_grace_started_at=None)


def research_quote(stock, *, at, bid, profit, cost=None, evaluator='normal', preset=None):
    return policy.source_row(stock, at=at, bid=bid, bid_qty=100,
        decision_profit_pct=profit,
        quote=dict(market_route='krx_nxt_integrated', item='005930_AL', transport_epoch=1, observed_epoch=at),
        coverage_complete=True, automatic_management_allowed=True,
        runtime_flags=stage_inputs(), cost_model=cost, vote_source=None,
        preset_stop=preset, native_decision_required=True, capture_evaluator=evaluator)


def research_evaluation(stock, quote, *, at=None, stage='common_soft', preset=None,
                        predecessor=None, evaluator='normal', legacy=False):
    return evaluation_source(stock, quote_source=quote, at=quote['at'] if at is None else at,
        evaluator=evaluator, stage=stage, decision_price=quote['bid'], decision_price_basis='executable_bid',
        decision_profit_pct=quote['decision_profit_pct'], priority_status='blocked_legacy' if legacy else 'reached',
        preset_stop=preset, preset_predecessor=predecessor, legacy_broker_recovered=legacy,
        quote_max_age_sec=3., decision_inputs=(stage_inputs(quote['cost_model']) if stage=='common_soft'
            else dict(handoff_enabled=quote['handoff_enabled'])))


def test_native_counter_anchor_separates_same_clock_evaluations_without_payload_identity():
    stock = stage_stock()
    quote = research_quote(stock, at=1000., bid=9950, profit=-.5)
    first = research_evaluation(stock, quote)
    second = research_evaluation(stock, quote)
    assert first['evaluation_id'] != second['evaluation_id']
    expected = dict(position_key=first['position_key'], pin_sha256=first['pin_sha256'],
        evaluator='normal', stage='common_soft', at=1000., generation=1)
    assert first['evaluation_id'] == policy.digest(expected)
    assert first['quantity_source']['status'] == 'full_fill'
    assert 'partial_fill' not in quote
    for bad in (True, 1., '1', -1):
        stock['_main_stop_evaluation_generation'] = bad
        with pytest.raises(ValueError, match='generation_invalid'):
            research_evaluation(stock, quote)


def test_quantity_and_decision_inputs_are_current_even_when_quote_is_shared():
    stock = stage_stock()
    quote = research_quote(stock, at=1000., bid=9950, profit=-.5)
    original = deepcopy(quote)
    stock['pending_entry_orders'].append(dict(ord_no='0000456', qty=2, filled_qty=0, status='OPEN'))
    stock['entry_requested_qty'] = stock['requested_buy_qty'] = 12
    actual = research_evaluation(stock, quote, at=1000.2)
    assert actual['quantity_source']['status'] == 'unknown'
    assert actual['at'] == 1000.2 and actual['quote_observation_at'] == 1000.
    assert quote == original
    stale=research_evaluation(stock, quote, at=1004.)
    assert stale['quote_binding_status']=='source_gap'


@pytest.mark.parametrize('order', [('fast_prearm','normal'), ('normal','fast_prearm')])
def test_shared_cadence_never_erases_actual_normal_call(monkeypatch, order):
    from src.engine import sniper_state_handlers as handlers
    stock = stage_stock()
    at = 1792112400.
    stock['_trailing_entry_cost_model']=dict(buy_cost_krw=10., sell_cost_rate=.001, known_at=at-1, source_sha256='a'*64)
    context = dict(at=at, bid=9900, bid_qty=20, quote=dict(market_route='KRX', item='005930',
        transport_epoch=1, observed_epoch=at), complete=True, market='REGULAR', evaluator=order[0],
        decision_profit_pct=-1., position_key=position_cycle_id(stock), quantity=10,
        buy_price=10000., pending_exit=False, quote_max_age_sec=3.)
    captured=[]
    monkeypatch.setattr(policy, 'enqueue_source', lambda stock,code,row: captured.append(deepcopy(row)) or True)
    monkeypatch.setattr(handlers, '_is_scalp_simulated_position', lambda *a: False)
    monkeypatch.setattr(handlers, '_main_stop_preset_observation', lambda *a, **k: None)
    assert handlers._capture_main_stop_observation(stock, '005930', context)
    stock['_trailing_entry_cost_model']['buy_cost_krw']=20.
    assert stock['_main_stop_last_quote_source']['cost_model']['buy_cost_krw']==10.
    context = dict(context, at=at+.2, evaluator=order[1])
    stock['_main_stop_current_quote_context'] = context
    assert handlers._capture_main_stop_observation(stock, '005930', context) is False
    # Whichever quote caller ran first, the actual normal owner emits separately.
    stock['_main_stop_current_quote_context'] = dict(context, evaluator='normal')
    event = handlers._observe_main_stop_evaluation(stock, '005930', at=at+.2, evaluator='normal',
        stage='common_soft', decision_price=9910, decision_price_basis='mark_price',
        decision_profit_pct=-.9, decision_inputs=stage_inputs())
    assert event and len(captured)==2
    assert captured[0]['schema']=='main_stop_source_v1'
    assert captured[1]['schema']=='main_stop_evaluation_source_v1'
    assert event['quote_source_sha256']==policy.digest(captured[0])
    assert event['at']==at+.2 and event['quote_observation_at']==at
    assert event['decision_price']==9910 and captured[0]['bid']==9900
    assert event['decision_inputs']['grace_enabled'] is True
    assert event['decision_inputs']['cost_model']['buy_cost_krw']==20.


def test_native_receipt_failure_is_source_only_and_next_receipt_exposes_loss(monkeypatch):
    from src.engine.scalping.main_stop_runtime_source import ensure_observation_epoch, observation_source_identity
    from src.engine import sniper_state_handlers as handlers
    stock=stage_stock()
    ensure_observation_epoch(stock)
    quote=research_quote(stock,at=1000.,bid=9900,profit=-1.)
    quote.update(observation_source_identity(stock))
    quote['source_sha256']=policy.digest({k:v for k,v in quote.items() if k!='source_sha256'})
    stock['_main_stop_last_quote_source']=quote
    stock['_main_stop_current_quote_context']=dict(at=1000.,bid=9900,bid_qty=100,
        quote=dict(item=quote['item'],market_route=quote['route'],transport_epoch=1,observed_epoch=1000.),
        complete=True,market='REGULAR',evaluator='normal',position_key=position_cycle_id(stock),
        quantity=10,buy_price=10000.,pending_exit=False,quote_max_age_sec=3.)
    monkeypatch.setattr(policy,'enqueue_source',lambda *a: False)
    inputs=dict(at=1000.,evaluator='normal',stage='common_soft',decision_price=9900,
        decision_price_basis='executable_bid',decision_profit_pct=-1.,decision_inputs=stage_inputs())
    before={k:deepcopy(v) for k,v in stock.items() if not k.startswith('_main_stop')}
    assert handlers._observe_main_stop_evaluation(stock,'005930',**inputs) is None
    assert all(stock[k]==v for k,v in before.items())
    monkeypatch.setattr(policy,'enqueue_source',lambda *a: True)
    actual=handlers._observe_main_stop_evaluation(stock,'005930',**inputs)
    assert actual['evaluation_rejected_count']==1
    assert actual['evaluation_generation']==2


def test_native_full_proof_is_retained_by_real_metadata_clear(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping.main_stop_quantity_source import build_quantity_source
    stock=stage_stock()
    monkeypatch.setattr(handlers,'move_orders_to_terminal',lambda *a,**k:None)
    handlers._clear_pending_entry_meta(stock)
    assert 'pending_entry_orders' not in stock
    assert build_quantity_source(stock,at=__import__('time').time())['status']=='full_fill'


def evaluation_stream(source):
    """Produce native stage receipts for explicit synthetic test quote scenarios.

    Callers create/mutate their synthetic quote scenario first. Malformed quotes
    remain unbound for negative consumer tests; no production source is relabeled.
    """
    from src.engine import sniper_execution_receipts as receipts
    states={}
    for quote in source:
        yield quote
        if quote.get('schema')!='main_stop_source_v1':
            continue
        try:
            key=quote['position_key']
            stock=states.get(key)
            if stock is None:
                qty=quote['quantity'];price=quote['buy_basis_krw']/qty
                if type(qty) is not int or qty<=0 or not float(price).is_integer():
                    continue
                code=str(quote['item'])[:6]
                stock=dict(id=quote['record_id'],code=code,strategy='SCALPING',
                    position_peak_cycle_id=key,entry_requested_qty=qty,requested_buy_qty=qty,
                    pending_entry_orders=[dict(ord_no='0000123',qty=qty,filled_qty=0,status='OPEN')])
                result=receipts._resolve_entry_effective_fill_qty(target_stock=stock,code=code,
                    order_no='0000123',exec_price=int(price),exec_qty=qty,order_qty=qty,
                    remaining_qty=0,cumulative_exec_amount=int(price)*qty,
                    execution_no='E1',unit_exec_qty=qty,unit_exec_price=int(price))
                assert result['status']!='invalid'
                stock.update(buy_qty=qty,buy_price=price,
                    main_stop_policy_pin={'pin_sha256':quote['pin_sha256']})
                original_quantity=quote.get('quantity_source')
                if isinstance(original_quantity,dict):
                    # Preserve the exact native receipt producer identities for
                    # source-to-cost tests; never normalize unknown to full.
                    from src.engine.scalping.main_stop_quantity_source import FILL_KEYS
                    for field in (*FILL_KEYS,'pending_entry_orders','entry_requested_qty','requested_buy_qty'):
                        stock.pop(field,None)
                    proof=original_quantity.get('proof') or {}
                    stock.update(deepcopy(proof.get('fill_receipts') or {}))
                    if proof.get('evidence_kind')=='native_bundle_terminal':
                        stock['initial_quantity_last_terminal_bundle']=deepcopy(proof['bundle'])
                    elif proof.get('evidence_kind')=='native_filled_order_census':
                        stock['pending_entry_orders']=deepcopy(proof['orders'])
                        stock['entry_requested_qty']=stock['requested_buy_qty']=proof['requested_qty']
                states[key]=stock
            stock['main_stop_source_rejected_count']=quote.get('capture_rejected_count',0)
            kwargs=dict(quote_source=quote,at=quote['at'],evaluator='normal',
                decision_price=quote['bid'],decision_price_basis='executable_bid',
                decision_profit_pct=quote['decision_profit_pct'],priority_status='reached',
                quote_max_age_sec=3.)
            predecessor=None
            preset=quote.get('preset_stop')
            if quote.get('role')=='SCALP_PRESET_TP' and isinstance(preset,dict):
                if preset.get('evaluator')!='normal':
                    continue
                predecessor=evaluation_source(stock,stage='preset_safety',preset_stop=preset,
                    decision_inputs=dict(handoff_enabled=quote['handoff_enabled']),**kwargs)
                yield predecessor
            inputs={key:quote.get(key) for key in ('grace_enabled','protect_enabled',
                'handoff_enabled','vote_max_worsen_pct','holding_vote_source','holding_ai_required','cost_model')}
            inputs['after_add']=bool(quote.get('add_count'))
            inputs['soft_stop_micro_grace_started_at']=None
            yield evaluation_source(stock,stage='common_soft',preset_predecessor=predecessor,
                decision_inputs=inputs,**kwargs)
        except (ValueError,TypeError,KeyError,ZeroDivisionError):
            # A malformed source must never be granted an invented actual call.
            continue


def native_preset_case(monkeypatch, *, fault=None, legacy=False):
    from zoneinfo import ZoneInfo
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping import avg_down_replay_capture, strategy_owner_replay
    at = datetime(2026, 10, 16, 10, tzinfo=ZoneInfo('Asia/Seoul')).timestamp()
    stock = stage_stock(record=10, role='SCALP_PRESET_TP', target='2026-10-16')
    stock.update(name='STOP_RESEARCH_TEST', exit_mode='SCALP_PRESET_TP', main_stop_source_at=at-.1,
        hard_stop_pct=-1.4, hard_stop_grace_sec=0, hard_stop_emergency_pct=-2.4,
        broker_recovered_legacy=legacy)
    depth = dict(item='005930', market_route='krx_only', transport_epoch=1, observed_epoch=at,
        best_bid=9700, best_bid_qty=20, orderbook={'bids':[{'price':9700,'volume':20}]})
    ws = dict(code='005930', curr=9800, upper_limit_price=13000, best_bid=9700, best_ask=9810,
        quote_age_ms=0, market_data_transport_epoch=1,
        last_realtime_type_item={'0D':'005930'}, last_realtime_type_ts={'0D':at},
        realtime_type_snapshots_by_route={'krx_only':{'0D':depth}})
    if fault == 'malformed_quote': depth['orderbook']['bids'][0]['volume'] = 'unknown'
    for module, names in ((avg_down_replay_capture, ('record_market_inputs','record_ai_state')),
        (strategy_owner_replay, ('observe_seed',))):
        for name in names: monkeypatch.setattr(module, name, lambda *a, **k: None)
    for name in ('_observe_initial_quantity_cap_following_tick', '_observe_avg_down_runtime_config',
        '_maybe_release_auto_manual_control_at_average_price', '_observe_entry_cancel_wait_counterfactuals',
        '_reconcile_pending_entry_orders', '_finalize_entry_split_probe_partial_position',
        '_append_holding_price_sample', '_persist_scalping_position_peak', '_update_holding_excursion_context',
        '_observe_smoothing_source_only_paths', '_maybe_emit_entry_ai_price_skip_followup', 'log_info'):
        monkeypatch.setattr(handlers, name, lambda *a, **k: None)
    for name in ('_retry_pending_hard_stop_manual_handoff', '_manual_control_exclusion_blocked',
        '_sell_cancel_reconciliation_blocks_holding', '_maybe_auto_exclude_open_loss_holding',
        '_nxt_rising_missed_partial_fill_reprice_enabled', '_entry_split_probe_pending_residual_reprice_enabled',
        '_maybe_submit_entry_split_probe_residual', '_has_active_sell_order_pending', '_is_scalp_simulated_position'):
        monkeypatch.setattr(handlers, name, lambda *a, **k: False)
    monkeypatch.setattr(handlers, '_holding_ws_freshness_recover_or_block', lambda stock,code,data,**k: (data,False,{}))
    monkeypatch.setattr(handlers, '_build_quote_consistency_fields', lambda *a, **k:
        ({'quote_consistency_state':'consistent'},9800,9810,9700))
    monkeypatch.setattr(handlers, '_holding_quote_provenance_fields', lambda *a, **k: {})
    monkeypatch.setattr(handlers, '_scalping_micro_estimator_log_fields', lambda *a, **k: {})
    monkeypatch.setattr(handlers, '_mutate_stock_state', lambda stock, **kw: stock.update(kw.get('set_fields') or {}))
    monkeypatch.setattr(handlers, '_remember_exit_context', lambda **k: None)
    monkeypatch.setattr(handlers, '_resolve_holding_elapsed_sec', lambda *a, **k: 3.)
    monkeypatch.setattr(handlers, '_sell_side_open_time_block_fields', lambda **k: {})
    monkeypatch.setattr(handlers, 'HIGHEST_PRICES', {})
    logs, captured = [], []
    monkeypatch.setattr(handlers, '_log_holding_pipeline', lambda stock,code,stage,**kw: logs.append((stage,kw)))
    def sink(stock,code,row):
        if fault == 'sink_failure': raise RuntimeError('sink_unavailable')
        captured.append(deepcopy(row)); return True
    monkeypatch.setattr(policy, 'enqueue_source', sink)
    return stock, ws, at, captured


@pytest.mark.parametrize('fault', [None, 'malformed_quote', 'sink_failure'])
@pytest.mark.parametrize('legacy', [False, True])
def test_actual_preset_stage_precedes_early_exit_and_source_failures_never_change_it(monkeypatch,fault,legacy):
    from src.engine import sniper_state_handlers as handlers
    stock,ws,at,captured=native_preset_case(monkeypatch,fault=fault,legacy=legacy)
    monkeypatch.setattr(handlers,'_rest_quote_only_hard_stop_confirmation_block',lambda *a,**k:False)
    monkeypatch.setattr(handlers,'_handoff_hard_stop_to_manual_control_if_enabled',lambda *a,**k:False)
    class NativeBranchReached(Exception):pass
    calls=[]
    def dispatch(**kwargs):
        calls.append(kwargs['exit_rule']);raise NativeBranchReached()
    def legacy_next(*a,**kwargs):
        calls.append('legacy_preset_skipped');raise NativeBranchReached()
    monkeypatch.setattr(handlers,'_dispatch_scalp_preset_exit',dispatch)
    monkeypatch.setattr(handlers,'_disable_scalp_preset_tp_order_for_trailing',legacy_next)
    with pytest.raises(NativeBranchReached):
        handlers.handle_holding_state(stock,'005930',ws,None,'BULL',now_ts=at)
    assert calls==['legacy_preset_skipped' if legacy else 'scalp_preset_hard_stop_pct']
    actual=[r for r in captured if r['schema']=='main_stop_evaluation_source_v1']
    assert not any(r['stage']=='common_soft' for r in actual)
    if fault != 'sink_failure':
        assert len(actual)==1 and actual[0]['stage']=='preset_safety'
        assert actual[0]['quote_binding_status']==('source_gap' if fault=='malformed_quote' else 'supported')
        assert actual[0]['decision_price']==9800 and captured[0]['bid']==9700
        assert actual[0]['decision_price_basis']=='mark_price'
        assert actual[0]['priority_status']==('blocked_legacy' if legacy else 'reached')
        assert actual[0]['preset_stop']['enabled'] is (not legacy)
    else:
        assert not actual and stock['main_stop_evaluation_source_gap']


@pytest.mark.parametrize('mark', [9950, 9650])
def test_native_common_soft_gate_records_above_and_below_threshold(monkeypatch, mark):
    from src.engine import sniper_state_handlers as handlers
    stock,ws,at,captured=native_preset_case(monkeypatch)
    stock['exit_mode']='TRAILING'
    stock['main_stop_policy_pin']=policy.pin(position_key=position_cycle_id(stock),
        role='SCANNER',market='REGULAR',target='2026-10-16',baseline=policy.StopValues(-3.,60,20,8,3,.67,1.,-5.,-4.,-2.,-.3))
    ws.update(curr=mark,best_bid=mark-10,best_ask=mark+10)
    depth=ws['realtime_type_snapshots_by_route']['krx_only']['0D']
    depth.update(best_bid=mark-10)
    depth['orderbook']['bids'][0]['price']=mark-10
    monkeypatch.setattr(handlers,'_build_quote_consistency_fields',lambda *a,**k:
        ({'quote_consistency_state':'consistent'},mark,mark+10,mark-10))
    monkeypatch.setattr(handlers,'_scalp_trailing_trusted_peak',lambda *a,**k:10000)
    monkeypatch.setattr(handlers,'_scalp_trailing_strength_and_event_replay',lambda *a,**k:(False,{}))
    monkeypatch.setattr(handlers,'_scalp_trailing_latch_first_crossing',lambda stock,code,decision,**k:decision)
    monkeypatch.setattr(handlers,'_scalp_trailing_latch_arm',lambda *a,**k:None)
    monkeypatch.setattr(handlers,'_evaluate_scalp_profit_stagnation_exit',lambda *a,**k:None)
    monkeypatch.setattr(handlers,'_observe_post_probe_hard_abort_recovery',lambda *a,**k:None)
    monkeypatch.setattr(handlers,'LAST_AI_CALL_TIMES',{'005930':at})
    def existing_quote_context(stock,code,**kwargs):
        handlers._prepare_main_stop_limit_up_quote(stock,code,ws_data=ws,
            quote_fields={'quote_consistency_state':'consistent'},now_ts=at,
            profit_rate=kwargs['holding_profit_rate_at_eval'])
    monkeypatch.setattr(handlers,'_observe_scalp_trailing_input_transition_safe',existing_quote_context)
    original=handlers._observe_main_stop_evaluation
    class GateReached(Exception):pass
    def observed(*args,**kwargs):
        result=original(*args,**kwargs)
        assert result is not None
        raise GateReached()
    monkeypatch.setattr(handlers,'_observe_main_stop_evaluation',observed)
    with pytest.raises(GateReached):
        handlers.handle_holding_state(stock,'005930',ws,None,'BULL',now_ts=at)
    event=captured[-1]
    assert event['stage']=='common_soft' and event['evaluator']=='normal'
    assert event['decision_price']==mark and event['decision_price_basis']=='mark_price'
    assert (event['decision_profit_pct']<=-3)==(mark==9650)
    assert event['preset_predecessor'] is None


def test_four_order_256_native_execution_proof_fits_each_envelope_without_nested_predecessor(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts
    from src.engine.scalping.main_stop_runtime_source import evaluation_reference
    qty=256
    stock=dict(id=101,code='005930',strategy='SCALPING',entry_requested_qty=qty,requested_buy_qty=qty,
        pending_entry_orders=[dict(ord_no=f'000012{i}',qty=64,filled_qty=0,status='OPEN') for i in range(4)])
    for index in range(4):
        for cumulative in range(1,65):
            result=receipts._resolve_entry_effective_fill_qty(target_stock=stock,code='005930',
                order_no=f'000012{index}',exec_price=10000,exec_qty=cumulative,order_qty=64,
                remaining_qty=64-cumulative,cumulative_exec_amount=10000*cumulative,
                execution_no=f'E{cumulative}',unit_exec_qty=1,unit_exec_price=10000)
            assert result['status']!='invalid'
    stock.update(buy_qty=qty,buy_price=10000.,status='HOLDING')
    stock['main_stop_policy_pin']=policy.pin(position_key=position_cycle_id(stock),
        role='SCALP_PRESET_TP',market='REGULAR',target='2026-10-16',baseline=policy.StopValues(-3.,60,20,8,3,.67,1.,-5.,-4.,-2.,-.3))
    preset=policy.preset_stop_receipt(stock,at=1000.,evaluator='normal',hard_pct=-1.4,
        emergency_pct=-2.4,grace_sec=0,held_sec=5,enabled=True)
    quote=research_quote(stock,at=1000.,bid=9950,profit=-.5,preset=preset)
    actual_preset=research_evaluation(stock,quote,stage='preset_safety',preset=preset)
    common=research_evaluation(stock,quote,predecessor=actual_preset)
    assert quote['quantity_source']['status']=='full_fill'
    assert common['quantity_source']['status']=='full_fill'
    assert common['preset_predecessor']==evaluation_reference(actual_preset)
    assert len(json.dumps(common['preset_predecessor']))<600
    encoded=[]
    def sink(fn,*args,**kwargs):
        encoded.append(args[-1]);return {'status':'queued'}
    monkeypatch.setattr(policy,'_SOURCE_SINK',sink)
    for receipt in (quote,actual_preset,common):
        body={k:v for k,v in receipt.items() if k!='source_sha256'}
        assert policy.enqueue_source(stock,'005930',body)
    assert all(isinstance(row,str) and len(row.encode())<=65536 for row in encoded)
    assert len(encoded)==3
    # Over-budget payloads are rejected explicitly without truncating evidence.
    oversized=dict(body,unexpected_payload='x'*65536)
    assert policy.enqueue_source(stock,'005930',oversized) is False and len(encoded)==3


def test_quantity_reference_reuses_existing_proof_only_after_current_generation_validation():
    from src.engine.scalping.main_stop_runtime_source import resolve_quantity_source
    stock=stage_stock()
    quote=research_quote(stock,at=1000.,bid=9950,profit=-.5)
    event=research_evaluation(stock,quote,at=1000.2)
    ref=event['quantity_source']
    assert ref['schema']=='main_stop_quantity_reference_v1' and 'proof' not in ref
    assert resolve_quantity_source(ref,quote,at=1000.2)==quote['quantity_source']
    for field,value in [('quantity_source_sha256','b'*64),('generation_sha256','c'*64),('observed_at',1000.3)]:
        forged=dict(ref,**{field:value})
        forged['source_sha256']=policy.digest({k:v for k,v in forged.items() if k!='source_sha256'})
        with pytest.raises(ValueError,match='reference_unbound'):
            resolve_quantity_source(forged,quote,at=1000.2)
    stock['pending_entry_orders'].append(dict(ord_no='0000456',qty=1,filled_qty=0,status='OPEN'))
    event=research_evaluation(stock,quote,at=1000.3)
    assert event['quantity_source']['schema']=='main_stop_quantity_source_v1'
    assert event['quantity_source']['status']=='unknown'


def test_actual_mark_gate_with_missing_quote_is_preserved_without_executable_evidence(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    stock=stage_stock()
    captured=[]
    monkeypatch.setattr(policy,'enqueue_source',lambda stock,code,row:captured.append(deepcopy(row)) or True)
    monkeypatch.setattr(handlers,'_is_scalp_simulated_position',lambda *a:False)
    event=handlers._observe_main_stop_evaluation(stock,'005930',at=1000.,evaluator='normal',
        stage='common_soft',decision_price=9950.,decision_price_basis='mark_price',
        decision_profit_pct=-.5,decision_inputs=stage_inputs())
    assert event['quote_binding_status']=='source_gap'
    assert event['decision_price']==9950. and event['at']==1000.
    assert event['quote_at'] is None and captured[0]['bid'] is None
    assert captured[0]['coverage_complete'] is False
    assert event['capture_rejected_count']==event['evaluation_rejected_count']==0
    assert not stock.get('main_stop_evaluation_source_gap')


def test_same_clock_native_quote_and_stage_order_has_one_shared_generation(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    stock=stage_stock()
    captured=[]
    monkeypatch.setattr(policy,'enqueue_source',lambda stock,code,row:captured.append(deepcopy(row)) or True)
    monkeypatch.setattr(handlers,'_is_scalp_simulated_position',lambda *a:False)
    monkeypatch.setattr(handlers,'_main_stop_preset_observation',lambda *a,**k:None)
    for index in range(5):
        bid=9950-index
        stock['_main_stop_current_quote_context']=dict(at=1000.,bid=bid,bid_qty=100,
            quote=dict(item='005930_AL',market_route='krx_nxt_integrated',transport_epoch=1,observed_epoch=1000.),
            complete=True,market='REGULAR',evaluator='normal',position_key=position_cycle_id(stock),
            quantity=10,buy_price=10000.,pending_exit=False,quote_max_age_sec=3.,
            decision_profit_pct=(bid/10000.-1)*100)
        event=handlers._observe_main_stop_evaluation(stock,'005930',at=1000.,evaluator='normal',
            stage='common_soft',decision_price=bid,decision_price_basis='executable_bid',
            decision_profit_pct=(bid/10000.-1)*100,decision_inputs=stage_inputs())
        assert event and event['quote_source_sha256']==policy.digest(captured[-2])
    assert [row['source_observation_generation'] for row in captured]==list(range(1,11))
    assert [row['schema'] for row in captured]==['main_stop_source_v1','main_stop_evaluation_source_v1']*5
    assert len({row['quote_id'] for row in captured[::2]})==5


def test_native_revive_resets_only_completed_cycle_source_state(monkeypatch):
    from src.engine import sniper_execution_receipts as receipts
    stock=stage_stock()
    quote=research_quote(stock,at=1000.,bid=9950,profit=-.5)
    first=research_evaluation(stock,quote)
    stock.update(main_stop_evaluation_rejected_count=1,main_stop_evaluation_source_gap='native_evaluation_queue_rejected',
        _main_stop_quantity_source=deepcopy(quote['quantity_source']),
        _main_stop_last_quote_source=quote,_main_stop_normal_preset_evaluation={'old':True},
        _main_stop_current_quote_context={'old':True},_main_stop_last_captured_quote=('old',),
        _main_stop_quote_context_by_evaluator={'normal': {'old': True}, 'fast': {'old': True}},
        _main_stop_observation_epoch=23,
        _main_stop_normal_exit_observation={'old': True},
        _main_stop_evaluation_lane_generations={'normal': 1, 'fast': 2},
        main_stop_source_superseded_rejected_count=9,
        main_stop_source_superseded_rejection={'record_id': 'prior-cycle'},
        main_stop_quantity_restore_source={'old':True},main_stop_quantity_source_gap='old',
        main_stop_quantity_restore_status='terminal_quantity_source_restored')
    # Ordinary observations never erase a loss within the still-open cycle.
    second=research_evaluation(stock,quote,at=1000.2)
    assert second['evaluation_rejected_count']==1 and second['evaluation_generation']==2
    assert set(stock['_main_stop_quote_context_by_evaluator']) == {'normal', 'fast'}
    assert stock['_main_stop_observation_epoch'] == 23
    assert stock['_main_stop_normal_exit_observation'] == {'old': True}
    assert stock['_main_stop_evaluation_lane_generations']['fast'] == 2
    old_cycle=position_cycle_id(stock)
    stock['historical_custody_receipt']={'original_owner':'Main','cycle':old_cycle}
    monkeypatch.setattr(receipts.POSITION_PEAK_LEDGER,'remove_for_stock',lambda stock:None)
    monkeypatch.setattr(receipts,'highest_prices',{})
    monkeypatch.setattr(receipts,'move_orders_to_terminal',lambda *a,**k:None)
    receipts._apply_scalp_revive_memory_state(target_stock=stock,code='005930',new_watch_id=102,
        revived_position_tag='SCANNER',revived_at_ts=1001.)
    assert {key for key in stock if key.startswith('_main_stop') or key.startswith('main_stop_')} == {
        'main_stop_source_superseded_rejected_count', 'main_stop_source_superseded_rejection'}
    assert stock['main_stop_source_superseded_rejected_count'] == 9
    assert stock['main_stop_source_superseded_rejection'] == {'record_id': 'prior-cycle'}
    assert stock['historical_custody_receipt']['cycle']==old_cycle
    assert set(receipts._POSITION_PEAK_RESET_KEYS)<=set(receipts._SELL_COMPLETE_RESET_KEYS)
    assert set(receipts._POSITION_PEAK_RESET_KEYS)<=set(receipts._SELL_REVIVE_RESET_KEYS)
    # The next native BUY producer establishes a fresh position and source ID.
    stock.update(stage_stock(record=102))
    current_quote=research_quote(stock,at=1002.,bid=9950,profit=-.5)
    current=research_evaluation(stock,current_quote)
    assert current['position_key']!=first['position_key']
    assert current['evaluation_generation']==1 and current['evaluation_rejected_count']==0
    assert current_quote['source_observation_generation']==1
    assert current['source_observation_generation']==2


def test_native_preset_uses_current_handoff_flag_instead_of_shared_quote(monkeypatch):
    from src.engine.scalping.main_stop_runtime_source import ensure_observation_epoch, observation_source_identity
    from src.engine import sniper_state_handlers as handlers
    stock=stage_stock(role='SCALP_PRESET_TP')
    ensure_observation_epoch(stock)
    quote=research_quote(stock,at=1000.,bid=9800,profit=-2.)
    quote.update(observation_source_identity(stock))
    quote['source_sha256']=policy.digest({k:v for k,v in quote.items() if k!='source_sha256'})
    stock['_main_stop_last_quote_source']=quote
    stock['_main_stop_current_quote_context']=dict(at=1000.2,bid=9800,bid_qty=100,
        quote=dict(item=quote['item'],market_route=quote['route'],transport_epoch=1,observed_epoch=1000.),
        complete=True,market='REGULAR',evaluator='normal',position_key=position_cycle_id(stock),
        quantity=10,buy_price=10000.,pending_exit=False,quote_max_age_sec=3.)
    monkeypatch.setattr(policy,'enqueue_source',lambda *a:True)
    event=handlers._observe_main_stop_preset_evaluation(stock,'005930',at=1000.2,evaluator='normal',
        decision_price=9800,decision_price_basis='mark_price',profit_rate=-2.,
        hard_pct=-1.4,emergency_pct=-2.4,grace_sec=0,held_sec=20,handoff_enabled=True)
    assert event['quote_source_sha256']==quote['source_sha256']
    assert quote['handoff_enabled'] is False and event['decision_inputs']['handoff_enabled'] is True


def test_observation_view_matches_native_producers_and_detaches_only_consumed_state():
    import os
    from datetime import date
    from src.engine.ai.holding_exit_vote import buy_fill_identity_from_runtime
    from src.engine.ai.holding_vote_replay_source import runtime_source
    from src.engine.scalping.main_stop_quantity_source import build_quantity_source
    from src.engine.scalping.main_stop_runtime_source import observation_view, bounded_observation_copy
    stock = stage_stock()
    original_quote = research_quote(stock, at=1000., bid=9950, profit=-.5)
    stock.update(_main_stop_quantity_source=original_quote['quantity_source'],
        holding_vote_coverage_pid=os.getpid(), holding_vote_coverage_started_at=900.,
        holding_vote_coverage_checked_at=1000., holding_vote_coverage_birth_at=900.,
        holding_vote_coverage_generation=buy_fill_identity_from_runtime(stock),
        holding_path_vote_ledger=[{'persisted_at': 990., 'original_ai': {'response': ['unchanged']}}, {}],
        buy_time=datetime(2026, 10, 12, 9), unrelated_unbounded_state=object())
    ledger = deepcopy(stock['holding_path_vote_ledger'])
    view = observation_view(stock)
    assert 'unrelated_unbounded_state' not in view
    assert view['holding_path_vote_ledger'] == [{'persisted_at': 990.}, {}]
    assert build_quantity_source(view, at=1001.) == build_quantity_source(stock, at=1001.)
    assert research_quote(view, at=1001., bid=9940, profit=-.6) == research_quote(
        deepcopy({k: v for k, v in stock.items() if k != 'unrelated_unbounded_state'}),
        at=1001., bid=9940, profit=-.6)
    args = dict(position_key='record:101', buy_fill_identity=buy_fill_identity_from_runtime(stock),
        market='REGULAR', now=1001., policy={'original': True}, data_root='unused', model='original')
    assert runtime_source(view, **args) == runtime_source(stock, **args)
    stock['_entry_receipt_executions_by_order_no']['0000123']['E1']['cumulative_qty'] = 999
    stock['main_stop_policy_pin']['role'] = 'changed'
    stock['holding_path_vote_ledger'][0]['persisted_at'] = 2000.
    assert view['_entry_receipt_executions_by_order_no']['0000123']['E1']['cumulative_qty'] == 10
    assert view['main_stop_policy_pin']['role'] == 'SCANNER'
    assert view['holding_path_vote_ledger'][0]['persisted_at'] == 990.
    assert ledger[0]['original_ai'] == stock['holding_path_vote_ledger'][0]['original_ai']
    values = policy.StopValues(-3., 60, 20, 8, 3, .67, 1., -5., -4., -2., -.3)
    immutable = (values, date(2026, 10, 12), datetime(2026, 10, 12, 9))
    copied = bounded_observation_copy(immutable)
    assert all(a is b for a, b in zip(immutable, copied))


def test_observation_view_retains_native_quantity_pending_veto_without_inference():
    from src.engine.scalping.main_stop_quantity_source import build_quantity_source
    from src.engine.scalping.main_stop_runtime_source import observation_view
    stock = stage_stock()
    stock['pending_add_order'] = {'qty': 1, 'status': 'OPEN'}
    original = deepcopy(stock)
    result = build_quantity_source(observation_view(stock), at=1000.)
    assert result == build_quantity_source(stock, at=1000.)
    assert result['status'] == 'unknown' and result['proof'] is None
    assert stock == original


def test_observation_view_covers_actual_source_read_keys():
    import ast
    import inspect
    import textwrap
    from src.engine import sniper_state_handlers as handlers
    from src.engine.sniper_scale_in import resolve_holding_elapsed_sec
    from src.engine.ai.holding_vote_replay_source import runtime_source
    from src.engine.scalping import main_stop_quantity_source as quantity
    from src.engine.scalping.main_stop_runtime_source import SOURCE_VIEW_KEYS

    functions = (policy.source_row, policy.protect_line_origin, policy.preset_stop_receipt,
        evaluation_source, quantity.build_quantity_source, quantity._pending,
        position_cycle_id, runtime_source, resolve_holding_elapsed_sec,
        handlers._main_stop_preset_observation, handlers._is_scalp_simulator_target,
        handlers._scalp_holding_source_position_key)
    consumed = set()
    for function in functions:
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'stock'
                    and node.func.attr == 'get' and node.args
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                consumed.add(node.args[0].value)
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name) and node.func.value.id == 'stock'
                    and node.func.attr == 'get' and node.args and isinstance(node.args[0], ast.Name)):
                for generator in (entry for entry in ast.walk(tree) if isinstance(entry, ast.comprehension)):
                    if (isinstance(generator.target, ast.Name) and generator.target.id == node.args[0].id
                            and isinstance(generator.iter, (ast.Tuple, ast.List))):
                        consumed.update(element.value for element in generator.iter.elts
                            if isinstance(element, ast.Constant) and isinstance(element.value, str))
    # Dynamic-key consumers are explicit native contracts, rather than inferred
    # solely from literal .get calls in the AST above.
    consumed.update(quantity.FILL_KEYS)
    consumed.add(quantity.RETAINED_KEY)
    consumed.update(f'_{prefix}_receipt_{kind}_by_order_no'
        for prefix in ('entry', 'add') for kind in ('filled', 'executions'))
    consumed.update(f'{prefix}_filled_qty' for prefix in ('entry', 'add'))
    assert consumed <= SOURCE_VIEW_KEYS, sorted(consumed - SOURCE_VIEW_KEYS)
    # Handler input views also consume local lifecycle facts. Their live source
    # cache is intentionally captured separately and is not part of this view.
    for function in (handlers._capture_main_stop_observation, handlers._observe_main_stop_evaluation):
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        consumed = {node.args[0].value for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name) and node.func.value.id == 'view'
            and node.func.attr == 'get' and node.args and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)}
        assert consumed <= SOURCE_VIEW_KEYS, sorted(consumed - SOURCE_VIEW_KEYS)


@pytest.mark.parametrize('value', [float('nan'), float('inf'), object(), {1: 'bad'},
    {'x' * 241: 1}, ['x'] * 257, 'x' * 1025])
def test_bounded_observation_copy_rejects_invalid_or_unbounded_values(value):
    from src.engine.scalping.main_stop_runtime_source import bounded_observation_copy
    with pytest.raises(ValueError, match='native_observation_'):
        bounded_observation_copy(value)


def test_observation_admission_bounds_depth_nodes_total_bytes_and_native_vote_tail():
    from src.engine.scalping.main_stop_runtime_source import bounded_observation_copy, observation_view
    deep = None
    for _ in range(18):
        deep = [deep]
    with pytest.raises(ValueError, match='budget_exceeded'):
        bounded_observation_copy(deep)
    with pytest.raises(ValueError, match='budget_exceeded'):
        bounded_observation_copy([[None] * 256 for _ in range(33)])
    with pytest.raises(ValueError, match='budget_exceeded'):
        bounded_observation_copy(['\U0001f600' * 1024 for _ in range(24)])
    ledger = [dict(persisted_at=float(i), original_ai={'not_copied': object()}) for i in range(192)]
    projected = observation_view({'holding_path_vote_ledger': ledger})
    assert len(projected['holding_path_vote_ledger']) == 192
    assert projected['holding_path_vote_ledger'][-1] == {'persisted_at': 191.}
    with pytest.raises(ValueError, match='vote_ledger_invalid'):
        observation_view({'holding_path_vote_ledger': ledger + [{}]})
    # Independently admissible fields share one aggregate 256 KiB budget.
    with pytest.raises(ValueError, match='budget_exceeded'):
        observation_view({'last_reversal_features': ['x' * 1024] * 180,
            '_trailing_entry_cost_model': ['x' * 1024] * 180})


@pytest.mark.parametrize('bad', [True, 1., '1', -1])
@pytest.mark.parametrize('key', ['_main_stop_quote_generation', '_main_stop_evaluation_generation',
    '_main_stop_source_observation_generation'])
def test_generation_reservation_rejects_all_invalid_live_counters_atomically(key, bad):
    from src.engine.scalping.main_stop_runtime_source import reserve_observation_generations
    live, view = {key: bad}, {'original': [1]}
    originals = deepcopy((live, view))
    with pytest.raises(ValueError, match='generation_invalid'):
        reserve_observation_generations(live, view, quote=True)
    assert (live, view) == originals


@pytest.mark.parametrize('kwargs', [{}, {'quote': True, 'evaluation': True}, {'quote': 1},
    {'evaluation': 'yes'}, {'quote': True, 'minimum': True}, {'quote': True, 'minimum': -1}])
def test_generation_reservation_rejects_ambiguous_calls_atomically(kwargs):
    from src.engine.scalping.main_stop_runtime_source import reserve_observation_generations
    live, view = {}, {'original': [1]}
    with pytest.raises(ValueError, match='reservation_invalid'):
        reserve_observation_generations(live, view, **kwargs)
    assert live == {} and view == {'original': [1]}


def test_reserved_generations_remain_unique_when_native_builders_finish_in_reverse_order():
    from threading import Lock
    from concurrent.futures import ThreadPoolExecutor
    from src.engine.scalping.main_stop_runtime_source import observation_view, reserve_observation_generations
    live = stage_stock()
    lock = Lock()
    def reserve(_):
        with lock:
            view = observation_view(live)
            reservation = reserve_observation_generations(live, view, quote=True)
        return view, reservation
    with ThreadPoolExecutor(max_workers=2) as pool:
        views = list(pool.map(reserve, range(8)))
    rows = [research_quote(view, at=1000., bid=9950, profit=-.5) for view, _ in reversed(views)]
    assert sorted(row['quote_generation'] for row in rows) == list(range(1, 9))
    assert sorted(row['source_observation_generation'] for row in rows) == list(range(1, 9))
    assert len({row['quote_id'] for row in rows}) == 8
    assert live['_main_stop_quote_generation'] == 8
    with lock:
        view = observation_view(live)
        reserved = reserve_observation_generations(live, view, evaluation=True, minimum=20)
    event = research_evaluation(view, rows[0])
    assert event['evaluation_generation'] == reserved['_main_stop_evaluation_generation'] == 1
    assert event['source_observation_generation'] == reserved['_main_stop_source_observation_generation'] == 21
    assert live['_main_stop_source_observation_generation'] == 21
    # Reserved but failed work leaves an observable gap; it is never reused.
    with lock:
        reserve_observation_generations(live, observation_view(live), evaluation=True)
        next_view = observation_view(live)
        reserve_observation_generations(live, next_view, evaluation=True)
    assert research_evaluation(next_view, rows[0])['evaluation_generation'] == 3


def test_observation_epoch_distinguishes_same_identity_lifecycle_reset():
    from src.engine.scalping.main_stop_runtime_source import ensure_observation_epoch, observation_view
    stock = stage_stock()
    first = ensure_observation_epoch(stock)
    frozen = observation_view(stock)
    assert ensure_observation_epoch(stock) == first
    second_stock = stage_stock()
    second = ensure_observation_epoch(second_stock)
    assert second > first and position_cycle_id(second_stock) == position_cycle_id(stock)
    stock.pop('_main_stop_observation_epoch')  # Native reset owns this removal.
    renewed = ensure_observation_epoch(stock)
    assert renewed > second
    assert frozen['_main_stop_observation_epoch'] == first
    assert frozen['main_stop_policy_pin'] == stock['main_stop_policy_pin']


@pytest.mark.parametrize('invalid', [True, False, 0, -1, 1., '1', None])
def test_observation_epoch_rejects_corrupted_ticket_without_replacing_it(invalid):
    from src.engine.scalping.main_stop_runtime_source import ensure_observation_epoch
    stock = {'_main_stop_observation_epoch': invalid}
    with pytest.raises(ValueError, match='native_observation_epoch_invalid'):
        ensure_observation_epoch(stock)
    assert stock == {'_main_stop_observation_epoch': invalid}


def test_native_lane_reservation_preserves_global_ids_and_exact_two_actor_vector():
    from src.engine.scalping.main_stop_runtime_source import (ensure_observation_epoch,
        observation_view, reserve_observation_generations, reserve_evaluation_lane,
        observation_source_identity)
    stock=stage_stock();ensure_observation_epoch(stock)
    identity=observation_source_identity(stock)
    records=[]
    for owner in ('fast','normal','normal','fast'):
        view=observation_view(stock)
        reserve_observation_generations(stock,view,evaluation=True)
        receipt=reserve_evaluation_lane(stock,view,owner)
        assert sum(receipt['evaluation_lane_generations'].values())==stock['_main_stop_evaluation_generation']
        assert all(receipt[key]==value for key,value in identity.items())
        records.append(receipt)
    assert [row['evaluation_lane_generation'] for row in records]==[1,1,2,2]
    assert records[0]['evaluation_lane_generations']=={'normal':0,'fast':1}
    assert stock['_main_stop_evaluation_lane_generations']=={'normal':2,'fast':2}


@pytest.mark.parametrize('bad', [{}, {'normal':True,'fast':0}, {'normal':0,'fast':-1},
    {'normal':0,'fast':0,'unknown':0}, {'normal':1.,'fast':0}])
def test_native_lane_bad_map_is_rejected_without_mutation(bad):
    from src.engine.scalping.main_stop_runtime_source import (ensure_observation_epoch,
        observation_view,reserve_evaluation_lane)
    stock=stage_stock();ensure_observation_epoch(stock)
    stock['_main_stop_evaluation_generation']=1
    stock['_main_stop_evaluation_lane_generations']=bad
    view=observation_view(stock);before=deepcopy((stock,view))
    with pytest.raises(ValueError,match='lane_generation_invalid'):
        reserve_evaluation_lane(stock,view,'normal')
    assert (stock,view)==before


def test_native_lane_never_relabels_an_unobserved_legacy_global_prefix():
    from src.engine.scalping.main_stop_runtime_source import (ensure_observation_epoch,
        observation_view,reserve_evaluation_lane)
    stock=stage_stock();ensure_observation_epoch(stock)
    stock['_main_stop_evaluation_generation']=3
    view=observation_view(stock);before=deepcopy((stock,view))
    with pytest.raises(ValueError,match='lane_global_generation_unbound'):
        reserve_evaluation_lane(stock,view,'normal')
    assert (stock,view)==before
