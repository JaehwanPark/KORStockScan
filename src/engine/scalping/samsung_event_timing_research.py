"""Offline, paired Samsung event-timing research over retained observations."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, deque
from datetime import datetime
import gzip
import itertools
import json
import math
from pathlib import Path
from statistics import mean, median
import time

from src.engine.scalping import samsung_continuous_recovery_research as R

RECIPES = ('recovery_only', 'sell_decay', 'absorption', 'either')
COST = .33
AUTHORITY = {**R.AUTHORITY,
    'primary_decision_metric': 'paired_cost_bound_target_first_timing',
    'source_quality_gate': 'retained_exact_route_clock_epoch_sequence_full_comparable_paths',
    'sample_floor': 'three_research_outcomes_not_native_support',
    'native_promotion_support': False,
    'price_basis': 'observed_trade_price_counterfactual_not_fill',
    'consumer_scope': 'offline_event_timing_and_conditional_exit_research'}


def write(path, body):
    value = {**body, **AUTHORITY}
    value['content_sha256'] = R.digest(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def write_cache(path, value):
    body = {**value, **AUTHORITY}
    body['content_sha256'] = R.digest(body)
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(body, separators=(',', ':'), allow_nan=False).encode()
    path.write_bytes(gzip.compress(encoded, compresslevel=1, mtime=0))


def read_cache(path):
    with gzip.open(path, 'rt') as source:
        value = json.load(source)
    if R.digest({k:v for k,v in value.items() if k != 'content_sha256'}) != value['content_sha256']:
        raise ValueError('cache_content_seal_invalid')
    return value


def connected(previous, current, *, flow=False):
    flag = 'flow_valid' if flow else 'valid'
    return (current[flag] and previous[flag] and current['continuous']
        and current['ep'] == previous['ep'] and current['seq'] == previous['seq'] + 1
        and 0 <= current['t'] - previous['t'] <= 10)


def build_events(rows, day):
    """Every entry is the first eligible observation, with a past-only low."""
    times = [r['t'] for r in rows]
    buy, sell = [0.], [0.]
    for r in rows:
        buy.append(buy[-1] + (r['q'] if r['flow_valid'] and r['side'] == 'BUY' else 0))
        sell.append(sell[-1] + (r['q'] if r['flow_valid'] and r['side'] == 'SELL' else 0))
    history = deque(maxlen=60)
    segment_start = 0
    events, active = [], None
    for i, row in enumerate(rows):
        if not row['flow_valid'] or (i and not connected(rows[i-1], row, flow=True)):
            history.clear()
            active = None
            segment_start = i
        if not row['flow_valid']:
            continue
        if active and row['t'] - active['start'] > 60:
            active = None
        threshold = None
        if row['side'] == 'SELL' and len(history) >= 20:
            prior = sorted(history)
            threshold = max(prior[int((len(prior)-1)*.95)], 3 * median(prior))
        if active is None and threshold is not None and row['q'] >= threshold:
            active = dict(id=R.digest([day, '005930_AL', row['ep'], row['seq']])[:24],
                day=day, start=row['t'], start_index=i, epoch=row['ep'],
                shock_sequence=row['seq'], shock_price=row['p'], shock_qty=row['q'],
                past_only_threshold=threshold, signals={})
            events.append(active)
            low = row['p']
        if active:
            low = min(low, row['p'])
            recovery = row['p'] >= low + 500
            flow = dict(sell_decay=None, absorption=None)
            left = bisect_right(times, row['t'] - 10, 0, i+1)
            split = bisect_right(times, row['t'] - 5, 0, i+1)
            if (row['t'] - active['start'] >= 10 and left >= segment_start
                and split-left >= 2 and i+1-split >= 2 and split > segment_start):
                recent_sell = sell[i+1] - sell[split]
                prior_sell = sell[split] - sell[left]
                recent_buy = buy[i+1] - buy[split]
                flow = dict(sell_decay=recent_sell/prior_sell if prior_sell > 0 else None,
                    absorption=recent_sell > recent_buy and row['p'] >= rows[split-1]['p'])
            weakening = flow['sell_decay'] is not None and flow['sell_decay'] <= .75
            absorption = flow['absorption'] is True
            eligible = dict(recovery_only=recovery, sell_decay=recovery and weakening,
                absorption=recovery and absorption, either=recovery and (weakening or absorption))
            for recipe, qualifies in eligible.items():
                if qualifies and recipe not in active['signals']:
                    active['signals'][recipe] = dict(index=i, t=row['t'], price=row['p'],
                        low_asof=low, recovery_ticks=(row['p']-low)/500, **flow)
        history.append(row['q'])
    return events


def price_segments(rows):
    """Maximal source-valid suffix endpoint, independent of exit thresholds."""
    ends = [0] * len(rows)
    for i in range(len(rows)-1, -1, -1):
        if not rows[i]['valid']:
            ends[i] = i-1
        elif i+1 < len(rows) and connected(rows[i], rows[i+1]):
            ends[i] = ends[i+1]
        else:
            ends[i] = i
    return ends


def full_path(rows, times, ends, entry, horizon):
    if entry is None:
        return False
    i = entry['index']
    end = entry['t'] + horizon
    last = bisect_right(times, end) - 1
    return (last >= i and ends[i] >= last and end - times[last] <= 1.5)


def tick_label(rows, times, ends, entry, *, horizon=600, target=.1, stop=.7, cost=COST):
    if entry is None:
        return dict(binary=None, net=None, status='entry_missing', path_complete=False)
    i = entry['index']
    if (not rows[i]['valid'] or entry['t'] != rows[i]['t'] or entry['price'] != rows[i]['p']
        or not R.finite(cost) or cost < 0):
        raise ValueError('entry_price_or_source_invalid')
    complete = full_path(rows, times, ends, entry, horizon)
    last = min(ends[i], bisect_right(times, entry['t']+horizon)-1)
    upper = entry['price'] * (1 + (cost+target)/100)
    lower = entry['price'] * (1 - stop/100)
    for j in range(i+1, last+1):
        row = rows[j]
        win, loss = row['p'] >= upper, row['p'] <= lower
        if win or loss:
            return dict(binary=1 if win else 0, net=(row['p']/entry['price']-1)*100-cost,
                status='target_first' if win else 'stop_first', path_complete=complete,
                exit_t=row['t'], exit_price=row['p'], delay=row['t']-entry['t'])
    if not complete:
        return dict(binary=None, net=None, status='path_source_gap', path_complete=False)
    row = rows[last]
    return dict(binary=None, net=(row['p']/entry['price']-1)*100-cost,
        status='neither', path_complete=True, exit_t=row['t'], exit_price=row['p'], horizon=horizon)


def observed_entry(rows, times, ends, original, at):
    index = max(original['index'], bisect_left(times, at))
    if (index >= len(rows) or rows[index]['t']-at > 1.5
        or ends[original['index']] < index):
        return None
    return dict(index=index, t=rows[index]['t'], price=rows[index]['p'])


def arms(rows, times, ends, grid, signal):
    event = {k:signal[k] for k in ('index','t','price')}
    boundary = (math.floor(event['t']/60)+1)*60
    minute = observed_entry(rows, times, ends, event, boundary)
    confirmation = None
    for row in grid:
        if (event['t'] <= row['t'] <= event['t']+180
            and row['features'].get('past_up') is True
            and R.finite(row['features'].get('range_location'))
            and row['features']['range_location'] <= .35):
            # First price confirmation stays first even if its receipt is missing.
            confirmation = observed_entry(rows, times, ends, event, row['t'])
            break
    return dict(event_now=event, minute_wait=minute, bar_confirmation=confirmation)


def select_events(events, recipe, reserve=842):
    selected, until = [], -math.inf
    for event in sorted(events, key=lambda e:(e['start'], e['shock_sequence'])):
        signal = event['signals'].get(recipe)
        if signal is None or event['start'] < until:
            continue
        selected.append(event)
        until = event['start'] + reserve
    return selected


def wilson(wins, count):
    if not count:
        return None
    p, z = wins/count, 1.6448536269514722
    return (p+z*z/(2*count)-z*math.sqrt((p*(1-p)+z*z/(4*count))/count))/(1+z*z/count)


def metric(labels):
    complete = [r for r in labels if r['path_complete']]
    wins = sum(r['binary'] == 1 for r in complete)
    losses = sum(r['binary'] == 0 for r in complete)
    n = wins + losses
    return dict(selected=len(labels), full_paths=len(complete), wins=wins, losses=losses,
        evaluable=n, win_rate=wins/n if n else None, wilson_lower=wilson(wins,n),
        target_fraction=wins/len(complete) if complete else None,
        mean_net_cf=mean(r['net'] for r in complete) if complete else None,
        statuses=dict(Counter(r['status'] for r in labels)),
        censored_known_terminal=sum(not r['path_complete'] and r['binary'] is not None for r in labels))


def paired(comparisons, arm='minute_wait'):
    rows = [c for c in comparisons if c['labels']['event_now']['path_complete']
        and c['labels'][arm]['path_complete']]
    now = [r['labels']['event_now'] for r in rows]
    later = [r['labels'][arm] for r in rows]
    return dict(comparable=len(rows), event_ids=[r['id'] for r in rows],
        early=metric(now), later=metric(later),
        mean_net_delta=mean(a['net']-b['net'] for a,b in zip(now,later)) if rows else None,
        gained_targets=sum(a['binary']==1 and b['binary']!=1 for a,b in zip(now,later)),
        lost_targets=sum(a['binary']!=1 and b['binary']==1 for a,b in zip(now,later)),
        mean_wait_sec=mean(c['entries'][arm]['t']-c['entries']['event_now']['t'] for c in rows) if rows else None,
        mean_price_saved_pct=mean((c['entries'][arm]['price']/c['entries']['event_now']['price']-1)*100 for c in rows) if rows else None)


def comparisons_for(cache, recipe, reserve=842):
    output = []
    rows = cache['rows']
    times = [r['t'] for r in rows]
    ends = price_segments(rows)
    for event in select_events(cache['events'], recipe, reserve):
        entries = arms(rows, times, ends, cache['grid'], event['signals'][recipe])
        labels = {name:tick_label(rows,times,ends,entry) for name,entry in entries.items()}
        output.append(dict(id=event['id'], day=event['day'], shock_t=event['start'],
            recipe=recipe, signal=event['signals'][recipe], entries=entries, labels=labels,
            native_identity=None, research_event_does_not_create_native_support=True))
    return output


def choose_recipe(training):
    candidates = []
    for recipe in RECIPES:
        labels = [c['labels']['event_now'] for c in training[recipe]]
        m = metric(labels)
        candidates.append(dict(recipe=recipe, train=m, paired=paired(training[recipe])))
    eligible = [r for r in candidates if r['train']['evaluable'] >= 3]
    best = max(eligible, key=lambda r:(r['train']['wilson_lower'], r['train']['win_rate'],
        r['train']['evaluable'], -RECIPES.index(r['recipe']))) if eligible else None
    return best, candidates


def exit_gate(pair):
    reasons = []
    if pair['comparable'] < 3:
        reasons.append('paired_full_paths_below_three')
    if pair['mean_net_delta'] is None or pair['mean_net_delta'] <= 0:
        reasons.append('early_net_advantage_not_observed')
    if not (pair['gained_targets'] > 0 or (pair['early']['target_fraction'] is not None
        and pair['early']['target_fraction'] > pair['later']['target_fraction'])):
        reasons.append('early_target_advantage_not_observed')
    return dict(allowed=not reasons, reasons=reasons)


EXIT_SPECS = [dict(horizon=h, target=tp, stop=sl)
    for h,tp,sl in itertools.product((600,1200,1800),(.1,.2,.3),(.4,.7))]
BASE_EXIT = dict(horizon=600, target=.1, stop=.7)


def exit_population(cache, recipe):
    rows = cache['rows']
    times = [r['t'] for r in rows]
    ends = price_segments(rows)
    population = []
    for event in select_events(cache['events'], recipe, reserve=2042):
        entry = {k:event['signals'][recipe][k] for k in ('index','t','price')}
        complete = all(full_path(rows,times,ends,entry,h) for h in (600,1200,1800))
        labels = [tick_label(rows,times,ends,entry,**spec) if complete else None for spec in EXIT_SPECS]
        population.append(dict(id=event['id'], day=event['day'], entry=entry,
            full_30min_source=complete, labels=labels))
    return population


def exit_metric(population, index):
    labels = [r['labels'][index] for r in population if r['full_30min_source']]
    wins = sum(r['net'] > 0 for r in labels)
    n = len(labels)
    return dict(selected=len(population), common_source_count=n, positive=wins,
        nonpositive=n-wins, net_positive_cf_rate=wins/n if n else None,
        wilson_lower=wilson(wins,n), mean_net_cf=mean(r['net'] for r in labels) if n else None,
        exit_states=dict(Counter(r['status'] for r in labels)),
        metric_role='completed_virtual_price_exit_not_main_target_label_or_realized_pnl')


def run_exit(caches, recipe, train_days, held_day):
    populations = {day:exit_population(cache,recipe) for day,cache in caches.items()}
    training = [r for day in train_days for r in populations[day]]
    test = populations[held_day]
    candidates = [dict(spec=spec,train=exit_metric(training,i)) for i,spec in enumerate(EXIT_SPECS)]
    eligible = [(i,r) for i,r in enumerate(candidates) if r['train']['common_source_count'] >= 3]
    chosen = max(eligible, key=lambda item:(item[1]['train']['wilson_lower'],
        item[1]['train']['net_positive_cf_rate'], item[1]['train']['common_source_count'],
        -sum(item[1]['spec'][k] != BASE_EXIT[k] for k in BASE_EXIT), -item[0])) if eligible else None
    baseline = EXIT_SPECS.index(BASE_EXIT)
    return dict(recipe=recipe, train_days=list(train_days), held_day=held_day,
        candidates=candidates, selected_spec=chosen[1]['spec'] if chosen else None,
        selected_train=chosen[1]['train'] if chosen else None,
        held=exit_metric(test,chosen[0]) if chosen else None,
        baseline_train=exit_metric(training,baseline),baseline_held=exit_metric(test,baseline),
        populations=populations, common_30min_source_gate=True,
        study_opened_by_explored_held_timing_result=True)


def prepare(root, output):
    started = time.monotonic()
    prior_path = root/'tmp/samsung-continuous-recovery-research-20261003/source-02/projection.json'
    prior_sha = R.P.file_sha(prior_path)
    prior = R.read(prior_path)
    manifest = {**prior['source_manifest'], str(prior_path):prior_sha}
    for path, sha in prior['kernel_manifest'].items():
        if R.P.file_sha(Path(path)) != sha:
            raise ValueError('prior_research_kernel_changed')
    kernels = {str(Path(__file__).resolve()):R.P.file_sha(Path(__file__)), **prior['kernel_manifest']}
    files, census = {}, {}
    for day in R.DAYS:
        rows, stats = R.stream_rows(root,day,'trade',manifest)
        events = build_events(rows,day)
        grid = [r for r in prior['market'] if r['day']==day]
        path = output/(day+'.json.gz')
        write_cache(path, dict(day=day, rows=rows,events=events,grid=grid))
        files[day] = dict(path=str(path),sha256=R.P.file_sha(path))
        census[day] = dict(trade=stats,events=len(events),
            first_signals={r:sum(r in e['signals'] for e in events) for r in RECIPES})
        print(day, 'events',len(events), 'signals',census[day]['first_signals'],flush=True)
    for path, sha in {**manifest,**kernels}.items():
        if R.P.file_sha(Path(path)) != sha:
            raise ValueError('source_or_kernel_changed_during_prepare')
    write(output/'manifest.json',dict(files=files,source_manifest=manifest,kernel_manifest=kernels,
        census=census,parent_sha256=prior['parent_sha256'],elapsed_sec=time.monotonic()-started))


def run(source, output):
    started = time.monotonic()
    source_sha = R.P.file_sha(source)
    manifest = R.read(source)
    for path,sha in manifest['kernel_manifest'].items():
        if R.P.file_sha(Path(path)) != sha:
            raise ValueError('event_research_kernel_changed')
    caches = {}
    for day,record in manifest['files'].items():
        path = Path(record['path'])
        if R.P.file_sha(path) != record['sha256']:
            raise ValueError('event_cache_changed')
        caches[day] = read_cache(path)
        if R.P.file_sha(path) != record['sha256']:
            raise ValueError('event_cache_changed_during_read')
    comparisons = {recipe:{day:comparisons_for(cache,recipe) for day,cache in caches.items()}
        for recipe in RECIPES}
    folds, exits = [], []
    for train_days,held in [(R.DAYS[:1],R.DAYS[1]),(R.DAYS[:2],R.DAYS[2])]:
        training = {r:[c for day in train_days for c in comparisons[r][day]] for r in RECIPES}
        winner, candidates = choose_recipe(training)
        test = comparisons[winner['recipe']][held] if winner else []
        primary = paired(test)
        gate = exit_gate(primary)
        fold = dict(train_days=list(train_days),held_day=held,candidates=candidates,
            recipe=winner['recipe'] if winner else None,train=winner['train'] if winner else None,
            paired_held=primary,confirmation_held=paired(test,'bar_confirmation'),
            held_arm_metrics={arm:metric([c['labels'][arm] for c in test]) for arm in ('event_now','minute_wait','bar_confirmation')},
            exit_gate=gate,held_comparisons=test)
        if winner and len(train_days)==1:
            follow = comparisons[winner['recipe']][R.DAYS[2]]
            fold['unchanged_10_02'] = dict(paired=paired(follow),confirmation=paired(follow,'bar_confirmation'))
        folds.append(fold)
        if winner and gate['allowed']:
            exits.append(run_exit(caches,winner['recipe'],train_days,held))
        print('fold',held,'recipe',fold['recipe'],'paired',primary['comparable'],
            'delta',primary['mean_net_delta'],'exit',gate,flush=True)
    if R.P.file_sha(source) != source_sha:
        raise ValueError('source_manifest_changed_during_run')
    for path,sha in manifest['kernel_manifest'].items():
        if R.P.file_sha(Path(path)) != sha:
            raise ValueError('event_research_kernel_changed_during_run')
    write(output/'result.json',dict(source_manifest_sha256=source_sha,census=manifest['census'],
        kernel_manifest=manifest['kernel_manifest'],folds=folds,exit_studies=exits,
        all_recipe_diagnostics={recipe:{day:dict(early=metric([c['labels']['event_now'] for c in rows]),
            paired=paired(rows),confirmation=paired(rows,'bar_confirmation')) for day,rows in days.items()}
            for recipe,days in comparisons.items()},
        elapsed_sec=time.monotonic()-started,selection='train_only_wilson_win_rate_support_simplicity',
        cost_pct=COST,event_reservation_sec=842,exit_reservation_sec=2042,
        events_not_native_support=True,stage2_neither_binary_null=True,
        stage3_positive_virtual_exit_does_not_relabel_stage2=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','run'))
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source',type=Path)
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare(args.root.resolve(),args.output.resolve())
    else:
        if not args.source:
            parser.error('--source is required')
        run(args.source.resolve(),args.output.resolve())


if __name__ == '__main__':
    main()
