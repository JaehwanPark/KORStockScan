"""First observed entry events and conditional current-exit price scenarios.

No live state, orders or policy publication. OHLC paths do not reconstruct the
mechanical width classifier, executable bid or complete holding state machine.
"""
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta
from statistics import mean
import math

from src.engine.scalping.entry_observation_recipe_policy import cluster
from src.engine.scalping.trailing_exit_decision import evaluate_trailing_take_profit
from src.engine.trade_profit import calculate_net_profit_rate

KST = timezone(timedelta(hours=9))
AUTHORITY = dict(runtime_effect=False, allowed_runtime_apply=False,
    actual_order_submitted=False, broker_order_forbidden=True,
    decision_authority='offline_first_signal_and_conditional_exit_research',
    metric_role='sim_probe_ev', primary_decision_metric='paired_cost_bound_price_cf',
    window_policy='frozen_first_observed_signal_60m_same_session',
    sample_floor='all_fixed_anchors_with_explicit_missing_denominators',
    source_quality_gate='source_hash_exact_scope_clock_cost_and_unambiguous_bar_order',
    forbidden_uses=['realized_pnl','runtime_apply','native_identity_synthesis',
                    'full_holding_replay_claim','independent_holdout_claim'])


def epoch(row):
    stamp = datetime.fromisoformat(row['ts'])
    if stamp.utcoffset() is None or stamp.astimezone(KST).date().isoformat() != row['day']:
        raise ValueError('first_signal_clock_invalid')
    return stamp.timestamp()


def event_key(row):
    if row.get('group') != 'non_samsung' or row.get('symbol') == '005930':
        raise ValueError('non_samsung_scope_required')
    return cluster(row) + (row['outcome_request_code'], row['source_bundle_sha256'])


def first_signal_events(rows):
    return observed_action_runs(rows, key_function=event_key)


def observed_action_runs(rows, *, key_function):
    """Union-action observed runs; no labels, artificial time bins or native IDs."""
    groups = defaultdict(list)
    seen = set()
    for row in rows:
        if row['trace'] in seen:
            raise ValueError('first_signal_duplicate_trace')
        seen.add(row['trace'])
        epoch(row)
        key_function(row)
        groups[cluster(row)].append(row)
    events = []
    for _, series in sorted(groups.items()):
        active, previous, prior_key = None, None, None
        for row in sorted(series, key=lambda r: (r['ts'], r['trace'])):
            key = key_function(row)
            if prior_key is not None and key != prior_key:
                if active is not None:
                    active['closed_by_trace'] = row['trace']
                    active['closed_at'] = row['ts']
                active, previous = None, None
            prior_key = key
            enters = [a for a in ('parent_action', 'candidate_action') if row[a] == 'ENTER_NOW']
            if not enters:
                if active is not None:
                    active['closed_by_trace'] = row['trace']
                    active['closed_at'] = row['ts']
                    active = None
                previous = row
                continue
            if active is None:
                active = dict(event_id='observed-run:' + row['trace'], key=list(key),
                    first_observed_at=row['ts'], left_censored=previous is None,
                    preceding_trace=previous['trace'] if previous else None,
                    preceding_gap_sec=epoch(row)-epoch(previous) if previous else None,
                    closed_by_trace=None, closed_at=None, observations=[], first_by_arm={},
                    max_internal_observation_gap_sec=0.)
                events.append(active)
            elif previous:
                active['max_internal_observation_gap_sec'] = max(
                    active['max_internal_observation_gap_sec'], epoch(row)-epoch(previous))
            active['observations'].append(row['trace'])
            for arm in enters:
                active['first_by_arm'].setdefault(arm, row['trace'])
            previous = row
    return sorted(events, key=lambda r: (r['first_observed_at'], r['event_id']))


def mask_first_signals(rows, events):
    chosen = {a: {e['first_by_arm'][a] for e in events if a in e['first_by_arm']}
              for a in ('parent_action', 'candidate_action')}
    return [{**r, **{a: r[a] if r['trace'] in chosen[a] else 'RECHECK' for a in chosen}} for r in rows]


def _number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) else None


def _at_price(price, peak, armed, entry, policy, strong, *, update_peak=True):
    if update_peak:
        peak = max(peak, price)
    net = calculate_net_profit_rate(entry, price, cost_rate=policy['runtime_cost_rate'])
    peak_net = calculate_net_profit_rate(entry, peak, cost_rate=policy['runtime_cost_rate'])
    decision = evaluate_trailing_take_profit(peak_price=peak, executable_bid=price,
        peak_profit_pct=peak_net, start_pct=policy['start_pct'], strong=strong,
        weak_limit_pct=policy['weak_pct'], strong_limit_pct=policy['strong_pct'],
        already_armed=armed)
    rule = ('emergency_stop' if net <= policy['emergency_stop_net_pct']
        else 'hard_stop' if net <= policy['hard_stop_net_pct']
        else 'trailing' if decision.triggered else None)
    return peak, decision.armed, rule


def _bar_order(points, state, entry, policy, strong):
    """Continuous segments between OHLC nodes are explicit scenario assumptions."""
    peak, armed = state
    last = None
    for price in points:
        prior_peak, prior_armed = peak, armed
        peak, armed, rule = _at_price(price, peak, armed, entry, policy, strong)
        if rule:
            exit_price = price
            if last is not None and price < last:
                # Locate the first current-kernel crossing, preserving runtime
                # fee rounding. The opening node is never backfilled at a stop.
                lo, hi = price, last
                for _ in range(40):
                    mid = (lo+hi)/2
                    if _at_price(mid, prior_peak, prior_armed, entry, policy, strong)[2]:
                        lo = mid
                    else:
                        hi = mid
                exit_price = lo
                rule = _at_price(exit_price, prior_peak, prior_armed, entry, policy, strong)[2]
            return dict(rule=rule, price=exit_price), (peak, armed)
        last = price
    return None, (peak, armed)


def validate_exit_policy(policy):
    required = {'start_pct','weak_pct','strong_pct','hard_stop_net_pct',
                'emergency_stop_net_pct','runtime_cost_rate'}
    if (set(policy) != required or any(_number(policy[k]) is None for k in required)
            or not 0 < policy['start_pct'] < 100
            or not 0 < policy['weak_pct'] <= policy['strong_pct'] < 100
            or not -100 < policy['emergency_stop_net_pct'] < policy['hard_stop_net_pct'] < 0
            or not 0 <= policy['runtime_cost_rate'] < 1):
        raise ValueError('first_signal_exit_policy_invalid')


def bar_exit_scenario(row, bars, *, policy, strong):
    """Two OHLC orders must agree; returns null on ambiguity/gaps, not zero PnL."""
    validate_exit_policy(policy)
    start = epoch(row)
    entry = _number(row.get('reference_price'))
    cost = _number((row.get('features') or {}).get('entry_cost_pct'))
    missing = lambda why: dict(status=why, net_pct=None, exit_at=None,
        rule=None, completed_operating_exit=False)
    if cost is None or cost < 0:
        return missing('cost_missing')
    if (entry is None or entry <= 0 or row.get('capture_valid') is not True
            or row.get('reference_type') != 'executable_ask'):
        return missing('entry_reference_missing')
    close = datetime.fromisoformat(row['ts']).astimezone(KST).replace(
        hour=15,minute=30,second=0,microsecond=0).timestamp()
    limit = min(start+3600, close)
    selected = [b for b in bars if start < b['t'] <= limit]
    state, previous = (entry, False), start
    last_price = None
    for i, bar in enumerate(selected):
        if (any(_number(bar.get(k)) is None for k in ('t','open','high','low','close'))
                or not 0 < bar['low'] <= min(bar['open'],bar['close'])
                or max(bar['open'],bar['close']) > bar['high']):
            return missing('bar_invalid')
        if not 0 < bar['t']-previous <= 90:
            return missing('price_gap')
        if i == 0 and bar['t']-start < 60:
            high_arm = _at_price(bar['high'], entry, False, entry, policy, strong)[1]
            low_stop = _at_price(bar['low'], entry, False, entry, policy, strong)[2]
            if high_arm or low_stop:
                return missing('first_partial_bar_ambiguous')
            # Any unseen pre-entry high is below the arm: a later armed peak
            # must dominate it, so it cannot decide a later trailing exit.
            state = (max(entry,bar['high']), False)
        else:
            orders = ([bar['open'],bar['high'],bar['low'],bar['close']],
                      [bar['open'],bar['low'],bar['high'],bar['close']])
            a, sa = _bar_order(orders[0],state,entry,policy,strong)
            b, sb = _bar_order(orders[1],state,entry,policy,strong)
            if bool(a) != bool(b) or (a and (a['rule'] != b['rule'] or abs(a['price']-b['price'])>1e-7)):
                return missing('intrabar_exit_order_ambiguous')
            if a:
                return dict(status='conditional_bar_exit', net_pct=(a['price']/entry-1)*100-cost,
                    runtime_net_pct=calculate_net_profit_rate(entry,a['price'],cost_rate=policy['runtime_cost_rate']),
                    exit_at=bar['t'], exit_price=a['price'], rule=a['rule'],
                    completed_operating_exit=False, classifier_state_assumed='STRONG' if strong else 'WEAK',
                    bid_equals_trade_price_assumed=True, intrabar_continuity_assumed=True)
            assert sa == sb
            state = sa
        last_price, previous = bar['close'], bar['t']
    if not selected or limit-previous > 90:
        return missing('insufficient_followup')
    return dict(status='session_censored' if start+3600>close else 'horizon_censored',
        net_pct=None, exit_at=None, rule=None, completed_operating_exit=False,
        mark_to_close_cf_pct=(last_price/entry-1)*100-cost,
        armed=state[1], classifier_state_assumed='STRONG' if strong else 'WEAK')


def summarize_paths(rows, paths):
    valid = [(r, paths[r['trace']]) for r in rows if paths[r['trace']].get('net_pct') is not None]
    groups = defaultdict(list)
    for row, path in valid:
        groups[cluster(row)].append(path['net_pct'])
    return dict(n=len(rows), evaluable=len(valid), cluster_count=len(groups),
        status_counts=dict(Counter(paths[r['trace']]['status'] for r in rows)),
        exit_rule_counts=dict(Counter(p.get('rule') for _,p in valid)),
        mean_price_cf_pct=mean(p['net_pct'] for _,p in valid) if valid else None,
        equal_cluster_mean_price_cf_pct=mean(mean(v) for v in groups.values()) if groups else None,
        positive_exit_rate_pct=100*mean(p['net_pct']>0 for _,p in valid) if valid else None,
        mark_censored_count=sum(paths[r['trace']].get('mark_to_close_cf_pct') is not None for r in rows))


def archive_exit_scenario(row, points, *, policy, strong):
    """Canonical archive events, with actual trade peak and fresh executable bid.

    Caller validates canonical row authority, physical scope and exclusions.
    The collector epoch stays separate from Main; width/default SCALP context
    remain assumptions. No protocol fields are interpreted here.
    """
    validate_exit_policy(policy)
    start = epoch(row)
    entry = _number(row.get('reference_price'))
    cost = _number((row.get('features') or {}).get('entry_cost_pct'))
    missing = lambda why: dict(status=why, net_pct=None, exit_at=None, rule=None,
        completed_operating_exit=False, actual_classifier_replayed=False)
    if cost is None or cost < 0:
        return missing('cost_missing')
    if (entry is None or entry <= 0 or row.get('capture_valid') is not True
            or row.get('reference_type') != 'executable_ask'):
        return missing('entry_reference_missing')
    close = datetime.fromisoformat(row['ts']).astimezone(KST).replace(
        hour=15,minute=30,second=0,microsecond=0).timestamp()
    limit = min(start+3600,close)
    expected_item = row['request_code']
    last, peak, armed, latest_trade, previous_at = {}, entry, False, None, None
    previous_kind = None
    kinds_at_time = defaultdict(set)
    for point in points:
        at = _number(point.get('t'))
        if at is not None:
            kinds_at_time[at].add(point.get('kind'))
    used = 0
    last_valid_bid = None
    for point in points:
        at = _number(point.get('t'))
        if at is None:
            return missing('archive_clock_invalid')
        if at > limit:
            break
        if point.get('item') != expected_item:
            return missing('archive_item_mismatch')
        kind, sequence, transport = point.get('kind'), point.get('sequence'), point.get('epoch')
        if (kind not in {'trade','depth'} or type(sequence) is not int or sequence <= 0
                or type(transport) is not int or transport <= 0):
            return missing('archive_sequence_invalid')
        if at <= start:
            last[kind] = point
            continue
        if set(last) != {'trade','depth'}:
            return missing('archive_prefix_missing')
        # Check the whole timestamp group before an early exit can return.
        if len(kinds_at_time[at]) > 1:
            return missing('archive_clock_or_tie_ambiguous')
        # Canonical timestamps have millisecond precision. Same-series order
        # is still proved by the contiguous sequence checked below.
        if previous_at is not None and (at < previous_at or (at == previous_at and kind != previous_kind)):
            return missing('archive_clock_or_tie_ambiguous')
        previous_at, previous_kind = at, kind
        prior = last[kind]
        if transport != prior['epoch']:
            return missing('archive_epoch_changed')
        if sequence != prior['sequence']+1:
            return missing('archive_sequence_gap')
        last[kind] = point
        if point.get('source_valid') is not True:
            return missing('archive_source_invalid')
        if kind == 'trade':
            price = _number(point.get('trade_price'))
            if price is None or price <= 0:
                return missing('archive_trade_invalid')
            latest_trade = (at,price)
        bid, ask, age = (_number(point.get(k)) for k in ('bid','ask','quote_age_ms'))
        if (bid is None or ask is None or bid <= 0 or ask < bid
                or age is None or not 0 <= age <= 700):
            # Mirrors quote freshness: stale quotes cannot execute an exit.
            continue
        if latest_trade and 0 <= at-latest_trade[0] <= .7:
            peak = max(peak,latest_trade[1])
        peak, armed, rule = _at_price(bid,peak,armed,entry,policy,strong,update_peak=False)
        used += 1
        last_valid_bid = (at,bid)
        if rule:
            return dict(status='conditional_archive_exit',net_pct=(bid/entry-1)*100-cost,
                runtime_net_pct=calculate_net_profit_rate(entry,bid,cost_rate=policy['runtime_cost_rate']),
                exit_at=at,exit_price=bid,rule=rule,peak_trade_price=peak,eligible_quote_updates=used,
                completed_operating_exit=False,actual_classifier_replayed=False,
                classifier_state_assumed='STRONG' if strong else 'WEAK',
                archive_item=expected_item,main_transport_epoch_binding_verified=False,
                actual_fill=False)
    if not last_valid_bid or limit-last_valid_bid[0] > .7:
        return missing('archive_endpoint_unobserved')
    return dict(status='archive_horizon_censored',net_pct=None,exit_at=None,rule=None,
        completed_operating_exit=False,actual_classifier_replayed=False,
        mark_to_close_cf_pct=(last_valid_bid[1]/entry-1)*100-cost,
        classifier_state_assumed='STRONG' if strong else 'WEAK')
