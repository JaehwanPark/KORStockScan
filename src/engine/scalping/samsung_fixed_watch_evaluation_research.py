"""Offline fixed-watch contract and owner comparison. No live consumer."""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from datetime import datetime
import json
from pathlib import Path
from statistics import mean
from zoneinfo import ZoneInfo

from src.engine.scalping import samsung_environment_conditioned_research as N
from src.engine.scalping import samsung_program_sequence_research as S
from src.trading.order.tick_utils import move_price_up_by_bps

P, O, R, C, Q = N.P, N.O, N.R, N.C, N.P.Q
KST = ZoneInfo('Asia/Seoul')
KEYS = ('parent_only|foreign=up|veto', 'parent_only|past_gap_180|program_change=down')
AUTHORITY = {**N.AUTHORITY, 'consumer_scope': 'offline_samsung_fixed_watch_evaluation',
    'primary_decision_metric': 'separate_original_native_and_clustered_price_episode_win_rates',
    'episode_support_registered': False, 'live_selector_registered': False,
    'trailing_role': 'no_new_trailing_sweep_no_full_live_exit_claim'}


def write(path, value):
    body = {**{k: v for k, v in value.items() if k != 'content_sha256'}, **AUTHORITY}
    body['content_sha256'] = R.digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, allow_nan=False) + '\n')


def fixed_watch(row):
    native = row.get('native')
    return (isinstance(native, list) and len(native) == 7
        and native[:5] == [row['day'], '005930', 'KRX', 'KRX_REGULAR', 'MAIN_FIXED_WATCH']
        and all(isinstance(v, str) and v for v in native[5:]))


def net_pct(entry, exit_price, cost_rate):
    if (not all(R.finite(v) for v in (entry, exit_price, cost_rate))
            or min(entry, exit_price) <= 0 or not 0 <= cost_rate < 1):
        raise ValueError('invalid_exact_cost_input')
    return (exit_price * (1 - cost_rate) / entry - 1) * 100


def frozen_spec(environment, sequence):
    selected = [environment['main_native']['selected'], sequence['main_native']['selected']]
    if [r['key'] for r in selected] != list(KEYS) or environment['binding']['parent_sha256'] == '':
        raise ValueError('prior_selected_candidate_drift')
    return dict(schema='samsung_frozen_candidate_contract_v1',
        parent_sha256=environment['binding']['parent_sha256'],
        discovery_days=list(N.DAYS), training_days=list(N.TRAIN),
        later_source_after_date='2026-10-04', original_candidate_scope='all_samsung_main_origins',
        dedicated_transfer_scope='005930/KRX/KRX_REGULAR/MAIN_FIXED_WATCH',
        candidates=[dict(key=KEYS[0], conditions={'foreign': 'up'}, historical_gap=None),
                    dict(key=KEYS[1], conditions={'program_change': 'down'}, historical_gap=180)],
        mode='parent_enter_veto_only_unknown_carries_parent', reselection_allowed=False,
        winner_retention_veto=False, episode_native_promotion=False,
        training_metrics=[r['train'] for r in selected])


def validate_frozen(frozen, root=None):
    if (frozen.get('schema') != 'samsung_frozen_candidate_contract_v1'
            or frozen.get('later_source_after_date') != '2026-10-04'
            or frozen.get('reselection_allowed') is not False
            or R.S.digest(frozen['parent_policy']) != frozen['parent_sha256']
            or (str(Path(__file__).resolve()) not in frozen.get('replay_dependency_seals', {})
                and (root is None or str(Path(root)/'src/engine/scalping/samsung_fixed_watch_evaluation_research.py') not in frozen.get('replay_dependency_seals', {})))):
        raise ValueError('invalid_frozen_contract_or_missing_kernel_binding')
    try:
        Q.verify_hashes(frozen['replay_dependency_seals'])
    except (ValueError, OSError):
        if root is None:
            raise
        from src.engine.scalping.samsung_policy_compatibility import validate,current_kernels
        validate(root,frozen,current_kernels(frozen,root))


def candidate_masks(rows, captures, frozen):
    """Fixed filters only; outcomes are never used to produce a mask."""
    if [(r['key'], r['conditions'], r['historical_gap']) for r in frozen['candidates']] != [
        (KEYS[0], {'foreign': 'up'}, None), (KEYS[1], {'program_change': 'down'}, 180)]:
        raise ValueError('unregistered_frozen_candidate')
    if [c['t'] for c in captures] != sorted({c['t'] for c in captures}):
        raise ValueError('ambiguous_or_unsorted_capture_clock')
    caps = {d: [c for c in captures if c['day'] == d] for d in {r['day'] for r in rows}}
    masks = {key: set() for key in KEYS}
    for day, group in caps.items():
        times = [c['t'] for c in group]
        sequence = S.sequence_rows(group, 180)
        contexts = {}
        for r in (r for r in rows if r['day'] == day):
            epoch = r['features'].get('stream_epoch') if r['features'].get('stream_valid') is True else None
            contexts[r['trace']] = [N.flow_environment(group, times, r['t'], epoch),
                                   S.asof(sequence, times, r['t'], epoch)]
        for i, definition in enumerate(frozen['candidates']):
            for row in (r for r in rows if r['day'] == day and r['parent'] == 'ENTER_NOW'):
                result = N.matches(contexts[row['trace']][i], definition)
                if result is not False:
                    masks[definition['key']].add(row['trace'])
    return masks


def native_comparison(rows, masks):
    parent = {r['trace'] for r in rows if r['parent'] == 'ENTER_NOW'}
    result = {}
    for scope, population in [('all_origins', rows), ('fixed_watch', [r for r in rows if fixed_watch(r)])]:
        days = sorted({r['day'] for r in population})
        result[scope] = dict(observations=len(population),
            original_native_clusters=len({tuple(r['native']) for r in population if r['native'] is not None}),
            by_day={day: dict(baseline=O.group_metric([r for r in population if r['day'] == day], parent),
                candidates={key: O.group_metric([r for r in population if r['day'] == day], ids)
                            for key, ids in masks.items()}) for day in days},
            train=dict(baseline=O.group_metric([r for r in population if r['day'] in N.TRAIN], parent),
                candidates={key: O.group_metric([r for r in population if r['day'] in N.TRAIN], ids)
                            for key, ids in masks.items()}))
    return result


def fold_contract(rows, train_days, validation_days):
    if set(train_days) & set(validation_days):
        raise ValueError('same_date_in_training_and_validation')
    membership = {}
    for row in rows:
        if not fixed_watch(row):
            continue
        fold = 'train' if row['day'] in train_days else 'validation' if row['day'] in validation_days else None
        if fold is None:
            continue
        # The same original admission cannot become two independent folds even
        # if a producer accidentally republishes it with a different date.
        identity = tuple(row['native'][1:])
        if identity in membership and membership[identity] != fold:
            raise ValueError('same_watch_admission_crosses_folds')
        membership[identity] = fold
    return dict(training_days=list(train_days), validation_days=list(validation_days),
        same_admission_crosses_folds=False, validation_role='previously_explored_diagnostic_not_pristine',
        promotion_contract_role='proposal_not_registered',
        proposed_support_unit='nonoverlap_episode_with_original_watch_and_date_cluster',
        proposed_support_reporting=['known_episode_count', 'censored_episode_count', 'watch_cluster_count', 'date_count'],
        proposed_comparison='fixed_candidate_and_same_scope_parent_on_whole_later_date_clusters',
        proposed_selection='higher_native_win_rate_and_support_adjusted_comparison_no_winner_retention_veto',
        proposed_live_acceptance='registered_source_cost_guard_episode_contract_and_rolling_cumulative_version_evidence',
        episode_count_replaces_generic_native_floor=False)


def bind_research_signals(signals, rows):
    """Original watch availability, not a synthetic independent admission."""
    observed = sorted(rows, key=lambda r: (r['t'], r['trace']))
    times = [r['t'] for r in observed]
    result, excluded = [], Counter()
    for signal in signals:
        i = bisect_right(times, signal['t']) - 1
        row = observed[i] if i >= 0 else None
        if row is None or not fixed_watch(row):
            excluded['watch_not_yet_observed_or_other_origin'] += 1
            continue
        if (row['features'].get('stream_valid') is not True
                or row['features'].get('stream_epoch') != signal['ep']):
            excluded['watch_epoch_unproven'] += 1
            continue
        result.append(dict(signal, native_identity=row['native'], watch_trace=row['trace']))
    return result, dict(excluded)


def clustered_episode_metric(outcomes):
    metric = P.terminal_metric(outcomes)
    by_day = {}
    for row in outcomes:
        day = row['native_identity'][0]
        by_day.setdefault(day, []).append(row)
    daily = {day: P.terminal_metric(rows) for day, rows in sorted(by_day.items())}
    rates = [r['win_rate'] for r in daily.values() if r['win_rate'] is not None]
    return dict(metric, original_watch_clusters=len({tuple(r['native_identity']) for r in outcomes}),
        source_dates=sorted(by_day), per_day=daily,
        equal_date_mean_win_rate=mean(rates) if rates else None,
        independent_native_support_added=0, actual_custody_verified=False)


def episode_replay(ctx, signals, rows, cost):
    bound, excluded = bind_research_signals(signals, rows)
    by_clock = {(r['t'], r['index']): r for r in bound}
    if len(by_clock) != len(bound):
        raise ValueError('duplicate_research_signal')
    replay = P.replay(bound, lambda f: P.exit_label(ctx, f, 'barrier', cost), cooldown=60)
    outcomes = []
    for out in replay['outcomes']:
        signal = by_clock[out['signal_t'], out['signal_index']]
        out = dict(out, native_identity=signal['native_identity'], watch_trace=signal['watch_trace'],
            research_episode_id=R.digest([signal['native_identity'], signal['t'], signal['index']]),
            actual_custody_verified=False)
        outcomes.append(out)
    return dict(outcomes=outcomes, metric=clustered_episode_metric(outcomes),
        excluded_signals=excluded, emitted_signals=len(signals), bound_signals=len(bound),
        blocked_signals=replay['blocked_signals'], cooldown=60,
        watch_binding_role='first_observed_identity_same_epoch_not_execution_admission')


def widget_target_label(ctx, signal, bps, cost_rate, horizon=1200):
    """Price reaching native target is a CF; no queue/fill/forced time exit."""
    if bps not in (40, 80) or not 0 <= cost_rate < 1 or horizon != 1200:
        raise ValueError('unregistered_widget_target_model')
    entry = Q.entry_for(ctx, signal)
    if entry is None or not C.actionable(ctx['depth'][entry['quote_index']]):
        return dict(complete=False, binary=None, net=None, status='nonactionable_entry')
    target = move_price_up_by_bps(entry['price'], bps)
    end = min(P.quote_prefix_end(ctx, entry['quote_index']), len(ctx['depth']) - 1)
    cutoff = min(entry['t'] + horizon, ctx['depth'][end]['t'], ctx['rows'][ctx['trade_ends'][entry['index']]]['t'])
    left = bisect_right(ctx['actionable_times'], entry['t'])
    right = bisect_right(ctx['actionable_times'], cutoff)
    hit = ctx['tree'].first(left, right, target, -C.math.inf)
    common = dict(entry=entry, horizon=horizon, target_price=target, target_bps=bps,
        cost_rate=cost_rate, independent_price_formula=True, actual_fill_claimed=False)
    if hit is not None:
        quote = ctx['depth'][ctx['actionable'][hit]]
        return dict(common, complete=True, binary=1, net=net_pct(entry['price'], target, cost_rate),
            exit_t=quote['t'], modeled_exit_price=target, observed_exit_bid=quote['bid'],
            exit_price_assumption='resting_limit_target_no_better_price_assumed_no_fill_claim',
            status='observed_bid_target_reached')
    return dict(common, complete=False, binary=None, net=None,
        status='target_not_observed_no_forced_terminal', observed_until=cutoff)


def captured_signal(ctx, row):
    i = bisect_right(ctx['times'], row['t']) - 1
    if (i < 0 or row['t'] - ctx['times'][i] > 1.5 or row['features'].get('stream_valid') is not True
            or ctx['rows'][i]['ep'] != row['features'].get('stream_epoch')):
        return None
    return dict(index=i, t=row['t'], captured_trace=row['trace'])


def same_entry_panel(ctx, rows, bps, cost_rate):
    results = []
    for row in rows:
        if row['parent'] != 'ENTER_NOW' or not fixed_watch(row):
            continue
        signal = captured_signal(ctx, row)
        if signal is None:
            results.append(dict(trace=row['trace'], status='captured_entry_source_missing'))
            continue
        main = P.exit_label(ctx, signal, 'barrier', cost_rate * 100)
        if main['complete']:
            net = net_pct(main['entry']['price'], main['exit_bid'], cost_rate)
            main = dict(main, net=net, terminal_win=int(net > 0))
        widget = widget_target_label(ctx, signal, bps, cost_rate)
        results.append(dict(trace=row['trace'], ts=row['ts'], recorded_research_price=row['price'],
            recorded_price_is_order_price=False, main_price_benchmark=main,
            widget_native_target_formula=widget,
            paired_known=main['complete'] and widget['complete'],
            net_difference_pct=widget['net'] - main['net'] if main['complete'] and widget['complete'] else None))
    return dict(rows=results, paired_known_count=sum(r.get('paired_known', False) for r in results),
        formula_role='same_ask_exact_sale_notional_cost_not_full_live_main_or_widget',
        independent_episodes=False)


def widget_receipt(events, owners, rows):
    completed = [e for e in events if e.get('symbol') == '005930' and e.get('event_type') == 'take_profit_episode_completed']
    if len(completed) != 1:
        raise ValueError('widget_unique_completed_episode_missing')
    receipt = completed[0]
    sid = receipt['signal_id']
    fills = [e for e in events if e.get('event_type') == 'order_execution_reconciled'
        and e.get('symbol') == '005930' and e.get('order_status') == 'FILLED'
        and (e.get('signal_id') == sid or e.get('parent_entry_signal_id') == sid)]
    if len(fills) != 2 or {f['side'] for f in fills} != {'BUY', 'SELL'}:
        raise ValueError('widget_exact_full_fill_pair_missing')
    buy, sell = (next(f for f in fills if f['side'] == side) for side in ('BUY', 'SELL'))
    qty = buy['filled_qty']
    if (not R.finite(qty) or qty <= 0 or qty != sell['filled_qty']
            or any(f['requested_qty'] != qty or f['remaining_qty'] != 0 for f in fills)
            or R.epoch(buy['observed_at']) >= R.epoch(sell['observed_at'])
            or any(f['execution_policy_content_sha256'] != receipt['execution_policy_content_sha256'] for f in fills)):
        raise ValueError('widget_quantity_clock_or_policy_conflict')
    terminals = [r for r in owners if r['event'] == 'ORDER_TERMINAL'
        and r['owner_type'] == 'widget_auto_trade' and r['position_id'].endswith(':' + sid)]
    if len(terminals) != 2 or {r['side'] for r in terminals} != {'BUY', 'SELL'}:
        raise ValueError('widget_custody_terminal_pair_missing')
    for fill in fills:
        terminal = next(r for r in terminals if r['side'] == fill['side'])
        if terminal['filled_qty'] != qty or terminal['fill_amount'] != qty * fill['fill_price']:
            raise ValueError('widget_custody_notional_conflict')
    contracts = [f['timing_operating_opportunity']['contract']['cost_contract'] for f in fills]
    if contracts[0] != contracts[1] or contracts[0]['calculation'] != 'sell_notional_times_rate_once':
        raise ValueError('widget_cost_contract_conflict')
    cost = contracts[0]['rate']
    net = net_pct(buy['fill_price'], sell['fill_price'], cost)
    start, end = R.epoch(buy['observed_at']), R.epoch(sell['observed_at'])
    overlap = [r for r in rows if start <= r['t'] <= end]
    regular_contracts = [e['timing_operating_opportunity']['contract'] for e in events
        if e.get('symbol') == '005930' and e.get('execution_policy_session') == 'KRX_REGULAR'
        and ((e.get('timing_operating_opportunity') or {}).get('contract') or {}).get('native_policy')]
    target = {r['native_policy']['take_profit_bps_from_equal_share_average'] for r in regular_contracts}
    costs = {r['cost_contract']['rate'] for r in regular_contracts}
    if len(target) != 1 or costs != {cost}:
        raise ValueError('regular_widget_target_or_cost_not_unique')
    return dict(signal_id=sid, buy_at=buy['observed_at'], sell_at=sell['observed_at'],
        buy_price=buy['fill_price'], sell_price=sell['fill_price'], quantity=qty,
        requested_and_actual_venue=buy['actual_execution_venue'],
        original_entry_session=buy['execution_policy_session'],
        original_target_bps=buy['timing_operating_opportunity']['contract']['native_policy']['take_profit_bps_from_equal_share_average'],
        regular_target_bps=next(iter(target)), cost_contract=contracts[0],
        execution_policy_sha256=receipt['execution_policy_content_sha256'],
        holding_sec=end - start, gross_realized_krw=(sell['fill_price'] - buy['fill_price']) * qty,
        configured_cost_krw=sell['fill_price'] * qty * cost,
        configured_net_pnl_krw=buy['fill_price'] * qty * net / 100, configured_net_return_pct=net,
        metric_role='actual_full_fills_with_configured_cost_estimate_not_broker_settlement',
        custody_verified=True, main_research_capture_overlap=len(overlap),
        first_main_research_capture=min(r['ts'] for r in rows),
        causal_entry_comparison='unavailable_disjoint_captured_decision_windows' if not overlap else 'requires_same_scope_pair')


def parent_generation(root, frozen, day):
    policy_root = root / 'data/runtime/mechanistic_entry_policy'
    _, effective, selector_path, effective_path = P.current_generation(policy_root)
    dated_path = policy_root / f'policy_{day}.json'
    bundles = [effective]
    seals = {str(p): R.P.file_sha(p) for p in (selector_path, effective_path)}
    if dated_path.exists():
        dated = R.read(dated_path)
        P.M.validate(dated, target_date=day)
        bundles.append(dated);seals[str(dated_path)] = R.P.file_sha(dated_path)
    for bundle in bundles:
        from src.engine.scalping.samsung_policy_compatibility import effective_policy
        effective_policy(root,frozen,bundle=bundle)
    return {b['bundle_sha256'] for b in bundles}, seals


def excluded_native_rows(originals):
    return [dict(trace=r['decision_trace_id'], reason='unverified_canonical_or_source_provenance')
        for r in originals if (r.get('stock_code'), r.get('effective_venue'), r.get('session_bucket'))
        == ('005930', 'KRX', 'KRX_REGULAR')
        and not (r.get('source_provenance_verified') is True and r.get('machine_observation_hash_verified') is True)]


def premarket_owner_bridge(root, widget, seals):
    """Two existing Main decisions, same recorded Widget fill endpoint only."""
    day = widget['buy_at'][:10]
    path = root / f'data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json'
    seals[str(path)] = R.P.file_sha(path)
    wanted = {r['decision_trace_id']: r for r in R.P.stream_array(path)
        if (r.get('stock_code'), r.get('effective_venue'), r.get('session_bucket'))
            == ('005930', 'PREMARKET_KRX_LIKE', 'PREMARKET_KRX_LIKE')
        and R.epoch(r['decision_ts']) <= R.epoch(widget['sell_at'])}
    archive = root / f'data/ai_decision_payloads/ai_decision_payloads_{day}.jsonl'
    if not archive.exists():archive = archive.with_suffix('.jsonl.gz')
    seals[str(archive)] = R.P.file_sha(archive)
    canonical = {}
    for line, raw in O.source_rows(archive):
        trace = raw.get('machine_observation_sha256')
        if trace not in wanted:
            continue
        cap = O.capture_record(raw, path=archive, seal=seals[str(archive)], line=line)
        saved = wanted[trace]
        payload = raw['source']['exact_payload']
        if (cap['captured_at'] != saved['decision_ts'] or cap['bundle'] != saved['bundle_sha256']
                or saved.get('source_provenance_verified') is not True
                or saved.get('machine_observation_hash_verified') is not True
                or payload['quote'] != saved['setup_evidence']['strategy_raw_input']['quote']
                or payload['current'] != saved['setup_evidence']['strategy_raw_input']['current']):
            raise ValueError('premarket_canonical_capture_conflict')
        if trace in canonical:raise ValueError('duplicate_premarket_capture')
        canonical[trace] = dict(payload=payload, location=dict(path=str(archive), line=line))
        if len(canonical) == len(wanted):break
    if set(canonical) != set(wanted):raise ValueError('premarket_capture_missing')
    results = []
    for trace, raw in sorted(wanted.items(), key=lambda pair: pair[1]['decision_ts']):
        payload = canonical[trace]['payload']; quote = payload['quote']
        ask, bid = quote.get('best_ask'), quote.get('best_bid')
        if (not all(R.finite(v) for v in (ask, bid, quote.get('quote_age_ms')))
                or not 0 < bid < ask or quote.get('quote_stale') is not False
                or not 0 <= quote['quote_age_ms'] <= 2000
                or payload['orderbook_top1']['ask']['price'] != ask
                or payload['ai_market_snapshot_v1'].get('market_data_route') != 'nxt_only'):
            raise ValueError('premarket_endpoint_quote_or_route_invalid')
        endpoint = net_pct(ask, widget['sell_price'], widget['cost_contract']['rate'])
        gross = (widget['sell_price'] / ask - 1) * 100
        main_cost = raw['comparison']['conservative_execution_cost_pct']
        if not R.finite(main_cost) or main_cost < 0:raise ValueError('premarket_main_cost_missing')
        results.append(dict(trace=trace, ts=raw['decision_ts'], original_scope=raw['session_bucket'],
            parent_action=raw['machine_action'], parent_reason=raw['machine_reason'],
            counterweight=raw['machine_core_comparison'], source_location=canonical[trace]['location'],
            observed_ask=ask, observed_bid=bid, common_widget_exit_fill_price=widget['sell_price'],
            overlaps_actual_widget_holding=R.epoch(widget['buy_at']) <= R.epoch(raw['decision_ts']),
            endpoint_net_same_configured_cost_pct=endpoint,
            entry_price_effect_vs_actual_widget_pct=endpoint - widget['configured_net_return_pct'],
            main_conservative_estimated_cost_pct=main_cost,
            endpoint_gross_minus_main_conservative_cost_pct=gross - main_cost,
            actual_main_submit=raw['ai_and_final_guard'].get('observed_actual_order_submitted'),
            actual_main_fill=raw['ai_and_final_guard'].get('fill_observed'),
            metric_role='point_endpoint_price_diagnostic_no_interim_path_or_executable_policy_claim',
            actual_main_pnl=None))
    Q.verify_hashes(seals)
    return dict(rows=results, generic_regular_candidate_population=False,
        same_main_widget_full_path_comparison=False, no_entry_at_widget_buy_time_interpolated=True)


def validate_replay_input(root, capsule, frozen):
    """Intake an explicitly prepared later source, never search or collect one."""
    if capsule.get('schema') != 'samsung_frozen_candidate_replay_input_v1':
        raise ValueError('invalid_replay_capsule_schema')
    day = capsule['day']
    if datetime.strptime(day, '%Y-%m-%d').date().isoformat() != day or day <= frozen['later_source_after_date']:
        raise ValueError('reused_discovery_or_prefreeze_source_date')
    if capsule.get('parent_sha256') != frozen['parent_sha256']:
        raise ValueError('replay_parent_policy_changed')
    bundle_hashes, policy_seals = parent_generation(root, frozen, day)
    sources = {str((root / capsule[role]['path']).resolve()): capsule[role]['sha256']
               for role in ('projection', 'capture_census', 'native_projection')}
    sources.update(policy_seals)
    Q.verify_hashes(sources)
    projection = R.read((root / capsule['projection']['path']).resolve())
    census = R.read((root / capsule['capture_census']['path']).resolve())
    if projection['parent_sha256'] != frozen['parent_sha256'] or not census.get('source_seals'):
        raise ValueError('replay_parent_or_source_seals_missing')
    Q.verify_hashes(census['source_seals'])
    rows, captures = projection['main'], census['captures']
    if not rows or {r['day'] for r in rows + captures} != {day}:
        raise ValueError('replay_date_population_conflict')
    if len({r['trace'] for r in rows}) != len(rows) or {r['trace'] for r in rows} != {c['trace'] for c in captures} or len(rows) != len(captures):
        raise ValueError('replay_trace_population_conflict')
    by_trace = {r['trace']: r for r in rows}
    replayed = set()
    originals = sorted(R.P.stream_array((root / capsule['native_projection']['path']).resolve()),
                       key=lambda r: r['decision_ts'])
    exclusions = excluded_native_rows(originals)
    if projection.get('excluded_native_rows', []) != exclusions:
        raise ValueError('replay_source_exclusion_ledger_conflict')
    expected = {r['decision_trace_id'] for r in originals
        if (r.get('stock_code'), r.get('effective_venue'), r.get('session_bucket')) == ('005930', 'KRX', 'KRX_REGULAR')
        and r.get('source_provenance_verified') is True and r.get('machine_observation_hash_verified') is True}
    if expected != set(by_trace):
        raise ValueError('replay_native_projection_population_incomplete')
    for raw in originals:
        row = by_trace.get(raw['decision_trace_id'])
        if row is None:
            continue
        if ((raw.get('stock_code'), raw.get('effective_venue'), raw.get('session_bucket'))
                != ('005930', 'KRX', 'KRX_REGULAR') or raw.get('source_date') != day
                or not raw.get('source_provenance_verified') or not raw.get('machine_observation_hash_verified')):
            raise ValueError('replay_native_projection_scope_or_provenance_conflict')
        from src.engine.scalping.samsung_policy_compatibility import source_bundle
        actual=source_bundle(root,frozen,raw)
        actual_path=root/'data/runtime/mechanistic_entry_policy/generations'/(actual['bundle_sha256']+'.json')
        sources[str(actual_path)]=R.P.file_sha(actual_path)
        prepared = P.D.fast_prepare(raw, frozen['parent_policy'])
        outcome = P.D.outcome_diagnosis(raw)
        try:
            native = list(R.P.opportunity_identity(raw))
        except ValueError:
            native = None
        label = dict(binary=int(outcome['value'] > 0) if outcome['value'] is not None else None,
                     net=outcome['value'], status=outcome['diagnosis'])
        if (row['ts'] != raw['decision_ts'] or row['parent'] != prepared['decision']['action']
                or row['guard'] != P.D.guard_summary(prepared)
                or row['native'] != native or row['label'] != label
                or row['cost'] != raw['comparison']['conservative_execution_cost_pct']
                or row['price'] != raw['setup_evidence']['strategy_raw_input']['current']['price']):
            raise ValueError('replay_normalized_projection_differs_from_native')
        if row['trace'] in replayed:
            raise ValueError('duplicate_native_projection_trace')
        replayed.add(row['trace'])
    if replayed != set(by_trace):
        raise ValueError('replay_native_projection_trace_missing')
    # These epochs belong to the independent archived price stream, not the
    # runtime socket. Reconstruct the two consumed fields from existing shards.
    stream_seals = {}
    trades, _ = R.stream_rows(root, day, 'trade', stream_seals)
    depth, _ = R.stream_rows(root, day, 'depth', stream_seals)
    ordered = sorted(rows, key=lambda r: (r['t'], r['trace']))
    features = R.market_features(trades, depth, [r['t'] for r in ordered])
    for row, feature in zip(ordered, features):
        if any(row['features'].get(k) != feature.get(k) for k in ('stream_valid', 'stream_epoch')):
            raise ValueError('replay_independent_stream_binding_conflict')
    sources.update(stream_seals)
    locations = {}
    for capture in captures:
        row = by_trace[capture['trace']]
        clock = datetime.fromtimestamp(capture['t'], KST).date().isoformat()
        if (row['t'] != capture['t'] or R.epoch(row['ts']) != row['t'] or clock != day
                or capture['ep'] != row['features'].get('stream_epoch')):
            raise ValueError('replay_capture_clock_or_epoch_conflict')
        loc = capture['source_location']
        if census['source_seals'].get(loc['path']) != loc['physical_sha256'] or not isinstance(loc['line'], int) or loc['line'] <= 0:
            raise ValueError('replay_raw_capture_location_unsealed')
        records = locations.setdefault(loc['path'], {})
        if loc['line'] in records:
            raise ValueError('duplicate_raw_capture_location')
        records[loc['line']] = capture
    for name, records in locations.items():
        seen = set()
        for line, raw in O.source_rows(Path(name)):
            if line in records:
                capture = records[line]
                row = by_trace[capture['trace']]
                cap = O.capture_record(raw, path=Path(name), seal=capture['source_location']['physical_sha256'], line=line)
                payload = raw['source']['exact_payload']; snap = payload['ai_market_snapshot_v1']
                if (cap['trace'] != capture['trace'] or R.epoch(cap['captured_at']) != capture['t']
                        or snap.get('effective_venue') != 'KRX' or snap.get('session_bucket') != 'krx_regular'
                        or payload.get('stock_code') != '005930'
                        or snap.get('market_data_route') != capture['market_route']
                        or {'krx_nxt_integrated': '_AL', 'nxt_only': '_NX', 'krx_only': ''}.get(capture['market_route']) != capture['market_suffix']
                        or capture['stream_valid'] != (row['features'].get('stream_valid') is True)
                        or snap['sources'].get('program') != capture['program']
                        or snap['sources'].get('investor') != capture['investor']
                        or N.optional_epoch(snap.get('captured_at')) != capture['snapshot_t']):
                    raise ValueError('replay_normalized_capture_differs_from_canonical_raw')
                seen.add(line)
            if line >= max(records):
                break
        if seen != set(records):
            raise ValueError('replay_raw_location_missing')
    Q.verify_hashes(sources); Q.verify_hashes(census['source_seals'])
    return rows, captures, {**sources, **census['source_seals']}


def prepare_later_input(root, day, frozen, output):
    """Normalize existing automatically produced files; never request data."""
    if datetime.strptime(day, '%Y-%m-%d').date().isoformat() != day or day <= frozen['later_source_after_date']:
        raise ValueError('prefreeze_preparation_date')
    native_path = root / f'data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json'
    capture_path = root / f'data/ai_decision_payloads/ai_decision_payloads_{day}.jsonl'
    if not capture_path.exists():
        capture_path = capture_path.with_suffix('.jsonl.gz')
    stream_root = root / f'data/observations/scalp_micro_reversion_forward/trade_date={day}/venue=SOR/session=SOR_REGULAR'
    required = [native_path, capture_path, stream_root / 'market_stream.manifest.json',
                stream_root / 'market_depth_stream.manifest.json']
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        write(output / 'preparation-status.json', dict(day=day, status='waiting_new_source_date',
            missing_source_paths=missing, data_collected=False, candidate_reselection=False,
            frozen_sha256=R.digest(frozen), official_policy_candidate=None))
        return None
    bundle_hashes, policy_seals = parent_generation(root, frozen, day)
    seals = {str(p): R.P.file_sha(p) for p in (native_path, capture_path)}
    seals.update(policy_seals)
    rows = []
    originals = sorted(R.P.stream_array(native_path), key=lambda r: r['decision_ts'])
    exclusions = excluded_native_rows(originals)
    for raw in originals:
        if (raw.get('stock_code'), raw.get('effective_venue'), raw.get('session_bucket')) != ('005930', 'KRX', 'KRX_REGULAR'):
            continue
        if raw.get('source_provenance_verified') is not True or raw.get('machine_observation_hash_verified') is not True:
            continue
        if raw.get('source_date') != day:
            raise ValueError('prepare_native_provenance_or_date_conflict')
        from src.engine.scalping.samsung_policy_compatibility import source_bundle
        actual=source_bundle(root,frozen,raw)
        actual_path=root/'data/runtime/mechanistic_entry_policy/generations'/(actual['bundle_sha256']+'.json')
        seals[str(actual_path)]=R.P.file_sha(actual_path)
        prepared = P.D.fast_prepare(raw, frozen['parent_policy'])
        outcome = P.D.outcome_diagnosis(raw)
        try:
            native = list(R.P.opportunity_identity(raw))
        except ValueError:
            native = None
        rows.append(dict(day=day, t=R.epoch(raw['decision_ts']), ts=raw['decision_ts'],
            trace=raw['decision_trace_id'], native=native, parent=prepared['decision']['action'],
            guard=P.D.guard_summary(prepared), price=raw['setup_evidence']['strategy_raw_input']['current']['price'],
            cost=raw['comparison']['conservative_execution_cost_pct'],
            label=dict(binary=int(outcome['value'] > 0) if outcome['value'] is not None else None,
                       net=outcome['value'], status=outcome['diagnosis'])))
    rows.sort(key=lambda r: (r['t'], r['trace']))
    if not rows:
        write(output / 'preparation-status.json', dict(day=day,
            status='source_quality_excluded_all' if exclusions else 'valid_empty_native_population',
            excluded_native_rows=exclusions, source_seals=seals, official_policy_candidate=None,
            data_collected=False, candidate_reselection=False))
        Q.verify_hashes(seals)
        return None
    if len({r['trace'] for r in rows}) != len(rows):
        raise ValueError('prepare_duplicate_native_population')
    trades, _ = R.stream_rows(root, day, 'trade', seals)
    depth, _ = R.stream_rows(root, day, 'depth', seals)
    for row, features in zip(rows, R.market_features(trades, depth, [r['t'] for r in rows])):
        row['features'] = {k: features.get(k) for k in ('stream_valid', 'stream_epoch')}
    by_trace = {r['trace']: r for r in rows}
    captures = []
    for line, raw in O.source_rows(capture_path):
        row = by_trace.get(raw.get('machine_observation_sha256'))
        if row is None:
            continue
        cap = O.capture_record(raw, path=capture_path, seal=seals[str(capture_path)], line=line)
        payload = raw['source']['exact_payload']; snap = payload['ai_market_snapshot_v1']
        route = snap.get('market_data_route')
        captures.append(dict(day=day, t=R.epoch(cap['captured_at']), trace=cap['trace'],
            ep=row['features']['stream_epoch'], stream_valid=row['features']['stream_valid'] is True,
            snapshot_t=N.optional_epoch(snap.get('captured_at')), market_route=route,
            market_suffix={'krx_nxt_integrated': '_AL', 'nxt_only': '_NX', 'krx_only': ''}.get(route),
            program=snap['sources'].get('program'), investor=snap['sources'].get('investor'),
            source_location=dict(path=str(capture_path), physical_sha256=seals[str(capture_path)], line=line)))
    captures.sort(key=lambda c: (c['t'], c['trace']))
    Q.verify_hashes(seals)
    write(output / 'projection.json', dict(main=rows, parent_sha256=frozen['parent_sha256'], excluded_native_rows=exclusions))
    write(output / 'capture-census.json', dict(captures=captures, source_seals=seals))
    capsule = dict(schema='samsung_frozen_candidate_replay_input_v1', day=day, parent_sha256=frozen['parent_sha256'],
        native_projection=dict(path=str(native_path), sha256=seals[str(native_path)]),
        **{role: dict(path=str(output / name), sha256=R.P.file_sha(output / name))
           for role, name in [('projection', 'projection.json'), ('capture_census', 'capture-census.json')]})
    write(output / 'replay-input.json', capsule)
    return capsule


def run(root, output):
    accepted = root / 'tmp/samsung-environment-conditioned-research-20261004'
    paths = [accepted / 'accepted-cold/result.json', accepted / 'accepted-sequence-cold/result.json',
             accepted / 'accepted-cold/source-census.json',
             root / 'tmp/samsung-opportunity-contract-20261004/accepted-cold/result.json']
    environment, sequence, census, ownership = [R.read(p) for p in paths]
    if ownership['owner_inventory'].get('chain_valid') is not True:
        raise ValueError('custody_journal_chain_not_verified')
    seals = {**environment['source_seals'], **sequence['source_seals'], **ownership['source_seals']}
    seals.update({str(p): R.P.file_sha(p) for p in paths})
    for p in [Path(__file__).resolve(), root / 'src/tests/test_samsung_fixed_watch_evaluation_research.py',
              root / 'docs/proposals/samsung-fixed-watch-evaluation-and-owner-comparison-plan-2026-10-04.md',
              root / 'src/trading/order/tick_utils.py', root / 'src/trading/widget_auto_trade/engine.py',
              root / 'src/engine/trade_profit.py']:
        seals[str(p)] = R.P.file_sha(p)
    Q.verify_hashes(seals); Q.verify_hashes(ownership['preserved'])
    manifest, source_seals, _ = C.load_manifest(root / 'tmp/samsung-pattern-campaign-20261004/verified-regular-source/manifest.json')
    seals.update(source_seals)
    projection = R.read(Path(manifest['projection'])); rows = projection['main']
    frozen = frozen_spec(environment, sequence)
    if projection['parent_sha256'] != frozen['parent_sha256']:
        raise ValueError('frozen_projection_parent_drift')
    masks = candidate_masks(rows, census['captures'], frozen)
    native = native_comparison(rows, masks)
    for i, key in enumerate(KEYS):
        if native['all_origins']['train']['candidates'][key] != frozen['training_metrics'][i]:
            raise ValueError('frozen_native_training_replay_mismatch')
    widget_path = root / 'data/report/widget_signal_auto_trade_events/widget_signal_auto_trade_events_20261002.jsonl'
    seals[str(widget_path)] = R.P.file_sha(widget_path)
    widget = widget_receipt([json.loads(s) for s in widget_path.open()], ownership['owner_inventory']['rows'],
                            [r for r in rows if r['day'] == '2026-10-02'])
    premarket = premarket_owner_bridge(root, widget, seals)
    bootstrap_path = root / 'data/runtime/policy_bootstrap/runtime_policy_bootstrap_2026-10-02.env'
    seals[str(bootstrap_path)] = R.P.file_sha(bootstrap_path)
    trailing = {s.split('=')[0].removeprefix('export '): s.split('=', 1)[1]
        for s in bootstrap_path.read_text().splitlines() if s.startswith('export KORSTOCKSCAN_SCALP_TRAILING_')
        and any(k in s.split('=')[0] for k in ('START_PCT', 'LIMIT_WEAK', 'LIMIT_STRONG', 'STRENGTH_VERSION'))}
    episodes, panels, causal = {}, {}, {}
    definitions = [d for d in P.definitions() if d['id'] in ('base_recovery:300:5', 'absorption_release:300:5')]
    for day in N.DAYS:
        prepared = R.read(Path(manifest['files'][day]['path']))
        ctx = C.campaign_context(P.E.read_cache(Path(prepared['cache']['path'])))
        main = [r for r in rows if r['day'] == day]
        episodes[day] = {d['id']: episode_replay(ctx, P.state_signals(ctx, prepared['frames'], d), main,
                             manifest['fee_profiles'][day]['cost_pct']) for d in definitions}
        captured = []
        for row in main:
            if fixed_watch(row) and row['parent'] == 'ENTER_NOW':
                signal = captured_signal(ctx, row)
                if signal is not None:
                    captured.append(dict(signal, ep=row['features']['stream_epoch']))
        for key, selected in [('parent_enter', {r['trace'] for r in main if r['parent'] == 'ENTER_NOW'}), *masks.items()]:
            episodes[day][key] = episode_replay(ctx, [s for s in captured if s['captured_trace'] in selected], main,
                                              manifest['fee_profiles'][day]['cost_pct'])
        if day == '2026-10-02':
            panels[day] = same_entry_panel(ctx, main, widget['regular_target_bps'], widget['cost_contract']['rate'])
        caps = [c for c in census['captures'] if c['day'] == day]
        full = candidate_masks(main, caps, frozen)
        checks = []
        for cut in (len(main)//3, 2*len(main)//3):
            prefix = main[:cut]; cutoff = prefix[-1]['t']
            actual = candidate_masks(prefix, [c for c in caps if c['t'] <= cutoff], frozen)
            expected = {key: ids & {r['trace'] for r in prefix} for key, ids in full.items()}
            checks.append(actual == expected)
        if not all(checks):
            raise ValueError('frozen_selector_uses_future_source')
        causal[day] = dict(actual_prefix_checks=len(checks), passed=all(checks))
    Q.verify_hashes(seals); Q.verify_hashes(ownership['preserved'])
    parent_path = root / 'tmp/machine-confirmation-candidate-research-20261003/run-final/frozen-candidates.json'
    frozen['parent_policy'] = R.read(parent_path)['parent_policy']
    frozen['replay_dependency_seals'] = {path: seal for path, seal in seals.items() if path.endswith('.py')}
    validate_frozen(frozen)
    write(output / 'frozen-candidates.json', frozen)
    write(output / 'episodes.json', dict(by_day=episodes,
        train={key: clustered_episode_metric([r for day in N.TRAIN for r in episodes[day][key]['outcomes']])
               for key in episodes[N.DAYS[0]]}))
    write(output / 'result.json', dict(source_seals=seals, preserved=ownership['preserved'],
        native_comparison=native, widget_actual=widget, same_entry_panels=panels,
        premarket_owner_bridge=premarket,
        original_main_exit_settings=dict(source=str(bootstrap_path), values=trailing,
            role='exact_date_prepared_configuration_pid_consumption_not_proven'),
        causal_prefix=causal, new_generic_policy_candidate=None,
        evaluation_contract=fold_contract(rows, N.TRAIN, N.DAYS[2:]),
        original_watch_cluster_kept=True, actual_main_closed_episode_support=ownership['usable_episode_count'],
        dedicated_publisher_registered=False, later_replay_status='waiting_new_source_date',
        prior_time_and_fixed_trailing_sweeps_repeated=False))
    return dict(output=str(output), official_policy_candidate=None, later_replay_status='waiting_new_source_date')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--frozen', type=Path)
    parser.add_argument('--replay-input', type=Path)
    parser.add_argument('--prepare-date')
    args = parser.parse_args(argv)
    output = args.output.resolve()
    root = args.root.resolve()
    if not output.is_relative_to(root / 'tmp') or output == root / 'tmp':
        parser.error('--output must be a new research generation under ROOT/tmp')
    if output.exists() and any(output.iterdir()):
        parser.error('output generation already exists; use a new generation')
    if (bool(args.frozen) != bool(args.replay_input or args.prepare_date)
            or (args.replay_input and args.prepare_date)):
        parser.error('--frozen requires exactly one of --replay-input or --prepare-date')
    if args.frozen:
        frozen = R.read(args.frozen)
        validate_frozen(frozen,root=root)
        capsule = R.read(args.replay_input) if args.replay_input else prepare_later_input(root, args.prepare_date, frozen, output)
        if capsule is None:
            status = R.read(output / 'preparation-status.json')['status']
            print(json.dumps(dict(status=status, day=args.prepare_date)))
            return
        rows, caps, seals = validate_replay_input(root, capsule, frozen)
        masks = candidate_masks(rows, caps, frozen)
        Q.verify_hashes(seals); validate_frozen(frozen,root=root)
        write(output / 'later-replay.json', dict(day=capsule['day'], source_seals=seals,
            frozen_sha256=R.P.file_sha(args.frozen), native_comparison=native_comparison(rows, masks),
            candidate_reselection=False, official_policy_candidate=None))
        print(json.dumps(dict(status='offline_later_replay_completed', day=capsule['day'])))
    else:
        print(json.dumps(run(root, output)))


if __name__ == '__main__':
    main()
