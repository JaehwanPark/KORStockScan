"""Offline extension: causal derivatives of already recorded program snapshots."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from pathlib import Path

from src.engine.scalping import samsung_environment_conditioned_research as N

P, R = N.P, N.R
AXES = ('program_change', 'sell_easing', 'net_acceleration', 'buy_acceleration', 'turn_positive')
HISTORY_GAPS = (60, 180, 300, 900)


def sequence_rows(captures, max_event_gap=60):
    """Distinct, causally available event clocks; duplicates add no support."""
    if max_event_gap not in HISTORY_GAPS:
        raise ValueError('unregistered_past_endpoint_interval')
    rows, history, previous_scope, conflict_clock = [], [], None, None
    for cap in captures:
        result = {axis: None for axis in AXES}
        result['sequence_status'] = 'unusable_current'
        scope = (cap['day'], cap['ep'], cap['market_route'], cap['market_suffix'])
        if scope != previous_scope:
            conflict_clock = None
        if (scope != previous_scope or not cap['stream_valid'] or cap['ep'] is None
                or N.source_status(cap['program'], cap) != 'valid'):
            history = []
        previous_scope = scope
        if cap['stream_valid'] and cap['ep'] is not None and N.source_status(cap['program'], cap) == 'valid':
            value = cap['program']['value']
            observed = R.epoch(cap['program']['observed_at'])
            keys = ('buy_qty', 'sell_qty', 'net_qty')
            if not all(R.finite(value.get(k)) for k in keys) or min(value['buy_qty'], value['sell_qty']) < 0:
                history = []
                result['sequence_status'] = 'numeric_missing'
            else:
                point = dict(t=observed, **{k: value[k] for k in keys})
                if conflict_clock is not None and point['t'] <= conflict_clock:
                    history = []
                    result['sequence_status'] = 'same_clock_conflict_quarantined'
                elif history and point['t'] == history[-1]['t']:
                    if point != history[-1]:
                        history = []
                        conflict_clock = point['t']
                        result['sequence_status'] = 'same_clock_conflict'
                else:
                    conflict_clock = None
                    if history and (not 0 < point['t'] - history[-1]['t'] <= max_event_gap
                            or any(point[k] < history[-1][k] for k in ('buy_qty', 'sell_qty'))):
                        history = []
                    history.append(point)
                    history = history[-3:]
                if history:
                    result['sequence_status'] = f'distinct_points_{len(history)}'
                if len(history) >= 2:
                    a, b = history[-2:]
                    result['program_change'] = N.sign(b['net_qty'] - a['net_qty'])
                if len(history) == 3:
                    a, b, c = history
                    def rate(x, y, key):
                        return (y[key] - x[key]) / (y['t'] - x['t'])
                    result.update(sell_easing=rate(b, c, 'sell_qty') < rate(a, b, 'sell_qty'),
                        net_acceleration=rate(b, c, 'net_qty') > rate(a, b, 'net_qty'),
                        buy_acceleration=rate(b, c, 'buy_qty') > rate(a, b, 'buy_qty'),
                        turn_positive=rate(a, b, 'net_qty') <= 0 < rate(b, c, 'net_qty'))
        rows.append(dict(cap, sequence=result))
    return rows


def asof(rows, times, t, ep):
    missing = {axis: None for axis in AXES}
    i = bisect_right(times, t) - 1
    if i < 0:
        return missing
    row = rows[i]
    if (row['ep'] != ep or ep is None or N.source_status(row['program'], row) != 'valid'
            or t - R.epoch(row['program']['observed_at']) > row['program']['freshness_limit_ms'] / 1000):
        return missing
    return row['sequence']


def selectors():
    result = [dict(id='all', conditions={})]
    for value in ('up', 'flat', 'down'):
        result.append(dict(id=f'program_change={value}', conditions={'program_change': value}))
    for axis in AXES[1:]:
        result.append(dict(id=f'{axis}=true', conditions={axis: True}))
    for axis, state in (('sell_easing', 'up'), ('sell_easing', 'flat'),
                        ('net_acceleration', 'up'), ('net_acceleration', 'down')):
        result.append(dict(id=f'{axis}=true&stock_300={state}', conditions={axis: True, 'stock_300': state}))
    result.append(dict(id='program_change=up&vwap_300=below', conditions={'program_change': 'up', 'vwap_300': 'below'}))
    result.append(dict(id='program_change=up&program_net=down', conditions={'program_change': 'up', 'program_net': 'down'}))
    expanded = [result[0]]
    for gap in HISTORY_GAPS:
        for definition in result[1:]:
            expanded.append(dict(id=f'past_gap_{gap}|' + definition['id'],
                conditions={k + f'_gap{gap}' if k in AXES else k: v
                            for k, v in definition['conditions'].items()}))
    return expanded


def run(root, output):
    accepted = root / 'tmp/samsung-environment-conditioned-research-20261004/accepted-cold'
    previous = R.read(accepted / 'result.json')
    census = R.read(accepted / 'source-census.json')
    seals = dict(previous['source_seals'])
    for path in (accepted / 'result.json', accepted / 'source-census.json', Path(__file__).resolve(),
            root / 'src/tests/test_samsung_program_sequence_research.py',
            root / 'docs/proposals/samsung-program-sequence-research-plan-2026-10-04.md'):
        seals[str(path)] = R.P.file_sha(path)
    P.Q.verify_hashes(seals)
    manifest, sources, _ = N.C.load_manifest(root / 'tmp/samsung-pattern-campaign-20261004/verified-regular-source/manifest.json')
    seals.update(sources)
    projection = R.read(Path(manifest['projection']))
    definitions = [d for d in P.definitions() if d['confirm'] == 5]
    registry = selectors()
    candidates, baselines, masks, source_census, replays = {}, {}, {}, {}, {}
    for day in N.DAYS:
        prepared = R.read(Path(manifest['files'][day]['path']))
        frames = prepared['frames']
        ctx = N.C.campaign_context(P.E.read_cache(Path(prepared['cache']['path'])))
        captures = [c for c in census['captures'] if c['day'] == day]
        env = N.environments(ctx, frames, captures)
        main = [r for r in projection['main'] if r['day'] == day]
        cenv = N.capture_environments(main, frames, ctx, captures)
        source_census[day] = {}
        for gap in HISTORY_GAPS:
            sequence = sequence_rows(captures, gap)
            times = [r['t'] for r in sequence]
            # Stored historical endpoints may be older than latest freshness.
            # No interpolation or claim of continuous sub-minute rates.
            for f in frames:
                env[f['index']].update({k + f'_gap{gap}': v for k, v in asof(sequence, times, f['t'], f['ep']).items() if k in AXES})
            for r in main:
                cenv[r['trace']].update({k + f'_gap{gap}': v for k, v in asof(sequence, times, r['t'], r['features'].get('stream_epoch')).items() if k in AXES})
            actual_prefix = all(sequence[:cut] == sequence_rows(captures[:cut], gap)
                                for cut in (len(captures)//3, 2*len(captures)//3))
            if not actual_prefix:
                raise ValueError('sequence_future_endpoint_dependency')
            source_census[day][str(gap)] = dict(captures=len(captures), actual_prefix_equal=actual_prefix,
                statuses=dict(Counter(r['sequence']['sequence_status'] for r in sequence)),
                frame_states={axis: dict(Counter(str(e.get(axis + f'_gap{gap}')) for e in env.values())) for axis in AXES})
        for selector in registry:
            masks.setdefault('parent_only|' + selector['id'], set()).update(N.parent_context_mask(main, selector, cenv))
        for definition in definitions:
            signals = P.state_signals(ctx, frames, definition)
            state_ids = {mode: P.captured_mask(main, frames, ctx, signals, mode)[0] for mode in P.MODES}
            labels = {}
            def label(f, model):
                key = (f['index'], model)
                if key not in labels:
                    labels[key] = P.exit_label(ctx, f, model, .23)
                return labels[key]
            for selector in registry:
                chosen = [f for f in signals if N.matches(env[f['index']], selector) is True]
                for model in ('barrier', 'state_failure'):
                    key = definition['id'] + '|' + selector['id'] + '|' + model
                    base_key = definition['id'] + '|' + model
                    replay = P.replay(chosen, lambda f: label(f, model), cooldown=60)
                    row = candidates.setdefault(key, dict(key=key, selector=selector['id'],
                        definition=definition['id'], exit=model, baseline=base_key, days={}))
                    row['days'][day] = replay['metric']
                    if selector['id'] == 'all':
                        baselines.setdefault(base_key, {})[day] = replay['metric']
                    replays[(day, key)] = replay
                for mode in P.MODES:
                    key = definition['id'] + '|' + selector['id'] + '|' + mode
                    masks.setdefault(key, set()).update(N.capture_mask(main, state_ids[mode], selector, cenv, mode))
    choice = N.select_price(list(candidates.values()), baselines)
    if choice['selected']:
        key = choice['selected']['key']
        choice['held'] = candidates[key]['days'][N.DAYS[2]]
        choice['held_baseline'] = baselines[candidates[key]['baseline']][N.DAYS[2]]
        choice['outcomes'] = {day: replays[(day, key)] for day in N.DAYS}
    P.Q.verify_hashes(seals)
    P.Q.verify_hashes(previous['preserved_policy_files'])
    N.write(output / 'result.json', dict(source_seals=seals, source_census=source_census,
        registry=registry, price_candidates=list(candidates.values()), price_selection=choice,
        main_native=N.native_summary(projection['main'], masks),
        preserved_policy_files=previous['preserved_policy_files'], official_policy_candidate=None,
        study_scope='past_distinct_program_rates_and_fixed_state_failure_exit',
        historical_endpoint_intervals=list(HISTORY_GAPS), latest_source_expiry_ms=60000,
        rate_role='past_endpoint_interval_average_not_interpolated_continuous_flow',
        derivative_source_role='recorded_program_context_not_new_protocol_or_order_authority'))
    return dict(output=str(output), price_candidates=len(candidates), selected=choice['selected'], official_policy_candidate=None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    print(N.json.dumps(run(args.root.resolve(), args.output.resolve()), allow_nan=False))


if __name__ == '__main__':
    main()
