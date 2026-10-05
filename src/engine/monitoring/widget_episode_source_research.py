"""Finite existing-source Widget/Episode hypotheses; no fetch or live publisher.

Uses native normalized inputs and accepted durable captures, independently of
actual-fill promotion floors. All six definitions are fixed before outcomes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path

from src.engine.monitoring import family_policy_semantics as projection
from src.engine.monitoring import widget_paired_policy_replay as widget
from src.engine.monitoring import low_price_two_leg_tuning as episode
from src.engine.monitoring import low_price_two_leg_entry_spot_research as replay

DEFINITIONS = {
    'widget': ['confirmation_2_vs_3', 'initial_ENTRY_READY_only', 'entry_one_quote_later'],
    'episode': ['half_low_proximity', 'first_half_profile_window', 'profile_start_one_minute_later'],
}
CONTRACT = dict(metric_role='existing_source_price_pattern_diagnostic', decision_authority='report_only',
    window_policy='native_recorded_dates_chronological_calibration_and_historical_comparison',
    sample_floor='no_actual_fill_floor_for_diagnostic_future_date_required_for_promotion',
    primary_decision_metric='native_paired_cost_net_and_ev_with_diagnostic_win_rate',
    source_quality_gate='native_valid_captures_exact_BBO_or_sealed_completed_bar_prefix',
    forbidden_uses=['runtime_apply', 'orders', 'realized_profit', 'OFF_chain_enablement', 'unknown_as_zero'],
    success_retention_role='diagnostic_only', definition_count=6, future_validation_required=True)


def widget_research(report, root):
    results = []
    input_cache = {}
    for symbol, source in sorted(report['symbols'].items()):
        for session, policy in sorted((source.get('sessions') or {}).items()):
            original = (policy.get('paired_economics') or {}).get('study') or {}
            if not original:
                continue
            receipt = original.get('incumbent_receipt') or {}
            row = dict(symbol=symbol, session=session, cohort='samsung' if symbol == '005930' else 'non_samsung',
                       hypotheses={}, source_status='not_identifiable')
            results.append(row)
            if not widget.incumbent_valid(original):
                row['reason'] = 'exact_incumbent_recipe_missing'
                continue
            names = tuple(sorted((original.get('source_audit') or {}).get('source_hashes') or {}))
            cache_key = (symbol, names)
            if cache_key not in input_cache:
                paths = [root / name if not Path(name).is_absolute() else Path(name)
                         for name in names]
                input_cache[cache_key] = widget.load_inputs(paths, symbol=symbol,
                                                        target_date=date.fromisoformat(report['target_date']))
            inputs, audit = input_cache[cache_key]
            row['source_census'] = audit
            params = original['baseline_parameters']
            paths = []
            study = widget.build_study(inputs, symbol=symbol, session=session, parameters=params,
                baseline_confirmations=original['baseline_confirmations'], axis='confirmations', values=(2, 3),
                target_date=date.fromisoformat(report['target_date']), source_audit=audit, accepted_paths=paths)
            row.update(source_status=study['status'], source_gap_reasons=study.get('path_source_gaps'),
                       scale_in_source_census=study.get('scale_in_source_census'), independent_opportunities=len(paths))
            if study['status'] != 'observed':
                row['reason'] = study['status']
                continue
            base_confirm = original['baseline_confirmations']
            for definition in DEFINITIONS['widget']:
                pairs = []
                for path, gap in paths:
                    models = {}
                    for model, participation in [('base', .5), ('stress', .25)]:
                        control = widget._arm(path, confirmations=base_confirm, parameters=params, participation=participation)
                        candidate_path = path
                        if definition == 'initial_ENTRY_READY_only' and path[0]['raw_state'] != 'ENTRY_READY':
                            candidate_path = [dict(r, raw_state='WATCH') for r in path]
                        candidate = widget._arm(candidate_path,
                            confirmations=5-base_confirm if definition == 'confirmation_2_vs_3' else base_confirm,
                            parameters=params, participation=participation,
                            entry_quote_delay=int(definition == 'entry_one_quote_later'))
                        models[model] = dict(baseline=control, candidate=candidate)
                    pairs.append(dict(source_date=widget._stamp(path[0]['observed_at']).date().isoformat(),
                        raw_first_at=path[0]['observed_at'], path_hash=widget.digest(path), source_gap=gap, models=models))
                row['hypotheses'][definition] = widget_pair_summary(pairs)
    return dict(rows=results, disposition_counts=dict(Counter(r['source_status'] for r in results)))


def widget_pair_summary(pairs):
    dates = sorted({r['source_date'] for r in pairs})
    windows = ({'calibration': dates[:-1], 'historical_comparison': dates[-1:]}
               if len(dates) >= 2 else {'calibration': dates})
    result = dict(source_dates=dates, future_validation='not_observed', windows={})
    for model in ('base', 'stress'):
        result['windows'][model] = {}
        for name, days in windows.items():
            all_rows = [p['models'][model] for p in pairs if p['source_date'] in days]
            rows = [p for p in all_rows if all(p[a]['status'] in {'completed_cf', 'no_entry'} for a in ('baseline', 'candidate'))]
            metrics = {}
            for arm in ('baseline', 'candidate'):
                outcomes = [p[arm] for p in rows]
                completed = [r for r in outcomes if r['status'] == 'completed_cf']
                metrics[arm] = dict(selected=len(completed),
                    wins=sum(r['net_return_pct'] > 0 for r in completed),
                    win_rate_pct=100*sum(r['net_return_pct'] > 0 for r in completed)/len(completed) if completed else None,
                    net_krw=sum(r['net_pnl_krw'] for r in outcomes) if rows else None,
                    ev_pct=sum(r.get('opportunity_return_pct', 0) for r in outcomes)/len(rows) if rows else None,
                    no_entry=len(outcomes)-len(completed))
            result['windows'][model][name] = dict(all_pairs=len(all_rows), comparable=len(rows),
                unknown=len(all_rows)-len(rows), outcomes=dict(Counter(
                    f"{p['baseline']['status']}|{p['candidate']['status']}" for p in all_rows)), **metrics)
    return result


def episode_window_coverage(candidate, contexts, days):
    """Count native valid lookback features at every intended signal clock.

    A partial saved prefix with no signal cannot prove an empty full window.
    Outcome calculations remain diagnostic until both arms cover that window.
    """
    rows = []
    for day in days:
        expected = set(range(candidate.scan_start_minute, candidate.scan_end_minute + 1))
        features = contexts[day].iter_window_features(candidate.lookback_bars,
            candidate.scan_start_minute, candidate.scan_end_minute)
        observed = {f.timestamp.hour * 60 + f.timestamp.minute for f in features
                    if f.timestamp.second == f.timestamp.microsecond == 0}
        missing = sorted(expected - observed)
        rows.append(dict(source_date=day.isoformat(), expected_signal_clocks=len(expected),
            observed_signal_clocks=len(expected & observed), missing_signal_clocks=missing,
            complete=not missing))
    return dict(complete=bool(rows) and all(r['complete'] for r in rows), dates=rows)


def episode_research(report, captures_by_date):
    from src.trading.low_price_two_leg.profiles import profiles_for_target_date
    target = date.fromisoformat(report['target_date'])
    profiles = profiles_for_target_date(target)
    binding = report['source_runtime_policy_binding']
    rows = []
    for pid, live in sorted(profiles.items()):
        captures = [body for bodies in captures_by_date.values() for body in bodies if body['profile_id'] == pid and body.get('execution_mode') == 'real']
        row = dict(profile_id=pid, symbol=live.symbol, session=live.session,
            cohort='samsung' if live.symbol == '005930' else 'non_samsung', observations=len(captures),
            action_counts=dict(Counter(b['action'] for b in captures)), hypotheses={}, status='not_identifiable')
        rows.append(row)
        if binding.get('status') != 'ready' or pid not in (binding.get('policies') or {}):
            row['reason'] = 'exact_incumbent_recipe_missing'
            continue
        p = binding['policies'][pid]
        if p.get('quantity') != 20:
            row['reason'] = 'unsupported_quantity_recipe'
            continue
        original = replace(live.policy, **{k: p[k] for k in ('rolling_high_drawdown_pct',
            'rolling_low_proximity_pct', 'lookback_bars', 'entry_valid_completed_bars', 'target_ticks')})
        base = replay.baseline_candidate(replace(live, policy=original))
        bars, conflicts = {}, set()
        invalid_bars = 0
        for body in captures:
            source = body.get('bar_source') or {}
            values = source.get('completed_bars')
            if source.get('source_ok') is not True or not isinstance(values, list):
                continue
            encoded = json.dumps(values, sort_keys=True, default=str).encode()
            if hashlib.sha256(encoded).hexdigest() != source.get('content_sha256'):
                invalid_bars += len(values)
                continue
            observed = datetime.fromisoformat(body['observed_at_kst'])
            for value in values:
                try:
                    at = datetime.fromisoformat(value['timestamp'])
                    if at.tzinfo is None or at + timedelta(minutes=1) > observed or at.date().isoformat() not in captures_by_date:
                        raise ValueError('bar_not_completed_in_registered_date')
                    bar = replay.Bar(at, *(int(value[k]) for k in ('open_price', 'high_price', 'low_price', 'close_price')))
                    if min(bar.open_price, bar.high_price, bar.low_price, bar.close_price) <= 0 or not (
                        bar.low_price <= min(bar.open_price, bar.close_price) <= max(bar.open_price, bar.close_price) <= bar.high_price):
                        raise ValueError('bar_price_invalid')
                    if at in bars and bars[at] != bar:
                        conflicts.add(at)
                    bars[at] = bar
                except (ValueError, KeyError, TypeError):
                    invalid_bars += 1
        row.update(unique_bars=len(bars), conflicting_bars=len(conflicts), invalid_bars=invalid_bars,
            feature_presence={k: sum((b.get('signal_features') or {}).get(k) is not None for b in captures)
                              for k in ('drawdown_pct', 'near_low_pct', 'signal_bar', 'runtime_policy_hash')})
        if conflicts or invalid_bars:
            row['reason'] = 'completed_bar_contract_invalid'
            continue
        if not bars:
            row['reason'] = 'saved_completed_bars_missing'
            continue
        contexts = replay.build_day_contexts(list(bars.values()))
        days = sorted(contexts)
        row['registered_dates_without_saved_bars'] = sorted(set(captures_by_date) - {d.isoformat() for d in days})
        definitions = dict(half_low_proximity=replace(base, rolling_low_proximity_pct=base.rolling_low_proximity_pct/2),
            first_half_profile_window=replace(base, scan_end_minute=(base.scan_start_minute+base.scan_end_minute)//2),
            profile_start_one_minute_later=replace(base, scan_start_minute=min(base.scan_start_minute+1, base.scan_end_minute)))
        names = ('calibration', 'historical_comparison') if len(days) >= 2 else ('calibration',)
        windows = [days[:-1], days[-1:]] if len(days) >= 2 else [days]
        control = replay._evaluate_candidate_windows(base, contexts, windows, include_episodes=True)
        for definition, candidate in definitions.items():
            outcomes = replay._evaluate_candidate_windows(candidate, contexts, windows, include_episodes=True)
            compared_windows = {}
            for name, dates, old, new in zip(names, windows, control, outcomes):
                coverage = {arm: episode_window_coverage(params, contexts, dates)
                            for arm, params in [('baseline', base), ('candidate', candidate)]}
                comparison = replay.paired_economics(old, new)
                complete = all(c['complete'] for c in coverage.values())
                if not complete:
                    comparison.update(comparable_observation_window=False,
                        economic_comparison_status='source_window_incomplete',
                        net_profit_uplift_krw_per_observation_day=None, ev_uplift_pct_point=None,
                        net_profit_improved=False)
                compared_windows[name] = dict(baseline=episode_metrics(old), candidate=episode_metrics(new),
                    source_window_coverage=coverage, comparison=comparison,
                    comparison_use='complete_observation_window' if complete else 'observed_prefix_diagnostic_only')
            row['hypotheses'][definition] = dict(baseline_parameters=base.public(), candidate_parameters=candidate.public(),
                source_dates=[d.isoformat() for d in days], windows=compared_windows,
                future_validation='not_observed', held_results='censored_not_zero', runtime_apply_allowed=False)
        row['status'] = 'report_only_evaluated'
    return dict(rows=rows, disposition_counts=dict(Counter(r['status'] for r in rows)),
                actual_fill_floor_used_for_research=False)


def episode_metrics(outcome):
    legs = [leg for item in outcome.get('episodes') or [] for leg in item.get('legs') or []]
    completed = [leg for leg in legs if leg.get('status') == 'COMPLETE']
    winners = sum(leg['net_profit_pct'] > 0 for leg in completed)
    return dict(episode._economic_brief(outcome), confirmed_wins=winners,
        confirmed_leg_count=len(completed), win_rate_pct=100*winners/len(completed) if completed else None,
        unknown_legs=sum(leg.get('status') == 'HELD' for leg in legs), win_rate_role='diagnostic_only')


def run(root, day, output):
    root, output = Path(root), Path(output)
    widget_path = root / f'data/report/widget_auto_trade_policy_calibration/widget_auto_trade_policy_calibration_{day}.json'
    episode_path = root / f'data/report/low_price_two_leg_tuning/low_price_two_leg_tuning_{day}.json'
    hashes = {str(p): projection.file_sha(p) for p in (widget_path, episode_path)}
    report_bytes = {str(p): p.read_bytes() for p in (widget_path, episode_path)}
    if any(hashlib.sha256(raw).hexdigest() != hashes[p] for p, raw in report_bytes.items()):
        raise ValueError('semantic_generation_changed_during_read')
    w, e = json.loads(report_bytes[str(widget_path)]), json.loads(report_bytes[str(episode_path)])
    if w.get('target_date') != day or e.get('target_date') != day:
        raise ValueError('family_research_source_date_invalid')
    captures, manifests = {}, {}
    dates = e['clean_baseline_window']['available_actual_observation_dates']
    if any(d < '2026-06-05' or d > day for d in dates):
        raise ValueError('family_research_date_scope_invalid')
    for source_date in dates:
        bodies = []
        manifest = episode.durable_observation_manifest(source_date,
            root / 'data/report/observation_source_quality_audit', accepted_observations=bodies)
        manifests[source_date] = manifest
        captures[source_date] = bodies if manifest.get('status') in {'pass', 'partial', 'valid_empty'} else []
    value = dict(schema='widget_episode_existing_source_research_v1', source_date=day,
        metric_contract=CONTRACT, definitions=DEFINITIONS, report_seals=hashes,
        runtime_effect=False, actual_order_submitted=False, allowed_runtime_apply=False,
        widget=widget_research(w, root), episode=episode_research(e, captures), source_manifests=manifests,
        new_independent_source_date=False, selection='research_only_no_policy_published',
        kernel_seals={str(Path(p).resolve()): projection.file_sha(p)
                      for p in (__file__, projection.__file__, widget.__file__, episode.__file__, replay.__file__)})
    if any(projection.file_sha(p) != sha for p, sha in hashes.items()):
        raise ValueError('semantic_generation_changed_during_read')
    output.mkdir(parents=True, exist_ok=False)
    snapshots = output / 'source_reports'
    snapshots.mkdir()
    value['report_snapshots'] = {}
    for p, raw in report_bytes.items():
        snapshot = snapshots / Path(p).name
        snapshot.write_bytes(raw)
        value['report_snapshots'][p] = dict(path=str(snapshot.resolve()), sha256=hashes[p])
    value = projection.seal(value)
    from src.utils.jsonl_io import write_json_object_generation_safe
    write_json_object_generation_safe(output / 'result.json', value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--date', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.date, args.output)
    print(json.dumps({f: result[f]['disposition_counts'] for f in ('widget', 'episode')}))


if __name__ == '__main__':
    main()
