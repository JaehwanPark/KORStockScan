"""Producer-shaped regressions for identified stop research comparisons."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timezone
import json
from types import SimpleNamespace

import pytest

from src.engine.scalping import main_stop_policy as policy
from src.engine.scalping import main_stop_replay as replay
from src.engine.scalping import holding_vote_exit_models as add_models
from src.engine.scalping.position_peak_ledger import position_cycle_id


@pytest.fixture(autouse=True)
def isolated_policy(monkeypatch):
    monkeypatch.setattr(policy, '_LOADED', None)


def baseline():
    return policy.StopValues(-3., 60, 20, 8, 3, .67, 1., -5., -4., -2., -.3)


def seal(value, key='source_sha256'):
    value[key] = policy.digest({k: v for k, v in value.items() if k != key})
    return value


def observations(profits=(-.1, -3.2, -.2, .5), *, role='SCANNER', preset_enabled=True,
                 preset_hard=-1.4, preset_grace=0):
    at = datetime(2026, 10, 16, 0, tzinfo=timezone.utc).timestamp()
    stock = dict(id=10, code='005930', strategy='SCALPING', position_tag='SCANNER',
                 buy_price=10000., buy_qty=10)
    stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
        role=role, market='REGULAR', target='2026-10-16', baseline=baseline())
    result = []
    for i, profit in enumerate(profits):
        stamp = at + i
        preset = None if role != 'SCALP_PRESET_TP' else policy.preset_stop_receipt(stock,
            at=stamp, evaluator='normal', hard_pct=preset_hard, grace_sec=preset_grace,
            emergency_pct=-4.5, held_sec=i+1, enabled=preset_enabled)
        result.append(policy.source_row(stock, at=stamp, bid=10000*(1+profit/100),
            bid_qty=20, quote=dict(market_route='KRX', item='005930', transport_epoch=1,
                observed_epoch=stamp), coverage_complete=True,
            automatic_management_allowed=True, decision_profit_pct=profit,
            cost_model=dict(buy_cost_krw=0., sell_cost_rate=.0023, known_at=at-1,
                source_sha256='a'*64, actual_broker_cost=False), vote_source=None,
            runtime_flags=dict(grace_enabled=True, protect_enabled=True,
                handoff_enabled=False, vote_max_worsen_pct=.8), preset_stop=preset))
    return result


def normal_terminal(rows, *, kind='observed_normal_exit'):
    first, last = rows[0], rows[-1]
    reference = dict(path='verified/native_terminal.json', sha256='b'*64)
    receipt = seal(dict(record_id=last['record_id'], position_key=last['position_key'],
        quantity=last['quantity'], decision_at=last['at'], decision_price=last['bid'],
        exit_rule='scalp_trailing_take_profit', status='COMPLETED',
        main_automatic_management_allowed=False, decision_automatic_management_allowed=True,
        seller_attribution_basis='native_main_decision_same_order_generation',
        executable_bid=last['bid'], decision_price_basis='executable_bid', partial_fill=False, add_count=0,
        source_sha256=reference['sha256']), 'sha256')
    value = {key: last[key] for key in ('position_key', 'record_id', 'pin_sha256', 'role',
        'market', 'item', 'route', 'transport_epoch', 'quantity', 'buy_basis_krw')}
    value.update(schema='main_stop_terminal_outcome_v1', kind=kind,
        first_source_sha256=first['source_sha256'], last_source_sha256=last['source_sha256'],
        at=last['at'], price=last['bid'], cost_source_sha256=last['cost_model']['source_sha256'],
        owner='main', automatic_management_allowed=True, manual=False, pending_add=False,
        partial_fill=False, add_count=0, source_reference=reference, receipt_binding=receipt,
        exit_rule=receipt['exit_rule'])
    return seal(value)


def test_recovery_and_earlier_stop_remain_in_same_identified_cohort():
    rows = observations()
    endpoint = normal_terminal(rows)
    prior = replay.replay(rows, baseline(), terminal_outcome=endpoint)
    early = replay.replay(rows, replace(baseline(), grace_sec=0), terminal_outcome=endpoint)
    assert prior['status'] == early['status'] == 'modeled'
    assert prior['reason'] == 'observed_normal_exit_endpoint'
    assert early['reason'] == 'scalp_soft_stop_pct'
    assert prior['modeled_net_krw'] > 0 > early['modeled_net_krw']
    assert prior['actual_realized_net_krw'] is None
    assert prior['terminal_source_sha256'] == endpoint['source_reference']['sha256']
    assert replay.replay(rows, baseline())['status'] == 'censored'


def native_terminal_case(tmp_path, *, decision_second=3):
    from src.tests import test_main_stop_research_cost as cost_fixture
    stock = dict(id=1, code='005930', strategy='SCALPING', buy_qty=2, buy_price=10000.)
    at = datetime.fromisoformat(cost_fixture.DAY + 'T10:00:00+09:00').timestamp()
    stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
        role='SCANNER', market='REGULAR', target=cost_fixture.DAY, baseline=baseline())
    rows = []
    for i, profit in enumerate((-.1, -3.2, -.2, .5)):
        stamp = at + (decision_second if i == 3 else i)
        rows.append(policy.source_row(stock, at=stamp, bid=10000*(1+profit/100), bid_qty=2,
            quote=dict(market_route='SOR', item='005930', transport_epoch=1, observed_epoch=stamp),
            coverage_complete=True, automatic_management_allowed=True, decision_profit_pct=profit,
            cost_model=dict(buy_cost_krw=0., sell_cost_rate=.0023, known_at=at-1,
                source_sha256='a'*64, actual_broker_cost=False), vote_source=None,
            runtime_flags=dict(grace_enabled=True, protect_enabled=True,
                handoff_enabled=False, vote_max_worsen_pct=.8)))
    decision = policy.normal_exit_decision_source(stock, at=rows[-1]['at'], price=rows[-1]['bid'],
        executable_bid=rows[-1]['bid'], mark_price=rows[-1]['bid']+1, exit_rule='scalp_trailing_take_profit')
    def native_exit(row):
        if row['id'] == 1:
            row['exit_signal'].update(exit_rule=decision['exit_rule'], exit_decision_source='TRAILING')
            fields = row['exit_signal']['fields']
            fields['main_stop_normal_exit_decision'] = json.dumps(decision)
            fields['exit_signal_contract']['exit_rule'] = decision['exit_rule']
            fields['exit_signal_contract']['signal_at'] = datetime.fromtimestamp(decision['decision_at'], timezone.utc).astimezone(__import__('zoneinfo').ZoneInfo('Asia/Seoul')).isoformat()
            if decision_second >= 60:
                row['exit_signal']['submission']['submitted_at'] = cost_fixture.DAY + ' 10:01:00'
            fields['exit_signal_contract_sha256'] = policy.digest(fields['exit_signal_contract'])
    data, costs, _, _, _ = cost_fixture.setup(tmp_path, mutate=native_exit)
    economic = cost_fixture.result(data, costs, cost_fixture.prepare(data, costs))
    assert economic['status'] == 'eligible', economic['reason']
    return stock, rows, economic


def test_native_decision_and_cost_overlay_bind_recovery_without_actual_profit_claim(tmp_path):
    _, rows, economic = native_terminal_case(tmp_path)
    endpoint = replay.normal_exit_terminal_outcome(first_row=rows[0], last_row=rows[-1], economic=economic)
    prior = replay.replay(rows, baseline(), terminal_outcome=endpoint)
    early = replay.replay(rows, replace(baseline(), grace_sec=0), terminal_outcome=endpoint)
    assert prior['status'] == early['status'] == 'modeled'
    assert prior['modeled_net_krw'] > 0 > early['modeled_net_krw']
    assert prior['actual_realized_net_krw'] is None
    changed_cost = deepcopy(economic)
    changed_cost.update(research_cost_krw=999, research_net_pnl_krw=-799, cost_receipt_sha256='d'*64)
    seal(changed_cost, 'artifact_sha256')
    assert replay.normal_exit_terminal_outcome(first_row=rows[0], last_row=rows[-1], economic=changed_cost) == endpoint


@pytest.mark.parametrize('fault', ['missing_decision', 'decision_clock', 'decision_price', 'pin',
    'custody', 'quantity', 'manual', 'status', 'management', 'basis', 'unsealed_cost'])
def test_native_endpoint_rejects_missing_or_different_decision_and_completion(tmp_path, fault):
    _, rows, cost = native_terminal_case(tmp_path)
    native = cost['terminal_observation']
    fields = native['exit_signal']['fields']
    decision = json.loads(fields['main_stop_normal_exit_decision'])
    if fault == 'missing_decision': fields.clear()
    elif fault in {'decision_clock', 'decision_price', 'pin'}:
        key = {'decision_clock':'decision_at', 'decision_price':'decision_price', 'pin':'pin_sha256'}[fault]
        decision[key] = 'e'*64 if fault == 'pin' else decision[key]+1
        fields['main_stop_normal_exit_decision'] = json.dumps(seal(decision))
    elif fault == 'custody': cost['custody_status'] = 'unverified'
    elif fault == 'quantity': cost['quantity_basis']['sell_qty'] = 1
    elif fault == 'manual': cost['manual_exit'] = True
    elif fault == 'status': native['status'] = 'HOLDING'
    elif fault == 'management':
        decision['automatic_management_allowed'] = False
        fields['main_stop_normal_exit_decision'] = json.dumps(seal(decision))
    elif fault == 'basis': native['buy_fill_legs'][0]['price'] += 1
    if fault != 'unsealed_cost': seal(cost, 'artifact_sha256')
    else: cost['research_cost_krw'] = 999
    with pytest.raises(ValueError):
        replay.normal_exit_terminal_outcome(first_row=rows[0], last_row=rows[-1], economic=cost)


@pytest.mark.parametrize('fault', [None, 'pin', 'manual', 'simulated', 'observer_failure', 'capture_failure'])
def test_dispatch_records_normal_decision_without_interfering_with_existing_exit(monkeypatch, fault):
    from src.engine import sniper_state_handlers as handlers
    rows = observations()
    stock = dict(id=10, code='005930', strategy='SCALPING', buy_price=10000., buy_qty=10)
    stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
        role='SCANNER', market='REGULAR', target='2026-10-16', baseline=baseline())
    if fault == 'pin': stock['main_stop_policy_pin']['pin_sha256'] = 'invalid'
    if fault == 'manual': stock['manual_control_exclusion_blocked'] = True
    if fault == 'observer_failure':
        def broken(*args, **kwargs): raise RuntimeError('observation_failed')
        monkeypatch.setattr(policy, 'normal_exit_decision_source', broken)
    stock['_main_stop_current_quote_context'] = dict(at=rows[-1]['at'], bid=rows[-1]['bid'], complete=True)
    monkeypatch.setattr(handlers, '_capture_main_stop_observation', lambda *a, **k: fault != 'capture_failure')
    logs = []
    monkeypatch.setattr(handlers, '_remember_exit_context', lambda **kwargs: None)
    monkeypatch.setattr(handlers, '_resolve_holding_elapsed_sec', lambda *args, **kwargs: 3.)
    monkeypatch.setattr(handlers, '_is_scalp_simulated_position', lambda *args: fault == 'simulated')
    monkeypatch.setattr(handlers, '_complete_scalp_simulated_sell', lambda **kwargs: logs.append(('simulated', {})))
    monkeypatch.setattr(handlers, '_mutate_stock_state', lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, '_log_holding_pipeline', lambda stock, code, stage, **kw: logs.append((stage,kw)))
    handlers._dispatch_scalp_preset_exit(stock=stock, code='005930', now_ts=rows[-1]['at'],
        curr_p=rows[-1]['bid'], buy_p=10000., profit_rate=.5, peak_profit=.8, strategy='SCALPING',
        sell_reason_type='PROFIT', reason='already decided', exit_rule='scalp_trailing_take_profit', fast_exit=True)
    signal = logs[0][1]
    assert logs[-1][0] == ('simulated' if fault == 'simulated' else 'scalp_fast_exit_deferred_for_reconciliation')
    if fault is None:
        receipt = json.loads(signal['main_stop_normal_exit_decision'])
        assert receipt['decision_at'] == rows[-1]['at'] and receipt['decision_price'] == rows[-1]['bid']
        assert receipt['status'] == 'decision_observed' and receipt['actual_order_submitted'] is False
    else:
        assert 'main_stop_normal_exit_decision' not in signal and signal['main_stop_normal_exit_decision_gap']


@pytest.mark.parametrize('change', ['position', 'last_source', 'future_clock', 'different_price',
    'quantity', 'manual', 'add', 'partial', 'source_reference', 'receipt', 'exit_rule'])
def test_normal_endpoint_rejects_unbound_or_unidentified_lifecycle(change):
    rows = observations()
    value = normal_terminal(rows)
    if change == 'position': value['position_key'] = 'unrelated'
    elif change == 'last_source': value['last_source_sha256'] = 'c'*64
    elif change == 'future_clock': value['at'] += 1
    elif change == 'different_price': value['price'] += 1
    elif change == 'quantity': value['quantity'] += 1
    elif change == 'manual': value['manual'] = True
    elif change == 'add': value['add_count'] = 1
    elif change == 'partial': value['partial_fill'] = True
    elif change == 'source_reference': value.pop('source_reference')
    elif change == 'receipt': value['receipt_binding']['source_sha256'] = 'c'*64
    elif change == 'exit_rule':
        value['exit_rule'] = value['receipt_binding']['exit_rule'] = 'scalp_hard_stop_pct'
        seal(value['receipt_binding'], 'sha256')
    seal(value)
    assert replay.replay(rows, baseline(), terminal_outcome=value)['reason'] == 'terminal_outcome_unbound'


def test_horizon_mark_never_becomes_economic_terminal():
    rows = observations()
    result = replay.replay(rows, baseline(), terminal_outcome=normal_terminal(rows, kind='horizon_mark'))
    assert result['status'] == 'censored'
    assert result['reason'] == 'horizon_mark_not_terminal'
    assert result['modeled_net_krw'] is None


@pytest.mark.parametrize('flag', ['manual', 'pending_add', 'partial_fill', 'other_exit'])
def test_endpoint_cannot_erase_observed_lifecycle_censoring(flag):
    rows = observations()
    rows[2][flag] = True
    seal(rows[2])
    result = replay.replay(rows, baseline(), terminal_outcome=normal_terminal(rows))
    assert result['status'] == 'censored'
    assert result['modeled_net_krw'] is None


@pytest.mark.parametrize('enabled,hard,grace', [(False, -1.4, 0), (True, -3.8, 0), (True, -1.4, 90)])
def test_preset_no_safety_can_reach_normal_common_soft(enabled, hard, grace):
    rows = observations(profits=(-.1, -3.2), role='SCALP_PRESET_TP',
        preset_enabled=enabled, preset_hard=hard, preset_grace=grace)
    result = replay.replay(rows, replace(baseline(), grace_sec=0))
    assert result['status'] == 'modeled'
    assert result['reason'] == 'scalp_soft_stop_pct'


def test_preset_still_precedes_common_and_terminal():
    rows = observations(role='SCALP_PRESET_TP')
    result = replay.replay(rows, replace(baseline(), grace_sec=0), terminal_outcome=normal_terminal(rows))
    assert result['status'] == 'censored'
    assert result['reason'] == 'preset_safety_precedes_soft_policy'


def test_add_clock_consumes_actual_operating_context_producer_without_rewriting(monkeypatch):
    from src.engine.scalping import strategy_owner_replay as owner
    from src.engine.scalping import avg_down_replay_capture as capture
    from src.engine.lifecycle import avg_down_policy_replay as lifecycle
    from src.engine import sniper_execution_receipts as receipts
    monkeypatch.setattr(capture, '_cached_policy', lambda *_: dict(rules={}))
    monkeypatch.setattr(capture, 'compact_policy_snapshot', lambda x: x)
    monkeypatch.setattr(capture, 'holding_state', lambda _h, stock: dict(stock=stock))
    monkeypatch.setattr(capture, 'micro_state', lambda *_: {})
    monkeypatch.setattr(lifecycle, 'snapshot_version', lambda _: 'verified-test-policy')
    monkeypatch.setattr(owner, 'entry_operating_model_identity', lambda: 'd'*64)
    monkeypatch.setattr(receipts, 'initial_main_entry_exit_fields', lambda *_a, **_k: {})
    handlers = SimpleNamespace(_is_any_simulated_position=lambda *_: False,
        _holding_sell_nxt_enabled_status=lambda *_: (False, 'existing_owner'))
    sizing = SimpleNamespace(budget_base_krw=100000, safety_ratio=1., absolute_budget_cap_krw=0)
    at = 1792108800.
    stock = dict(id=10, code='005930', strategy='SCALPING', position_tag='SCANNER',
        buy_qty=10, buy_price=10000., pending_add_type='AVG_DOWN')
    context = owner.freeze_entry_operating_context(handlers, stock, sizing, now_ts=at, strict=True)
    assert isinstance(context['frozen_at'], str)
    stock['_trailing_entry_cost_model'] = dict(buy_cost_krw=0,
        sell_cost_rate=context['cost_rate'], source_sha256=context['sha256'],
        known_at=context['frozen_at'], allocation='frozen_configured_round_trip_rate_on_sell_model_only',
        actual_broker_cost=False)
    original = deepcopy(stock['_trailing_entry_cost_model'])
    result = add_models.record_generation(stock, dict(economics_complete=True), at=at+1, completed=True)
    assert result['schema'] == 'verified_post_add_generation_v1'
    assert result['cost_source_sha256'] == context['sha256']
    assert stock['_trailing_entry_cost_model'] == original


@pytest.mark.parametrize('clock', ['2026-10-16T09:00:00', True, 0, float('nan'),
    '2027-10-16T09:00:00+09:00'])
def test_invalid_add_cost_clock_cannot_publish_generation(clock):
    stock = dict(id=10, code='005930', buy_qty=10, buy_price=10000., pending_add_type='AVG_DOWN',
        _trailing_entry_cost_model=dict(known_at=clock, buy_cost_krw=0, source_sha256='a'*64,
            allocation='frozen_configured_round_trip_rate_on_sell_model_only'))
    assert add_models.record_generation(stock, dict(economics_complete=True),
        at=1792108801., completed=True) is None


def test_malformed_add_metadata_is_observation_gap():
    stock = dict(_trailing_entry_cost_model='invalid', post_add_economic_generation={'old': True})
    assert add_models.record_generation(stock, {}, at=1792108801., completed=True) is None
    assert 'post_add_economic_generation' not in stock


@pytest.mark.parametrize('n,total,squares,expected', [(1, 1, 1., 'hold_sample'),
    (2, 10, 2., 'hold_sample'), (2, 2, 200., 'hold_sample'), (2, 2, 2., 'hold_no_edge')])
def test_sample_uncertainty_is_not_measured_no_edge(n, total, squares, expected):
    row = {f'{split}_{key}': value for split in ('train', 'holdout')
        for key, value in dict(n=n, total=total, delta=-float(n), delta_sq=squares,
            safety_regressions=0).items()}
    contract = dict(allowed_keys=['grace_sec'], min_train=2, min_holdout=2,
        max_censoring_ratio=.2, max_standard_error_krw=1., minimum_paired_ev_krw=0.)
    assert replay.choose({'grace_sec:0': row}, contract) == (None, expected)


def test_native_flat_flag_and_same_second_fill_precision_are_retained(tmp_path):
    _, rows, economic = native_terminal_case(tmp_path, decision_second=60.5)
    endpoint = replay.normal_exit_terminal_outcome(first_row=rows[0], last_row=rows[-1], economic=economic)
    receipt = endpoint['receipt_binding']
    assert economic['terminal_observation']['main_automatic_management_allowed'] is False
    assert receipt['main_automatic_management_allowed'] is False
    assert receipt['decision_automatic_management_allowed'] is True
    assert receipt['native_terminal_at'] == rows[-1]['at'] - .5
    assert receipt['sell_fill_clock_precision_bound_sec'] == 1.0
    assert endpoint['at'] == rows[-1]['at']  # No clock correction or quote interpolation.
    fields = economic['terminal_observation']['exit_signal']['fields']
    decision = json.loads(fields['main_stop_normal_exit_decision'])
    decision['decision_at'] += 1
    fields['main_stop_normal_exit_decision'] = json.dumps(seal(decision))
    rows[-1]['at'] += 1
    seal(rows[-1]); seal(economic, 'artifact_sha256')
    with pytest.raises(ValueError, match='completion_mismatch'):
        replay.normal_exit_terminal_outcome(first_row=rows[0], last_row=rows[-1], economic=economic)


def test_exact_quote_capture_overrides_cadence_once_without_io_or_partial_inference(monkeypatch):
    from src.engine import sniper_state_handlers as handlers
    rows = observations()
    stock = dict(id=10, code='005930', strategy='SCALPING', buy_price=10000., buy_qty=10,
        main_stop_source_at=rows[-1]['at']-.1, entry_partial_fill_deferred_notice={'sent':False},
        _trailing_entry_cost_model=rows[-1]['cost_model'])
    stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
        role='SCANNER', market='REGULAR', target='2026-10-16', baseline=baseline())
    context = dict(at=rows[-1]['at'], bid=rows[-1]['bid'], bid_qty=20,
        quote=dict(market_route='KRX', item='005930', transport_epoch=1, observed_epoch=rows[-1]['at']),
        complete=True, market='REGULAR', evaluator='normal', decision_profit_pct=.5,
        position_key=position_cycle_id(stock), quantity=10, buy_price=10000., pending_exit=False)
    stock['_main_stop_current_quote_context'] = context
    captured = []
    monkeypatch.setattr(policy, 'enqueue_source', lambda stock, code, row: captured.append(deepcopy(row)) or True)
    monkeypatch.setattr(handlers, '_is_scalp_simulated_position', lambda *a: False)
    def forbidden(*args, **kwargs): raise AssertionError('unexpected source I/O')
    monkeypatch.setattr(handlers.POSITION_PEAK_LEDGER, 'record_stop_pin', forbidden)
    monkeypatch.setattr(handlers.POSITION_PEAK_LEDGER, 'get_for_stock', forbidden)
    monkeypatch.setattr(handlers, '_main_stop_preset_observation', lambda *a, **k: None)
    assert handlers._capture_main_stop_observation(stock, '005930', context) is False
    result = handlers._main_stop_normal_exit_fields(stock, '005930', at=context['at'],
        mark_price=context['bid']+17, exit_rule='scalp_trailing_take_profit')
    decision = json.loads(result['main_stop_normal_exit_decision'])
    assert decision['decision_price'] == decision['executable_bid'] == context['bid']
    assert decision['mark_price'] == context['bid']+17
    assert decision['quantity_source_status'] == 'runtime_observed_not_terminal'
    assert 'partial_fill' not in decision
    assert captured[0]['partial_fill'] is True  # Known historical producer gap stays visible.
    assert len(captured) == 1 and captured[0]['at'] == context['at']
    stock['exit_requested'] = True
    again = handlers._main_stop_normal_exit_fields(stock, '005930', at=context['at'],
        mark_price=context['bid']+17, exit_rule='scalp_trailing_take_profit')
    assert again == result and len(captured) == 1
    context['quote']['transport_epoch'] += 1
    failed = handlers._main_stop_normal_exit_fields(stock, '005930', at=context['at'],
        mark_price=context['bid']+17, exit_rule='scalp_trailing_take_profit')
    assert 'main_stop_normal_exit_decision_gap' in failed and len(captured) == 1


def test_daily_decision_mark_and_modeled_executable_bid_are_separate(tmp_path):
    stock, rows, economic = native_terminal_case(tmp_path)
    decision = policy.normal_exit_decision_source(stock, at=rows[-1]['at'], price=10100,
        executable_bid=rows[-1]['bid'], mark_price=10100, exit_rule='daily_limit_up_immediate_exit')
    native = economic['terminal_observation']
    native['exit_signal']['exit_rule'] = decision['exit_rule']
    native['exit_signal']['fields']['main_stop_normal_exit_decision'] = json.dumps(decision)
    economic['main_exit_source']['exit_rule'] = decision['exit_rule']
    seal(economic, 'artifact_sha256')
    endpoint = replay.normal_exit_terminal_outcome(first_row=rows[0], last_row=rows[-1], economic=economic)
    assert endpoint['price'] == rows[-1]['bid']
    assert endpoint['receipt_binding']['decision_price'] == 10100
    assert endpoint['receipt_binding']['decision_price_basis'] == 'mark_price'


def test_native_subsecond_fill_clock_has_no_whole_second_allowance(tmp_path):
    _, rows, economic = native_terminal_case(tmp_path, decision_second=60.5)
    native = economic['terminal_observation']
    native['terminal_fill_time'] = native['terminal_fill_time'].replace('10:01:00+', '10:01:00.250000+')
    seal(economic, 'artifact_sha256')
    with pytest.raises(ValueError, match='completion_mismatch'):
        replay.normal_exit_terminal_outcome(first_row=rows[0], last_row=rows[-1], economic=economic)


@pytest.mark.parametrize('fault', [None, 'malformed_quote', 'sink_failure'])
def test_native_early_preset_limit_up_captures_source_without_changing_exit(monkeypatch, fault):
    from zoneinfo import ZoneInfo
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping import avg_down_replay_capture, strategy_owner_replay
    at = datetime(2026, 10, 16, 10, tzinfo=ZoneInfo('Asia/Seoul')).timestamp()
    stock = dict(id=10, code='005930', name='STOP_RESEARCH_TEST', status='HOLDING', strategy='SCALPING',
        exit_mode='SCALP_PRESET_TP', buy_qty=10, buy_price=10000., main_stop_source_at=at-.1,
        _trailing_entry_cost_model=observations()[-1]['cost_model'])
    stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
        role='SCALP_PRESET_TP', market='REGULAR', target='2026-10-16', baseline=baseline())
    depth = dict(item='005930', market_route='krx_only', transport_epoch=1, observed_epoch=at,
        best_bid=13000, best_bid_qty=20, orderbook={'bids':[{'price':13000,'volume':20}]})
    ws = dict(code='005930', curr=13010, upper_limit_price=13010, best_bid=13000, best_ask=13020,
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
        ({'quote_consistency_state':'consistent'},13010,13020,13000))
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
    class NativeExitReached(Exception): pass
    def original_next_step(*args, **kwargs): raise NativeExitReached()
    monkeypatch.setattr(handlers, '_confirm_cancel_or_reload_remaining', original_next_step)
    with pytest.raises(NativeExitReached):
        handlers.handle_holding_state(stock, '005930', ws, None, 'BULL', now_ts=at)
    signal = next(fields for stage,fields in logs if stage == 'exit_signal')
    assert signal['exit_rule'] == 'daily_limit_up_immediate_exit'
    if fault is None:
        decision = json.loads(signal['main_stop_normal_exit_decision'])
        assert len(captured) == 1 and captured[0]['at'] == at and captured[0]['bid'] == 13000
        assert decision['decision_at'] == at and decision['decision_price'] == 13010
        assert decision['executable_bid'] == 13000 and decision['decision_price_basis'] == 'mark_price'
    else:
        assert not captured and signal['main_stop_normal_exit_decision_gap']
        assert 'main_stop_normal_exit_decision' not in signal
