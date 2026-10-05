"""Shared frozen admission recipe; pure facts and no broker or publisher I/O.

Owned by the existing Main entry evaluator and offline replay adapters. The
recipe is enabled only by an explicitly validated machine policy component.
"""
from copy import deepcopy
import math
from src.engine.scalping import entry_strategy_policy as S

RECIPE_ID = 'pullback_p60_v0'
POLICY_SCHEMA = 'main_entry_admission_recipe_v1'
DECISION_SCHEMA = 'main_entry_admission_recipe_decision_v1'
SOFT_CONFIRMATION = frozenset({
    'trigger_confirmation_missing', 'volume_confirmation_missing',
    'micro_continuation_unconfirmed', 'no_supported_setup',
})


def number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def contract(parent):
    return dict(schema=POLICY_SCHEMA, recipe_id=RECIPE_ID,
        exact_scope=['KRX', 'KRX_REGULAR'], symbol_predicate='exclude_005930',
        admission_mode='replace', parent_policy_sha256=S.digest(parent),
        parameters=dict(minimum_buy_pressure_10t=60, maximum_buy_pressure_10t=100,
            minimum_trusted_tick_count=10, maximum_micro_vwap_bp=0,
            net_aggressive_delta_comparison='strictly_positive'),
        source_quality_contract='parent_guards_and_original_raw_capture',
        counterweight_fact_ids=sorted(SOFT_CONFIRMATION))


def validate(value, parent):
    try:
        valid = isinstance(value, dict) and S.digest(value) == S.digest(contract(parent))
    except (ValueError, TypeError, OverflowError):
        valid = False
    return [] if valid else ['entry_admission_recipe_contract_invalid']


def candidate_policy(parent):
    result = deepcopy(parent)
    result.pop('entry_admission_recipe', None)
    result['entry_admission_recipe'] = contract(result)
    return result


def condition(raw):
    """The previously selected p60/v0 rule; no action or outcome inputs."""
    f = raw.get('features') or {}
    pressure, delta, vwap, trusted = (number(f.get(k)) for k in (
        'buy_pressure_10t', 'net_aggressive_delta_10t',
        'curr_vs_micro_vwap_bp', 'tick_aggressor_trusted_count'))
    return bool(pressure is not None and 60 <= pressure <= 100
        and delta is not None and delta > 0 and vwap is not None and vwap <= 0
        and trusted is not None and trusted >= 10
        and f.get('tick_aggressor_pressure_usable') is True
        and f.get('tick_context_stale') is False and f.get('quote_stale') is False
        and f.get('micro_vwap_available') is True)


def evaluate(setup, parent, *, baseline, situation_veto):
    """Replace entry admission in exact non-Samsung KRX regular scope.

    A distinct pullback setup may resolve the enumerated soft confirmations.
    Every other original risk disposition and all parent hard guards survive.
    The original breakout/family/price-response facts are not edited.
    """
    raw = setup.get('strategy_raw_input')
    if not isinstance(raw, dict) or setup.get('strategy_raw_sha256') != S.digest(raw):
        raise ValueError('pullback_raw_capture_invalid')
    rebuilt = baseline.get('effective_setup_evidence') or setup
    scope = (str(raw.get('stock_code') or '').isdigit()
        and len(str(raw.get('stock_code') or '')) == 6
        and raw['stock_code'] != '005930'
        and str(raw.get('effective_venue') or '').upper() == 'KRX'
        and str(raw.get('session_bucket') or '').upper() == 'KRX_REGULAR')
    matched = bool(scope and condition(raw))
    ledger = []
    for risk in baseline['core_comparison']['risk_assessments']:
        existing = risk['disposition'] == 'COMPENSATED'
        proposed = bool(matched and risk['disposition'] == 'RECHECKABLE'
            and risk['risk_code'] == 'CONFIRMATION_MISSING'
            and risk['fact_id'] in SOFT_CONFIRMATION)
        ledger.append(dict(original=deepcopy(risk), existing_resolved=existing,
            proposed_counterweight='trusted_buy_flow_at_or_below_vwap' if proposed else None,
            resolved=existing or proposed))
    reasons = []
    if not scope: reasons.append('outside_scope_parent_inherited')
    if not matched: reasons.append('frozen_condition_not_met')
    if baseline['action'] == 'BLOCK': reasons.append('parent_block_preserved')
    if rebuilt.get('invalidation_facts'): reasons.append('invalidation_preserved')
    if (rebuilt.get('source_quality') or {}).get('status') != 'fresh_consistent':
        reasons.append('parent_source_guard_preserved')
    if (baseline.get('liquidity_inputs_complete') is not True
            or baseline.get('liquidity_threshold_pass') is not True):
        reasons.append('parent_liquidity_guard_preserved')
    thresholds = (baseline.get('strategy_selection') or {}).get('effective_thresholds') or {}
    if thresholds.get('micro_confirmation_recipe', 0) != 0:
        reasons.append('parent_micro_recipe_preserved')
    if any(not row['resolved'] for row in ledger): reasons.append('unresolved_risk_facts')
    proposed = baseline['action']
    if scope and proposed == 'ENTER_NOW' and reasons:
        proposed = 'RECHECK'
    if scope and baseline['action'] == 'RECHECK' and not reasons:
        proposed = situation_veto(
            {**baseline, 'action': 'ENTER_NOW'}, setup, parent)['action']
        if proposed != 'ENTER_NOW': reasons.append('parent_situation_veto_preserved')
    return dict(schema=DECISION_SCHEMA, parent_sha256=S.digest(parent),
        original_raw_sha256=setup['strategy_raw_sha256'], parent_action=baseline['action'],
        parent_reason=baseline['reason'], proposed_action=proposed,
        condition_match=matched, changed=proposed != baseline['action'],
        unresolved_reasons=reasons, fact_ledger=ledger,
        original_setup_family=rebuilt.get('setup_family'),
        original_setup_state=rebuilt.get('setup_state'),
        original_local_breakout=deepcopy(rebuilt.get('local_breakout')),
        proposed_setup_family='PULLBACK_BUY_FLOW' if matched else None)
