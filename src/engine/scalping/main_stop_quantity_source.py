"""Bound existing BUY receipts to one stop-research quantity generation.

Builders/validators are pure and bounded. The explicit startup restorer reads
only the existing terminal journal. No broker calls, quantity mutation, or
terminal inference from notifications, labels, empty maps, or local expiry.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math

from .position_peak_ledger import position_cycle_id

SCHEMA = 'main_stop_quantity_source_v1'
MAX_BYTES = 65536
MAX_ORDERS = 32
MAX_EXECUTIONS = 256
RETAINED_KEY = '_main_stop_quantity_source'
FILL_KEYS = ('_entry_receipt_filled_by_order_no',
             '_entry_receipt_executions_by_order_no',
             '_entry_receipt_requested_by_order_no',
             '_entry_receipt_filled_amount_by_order_no',
             '_entry_receipt_economics_complete_by_order_no',
             'holding_buy_fill_legs')


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def _number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def _integer(value, *, zero=False):
    return type(value) is int and value >= (0 if zero else 1)


def _bounded(value):
    """Admit the tree before copying/encoding any runtime receipt maps."""
    remaining = 4096
    def visit(item, depth=0):
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 12:
            raise ValueError('quantity_proof_budget_exceeded')
        if isinstance(item, dict):
            if len(item) > MAX_EXECUTIONS:
                raise ValueError('quantity_proof_budget_exceeded')
            for key, child in item.items():
                if not isinstance(key, str) or len(key) > 240:
                    raise ValueError('quantity_proof_identity_invalid')
                visit(child, depth+1)
        elif isinstance(item, list):
            if len(item) > MAX_EXECUTIONS:
                raise ValueError('quantity_proof_budget_exceeded')
            for child in item:
                visit(child, depth+1)
        elif isinstance(item, str):
            if len(item) > 1024:
                raise ValueError('quantity_proof_budget_exceeded')
        elif item is not None and not isinstance(item, bool) and not _number(item):
            raise ValueError('quantity_proof_value_invalid')
    visit(value)
    if len(json.dumps(value, ensure_ascii=True, allow_nan=False)) > MAX_BYTES:
        raise ValueError('quantity_proof_budget_exceeded')


def _fill_facts(snapshot):
    from src.engine.ai.holding_exit_vote import (
        buy_fill_legs_from_runtime, buy_fill_identity_from_legs,
    )
    filled = snapshot.get('_entry_receipt_filled_by_order_no')
    executions = snapshot.get('_entry_receipt_executions_by_order_no')
    if (not isinstance(filled, dict) or not filled or len(filled) > MAX_ORDERS
            or not isinstance(executions, dict) or set(executions) != set(filled)
            or sum(len(v) if isinstance(v, dict) else MAX_EXECUTIONS+1
                   for v in executions.values()) > MAX_EXECUTIONS):
        raise ValueError('native_buy_fill_census_missing')
    legs = buy_fill_legs_from_runtime(snapshot)
    identity = buy_fill_identity_from_legs(legs)
    if not legs or not identity:
        raise ValueError('native_buy_fill_identity_unverified')
    if {leg['order_no'] for leg in legs} != set(filled):
        raise ValueError('native_buy_fill_census_changed')
    facts = {}
    for order, quantity in filled.items():
        if not isinstance(order, str) or not order or order.startswith('__') or not _integer(quantity):
            raise ValueError('native_buy_fill_identity_unverified')
        prior_qty, prior_amount, ordered = 0, 0, None
        for signature in sorted(executions[order].values(), key=lambda s: s['cumulative_qty']):
            cumulative = signature['cumulative_qty']
            delta = cumulative-prior_qty
            order_qty, remaining = signature.get('order_qty'), signature.get('remaining_qty')
            if (not _integer(cumulative) or delta <= 0 or not _integer(order_qty)
                    or not _integer(remaining, zero=True) or cumulative+remaining != order_qty
                    or ordered is not None and order_qty != ordered):
                raise ValueError('native_buy_order_quantity_unverified')
            unit_qty, unit_price = signature.get('unit_exec_qty'), signature.get('unit_exec_price')
            amount = signature.get('cumulative_exec_amount')
            if unit_qty is not None and (not _integer(unit_qty) or unit_qty != delta):
                raise ValueError('native_buy_unit_quantity_conflict')
            if amount is None:
                if unit_qty != delta or not _integer(unit_price):
                    raise ValueError('native_buy_basis_unverified')
                amount = prior_amount+delta*unit_price
            if (not _integer(amount) or amount <= prior_amount or
                    unit_price is not None and (not _integer(unit_price) or
                        unit_qty is not None and amount-prior_amount != unit_qty*unit_price)):
                raise ValueError('native_buy_basis_conflict')
            ordered, prior_qty, prior_amount = order_qty, cumulative, amount
        if prior_qty != quantity:
            raise ValueError('native_buy_fill_quantity_conflict')
        for key, expected in (('_entry_receipt_requested_by_order_no', ordered),
                              ('_entry_receipt_filled_amount_by_order_no', prior_amount)):
            declared = snapshot.get(key)
            if declared is not None and (not isinstance(declared, dict)
                    or set(declared) != set(filled) or declared.get(order) != expected):
                raise ValueError('native_buy_receipt_map_conflict')
        complete = snapshot.get('_entry_receipt_economics_complete_by_order_no')
        if complete is not None and (not isinstance(complete, dict)
                or set(complete) != set(filled) or type(complete.get(order)) not in (bool, int)
                or complete.get(order) != 1):
            raise ValueError('native_buy_basis_unverified')
        facts[order] = dict(filled_qty=quantity, ordered_qty=ordered, amount=prior_amount,
            remaining_qty=ordered-quantity)
    return facts, identity


def _proven(proof, quantity, basis, at):
    _bounded(proof)
    snapshot = proof['fill_receipts']
    facts, identity = _fill_facts(snapshot)
    if (sum(row['filled_qty'] for row in facts.values()) != quantity
            or not math.isclose(sum(row['amount'] for row in facts.values()), basis,
                                rel_tol=1e-12, abs_tol=1e-6)):
        raise ValueError('native_buy_position_basis_changed')
    kind = proof.get('evidence_kind')
    if kind == 'native_bundle_terminal':
        from .initial_quantity_bundle_state import bundle_state_valid, bundle_is_terminal
        bundle = proof['bundle']
        if (not bundle_state_valid(bundle) or not bundle_is_terminal(bundle)
                or bundle['target_id'] != str(proof['record_id']) or bundle['code'] != proof['code']):
            raise ValueError('native_buy_bundle_terminal_unverified')
        selected = {}
        for leg, state in zip(bundle['planned_legs'], bundle['leg_states']):
            if not _number(state.get('terminal_confirmed_at_epoch')) or state['terminal_confirmed_at_epoch'] > at:
                raise ValueError('native_buy_terminal_not_yet_known')
            filled = state.get('filled_qty', 0)
            if filled:
                order = state['broker_order_no']
                if order in selected or not _integer(filled):
                    raise ValueError('native_buy_bundle_order_conflict')
                selected[order] = (filled, leg['qty'])
        if set(selected) != set(facts) or any(selected[o] != (r['filled_qty'], r['ordered_qty'])
                                               for o, r in facts.items()):
            raise ValueError('native_buy_bundle_fill_census_conflict')
        status = 'full_fill' if quantity == bundle['requested_qty'] else 'settled_partial'
    elif kind == 'native_filled_order_census':
        orders = proof['orders']
        if not isinstance(orders, list) or not orders or len(orders) > MAX_ORDERS:
            raise ValueError('native_buy_order_census_missing')
        indexed = {}
        for order in orders:
            key = order.get('ord_no')
            if (key in indexed or key not in facts or order.get('status') != 'FILLED'
                    or not _integer(order.get('qty')) or not _integer(order.get('filled_qty'))
                    or order.get('qty') != facts[key]['filled_qty']
                    or order.get('filled_qty') != facts[key]['filled_qty']
                    or facts[key]['remaining_qty'] != 0
                    or any(order.get(k) for k in ('cancel_terminal_pending',
                        'owner_registry_cancel_reconciliation_required', 'entry_reprice_cancel_terminal_pending'))):
                raise ValueError('native_buy_order_terminal_unverified')
            indexed[key] = order
        if (set(indexed) != set(facts) or not _integer(proof.get('requested_qty'))
                or proof.get('requested_qty') != quantity):
            raise ValueError('native_buy_order_census_conflict')
        status = 'full_fill'
    else:
        raise ValueError('native_buy_terminal_source_missing')
    return status, identity


def validate_quantity_source(receipt, *, position_key, at, quantity, buy_basis_krw):
    try:
        _bounded(receipt)
        if (receipt.get('schema') != SCHEMA or receipt.get('position_key') != position_key
                or receipt.get('source_sha256') != _digest({k:v for k,v in receipt.items() if k != 'source_sha256'})
                or not _number(at) or not _integer(quantity) or not _number(buy_basis_krw)
                or quantity != receipt.get('quantity') or buy_basis_krw != receipt.get('buy_basis_krw')
                or not _number(receipt.get('known_at')) or not _number(receipt.get('captured_at'))
                or not 0 < receipt['known_at'] <= receipt['captured_at'] <= at
                or receipt.get('allowed_runtime_apply') is not False
                or receipt.get('actual_order_submitted') is not False):
            return False
        proof = receipt['proof']
        if (receipt.get('generation_sha256') != _digest(dict(position_key=position_key,
                quantity=quantity, buy_basis_krw=buy_basis_krw, proof=proof))
                or proof.get('position_key') != position_key
                or receipt.get('evidence_kind') != proof.get('evidence_kind')):
            return False
        status, identity = _proven(proof, quantity, buy_basis_krw, receipt['known_at'])
        return receipt.get('status') == status and receipt.get('buy_fill_identity') == identity
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return False


def _pending(stock):
    return any(stock.get(key) for key in ('pending_add_qty', 'pending_add_ord_no', 'pending_add_order',
        'pending_add_ord_nos', 'add_count', '_add_receipt_filled_by_order_no',
        'scale_in_submit_reserved_qty',
        'entry_cancel_terminal_reconciliation_required', 'entry_reprice_cancel_terminal_pending',
        'owner_registry_reconciliation_required'))


def build_quantity_source(stock, *, at):
    """Use only the in-memory native sources available at this evaluation."""
    key, quantity, average = position_cycle_id(stock), stock.get('buy_qty'), stock.get('buy_price')
    basis = quantity*average if _integer(quantity) and _number(quantity) and _number(average) else None
    if not _number(basis):
        basis = None
    result = dict(schema=SCHEMA, position_key=key, quantity=quantity if _number(quantity) else None,
        buy_basis_krw=basis, known_at=at if _number(at) else None,
        captured_at=at if _number(at) else None, status='unknown',
        reason='native_buy_terminal_source_missing', evidence_kind=None, proof=None,
        buy_fill_identity=None, generation_sha256=None,
        actual_order_submitted=False, allowed_runtime_apply=False)
    try:
        if not _number(at) or at <= 0 or not _integer(quantity) or not _number(basis) or basis <= 0 or _pending(stock):
            raise ValueError('quantity_or_entry_generation_unsettled')
        snapshot = {name: stock[name] for name in FILL_KEYS if stock.get(name) is not None}
        _bounded(snapshot)
        facts, _ = _fill_facts(snapshot)
        active = stock.get('initial_quantity_bundle')
        bundle = active if active is not None else stock.get('initial_quantity_last_terminal_bundle')
        orders = stock.get('pending_entry_orders')
        if bundle is None and any(stock.get(name) for name in (
                'entry_split_probe_bundle_id', 'entry_split_order_probe_first_applied',
                'entry_split_probe_requested_qty', 'entry_split_probe_target_qty',
                'entry_split_probe_phase', 'entry_split_probe_abort_reason',
                'entry_split_probe_partial_complete_qty')):
            # Probe abort/rebase may replace requested quantities with holdings.
            # Exact fills of submitted orders alone do not settle unsent legs.
            raise ValueError('legacy_probe_target_generation_unverified')
        if bundle is None and not orders:
            retained = stock.get(RETAINED_KEY)
            if (validate_quantity_source(retained, position_key=key, at=at,
                    quantity=quantity, buy_basis_krw=basis)
                    and retained['proof']['fill_receipts'] == snapshot
                    and not any(stock.get(name) for name in ('entry_requested_qty', 'requested_buy_qty'))):
                return deepcopy(retained)
            raise ValueError('native_buy_order_census_missing')
        proof = dict(position_key=key, code=str(stock.get('code') or '')[:6],
            record_id=stock.get('id'), fill_receipts=deepcopy(snapshot))
        if bundle is not None:
            _bounded(bundle)
            proof.update(evidence_kind='native_bundle_terminal', bundle=deepcopy(bundle))
            # A new/open order cannot be hidden behind a prior terminal bundle.
            if orders and any(not isinstance(o, dict) or o.get('ord_no') not in facts
                    or o.get('filled_qty') != facts[o['ord_no']]['filled_qty']
                    or o.get('cancel_terminal_pending') for o in orders):
                raise ValueError('native_buy_order_census_conflict')
        else:
            _bounded(orders)
            requested = stock.get('entry_requested_qty', stock.get('requested_buy_qty'))
            if any(stock.get(name, requested) != requested
                   for name in ('entry_requested_qty', 'requested_buy_qty')):
                raise ValueError('native_buy_requested_quantity_conflict')
            proof.update(evidence_kind='native_filled_order_census',
                orders=[{k:o.get(k) for k in ('ord_no','qty','filled_qty','status',
                    'cancel_terminal_pending','owner_registry_cancel_reconciliation_required',
                    'entry_reprice_cancel_terminal_pending')} for o in orders], requested_qty=requested)
        status, identity = _proven(proof, quantity, basis, at)
        result.update(status=status, reason='native_buy_terminal_and_position_bound',
            evidence_kind=proof['evidence_kind'], proof=proof, buy_fill_identity=identity,
            generation_sha256=_digest(dict(position_key=key, quantity=quantity, buy_basis_krw=basis, proof=proof)))
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as exc:
        result['reason'] = str(exc) if isinstance(exc, ValueError) else 'native_buy_receipt_invalid'
    return {**result, 'source_sha256': _digest(result)}


def retain_quantity_source(stock, *, at):
    """Called before native metadata clear; keep only independently valid proof."""
    receipt = build_quantity_source(stock, at=at)
    if receipt['status'] in {'full_fill', 'settled_partial'}:
        stock[RETAINED_KEY] = receipt
    else:
        stock.pop(RETAINED_KEY, None)


def restore_terminal_quantity_source(stock, *, bundle_root, at):
    """Startup only: validate an existing terminal journal, without adoption.

    Never restore an active bundle, request a broker snapshot, or read files on
    the stop hot path. Original BUY receipt maps must already be restored.
    """
    from pathlib import Path
    from .initial_quantity_bundle_state import (
        bundle_target_index_path, bundle_state_path, read_bundle_for_target,
    )
    from .main_stop_policy import bounded_object
    if stock.get('initial_quantity_bundle') is not None:
        return 'active_bundle_owned_elsewhere'
    try:
        root = Path(bundle_root).absolute()
        if any(p.is_symlink() for p in (root, *root.parents)):
            return 'terminal_quantity_path_invalid'
        code, record = str(stock.get('code') or '')[:6], str(stock.get('id') or '')
        index_path = bundle_target_index_path(root, code, record)
        if not index_path.exists():
            return 'terminal_quantity_index_absent'
        index, index_sha = bounded_object(index_path, MAX_BYTES)
        if index.get('phase') != 'terminal':
            return 'terminal_quantity_index_not_terminal'
        journal_path = bundle_state_path(root, index['attempt_id'])
        journal, journal_sha = bounded_object(journal_path, MAX_BYTES)
        # The native second read is bounded too, including a file replaced
        # between admission and native identity validation.
        bundle, status = read_bundle_for_target(root, code, record,
            read_object=lambda path: bounded_object(path, MAX_BYTES)[0])
        if status != 'target_bundle_terminal' or bundle != journal:
            return 'terminal_quantity_native_journal_unverified'
        candidate = dict(stock, initial_quantity_last_terminal_bundle=bundle)
        source = build_quantity_source(candidate, at=at)
        if source['status'] not in {'full_fill', 'settled_partial'}:
            return 'terminal_quantity_fill_binding_unverified:' + source['reason']
        if (bounded_object(index_path, MAX_BYTES)[1] != index_sha
                or bounded_object(journal_path, MAX_BYTES)[1] != journal_sha):
            return 'terminal_quantity_journal_changed'
        stock['initial_quantity_last_terminal_bundle'] = deepcopy(bundle)
        stock[RETAINED_KEY] = source
        stock['main_stop_quantity_restore_source'] = dict(index_sha256=index_sha,
            journal_sha256=journal_sha, bundle_content_sha256=bundle['bundle_content_sha256'],
            restored_at=at, runtime_effect=False, allowed_runtime_apply=False)
        return 'terminal_quantity_source_restored'
    except (OSError, ValueError, KeyError, TypeError, AttributeError, OverflowError):
        return 'terminal_quantity_source_unverified'
