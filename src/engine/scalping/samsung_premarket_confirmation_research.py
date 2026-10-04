"""Bounded offline Samsung premarket confirmation ablations; no live caller.

Captured Main masks and retained-stream price proxies are separate estimands.
No normalized API schema, live setup, policy, custody or order is mutated.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter
from pathlib import Path

from src.engine.scalping import samsung_fixed_watch_evaluation_research as F

R, P, C, Q, O, D = F.R, F.P, F.C, F.Q, F.O, F.P.D
SCOPE = ('PREMARKET_KRX_LIKE', 'PREMARKET_KRX_LIKE')
RECIPES = ('soft_only_bound', 'positive_micro', 'nonnegative_price', 'bid_rise_5',
    'bid_hold_5', 'bid_hold_15', 'nonnegative_bid_hold_5', 'trade_backed_1',
    'trade_backed_refill_half')
AUTHORITY = {**F.AUTHORITY, 'consumer_scope': 'offline_samsung_premarket_confirmation',
    'metric_role': 'captured_main_confirmation_and_separate_retained_price_proxy',
    'primary_decision_metric': 'train_only_price_binary_win_rate_not_native_promotion',
    'source_quality_gate': 'canonical_scope_parent_and_past_exact_nx_archive_prefix',
    'sample_floor': 'three_train_price_binary_comparisons_not_registered_main_support',
    'episode_support_registered': False, 'synthetic_native_identity': False,
    'success_preservation_veto': False, 'live_selector_registered': False}
MODEL = dict(horizon=1200, target_net=.1, cost_pct=.23, gross_stop_pct=-.7,
             price_basis='past_ask_entry_observed_bid_exit', latency=0.)


def write(path, body):
    value = {**{k: v for k, v in body.items() if k != 'content_sha256'}, **AUTHORITY}
    value['content_sha256'] = R.digest(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(C.json.dumps(value, indent=2, allow_nan=False) + '\n')


def quote_window(ctx, at, seconds, epoch):
    """Only receipts strictly before the decision; inspect intervening rows."""
    right = bisect_left(ctx['dt'], at) - 1
    left = Q.quote_at(ctx['depth'], ctx['dt'], at - seconds, epoch)
    if left is None or right < left or at - ctx['dt'][right] > 1.5:
        return None
    rows = ctx['depth'][left:right + 1]
    if any(not C.actionable(q) or q['ep'] != epoch for q in rows):
        return None
    if any(not b['continuous'] or b['seq'] != a['seq'] + 1
           or not 0 <= b['t'] - a['t'] <= 1.5 for a, b in zip(rows, rows[1:])):
        return None
    return rows


def past_features(ctx, at):
    """Market-only proxies; never fabricate completed bars or Main setup facts."""
    i = bisect_left(ctx['times'], at) - 1
    if i < 9 or at - ctx['times'][i] > 1.5:
        return dict(usable=False, reason='trusted_ten_trade_prefix_missing')
    trades = ctx['rows'][i - 9:i + 1]
    if (any(not r['flow_valid'] for r in trades)
            or any(not P.E.connected(a, b, flow=True) for a, b in zip(trades, trades[1:]))):
        return dict(usable=False, reason='trusted_ten_trade_prefix_invalid')
    ep = trades[-1]['ep']
    qi = Q.quote_at(ctx['depth'], ctx['dt'], at, ep)
    if qi is None or not C.actionable(ctx['depth'][qi]):
        return dict(usable=False, reason='past_executable_quote_missing')
    buy = sum(r['q'] for r in trades if r['side'] == 'BUY')
    sell = sum(r['q'] for r in trades if r['side'] == 'SELL')
    result = dict(usable=True, delta=buy - sell,
        price_pct=(trades[-1]['p'] / trades[0]['p'] - 1) * 100,
        bid_5=None, bid_15=None, proof=None, refill=None,
        proof_source='retained_fixed_ask_depletion_proxy_not_captured_feature',
        signal=dict(index=i, t=at), archive_epoch=ep,
        last_trade_at=trades[-1]['t'], last_quote_at=ctx['depth'][qi]['t'])
    for seconds in (5, 15):
        quotes = quote_window(ctx, at, seconds, ep)
        if quotes:
            result[f'bid_{seconds}'] = quotes[-1]['bid'] - quotes[0]['bid']
    quotes = quote_window(ctx, at, 1, ep)
    if quotes and len(quotes) >= 2 and all(q['ask'] == quotes[0]['ask'] for q in quotes):
        maximum = 0.; backed = 0.; refill = 0.
        for a, b in zip(quotes, quotes[1:]):
            refill += max(0., b['aq'] - a['aq'])
            depletion = quotes[0]['aq'] - b['aq']
            if depletion > maximum:
                maximum = depletion
                # Equal clocks across streams do not prove post-anchor order.
                lo, hi = bisect_right(ctx['times'], quotes[0]['t']), bisect_left(ctx['times'], b['t'])
                window = ctx['rows'][lo:hi]
                if (any(not r['flow_valid'] or r['ep'] != ep for r in window)
                        or any(not P.E.connected(x, y, flow=True) for x, y in zip(window, window[1:]))):
                    return {**result, 'proof': None, 'refill': None}
                backed = sum(r['q'] for r in window if r['side'] == 'BUY' and r['p'] == b['ask'])
        result.update(proof=(min(1., backed / maximum) if maximum > 0 else 0.),
                      refill=(refill / maximum if maximum > 0 else 0.),
                      depletion=maximum, downward=False)
    return result


def masks(features, minimum_delta=1.):
    """One deterministic vector shared by all labels; nulls are not zero."""
    if not R.finite(minimum_delta) or minimum_delta < 0:
        raise ValueError('parent_delta_threshold_invalid')
    f = features
    flow = f.get('usable') is True and R.finite(f.get('delta')) and f['delta'] >= minimum_delta
    price = R.finite(f.get('price_pct')) and f['price_pct'] > 0
    flat = R.finite(f.get('price_pct')) and f['price_pct'] >= 0
    rise = R.finite(f.get('bid_5')) and f['bid_5'] > 0
    hold5 = R.finite(f.get('bid_5')) and f['bid_5'] >= 0
    hold15 = R.finite(f.get('bid_15')) and f['bid_15'] >= 0
    proof = (flow and R.finite(f.get('proof')) and .5 <= f['proof'] <= 1.
             and R.finite(f.get('depletion')) and f['depletion'] > 0
             and f.get('downward') is False)
    return dict(soft_only_bound=True, positive_micro=flow and price,
        nonnegative_price=flow and flat, bid_rise_5=flow and price and rise,
        bid_hold_5=flow and price and hold5, bid_hold_15=flow and price and hold15,
        nonnegative_bid_hold_5=flow and flat and hold5, trade_backed_1=proof,
        trade_backed_refill_half=proof and R.finite(f.get('refill')) and 0 <= f['refill'] <= .5)


def envelope(prepared, provenance=True):
    guard = D.guard_summary(prepared, provenance=provenance)
    decision = prepared['decision']
    return bool(decision['action'] == 'RECHECK'
        and decision['reason'] in {'SETUP_DISCOVERY_RECHECK', 'MICRO_PRICE_RESPONSE_RECHECK',
                                   'TRIGGER_CONFIRMATION_RECHECK'}
        and not guard['blockers']), guard


def captured_masks(row, prepared, past, parent):
    allowed, guard = envelope(prepared)
    micro = prepared['rebuilt'].get('micro_recovery_observation') or {}
    quote = row['setup_evidence']['strategy_raw_input'].get('quote') or {}
    now = R.epoch(row['decision_ts'])
    fresh = (quote.get('quote_stale') is False and R.finite(quote.get('quote_age_ms'))
        and 0 <= quote['quote_age_ms'] <= 2000
        and R.finite(quote.get('evaluation_as_of')) and 0 <= now - quote['evaluation_as_of'] <= 2
        and all(R.finite(quote.get(k)) for k in ('best_ask', 'best_bid'))
        and 0 < quote['best_bid'] < quote['best_ask'])
    if not fresh or micro.get('source_usable') is not True:
        allowed = False
        guard = {**guard, 'blockers': [*guard['blockers'], 'captured_quote_or_micro_source_unusable']}
    f = dict(past, usable=micro.get('source_usable') is True,
             delta=micro.get('net_aggressive_delta_10t'), price_pct=micro.get('price_change_10t_pct'),
             proof=None, refill=None, depletion=None, downward=None,
             proof_source='captured_machine_confirmation_fixed_price_window_v1')
    window = row['setup_evidence']['strategy_raw_input'].get('mechanistic_micro_window') or {}
    raw = window.get('feature') or {}
    now_ms = now * 1000
    if (raw.get('source_quality_status') == 'eligible' and raw.get('eligible_for_feature_ablation') is True
            and raw.get('horizon_ms') == 1000 and raw.get('source_gap_reasons') == []
            and window.get('item') == '005930_NX' and window.get('source_quality_status') == 'eligible'
            and R.finite(raw.get('checkpoint_at_ms')) and 0 <= now_ms - raw['checkpoint_at_ms'] <= 2000
            and R.finite(raw.get('window_started_at_ms'))
            and raw['checkpoint_at_ms'] - raw['window_started_at_ms'] == 1000
            and R.finite(window.get('cutoff_ms')) and window['cutoff_ms'] == raw['checkpoint_at_ms']
            and (window.get('machine_market_route_binding') or {}).get('market_data_route') == 'nxt_only'):
        f.update(proof=raw.get('aggressive_buy_trade_backed_ratio'), refill=raw.get('refill_ratio'),
            depletion=raw.get('max_best_ask_depletion_qty'), downward=raw.get('downward_reprice_observed'))
    threshold = prepared['decision']['applied_thresholds']['minimum_micro_net_aggressive_delta_10t']
    if prepared['decision']['applied_thresholds']['minimum_micro_price_change_10t_pct'] != 0:
        raise ValueError('parent_price_threshold_requires_replan')
    vector = masks(f, threshold)
    # Preserve the original situation owner after the soft mask as well.
    vetoed = D.E._apply_entry_situation_veto(
        {**prepared['decision'], 'action': 'ENTER_NOW'}, row['setup_evidence'], parent)
    if vetoed['action'] != 'ENTER_NOW':
        allowed = False
        guard = {**guard, 'blockers': [*guard['blockers'], 'entry_situation_veto']}
    return {key: allowed and value for key, value in vector.items()}, guard, f


def choose(train_trials):
    baseline = train_trials['soft_only_bound']['metric']
    eligible = [key for key, trial in train_trials.items() if key != 'soft_only_bound'
        and trial['metric']['binary'] >= 3 and baseline['binary'] >= 3
        and trial['metric']['conditional_target_first_win_rate'] > baseline['conditional_target_first_win_rate']]
    return max(eligible, key=lambda key: (
        train_trials[key]['metric']['conditional_target_first_win_rate'],
        train_trials[key]['metric']['binary'], -RECIPES.index(key)), default=None)


def price_trials(ctx, features):
    result = {}
    # Every candidate reuses exactly the same label for a given signal.
    outcomes = {i: C.label(ctx, f['signal'], horizon=MODEL['horizon'],
        target_net=MODEL['target_net'], cost_pct=MODEL['cost_pct'])
        for i, f in enumerate(features) if f.get('usable') is True}
    vectors = [masks(f) for f in features]
    for key in RECIPES:
        signals = [dict(f['signal'], feature_index=i) for i, f in enumerate(features)
                   if f.get('usable') is True and vectors[i][key]]
        replayed = P.replay(signals, lambda s: outcomes[s['feature_index']], cooldown=5)
        result[key] = dict(metric=replayed['metric'], episodes=replayed['outcomes'], blocked=replayed['blocked_signals'],
            eligible_signals=len(signals), unit='modeled_nonoverlapping_price_episode_not_native',
            same_price_cost_exit_per_signal=True)
    return result


def captured_summary(panel, key, days):
    """First selected observation per original watch, never last winning row."""
    selected = []; seen = set()
    for row in panel:
        native = tuple(row['native'])
        if row['day'] in days and row['masks'][key] and native not in seen:
            seen.add(native); selected.append(row)
    labels = [r['original_diagnosis']['value'] for r in selected
              if r['original_diagnosis']['value'] is not None]
    return dict(selected_observations=sum(r['day'] in days and r['masks'][key] for r in panel),
        original_native_clusters=len(selected), source_dates=len({r['day'] for r in selected}),
        original_known_binary=len(labels), original_target_first=sum(v > 0 for v in labels),
        original_win_rate=sum(v > 0 for v in labels) / len(labels) if labels else None,
        first_selected_traces=[r['trace'] for r in selected],
        original_unknown=len(selected) - len(labels),
        same_stamp_price_metric=P.terminal_metric([r['price_label'] for r in selected]),
        unit='first_selected_original_watch_date_not_dense_signal')


def verify_capture(row, capture):
    raw, cap = capture
    p = raw['source']['exact_payload']; saved = row['setup_evidence']['strategy_raw_input']
    if (cap['captured_at'] != row['decision_ts'] or cap['bundle'] != row['bundle_sha256']
            or row.get('source_provenance_verified') is not True
            or row.get('machine_observation_hash_verified') is not True
            or any(p.get(k) != saved.get(k) for k in ('current', 'quote', 'features'))
            or p.get('ai_market_snapshot_v1', {}).get('market_data_route') != 'nxt_only'
            or (row.get('effective_venue'), row.get('session_bucket')) != SCOPE
            or row['source_date'] != row['decision_ts'][:10] or row['stock_code'] != '005930'):
        raise ValueError('canonical_scope_payload_conflict')
    R.epoch(row['decision_ts'])
    native = list(R.P.opportunity_identity(row))
    identity_keys = O.NATIVE_KEYS[:3] if row.get('watch_origin') == 'MAIN_FIXED_WATCH' else ('scanner_promotion_id',)
    if any((cap['top_native'].get(k) or cap['payload_native'].get(k)) != row.get(k)
           for k in identity_keys):
        raise ValueError('canonical_native_conflict')
    return native


def intake(root, seals):
    days, excluded = {}, []
    for day in R.DAYS:
        path = root / f'data/report/machine_observation_projection/machine_observation_projection_{day}_0_1.json'
        seals[str(path)] = R.P.file_sha(path)
        wanted = [r for r in R.P.stream_array(path) if r.get('stock_code') == '005930'
            and (r.get('effective_venue'), r.get('session_bucket')) == SCOPE]
        if len({r['decision_trace_id'] for r in wanted}) != len(wanted):
            raise ValueError('duplicate_projection_trace')
        archive = root / f'data/ai_decision_payloads/ai_decision_payloads_{day}.jsonl'
        if not archive.exists():
            archive = archive.with_suffix('.jsonl.gz')
        seals[str(archive)] = R.P.file_sha(archive)
        targets = {r['decision_trace_id'] for r in wanted}; captures = {}; errors = {}; raw_census = []
        for line, raw in O.source_rows(archive):
            trace = raw.get('machine_observation_sha256')
            context = raw.get('label_context') or {}
            if (context.get('stock_code') == '005930'
                    and tuple(str(context.get(k) or '').upper() for k in ('effective_venue', 'session_bucket')) == SCOPE):
                try:
                    O.capture_record(raw, path=archive, seal=seals[str(archive)], line=line)
                    evidence_errors = D.E.validate_entry_setup_evidence((raw.get('source') or {}).get('setup_evidence'))
                    canonical = True
                except (ValueError, KeyError, TypeError, AttributeError) as exc:
                    evidence_errors = [str(exc)]; canonical = False
                assessment = (raw.get('source') or {}).get('assessment') or {}
                raw_census.append(dict(trace=trace, ts=raw.get('captured_at'),
                    canonical_hash_valid=canonical, setup_validation_errors=evidence_errors,
                    projected=trace in targets, recorded_action=assessment.get('action'),
                    recorded_reason=assessment.get('reason'),
                    source_location=dict(path=str(archive), line=line),
                    disposition='projected' if trace in targets else
                        'invalid_source_setup_excluded' if evidence_errors else 'projection_gap_not_silently_admitted'))
            if trace not in targets:
                continue
            if trace in captures or trace in errors:
                errors[trace] = 'duplicate_canonical_capture'; captures.pop(trace, None); continue
            try:
                cap = O.capture_record(raw, path=archive, seal=seals[str(archive)], line=line)
                captures[trace] = raw, cap
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                errors[trace] = str(exc)
        rows = []
        for row in sorted(wanted, key=lambda r: r['decision_ts']):
            trace = row['decision_trace_id']
            try:
                if trace in errors or trace not in captures:
                    raise ValueError(errors.get(trace, 'canonical_capture_missing'))
                native = verify_capture(row, captures[trace])
            except (ValueError, KeyError, TypeError, AttributeError) as exc:
                excluded.append(dict(day=day, trace=trace, reason=str(exc))); continue
            policy_path = root / 'data/runtime/mechanistic_entry_policy/generations' / (row['bundle_sha256'] + '.json')
            seals[str(policy_path)] = R.P.file_sha(policy_path)
            generation = R.read(policy_path)
            P.M.validate(generation, target_date=generation['target_date'])
            parent = generation['scope_policies']['|'.join(SCOPE)]['machine_policy']
            prepared = D.fast_prepare(row, parent)
            if (prepared['decision']['action'], prepared['decision']['reason']) != (row['machine_action'], row['machine_reason']):
                raise ValueError('exact_premarket_parent_replay_conflict')
            rows.append(dict(raw=row, prepared=prepared, parent=parent, native=native,
                parent_sha256=R.S.digest(parent), capture_location={k: captures[trace][1][k]
                    for k in ('path', 'physical_sha256', 'line')}))
        days[day] = dict(rows=rows, original_count=len(wanted), raw_capture_census=raw_census,
            status='valid_empty' if not wanted else 'eligible' if rows else 'source_quality_excluded_all')
    return days, excluded


def run(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if not output.is_relative_to(root / 'tmp') or output == root / 'tmp' or output.exists():
        raise ValueError('research_output_requires_new_workspace_tmp_child')
    prior_path = root / 'tmp/samsung-fixed-watch-evaluation-20261004/validation/closure.json'
    prior = R.read(prior_path)
    seals = {**prior['source_seals'], str(prior_path): R.P.file_sha(prior_path)}
    Q.verify_hashes(seals); Q.verify_hashes(prior['preserved'])
    for module in (F, D, D.E, D.S):
        path = Path(module.__file__).resolve(); seals[str(path)] = R.P.file_sha(path)
    for relative in ('src/engine/scalping/samsung_premarket_confirmation_research.py',
        'src/tests/test_samsung_premarket_confirmation_research.py',
        'docs/proposals/samsung-premarket-confirmation-component-research-plan-2026-10-04.md'):
        path = root / relative; seals[str(path)] = R.P.file_sha(path)
    manifest, records, _ = C.load_manifest(root / 'tmp/samsung-pattern-campaign-20261004/verified-session-source/manifest.json')
    seals.update(records)
    captures, exclusions = intake(root, seals)
    training = {}; validation = {}; sensitivity = {}; panel = []; source_census = {}; prefix_checks = []
    frozen = dict(recipes=list(RECIPES), price_model=MODEL, source_seals=seals,
        training_dates=list(R.DAYS[:2]), retrospective_validation_dates=[R.DAYS[2]],
        native_parent_scope=list(SCOPE), main_native_is_not_dense_price_unit=True,
        no_setup_or_guard_fabricated=True)
    write(output / 'frozen-experiment.json', frozen)
    for day in R.DAYS:
        cache = P.E.read_cache(Path(manifest['files']['NXT_PREMARKET|' + day]['path']))
        ctx = C.campaign_context(cache)
        sensitivity_ctx = C.campaign_context(cache, max_quote_gap=10.)
        # Freeze decision clocks from retained frames; no outcome is read here.
        features = [past_features(ctx, f['t']) for f in cache['frames']]
        source_census[day] = dict(main_observations=captures[day]['original_count'],
            canonical_archive_captures=len(captures[day]['raw_capture_census']),
            raw_capture_census=captures[day]['raw_capture_census'],
            accepted_main=len(captures[day]['rows']), main_status=captures[day]['status'],
            original_native_clusters=len({tuple(r['native']) for r in captures[day]['rows']}),
            trades=len(cache['rows']), quotes=len(cache['depth']), frames=len(features),
            usable_features=sum(f.get('usable') is True for f in features),
            proxy_missing=dict(Counter(f.get('reason') for f in features if f.get('usable') is not True)))
        if cache['frames']:
            for frame in (cache['frames'][len(cache['frames']) // 3], cache['frames'][2 * len(cache['frames']) // 3]):
                at = frame['t']
                prefix = dict(rows=[r for r in cache['rows'] if r['t'] < at],
                              depth=[q for q in cache['depth'] if q['t'] < at])
                if past_features(C.campaign_context(prefix), at) != past_features(ctx, at):
                    raise ValueError('actual_source_future_mask_conflict')
                prefix_checks.append(dict(day=day, at=at, equal=True))
        for item in captures[day]['rows']:
            row, prepared = item['raw'], item['prepared']; at = R.epoch(row['decision_ts'])
            past = past_features(ctx, at)
            vector, guard, inputs = captured_masks(row, prepared, past, item['parent'])
            entry = Q.entry_for(ctx, past.get('signal'))
            expected = row['setup_evidence']['strategy_raw_input']['quote']['best_ask']
            label = C.label(ctx, past.get('signal'), horizon=1200, cost_pct=.23)
            if entry is None or entry['price'] != expected:
                label = dict(binary=None, net=None, complete=False, status='captured_quote_mismatch')
            panel.append(dict(day=day, trace=row['decision_trace_id'], ts=row['decision_ts'],
                native=item['native'], parent_sha256=item['parent_sha256'], location=item['capture_location'],
                parent_action=row['machine_action'], parent_reason=row['machine_reason'],
                guard=guard, setup_family=prepared['rebuilt']['setup_family'],
                structure_phase=prepared['rebuilt']['structure_phase'],
                completed_bars=row['setup_evidence']['source_quality'].get('completed_bar_count'),
                capture_source_quality=row['setup_evidence']['source_quality'],
                inputs=inputs, masks=vector, ask=expected,
                original_path=row['comparison'].get('entry_path_first_hit'),
                original_cost_pct=row['comparison'].get('conservative_execution_cost_pct'),
                original_diagnosis=D.outcome_diagnosis(row),
                price_label=label, actual_main_pnl=None,
                archive_epoch_equated_to_capture_transport_epoch=False))
        trials = price_trials(ctx, features)
        sensitivity[day] = price_trials(sensitivity_ctx, features)
        if day in R.DAYS[:2]:
            training[day] = trials
        else:
            validation[day] = trials
        if day == R.DAYS[1]:
            train_summary = {key: dict(metric=P.terminal_metric([
                e for d in training.values() for e in d[key]['episodes']])) for key in RECIPES}
            selected = choose(train_summary)
            # Persist selection before opening any held-day price outcomes.
            write(output / 'frozen-selection.json', dict(selected=selected,
                train_summary=train_summary, holdout_used_for_selection=False,
                comparator='market_soft_only_bound_not_parent_policy'))
    Q.verify_hashes(seals); Q.verify_hashes(prior['preserved'])
    write(output / 'episodes.json', dict(training=training, retrospective_validation=validation,
        quote_gap_10sec_sensitivity=sensitivity, sensitivity_used_for_selection=False))
    write(output / 'result.json', dict(source_seals=seals, preserved=prior['preserved'],
        census=source_census, excluded=exclusions, captured_main_panel=panel,
        captured_parent_enter_count=sum(r['parent_action'] == 'ENTER_NOW' for r in panel),
        captured_parent_win_rate=None, parent_improvement_identified=False,
        captured_native_summary={key: dict(
            train=captured_summary(panel, key, R.DAYS[:2]),
            retrospective_validation=captured_summary(panel, key, R.DAYS[2:])) for key in RECIPES},
        price_research_selected=selected, train_summary=train_summary,
        retrospective_validation_summary={day: {key: trial['metric'] for key, trial in trials.items()}
            for day, trials in validation.items()}, actual_prefix_checks=prefix_checks,
        quote_gap_10sec_sensitivity={day: {key: trial['metric'] for key, trial in trials.items()}
            for day, trials in sensitivity.items()}, sensitivity_used_for_selection=False,
        official_policy_candidate=None, research_hypothesis_count=len(RECIPES),
        dense_proxy_replays_main_setup=False, price_model=MODEL))
    return dict(captured=len(panel), excluded=len(exclusions), selected=selected,
        official_policy_candidate=None, runtime_effect=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    print(C.json.dumps(run(args.workspace, args.output)))


if __name__ == '__main__':
    main()
