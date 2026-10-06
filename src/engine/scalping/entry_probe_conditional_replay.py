"""Frozen SCALPING probe plans and causal price reconstruction, without orders.

This owner consumes verified original receipts. It never estimates a broker
fill or turns a price reconstruction into paired EV or execution authority.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import math
from functools import lru_cache
from pathlib import Path
import re
from types import FunctionType, SimpleNamespace
import os

from src.engine.scalping.strategy_owner_components import digest

SCHEMA = 'entry_probe_conditional_plan_v1'
REPLAY_SCHEMA = 'entry_probe_conditional_replay_v1'
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False,
                 actual_order_submitted=False, broker_order_forbidden=True)


def seal(value, field='seed_sha256'):
    body = deepcopy({k: v for k, v in value.items() if k != field})
    return {**body, field: digest(body)}


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def clock(value):
    if number(value):
        return value
    stamp = datetime.fromisoformat(value)
    if stamp.tzinfo is None:
        raise ValueError('conditional_clock_timezone_missing')
    return stamp.timestamp()


@lru_cache(maxsize=32)
def _kernel_sha(path, signature):
    value = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    stat = Path(path).stat()
    if signature != (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns):
        raise ValueError('conditional_kernel_changed_during_read')
    return value


def kernel_identity():
    # Includes the native P1 resolver and quantity distribution owner.
    root = Path(__file__).resolve().parents[1]
    paths = (root / 'sniper_entry_latency.py', Path(__file__),
             root / 'scalping/entry_split_order_plan.py',
             root.parent / 'trading/order/tick_utils.py')
    result = {}
    for path in paths:
        stat = path.stat()
        result[str(path.relative_to(root.parent.parent))] = _kernel_sha(str(path),
            (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))
    return result


def valid_seed(seed):
    try:
        plan, context = seed['atomic_plan'], seed['operating_contract']
        total, legs = seed['total_qty'], plan['legs']
        return bool(seed.get('schema') == SCHEMA and seed == seal(seed)
            and all(seed.get(k) is v for k, v in AUTHORITY.items())
            and seed.get('reservation_performed') is False
            and plan.get('valid') is True and not plan.get('blockers')
            and digest(plan) == seed['plan_sha256']
            and context.get('sha256') == digest({k:v for k,v in context.items() if k!='sha256'})
            and context.get('schema') == 'entry_split_operating_economics_v1'
            and number(context['budget_krw']) and context['budget_krw'] > 0
            and type(total) is int and total > 1 and plan['total_qty'] == total
            and plan['immediate_qty'] == 1 and plan['deferred_probe_residual_qty'] == total - 1
            and legs[0]['execution_phase'] == 'immediate' and legs[0]['qty'] == 1
            and all(type(x['qty']) is int and x['qty'] > 0 for x in legs)
            and sum(x['qty'] for x in legs) == total
            and all(x['execution_phase'] == 'after_verified_probe_fill' and x['numeric_price'] is None
                    for x in legs[1:])
            and [x['qty'] for x in legs[1:]] == seed['continuation']['residual_quantities']
            and seed['continuation']['requested_qty'] == total
            and seed['continuation']['residual_qty'] == total - 1
            and seed['evaluation_attempt_id'] == plan['action_receipt_id']
            and seed['scanner_promotion_id'] == plan['scanner_promotion_id']
            and seed['policy_bundle_hash'] == plan['policy_bundle_hash']
            and re.fullmatch(r'[0-9a-f]{64}', seed['policy_bundle_hash'])
            and re.fullmatch(r'[0-9]{6}', seed['stock_code'])
            and seed['effective_venue'] == plan['effective_venue']
            and seed['session_bucket'] == plan['market_session_bucket']
            and seed['source_date'] >= '2026-09-29'
            and seed['observed_at'][:10] == seed['source_date']
            and clock(context['frozen_at']) <= clock(seed['observed_at'])
            and seed['price_kernel_identity']
            and all(re.fullmatch(r'[0-9a-f]{64}', str(v)) for v in seed['price_kernel_identity'].values())
            and type(seed['pricing_rules']['SCALPING_ENTRY_PRICE_RESOLVER_ENABLED']) is bool
            and type(seed['pricing_rules']['SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS']) is int
            and seed['pricing_rules']['SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS'] > 0
            and seed.get('source_identity', {}).get('evaluation_attempt_id') == seed['evaluation_attempt_id']
            and number(seed['max_slippage_bps']) and seed['max_slippage_bps'] >= 0
            and type(seed['probe_reference_ask']) is int and seed['probe_reference_ask'] > 0
            and number(seed['probe_timeout_sec']) and seed['probe_timeout_sec'] > 0)
    except (TypeError, KeyError, ValueError, AttributeError, IndexError, OverflowError):
        return False


def freeze_conditional_plan(plan, *, stock_code, observed_at, operating_context=None,
                            probe_order=None, source_identity=None, diagnostic=None, **unused):
    from src.engine.scalping.strategy_owner_replay import KST, entry_operating_route_supported
    try:
        context = deepcopy(operating_context or {})
        order = probe_order or {}
        rules = (context.get('policy_snapshot') or {}).get('rules') or {}
        pricing_rules = {key: deepcopy(rules[key]) for key in (
            'SCALPING_ENTRY_PRICE_RESOLVER_ENABLED', 'SCALPING_ENTRY_PRICE_RESOLVER_MAX_BELOW_BID_BPS')}
        stamp = datetime.fromtimestamp(observed_at, KST).isoformat()
        seed = seal(dict(schema=SCHEMA, source_date=stamp[:10], observed_at=stamp,
            stock_code=stock_code, evaluation_attempt_id=plan['action_receipt_id'],
            scanner_promotion_id=plan['scanner_promotion_id'],
            effective_venue=plan['effective_venue'], session_bucket=plan['market_session_bucket'],
            policy_bundle_hash=plan['policy_bundle_hash'], total_qty=plan['total_qty'],
            policy_bundle_sha256=plan['policy_bundle_hash'],
            entry_price_policy_sha256=plan['price_policy_sha256'],
            atomic_plan=deepcopy(plan), plan_sha256=digest(plan), operating_contract=context,
            continuation=deepcopy(order.get('entry_split_order_probe_continuation') or {}),
            probe_timeout_sec=order.get('entry_split_order_probe_timeout_sec'),
            max_slippage_bps=order.get('entry_split_order_probe_max_slippage_bps'),
            anchor_mode=order.get('entry_split_order_probe_anchor_mode'),
            probe_reference_ask=order.get('price'),
            observed_machine_action=plan.get('observed_machine_action'),
            source_identity=deepcopy(source_identity or {}), pricing_rules=pricing_rules,
            runtime_pid=os.getpid(),
            price_kernel_identity=kernel_identity(), reservation_performed=False, **AUTHORITY))
        if (not valid_seed(seed) or not entry_operating_route_supported(seed['effective_venue'],
                seed['session_bucket'], context.get('broker_route'))):
            raise ValueError('conditional_plan_or_operating_contract_invalid')
        if isinstance(diagnostic, dict):
            diagnostic.update(status='recorded_conditional_source_only', blocker=None)
        return seed
    except (KeyError, TypeError, ValueError, OSError, OverflowError) as exc:
        if isinstance(diagnostic, dict):
            diagnostic.update(status='source_gap', blocker=str(exc))
        return None


def native_receipt(seed, *, kind, sequence, event_at, available_at, source, **fields):
    """Bind an already observed native result. No reads, guesses or state writes."""
    if not valid_seed(seed):
        raise ValueError('conditional_seed_invalid')
    value = dict(kind=kind, sequence=sequence, event_at=event_at, available_at=available_at,
        evaluation_attempt_id=seed['evaluation_attempt_id'], plan_sha256=seed['plan_sha256'],
        stock_code=seed['stock_code'], effective_venue=seed['effective_venue'],
        session_bucket=seed['session_bucket'], source_sha256=digest(source),
        native_source=deepcopy(source), **fields)
    return seal(value, 'sha256')


def operating_source_gaps(seed):
    """Contract inventory, independent of price reconstruction or actual PnL."""
    context = seed.get('operating_contract') if isinstance(seed, dict) else None
    context = context if isinstance(context, dict) else {}
    gaps = ['operating_'+key+'_missing' for key in ('cost_policy_version', 'cost_provenance',
        'exit_policy_version', 'initial_fill_exit_state', 'order_leg_ttl_sec',
        'order_timeout_owner', 'policy_snapshot', 'initial_policy_state',
        'conditional_residual_ttl_contract') if not context.get(key)]
    if (not number(context.get('cost_rate')) or context['cost_rate'] < 0):
        gaps.append('operating_cost_rate_missing_or_invalid')
    capital = context.get('capital_source') or {}
    capital = capital if isinstance(capital, dict) else {}
    if (capital.get('status') != 'recorded_source_only'
            or capital.get('sha256') != digest({k:v for k,v in capital.items() if k!='sha256'})):
        gaps.append('exact_capital_source_missing_or_invalid')
    return gaps


def frozen_native_pricer(seed):
    from src.engine.sniper_entry_latency import resolve_scalping_entry_price
    # The post-probe branch uses these two rules and pure tick helpers. Clone
    # the function's namespace so offline evaluation never mutates live rules.
    namespace = {**resolve_scalping_entry_price.__globals__,
                 'TRADING_RULES': SimpleNamespace(**seed['pricing_rules'])}
    cloned = FunctionType(resolve_scalping_entry_price.__code__, namespace,
                          resolve_scalping_entry_price.__name__)
    cloned.__kwdefaults__ = deepcopy(resolve_scalping_entry_price.__kwdefaults__)
    return cloned


def reconstruct_prices(seed, receipts, *, pricer=None):
    """Reconstruct only prices from exact fill/decision evidence in causal order.

    A real probe fill is a control input, never a counterfactual candidate fill.
    Missing sequence, source, guard, quantity or capital evidence stops replay.
    """
    result = dict(schema=REPLAY_SCHEMA, seed=deepcopy(seed), status='source_gap',
        replay_role='actual_execution_price_reconstruction_only', blocker=None,
        residual_orders=None, net_pnl_krw=None, paired_economic_eligible=False, **AUTHORITY)
    result['operating_source_gaps'] = operating_source_gaps(seed or {})
    try:
        if not valid_seed(seed):
            raise ValueError('conditional_seed_invalid')
        if seed['price_kernel_identity'] != kernel_identity():
            raise ValueError('conditional_original_price_kernel_unavailable')
        validated, seen_sequences = [], {}
        for row in receipts:
            if (not isinstance(row, dict) or row != seal(row, 'sha256')
                or row.get('kind') not in {'probe_fill','residual_decision'}
                or row.get('evaluation_attempt_id') != seed['evaluation_attempt_id']
                or row.get('plan_sha256') != seed['plan_sha256']
                or row.get('stock_code') != seed['stock_code']
                or row.get('effective_venue') != seed['effective_venue']
                or row.get('session_bucket') != seed['session_bucket']
                or row.get('source_sha256') != digest(row.get('native_source'))
                or type(row.get('sequence')) is not int or row['sequence'] < 1
                or clock(row['available_at']) < clock(row['event_at'])
                or clock(row['event_at']) < clock(seed['observed_at'])):
                raise ValueError('conditional_receipt_identity_or_clock_invalid')
            if row['sequence'] in seen_sequences:
                if seen_sequences[row['sequence']] != row:
                    raise ValueError('conditional_receipt_sequence_conflict')
                continue
            seen_sequences[row['sequence']] = row
            validated.append(row)
        ordered = sorted(validated, key=lambda r:(clock(r['available_at']),r['sequence']))
        if len({r['sequence'] for r in ordered}) != len(ordered):
            raise ValueError('conditional_receipt_sequence_conflict')
        fills = [r for r in ordered if r.get('kind') == 'probe_fill']
        if len(fills) != 1:
            raise ValueError('exact_probe_fill_receipt_missing_or_conflicting')
        fill = fills[0]
        if (fill.get('broker_receipt_verified') is not True or not fill.get('broker_order_no')
                or type(fill.get('cumulative_qty')) is not int or fill['cumulative_qty'] != 1
                or type(fill.get('fill_price')) is not int
                or fill['fill_price'] <= 0):
            raise ValueError('exact_probe_fill_contract_invalid')
        if any(fill.get(field) != fill['native_source'].get(source) for field, source in (
                ('broker_order_no','order_no'), ('cumulative_qty','fill_qty'), ('fill_price','fill_price'))):
            raise ValueError('probe_fill_original_source_binding_invalid')
        if fill.get('runtime_pid') != seed.get('runtime_pid'):
            raise ValueError('probe_receipt_runtime_identity_conflict')
        decisions = [r for r in ordered if r.get('kind') == 'residual_decision']
        if not decisions:
            raise ValueError('post_probe_decision_receipt_missing')
        for decision in decisions:
            if (decision['sequence'] <= fill['sequence']
                    or decision.get('runtime_pid') != fill.get('runtime_pid')
                    or clock(decision['event_at']) < clock(fill['available_at'])):
                raise ValueError('post_probe_decision_outside_causal_window')
            action = decision.get('continuation_action')
            original = decision['native_source']
            quote = original.get('quote') or {}
            if (action != original.get('continuation_action')
                    or decision.get('guard_allowed') != original.get('guard_allowed')
                    or decision.get('fresh_mark_price') != original.get('fresh_mark_price')
                    or decision.get('native_residual_orders') != original.get('native_residual_orders')
                    or any(decision.get(field) != quote.get(source) for field,source in (
                        ('quote_route','market_route'), ('quote_transport_epoch','transport_epoch'),
                        ('quote_received_at','observed_epoch'), ('best_bid','best_bid'), ('best_ask','best_ask')))
                    or decision.get('capital_allowed') != (original.get('account_guard', {}).get('account_guard_allowed') is True)
                    or decision.get('quantity_allowed') != (original.get('quantity', {}).get('allowed') is True)):
                raise ValueError('post_probe_original_source_binding_invalid')
            if action in {'BLOCK','HARD_NEGATIVE'}:
                result.update(status='reconstructed_residual_aborted', residual_orders=[], held_probe_qty=1)
                break
            if clock(decision['available_at']) - clock(fill['available_at']) > seed['probe_timeout_sec']:
                raise ValueError('post_probe_decision_outside_causal_window')
            if action == 'DEFER':
                continue
            if (decision.get('guard_allowed') is not True or decision.get('capital_allowed') is not True
                    or decision.get('quantity_allowed') is not True
                    or decision.get('quote_route') != seed['operating_contract']['broker_route']
                    or type(decision.get('transport_epoch')) is not int
                    or decision['transport_epoch'] != decision.get('quote_transport_epoch')
                    or not number(decision.get('quote_freshness_limit_sec'))
                    or not 0 < decision['quote_freshness_limit_sec']
                    or not 0 <= clock(decision['event_at']) - clock(decision['quote_received_at']) <= decision['quote_freshness_limit_sec']):
                raise ValueError('post_probe_guard_capital_or_quote_unproven')
            if (fill['fill_price'] - seed['probe_reference_ask']) / seed['probe_reference_ask'] * 10000 > seed['max_slippage_bps']:
                raise ValueError('probe_fill_slippage_above_frozen_cap')
            from src.engine.scalping.entry_split_order_plan import build_probe_residual_orders
            resolve = pricer or frozen_native_pricer(seed)
            prices = []
            for i, qty in enumerate(seed['continuation']['residual_quantities']):
                price = resolve(strategy_id='SCALPING', defensive_order_price=fill['fill_price'], target_buy_price=0,
                    best_bid=decision['best_bid'], best_ask=decision['best_ask'],
                    phase='post_probe', probe_fill_price=fill['fill_price'],
                    fresh_mark_price=decision['fresh_mark_price'], continuation_action=action,
                    residual_leg_index=i)
                if price.get('allowed') is not True:
                    raise ValueError('post_probe_price_kernel_rejected')
                prices.append(price['resolved_order_price'])
            orders, proof = build_probe_residual_orders(continuation=seed['continuation'], probe_fill_price=fill['fill_price'],
                best_bid=decision['best_bid'], best_ask=decision['best_ask'], resolved_leg_prices=prices)
            if proof.get('allowed') is not True or sum(o['qty'] for o in orders) != seed['total_qty'] - 1:
                raise ValueError('post_probe_residual_quantity_invalid')
            native_orders = decision.get('native_residual_orders')
            if (not isinstance(native_orders, list)
                    or [(o.get('qty'), o.get('price')) for o in native_orders]
                    != [(o['qty'], o['price']) for o in orders]):
                raise ValueError('post_probe_native_price_or_quantity_mismatch')
            result.update(status='reconstructed_prices', residual_orders=orders, held_probe_qty=1,
                          price_phase='post_probe_before_individual_leg_reprice',
                          fill_receipt_sha256=fill['sha256'], decision_receipt_sha256=decision['sha256'])
            break
        else:
            raise ValueError('post_probe_deferred_terminal_unobserved')
    except (KeyError, TypeError, ValueError, AttributeError, OSError, OverflowError) as exc:
        result.update(status='source_gap', blocker=str(exc), residual_orders=None)
    return seal(result, 'sha256')
