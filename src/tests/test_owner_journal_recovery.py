"""Journal cache publication and append-only recovery of an existing full fill."""
import copy
import hashlib
import json
import threading

import pytest

from src.trading.order.owner_custody_registry import (
    OwnerOrderContext, OrderOwnerRegistry, OwnerRegistryConflict,
)
from src.trading.order import owner_journal_recovery as R


@pytest.fixture
def bound(tmp_path, monkeypatch):
    monkeypatch.setenv('KORSTOCKSCAN_BROKER_ACCOUNT_KEY', 'journal-test-account')
    monkeypatch.setenv('KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE', str(tmp_path/'excluded'))
    monkeypatch.delenv('KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES', raising=False)
    registry = OrderOwnerRegistry(tmp_path/'journal.jsonl')
    ctx = OwnerOrderContext('main_scalping', 'main_scalping:123', 'main_scalping:123', 'entry:123')
    intent = registry.reserve(context=ctx, symbol='034020', side='BUY', quantity=1,
                              route='NXT', order_date='2026-10-15')
    registry.transition(intent, state='ORDER_BOUND', broker_order_no='0057428')
    registry._read_locked()  # warm the pre-fill generation
    return registry, ctx, intent


def fill(registry, ctx):
    registry.record_fill(context=ctx, symbol='034020', side='BUY', order_quantity=1,
        order_date='2026-10-15', broker_order_no='0057428', cumulative_filled_qty=1,
        cumulative_fill_amount=62600, execution_no='142564')


def test_cache_publication_cannot_pair_new_signature_with_pre_fill_events(bound, monkeypatch):
    registry, ctx, intent = bound
    fill(registry, ctx)
    copying, resume = threading.Event(), threading.Event()
    original = copy.deepcopy
    errors = []

    def pause_new_snapshot(value, *args, **kwargs):
        if (threading.current_thread().name == 'journal-cache-reader'
                and isinstance(value, list) and len(value) == 3):
            copying.set()
            if not resume.wait(5):
                raise AssertionError('reader was not released')
        return original(value, *args, **kwargs)

    monkeypatch.setattr(copy, 'deepcopy', pause_new_snapshot)

    def reader():
        try:
            registry._read_locked()
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=reader, name='journal-cache-reader')
    thread.start()
    try:
        assert copying.wait(5)
        registry.transition(intent, state='ORDER_TERMINAL', broker_order_no='0057428',
                            reason='shared_ws_execution_receipt_terminal')
    finally:
        resume.set()
        thread.join(5)
    assert not thread.is_alive() and not errors
    # Cold verification cannot hide a stale cache or a forked hash chain.
    cold = OrderOwnerRegistry(registry.path)
    events = cold.verified_events_snapshot()
    assert len(events) == 4
    assert events[-1]['previous_hash'] == events[-2]['event_hash']
    assert events[-1]['filled_qty'] == 1 and events[-1]['fill_amount'] == 62600


def stale_tail(bound):
    registry, ctx, intent = bound
    before = registry._read_locked()
    fill(registry, ctx)
    anchor = before[-1]
    payload = {k: anchor.get(k) for k in R.IDENTITY}
    payload.update(event='ORDER_TERMINAL', state='ORDER_TERMINAL', filled_qty=0,
                   fill_amount=0, reason='shared_ws_execution_receipt_terminal')
    registry._append_locked(before, payload)  # reproduce the former stale-cache writer
    return registry.path.read_bytes()


def test_recovery_appends_only_and_cold_reader_restores_existing_full_fill(bound):
    registry, ctx, _ = bound
    original = stale_tail(bound)
    digest = hashlib.sha256(original).hexdigest()
    with pytest.raises(OwnerRegistryConflict, match='chain_invalid'):
        registry.verified_events_snapshot()
    preview = registry.reconcile_stale_terminal_tail(expected_sha256=digest)
    assert preview['status'] == 'validated' and registry.path.read_bytes() == original
    result = registry.reconcile_stale_terminal_tail(expected_sha256=digest, apply=True)
    assert result['status'] == 'applied' and not result['broker_order_attempted']
    assert registry.path.read_bytes().startswith(original)
    cold = OrderOwnerRegistry(registry.path)
    events = cold.verified_events_snapshot()
    assert len(events) == 5 and events[-1]['event'] == R.EVENT
    row = cold.order_owner(order_date='2026-10-15', broker_order_no='0057428')
    assert row['state'] == 'ORDER_TERMINAL' and row['filled_qty'] == 1
    assert row['fill_amount'] == 62600 and row['execution_no'] == '142564'
    assert row['fill_observed_at_kst'] == events[-3]['observed_at_kst']
    assert cold.owner_position_qty(ctx.position_id, symbol='034020') == 1
    # A normal subsequent append and a new cold read must retain the repair.
    cold.retire_automatic_owners_to_manual()
    assert OrderOwnerRegistry(registry.path).native_owner_contract('034020')['registered']
    with pytest.raises(OwnerRegistryConflict, match='source_changed'):
        cold.reconcile_stale_terminal_tail(expected_sha256=digest, apply=True)


@pytest.mark.parametrize('damage', [
    'partial', 'sell', 'retired_owner', 'foreign_order', 'wrong_reason', 'fill_hash',
    'terminal_hash', 'unknown_field', 'missing_execution', 'truncated', 'source_sha',
])
def test_recovery_rejects_unsupported_or_unverified_source_without_mutation(bound, damage):
    registry, _, _ = bound
    raw = stale_tail(bound)
    rows = [json.loads(line) for line in raw.splitlines()]
    if damage == 'partial': rows[-2]['filled_qty'] = 0
    if damage == 'sell': rows[-1]['side'] = 'SELL'
    if damage == 'retired_owner': rows[-1]['owner_type'] = 'episode'
    if damage == 'foreign_order': rows[-1]['broker_order_no'] = '0057429'
    if damage == 'wrong_reason': rows[-1]['reason'] = 'guessed_terminal'
    if damage == 'fill_hash': rows[-2]['event_hash'] = '0'*64
    if damage == 'terminal_hash': rows[-1]['event_hash'] = '0'*64
    if damage == 'unknown_field': rows[-1]['canceled_qty'] = 1
    if damage == 'missing_execution': rows[-2]['execution_no'] = ''
    raw = b''.join((json.dumps(r, sort_keys=True, separators=(',', ':'))+'\n').encode() for r in rows)
    if damage == 'truncated': raw = raw.rstrip()
    registry.path.write_bytes(raw)
    digest = 'f'*64 if damage == 'source_sha' else hashlib.sha256(raw).hexdigest()
    with pytest.raises(OwnerRegistryConflict):
        registry.reconcile_stale_terminal_tail(expected_sha256=digest, apply=True)
    assert registry.path.read_bytes() == raw


@pytest.mark.parametrize('damage', ['quantity', 'prefix_hash', 'prefix_bytes', 'fill_hash',
                                    'extra_field', 'unbound', 'receipt_hash', 'missing', 'bool_quantity'])
def test_cold_reader_rejects_forged_or_missing_recovery_receipt(bound, damage):
    registry, _, _ = bound
    raw = stale_tail(bound)
    registry.reconcile_stale_terminal_tail(expected_sha256=hashlib.sha256(raw).hexdigest(), apply=True)
    receipt = json.loads(registry.path.read_bytes().splitlines()[-1])
    if damage == 'quantity': receipt['filled_qty'] = 2
    if damage == 'bool_quantity': receipt['filled_qty'] = True
    if damage == 'prefix_hash': receipt['recovery_source']['journal_prefix_sha256'] = '0'*64
    if damage == 'prefix_bytes': receipt['recovery_source']['journal_prefix_bytes'] += 1
    if damage == 'fill_hash': receipt['recovery_source']['fill_event_hash'] = '0'*64
    if damage == 'extra_field': receipt['canceled_qty'] = 1
    if damage == 'unbound': receipt['previous_hash'] = '0'*64
    receipt['event_hash'] = hashlib.sha256(receipt['previous_hash'].encode()
                                         + registry._canonical(receipt)).hexdigest()
    if damage == 'receipt_hash': receipt['event_hash'] = '0'*64
    tail = b'' if damage == 'missing' else (json.dumps(receipt)+'\n').encode()
    registry.path.write_bytes(raw + tail)
    with pytest.raises(OwnerRegistryConflict):
        OrderOwnerRegistry(registry.path).verified_events_snapshot()


@pytest.mark.parametrize('defect', ['partial', 'sell', 'retired', 'wrong_intent',
                                   'missing_execution', 'canceled', 'unknown_history'])
def test_recovery_proof_itself_rejects_semantically_unsupported_history(bound, defect):
    raw = stale_tail(bound)
    rows = [json.loads(line) for line in raw.splitlines()]
    if defect == 'partial': rows[-2]['filled_qty'] = 0
    if defect in {'sell', 'retired'}:
        for row in rows:
            row['side' if defect == 'sell' else 'owner_type'] = 'SELL' if defect == 'sell' else 'episode'
    if defect == 'wrong_intent': rows[-1]['intent_id'] = 'foreign'
    if defect == 'missing_execution': rows[-2]['execution_no'] = ''
    if defect == 'canceled': rows[-2]['canceled_qty'] = 1
    if defect == 'unknown_history': rows.insert(1, dict(rows[0], event='UNKNOWN_EVENT'))
    with pytest.raises(ValueError, match='proof_invalid'):
        R.recovery_payload(rows[:-1], rows[-1], raw)
