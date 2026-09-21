"""Main entry strategy coordinates and deterministic type/state selection.

No I/O, broker authority or independent publisher. The scoped context only
parameterizes the existing fact producers; all unscoped callers retain v1.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
import hashlib
import json
import math
import re
from datetime import datetime
from zoneinfo import ZoneInfo

SCHEMA = 'main_entry_strategy_v2'
KERNEL = 'main_entry_raw_strategy_v2'
POLICY_VERSION = 'main_entry_strategy_thresholds_v2'
# name: (incumbent, finite search seed); domains are strategy ranges, not safety.
REGISTRY = {
    'structural_positive_returns': (3, (2, 3, 4)),
    'structural_positive_slopes': (2, (2, 3, 4)),
    'early_positive_returns': (3, (2, 3, 4)),
    'early_positive_slopes': (3, (2, 3, 4)),
    'early_return_floor_pct': (-.5, (-1., -.5, -.25)),
    'early_drawdown_floor_pct': (-1.5, (-2., -1.5, -1.)),
    'early_volume_ratio': (1., (.8, 1., 1.2)),
    'overextension_runup_pct': (15., (12., 15., 18., 20.)),
    'overextension_vwap_bp': (80., (60., 80., 100., 120.)),
    'overextension_ma5_bp': (80., (60., 80., 100., 120.)),
    'tape_supportive_score': (68., (60., 64., 68., 72.)),
    'tape_adverse_score': (42., (35., 42., 48.)),
    'momentum_accelerating_score': (68., (60., 64., 68., 72.)),
    'momentum_fading_score': (42., (35., 42., 48.)),
    'trigger_buy_pressure': (60., (55., 60., 65.)),
    'reversal_tick_acceleration': (1.5, (1., 1.5, 2.)),
    'distribution_return_5m_pct': (-.5, (-1., -.75, -.5, -.3)),
    'distribution_return_10m_pct': (-1., (-1.5, -1., -.75)),
    'distribution_drawdown_pct': (-2., (-3., -2., -1.5)),
    'distribution_volume_ratio': (.5, (.3, .5, .7)),
    'ask_wall_spread_bp': (50., (40., 50., 60., 80.)),
    'ask_wall_ratio': (5., (3., 5., 7., 10.)),
    'short_drawdown_floor_pct': (-.75, (-1., -.75, -.5)),
    'short_volume_ratio': (1.2, (.8, 1., 1.2)),
    'probe_runup_pct': (15., (12., 15., 18., 20.)),
    'probe_spread_bp': (50., (40., 50., 60., 80.)),
    'probe_buy_pressure': (55., (50., 55., 60.)),
    'depth_adverse_ratio': (2., (1.5, 2., 3.)),
    'depth_supportive_ratio': (1., (.8, 1., 1.5)),
    'top1_supportive_ratio': (1.5, (1., 1.5, 2.)),
    'cost_low_spread_bp': (15., (10., 15., 20.)),
    'cost_observable_spread_bp': (50., (40., 50., 80.)),
    'cost_extreme_spread_bp': (150., (100., 150., 200.)),
    'volume_absent_ratio': (.5, (.3, .5, .7)),
    'volume_confirm_ratio': (1., (.8, 1., 1.2)),
    'deep_drawdown_pct': (-2., (-3., -2., -1.5)),
    'recovery_positive_windows': (2, (1, 2, 3)),
    'tail_spread_bp': (100., (80., 100., 120.)),
    'tail_fillability': (15., (10., 15., 25.)),
    'tail_top3_ratio': (5., (3., 5., 7.)),
    'relative_weakness_pct_point': (-.5, (-.75, -.5, -.25)),
    'late_watch_sec': (600., (300., 600., 900.)),
    'material_extension_pct': (1., (.5, 1., 1.5)),
    'repromotion_count': (3, (2, 3, 4)),
    'reset_drawdown_pct': (-.5, (-.75, -.5, -.25)),
    'micro_confirmation_recipe': (0, (0, 1, 2, 3)),
    'minimum_depletion_fraction_per_sec': (0., (0., .01, .05, .1)),
    'minimum_trade_backed_ratio': (.5, (.5, .7, .9)),
    'maximum_refill_ratio': (1., (.25, .5, 1.)),
    'maximum_spread_bp': (100., (40., 60., 80., 100.)),
    'minimum_fillability_score': (15., (15., 30., 45., 60.)),
    'maximum_top3_ask_to_bid_ratio': (5., (1., 1.5, 2., 3., 5.)),
    'minimum_micro_net_aggressive_delta_10t': (1., (1., 5., 10.)),
    'minimum_micro_price_change_10t_pct': (0., (0., .02, .05)),
}
REGISTRY.update({
    'absorption_count': (1, (1, 2, 3)),
    'absorption_buy_pressure': (55., (50., 55., 60.)),
    'deceleration_margin_pct': (.05, (.02, .05, .1)),
    'rejection_wick_ratio': (.35, (.25, .35, .5)),
    'rejection_rebound_pct': (.5, (.25, .5, .75)),
    'reference_reclaim_bp': (-50., (-80., -50., -20.)),
    'recovery_tick_acceleration': (1., (.8, 1., 1.2)),
    'prior_adverse_drawdown_pct': (-1., (-1.5, -1., -.5)),
    'fresh_precursor_count': (3, (2, 3, 4)),
    'degraded_precursor_count': (4, (3, 4, 5)),
    'non_tape_precursor_count': (3, (2, 3, 4)),
    'clean_drawdown_pct': (-.5, (-.75, -.5, -.25)),
    'clean_precursor_count': (2, (2, 3, 4)),
    'clean_max_cost_pct': (.25, (.15, .25, .35)),
    'recovery_drawdown_pct': (-2., (-3., -2., -1.5)),
})
STRUCTURE_REGISTRY = {
    'breakout_lookback': (10, (5, 10, 20)),
    'breakout_event_window': (3, (2, 3, 5)),
    'breakout_failure_closes': (2, (1, 2, 3)),
    'breakout_tolerance_ticks': (0, (0, 1, 2)),
    'structure_volume_confirm': (1.1, (.8, 1.1, 1.3)),
    'structure_volume_divergence': (.8, (.5, .8, 1.)),
    'structure_divergence_return_pct': (.1, (.05, .1, .2)),
    'structure_failure_wick': (.35, (.25, .35, .5)),
    'structure_failure_drawdown_pct': (-.25, (-.5, -.25, -.1)),
    'structure_bounce_slope': (-.03, (-.05, -.03, -.01)),
    'structure_pullback_return_min': (-.6, (-1., -.6, -.3)),
    'structure_pullback_return_max': (.25, (.1, .25, .5)),
    'structure_pullback_drawdown_pct': (-1.2, (-1.5, -1.2, -.8)),
}
REGISTRY.update(STRUCTURE_REGISTRY)
def coordinate_bounds(name):
    default, grid = REGISTRY[name]
    if name == 'micro_confirmation_recipe':
        return 0, 3
    if name in {'minimum_trade_backed_ratio', 'maximum_refill_ratio'}:
        return 0., 1.
    if name in {'structural_positive_returns', 'structural_positive_slopes', 'early_positive_returns', 'early_positive_slopes', 'non_tape_precursor_count'}:
        return 1, 4
    if name in {'fresh_precursor_count', 'degraded_precursor_count'}:
        return 1, 5
    if name == 'recovery_positive_windows':
        return 1, 3
    if name == 'breakout_tolerance_ticks':
        return 0, 10
    if isinstance(default, int):
        return 1, 390 if 'lookback' in name else 30
    if default < 0:
        return (-10000., 0.) if name.endswith('_bp') else (-100., 0.)
    if name == 'late_watch_sec':
        return 1., 86400.
    if any(word in name for word in ('pressure', 'fillability', 'score')):
        return 0., 100.
    if name in {'rejection_wick_ratio', 'structure_failure_wick'}:
        return 0., 1.
    return 0., max(100., max(grid) * 10)


FEATURES = {'price', 'tick_pct', 'spread_bp', 'fillability_score', 'volatility_pct',
            'return_5m_pct', 'market_cap_krw', 'watch_age_sec'}
_CURRENT = ContextVar('main_entry_strategy', default=None)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def knob(name, fallback):
    values = _CURRENT.get()
    return values[name] if values is not None else fallback


@contextmanager
def using(values):
    token = _CURRENT.set(values)
    try:
        yield
    finally:
        _CURRENT.reset(token)


def default_profile(policy):
    if 'strategy' in policy:
        return deepcopy(policy['strategy']['nodes'][policy['strategy']['root']]['profile'])
    return {name: policy.get('thresholds', {}).get(name, spec[0])
            for name, spec in REGISTRY.items()}


def seed(policy, scope):
    result = deepcopy(policy)
    result.pop('hierarchy', None)
    result['version'] = POLICY_VERSION
    result['postclose_selection'].update(minimum_cost_adjusted_ev_pct=0., minimum_unique_symbol_count=1)
    result['strategy'] = dict(schema=SCHEMA, kernel=KERNEL, scope=list(scope),
        root='root', nodes={'root': {'profile': default_profile(policy)}},
        feature_version='main_entry_asof_features_v1')
    return result


def validate(strategy):
    errors = []
    if not isinstance(strategy, dict) or set(strategy) != {
        'schema', 'kernel', 'scope', 'root', 'nodes', 'feature_version'}:
        return ['strategy_fields_invalid']
    if strategy['schema'] != SCHEMA or strategy['kernel'] != KERNEL or strategy['feature_version'] != 'main_entry_asof_features_v1':
        errors.append('strategy_version_invalid')
    from src.engine.scalping.entry_setup_evidence import mechanistic_scope_supported
    scope = strategy['scope']
    if not isinstance(scope, list) or len(scope) != 2 or not mechanistic_scope_supported(*scope):
        errors.append('strategy_scope_invalid')
    nodes = strategy['nodes']
    if not isinstance(nodes, dict) or not nodes or len(nodes) > 63:
        return errors + ['strategy_nodes_invalid']
    visited = set()
    def visit(key, ancestors):
        if not isinstance(key, str) or key in ancestors or key in visited or key not in nodes:
            raise ValueError('strategy_tree_invalid')
        visited.add(key)
        node = nodes[key]
        if not isinstance(node, dict) or set(node) not in ({'profile'}, {'profile', 'split'}):
            raise ValueError('strategy_node_invalid')
        profile = node['profile']
        if not isinstance(profile, dict) or set(profile) != set(REGISTRY):
            raise ValueError('strategy_profile_incomplete')
        for name, value in profile.items():
            default, grid = REGISTRY[name]
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not coordinate_bounds(name)[0] <= value <= coordinate_bounds(name)[1]:
                raise ValueError('strategy_coordinate_invalid:' + name)
            if isinstance(default, int) and not isinstance(value, int):
                raise ValueError('strategy_integer_required:' + name)
        if profile['momentum_fading_score'] >= profile['momentum_accelerating_score'] or profile['tape_adverse_score'] >= profile['tape_supportive_score'] or not profile['cost_low_spread_bp'] <= profile['cost_observable_spread_bp'] <= profile['cost_extreme_spread_bp'] or profile['volume_absent_ratio'] >= profile['volume_confirm_ratio']:
            raise ValueError('strategy_ordered_bounds_invalid')
        if 'split' in node:
            split = node['split']
            if not isinstance(split, dict) or set(split) != {'feature', 'boundary', 'lt', 'ge'} or split['feature'] not in FEATURES:
                raise ValueError('strategy_split_invalid')
            boundary = split['boundary']
            if isinstance(boundary, bool) or not isinstance(boundary, (int, float)) or not math.isfinite(boundary):
                raise ValueError('strategy_boundary_invalid')
            for child in ('lt', 'ge'):
                visit(split[child], ancestors | {key})
    try:
        visit(strategy['root'], set())
        if visited != set(nodes):
            errors.append('strategy_unreachable_nodes')
    except (ValueError, TypeError, KeyError) as exc:
        errors.append(str(exc))
    return errors


def _number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None


def features(payload, setup):
    current, facts = payload.get('current') or {}, payload.get('features') or {}
    structure = (payload.get('entry_candle_context') or {}).get('structure') or {}
    price = _number(current.get('price'))
    from src.trading.order.tick_utils import get_tick_size
    values = dict(price=price, tick_pct=(get_tick_size(price) / price * 100 if price and price > 0 else None),
        spread_bp=_number(facts.get('spread_bp')), fillability_score=_number(facts.get('fillability_score')),
        volatility_pct=_number(facts.get('realized_volatility_pct')),
        return_5m_pct=_number((structure.get('returns_pct') or {}).get('5')),
        watch_age_sec=_number((setup.get('entry_timing_observation_v1') or {}).get('watch_age_sec')),
        market_cap_krw=None)
    if values['volatility_pct'] is None:
        from statistics import pstdev
        bars = (payload.get('entry_candle_context') or {}).get('bars') or []
        closes = [_number(row.get('c')) for row in bars if isinstance(row, dict) and not row.get('forming')][-21:]
        if len(closes) >= 3 and all(x is not None and x > 0 for x in closes):
            values['volatility_pct'] = pstdev((right / left - 1) * 100 for left,right in zip(closes, closes[1:]))
    metadata = payload.get('strategy_metadata') or {}
    cap = metadata.get('market_cap')
    if cap is not None:
        try:
            at = datetime.fromisoformat(metadata['observed_at'])
            known, effective = (datetime.fromisoformat(cap[k]) for k in ('known_at', 'effective_at'))
            if not all(t.tzinfo for t in (at, known, effective)) or cap['unit'] != 'KRW' or re.fullmatch(r'[0-9a-f]{64}', str(cap['source_sha256'])) is None or cap.get('corporate_action_consistent') is not True:
                raise ValueError('strategy_metadata_contract_invalid')
            if known <= at and effective <= at:
                values['market_cap_krw'] = _number(cap['value'])
                if values['market_cap_krw'] is None or values['market_cap_krw'] <= 0:
                    raise ValueError('strategy_metadata_value_invalid')
        except (KeyError, TypeError) as exc:
            raise ValueError('strategy_metadata_contract_invalid') from exc
    return values


def select(policy, payload, setup):
    strategy = policy['strategy']
    errors = validate(strategy)
    if errors:
        raise ValueError(','.join(errors))
    group = (setup.get('mechanistic_context') or {}).get('group') or {}
    parts = group.get('key_parts') or {}
    routing = payload.get('routing') or {}
    raw_scope = [str(payload.get('effective_venue') or routing.get('effective_venue') or '').upper(),
                 str(payload.get('session_bucket') or routing.get('session_bucket') or '').upper()]
    stored_scope = [parts.get('venue'), parts.get('session_bucket')]
    if all(raw_scope) and all(stored_scope) and raw_scope != stored_scope:
        raise ValueError('strategy_source_scope_conflict')
    if (raw_scope if all(raw_scope) else stored_scope) != strategy['scope']:
        raise ValueError('strategy_source_scope_mismatch')
    values = features(payload, setup)
    path, key, reason = [], strategy['root'], 'leaf'
    while True:
        path.append(key)
        node = strategy['nodes'][key]
        if 'split' not in node:
            break
        split = node['split']
        value = values[split['feature']]
        if value is None:
            reason = 'unknown_parent'
            break
        key = split['lt' if value < split['boundary'] else 'ge']
    profile = deepcopy(node['profile'])
    return profile, dict(schema=SCHEMA, kernel=KERNEL, policy_sha256=digest(policy),
        selector_sha256=digest(strategy), features=values, path=path, leaf=key,
        fallback_reason=reason, effective_thresholds=profile, profile_sha256=digest(profile))


def legacy_projection(policy):
    """Unscoped consumer projection keeps the incumbent common coordinates."""
    result = deepcopy(policy)
    result.pop('strategy', None)
    if result.get('version') == POLICY_VERSION:
        from src.engine.scalping.entry_setup_evidence import MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        result['version'] = MECHANISTIC_FULL_POPULATION_POLICY_VERSION
        result['postclose_selection']['minimum_unique_symbol_count'] = max(3, result['postclose_selection']['minimum_unique_symbol_count'])
    return result


def _rebuild_captured_local_structure(payload, profile):
    """Recover the current local event from the captured completed minute tail.

    Only date-bound model bars are admitted; session metrics remain their
    original predecision numerical observations. No daily/latest lookup occurs.
    """
    from src.engine.scalping.entry_candle_context import _local_breakout, LOCAL_BREAKOUT_VERSION
    context = payload.get('entry_candle_context') or {}
    structure = context.get('structure') or {}
    changed = any(profile[k] != REGISTRY[k][0] for k in STRUCTURE_REGISTRY if k.startswith('breakout_'))
    if structure.get('structure_contract_version') == LOCAL_BREAKOUT_VERSION and not changed:
        return
    stamp = payload.get('strategy_observed_at')
    if not stamp:
        # Live current-version fixtures/inputs use their own producer contract.
        if changed:
            raise ValueError('strategy_local_bar_clock_missing')
        return
    observed = datetime.fromisoformat(stamp)
    if observed.tzinfo is None:
        raise ValueError('strategy_local_bar_clock_invalid')
    observed = observed.astimezone(ZoneInfo('Asia/Seoul'))
    bars = []
    for row in context.get('bars') or []:
        if row.get('forming'):
            continue
        try:
            moment = datetime.fromisoformat(observed.date().isoformat() + 'T' + row['t']).replace(tzinfo=observed.tzinfo)
            bar = {k: row[k] for k in ('o','h','l','c','v')}
            if moment.timestamp() + 60 > observed.timestamp() or any(_number(v) is None for v in bar.values()):
                raise ValueError('strategy_local_bar_future_or_invalid')
            if not (0 < bar['l'] <= min(bar['o'], bar['c']) <= max(bar['o'], bar['c']) <= bar['h']) or bar['v'] < 0:
                raise ValueError('strategy_local_bar_ohlcv_invalid')
            bars.append(dict(bar, dt=moment, forming=False))
        except (KeyError, TypeError) as exc:
            raise ValueError('strategy_local_bar_contract_missing') from exc
    if not bars or any(a['dt'] >= b['dt'] for a,b in zip(bars,bars[1:])):
        raise ValueError('strategy_local_bar_sequence_missing')
    required = profile['breakout_lookback'] + profile['breakout_event_window']
    if context.get('completed_bar_count', 0) > len(bars) and len(bars) < required:
        raise ValueError('strategy_local_bar_tail_truncated')
    local = _local_breakout(bars)
    regime = structure.get('regime')
    previous = regime
    if local['status'] == 'failed_breakout':
        regime = 'failed_breakout'
    elif regime == 'failed_breakout':
        regime = 'range'
    local['recheck_required'] = local['status'] == 'retest_pending' or (previous == 'failed_breakout' and regime != 'failed_breakout')
    structure.update(local_breakout=local, structure_contract_version=LOCAL_BREAKOUT_VERSION, regime=regime)
    from src.engine.scalping.entry_candle_context import ADVERSE_REGIMES
    structure['alignment'] = 'adverse' if regime in ADVERSE_REGIMES else 'positive' if regime in {'breakout','healthy_pullback'} else 'neutral'


def rebuild(setup, policy):
    """Replay the existing fact kernels from preserved predecision inputs."""
    from src.engine.scalping.ai_decision_quality import (
        build_exact_payload_analysis_v1, build_v2_13_recovery_confirmation_analysis_v1)
    from src.engine.scalping.entry_setup_evidence import build_entry_setup_evidence
    payload = setup.get('strategy_raw_input')
    if not isinstance(payload, dict) or not payload:
        raise ValueError('strategy_raw_input_missing')
    if setup.get('strategy_raw_sha256') != digest(payload):
        raise ValueError('strategy_raw_input_hash_invalid')
    profile, receipt = select(policy, payload, setup)
    payload = deepcopy(payload)
    tape = payload.get('features') or {}
    if any(profile[k] != REGISTRY[k][0] for k in ('tape_supportive_score', 'tape_adverse_score')):
        score = _number(tape.get('order_flow_pressure_score'))
        if score is None or tape.get('order_flow_pressure_source') != 'trusted_aggressor':
            raise ValueError('strategy_tape_score_source_missing')
        tape['entry_order_flow_status'] = ('supportive' if score >= profile['tape_supportive_score']
            else 'adverse' if score <= profile['tape_adverse_score'] else 'neutral')
    if any(profile[k] != REGISTRY[k][0] for k in ('momentum_accelerating_score', 'momentum_fading_score')):
        score = _number(tape.get('entry_momentum_score'))
        if score is None:
            raise ValueError('strategy_momentum_score_source_missing')
        tape['entry_momentum_status'] = ('accelerating' if score >= profile['momentum_accelerating_score']
            else 'fading' if score <= profile['momentum_fading_score'] else 'flat')
    with using(profile):
        full_bars = (payload.get('entry_candle_context') or {}).get('strategy_completed_bars')
        structure_changed = any(profile[k] != REGISTRY[k][0] for k in STRUCTURE_REGISTRY)
        if structure_changed and (full_bars or any(profile[k] != REGISTRY[k][0] for k in STRUCTURE_REGISTRY if k.startswith('structure_'))):
            from src.engine.scalping.entry_candle_context import _structure
            context = payload.get('entry_candle_context') or {}
            frozen = context.get('strategy_completed_bars')
            if not isinstance(frozen, dict) or frozen.get('sha256') != digest(frozen.get('body')):
                raise ValueError('strategy_completed_bar_source_missing')
            body = frozen['body']
            cutoff = datetime.fromisoformat(body['observed_at'])
            if cutoff.tzinfo is None:
                raise ValueError('strategy_bar_clock_invalid')
            bars = []
            for row in body['bars']:
                bar = {**row, 'dt': datetime.fromisoformat(row['dt'])}
                if bar['dt'].tzinfo is None or bar['dt'].timestamp() + 60 > cutoff.timestamp() or bar.get('forming'):
                    raise ValueError('strategy_future_or_forming_bar')
                if (any(_number(bar.get(k)) is None for k in ('o', 'h', 'l', 'c', 'v'))
                    or not 0 < bar['l'] <= min(bar['o'], bar['c']) <= max(bar['o'], bar['c']) <= bar['h']
                    or bar['v'] < 0
                    or bar['dt'].astimezone(ZoneInfo('Asia/Seoul')).date() != cutoff.astimezone(ZoneInfo('Asia/Seoul')).date()):
                    raise ValueError('strategy_completed_bar_ohlcv_or_session_invalid')
                bars.append(bar)
            if len(bars) != context.get('completed_bar_count') or any(
                a['dt'] >= b['dt'] for a,b in zip(bars, bars[1:])):
                raise ValueError('strategy_completed_bar_coverage_invalid')
            context['structure'] = _structure(bars, local_breakout=True)
        else:
            _rebuild_captured_local_structure(payload, profile)
        exact = build_exact_payload_analysis_v1(payload, stage='entry', live_entry=True)
        recovery = build_v2_13_recovery_confirmation_analysis_v1(payload, stage='entry')
        rebuilt = build_entry_setup_evidence(exact_payload=payload, exact_analysis=exact,
            recovery_analysis=recovery, entry_timing_context=payload.get('entry_timing_context'),
            balanced_policy=True, timing_aware_policy=True)
    rebuilt['strategy_raw_input'] = deepcopy(setup['strategy_raw_input'])
    rebuilt['strategy_raw_sha256'] = setup['strategy_raw_sha256']
    rebuilt['strategy_selection'] = receipt
    rebuilt['evidence_sha256'] = digest({k: v for k, v in rebuilt.items() if k != 'evidence_sha256'})
    effective = legacy_projection(policy)
    effective['thresholds'].update({k: profile[k] for k in effective['thresholds']})
    return rebuilt, effective, receipt


def joint_candidates(parent, scope, *, domains=None, selectors=None, start=0, limit=96, local_first=False):
    """Bounded traversal of a declared Cartesian domain, with resumable cursor.

    Coprime stride visits every combination once; all coordinates participate
    from the first batch. Small domains are exhausted exactly. Search progress
    is not a proof of global optimality until the cursor reaches domain_size.
    """
    domains = domains or {name: list(spec[1]) for name, spec in REGISTRY.items()}
    names = sorted(domains)
    if set(names) - set(REGISTRY) or any(not domains[n] for n in names):
        raise ValueError('strategy_search_domain_invalid')
    selectors = selectors or [None]
    size = math.prod(len(domains[n]) for n in names) * len(selectors)
    stride = max(1, size // 1_618_033 * 1_000_000 + 1)
    while math.gcd(stride, size) != 1:
        stride += 1
    base = seed(parent, scope) if 'strategy' not in parent else deepcopy(parent)
    initial = []
    if local_first:
        inherited = base['strategy']['nodes'][base['strategy']['root']]['profile']
        # Try nearby changes before simultaneously perturbing every coordinate.
        # This changes traversal order only; the full joint frontier remains.
        for name in names:
            options = [v for v in domains[name] if v != inherited[name]]
            if options:
                for value in dict.fromkeys((min(options), max(options))):
                    initial.append({name: value})
    domain_hash = digest(dict(domains=domains, selectors=selectors, parent=digest(parent), local_first=local_first))
    total = size + len(initial)
    for cursor in range(start, min(start + limit, total)):
        if cursor < len(initial):
            selector, values = None, initial[cursor]
        else:
            index = (cursor - len(initial)) * stride % size
            selector = selectors[index % len(selectors)]
            index //= len(selectors)
            values = {}
            for name in names:
                values[name] = domains[name][index % len(domains[name])]
                index //= len(domains[name])
        candidate = deepcopy(base)
        root = candidate['strategy']['root']
        profile = candidate['strategy']['nodes'][root]['profile']
        profile.update(values)
        # One learned split per candidate; parent fallback is evaluated as part
        # of the whole portfolio. No child-specific publication or sample floor.
        if selector is not None:
            feature, boundary, side = selector
            inherited = deepcopy(base['strategy']['nodes'][root]['profile'])
            candidate['strategy']['nodes'] = {
                root: {'profile': inherited, 'split': dict(feature=feature, boundary=boundary, lt='lt', ge='ge')},
                'lt': {'profile': deepcopy(profile if side == 'lt' else inherited)},
                'ge': {'profile': deepcopy(profile if side == 'ge' else inherited)},
            }
        if validate(candidate['strategy']):
            candidate = None
        yield candidate, dict(cursor=cursor + 1, domain_size=total,
            domain_sha256=domain_hash, search_complete=cursor + 1 == total)


def select_report_candidate(source):
    """Choose the scope using train results only, never the holdout winners."""
    proposals = []
    for scope, result in sorted((source.get('strategy_refinements_by_scope') or {}).items()):
        candidate = result.get('candidate') or {}
        economy = (((candidate.get('evidence') or {}).get('train') or {}).get('economics') or {})
        if candidate.get('evaluation_basis') == 'machine_nonentry_opportunity_v1':
            win_rate, net = _number(economy.get('win_rate_pct')), _number(economy.get('selected_path_ev_pct'))
            score = (win_rate, net, _number(economy.get('paired_admission_delta_pct')) or 0.) if win_rate is not None and net is not None and net >= 0 else None
        else:
            net = _number(economy.get('daily_net_profit_delta_krw'))
            score = (0., net, 0.) if net is not None and net > 0 else None
        if score is not None:
            proposals.append((score, scope, result))
    if not proposals:
        return None
    _, scope, result = max(proposals, key=lambda item: (item[0], item[1]))
    return scope, result


def promotion_errors(candidate, parent, scope):
    """One gate used by research, publisher and activation; no 10bp floor."""
    errors = []
    if not isinstance(candidate, dict) or candidate.get('schema') != 'main_entry_strategy_candidate_v2':
        return ['strategy_candidate_schema_invalid']
    if candidate.get('parent_policy') != parent or candidate.get('parent_sha256') != digest(parent) or candidate.get('scope') != list(scope):
        errors.append('strategy_candidate_parent_or_scope_mismatch')
    policy = candidate.get('policy') or {}
    from src.engine.scalping.entry_setup_evidence import validate_mechanistic_entry_threshold_policy
    errors.extend(validate_mechanistic_entry_threshold_policy(policy))
    if policy.get('strategy', {}).get('scope') != list(scope):
        errors.append('strategy_candidate_scope_invalid')
    if candidate.get('policy_sha256') != digest(policy):
        errors.append('strategy_candidate_policy_hash_invalid')
    if candidate.get('evidence_sha256') != digest(candidate.get('evidence')):
        errors.append('strategy_candidate_evidence_hash_invalid')
    evidence = candidate.get('evidence') or {}
    if candidate.get('evaluation_basis') == 'machine_nonentry_opportunity_v1':
        # Machine opportunity selection is independent of auxiliary AI and
        # portfolio replay. Existing holdout losses still reject a successor.
        for split in ('train', 'holdout'):
            arm = evidence.get(split) or {}
            if split == 'holdout' and not arm:
                continue
            days, ids = arm.get('source_dates') or [], arm.get('opportunity_ids') or []
            economy = arm.get('economics') or {}
            try:
                valid_dates = days and all(datetime.fromisoformat(d).date().isoformat() == d and d >= '2026-06-05' for d in days)
            except (ValueError, TypeError):
                valid_dates = False
            if not valid_dates or not ids or len(ids) != len(set(ids)):
                errors.append(split + '_machine_support_invalid')
            if (economy.get('status') != 'supported_machine_admission'
                or economy.get('basis') != 'nonentry_to_enter_now_fixed_exit_cost_adjusted_path'
                or economy.get('auxiliary_ai_required') is not False):
                errors.append(split + '_machine_metric_invalid')
            delta = _number(economy.get('paired_admission_delta_pct'))
            if delta is None or delta < 0:
                errors.append(split + '_machine_opportunity_not_improved')
            if economy.get('selected_attempt_count', 0):
                ev, worst = _number(economy.get('selected_path_ev_pct')), _number(economy.get('worst_selected_path_pct'))
                win_rate = _number(economy.get('win_rate_pct'))
                from src.engine.scalping.ai_action_outcome_calibration import CATASTROPHIC_LOSS_PCT
                if (ev is None or ev < 0 or worst is None or worst <= CATASTROPHIC_LOSS_PCT
                    or win_rate is None or not 0 <= win_rate <= 100):
                    errors.append(split + '_machine_selected_path_invalid')
            elif split == 'train':
                errors.append('train_machine_no_recovered_entry')
        train, holdout = evidence.get('train') or {}, evidence.get('holdout') or {}
        if holdout and (not train.get('source_dates') or not holdout.get('source_dates')
                       or max(train['source_dates']) >= min(holdout['source_dates'])
                       or set(train.get('opportunity_ids', [])) & set(holdout.get('opportunity_ids', []))):
            errors.append('strategy_machine_holdout_leak')
        if candidate.get('selected_without_holdout') is not True:
            errors.append('strategy_holdout_selection_leak')
        return sorted(set(errors))
    dates = []
    for name, minimum in [('train', 10), ('holdout', 3)]:
        arm = evidence.get(name) or {}
        days = arm.get('source_dates') or []
        ids = arm.get('opportunity_ids') or []
        changed = arm.get('changed_opportunity_ids') or []
        economy = arm.get('economics') or {}
        if not days or any(not isinstance(d, str) or d < '2026-06-05' for d in days):
            errors.append(name + '_dates_invalid')
        try:
            for day in days:
                if datetime.fromisoformat(day).date().isoformat() != day:
                    raise ValueError('not_date')
        except (ValueError, TypeError):
            errors.append(name + '_date_syntax_invalid')
        dates.append(days)
        if not set(changed) <= set(ids) or len(changed) != len(set(changed)) or len(ids) != len(set(ids)) or len(ids) < minimum or (name == 'holdout' and len(set(changed)) < 3):
            errors.append(name + '_support_insufficient')
        if economy.get('status') != 'supported_operating_comparison':
            errors.append(name + '_operating_economics_unbound')
        old, new = economy.get('incumbent') or {}, economy.get('candidate') or {}
        fields = [new.get('net_pnl_krw'), new.get('ev_pct'), economy.get('daily_net_profit_delta_krw'),
                  economy.get('robust_paired_delta_ev_lower_bound_pct')]
        if any(_number(v) is None or v <= 0 for v in fields):
            errors.append(name + '_positive_cost_adjusted_improvement_missing')
        if _number(old.get('net_pnl_krw')) is None or _number(new.get('net_pnl_krw')) is None or new['net_pnl_krw'] <= old['net_pnl_krw']:
            errors.append(name + '_net_profit_not_improved')
        from src.engine.scalping.ai_action_outcome_calibration import CATASTROPHIC_LOSS_PCT
        if _number(new.get('worst')) is None or new['worst'] <= CATASTROPHIC_LOSS_PCT:
            errors.append(name + '_catastrophic_loss_guard_failed')
        if arm.get('source_complete') is not True or arm.get('downstream_context_bound') is not True:
            errors.append(name + '_source_or_downstream_incomplete')
    if all(dates) and max(dates[0]) >= min(dates[1]):
        errors.append('strategy_holdout_not_chronological')
    if set((evidence.get('train') or {}).get('opportunity_ids') or []) & set((evidence.get('holdout') or {}).get('opportunity_ids') or []):
        errors.append('strategy_opportunity_leak')
    if candidate.get('selected_without_holdout') is not True:
        errors.append('strategy_holdout_selection_leak')
    return sorted(set(errors))
