"""Offline Samsung state/flow hypothesis replay. No live consumer or API calls."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime, time
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.scalping import samsung_opportunity_contract_research as O

P, R, C = O.P, O.P.R, O.P.C
DAYS = tuple(R.DAYS)
TRAIN = DAYS[:2]
EXITS = ('barrier', 'time_600', 'time_1200')
AUTHORITY = {**P.AUTHORITY,
    'consumer_scope': 'offline_samsung_environment_conditioned_research',
    'metric_role': 'report_only_environment_conditioned_price_and_native_comparison',
    'primary_decision_metric': 'known_terminal_net_positive_fraction_for_price_shortlist',
    'source_quality_gate': 'canonical_trace_route_epoch_asof_availability_and_original_expiry',
    'external_market_inferred_from_stock': False,
    'live_selector_registered': False}


def write(path, value):
    body = {**{k: v for k, v in value.items() if k != 'content_sha256'}, **AUTHORITY}
    body['content_sha256'] = R.digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + '\n')


def selectors():
    """Outcome-independent finite registry; unknown never means flat."""
    result = [dict(id='all', conditions={})]
    axes = ('stock_300', 'stock_900', 'program_net', 'program_delta',
            'foreign', 'institution', 'smart_money')
    for axis in axes:
        for value in ('down', 'flat', 'up'):
            result.append(dict(id=f'{axis}={value}', conditions={axis: value}))
    for axis in ('vwap_300', 'vwap_900'):
        for value in ('below', 'above'):
            result.append(dict(id=f'{axis}={value}', conditions={axis: value}))
    result.append(dict(id='past_range_900=cost_room', conditions={'past_range_900': 'cost_room'}))
    for stock in ('down', 'flat', 'up'):
        for flow in ('down', 'flat', 'up'):
            result.append(dict(id=f'stock_900={stock}&program_delta={flow}',
                               conditions={'stock_900': stock, 'program_delta': flow}))
    for net, delta in (('down', 'up'), ('up', 'down')):
        result.append(dict(id=f'program_net={net}&program_delta={delta}',
                           conditions={'program_net': net, 'program_delta': delta}))
    result.append(dict(id='program_delta=up&smart_money=up',
                       conditions={'program_delta': 'up', 'smart_money': 'up'}))
    for breadth in ('down', 'flat', 'up'):
        result.append(dict(id=f'prior_published_breadth={breadth}',
                           conditions={'prior_published_breadth': breadth}))
        for stock in ('down', 'flat', 'up'):
            result.append(dict(id=f'prior_published_breadth={breadth}&stock_900={stock}',
                conditions={'prior_published_breadth': breadth, 'stock_900': stock}))
    return result


def matches(environment, definition):
    values = [(environment.get(k), v) for k, v in definition['conditions'].items()]
    # Missing required context retains parent in the capture adapter, even if
    # another known dimension is false. It never admits a new price signal.
    if any(actual is None for actual, _ in values):
        return None
    return all(actual == expected for actual, expected in values)


def sign(value, threshold=0.):
    if not R.finite(value):
        return None
    return 'up' if value > threshold else 'down' if value < -threshold else 'flat'


def optional_epoch(value):
    try:
        return R.epoch(value)
    except (TypeError, ValueError, OverflowError):
        return None


def published_breadth(reports, asof):
    """A previously published blue-chip pool breadth, never an intraday index."""
    eligible = [r for r in reports if r['published_t'] <= asof]
    if not eligible:
        return dict(state=None, status='no_preexisting_published_report')
    source = max(eligible, key=lambda r: (r['published_t'], r['path']))
    # Preserve the reported quote date and its age; a newer publication cannot
    # renew an old quote population. Fixed 72h age is a diagnostic convention.
    if (asof - source['quote_close_t'] > 72 * 3600 or source['quote_close_t'] > source['published_t']
            or source['published_t'] > asof):
        return dict(state=None, status='published_but_quote_population_expired', source=source)
    ratio = source['ma20_ratio']
    return dict(state='down' if ratio < 40 else 'up' if ratio >= 60 else 'flat',
                status='valid_prior_published_blue_chip_pool', source=source)


def breadth_intake(root):
    reports, seals, excluded = [], {}, []
    # Only preceding-day publications for the bounded three-date study.
    # No generated cache or same-day EOD output is backfilled onto decisions.
    for day in ('2026-09-28', '2026-09-29', '2026-09-30'):
        path = root / f'data/report/report_{day}.json'
        if not path.exists():
            continue
        seals[str(path)] = R.P.file_sha(path)
        try:
            raw = R.read(path)
            stats, meta = raw.get('stats') or {}, raw.get('meta') or {}
            ratio, count = stats.get('ma20_ratio'), stats.get('total_valid')
            if not R.finite(ratio) or not 0 <= ratio <= 100 or not R.finite(count) or count <= 0:
                raise ValueError('prior_report_breadth_domain_invalid')
            published = datetime.strptime(meta['report_generated_at'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=ZoneInfo('Asia/Seoul'))
            quote_day = datetime.strptime(stats['quote_date'], '%Y-%m-%d').date()
            quote_close = datetime.combine(quote_day, time(15, 30), tzinfo=ZoneInfo('Asia/Seoul'))
        except (KeyError, ValueError, TypeError, AttributeError) as error:
            excluded.append(dict(path=str(path), physical_sha256=seals[str(path)],
                                 reason='invalid_optional_breadth_source', error_type=type(error).__name__))
            continue
        reports.append(dict(path=str(path), physical_sha256=seals[str(path)],
            published_t=published.timestamp(), quote_close_t=quote_close.timestamp(),
            published_at=published.isoformat(), quote_date=quote_day.isoformat(),
            ma20_ratio=ratio, total_valid=count, role='previous_published_blue_chip_pool_not_whole_market'))
    producer = root / 'src/engine/daily_report_service.py'
    seals[str(producer)] = R.P.file_sha(producer)
    return reports, seals, excluded


def source_status(source, capture, *, investor=False):
    """Validate normalized recorded domain; this does not parse API packets."""
    if not isinstance(source, dict) or not isinstance(source.get('value'), dict):
        return 'missing'
    observed = optional_epoch(source.get('observed_at'))
    limit = source.get('freshness_limit_ms')
    if source.get('quality') != 'fresh':
        return 'recorded_' + str(source.get('quality') or 'unknown_quality')
    if observed is None or not R.finite(limit) or not 0 < limit <= 60000:
        return 'invalid_clock_or_expiry'
    if observed > capture['t'] or capture['t'] - observed > limit / 1000:
        return 'future_or_expired_at_capture'
    if (source.get('market_suffix') != capture['market_suffix']
            or source.get('market_route') != capture['market_route']):
        return 'route_conflict'
    age = source.get('age_ms')
    snapshot_t = capture['snapshot_t']
    if (not R.finite(age) or age < 0 or snapshot_t is None or snapshot_t > capture['t']
            or abs((snapshot_t - observed) * 1000 - age) > 100):
        return 'recorded_age_conflict'
    if investor and (source['value'].get('source_data_date') != capture['day']
                     or source['value'].get('request_code') != '005930' + capture['market_suffix']):
        return 'investor_date_or_item_conflict'
    return 'valid'


def intake(root, projection):
    """Read only the exact frozen capture locations, verifying canonical hashes."""
    accepted = root / 'tmp/samsung-opportunity-contract-20261004/accepted-source'
    seals, by_path, expected = {}, defaultdict(dict), {}
    for day in DAYS:
        path = accepted / f'{day}.json'
        seals[str(path)] = R.P.file_sha(path)
        capsule = R.read(path)
        for cap in capsule['captures']:
            if cap['trace'] in expected or cap['line'] in by_path[cap['path']]:
                raise ValueError('duplicate_capture_location_or_trace')
            expected[cap['trace']] = cap
            by_path[cap['path']][cap['line']] = cap
            seals[cap['path']] = cap['physical_sha256']
    P.Q.verify_hashes(seals)
    originals = {r['trace']: r for r in projection['main']}
    if set(expected) != set(originals):
        raise ValueError('capture_projection_population_mismatch')
    rows = []
    for name, locations in sorted(by_path.items()):
        for line, raw in O.source_rows(Path(name)):
            cap = locations.get(line)
            if cap is not None:
                actual = O.capture_record(raw, path=Path(name), seal=seals[name], line=line)
                if actual != cap:
                    raise ValueError('capture_capsule_drift')
                old = originals[cap['trace']]
                payload = raw['source']['exact_payload']
                snap = payload['ai_market_snapshot_v1']
                now = R.epoch(cap['captured_at'])
                if (now != old['t'] or payload.get('stock_code') != '005930'
                        or snap.get('effective_venue') != 'KRX'
                        or snap.get('session_bucket') != 'krx_regular'):
                    raise ValueError('capture_scope_or_time_mismatch')
                sources = snap['sources']
                quote_source = sources.get('quote') or sources.get('orderbook') or {}
                # Preserve recorded integrated route as context, never relabel
                # _AL program/investor observations as KRX-only executions.
                suffix = {'krx_nxt_integrated': '_AL', 'nxt_only': '_NX', 'krx_only': ''}.get(snap.get('market_data_route'))
                if (quote_source.get('market_suffix') is not None
                        and quote_source['market_suffix'] != suffix):
                    raise ValueError('capture_quote_context_suffix_conflict')
                row = dict(day=old['day'], t=now, trace=old['trace'],
                    ep=old['features'].get('stream_epoch'),
                    stream_valid=old['features'].get('stream_valid') is True,
                    snapshot_t=optional_epoch(snap.get('captured_at')),
                    market_route=snap.get('market_data_route'), market_suffix=suffix,
                    program=sources.get('program'), investor=sources.get('investor'),
                    external_market=(payload.get('entry_candle_context') or {}).get('market_context'),
                    external_sector=(payload.get('entry_candle_context') or {}).get('sector_context'),
                    source_location=dict(path=name, line=line, physical_sha256=seals[name]))
                if not row['market_route'] or row['market_suffix'] is None:
                    raise ValueError('capture_context_route_missing')
                rows.append(row)
            if line >= max(locations):
                break
    if len(rows) != len(originals):
        raise ValueError('capture_source_location_missing')
    rows.sort(key=lambda r: (r['t'], r['trace']))
    if len({r['t'] for r in rows}) != len(rows):
        raise ValueError('ambiguous_capture_availability_clock')
    P.Q.verify_hashes(seals)
    return rows, seals


def flow_environment(captures, times, t, ep):
    result = {k: None for k in ('program_net', 'program_delta', 'foreign', 'institution', 'smart_money')}
    i = bisect_right(times, t) - 1
    if i < 0:
        return result
    cap = captures[i]
    if not cap['stream_valid'] or ep is None or cap['ep'] != ep:
        return result
    for role in ('program', 'investor'):
        src = cap[role]
        if source_status(src, cap, investor=role == 'investor') != 'valid':
            continue
        # Available only after capture, and expiry is measured from source.
        if t - R.epoch(src['observed_at']) > src['freshness_limit_ms'] / 1000:
            continue
        value = src['value']
        fields = (('program_net', 'net_qty'), ('program_delta', 'delta_qty')) if role == 'program' else (
            ('foreign', 'foreign_net'), ('institution', 'inst_net'), ('smart_money', 'smart_money_net'))
        for axis, key in fields:
            result[axis] = sign(value.get(key))
    return result


def stock_environment(ctx, frame):
    result = {}
    for window, threshold in ((300, .2), (900, .3)):
        x = frame['windows'].get(str(window))
        cutoff = frame['t'] - window
        j = bisect_right(ctx['dt'], cutoff) - 1
        valid = (x is not None and j >= 0 and cutoff - ctx['dt'][j] <= 1.5
                 and ctx['depth'][j]['valid'] and ctx['depth'][j]['ep'] == frame['ep']
                 and frame['quote_index'] <= P.quote_prefix_end(ctx, j))
        value = (frame['bid'] / ctx['depth'][j]['bid'] - 1) * 100 if valid else None
        result[f'stock_{window}'] = sign(value, threshold)
        result[f'return_{window}_pct'] = value
        result[f'vwap_{window}'] = ('above' if frame['bid'] >= x['vwap'] else 'below') if x else None
        if window == 900:
            result['past_range_900'] = ('cost_room' if (x['high'] / x['low'] - 1) * 100 >= .33
                                      else 'narrow') if x else None
    return result


def environments(ctx, frames, captures):
    times = [c['t'] for c in captures]
    return {f['index']: {**stock_environment(ctx, f),
                        **flow_environment(captures, times, f['t'], f['ep'])} for f in frames}


def capture_environments(rows, frames, ctx, captures):
    ft = [f['t'] for f in frames]
    times = [c['t'] for c in captures]
    result = {}
    for row in rows:
        i = bisect_right(ft, row['t']) - 1
        f = frames[i] if i >= 0 else None
        fresh = (f is not None and row['features'].get('stream_valid') is True
                 and row['t'] - f['t'] <= 1.5 and f['ep'] == row['features'].get('stream_epoch'))
        result[row['trace']] = {**(stock_environment(ctx, f) if fresh else {}),
            **flow_environment(captures, times, row['t'], row['features'].get('stream_epoch'))}
    return result


def capture_mask(rows, state_ids, selector, contexts, mode):
    if mode not in P.MODES:
        raise ValueError('unregistered_capture_mode')
    selected = set()
    for row in rows:
        match = matches(contexts[row['trace']], selector)
        parent = row['parent'] == 'ENTER_NOW'
        if match is None:
            admitted = parent
        elif mode == 'soft_add':
            admitted = parent or (match and row['trace'] in state_ids)
        else:
            admitted = match and row['trace'] in state_ids and (parent or mode == 'replace_soft')
        if admitted:
            selected.add(row['trace'])
    return selected


def parent_context_mask(rows, selector, contexts):
    """A condition-only veto of incumbent ENTER, with missing-context carry."""
    return {r['trace'] for r in rows if r['parent'] == 'ENTER_NOW'
            and matches(contexts[r['trace']], selector) is not False}


def aggregate(metrics):
    n = sum(m['known_terminal'] for m in metrics)
    wins = sum(m['positive'] for m in metrics)
    binary = sum(m['binary'] for m in metrics)
    targets = sum(m['target_first'] for m in metrics)
    attempts = sum(m['attempts'] for m in metrics)
    return dict(attempts=attempts, known_terminal=n, positive=wins,
        censored=attempts - n, win_rate=wins / n if n else None, wilson=P.E.wilson(wins, n),
        mean_net_cf=sum(m['mean_net_cf'] * m['known_terminal'] for m in metrics
                        if m['mean_net_cf'] is not None) / n if n else None,
        binary=binary, target_first=targets, conditional_target_first_win_rate=targets / binary if binary else None,
        unknown_win_bounds=[wins / attempts, (wins + attempts - n) / attempts] if attempts else None)


def select_price(candidates, baselines, train_days=TRAIN):
    """Held outcomes cannot affect selection, including tie breaking."""
    eligible = []
    for item in candidates:
        if item['selector'] == 'all':
            continue
        m = aggregate([item['days'][d] for d in train_days])
        base = aggregate([baselines[item['baseline']][d] for d in train_days])
        if (m['known_terminal'] >= 3 and all(item['days'][d]['known_terminal'] >= 1 for d in train_days)
                and base['win_rate'] is not None and m['win_rate'] > base['win_rate']
                and m['mean_net_cf'] > 0):
            eligible.append(dict(key=item['key'], train=m, baseline_train=base))
    eligible.sort(key=lambda x: (-x['train']['win_rate'], -x['train']['wilson'],
                                -x['train']['known_terminal'], x['key']))
    return dict(training_days=list(train_days), eligible_count=len(eligible),
                selected=eligible[0] if eligible else None, shortlist=eligible[:10])


def native_summary(rows, masks):
    old = {r['trace'] for r in rows if r['parent'] == 'ENTER_NOW'}
    train = [r for r in rows if r['day'] in TRAIN]
    held = [r for r in rows if r['day'] == DAYS[2]]
    base = O.group_metric(train, old)
    ranked = []
    all_metrics = []
    for key, ids in sorted(masks.items()):
        metric = O.group_metric(train, ids)
        all_metrics.append(dict(key=key, train=metric))
        if (metric['selected_opportunity_count'] >= 3 and base['selected_opportunity_count'] >= 3
                and metric['win_rate_pct'] > base['win_rate_pct']):
            ranked.append(dict(key=key, train=metric))
    ranked.sort(key=lambda x: (-x['train']['win_rate_pct'], -x['train']['support_adjusted_win_rate_pct'], x['key']))
    selected = ranked[0] if ranked else None
    if selected:
        ids = masks[selected['key']]
        selected['held'] = O.group_metric(held, ids)
        selected['paired'] = P.paired_native(held, old, ids)
    return dict(baseline=dict(train=base, held=O.group_metric(held, old)), selected=selected,
                eligible_count=len(ranked), candidates=all_metrics,
                formal_feasibility=P.promotion_feasibility(rows), official_policy_candidate=None,
                success_preservation_veto=False)


def run(root, output):
    regular, _, projection, seals, binding = P.load_sources(root)
    captures, cap_seals = intake(root, projection)
    seals.update(cap_seals)
    breadth, breadth_seals, breadth_excluded = breadth_intake(root)
    seals.update(breadth_seals)
    for path in (Path(__file__).resolve(), Path(O.__file__).resolve(), root / 'src/tests/test_samsung_environment_conditioned_research.py',
                 root / 'docs/proposals/samsung-environment-conditioned-pattern-research-plan-2026-10-04.md'):
        seals[str(path)] = R.P.file_sha(path)
    registry, definitions = selectors(), P.definitions()
    census, flows, masks, candidates, baselines, cells = {}, {}, {}, {}, {}, {}
    replay_data = {}
    for day in DAYS:
        prepared = R.read(Path(regular['files'][day]['path']))
        frames = prepared['frames']
        ctx = C.campaign_context(P.E.read_cache(Path(prepared['cache']['path'])))
        cap = [r for r in captures if r['day'] == day]
        main = [r for r in projection['main'] if r['day'] == day]
        env = environments(ctx, frames, cap)
        cenv = capture_environments(main, frames, ctx, cap)
        for f in frames:
            env[f['index']]['prior_published_breadth'] = published_breadth(breadth, f['t'])['state']
        for row in main:
            cenv[row['trace']]['prior_published_breadth'] = published_breadth(breadth, row['t'])['state']
        census[day] = dict(frames=len(frames), captures=len(cap),
            capture_source_status={role: dict(Counter(source_status(r[role], r, investor=role == 'investor') for r in cap))
                                   for role in ('program', 'investor')},
            frame_states={axis: dict(Counter(str(e.get(axis)) for e in env.values()))
                          for axis in ('stock_300', 'stock_900', 'vwap_300', 'vwap_900', 'past_range_900',
                                       'program_net', 'program_delta', 'foreign', 'institution', 'smart_money', 'prior_published_breadth')},
            external_market_capture_count=sum(isinstance(r['external_market'], dict) for r in cap),
            external_sector_capture_count=sum(isinstance(r['external_sector'], dict) for r in cap),
            prior_published_breadth=published_breadth(breadth, main[0]['t']))
        flows[day] = {axis: dict(Counter(str(e.get(axis)) for e in cenv.values()))
                     for axis in ('program_net', 'program_delta', 'foreign', 'institution', 'smart_money')}
        cells[day] = []
        for selector in registry:
            matched = [r for r in main if matches(cenv[r['trace']], selector) is True]
            cells[day].append(dict(selector=selector['id'], captures=len(matched),
                unknown=sum(matches(cenv[r['trace']], selector) is None for r in main),
                original_binary=P.binary_metric(matched), parent_actions=dict(Counter(r['parent'] for r in matched)),
                guard_blocked=sum(bool(r['guard']['blockers']) for r in matched),
                native=O.group_metric(matched, {r['trace'] for r in matched})))
            masks.setdefault('parent_only|' + selector['id'] + '|veto', set()).update(
                parent_context_mask(main, selector, cenv))
        for definition in definitions:
            signals = P.state_signals(ctx, frames, definition)
            state_ids = {mode: P.captured_mask(main, frames, ctx, signals, mode)[0] for mode in P.MODES}
            label_cache = {}
            def label(f, model):
                key = (f['index'], model)
                if key not in label_cache:
                    label_cache[key] = P.exit_label(ctx, f, model, .23)
                return label_cache[key]
            for selector in registry:
                chosen = [f for f in signals if matches(env[f['index']], selector) is True]
                for model in EXITS:
                    key = definition['id'] + '|' + selector['id'] + '|' + model
                    base_key = definition['id'] + '|' + model
                    result = P.replay(chosen, lambda f: label(f, model), cooldown=60)
                    row = candidates.setdefault(key, dict(key=key, definition=definition['id'],
                        selector=selector['id'], exit=model, baseline=base_key, days={}))
                    row['days'][day] = result['metric']
                    row.setdefault('signal_census', {})[day] = dict(total=len(signals), qualified=len(chosen),
                        unknown=sum(matches(env[f['index']], selector) is None for f in signals),
                        blocked_after_admission=result['blocked_signals'])
                    if selector['id'] == 'all':
                        baselines.setdefault(base_key, {})[day] = result['metric']
                    replay_data[(day, key)] = (chosen, ctx)
                for mode in P.MODES:
                    key = definition['id'] + '|' + selector['id'] + '|' + mode
                    masks.setdefault(key, set()).update(capture_mask(main, state_ids[mode], selector, cenv, mode))
    candidate_list = list(candidates.values())
    choice = select_price(candidate_list, baselines)
    sensitivity = []
    if choice['selected']:
        key = choice['selected']['key']
        candidate = candidates[key]
        for cost, latency in ((.23, 0.), (.33, 0.), (.23, 1.)):
            results = {}
            for day in DAYS:
                signals, ctx = replay_data[(day, key)]
                results[day] = P.replay(signals, lambda f: P.exit_label(ctx, f, candidate['exit'], cost, latency), cooldown=60)
            sensitivity.append(dict(cost_pct=cost, latency_sec=latency, days=results))
        choice['held'] = candidate['days'][DAYS[2]]
        choice['held_baseline'] = baselines[candidate['baseline']][DAYS[2]]
        choice['pooled_audit_only'] = aggregate(list(candidate['days'].values()))
        choice['pooled_baseline_audit_only'] = aggregate(list(baselines[candidate['baseline']].values()))
        choice['held_validation'] = ('direction_confirmed_thin_support' if
            choice['held']['win_rate'] is not None and choice['held_baseline']['win_rate'] is not None
            and choice['held']['win_rate'] > choice['held_baseline']['win_rate']
            and choice['held']['mean_net_cf'] > 0 else 'not_confirmed')
        choice['same_signal_replay_decomposition'] = {}
        for day in DAYS:
            signals, ctx = replay_data[(day, key)]
            all_key = candidate['definition'] + '|all|' + candidate['exit']
            baseline_signals, _ = replay_data[(day, all_key)]
            baseline_run = P.replay(baseline_signals, lambda f: P.exit_label(ctx, f, candidate['exit'], .23), cooldown=60)
            chosen_run = sensitivity[0]['days'][day]
            old = {r['signal_index']: r for r in baseline_run['outcomes']}
            new = {r['signal_index']: r for r in chosen_run['outcomes']}
            choice['same_signal_replay_decomposition'][day] = dict(
                baseline_outcomes=baseline_run['outcomes'], candidate_outcomes=chosen_run['outcomes'],
                retained_signal_count=len(old.keys() & new.keys()), removed_signal_count=len(old.keys() - new.keys()),
                added_signal_count=len(new.keys() - old.keys()),
                removed_known_positive=sum(r['complete'] and r['net'] > 0 for i, r in old.items() if i not in new),
                added_known_positive=sum(r['complete'] and r['net'] > 0 for i, r in new.items() if i not in old))
    preserved = regular['preserved']
    P.Q.verify_hashes(preserved)
    P.Q.verify_hashes(seals)
    write(output / 'source-census.json', dict(census=census, capture_flow_states=flows, captures=captures,
        prior_breadth_reports=breadth, excluded_optional_breadth_sources=breadth_excluded,
        capture_conditional_cells=cells,
        external_market_status=('source_unavailable_in_exact_captures' if not any(
            c['external_market_capture_count'] for c in census.values()) else 'unreviewed_source_present_not_consumed'),
        external_sector_status=('source_unavailable_in_exact_captures' if not any(
            c['external_sector_capture_count'] for c in census.values()) else 'unreviewed_source_present_not_consumed'),
        external_intraday_market_sector_hypotheses_executed=False,
        prior_published_pool_breadth_hypotheses_executed=True, source_seals=seals,
        stock_trend_role='own_stock_not_market_regime', integrated_flow_role='recorded_capture_context_not_krx_only'))
    write(output / 'result.json', dict(binding=binding, registry=registry,
        signal_definitions=definitions, exits=list(EXITS), price_candidate_count=len(candidate_list),
        price_candidates=candidate_list, price_selection=choice, price_sensitivity=sensitivity,
        main_native=native_summary(projection['main'], masks),
        main_trace_candidates=[dict(key=key, train=P.binary_metric([r for r in projection['main'] if r['day'] in TRAIN and r['trace'] in ids]),
                                    held=P.binary_metric([r for r in projection['main'] if r['day'] == DAYS[2] and r['trace'] in ids]))
                               for key, ids in sorted(masks.items())],
        preserved_policy_files=preserved, source_seals=seals,
        official_policy_candidate=None, executed_hypothesis_scope='own_stock_direction_program_investor_conditioning',
        all_hypotheses_exhausted=False))
    return dict(output=str(output), conditions=len(registry), price_candidates=len(candidate_list),
                selected=choice['selected']['key'] if choice['selected'] else None,
                preserved_policy_files=len(preserved), official_policy_candidate=None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run(args.root.resolve(), args.output.resolve()), allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
