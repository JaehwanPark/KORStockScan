"""Offline Samsung policy, causal state, exit and repeated-opportunity replay.

This producer has no live caller. Price episodes never become native identities.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
import time

from src.engine.scalping import samsung_pattern_campaign as C
from src.engine.scalping import mechanistic_entry_runtime_policy as M
from src.engine.scalping import samsung_session_pattern_research as S
from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit

Q, E, R, D = C.Q, C.E, C.R, C.R.D
FAMILIES = ('base_recovery', 'absorption_release', 'failed_breakdown',
            'higher_low_sequence', 'pullback_resume', 'range_return')
EXITS = ('barrier', 'time_600', 'time_1200', 'trail_04_04', 'trail_04_08', 'trail_01_02',
         'state_failure', 'past_ceiling')
SCOPES = ('SOR_REGULAR', 'SOR_PREMARKET', 'SOR_AFTERMARKET',
          'NXT_PREMARKET', 'NXT_REGULAR_OVERLAP')
MODES = ('veto', 'soft_add', 'replace_soft')
AUTHORITY = {**C.AUTHORITY,
    'consumer_scope': 'offline_samsung_policy_episode_research',
    'benchmark_role': 'same_hash_main_capture_and_separate_price_path_replay',
    'primary_decision_metric': 'original_cost_bound_target_first_win_rate',
    'episode_metric': 'known_terminal_net_positive_fraction_with_time_exit',
    'native_promotion_support': False,
    'synthetic_native_identity': False,
    'success_preservation_veto': False,
    'pristine_holdout': False,
    'live_promotion_forbidden': True,
    'trailing_role': 'pure_formula_fixed_width_bid_peak_sensitivity_not_full_live_exit'}


def write(path, value):
    body = {**{k: v for k, v in value.items() if k != 'content_sha256'}, **AUTHORITY}
    body['content_sha256'] = R.digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(C.json.dumps(body, indent=2, allow_nan=False) + '\n')


def definitions():
    return [dict(id=f'{family}:{window}:{confirm}', family=family,
                 window=window, confirm=confirm)
            for family in FAMILIES for window in (300, 900) for confirm in (5, 15)]


def quote_prefix_end(ctx, qi):
    pos = bisect_left(ctx['valid'], qi)
    if pos == len(ctx['valid']) or ctx['valid'][pos] != qi:
        return qi
    return ctx['valid'][ctx['quote_ends'][pos]]


def connected_frames(ctx, previous, current):
    return (previous['ep'] == current['ep'] and current['t'] >= previous['t']
            and current['quote_index'] <= quote_prefix_end(ctx, previous['quote_index'])
            and current['index'] <= ctx['trade_ends'][previous['index']])


def state_signals(ctx, frames, definition, cost=.23):
    """Emit the first observed transition, with no access to future outcomes."""
    family, window, confirm = (definition[k] for k in ('family', 'window', 'confirm'))
    if family not in FAMILIES or window not in (300, 900) or confirm not in (5, 15):
        raise ValueError('unregistered_state_definition')
    state = None
    previous = None
    spent = None
    result = []
    for f in frames:
        x = f['windows'].get(str(window))
        if x is None or (previous is not None and not connected_frames(ctx, previous, f)):
            state = None
            spent = None
            previous = f if x is not None else None
            if x is None:
                continue
        p = previous['windows'].get(str(window)) if previous is not None else None
        buying = f['buy_share'] is not None and f['buy_share'] >= .5
        near = x['distance'] <= 500 and x['drawdown'] >= 500
        room = (x['high'] / f['ask'] - 1) * 100 - cost
        # Rearm only after a new observed price excursion. A repeated visit to
        # the same numeric low can be a new cycle, but a persistent touch cannot.
        if spent is not None and (f['bid'] >= spent[1] + 1000 or f['bid'] < spent[1] - 500):
            spent = None
        if state is not None and f['t'] - state['born'] > window:
            state = None
        if state is None:
            anchor = x['low']
            arm = near
            support = None
            if family == 'absorption_release':
                arm = near and f['sell_dominant'] and f['hold'] >= confirm and f['sell_count'] >= 3
            elif family == 'failed_breakdown':
                arm = bool(p and f['bid'] < p['low'])
                support = p['low'] if p else None
            elif family == 'pullback_resume':
                arm = bool(p and previous['bid'] < p['high'] <= f['bid'] and x['high'] - x['low'] >= 1000)
                anchor = p['high'] if p else anchor
            elif family == 'range_return':
                arm = near and room >= .1 and f['hold'] >= confirm
            elif family == 'higher_low_sequence':
                arm = near and x['high'] - x['low'] >= 1000
            if arm and (f['ep'], anchor) != spent:
                state = dict(born=f['t'], low=f['bid'], low_at=f['t'], high=f['bid'],
                             anchor=anchor, support=support, phase='armed', phase_at=f['t'])
        hit = False
        if state is not None:
            if f['bid'] < state['low']:
                state['low'] = f['bid']
                state['low_at'] = f['t']
                if family == 'higher_low_sequence':
                    state['phase'] = 'armed'
            if family in ('base_recovery', 'range_return'):
                hit = (f['t'] - state['low_at'] >= confirm and f['bid'] >= state['low'] + 500
                       and buying and (family != 'range_return' or room >= .1))
            elif family == 'absorption_release':
                hit = (f['t'] - state['born'] >= confirm and f['bid'] >= state['low']
                       and buying and f['sell_decay'] is not None and f['sell_decay'] <= .5)
            elif family == 'failed_breakdown':
                hit = (f['t'] - state['born'] >= confirm and f['bid'] >= state['support'] and buying)
            elif family == 'higher_low_sequence':
                if f['bid'] <= state['low'] and state['phase'] != 'armed':
                    state.update(phase='armed', high=f['bid'], phase_at=f['t'])
                if state['phase'] == 'armed' and f['bid'] >= state['low'] + 500:
                    state.update(phase='bounce', high=f['bid'], phase_at=f['t'])
                elif state['phase'] == 'bounce':
                    state['high'] = max(state['high'], f['bid'])
                    if state['low'] < f['bid'] <= state['high'] - 500:
                        state.update(phase='retest', second_low=f['bid'], phase_at=f['t'])
                elif state['phase'] == 'retest':
                    state['second_low'] = min(state['second_low'], f['bid'])
                    hit = (state['second_low'] > state['low'] and f['t'] - state['phase_at'] >= confirm
                           and f['bid'] >= state['second_low'] + 500 and buying)
            elif family == 'pullback_resume':
                if state['phase'] == 'armed':
                    state['high'] = max(state['high'], f['bid'])
                    if f['bid'] <= state['high'] - 500:
                        state.update(phase='pullback', pullback_low=f['bid'], phase_at=f['t'])
                else:
                    state['pullback_low'] = min(state['pullback_low'], f['bid'])
                    hit = (f['t'] - state['phase_at'] >= confirm
                           and state['pullback_low'] >= state['anchor'] - 500
                           and f['bid'] >= state['pullback_low'] + 500 and buying)
            if hit:
                result.append(dict(f, state_born=state['born'], anchor=state['anchor'],
                                   state_rule=definition['id']))
                spent = (f['ep'], state['anchor'])
                state = None
        previous = f
    return result


def exit_label(ctx, signal, model, cost=.23, latency=0.):
    """A chronological observed-price sensitivity, never a filled position."""
    if model not in EXITS or not R.finite(cost) or cost < 0:
        raise ValueError('unregistered_exit_model_or_cost')
    horizon = 600 if model == 'time_600' else 1200
    base = C.label(ctx, signal, horizon=horizon, cost_pct=cost, latency=latency)
    if model == 'barrier' or 'entry' not in base:
        return dict(base, exit_model=model, terminal_win=int(base['net'] > 0) if base['complete'] else None)
    entry = base['entry']
    qi = entry['quote_index']
    deadline = entry['t'] + horizon
    end = min(quote_prefix_end(ctx, qi), len(ctx['depth']) - 1)
    cutoff = min(deadline, ctx['depth'][end]['t'], ctx['rows'][ctx['trade_ends'][entry['index']]]['t'])
    left = bisect_right(ctx['actionable_times'], entry['t'])
    right = bisect_right(ctx['actionable_times'], cutoff)
    peak = entry['price']
    armed = False
    start, width = (.1, .2) if model == 'trail_01_02' else (.4, .8 if model == 'trail_04_08' else .4)
    common = {k: v for k, v in base.items() if k not in (
        'binary', 'net', 'complete', 'status', 'exit_t', 'exit_bid', 'terminal_win', 'after_terminal_gap_ignored')}
    target = entry['price'] * (1 + (cost + .1) / 100)
    past_window = (signal.get('windows') or {}).get('900') or (signal.get('windows') or {}).get('300')
    if model == 'past_ceiling' and past_window is None:
        return dict(common, complete=False, binary=None, net=None, terminal_win=None,
                    status='past_ceiling_input_missing', exit_model=model, after_terminal_gap_ignored=False)
    if model == 'past_ceiling':
        target = max(target, past_window['high'])
    state_floor = ctx['depth'][qi]['bid'] - 500
    for k in range(left, right):
        q = ctx['depth'][ctx['actionable'][k]]
        gross = (q['bid'] / entry['price'] - 1) * 100
        peak = max(peak, q['bid'])
        decision = evaluate_trailing_take_profit(
            peak_price=peak, executable_bid=q['bid'], peak_profit_pct=(peak / entry['price'] - 1) * 100 - cost,
            start_pct=start, strong=False, weak_limit_pct=width, strong_limit_pct=width, already_armed=armed)
        armed = decision.armed
        target_hit = model in ('state_failure', 'past_ceiling') and q['bid'] >= target
        failure = model == 'state_failure' and q['bid'] <= state_floor
        if gross <= -.7 or failure or target_hit or (model.startswith('trail') and decision.triggered):
            net = gross - cost
            status = 'stop_first' if gross <= -.7 else 'state_failure' if failure else 'target_first' if target_hit else 'trailing_exit'
            return dict(common, complete=True, binary=0 if gross <= -.7 else 1 if target_hit else None, net=net,
                        terminal_win=int(net > 0), status=status,
                        exit_t=q['t'], exit_bid=q['bid'], exit_model=model,
                        after_terminal_gap_ignored=deadline > cutoff)
    # An earlier barrier label cannot prove the rest of a time/trailing path.
    timed = C.label(ctx, signal, horizon=horizon, target_net=1000., cost_pct=cost, latency=latency)
    if timed['complete'] and timed['status'] == 'neither':
        return dict(timed, exit_model=model, status='time_exit', terminal_win=int(timed['net'] > 0))
    return dict(common, complete=False, binary=None, net=None, terminal_win=None,
                status='censored_before_terminal', exit_model=model, after_terminal_gap_ignored=False)


def terminal_metric(outcomes):
    full = [r for r in outcomes if r['complete']]
    values = [r['net'] for r in full]
    wins = sum(n > 0 for n in values)
    binary = [r for r in full if r['binary'] is not None]
    targets = sum(r['binary'] == 1 for r in binary)
    n = len(full)
    return dict(attempts=len(outcomes), known_terminal=n, positive=wins, nonpositive=n - wins,
                win_rate=wins / n if n else None, wilson=E.wilson(wins, n),
                mean_net_cf=mean(values) if values else None, worst_net_cf=min(values) if values else None,
                censored=len(outcomes) - n, binary=len(binary), target_first=targets,
                conditional_target_first_win_rate=targets / len(binary) if binary else None,
                unknown_win_bounds=[wins / len(outcomes), (wins + len(outcomes) - n) / len(outcomes)] if outcomes else None,
                states=dict(Counter(r['status'] for r in outcomes)))


def replay(signals, get_label, *, cooldown=5, reservation='terminal'):
    """Unknown termination blocks later admissions; never assume a flat account."""
    if cooldown not in (5, 60) or reservation not in ('terminal', 'horizon'):
        raise ValueError('unregistered_admission_model')
    until = -C.math.inf
    outcomes = []
    blocked = 0
    for f in sorted(signals, key=lambda r: (r['t'], r['index'])):
        if f['t'] < until:
            blocked += 1
            continue
        out = get_label(f)
        outcomes.append(dict(out, signal_t=f['t'], signal_index=f['index'],
                             captured_trace=f.get('captured_trace')))
        if not out['complete']:
            until = C.math.inf
        elif reservation == 'horizon':
            until = out['entry']['t'] + out['horizon'] + cooldown
        else:
            until = out['exit_t'] + cooldown
    return dict(metric=terminal_metric(outcomes), outcomes=outcomes, blocked_signals=blocked,
                reservation=reservation, cooldown=cooldown, broker_custody_verified=False)


def opportunity_census(ctx, frames, cost):
    """Future extrema are a diagnostic upper bound, unavailable to any rule."""
    stats = {str(h): Counter() for h in (120, 600, 1200, 3600)}
    maxima = {k: [] for k in stats}
    for f in frames:
        e = Q.entry_for(ctx, f)
        if e is None or not C.actionable(ctx['depth'][e['quote_index']]):
            continue
        cutoff = min(ctx['depth'][quote_prefix_end(ctx, e['quote_index'])]['t'],
                     ctx['rows'][ctx['trade_ends'][e['index']]]['t'])
        left = bisect_right(ctx['actionable_times'], e['t'])
        for key, s in stats.items():
            deadline = e['t'] + int(key)
            right = bisect_right(ctx['actionable_times'], min(deadline, cutoff))
            s['frames'] += 1
            if left < right:
                _, high = ctx['tree'].extrema(left, right)
                maximum = (high / e['price'] - 1) * 100 - cost
                maxima[key].append(maximum)
                if maximum >= .1:
                    s['observed_fee_covering_move'] += 1
            endpoint = Q.quote_at(ctx['depth'], ctx['dt'], deadline, e['epoch'])
            full = (cutoff >= deadline - 1.5 and E.full_path(ctx['rows'], ctx['times'], ctx['trade_ends'], e, int(key))
                    and endpoint is not None and C.actionable(ctx['depth'][endpoint])
                    and endpoint <= quote_prefix_end(ctx, e['quote_index']))
            s['full_horizon' if full else 'censored_horizon'] += 1
    return {k: dict(v, max_observed_net_mfe=max(maxima[k]) if maxima[k] else None,
                    independent_opportunity_count=False) for k, v in stats.items()}


def excursion_census(ctx, cost, net_target=.1):
    """Nonoverlapping low-to-recovery movements; lows are retrospective only."""
    low = previous = None
    until = -C.math.inf
    cycles = []
    for qi, q in enumerate(ctx['depth']):
        if not C.actionable(q) or q['t'] < until:
            continue
        ti = bisect_right(ctx['times'], q['t']) - 1
        good_trade = (ti >= 0 and ctx['rows'][ti]['valid'] and ctx['rows'][ti]['ep'] == q['ep']
                      and q['t'] - ctx['times'][ti] <= 1.5)
        good_prefix = (previous is not None and qi <= quote_prefix_end(ctx, previous['qi'])
                       and good_trade and ti <= ctx['trade_ends'][previous['ti']])
        if not good_prefix:
            low = None
        if not good_trade:
            previous = None
            continue
        current = dict(qi=qi, ti=ti, t=q['t'], ask=q['ask'], ep=q['ep'])
        if low is None or q['ask'] < low['ask']:
            low = current
        if q['t'] > low['t'] and q['bid'] >= low['ask'] * (1 + (cost + net_target) / 100):
            cycles.append(dict(low=low, recovery_t=q['t'], recovery_bid=q['bid'],
                               observed_net_move=(q['bid'] / low['ask'] - 1) * 100 - cost,
                               duration_sec=q['t'] - low['t']))
            until = q['t'] + 60
            low = previous = None
        else:
            previous = current
    return dict(events=len(cycles), cycles=cycles, cost_pct=cost, net_target=net_target,
                cooldown_sec=60, retrospective_low_not_tradable_entry=True,
                independent_samples=False, native_promotion_support=False)


def binary_metric(rows):
    eligible = [r for r in rows if r['label']['binary'] is not None]
    wins = sum(r['label']['binary'] == 1 for r in eligible)
    return dict(attempts=len(rows), binary=len(eligible), wins=wins,
                losses=len(eligible) - wins, unknown=len(rows) - len(eligible),
                win_rate=wins / len(eligible) if eligible else None, wilson=E.wilson(wins, len(eligible)))


def promotion_feasibility(rows):
    """An identity upper bound, independent of any candidate's signal quality."""
    groups = {day: {tuple(r['native']) for r in rows if r['day'] == day and r['native'] is not None}
              for day in R.DAYS}
    train_upper = len(set().union(*(groups[d] for d in R.DAYS[:2])))
    held_upper = len(groups[R.DAYS[2]])
    return dict(contract='native_scanner_or_fixed_watch_v2',
                native_groups_per_day={d: len(g) for d, g in groups.items()},
                train_selected_opportunity_upper_bound=train_upper,
                held_selected_opportunity_upper_bound=held_upper,
                publisher_train_floor=30, publisher_holdout_floor=10,
                eligible_under_current_identity_contract=train_upper >= 30 and held_upper >= 10,
                source_scope='sealed_retained_samsung_capture_only',
                missing_identity_not_synthesized=True)


def native_first(rows, selected):
    found = set()
    result = []
    for r in sorted(rows, key=lambda r: (r['t'], r['trace'])):
        if r['trace'] not in selected or r['native'] is None:
            continue
        key = tuple(r['native'])
        if key not in found:
            found.add(key)
            result.append(r)
    return result


def paired_native(rows, baseline_ids, candidate_ids):
    old = {tuple(r['native']): r for r in native_first(rows, baseline_ids)}
    new = {tuple(r['native']): r for r in native_first(rows, candidate_ids)}
    counts = Counter()
    changes = []
    for identity in sorted(old.keys() | new.keys(), key=str):
        a, b = old.get(identity), new.get(identity)
        av = a['label']['binary'] if a else None
        bv = b['label']['binary'] if b else None
        same = a is not None and b is not None and a['trace'] == b['trace']
        counts['unchanged' if same else 'changed'] += 1
        if not same:
            counts['changed_known_both' if a and b and av is not None and bv is not None else 'changed_unresolved_or_admission'] += 1
            changes.append(dict(native_identity=list(identity), baseline_trace=a['trace'] if a else None,
                                candidate_trace=b['trace'] if b else None,
                                baseline_binary=av, candidate_binary=bv,
                                baseline_status=a['label'].get('status', 'unknown') if a else 'not_admitted',
                                candidate_status=b['label'].get('status', 'unknown') if b else 'not_admitted'))
    return dict(counts=dict(counts), changes=changes)


def captured_mask(rows, frames, ctx, signals, mode):
    if mode not in MODES:
        raise ValueError('unregistered_capture_mode')
    ft = [f['t'] for f in frames]
    st = [s['t'] for s in signals]
    chosen = set()
    census = Counter()
    for r in rows:
        i = bisect_left(ft, r['t']) - 1
        j = bisect_left(st, r['t']) - 1
        fresh = (i >= 0 and r['t'] - ft[i] <= 1.5 and r['features'].get('stream_valid') is True
                 and frames[i]['ep'] == r['features'].get('stream_epoch'))
        hit = bool(fresh and j >= 0 and r['t'] - st[j] <= 60
                   and connected_frames(ctx, signals[j], frames[i])
                   and frames[i]['ask'] <= signals[j]['ask'] + 500
                   and frames[i]['bid'] >= signals[j]['anchor'])
        safe = r['guard']['cohort'] in ('parent_enter', 'soft_confirmation_only') and not r['guard']['blockers']
        parent_enter = r['parent'] == 'ENTER_NOW'
        soft_enter = hit and safe and r['recoverable']
        admitted = (parent_enter and hit) if mode == 'veto' else (
            parent_enter or soft_enter) if mode == 'soft_add' else ((parent_enter and hit) or soft_enter)
        if hit:
            census['state_matches'] += 1
            census['guard_compatible' if safe else 'guard_blocked'] += 1
        if admitted:
            chosen.add(r['trace'])
    return chosen, dict(census)


def choose_native(rows, definitions_, masks, train_days, unit='native'):
    """The original target-first objective; no retained-success or EV veto."""
    training = [r for r in rows if r['day'] in train_days]
    baseline_ids = {r['trace'] for r in training if r['parent'] == 'ENTER_NOW'}
    if unit not in ('native', 'trace'):
        raise ValueError('unregistered_capture_unit')
    def admitted(ids):
        return native_first(training, ids) if unit == 'native' else [r for r in training if r['trace'] in ids]
    base = binary_metric(admitted(baseline_ids))
    candidates = []
    for definition in definitions_:
        for mode in MODES:
            key = definition['id'] + ':' + mode
            m = binary_metric(admitted(masks[key]))
            candidates.append(dict(key=key, metric=m))
    eligible = [c for c in candidates if c['metric']['binary'] >= 3 and base['binary'] >= 3
                and c['metric']['win_rate'] > base['win_rate']]
    selected = max(eligible, key=lambda c: (c['metric']['win_rate'], c['metric']['wilson'],
                                          c['metric']['binary'], -len(c['key']), c['key'])) if eligible else None
    return dict(train_days=list(train_days), unit=unit, baseline=base, candidates=candidates, selected=selected)


def current_generation(policy_root):
    """Resolve the immutable adopted generation, never the dated staging file."""
    selector_path = policy_root / 'current.json'
    selector = R.read(selector_path)
    if (selector.get('schema') != 'main_entry_current_v2'
            or selector.get('receipt_sha256') != M.digest({k: v for k, v in selector.items() if k != 'receipt_sha256'})
            or len(str(selector.get('bundle_sha256', ''))) != 64
            or any(c not in '0123456789abcdef' for c in selector['bundle_sha256'])):
        raise ValueError('invalid_current_receipt')
    effective_path = policy_root / 'generations' / (selector['bundle_sha256'] + '.json')
    effective = R.read(effective_path)
    M.validate(effective, target_date=effective['target_date'])
    activation = effective.get('strategy_activation') or {}
    if (effective['bundle_sha256'] != selector['bundle_sha256']
            or activation.get('effective_from') != selector.get('effective_from')
            or activation.get('parent_bundle_sha256') != selector.get('previous_bundle_sha256')):
        raise ValueError('invalid_current_generation_binding')
    return selector, effective, selector_path, effective_path


def load_sources(root):
    base = root / 'tmp/samsung-pattern-campaign-20261004'
    regular, a, _ = C.load_manifest(base / 'verified-regular-source/manifest.json')
    sessions, b, _ = C.load_manifest(base / 'verified-session-source/manifest.json')
    projection = R.read(Path(regular['projection']))
    seals = {**a, **b}
    policy_root = root / 'data/runtime/mechanistic_entry_policy'
    selector, effective, selector_path, effective_path = current_generation(policy_root)
    dated_path = policy_root / 'policy_2026-10-06.json'
    dated = R.read(dated_path)
    M.validate(dated, target_date='2026-10-06')
    frozen_path = root / 'tmp/machine-confirmation-candidate-research-20261003/run-final/frozen-candidates.json'
    frozen = R.read(frozen_path)['parent_policy']
    def scoped(bundle):
        return bundle['scope_policies']['KRX|KRX_REGULAR']['machine_policy']
    parent_hash = R.S.digest(frozen)
    if (parent_hash != projection['parent_sha256'] or R.S.digest(scoped(effective)) != parent_hash
            or R.S.digest(scoped(dated)) != parent_hash or selector['bundle_sha256'] != effective['bundle_sha256']):
        raise ValueError('current_or_dated_machine_parent_differs_from_capture')
    for p in (selector_path, effective_path, dated_path, frozen_path):
        seals[str(p)] = R.P.file_sha(p)
    for p in (Path(__file__).resolve(), root / 'src/engine/scalping/trailing_exit_decision.py',
              root / 'src/engine/scalping/mechanistic_entry_runtime_policy.py',
              root / 'src/tests/test_samsung_policy_episode_research.py',
              root / 'docs/proposals/samsung-policy-episode-replay-research-plan-2026-10-04.md'):
        seals[str(p)] = R.P.file_sha(p)
    Q.verify_hashes(seals)
    captured = {r['trace']: r for r in projection['main']}
    reproduced = 0
    for day in R.DAYS:
        raw_path = root / f'data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json'
        for raw in R.P.stream_array(raw_path):
            r = captured.get(raw['decision_trace_id'])
            if r is None:
                continue
            prepared = D.fast_prepare(raw, frozen)
            if prepared['decision']['action'] != r['parent'] or D.guard_summary(prepared) != r['guard']:
                raise ValueError('captured_parent_replay_mismatch')
            reproduced += 1
    if reproduced != len(captured) or len(captured) != len(projection['main']):
        raise ValueError('captured_trace_missing_or_duplicate')
    return regular, sessions, projection, seals, dict(parent_sha256=parent_hash,
        effective_bundle=effective['bundle_sha256'], dated_bundle=dated['bundle_sha256'],
        reproduced_captures=reproduced, current_policy_files_verified=True, pid_consumption_claimed=False)


def prior_day(root, output, primary_result):
    """Stress frozen conditions on an existing earlier day, never a holdout."""
    primary = R.read(primary_result)
    Q.verify_hashes(primary['source_seals'])
    records = {str(primary_result): R.P.file_sha(primary_result), str(Path(__file__).resolve()): R.P.file_sha(Path(__file__))}
    day = '2026-09-28'
    # Configuration of this offline CLI reader only; restore its route table.
    routes = S.SESSION_ROUTES
    try:
        S.SESSION_ROUTES = {**routes, 'SOR_REGULAR': ('SOR', '005930_AL')}
        cache, books, stats = S.partition(root, day, 'SOR_REGULAR', records)
    finally:
        S.SESSION_ROUTES = routes
    reference = R.P.calibration.existing_or_gzip_path(root / f'data/report/micro_reversion_economic_reference/micro_reversion_economic_reference_{day}.json')
    if reference is None:
        raise ValueError('prior_day_cost_reference_missing')
    body = R.P.calibration._load_json(reference)
    records[str(reference)] = R.P.file_sha(reference)
    records.update({str(Path(r['resolved_path']).resolve()): r['expected_sha256'] for r in body['source_artifacts']})
    profiles = {v: R.P.calibration._hierarchy_cost_profiles(root / 'data', day, v).get('005930') for v in ('KRX', 'NXT')}
    if not all(profiles.values()):
        raise ValueError('prior_day_exact_cost_missing')
    costs = {v: sum(p[k] for k in ('buy_fee_bps', 'sell_fee_bps', 'statutory_sell_tax_bps', 'uncertainty_buffer_bps')) / 100
             for v, p in profiles.items()}
    if costs['KRX'] != costs['NXT']:
        raise ValueError('prior_day_route_cost_mismatch')
    cost = costs['KRX']
    frames = C.feature_rows(cache, books)
    ctx = C.campaign_context(cache)
    signals = {d['id']: state_signals(ctx, frames, d, cost) for d in definitions()}
    labels = {}
    def get(f, model, friction):
        key = (f['index'], model, friction)
        if key not in labels:
            labels[key] = exit_label(ctx, f, model, friction)
        return labels[key]
    outcomes = {}
    daily = {}
    for definition in definitions():
        for friction in (cost, .33):
            for model in EXITS:
                for cooldown in (5, 60):
                    key = f"{definition['id']}:{model}:{friction}:{cooldown}"
                    result = replay(signals[definition['id']], lambda f: get(f, model, friction), cooldown=cooldown)
                    outcomes[key] = result
                    daily[key] = result['metric']
    frozen = []
    for fold in primary['price_folds']:
        if fold['scope'] != 'SOR_REGULAR' or fold['selected'] is None:
            continue
        held_rule = fold['held']
        earlier_key = f"{held_rule['definition']['id']}:{held_rule['model']}:{cost}:{held_rule['cooldown']}"
        frozen.append(dict(family=fold['family'], train_days=fold['train_days'],
                           primary_held_day=fold['held_day'], key=fold['selected']['key'],
                           earlier_key=earlier_key, earlier_day=daily[earlier_key]))
    Q.verify_hashes(records)
    Q.verify_hashes(primary['source_seals'])
    Q.verify_hashes(primary['preserved'])
    write(output / 'result.json', dict(day=day, scope='SOR_REGULAR', stats=stats, frames=len(frames),
        source_seals={**primary['source_seals'], **records}, preserved=primary['preserved'],
        fee_profile=profiles, cost_pct=cost, frozen_candidates=frozen, daily=daily,
        outcomes=outcomes, state_signals=signals, opportunity_census=opportunity_census(ctx, frames, cost),
        excursions={str(n): excursion_census(ctx, cost, n) for n in (0., .1, .4)},
        earlier_day_role='previously_unused_prior_day_stress_not_chronological_holdout',
        main_capture_unavailable=True, official_policy_candidate=None))
    print('prior day', day, 'frames', len(frames), 'state signals', sum(map(len, signals.values())), flush=True)


def run(root, output, max_quote_gap=1.5):
    started = time.monotonic()
    regular, sessions, projection, seals, binding = load_sources(root)
    rows = projection['main']
    defs = definitions()
    masks = {d['id'] + ':' + m: set() for d in defs for m in MODES}
    daily = {}
    detail = {}
    price_baselines = {}
    state_census = {}
    price_folds = []
    for scope in SCOPES:
        for day in R.DAYS:
            key = scope + '|' + day
            if scope == 'SOR_REGULAR':
                prepared = R.read(Path(regular['files'][day]['path']))
                cache = E.read_cache(Path(prepared['cache']['path']))
                frames = prepared['frames']
            else:
                cache = E.read_cache(Path(sessions['files'][key]['path']))
                frames = cache['frames']
            ctx = C.campaign_context(cache, max_quote_gap)
            signal_ctx = ctx if max_quote_gap == 1.5 else C.campaign_context(cache)
            cost = regular['fee_profiles'][day]['cost_pct']
            signals = {d['id']: state_signals(signal_ctx, frames, d, cost) for d in defs}
            native_rows = [r for r in rows if r['day'] == day] if scope == 'SOR_REGULAR' else []
            if native_rows:
                for d in defs:
                    for mode in MODES:
                        ids, census = captured_mask(native_rows, frames, signal_ctx, signals[d['id']], mode)
                        masks[d['id'] + ':' + mode].update(ids)
                        state_census[key + ':' + d['id'] + ':' + mode] = census
            current = []
            frame_times = [f['t'] for f in frames]
            for r in native_rows:
                if r['parent'] != 'ENTER_NOW':
                    continue
                i = bisect_right(ctx['times'], r['t']) - 1
                if i >= 0 and r['t'] - ctx['times'][i] <= 1.5 and ctx['rows'][i]['ep'] == r['features'].get('stream_epoch'):
                    fi = bisect_left(frame_times, r['t']) - 1
                    point = Q.entry_for(ctx, dict(index=i, t=r['t']))
                    fresh = (point is not None and fi >= 0 and r['t'] - frames[fi]['t'] <= 1.5
                        and connected_frames(signal_ctx, frames[fi], dict(index=i, t=r['t'],
                            quote_index=point['quote_index'], ep=point['epoch'])))
                    past_windows = frames[fi]['windows'] if fresh else {}
                    current.append(dict(index=i, t=r['t'], captured_trace=r['trace'], windows=past_windows))
            labels = {}
            def get(f, model, friction, latency=0.):
                lk = (f['index'], f['t'], model, friction, latency)
                if lk not in labels:
                    labels[lk] = exit_label(ctx, f, model, friction, latency)
                return labels[lk]
            results = {}
            bases = {}
            for friction in (cost, .33):
                for model in EXITS:
                    for cooldown in (5, 60):
                        base_key = f'{model}:{friction}:{cooldown}'
                        base = replay(current, lambda f: get(f, model, friction), cooldown=cooldown)
                        bases[base_key] = base['metric'] if native_rows else None
                        detail[key + ':main:' + base_key] = base
                        for d in defs:
                            rule_key = d['id'] + ':' + base_key
                            result = replay(signals[d['id']], lambda f: get(f, model, friction), cooldown=cooldown)
                            fixed = replay(signals[d['id']], lambda f: get(f, model, friction), cooldown=cooldown, reservation='horizon')
                            results[rule_key] = dict(definition=d, model=model, cost=friction, cooldown=cooldown,
                                baseline_key=base_key, metric=result['metric'], horizon_reserved_metric=fixed['metric'],
                                emitted_signals=len(signals[d['id']]), blocked_signals=result['blocked_signals'])
                            detail[key + ':' + rule_key] = result
            daily[key] = results
            price_baselines[key] = bases
            write(output / (scope + '-' + day + '-opportunities.json'), dict(scope=scope, day=day,
                fee_profile=regular['fee_profiles'][day], frames=len(frames),
                opportunity_census=opportunity_census(ctx, frames, cost),
                opportunity_census_stress=opportunity_census(ctx, frames, .33),
                excursions={str(n): excursion_census(ctx, cost, n) for n in (0., .1, .4)},
                state_signals=signals, fee_stress=.33, max_observed_quote_gap_sec=max_quote_gap))
            print(key, 'frames', len(frames), 'states', sum(map(len, signals.values())),
                  'labels', len(labels), flush=True)
        # Each family freezes one training choice before inspecting later results.
        for train_days, held in ((R.DAYS[:1], R.DAYS[1]), (R.DAYS[:2], R.DAYS[2])):
            for family in FAMILIES:
                candidates = []
                for rk, r in daily[scope + '|' + train_days[0]].items():
                    if r['definition']['family'] != family:
                        continue
                    # Cost is an evidence scenario, never a selectable policy knob.
                    if r['cost'] != regular['fee_profiles'][train_days[0]]['cost_pct']:
                        continue
                    outcomes = [o for td in train_days for o in detail[scope + '|' + td + ':' + rk]['outcomes']]
                    m = terminal_metric(outcomes)
                    if scope == 'SOR_REGULAR':
                        base_out = [o for td in train_days for o in detail[scope + '|' + td + ':main:' + r['baseline_key']]['outcomes']]
                        base_m = terminal_metric(base_out)
                    else:
                        base_m = None
                    candidates.append(dict(key=rk, metric=m, main_baseline=base_m))
                eligible = [c for c in candidates if c['metric']['known_terminal'] >= 3
                    and (c['main_baseline'] is None or (c['main_baseline']['known_terminal'] >= 3
                        and c['metric']['win_rate'] > c['main_baseline']['win_rate']))]
                selected = max(eligible, key=lambda c: (c['metric']['win_rate'], c['metric']['wilson'],
                    c['metric']['known_terminal'], -len(c['key']), c['key'])) if eligible else None
                held_result = daily[scope + '|' + held].get(selected['key']) if selected else None
                stress_key = (held_result['definition']['id'] + ':' + held_result['model'] +
                    ':0.33:' + str(held_result['cooldown'])) if held_result else None
                price_folds.append(dict(scope=scope, family=family, train_days=list(train_days), held_day=held,
                    selected=selected, held=held_result,
                    held_stress=daily[scope + '|' + held].get(stress_key) if stress_key else None,
                    held_main_baseline=price_baselines[scope + '|' + held].get(held_result['baseline_key']) if held_result else None,
                    training_candidates=candidates, causal_source_quality=True, native_promotion_support=False))
    native_folds = []
    for unit in ('native', 'trace'):
        for train_days, held in ((R.DAYS[:1], R.DAYS[1]), (R.DAYS[:2], R.DAYS[2])):
            fitted = choose_native(rows, defs, masks, train_days, unit)
            held_rows = [r for r in rows if r['day'] == held]
            base_ids = {r['trace'] for r in held_rows if r['parent'] == 'ENTER_NOW'}
            selected = fitted['selected']
            candidate_ids = masks[selected['key']] if selected else set()
            def admitted(ids):
                return native_first(held_rows, ids) if unit == 'native' else [r for r in held_rows if r['trace'] in ids]
            native_folds.append(dict(fitted, held_day=held,
                held_baseline=binary_metric(admitted(base_ids)),
                held_candidate=binary_metric(admitted(candidate_ids)) if selected else None,
                paired_training=paired_native([r for r in rows if r['day'] in train_days],
                    {r['trace'] for r in rows if r['day'] in train_days and r['parent'] == 'ENTER_NOW'},
                    candidate_ids) if selected else None,
                paired_held=paired_native(held_rows, base_ids, candidate_ids) if selected else None))
    native_daily = {}
    for day in R.DAYS:
        day_rows = [r for r in rows if r['day'] == day]
        ids = {r['trace'] for r in day_rows if r['parent'] == 'ENTER_NOW'}
        groups = Counter(tuple(r['native']) for r in day_rows if r['native'])
        native_daily[day] = dict(captures=len(day_rows), native_captures=sum(groups.values()),
            native_groups=len(groups), captures_per_native_group=list(groups.values()),
            incumbent_trace=binary_metric([r for r in day_rows if r['trace'] in ids]),
            incumbent_native=binary_metric(native_first(day_rows, ids)),
            candidates={rk: dict(trace=binary_metric([r for r in day_rows if r['trace'] in mask]),
                native=binary_metric(native_first(day_rows, mask))) for rk, mask in masks.items()})
    Q.verify_hashes(seals)
    Q.verify_hashes(regular['preserved'])
    write(output / 'result.json', dict(binding=binding, source_seals=seals, preserved=regular['preserved'],
        native_daily=native_daily, native_folds=native_folds, state_capture_census=state_census,
        daily=daily, price_folds=price_folds, price_baselines=price_baselines,
        state_definitions=defs, exits=list(EXITS), price_combinations_per_scope_day=768,
        native_combinations=72, elapsed_sec=time.monotonic() - started,
        price_selection_objective='known_terminal_net_positive_fraction_training_only',
        max_observed_quote_gap_sec=max_quote_gap, quote_gap_sensitivity=max_quote_gap != 1.5,
        status='bounded_hypotheses_evaluated_pending_final_review',
        promotion_feasibility=promotion_feasibility(rows),
        official_policy_candidate=None, execution_route_verified=False,
        extra_impact_assumed_zero=True, account_capacity_custody_not_reconstructed=True))
    write(output / 'outcomes.json', dict(outcomes=detail))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-quote-gap', type=float, choices=(1.5, 3., 10.), default=1.5)
    parser.add_argument('--prior-day-of', type=Path)
    args = parser.parse_args(argv)
    if args.prior_day_of:
        if args.max_quote_gap != 1.5:
            parser.error('prior-day stress uses the strict observation model')
        prior_day(args.root.resolve(), args.output.resolve(), args.prior_day_of.resolve())
    else:
        run(args.root.resolve(), args.output.resolve(), args.max_quote_gap)


if __name__ == '__main__':
    main()
