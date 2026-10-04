"""Offline Samsung quote-recovery research; no runtime publisher or broker calls."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, deque
import json
import math
from pathlib import Path
from statistics import mean
import time

from src.engine.scalping import samsung_event_timing_research as E

R = E.R
RECIPES = ('bid_recovery', 'mid_recovery', 'sustained_bid', 'absorption_then_bid')
AUTHORITY = {**E.AUTHORITY,
    'primary_decision_metric': 'train_only_paired_quote_target_first_win_rate',
    'price_basis': 'past_ask_entry_observed_bid_exit_not_fill',
    'source_quality_gate': 'exact_retained_route_epoch_sequence_bounded_valid_quote_gaps',
    'consumer_scope': 'offline_quote_recovery_hypothesis_research',
    'benchmark_role': 'prior_trade_recovery_hypothesis_not_incumbent_main_policy'}


def write(path, body):
    value = {**{k:v for k,v in body.items() if k != 'content_sha256'}, **AUTHORITY}
    value['content_sha256'] = R.digest(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def write_cache(path, body):
    value = {**{k:v for k,v in body.items() if k != 'content_sha256'}, **AUTHORITY}
    value['content_sha256'] = R.digest(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(E.gzip.compress(json.dumps(value,separators=(',', ':'),allow_nan=False).encode(),
        compresslevel=1,mtime=0))


def prefixes(depth):
    broken, invalid = [0], [0]
    for i, row in enumerate(depth):
        prev = depth[i-1] if i else row
        connected = (not i or (row['continuous'] and row['ep'] == prev['ep']
            and row['seq'] == prev['seq']+1 and 0 <= row['t']-prev['t'] <= 10))
        broken.append(broken[-1] + (not connected))
        invalid.append(invalid[-1] + (not row['valid']))
    return broken, invalid


def quote_at(depth, times, at, epoch):
    # Distinct streams have no common sequence at equal receipt timestamps.
    i = bisect_left(times, at)-1
    if i < 0 or not depth[i]['valid'] or depth[i]['ep'] != epoch or at-times[i] > 1.5:
        return None
    return i


def select_anchors(events):
    """Reserve every first shock, independently of signals and outcomes."""
    selected, until = [], -math.inf
    for event in sorted(events, key=lambda e:(e['start'], e['shock_sequence'])):
        if event['start'] >= until:
            selected.append(event)
            until = event['start']+842
    return selected


def select_signal_events(events, recipe):
    """First received qualifying signal; reserve both comparison windows."""
    choices = [e for e in events if recipe in e['signals']]
    choices.sort(key=lambda e:(e['signals'][recipe]['t'],e['shock_sequence']))
    selected, until = [], -math.inf
    for event in choices:
        signal = event['signals'][recipe]
        baseline = event['baseline_signal']
        first = min(signal['t'],baseline['t']) if baseline else signal['t']
        if first < until:
            continue
        selected.append(event)
        until = max(signal['t'],baseline['t'] if baseline else signal['t'])+601.5
    return selected


def build_signals(cache):
    rows, depth = cache['rows'], cache['depth']
    dt = [r['t'] for r in depth]
    broken, invalid = prefixes(depth)
    output = []
    for original in cache['events']:
        event = {k:original[k] for k in ('id','day','start','start_index','epoch','shock_sequence')}
        event.update(signals={}, baseline_signal=original['signals'].get('recovery_only'),
            feature_resets=0, quote_observations=0, window_gap=None)
        low_bid = low_mid = mid_bid = mid_spread = None
        absorbed = sustained_at = None
        sustained_quotes, frames, flow = set(), deque(), deque()
        previous_q = None
        for i in range(event['start_index'], len(rows)):
            row = rows[i]
            if row['t'] > event['start']+180:
                break
            if not row['flow_valid'] or (i > event['start_index'] and not E.connected(rows[i-1],row,flow=True)):
                event['window_gap'] = 'trade_flow_discontinuity'
                break
            qi = quote_at(depth, dt, row['t'], event['epoch'])
            reset = qi is None or (previous_q is not None and
                (qi < previous_q or broken[qi+1] != broken[previous_q+1]
                 or invalid[qi+1] != invalid[previous_q+1]
                 or depth[qi]['t']-depth[previous_q]['t'] > 1.5))
            if reset:
                low_bid = low_mid = mid_bid = mid_spread = None
                absorbed = sustained_at = previous_q = None
                sustained_quotes.clear(); frames.clear(); flow.clear()
                event['feature_resets'] += 1
            if qi is None:
                continue
            q = depth[qi]
            event['quote_observations'] += 1
            bid, spread = q['bid'], q['ask']-q['bid']
            midpoint = (q['bid']+q['ask'])/2
            low_bid = min(low_bid,bid) if low_bid is not None else bid
            if low_mid is None or midpoint < low_mid:
                low_mid, mid_bid, mid_spread = midpoint, bid, spread
            if not frames or frames[-1]['index'] != qi:
                frames.append(dict(index=qi,t=q['t'],bid=bid))
            while frames and frames[0]['t'] < row['t']-6.5:
                frames.popleft()
            flow.append(row)
            while flow and flow[0]['t'] <= row['t']-5:
                flow.popleft()
            before = [f for f in frames if f['t'] <= row['t']-5]
            current = [f for f in frames if f['t'] > row['t']-5]
            sells = [r for r in flow if r['side']=='SELL']
            buys = [r for r in flow if r['side']=='BUY']
            if (before and len(current) >= 3 and len(sells) >= 3
                and all(f['bid'] == bid for f in [before[-1],*current])
                and sum(r['q'] for r in sells) > sum(r['q'] for r in buys)):
                if absorbed is None:
                    absorbed = dict(t=row['t'],bid=bid,sell_qty=sum(r['q'] for r in sells))
            if absorbed and bid < absorbed['bid']:
                absorbed = None
            recovered = bid >= low_bid+500
            if recovered:
                if sustained_at is None:
                    sustained_at = row['t']
                sustained_quotes.add(qi)
            else:
                sustained_at = None
                sustained_quotes.clear()
            persistent = (sustained_at is not None and row['t']-sustained_at >= 2
                and len(sustained_quotes) >= 3)
            qualifies = dict(bid_recovery=recovered,
                mid_recovery=midpoint >= low_mid+500 and bid > mid_bid and spread <= mid_spread,
                sustained_bid=persistent,
                absorption_then_bid=bool(absorbed and bid >= absorbed['bid']+500 and persistent))
            for recipe, eligible in qualifies.items():
                if eligible and recipe not in event['signals']:
                    event['signals'][recipe] = dict(index=i,t=row['t'],price=q['ask'],
                        quote_index=qi,bid=bid,ask=q['ask'],low_bid_asof=low_bid,
                        low_mid_asof=low_mid,spread=spread,
                        absorption_receipt=absorbed.copy() if absorbed else None)
            previous_q = qi
        if not event['quote_observations']:
            event['window_gap'] = event['window_gap'] or 'no_fresh_past_quote'
        if rows and rows[-1]['t'] < event['start']+180-1.5:
            event['window_gap'] = event['window_gap'] or 'retained_stream_end'
        output.append(event)
    return output


def context(cache):
    rows, depth = cache['rows'], cache['depth']
    times, dt = [r['t'] for r in rows], [r['t'] for r in depth]
    broken, invalid = prefixes(depth)
    valid = [i for i,r in enumerate(depth) if r['valid']]
    valid_times = [dt[i] for i in valid]
    ends = [0]*len(valid)
    for k in range(len(valid)-1,-1,-1):
        i = valid[k]
        if k+1 < len(valid):
            j = valid[k+1]
            connected = broken[j+1] == broken[i+1] and dt[j]-dt[i] <= 1.5
            ends[k] = ends[k+1] if connected else k
        else:
            ends[k] = k
    return dict(rows=rows,depth=depth,times=times,dt=dt,trade_ends=E.price_segments(rows),
        broken=broken,invalid=invalid,valid=valid,valid_times=valid_times,quote_ends=ends)


def entry_for(ctx, signal):
    if signal is None:
        return None
    row = ctx['rows'][signal['index']]
    qi = quote_at(ctx['depth'],ctx['dt'],signal['t'],row['ep'])
    if qi is None or not row['valid']:
        return None
    return dict(index=signal['index'],t=signal['t'],price=ctx['depth'][qi]['ask'],
        quote_index=qi,epoch=row['ep'])


def missing(status):
    return dict(binary=None,net=None,status=status,path_complete=False,strict_complete=False)


def endpoint_comparison(ctx, baseline, candidate, deadline):
    """Point-price diagnostic; missing interim quotes do not prove target order."""
    if baseline is None or candidate is None:
        return dict(status='entry_missing',comparable=False)
    if not all(E.full_path(ctx['rows'],ctx['times'],ctx['trade_ends'],e,deadline-e['t'])
               for e in (baseline,candidate)):
        return dict(status='trade_path_gap',comparable=False)
    qi = quote_at(ctx['depth'],ctx['dt'],deadline,baseline['epoch'])
    if qi is None or candidate['epoch'] != baseline['epoch']:
        return dict(status='endpoint_quote_missing',comparable=False)
    bid = ctx['depth'][qi]['bid']
    old, new = [(bid/e['price']-1)*100-E.COST for e in (baseline,candidate)]
    return dict(status='observed',comparable=True,baseline_net_cf=old,candidate_net_cf=new,
        delta=new-old,baseline_positive_cf=old>0,candidate_positive_cf=new>0,
        bid=bid,quote_t=ctx['depth'][qi]['t'],deadline=deadline,
        ask_change_pct=(candidate['price']/baseline['price']-1)*100,
        delay_sec=candidate['t']-baseline['t'],
        metric_role='fixed_time_quote_price_cf_not_target_first_or_realized_pnl')


def quote_label(ctx, entry, deadline):
    if entry is None:
        return missing('entry_missing')
    if deadline <= entry['t']:
        return missing('entry_after_common_deadline')
    qi = entry['quote_index']
    if (qi != quote_at(ctx['depth'],ctx['dt'],entry['t'],entry['epoch'])
        or entry['price'] != ctx['depth'][qi]['ask']
        or entry['epoch'] != ctx['rows'][entry['index']]['ep']
        or entry['t'] != ctx['rows'][entry['index']]['t']):
        raise ValueError('quote_entry_source_or_ask_binding_invalid')
    first = bisect_left(ctx['valid'],qi)
    last = bisect_right(ctx['valid_times'],deadline)-1
    raw_last = bisect_right(ctx['dt'],deadline)-1
    quote_complete = (last >= first and ctx['quote_ends'][first] >= last
        and deadline-ctx['valid_times'][last] <= 1.5
        and ctx['broken'][raw_last+1] == ctx['broken'][qi+1])
    trade_complete = E.full_path(ctx['rows'],ctx['times'],ctx['trade_ends'],entry,deadline-entry['t'])
    complete = quote_complete and trade_complete
    strict = complete and ctx['invalid'][raw_last+1] == ctx['invalid'][qi]
    excluded = (ctx['invalid'][raw_last+1]-ctx['invalid'][qi]) if last >= first else None
    end = min(last,ctx['quote_ends'][first])
    cutoff_trade = ctx['rows'][ctx['trade_ends'][entry['index']]]['t']
    endpoint, hit, maximum, minimum = None, None, -math.inf, math.inf
    for k in range(first,end+1):
        q = ctx['depth'][ctx['valid'][k]]
        if k > first and q['t'] <= entry['t']:
            continue
        observed = max(entry['t'],q['t'])
        if observed > cutoff_trade:
            break
        endpoint = (q,observed)
        gross = (q['bid']/entry['price']-1)*100
        maximum, minimum = max(maximum,gross-E.COST),min(minimum,gross-E.COST)
        if hit is None and (gross-E.COST >= .1 or gross <= -.7):
            hit = dict(binary=1 if gross-E.COST >= .1 else 0,net=gross-E.COST,
                status='target_first' if gross-E.COST >= .1 else 'stop_first',
                path_complete=complete,strict_complete=strict,exit_t=observed,exit_bid=q['bid'],
                excluded_quote_rows=excluded)
    extra = dict(max_net_cf=maximum if complete else None,min_net_cf=minimum if complete else None,
        deadline_net_cf=(endpoint[0]['bid']/entry['price']-1)*100-E.COST if complete and endpoint else None,
        entry_spread_pct=(entry['price']/ctx['depth'][qi]['bid']-1)*100)
    if hit:
        return {**hit,**extra}
    if not complete or endpoint is None:
        result = missing('quote_path_gap' if not quote_complete else 'trade_path_gap')
        result['excluded_quote_rows'] = excluded
        return result
    q, observed = endpoint
    return dict(binary=None,net=(q['bid']/entry['price']-1)*100-E.COST,status='neither',
        path_complete=True,strict_complete=strict,exit_t=observed,exit_bid=q['bid'],
        excluded_quote_rows=excluded,**extra)


def cached_label(ctx, entry, deadline):
    if entry is None:
        return missing('entry_missing')
    key = (entry['index'],entry['quote_index'],entry['price'],entry['t'],entry['epoch'],deadline)
    labels = ctx.setdefault('label_cache',{})
    if key not in labels:
        labels[key] = quote_label(ctx,entry,deadline)
    return labels[key]


def comparison_rows(cache, recipe, scope='anchors', ctx=None):
    ctx = context(cache) if ctx is None else ctx
    output = []
    events = (select_anchors(cache['quote_events']) if scope=='anchors'
        else select_signal_events(cache['quote_events'],recipe) if scope=='signals'
        else cache['quote_events'])
    for event in events:
        baseline = entry_for(ctx,event['baseline_signal'])
        signal = event['signals'].get(recipe)
        candidate = entry_for(ctx,signal)
        deadline = baseline['t']+600 if baseline else None
        labels = dict(baseline=cached_label(ctx,baseline,deadline) if deadline else missing('benchmark_signal_missing'),
            candidate=cached_label(ctx,candidate,deadline) if deadline else missing('benchmark_signal_missing'))
        own = cached_label(ctx,candidate,candidate['t']+600) if candidate else missing('entry_missing')
        output.append(dict(id=event['id'],day=event['day'],shock_t=event['start'],recipe=recipe,scope=scope,
            signal_status='observed' if signal else 'source_gap' if event['window_gap'] else 'not_reached',
            window_gap=event['window_gap'],feature_resets=event['feature_resets'],signal=signal,
            entries=dict(baseline=baseline,candidate=candidate),labels=labels,own_600=own,
            endpoint=endpoint_comparison(ctx,baseline,candidate,deadline) if deadline else
                dict(status='benchmark_signal_missing',comparable=False),
            deadline=deadline,native_identity=None))
    return output


def paired(comparisons, strict=False):
    key = 'strict_complete' if strict else 'path_complete'
    rows = [r for r in comparisons if all(r['labels'][arm][key] for arm in ('baseline','candidate'))]
    base = E.metric([r['labels']['baseline'] for r in rows])
    new = E.metric([r['labels']['candidate'] for r in rows])
    win_delta = new['win_rate']-base['win_rate'] if new['win_rate'] is not None and base['win_rate'] is not None else None
    return dict(comparable=len(rows),event_ids=[r['id'] for r in rows],baseline=base,candidate=new,
        win_rate_delta=win_delta,
        mean_net_delta=mean(r['labels']['candidate']['net']-r['labels']['baseline']['net'] for r in rows) if rows else None,
        common_deadline_delta=mean(r['labels']['candidate']['deadline_net_cf']-r['labels']['baseline']['deadline_net_cf'] for r in rows) if rows else None,
        gained_targets=sum(r['labels']['candidate']['binary']==1 and r['labels']['baseline']['binary']!=1 for r in rows),
        lost_targets=sum(r['labels']['candidate']['binary']!=1 and r['labels']['baseline']['binary']==1 for r in rows),
        mean_delay_sec=mean(r['entries']['candidate']['t']-r['entries']['baseline']['t'] for r in rows) if rows else None,
        same_ask_count=sum(r['entries']['candidate']['price']==r['entries']['baseline']['price'] for r in rows))


def endpoint_metric(rows):
    observed = [r for r in rows if r['endpoint']['comparable']]
    points = [r['endpoint'] for r in observed]
    return dict(comparable=len(observed),event_ids=[r['id'] for r in observed],
        states=dict(Counter(r['endpoint']['status'] for r in rows)),
        baseline_positive_cf=sum(p['baseline_positive_cf'] for p in points),
        candidate_positive_cf=sum(p['candidate_positive_cf'] for p in points),
        mean_baseline_net_cf=mean(p['baseline_net_cf'] for p in points) if points else None,
        mean_candidate_net_cf=mean(p['candidate_net_cf'] for p in points) if points else None,
        mean_delta=mean(p['delta'] for p in points) if points else None,
        mean_ask_change_pct=mean(p['ask_change_pct'] for p in points) if points else None,
        mean_delay_sec=mean(p['delay_sec'] for p in points) if points else None,
        target_first_support=False,used_for_selection=False)


def policy_comparison(rows):
    # Missing feature/outcome windows cannot masquerade as intentional vetoes.
    universe = [r for r in rows if r['labels']['baseline']['path_complete'] and
        (r['labels']['candidate']['path_complete'] or
         (r['signal_status']=='not_reached' and r['feature_resets']==0))]
    baseline = E.metric([r['labels']['baseline'] for r in universe])
    candidate = E.metric([r['labels']['candidate'] for r in universe
        if r['labels']['candidate']['path_complete']])
    delta = (candidate['win_rate']-baseline['win_rate']) if candidate['win_rate'] is not None and baseline['win_rate'] is not None else None
    return dict(universe=len(universe),admitted=candidate['full_paths'],
        not_admitted=len(universe)-candidate['full_paths'],excluded=len(rows)-len(universe),
        event_ids=[r['id'] for r in universe],baseline=baseline,candidate=candidate,
        win_rate_delta=delta,no_entry_is_not_zero_pnl=True)


def choose(training):
    candidates = [dict(recipe=r,paired=paired(training[r]),policy=policy_comparison(training[r])) for r in RECIPES]
    eligible = [c for c in candidates if c['paired']['comparable'] >= 3
        and c['policy']['baseline']['evaluable'] >= 3 and c['policy']['candidate']['evaluable'] >= 3
        and c['policy']['win_rate_delta'] > 0]
    best = max(eligible,key=lambda c:(c['policy']['candidate']['win_rate'],
        c['policy']['candidate']['wilson_lower'],c['policy']['candidate']['evaluable'],
        -RECIPES.index(c['recipe']))) if eligible else None
    return best,candidates


def verify_hashes(records):
    for name,sha in records.items():
        if R.P.file_sha(Path(name)) != sha:
            raise ValueError('sealed_file_changed:'+name)


def locked_price_context(depth):
    """Local producer accepts equality; this never certifies executable BBO."""
    rows = [dict(row) for row in depth]
    restored = 0
    for row in rows:
        if (not row['valid'] and R.finite(row['bid']) and row['bid'] > 0
            and row['bid'] == row['ask'] and 0 <= row['t']-row['ex'] <= 5):
            row['valid'] = True
            restored += 1
    return rows,restored


def prepare(root, source, output, include_locked=False):
    started = time.monotonic()
    source_sha = R.P.file_sha(source)
    prior = R.read(source)
    verify_hashes({**prior['source_manifest'],**prior['kernel_manifest']})
    sources = {**prior['source_manifest'],str(source):source_sha}
    kernels = {**prior['kernel_manifest'],str(Path(__file__).resolve()):R.P.file_sha(Path(__file__))}
    plan = root/'docs/proposals/samsung-quote-recovery-and-absorption-research-plan-2026-10-04.md'
    plan_sha = R.P.file_sha(plan)
    files, census = {}, {}
    for day,record in prior['files'].items():
        path = Path(record['path'])
        verify_hashes({str(path):record['sha256']})
        cache = E.read_cache(path)
        verify_hashes({str(path):record['sha256']})
        sources[str(path)] = record['sha256']
        depth, stats = R.stream_rows(root,day,'depth',sources)
        restored = 0
        if include_locked:
            depth,restored = locked_price_context(depth)
        cache['depth'] = depth
        cache['quote_events'] = build_signals(cache)
        out = output/(day+'.json.gz')
        write_cache(out,cache)
        files[day] = dict(path=str(out),sha256=R.P.file_sha(out))
        anchors = select_anchors(cache['quote_events'])
        census[day] = dict(depth=stats,locked_price_rows_restored=restored,
            events=len(cache['quote_events']),anchors=len(anchors),
            anchor_ids=[r['id'] for r in anchors],
            raw_signals={r:sum(r in e['signals'] for e in cache['quote_events']) for r in RECIPES},
            anchor_signals={r:sum(r in e['signals'] for e in anchors) for r in RECIPES},
            window_gaps=dict(Counter(e['window_gap'] for e in cache['quote_events'] if e['window_gap'])))
        print(day,'anchors',len(anchors),'signals',census[day]['anchor_signals'],flush=True)
    verify_hashes({**sources,**kernels,str(plan):plan_sha})
    write(output/'manifest.json',dict(files=files,census=census,source_manifest=sources,
        kernel_manifest=kernels,plan_path=str(plan),plan_sha256=plan_sha,
        locked_price_context=include_locked,locked_quotes_execution_verified=False,
        elapsed_sec=time.monotonic()-started))


def run(source, output):
    started = time.monotonic()
    source_sha = R.P.file_sha(source)
    manifest = R.read(source)
    seals = {**manifest['source_manifest'],**manifest['kernel_manifest'],
        manifest['plan_path']:manifest['plan_sha256'],str(source):source_sha}
    verify_hashes(seals)
    comparisons = {r:{} for r in RECIPES}
    signal_rows, overlapping = {r:{} for r in RECIPES},{r:{} for r in RECIPES}
    for day,record in manifest['files'].items():
        path = Path(record['path'])
        verify_hashes({str(path):record['sha256']})
        cache = E.read_cache(path)
        verify_hashes({str(path):record['sha256']})
        ctx = context(cache)
        for recipe in RECIPES:
            comparisons[recipe][day] = comparison_rows(cache,recipe,ctx=ctx)
            signal_rows[recipe][day] = comparison_rows(cache,recipe,'signals',ctx)
            # Descriptive only; overlapping events never augment fit support.
            raw = comparison_rows(cache,recipe,'all',ctx)
            overlapping[recipe][day] = dict(events=len(raw),
                signals=sum(r['signal_status']=='observed' for r in raw),
                own_600=E.metric([r['own_600'] for r in raw]),paired=paired(raw),
                endpoint=endpoint_metric(raw),
                independent_support=False,used_for_selection=False)
    folds = []
    for train_days,held in [(R.DAYS[:1],R.DAYS[1]),(R.DAYS[:2],R.DAYS[2])]:
        training = {r:[c for day in train_days for c in comparisons[r][day]] for r in RECIPES}
        chosen,candidates = choose(training)
        test = comparisons[chosen['recipe']][held] if chosen else []
        fold = dict(train_days=list(train_days),held_day=held,selected_recipe=chosen['recipe'] if chosen else None,
            selection_status='research_selected_not_runtime' if chosen else 'no_supported_paired_win_improvement',
            train_candidates=candidates,held=paired(test),held_strict=paired(test,True),held_policy=policy_comparison(test))
        folds.append(fold)
        print('fold',held,'selected',fold['selected_recipe'],'held',fold['held']['comparable'],flush=True)
    diagnostics = {r:{day:dict(anchors=len(rows),
        signals=dict(Counter(x['signal_status'] for x in rows)),
        endpoint=endpoint_metric(rows),
        own_600=E.metric([x['own_600'] for x in rows]),paired=paired(rows),strict_paired=paired(rows,True),
        policy=policy_comparison(rows),
        label_states={a:dict(Counter(x['labels'][a]['status'] for x in rows)) for a in ('baseline','candidate')},
        comparisons=rows) for day,rows in days.items()} for r,days in comparisons.items()}
    signal_diagnostics = {r:{day:dict(selected=len(rows),own_600=E.metric([x['own_600'] for x in rows]),
        endpoint=endpoint_metric(rows),
        paired=paired(rows),strict_paired=paired(rows,True),comparisons=rows)
        for day,rows in days.items()} for r,days in signal_rows.items()}
    signal_folds = []
    for train_days,held in [(R.DAYS[:1],R.DAYS[1]),(R.DAYS[:2],R.DAYS[2])]:
        training = {r:[c for day in train_days for c in signal_rows[r][day]] for r in RECIPES}
        chosen,candidates = choose(training)
        test = signal_rows[chosen['recipe']][held] if chosen else []
        signal_folds.append(dict(train_days=list(train_days),held_day=held,
            selected_recipe=chosen['recipe'] if chosen else None,train_candidates=candidates,
            held=paired(test),held_strict=paired(test,True),
            selection_role='supplemental_timing_only_no_no_signal_universe'))
    verify_hashes(seals)
    write(output/'result.json',dict(source_manifest_sha256=source_sha,census=manifest['census'],
        folds=folds,diagnostics=diagnostics,signal_diagnostics=signal_diagnostics,
        signal_folds=signal_folds,overlapping_diagnostics=overlapping,elapsed_sec=time.monotonic()-started,
        selection='train_only_win_rate_then_wilson_support_simplicity',cost_pct=E.COST,
        event_reservation_sec=842,signal_window_sec=180,persistence_sec=2,
        success_preservation_veto=False,exit_grid_executions=0,
        locked_price_context=manifest['locked_price_context'],locked_quotes_execution_verified=False,
        raw_invalid_depth_excluded_without_price_interpolation=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','run'))
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--include-locked-price-context',action='store_true')
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare(args.root.resolve(),args.source.resolve(),args.output.resolve(),args.include_locked_price_context)
    else:
        run(args.source.resolve(),args.output.resolve())


if __name__ == '__main__':
    main()
