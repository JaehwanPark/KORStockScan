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
from src.tests.test_main_stop_runtime_source import evaluation_stream


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
    prior = replay.replay(evaluation_stream(rows), baseline(), terminal_outcome=endpoint)
    early = replay.replay(evaluation_stream(rows), replace(baseline(), grace_sec=0), terminal_outcome=endpoint)
    assert prior['status'] == early['status'] == 'modeled'
    assert prior['reason'] == 'observed_normal_exit_endpoint'
    assert early['reason'] == 'scalp_soft_stop_pct'
    assert prior['modeled_net_krw'] > 0 > early['modeled_net_krw']
    assert prior['actual_realized_net_krw'] is None
    assert prior['terminal_source_sha256'] == endpoint['source_reference']['sha256']
    assert replay.replay(evaluation_stream(rows), baseline())['status'] == 'censored'


def native_terminal_case(tmp_path, *, decision_second=3):
    from src.tests import test_main_stop_research_cost as cost_fixture
    stock = dict(id=1, code='005930', strategy='SCALPING', buy_qty=2, buy_price=10000.)
    at = datetime.fromisoformat(cost_fixture.DAY + 'T10:00:00+09:00').timestamp()
    from src.engine import sniper_execution_receipts as native_receipts
    stock.update(entry_requested_qty=2,requested_buy_qty=2,
        pending_entry_orders=[dict(ord_no='11',qty=2,filled_qty=0,status='OPEN')])
    native_receipts._resolve_entry_effective_fill_qty(target_stock=stock,code='005930',order_no='11',
        exec_price=10000,exec_qty=2,order_qty=2,remaining_qty=0,cumulative_exec_amount=20000,
        execution_no='101',unit_exec_qty=2,unit_exec_price=10000)
    stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
        role='SCANNER', market='REGULAR', target=cost_fixture.DAY, baseline=baseline())
    rows = []
    for i, profit in enumerate((-.1, -3.2, -.2, .5)):
        stamp = at + (decision_second if i == 3 else i)
        rows.append(policy.source_row(stock, at=stamp, bid=10000*(1+profit/100), bid_qty=2,
            quote=dict(market_route='SOR', item='005930', transport_epoch=1, observed_epoch=stamp),
            coverage_complete=True, automatic_management_allowed=True, decision_profit_pct=profit,
            native_decision_required=True,capture_evaluator="normal",
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
    prior = replay.replay(evaluation_stream(rows), baseline(), terminal_outcome=endpoint)
    early = replay.replay(evaluation_stream(rows), replace(baseline(), grace_sec=0), terminal_outcome=endpoint)
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
    stock = dict(id=10, code='005930', strategy='SCALPING', buy_price=10000., buy_qty=10,
        status='HOLDING', exit_token='native-fast-claim', exit_requested=True)
    stock['main_stop_policy_pin'] = policy.pin(position_key=position_cycle_id(stock),
        role='SCANNER', market='REGULAR', target='2026-10-16', baseline=baseline())
    if fault == 'pin': stock['main_stop_policy_pin']['pin_sha256'] = 'invalid'
    if fault == 'manual': stock['manual_control_exclusion_blocked'] = True
    if fault == 'observer_failure':
        def broken(*args, **kwargs): raise RuntimeError('observation_failed')
        monkeypatch.setattr(policy, 'normal_exit_decision_source', broken)
    stock['_main_stop_current_quote_context'] = dict(at=rows[-1]['at'], bid=rows[-1]['bid'], complete=True,
        evaluator='fast')
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
    if fault == 'manual':
        assert logs == []  # The native ownership guard precedes observer metadata.
        return
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
    assert replay.replay(evaluation_stream(rows), baseline(), terminal_outcome=value)['reason'] == 'terminal_outcome_unbound'


def test_horizon_mark_never_becomes_economic_terminal():
    rows = observations()
    result = replay.replay(evaluation_stream(rows), baseline(), terminal_outcome=normal_terminal(rows, kind='horizon_mark'))
    assert result['status'] == 'censored'
    assert result['reason'] == 'horizon_mark_not_terminal'
    assert result['modeled_net_krw'] is None


@pytest.mark.parametrize('flag', ['manual', 'pending_add', 'other_exit'])
def test_endpoint_cannot_erase_observed_lifecycle_censoring(flag):
    rows = observations()
    rows[2][flag] = True
    seal(rows[2])
    result = replay.replay(evaluation_stream(rows), baseline(), terminal_outcome=normal_terminal(rows))
    assert result['status'] == 'censored'
    assert result['modeled_net_krw'] is None


@pytest.mark.parametrize('enabled,hard,grace', [(False, -1.4, 0), (True, -3.8, 0), (True, -1.4, 90)])
def test_preset_no_safety_can_reach_normal_common_soft(enabled, hard, grace):
    rows = observations(profits=(-.1, -3.2), role='SCALP_PRESET_TP',
        preset_enabled=enabled, preset_hard=hard, preset_grace=grace)
    result = replay.replay(evaluation_stream(rows), replace(baseline(), grace_sec=0))
    assert result['status'] == 'modeled'
    assert result['reason'] == 'scalp_soft_stop_pct'


def test_preset_still_precedes_common_and_terminal():
    rows = observations(role='SCALP_PRESET_TP')
    result = replay.replay(evaluation_stream(rows), replace(baseline(), grace_sec=0), terminal_outcome=normal_terminal(rows))
    assert result['status'] == 'unreachable'
    assert result['reason'] == 'native_preset_safety_precedes_common_soft'


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
    assert 'partial_fill' not in captured[0]
    assert captured[0]['quantity_source']['status'] == 'unknown'  # Known historical producer gap stays visible.
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


def test_legacy_shared_quotes_never_authorize_a_normal_soft_decision():
    source=observations()
    result=replay.replay(source,replace(baseline(),grace_sec=0),terminal_outcome=normal_terminal(source))
    assert result['status']=='source_unsupported'
    assert result['reason']=='actual_common_soft_decision_unobserved'
    diagnostics=replay.source_diagnostics(source,baseline())
    assert diagnostics['counts']['shared_quotes']==4
    assert diagnostics['native_support']['whole_population_scanned'] is True
    assert diagnostics['native_support']['supported_windows']['decisions']==0
    assert diagnostics['native_support']['status']=='source_unsupported'


def test_real_normal_clock_and_mark_basis_advance_decision_without_rewriting_quote():
    from src.tests.test_main_stop_runtime_source import stage_stock,research_quote,stage_inputs
    from src.engine.scalping.main_stop_runtime_source import evaluation_source
    stock=stage_stock();events=[];original=[]
    for n,profit in enumerate((-.1,-3.5)):
        q=research_quote(stock,at=1000.+n,bid=9990,profit=-.1,cost=observations()[0]['cost_model'])
        q['cost_model']=dict(q['cost_model'],known_at=999.);seal(q)
        original.append(deepcopy(q));events.append(q)
        events.append(evaluation_source(stock,quote_source=q,at=1000.2+n,evaluator='normal',stage='common_soft',
            decision_price=10000*(1+profit/100),decision_price_basis='mark_price',decision_profit_pct=profit,
            priority_status='reached',quote_max_age_sec=3.,decision_inputs=stage_inputs(q['cost_model'])))
    result=replay.replay(events,replace(baseline(),grace_sec=0))
    assert result['status']=='modeled' and result['crossing_at']==1001.2
    assert result['quantity_status']=='full_fill'
    assert [events[0],events[2]]==original
    # Different mark-based crossing and executable bid remain separately bound.
    assert result['modeled_net_krw']==pytest.approx(9990*10*.9977-100000)


@pytest.mark.parametrize('fault',['quantity','anchor','predecessor','legacy','generation_loss'])
def test_actual_evaluation_requires_quantity_generation_and_scope(fault):
    source=list(evaluation_stream(observations(role='SCALP_PRESET_TP',preset_hard=-4.5)))
    target=next(row for row in source if row.get('stage')=='common_soft')
    if fault=='quantity':target['quantity_source']=None
    elif fault=='anchor':target['evaluation_id']='f'*64
    elif fault=='predecessor':target['preset_predecessor']['source_sha256']='f'*64
    elif fault=='legacy':target['legacy_broker_recovered']=True
    elif fault=='generation_loss':target['evaluation_rejected_count']=1
    seal(target)
    result=replay.replay(source,replace(baseline(),grace_sec=0))
    assert result['status'] in {'source_gap','source_unsupported'}
    assert result['modeled_net_krw'] is None


def test_whole_population_support_counts_survive_early_counterfactual_crossing():
    source=list(evaluation_stream(observations()))
    result=replay.replay(source,replace(baseline(),grace_sec=0))
    assert result['status']=='modeled'
    assert result['source_support']['common_soft_decisions_seen']==2
    census=replay.source_diagnostics(source,baseline())
    assert census['native_support']['supported_windows']['decisions']==4
    assert census['native_support']['evaluator_census']=={'normal:common_soft':4}
    assert census['economic_binding_source']['quantity_source']['status']=='full_fill'


@pytest.mark.parametrize('fault',['coverage','route','gap','manual','basis'])
def test_terminal_bridge_cannot_hide_unobserved_tail_source_change(fault):
    raw=observations();events=list(evaluation_stream(raw[:-1]))
    last=deepcopy(raw[-1])
    if fault=='coverage':last['coverage_complete']=False
    elif fault=='route':last['route']='OTHER'
    elif fault=='gap':last['at']+=4;last['quote_at']+=4
    elif fault=='manual':last['manual']=True
    elif fault=='basis':last['buy_basis_krw']+=1
    seal(last);events.append(last)
    endpoint=normal_terminal([raw[0],last])
    result=replay.replay(events,baseline(),terminal_outcome=endpoint)
    assert result['status']!='modeled' and result['modeled_net_krw'] is None


def test_legacy_preset_skip_is_unsupported_not_observed_unreachability():
    from src.tests.test_main_stop_runtime_source import stage_stock,research_quote,research_evaluation
    stock=stage_stock(role='SCALP_PRESET_TP')
    receipt=policy.preset_stop_receipt(stock,at=1000.,evaluator='normal',hard_pct=-1.4,
        grace_sec=0,emergency_pct=-4.5,held_sec=100.,enabled=False)
    quote=research_quote(stock,at=1000.,bid=9600,profit=-4.,preset=receipt)
    actual=research_evaluation(stock,quote,stage='preset_safety',preset=receipt,legacy=True)
    result=replay.replay([quote,actual],baseline())
    assert result['status']=='source_unsupported'
    assert result['reason']=='legacy_recovered_decision_scope_unsupported'


@pytest.mark.parametrize('fault',[None,'prefix_below','first_full_below','missing_touch','active_touch','loss','clock_gap'])
def test_initial_unknown_quantity_only_skips_a_proven_common_no_exit_prefix(fault):
    from src.tests.test_main_stop_runtime_source import stage_stock,research_quote,stage_inputs
    from src.engine.scalping.main_stop_runtime_source import evaluation_source
    stock=stage_stock();events=[]
    for n in range(3):
        stock['entry_requested_qty']=stock['requested_buy_qty']=11 if n==0 else 10
        at=1000.+n+(4 if fault=='clock_gap' and n else 0)
        profit=-.1 if n<2 else -3.5
        if fault=='prefix_below' and n==0:profit=-3.2
        if fault=='first_full_below' and n==1:profit=-3.2
        q=research_quote(stock,at=at,bid=10000*(1+profit/100),profit=profit,
            cost=dict(buy_cost_krw=0.,sell_cost_rate=.0023,known_at=999.,source_sha256='a'*64))
        inputs=stage_inputs(q['cost_model'])
        if fault=='missing_touch' and n==0:inputs.pop('soft_stop_micro_grace_started_at')
        if fault=='active_touch' and n==0:inputs['soft_stop_micro_grace_started_at']=990.
        if fault=='loss':stock['main_stop_evaluation_rejected_count']=1
        e=evaluation_source(stock,quote_source=q,at=at,evaluator='normal',stage='common_soft',
            decision_price=q['bid'],decision_price_basis='mark_price',decision_profit_pct=profit,
            priority_status='reached',quote_max_age_sec=3.,decision_inputs=inputs)
        events.extend([q,e])
    result=replay.replay(events,replace(baseline(),grace_sec=0),support_soft_threshold=-3.)
    if fault is None:
        assert result['status']=='modeled'
        assert result['excluded_initial_quantity_decisions']==1
        assert result['comparison_start']['at']==1001.
        diagnostic=replay.source_diagnostics(events,baseline(),support_soft_threshold=-3.)
        assert diagnostic['comparison_prefix']['whole_lifecycle_no_exit_prefix_proven'] is True
        assert diagnostic['comparison_prefix']['excluded_initial_quantity_decisions']==1
        assert diagnostic['economic_binding_source']['at']==1001.
    else:
        assert result['status']!='modeled',result
        assert result['modeled_net_krw'] is None
        if fault=='first_full_below':assert result['reason']=='pre_crossing_source_missing'


def test_initial_missing_depth_keeps_actual_gate_and_never_models_a_crossing():
    from src.tests.test_main_stop_runtime_source import stage_stock,research_quote,stage_inputs
    from src.engine.scalping.main_stop_runtime_source import evaluation_source
    stock=stage_stock();events=[]
    for n,profit in enumerate((-.1,-.1,-3.5)):
        q=research_quote(stock,at=1000.+n,bid=10000*(1+profit/100),profit=profit,
            cost=dict(buy_cost_krw=0.,sell_cost_rate=.0023,known_at=999.,source_sha256='a'*64))
        if n==0:
            q.update(bid=None,bid_qty=None,quote_at=None,coverage_complete=False,item=None,route=None,transport_epoch=None)
            seal(q)
        actual=evaluation_source(stock,quote_source=q,at=1000.+n,evaluator='normal',stage='common_soft',
            decision_price=10000*(1+profit/100),decision_price_basis='mark_price',decision_profit_pct=profit,
            priority_status='reached',quote_max_age_sec=3.,decision_inputs=stage_inputs(q['cost_model']))
        events.extend([q,actual])
    result=replay.replay(events,replace(baseline(),grace_sec=0))
    assert result['status']=='modeled' and result['excluded_initial_quote_decisions']==1
    assert result['comparison_start']['at']==1001.
    census=replay.source_diagnostics(events,baseline())
    assert census['native_support']['evaluator_census']=={'normal:common_soft':3}
    assert census['native_support']['gaps']['actual_decision_quote_source_gap']==1
    crossing=deepcopy(events[:2]);crossing[1]['decision_profit_pct']=-4.
    seal(crossing[1])
    outcome=replay.replay(crossing,replace(baseline(),grace_sec=0))
    assert outcome['status']=='source_unsupported' and outcome['modeled_net_krw'] is None


def test_missing_actual_evaluation_generation_never_grants_an_earlier_start():
    events=list(evaluation_stream(observations()))
    dropped=[row for row in events if row.get('evaluation_generation')!=1]
    outcome=replay.replay(dropped,replace(baseline(),grace_sec=0))
    assert outcome['status']=='source_gap' and outcome['reason']=='native_evaluation_generation_missing'
    dropped=[row for row in events if row.get('evaluation_generation')!=2]
    outcome=replay.replay(dropped,baseline(),terminal_outcome=normal_terminal(observations()))
    assert outcome['status']=='source_gap' and outcome['reason']=='native_evaluation_generation_missing'


@pytest.mark.parametrize('fault',['quantity_unknown','pending_exit','future_cost','cost_rate'])
def test_last_quote_without_soft_evaluation_still_needs_terminal_quantity_and_cost(fault):
    from src.tests.test_main_stop_runtime_source import stage_stock,research_quote,research_evaluation
    stock=stage_stock();events=[];quotes=[]
    for n,profit in enumerate((-.1,-.2,.5)):
        quote=research_quote(stock,at=1000.+n,bid=10000*(1+profit/100),profit=profit,
            cost=dict(buy_cost_krw=0.,sell_cost_rate=.0023,known_at=999.,source_sha256='a'*64))
        quotes.append(quote);events.append(quote)
        if n<2:events.append(research_evaluation(stock,quote))
    last=quotes[-1]
    if fault=='quantity_unknown':
        last['quantity_source']['status']='unknown'
        seal(last['quantity_source'])
    elif fault=='pending_exit':last['pending_exit']=True
    elif fault=='future_cost':last['cost_model']['known_at']=2000.
    elif fault=='cost_rate':last['cost_model']['sell_cost_rate']=-1.
    seal(last)
    result=replay.replay(events,baseline(),terminal_outcome=normal_terminal(quotes))
    assert result['status']!='modeled' and result['modeled_net_krw'] is None


def test_preset_predecessor_keeps_its_own_quote_and_price_basis():
    from src.tests.test_main_stop_runtime_source import stage_stock,research_quote,stage_inputs
    from src.engine.scalping.main_stop_runtime_source import evaluation_source
    stock=stage_stock(role='SCALP_PRESET_TP');at=1000.
    preset=policy.preset_stop_receipt(stock,at=at,evaluator='normal',hard_pct=-1.4,
        grace_sec=0,emergency_pct=-4.5,held_sec=100.,enabled=True)
    q1=research_quote(stock,at=at,bid=9990,profit=-.1,preset=preset,
        cost=dict(buy_cost_krw=0.,sell_cost_rate=.0023,known_at=999.,source_sha256='a'*64))
    first=evaluation_source(stock,quote_source=q1,at=at,evaluator='normal',stage='preset_safety',
        decision_price=9991,decision_price_basis='mark_price',decision_profit_pct=-.09,
        priority_status='reached',quote_max_age_sec=3.,preset_stop=preset,
        decision_inputs={'handoff_enabled':False})
    q2=research_quote(stock,at=at,bid=9992,profit=-.08,preset=preset,cost=q1['cost_model'])
    second=evaluation_source(stock,quote_source=q2,at=at,evaluator='normal',stage='common_soft',
        decision_price=9992,decision_price_basis='executable_bid',decision_profit_pct=-.08,
        priority_status='reached',quote_max_age_sec=3.,preset_predecessor=first,
        decision_inputs=stage_inputs(q2['cost_model']))
    result=replay.replay([q1,first,q2,second],baseline())
    assert result['status']=='censored' and result['reason']=='crossing_not_observed'
    assert result['source_support']['common_soft_decisions_seen']==1


def test_preset_uses_actual_stage_handoff_flag_instead_of_shared_quote():
    events=list(evaluation_stream(observations((-.1,-1.5),role='SCALP_PRESET_TP')))
    preset=next(value for value in reversed(events) if value.get('stage')=='preset_safety')
    quote=next(value for value in events if value.get('source_sha256')==preset['quote_source_sha256'])
    assert quote['handoff_enabled'] is False
    preset['decision_inputs']['handoff_enabled']=True;seal(preset)
    assert replay.native_preset_decision(quote,preset).disposition=='manual_handoff'
    del preset['decision_inputs']['handoff_enabled'];seal(preset)
    with pytest.raises(ValueError,match='native_preset_decision_inputs_missing'):
        replay.evaluation_binding(preset,quote)


def test_supported_quote_claim_survives_recent_quote_eviction():
    from src.engine.lifecycle.research_input_budget import health
    baseline_bytes=health()['used_bytes']
    events=list(evaluation_stream(observations(tuple([-.1]*7))))
    with replay.bound_evaluations(events) as (stream,state):
        for index,(quote,evaluation) in enumerate(stream):
            if index==1:
                before=health()['used_bytes'];state['pin_supported_quote'](quote)
                claimed=health()['used_bytes']-before;first=quote
        assert state['first_supported_quote'] is first and claimed>0
        # Four recent quotes, original first and separately pinned supported
        # quote retain independent reservations through the entire join.
        assert health()['used_bytes']>=baseline_bytes+claimed
    assert health()['used_bytes']==baseline_bytes


def test_detached_diagnostic_endpoint_and_copy_keep_their_budget_claims():
    import gc
    from src.engine.lifecycle.research_input_budget import health
    gc.collect();baseline_bytes=health()['used_bytes']
    diagnostics=replay.source_diagnostics(evaluation_stream(observations()),baseline())
    endpoint=diagnostics['source_endpoints']['first']
    economic=diagnostics['economic_binding_source']
    encoded=json.dumps(diagnostics,allow_nan=False)
    clone=deepcopy(endpoint)
    del diagnostics;gc.collect()
    assert health()['used_bytes']>baseline_bytes and json.loads(encoded)['source_endpoints']['first']==endpoint
    del endpoint,economic;gc.collect()
    assert health()['used_bytes']>baseline_bytes and clone['schema']=='main_stop_source_v1'
    del clone;gc.collect()
    assert health()['used_bytes']==baseline_bytes


@pytest.mark.parametrize('fault',[None,'buy','record','stop_cycle_key','missing','path','schema'])
def test_actual_vote_binds_native_record_and_proven_buy_generation(fault):
    from src.tests.test_main_stop_runtime_source import stage_stock,research_quote,stage_inputs
    from src.engine.scalping.main_stop_runtime_source import evaluation_source
    from src.engine.ai import holding_exit_vote,holding_vote_replay_source
    stock=stage_stock();events=[]
    for n,profit in enumerate((-.1,-3.2)):
        at=1000.+n;cost=dict(buy_cost_krw=0.,sell_cost_rate=.0023,known_at=999.,source_sha256='a'*64)
        quote=research_quote(stock,at=at,bid=10000*(1+profit/100),profit=profit,cost=cost)
        vote=holding_vote_replay_source.runtime_source(stock,position_key=f"record:{stock['id']}",
            buy_fill_identity=holding_exit_vote.buy_fill_identity_from_runtime(stock),
            market=quote['market'],now=at,policy={},data_root=None,model='fixture',path_id='EXIT_SOFT_STOP')
        inputs=dict(stage_inputs(cost),holding_ai_required=True,holding_vote_source=vote)
        actual=evaluation_source(stock,quote_source=quote,at=at,evaluator='normal',stage='common_soft',
            decision_price=quote['bid'],decision_price_basis='executable_bid',decision_profit_pct=profit,
            priority_status='reached',quote_max_age_sec=3.,decision_inputs=inputs)
        if n==1 and fault:
            changed=actual['decision_inputs']['holding_vote_source']
            if fault=='buy':changed['buy_fill_identity']='f'*64
            elif fault=='record':changed['position_key']='record:999'
            elif fault=='stop_cycle_key':changed['position_key']=quote['position_key']
            elif fault=='path':changed['path_id']='EXIT_TRAILING_TP'
            elif fault=='schema':changed['schema']='unbound_vote_source'
            else:actual['decision_inputs']['holding_vote_source']=None
            seal(actual)
        events.extend((quote,actual))
    calls=[]
    def original_vote(row,at):
        calls.append(at)
        return dict(decision='PASS',source_verified=True,max_defer_sec=0.)
    result=replay.replay(events,replace(baseline(),grace_sec=0,protect_emergency_pct=-4.),
        vote_reader=original_vote)
    if fault:
        assert result['status']=='source_gap' and result['modeled_net_krw'] is None
        assert result['reason']==('holding_vote_buy_generation_mismatch' if fault=='buy'
            else 'holding_vote_reference_unbound' if fault=='missing'
            else 'holding_vote_native_path_mismatch' if fault in {'path','schema'}
            else 'holding_vote_record_generation_mismatch')
        assert not calls
    else:
        assert result['status']=='modeled' and calls==[1001.]
    assert events[0]['position_key'].startswith('target:')
    assert events[1]['decision_inputs']['holding_vote_source']['position_key'].startswith('record:')


def native_lane_rows():
    """New synthetic calls use actual producers; no historical row is upgraded."""
    from src.engine.scalping import main_stop_runtime_source as runtime
    from src.tests.test_main_stop_runtime_source import stage_stock,stage_inputs
    stock=stage_stock(role='SCALP_PRESET_TP')
    runtime.ensure_observation_epoch(stock)
    result=[];predecessor=None
    cost=dict(buy_cost_krw=0.,sell_cost_rate=.0023,known_at=999.,source_sha256='a'*64)
    for owner,stage,at,profit in (
            ('normal','preset_safety',1000.,-.1),('normal','common_soft',1000.,-.1),
            ('fast','preset_safety',1001.01,-.1),
            ('normal','preset_safety',1001.,-3.2),('normal','common_soft',1001.,-3.2)):
        view=runtime.observation_view(stock)
        runtime.reserve_observation_generations(stock,view,quote=True)
        quote=policy.source_row(view,at=at,bid=10000*(1+profit/100),bid_qty=100,
            quote=dict(market_route='KRX',item='005930',transport_epoch=1,observed_epoch=at),
            coverage_complete=True,automatic_management_allowed=True,cost_model=cost,vote_source=None,
            runtime_flags=stage_inputs(cost),decision_profit_pct=profit,
            native_decision_required=True,capture_evaluator=owner,seal=False)
        quote.update(runtime.observation_source_identity(view));seal(quote)
        runtime.reserve_observation_generations(stock,view,evaluation=True)
        lane=runtime.reserve_evaluation_lane(stock,view,owner)
        preset=(policy.preset_stop_receipt(view,at=at,evaluator=owner,hard_pct=-5.,
            grace_sec=0,emergency_pct=-5.5,held_sec=100,enabled=True) if stage=='preset_safety' else None)
        evaluation=runtime.evaluation_source(view,quote_source=quote,at=at,evaluator=owner,stage=stage,
            decision_price=quote['bid'],decision_price_basis='executable_bid',decision_profit_pct=profit,
            priority_status='reached',quote_max_age_sec=3.,preset_stop=preset,
            preset_predecessor=predecessor if stage=='common_soft' else None,
            decision_inputs=stage_inputs(cost) if stage=='common_soft' else {'handoff_enabled':False},seal=False)
        evaluation.update(lane);seal(evaluation)
        if owner=='normal' and stage=='preset_safety':predecessor=runtime.evaluation_reference(evaluation)
        result.extend((quote,evaluation))
    return result


def test_native_lane_order_uses_actual_index_without_rewriting_caller_clocks(tmp_path):
    from collections import Counter
    from src.engine.automation import main_stop_postclose as post,main_stop_source_index as index
    from src.engine.lifecycle.holding_window_generation import byte_generation
    events=native_lane_rows();original=deepcopy(events)
    source=tmp_path/'holding_pipeline_2026-10-16.jsonl'
    source.write_text(''.join(json.dumps(dict(stage='main_stop_source',fields=dict(main_stop_source=row)))+'\n'
        for row in events))
    census=Counter();refs=index.prepare(tmp_path/'index',{str(source):byte_generation(source)},post.source_events,census)
    for position in index.positions(refs,tmp_path/'positions',census):
        rows=list(position.rows())
        assert [row['evaluation_generation'] for row in rows if row['schema']==replay.EVALUATION_SCHEMA]==[1,2,4,5,3]
        with replay.bound_evaluations(iter(rows)) as (bound,state):
            observed=list(bound)
            assert not [row for row,ev in observed if row['schema']=='main_stop_contract_gap']
            assert state['evaluation_global_prefix']==5
            assert state['evaluation_lane_previous']=={'normal':4,'fast':1}
        result=replay.replay(iter(rows),replace(baseline(),grace_sec=0,protect_emergency_pct=-4.))
        assert result['status']=='modeled' and result['crossing_at']==1001.
        assert result['source_support']['native_evaluations_seen']==5
    assert events==original


@pytest.mark.parametrize('fault',['missing_fast','duplicate_fast','missing_normal','quote_scope','lane_vector',
    'runtime_incarnation','mixed_legacy','predecessor_lane'])
def test_native_lane_integrity_remains_strict_after_an_early_crossing(fault):
    events=native_lane_rows()
    if fault=='missing_fast':events=[row for row in events if row.get('evaluator')!='fast']
    elif fault=='duplicate_fast':events.append(deepcopy(events[5]))
    elif fault=='missing_normal':events.pop(7)
    elif fault=='quote_scope':events[6]['source_runtime_incarnation']='f'*32;seal(events[6])
    elif fault=='lane_vector':events[9]['evaluation_lane_generations']={'normal':3,'fast':2};seal(events[9])
    elif fault=='runtime_incarnation':
        for row in events[4:6]:row['source_runtime_incarnation']='f'*32;seal(row)
        events[5]['quote_source_sha256']=events[4]['source_sha256'];seal(events[5])
    elif fault=='mixed_legacy':
        for row in events[4:6]:
            for key in ('evaluation_lane_scope','source_runtime_pid','source_runtime_incarnation',
                'evaluation_lane_generation','evaluation_lane_generations'):row.pop(key,None)
            seal(row)
        events[5]['quote_source_sha256']=events[4]['source_sha256'];seal(events[5])
    else:
        events[9]['evaluation_lane_generation']=5
        events[9]['evaluation_lane_generations']={'normal':5,'fast':0}
        seal(events[9])
    events.sort(key=lambda row:(row['at'],row['source_observation_generation']))
    result=replay.replay(iter(events),replace(baseline(),grace_sec=0,protect_emergency_pct=-4.))
    assert result['status']=='source_gap' and result['modeled_net_krw'] is None
    assert result['allowed_runtime_apply'] is False


def test_native_lane_pending_claims_close_on_early_context_exit():
    from src.engine.lifecycle.research_input_budget import health
    events=native_lane_rows();events.sort(key=lambda row:(row['at'],row['source_observation_generation']))
    before=health()['used_bytes']
    with replay.bound_evaluations(iter(events)) as (bound,state):
        for row,ev in bound:
            if ev and ev['evaluation_generation']==4:break
        assert state['evaluation_global_prefix']==2
        assert health()['used_bytes']>before
    assert health()['used_bytes']==before


def test_restored_datetime_and_large_order_receipt_reach_native_terminal_consumer(monkeypatch, tmp_path):
    import pandas as pd
    from src.database.db_manager import _canonical_target_datetimes
    from src.engine import sniper_state_handlers as handlers
    stock, rows, economic = native_terminal_case(tmp_path)
    # Exercise the DB dataframe conversion, actual forced capture and final
    # native receipt reader together, without reconstructing a lost receipt.
    restored = pd.DataFrame([dict(holding_started_at=datetime(2026,10,16,9),
                                 order_time=pd.NaT)]).to_dict('records')[0]
    stock.update(_canonical_target_datetimes(restored))
    stock['pending_entry_orders'][0]['entry_feature_telemetry'] = 'x'*1_000_000
    stock['_trailing_entry_cost_model'] = rows[-1]['cost_model']
    stock['_main_stop_current_quote_context'] = dict(at=rows[-1]['at'],bid=rows[-1]['bid'],bid_qty=2,
        quote=dict(market_route='SOR',item='005930',transport_epoch=1,observed_epoch=rows[-1]['at']),
        complete=True,market='REGULAR',evaluator='normal',decision_profit_pct=.5,
        position_key=position_cycle_id(stock),quantity=2,buy_price=10000.,pending_exit=False)
    captured=[]
    monkeypatch.setattr(policy,'enqueue_source',lambda s,c,row: captured.append(deepcopy(row)) or True)
    monkeypatch.setattr(handlers,'_is_scalp_simulated_position',lambda *a:False)
    monkeypatch.setattr(handlers,'_main_stop_preset_observation',lambda *a,**k:None)
    fields=handlers._main_stop_normal_exit_fields(stock,'005930',at=rows[-1]['at'],
        mark_price=rows[-1]['bid']+1,exit_rule='scalp_trailing_take_profit')
    assert 'main_stop_normal_exit_decision' in fields, fields
    assert captured[0]['quantity_source']['status']=='full_fill'
    seal(captured[0])  # The real queue seals this detached source before writing.
    economic['terminal_observation']['exit_signal']['fields'].update(fields)
    seal(economic,'artifact_sha256')
    endpoint=replay.normal_exit_terminal_outcome(first_row=rows[0],last_row=captured[0],economic=economic)
    assert endpoint['receipt_binding']['status']=='COMPLETED'
    assert endpoint['at']==rows[-1]['at']
