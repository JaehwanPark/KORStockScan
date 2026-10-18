"""Native receipt producers, source-only quantity proofs and missing evidence."""
from copy import deepcopy

import pytest

from src.engine.scalping import main_stop_quantity_source as quantity
from src.engine.scalping.position_peak_ledger import position_cycle_id
from src.engine.scalping.initial_quantity_bundle_state import new_bundle_state, next_bundle_state
from src.engine.scalping.initial_quantity_timeout import build_bundle_timeout_schedule


def native_stock(*, filled=4, ordered=4):
    from src.engine import sniper_execution_receipts as receipts
    stock = dict(id=101, code='005930', strategy='SCALPING', status='BUY_ORDERED',
        entry_requested_qty=ordered, requested_buy_qty=ordered,
        pending_entry_orders=[dict(ord_no='0000123', qty=ordered, filled_qty=0, status='OPEN')])
    result = receipts._resolve_entry_effective_fill_qty(target_stock=stock, code='005930',
        order_no='0000123', exec_price=10000, exec_qty=filled, order_qty=ordered,
        remaining_qty=ordered-filled, cumulative_exec_amount=10000*filled,
        execution_no='E1', unit_exec_qty=filled, unit_exec_price=10000)
    assert result['status'] != 'invalid'
    stock.update(buy_qty=filled, buy_price=10000., entry_filled_qty=filled)
    return stock


def terminal_bundle(stock, root=None):
    schedule = build_bundle_timeout_schedule(quantity_type='KRX_PARENT', policy_sha256='a'*64,
        decision_at='2026-10-16T09:59:50+09:00', order_start_at='2026-10-16T10:00:00+09:00',
        total_wait_sec=60, leg_count=1, cancel_confirm_reserve_sec=5)
    qty, ordered = stock['buy_qty'], stock['entry_requested_qty']
    initial = new_bundle_state(attempt_id='stop-quantity-test', code='005930', target_id='101',
        schedule=schedule, requested_qty=ordered,
        planned_legs=[dict(leg_index=0, qty=ordered, price=10000, route='KRX', tag='parent')])
    from src.engine.scalping.initial_quantity_bundle_state import (
        create_indexed_bundle, save_bundle_state_cas, retire_indexed_bundle,
    )
    path = create_indexed_bundle(root, initial) if root is not None else None
    previous = initial
    def persisted(state):
        nonlocal previous
        if path is not None:
            save_bundle_state_cas(path, state, expected_parent_sha256=previous['bundle_content_sha256'])
        previous = state
        return state
    at = schedule['order_start_at_epoch']
    intent = persisted(next_bundle_state(initial, 0, dict(state='SUBMIT_INTENT', submit_intent_at_epoch=at)))
    opened = persisted(next_bundle_state(intent, 0, dict(state='OPEN', submit_intent_at_epoch=at,
        broker_order_no='0000123')))
    state = 'TERMINAL_FILLED' if qty == ordered else 'TERMINAL_CANCELLED'
    if state == 'TERMINAL_CANCELLED':
        opened = persisted(next_bundle_state(opened, 0, dict(state='PARTIAL', submit_intent_at_epoch=at,
            broker_order_no='0000123')))
        opened = persisted(next_bundle_state(opened, 0, dict(state='CANCEL_REQUESTED', submit_intent_at_epoch=at,
            broker_order_no='0000123')))
    terminal = persisted(next_bundle_state(opened, 0, dict(state=state, submit_intent_at_epoch=at,
        broker_order_no='0000123', terminal_confirmed=True, terminal_confirmed_at_epoch=at+10,
        broker_terminal_receipt_id='broker-proof', owner_registry_receipt_id='owner-proof',
        account_position_receipt_id='account-proof', broker_unfilled_qty=0,
        owner_registry_terminal=True, account_position_reconciled=True,
        ordered_qty=ordered, filled_qty=qty, cancelled_qty=ordered-qty)))
    if root is not None:
        assert retire_indexed_bundle(root, terminal)
    return terminal, at+11


def valid(receipt, stock, at):
    return quantity.validate_quantity_source(receipt, position_key=position_cycle_id(stock),
        quantity=stock['buy_qty'], buy_basis_krw=stock['buy_qty']*stock['buy_price'], at=at)


def test_actual_native_maps_and_full_order_census_ignore_notification_state():
    stock = native_stock()
    assert stock['_entry_receipt_economics_complete_by_order_no'] == {'0000123': 1}
    for notice in (False, True):
        stock['entry_partial_fill_deferred_notice'] = notice
        receipt = quantity.build_quantity_source(stock, at=1000.)
        assert receipt['status'] == 'full_fill' and valid(receipt, stock, 1000.)
        assert receipt['actual_order_submitted'] is False
        assert receipt['allowed_runtime_apply'] is False


@pytest.mark.parametrize('filled', [2, 4])
def test_native_terminal_bundle_preserves_full_vs_settled_partial(filled):
    stock = native_stock(filled=filled)
    bundle, at = terminal_bundle(stock)
    stock['initial_quantity_bundle'] = bundle
    stock['pending_entry_orders'] = []
    receipt = quantity.build_quantity_source(stock, at=at)
    assert receipt['status'] == ('full_fill' if filled == 4 else 'settled_partial')
    assert valid(receipt, stock, at)
    assert not valid(receipt, stock, at-2)


def test_terminal_retention_survives_bundle_metadata_clear_without_inventing_birth():
    stock = native_stock(filled=2)
    bundle, at = terminal_bundle(stock)
    stock['initial_quantity_last_terminal_bundle'] = bundle
    stock.pop('pending_entry_orders')
    stock.pop('entry_requested_qty')
    stock.pop('requested_buy_qty')
    receipt = quantity.build_quantity_source(stock, at=at)
    assert receipt['status'] == 'settled_partial' and valid(receipt, stock, at)
    assert receipt['known_at'] == at


def test_cleared_legacy_census_needs_preclear_receipt_and_same_native_generation():
    stock = native_stock()
    quantity.retain_quantity_source(stock, at=1000.)
    for key in ('pending_entry_orders','entry_requested_qty','requested_buy_qty','entry_filled_qty'):
        stock.pop(key, None)
    receipt = quantity.build_quantity_source(stock, at=1001.)
    assert receipt['status'] == 'full_fill' and valid(receipt, stock, 1001.)
    assert receipt['known_at'] == 1000.
    stock['buy_price'] = 10001.
    assert quantity.build_quantity_source(stock, at=1002.)['status'] == 'unknown'


@pytest.mark.parametrize('fault', ['no_orders','empty_maps','label_only','notice_only',
    'partial','pending_cancel','new_order','basis','future_terminal','wrong_target',
    'open_bundle','bad_economics','bool_requested','bool_order','too_many_executions',
    'probe_rebased_full_label'])
def test_missing_conflicting_or_later_sources_never_become_full(fault):
    stock = native_stock()
    at = 2000000000.
    if fault == 'no_orders': stock.pop('pending_entry_orders')
    elif fault == 'empty_maps': stock['_entry_receipt_filled_by_order_no'] = {}
    elif fault in ('label_only','notice_only'):
        stock = dict(id=101, code='005930', buy_qty=4, buy_price=10000.,
            entry_fill_quality='FULL_FILL', entry_partial_fill_deferred_notice=(fault == 'notice_only'))
    elif fault == 'partial': stock = native_stock(filled=2)
    elif fault == 'pending_cancel': stock['pending_entry_orders'][0]['cancel_terminal_pending'] = True
    elif fault == 'new_order': stock['pending_entry_orders'].append(dict(ord_no='0000124',qty=1,status='OPEN'))
    elif fault == 'basis': stock['buy_price'] = 10001.
    elif fault in ('future_terminal','wrong_target','open_bundle'):
        bundle, at = terminal_bundle(stock)
        if fault == 'future_terminal': at -= 2
        elif fault == 'wrong_target': bundle['target_id'] = '102'
        else: bundle['leg_states'][0]['state'] = 'OPEN'
        stock['initial_quantity_bundle'] = bundle
    elif fault == 'bad_economics': stock['_entry_receipt_economics_complete_by_order_no']['0000123'] = 0
    elif fault == 'bool_requested': stock['entry_requested_qty'] = True
    elif fault == 'bool_order': stock['pending_entry_orders'][0]['qty'] = True
    elif fault == 'too_many_executions':
        stock['_entry_receipt_executions_by_order_no']['0000123'] = {str(i):{} for i in range(257)}
    elif fault == 'probe_rebased_full_label':
        stock.update(entry_fill_quality='FULL_FILL', entry_split_probe_phase='aborted',
                     entry_split_probe_target_qty=10, entry_split_probe_requested_qty=4)
    receipt = quantity.build_quantity_source(stock, at=at)
    assert receipt['status'] == 'unknown' and not valid(receipt, stock, at)


def test_failed_retain_drops_stale_full_proof_and_restarted_label_is_unknown():
    stock = native_stock()
    quantity.retain_quantity_source(stock, at=1000.)
    assert quantity.RETAINED_KEY in stock
    stock['pending_entry_orders'][0]['cancel_terminal_pending'] = True
    quantity.retain_quantity_source(stock, at=1001.)
    assert quantity.RETAINED_KEY not in stock
    stock = dict(id=101, code='005930',buy_qty=4,buy_price=10000.,entry_fill_quality='FULL_FILL')
    assert quantity.build_quantity_source(stock, at=1002.)['status'] == 'unknown'


def test_receipt_seal_clock_and_quantity_generation_tamper_rejected():
    stock = native_stock()
    receipt = quantity.build_quantity_source(stock, at=1000.)
    for key, value in [('quantity',5), ('known_at',1001.), ('buy_basis_krw',40001.),
                       ('generation_sha256','a'*64),('buy_fill_identity','b'*64)]:
        changed = deepcopy(receipt)
        changed[key] = value
        changed['source_sha256'] = quantity._digest({k:v for k,v in changed.items() if k != 'source_sha256'})
        assert not valid(changed, stock, 1000.)


@pytest.mark.parametrize('at', [None, True, -1, float('nan'), float('inf')])
def test_bad_clock_is_sealed_unknown_and_cannot_grant_quantity(at):
    stock = native_stock()
    receipt = quantity.build_quantity_source(stock, at=at)
    assert receipt['status'] == 'unknown'
    assert not valid(receipt, stock, 2000.)


@pytest.mark.parametrize('filled', [2, 4])
def test_startup_recovers_existing_terminal_journal_once_without_runtime_adoption(tmp_path, filled):
    stock = native_stock(filled=filled)
    _, at = terminal_bundle(stock, tmp_path)
    for key in ('pending_entry_orders','entry_requested_qty','requested_buy_qty','entry_filled_qty',
                '_entry_receipt_requested_by_order_no','_entry_receipt_filled_amount_by_order_no',
                '_entry_receipt_economics_complete_by_order_no'):
        stock.pop(key, None)
    before = {str(p):p.read_bytes() for p in tmp_path.rglob('*.json')}
    assert quantity.restore_terminal_quantity_source(stock, bundle_root=tmp_path, at=at) == 'terminal_quantity_source_restored'
    assert 'initial_quantity_bundle' not in stock
    receipt = quantity.build_quantity_source(stock, at=at+1)
    assert receipt['status'] == ('full_fill' if filled == 4 else 'settled_partial')
    assert valid(receipt, stock, at+1)
    assert {str(p):p.read_bytes() for p in tmp_path.rglob('*.json')} == before


@pytest.mark.parametrize('fault', ['active','absent','wrong_basis','wrong_target','symlink','unbounded','changed'])
def test_startup_recovery_never_adopts_active_unbound_or_changed_journal(tmp_path, monkeypatch, fault):
    stock = native_stock()
    bundle, at = terminal_bundle(stock, tmp_path)
    from src.engine.scalping.initial_quantity_bundle_state import bundle_target_index_path
    index_path = bundle_target_index_path(tmp_path, '005930', '101')
    if fault == 'active': stock['initial_quantity_bundle'] = bundle
    elif fault == 'absent': index_path.unlink()
    elif fault == 'wrong_basis': stock['buy_price'] = 9999.
    elif fault == 'wrong_target': stock['id'] = 102
    elif fault == 'symlink':
        dest = tmp_path/'copy.json';dest.write_bytes(index_path.read_bytes())
        index_path.unlink();index_path.symlink_to(dest)
    elif fault == 'unbounded': index_path.write_text(' '*(quantity.MAX_BYTES+1))
    elif fault == 'changed':
        from src.engine.scalping import initial_quantity_bundle_state as native
        original = native.read_bundle_for_target
        def changing(*args, **kwargs):
            result = original(*args, **kwargs)
            index_path.write_bytes(index_path.read_bytes()+b' ')
            return result
        monkeypatch.setattr(native, 'read_bundle_for_target', changing)
    status = quantity.restore_terminal_quantity_source(stock, bundle_root=tmp_path, at=at)
    assert status != 'terminal_quantity_source_restored'
    assert 'initial_quantity_last_terminal_bundle' not in stock


def test_native_main_boot_restore_consumes_fill_then_terminal_source(tmp_path, monkeypatch):
    from src.engine import kiwoom_sniper_v2 as main
    from src.engine.ai.holding_exit_vote import persist_buy_fill_receipt
    stock = native_stock(filled=2)
    stock.update(name='QUANTITY_SOURCE_TEST', position_tag='SCALP_BASE',
                 buy_time='2026-10-16 10:00:00')
    terminal_bundle(stock, tmp_path/'runtime/initial_quantity/bundles')
    assert persist_buy_fill_receipt(stock, tmp_path)
    loaded = {key: stock[key] for key in ('id','code','name','strategy','status','buy_qty','buy_price',
                                         'position_tag','buy_time')}
    loaded['status'] = 'HOLDING'
    monkeypatch.setattr(main, 'DATA_DIR', tmp_path)
    monkeypatch.setattr(main, 'highest_prices', {})
    monkeypatch.setattr(main.POSITION_PEAK_LEDGER, 'restore_peak', lambda stock: (0, 'missing'))
    main._restore_holding_runtime_state([loaded])
    assert loaded['buy_fill_identity_restore_status'] == 'restored'
    assert loaded['main_stop_quantity_restore_status'] == 'terminal_quantity_source_restored'
    receipt = loaded[quantity.RETAINED_KEY]
    assert receipt['status'] == 'settled_partial' and valid(receipt, loaded, receipt['captured_at'])
    assert loaded['buy_qty'] == 2 and 'initial_quantity_bundle' not in loaded


def test_native_startup_second_read_never_falls_back_to_unbounded_read_bytes(tmp_path, monkeypatch):
    from pathlib import Path
    stock = native_stock()
    _, at = terminal_bundle(stock, tmp_path)
    def denied(*args, **kwargs):
        raise AssertionError('unbounded_read_bytes_called')
    monkeypatch.setattr(Path, 'read_bytes', denied)
    assert quantity.restore_terminal_quantity_source(stock, bundle_root=tmp_path, at=at) == 'terminal_quantity_source_restored'


def test_atomic_growth_between_admission_and_native_reader_is_bounded(tmp_path, monkeypatch):
    from src.engine.scalping import initial_quantity_bundle_state as native
    stock = native_stock()
    _, at = terminal_bundle(stock, tmp_path)
    path = native.bundle_target_index_path(tmp_path, '005930', '101')
    original = native.read_bundle_for_target
    def growing(*args, **kwargs):
        assert kwargs.get('read_object') is not None
        path.write_text(' '*(quantity.MAX_BYTES+1))
        return original(*args, **kwargs)
    monkeypatch.setattr(native, 'read_bundle_for_target', growing)
    assert quantity.restore_terminal_quantity_source(stock, bundle_root=tmp_path, at=at) != 'terminal_quantity_source_restored'
    assert 'initial_quantity_last_terminal_bundle' not in stock
