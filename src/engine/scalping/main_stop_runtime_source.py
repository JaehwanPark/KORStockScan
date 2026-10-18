"""Pure receipts for actual Main stop evaluation stages; no execution authority.

A quote observation is not evidence that any stop rule ran. These receipts bind
an actual caller/stage to the original shared quote and its immutable policy.
"""
from __future__ import annotations

from copy import deepcopy

from .main_stop_policy import digest, finite, next_source_observation_generation

EVALUATION_SCHEMA = 'main_stop_evaluation_source_v1'
STAGES = {'preset_safety', 'common_soft'}



PREDECESSOR_SCHEMA = 'main_stop_evaluation_reference_v1'
PREDECESSOR_KEYS = ('evaluation_id', 'source_sha256', 'at', 'evaluator', 'stage', 'position_key', 'pin_sha256')


def evaluation_reference(receipt):
    if (not isinstance(receipt, dict) or receipt.get('schema') != EVALUATION_SCHEMA
            or receipt.get('source_sha256') != digest({k:v for k,v in receipt.items() if k != 'source_sha256'})
            or receipt.get('stage') != 'preset_safety' or receipt.get('evaluator') != 'normal'):
        raise ValueError('native_preset_predecessor_invalid')
    return dict(schema=PREDECESSOR_SCHEMA, **{key:receipt[key] for key in PREDECESSOR_KEYS})



QUANTITY_REFERENCE_SCHEMA = 'main_stop_quantity_reference_v1'
_QUANTITY_IDENTITY = ('generation_sha256', 'status', 'position_key', 'quantity', 'buy_basis_krw', 'buy_fill_identity')


def _quantity_reference(current, quote, *, at):
    original = quote.get('quantity_source')
    if (not isinstance(original, dict) or current.get('status') not in {'full_fill', 'settled_partial'}
            or original.get('schema') != 'main_stop_quantity_source_v1'
            or original.get('source_sha256') != digest({k:v for k,v in original.items() if k != 'source_sha256'})
            or any(not finite(original.get(k)) for k in ('known_at', 'captured_at'))
            or not 0 < original['known_at'] <= original['captured_at'] <= at
            or original.get('allowed_runtime_apply') is not False
            or original.get('actual_order_submitted') is not False
            or any(current.get(key) != original.get(key) for key in _QUANTITY_IDENTITY)
            or current.get('proof') != original.get('proof')):
        return current
    body = dict(schema=QUANTITY_REFERENCE_SCHEMA, quote_source_sha256=quote['source_sha256'],
                quantity_source_sha256=original['source_sha256'], observed_at=at,
                **{key:current[key] for key in _QUANTITY_IDENTITY},
                runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False)
    return dict(body, source_sha256=digest(body))


def resolve_quantity_source(receipt, quote, *, at):
    """Resolve only an exact existing quote proof; never repair an unknown one."""
    from .main_stop_quantity_source import validate_quantity_source
    identity = dict(position_key=quote['position_key'], at=at,
                    quantity=quote['quantity'], buy_basis_krw=quote['buy_basis_krw'])
    if not isinstance(receipt, dict):
        raise ValueError('quantity_terminal_source_missing')
    if receipt.get('schema') != QUANTITY_REFERENCE_SCHEMA:
        return receipt
    original = quote.get('quantity_source')
    if (quote.get('source_sha256') != digest({k:v for k,v in quote.items() if k != 'source_sha256'})
            or receipt.get('source_sha256') != digest({k:v for k,v in receipt.items() if k != 'source_sha256'})
            or receipt.get('observed_at') != at
            or receipt.get('quote_source_sha256') != quote.get('source_sha256')
            or not isinstance(original, dict)
            or receipt.get('quantity_source_sha256') != original.get('source_sha256')
            or any(receipt.get(key) != original.get(key) for key in _QUANTITY_IDENTITY)
            or any(receipt.get(key) is not False for key in ('runtime_effect', 'allowed_runtime_apply', 'actual_order_submitted'))
            or not validate_quantity_source(original, **identity)):
        raise ValueError('quantity_source_reference_unbound')
    return original


def evaluation_source(stock, *, quote_source, at, evaluator, stage, decision_price,
                      decision_price_basis, decision_profit_pct, priority_status,
                      preset_stop=None, preset_predecessor=None, legacy_broker_recovered=False,
                      quote_max_age_sec=None, decision_inputs=None, seal=True):
    from .position_peak_ledger import position_cycle_id
    q = quote_source
    quote_supported = bool(isinstance(q, dict) and q.get('coverage_complete') is True
        and isinstance(q.get('item'), str) and q['item']
        and isinstance(q.get('route'), str) and q['route']
        and type(q.get('transport_epoch')) is int and q['transport_epoch'] > 0
        and finite(q.get('quote_at')) and q['quote_at'] > 0
        and finite(at) and finite(quote_max_age_sec) and quote_max_age_sec > 0
        and 0 <= at - q['quote_at'] <= quote_max_age_sec
        and finite(q.get('bid')) and q['bid'] > 0)
    if (not isinstance(q, dict) or q.get('schema') != 'main_stop_source_v1'
            or q.get('source_sha256') != digest({k: v for k, v in q.items() if k != 'source_sha256'})
            or q.get('position_key') != position_cycle_id(stock)
            or q.get('pin_sha256') != (stock.get('main_stop_policy_pin') or {}).get('pin_sha256')
            or q.get('quantity') != stock.get('buy_qty')
            or q.get('buy_basis_krw') != stock.get('buy_qty', 0) * stock.get('buy_price', 0)
            or type(q.get('coverage_complete')) is not bool
            or not finite(q.get('at')) or not finite(at) or not q['at'] <= at
            or not finite(quote_max_age_sec) or quote_max_age_sec <= 0
            or type(legacy_broker_recovered) is not bool
            or evaluator not in {'normal', 'fast'} or stage not in STAGES
            or (stage == 'common_soft' and evaluator != 'normal')
            or priority_status not in {'reached', 'blocked_legacy'}
            or (priority_status == 'blocked_legacy' and stage != 'preset_safety')
            or decision_price_basis not in {'mark_price', 'executable_bid'}
            or not finite(decision_price) or decision_price <= 0
            or not finite(decision_profit_pct)
            or (decision_price_basis == 'executable_bid' and decision_price != q['bid'])):
        raise ValueError('native_stop_evaluation_binding_invalid')
    prior_generation = stock.get('_main_stop_evaluation_generation', 0)
    if type(prior_generation) is not int or prior_generation < 0:
        raise ValueError('native_stop_evaluation_generation_invalid')
    generation = prior_generation + 1
    from .main_stop_quantity_source import build_quantity_source
    quantity_source = _quantity_reference(build_quantity_source(stock, at=at), q, at=at)
    if stage == 'common_soft' and (not isinstance(decision_inputs, dict)
            or any(type(decision_inputs.get(k)) is not bool for k in
                   ('grace_enabled', 'after_add', 'handoff_enabled', 'holding_ai_required'))):
        raise ValueError('native_soft_decision_inputs_missing')
    if stage == 'preset_safety' and (not isinstance(decision_inputs, dict)
            or type(decision_inputs.get('handoff_enabled')) is not bool):
        raise ValueError('native_preset_decision_inputs_missing')
    if preset_predecessor is not None:
        if preset_predecessor.get('schema') == EVALUATION_SCHEMA:
            preset_predecessor = evaluation_reference(preset_predecessor)
        if (set(preset_predecessor) != {'schema', *PREDECESSOR_KEYS}
                or preset_predecessor.get('schema') != PREDECESSOR_SCHEMA
                or preset_predecessor.get('at') != at
                or preset_predecessor.get('position_key') != q['position_key']
                or preset_predecessor.get('pin_sha256') != q['pin_sha256']
                or preset_predecessor.get('evaluator') != 'normal'
                or preset_predecessor.get('stage') != 'preset_safety'):
            raise ValueError('native_preset_predecessor_invalid')
    anchor = dict(position_key=q['position_key'], pin_sha256=q['pin_sha256'],
                  evaluator=evaluator, stage=stage, at=at, generation=generation)
    body = dict(schema=EVALUATION_SCHEMA, evaluation_id=digest(anchor),
                evaluation_generation=generation,
                source_observation_generation=next_source_observation_generation(
                    stock, minimum=q.get('source_observation_generation', 0)),
                **{key: q[key] for key in ('position_key', 'record_id', 'role', 'market', 'pin_sha256',
                    'source_stop_values', 'parent_values_sha256', 'quantity', 'buy_basis_krw')},
                evaluator=evaluator, decision_owner='main_scalping', stage=stage,
                rule_scope=[stage], at=at, decision_price=decision_price,
                decision_price_basis=decision_price_basis, decision_profit_pct=decision_profit_pct,
                decision_price_observation='native_gate_argument', independently_verified_mark_clock=False,
                quote_source_sha256=q['source_sha256'], quote_at=q['quote_at'],
                quote_binding_status='supported' if quote_supported else 'source_gap',
                quote_observation_at=q['at'], quote_max_age_sec=quote_max_age_sec,
                quote_validated_at=at, legacy_broker_recovered=legacy_broker_recovered,
                route=q['route'], item=q['item'],
                transport_epoch=q['transport_epoch'], priority_status=priority_status,
                preset_stop=preset_stop, preset_predecessor=preset_predecessor,
                quantity_source=quantity_source, decision_inputs=deepcopy(decision_inputs),
                capture_rejected_count=stock.get('main_stop_source_rejected_count', 0),
                evaluation_rejected_count=stock.get('main_stop_evaluation_rejected_count', 0),
                runtime_effect=False, allowed_runtime_apply=False, actual_order_submitted=False)
    stock['_main_stop_evaluation_generation'] = generation
    return dict(body, source_sha256=digest(body)) if seal else body
