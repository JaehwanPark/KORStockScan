"""Offline retained-source Samsung hypotheses; no live consumers or publication."""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, deque
from datetime import datetime
import itertools
import json
import math
from pathlib import Path
from statistics import mean
import time
from zoneinfo import ZoneInfo

from src.engine.scalping import samsung_quote_recovery_research as Q

E, R = Q.E, Q.R
FAMILIES = ('absorption', 'sell_decay', 'flow_flip', 'range_retest',
    'range_reclaim', 'vwap_reclaim', 'trend_pullback', 'breakout',
    'book_support', 'bid_replenish', 'ask_depletion', 'book_flip')
WINDOWS = (60, 180, 300, 900, 1800)
HORIZONS = (600, 1200, 1800, 3600)
REGIONS = ('all', 'open', 'day')
AUTHORITY = {**Q.AUTHORITY,
    'consumer_scope': 'offline_retained_source_pattern_campaign',
    'benchmark_role': 'unconditional_clock_price_reference_not_incumbent_main',
    'primary_decision_metric': 'train_only_target_first_conditional_win_rate',
    'price_basis': 'nonlocked_positive_quantity_ask_entry_bid_exit_price_cf_not_fill',
    'source_quality_gate': 'causal_exact_cache_epoch_sequence_prefix_until_terminal',
    'sample_floor': 'three_research_binary_outcomes_not_native_promotion_support'}


def write(path, body):
    value = {**{k:v for k,v in body.items() if k != 'content_sha256'}, **AUTHORITY}
    value['content_sha256'] = R.digest(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def load_manifest(source):
    sha = R.P.file_sha(source)
    manifest = R.read(source)
    seals = {**manifest['records'],**{r['path']:r['sha256'] for r in manifest['files'].values()},str(source):sha}
    Q.verify_hashes(seals)
    return manifest,seals,sha


class PriceTree:
    """Observed-price range extrema and chronological first boundary search."""
    def __init__(self, values):
        self.n = len(values)
        self.size = 1 << max(0, (self.n-1).bit_length())
        self.lo = [math.inf]*(2*self.size)
        self.hi = [-math.inf]*(2*self.size)
        for i, value in enumerate(values):
            self.lo[self.size+i] = self.hi[self.size+i] = value
        for i in range(self.size-1, 0, -1):
            self.lo[i] = min(self.lo[2*i], self.lo[2*i+1])
            self.hi[i] = max(self.hi[2*i], self.hi[2*i+1])

    def extrema(self, left, right):
        left, right = left+self.size, right+self.size
        low, high = math.inf, -math.inf
        while left < right:
            if left & 1:
                low, high = min(low, self.lo[left]), max(high, self.hi[left]); left += 1
            if right & 1:
                right -= 1; low, high = min(low, self.lo[right]), max(high, self.hi[right])
            left //= 2; right //= 2
        return low, high

    def first(self, left, right, target, stop):
        def visit(node, start, end):
            if end <= left or start >= right or (self.hi[node] < target and self.lo[node] > stop):
                return None
            if end-start == 1:
                return start
            mid = (start+end)//2
            found = visit(node*2, start, mid)
            return found if found is not None else visit(node*2+1, mid, end)
        return visit(1, 0, self.size)


def actionable(q):
    return bool(q['valid'] and 0 < q['bid'] < q['ask']
        and R.finite(q['bq']) and q['bq'] > 0 and R.finite(q['aq']) and q['aq'] > 0)


def campaign_context(cache, max_quote_gap=1.5):
    if not R.finite(max_quote_gap) or not 0 < max_quote_gap <= 10:
        raise ValueError('invalid_offline_quote_gap')
    ctx = Q.context(cache)
    # Invalid intervening receipts are evidence loss even when the surrounding
    # valid observations have consecutive clocks. Never skip them in a label.
    ends = [0]*len(ctx['valid'])
    for k in range(len(ends)-1, -1, -1):
        i = ctx['valid'][k]
        if k+1 < len(ends):
            j = ctx['valid'][k+1]
            connected = (ctx['broken'][j+1] == ctx['broken'][i+1]
                and ctx['invalid'][j+1] == ctx['invalid'][i+1]
                and 0 <= ctx['dt'][j]-ctx['dt'][i] <= max_quote_gap)
            ends[k] = ends[k+1] if connected else k
        else:
            ends[k] = k
    ctx['quote_ends'] = ends
    use = [i for i, q in enumerate(ctx['depth']) if actionable(q)]
    ctx.update(max_quote_gap=max_quote_gap, actionable=use, actionable_times=[ctx['depth'][i]['t'] for i in use],
        tree=PriceTree([ctx['depth'][i]['bid'] for i in use]))
    return ctx


def label(ctx, signal, horizon=600, target_net=.1, latency=0., cost_pct=E.COST):
    """An observed absorbing terminal needs a valid prefix, not a later horizon."""
    if (not R.finite(cost_pct) or cost_pct<0 or not R.finite(horizon) or horizon<=0
        or not R.finite(target_net) or target_net<0 or not R.finite(latency) or latency<0):
        raise ValueError('invalid_research_price_model')
    if signal is None:
        return dict(binary=None, net=None, status='entry_missing', complete=False)
    entry = Q.entry_for(ctx, signal)
    if entry is None or not actionable(ctx['depth'][entry['quote_index']]):
        return dict(binary=None, net=None, status='nonactionable_entry', complete=False)
    decision = entry.copy()
    if latency:
        i = bisect_left(ctx['times'], decision['t']+latency)
        if (i >= len(ctx['rows']) or i > ctx['trade_ends'][decision['index']]
            or ctx['rows'][i]['t']-(decision['t']+latency) > 1.5):
            return dict(binary=None, net=None, status='latency_trade_gap', complete=False)
        entry = Q.entry_for(ctx, dict(index=i, t=ctx['rows'][i]['t']))
        if entry is None or not actionable(ctx['depth'][entry['quote_index']]):
            return dict(binary=None, net=None, status='latency_quote_unavailable', complete=False)
        # A new price cannot bridge a quote path break during the decision delay.
        k0 = bisect_left(ctx['valid'], decision['quote_index'])
        k1 = bisect_left(ctx['valid'], entry['quote_index'])
        if k1 > ctx['quote_ends'][k0] or entry['epoch'] != decision['epoch']:
            return dict(binary=None, net=None, status='latency_quote_gap', complete=False)
    qi = entry['quote_index']
    valid_pos = bisect_left(ctx['valid'], qi)
    quote_end = ctx['valid'][ctx['quote_ends'][valid_pos]]
    trade_end = ctx['trade_ends'][entry['index']]
    deadline = entry['t']+horizon
    cutoff = min(deadline, ctx['depth'][quote_end]['t'], ctx['rows'][trade_end]['t'])
    left = bisect_right(ctx['actionable_times'], entry['t'])
    right = bisect_right(ctx['actionable_times'], cutoff)
    target = entry['price']*(1+(cost_pct+target_net)/100)
    stop = entry['price']*.993
    hit = ctx['tree'].first(left, right, target, stop)
    common = dict(entry=entry, decision=decision, horizon=horizon, target_net=target_net,
        cost_pct=cost_pct, native_identity=None, latency_sec=latency,
        max_observed_quote_gap_sec=ctx['max_quote_gap'],
        quote_gap_sensitivity=ctx['max_quote_gap'] != 1.5)
    if hit is not None:
        q = ctx['depth'][ctx['actionable'][hit]]
        won = q['bid'] >= target
        return dict(binary=int(won), net=(q['bid']/entry['price']-1)*100-cost_pct,
            status='target_first' if won else 'stop_first', complete=True,
            exit_t=q['t'], exit_bid=q['bid'], after_terminal_gap_ignored=deadline > cutoff,
            **common)
    # For a time exit require both continuous streams through the deadline and a
    # fresh, actually nonlocked endpoint. An old actionable bid is not executable.
    raw_last = bisect_right(ctx['dt'], deadline)-1
    end_qi = Q.quote_at(ctx['depth'], ctx['dt'], deadline, entry['epoch'])
    full = (E.full_path(ctx['rows'], ctx['times'], ctx['trade_ends'], entry, horizon)
        and deadline-ctx['depth'][quote_end]['t'] <= 1.5
        and ctx['broken'][raw_last+1] == ctx['broken'][qi+1]
        and ctx['invalid'][raw_last+1] == ctx['invalid'][qi+1])
    if not full:
        return dict(binary=None, net=None, status='censored_before_terminal', complete=False, **common)
    if end_qi is None or not actionable(ctx['depth'][end_qi]):
        return dict(binary=None, net=None, status='time_exit_nonactionable', complete=False, **common)
    q = ctx['depth'][end_qi]
    return dict(binary=None, net=(q['bid']/entry['price']-1)*100-cost_pct,
        status='neither', complete=True, exit_t=deadline, exit_bid=q['bid'],
        after_terminal_gap_ignored=False, **common)


def feature_rows(cache, books=None):
    """First causal source-valid trade receipt per second; no future extrema."""
    rows, depth = cache['rows'], cache['depth']
    times, dt = [r['t'] for r in rows], [q['t'] for q in depth]
    buy, sell, sells, volume, notional = [[0.] for _ in range(5)]
    for r in rows:
        good = r['flow_valid']
        buy.append(buy[-1]+(r['q'] if good and r['side']=='BUY' else 0))
        sell.append(sell[-1]+(r['q'] if good and r['side']=='SELL' else 0))
        sells.append(sells[-1]+int(good and r['side']=='SELL'))
        volume.append(volume[-1]+(r['q'] if good else 0))
        notional.append(notional[-1]+(r['q']*r['p'] if good else 0))
    lookbacks = sorted(set(WINDOWS)|{w//2 for w in WINDOWS})
    lows = {w:deque() for w in lookbacks}; highs = {w:deque() for w in lookbacks}
    retests = {}; last_q = -1; segment_i = 0; quote_start = None
    hold_t = None; held_bid = None; hold_quotes = 0; last_second = None; previous = None
    output = []; book_history = deque()

    def reset():
        nonlocal quote_start, hold_t, held_bid, hold_quotes, previous
        for q in (*lows.values(), *highs.values()): q.clear()
        retests.clear(); quote_start = hold_t = held_bid = previous = None; hold_quotes = 0
        book_history.clear()

    for i, row in enumerate(rows):
        if not row['flow_valid'] or (i and not E.connected(rows[i-1], row, flow=True)):
            segment_i = i; reset()
        if not row['flow_valid']:
            continue
        qi = Q.quote_at(depth, dt, row['t'], row['ep'])
        if qi is None:
            reset(); last_q = bisect_left(dt, row['t'])-1
            continue
        # Consume every intervening depth receipt, so bad clocks/sequence cannot
        # disappear between 1-second observations.
        for k in range(last_q+1, qi+1):
            q = depth[k]
            if (not q['valid'] or q['ep'] != row['ep'] or (k and
                (not q['continuous'] or q['ep'] != depth[k-1]['ep']
                 or q['seq'] != depth[k-1]['seq']+1 or not 0 <= q['t']-depth[k-1]['t'] <= 1.5))):
                reset()
            if not q['valid'] or q['ep'] != row['ep']:
                continue
            if quote_start is None: quote_start = q['t']
            book = books.get((q['ep'],q['seq'])) if books else None
            book_history.append((k,book))
            while book_history and depth[book_history[0][0]]['t'] < q['t']-6.5:
                book_history.popleft()
            if held_bid != q['bid']:
                hold_t, held_bid, hold_quotes = q['t'], q['bid'], 1
            else:
                hold_quotes += 1
            for w in lookbacks:
                while lows[w] and depth[lows[w][-1]]['bid'] > q['bid']: lows[w].pop()
                while highs[w] and depth[highs[w][-1]]['bid'] < q['bid']: highs[w].pop()
                lows[w].append(k); highs[w].append(k)
                while lows[w] and depth[lows[w][0]]['t'] <= q['t']-w: lows[w].popleft()
                while highs[w] and depth[highs[w][0]]['t'] <= q['t']-w: highs[w].popleft()
            for w in WINDOWS:
                low = depth[lows[w][0]]['bid']
                state = retests.get(w)
                if state is None or state['low'] != low:
                    state = retests[w] = dict(low=low, first=q['t'], away=False, confirmed=False)
                if q['bid'] >= low+500: state['away'] = True
                if state['away'] and q['bid']==low and q['t']-state['first']>=10:
                    state['confirmed'] = True
        last_q = qi
        q = depth[qi]
        if (last_second == math.floor(row['t']) or not actionable(q) or quote_start is None):
            continue
        last_second = math.floor(row['t'])
        left5 = bisect_right(times, row['t']-5, 0, i+1)
        left10 = bisect_right(times, row['t']-10, 0, i+1)
        left20 = bisect_right(times, row['t']-20, 0, i+1)
        if row['t']-times[segment_i] < 20 or left20 < segment_i:
            continue
        bv, sv = buy[i+1]-buy[left5], sell[i+1]-sell[left5]
        pb, ps = buy[left5]-buy[left10], sell[left5]-sell[left10]
        recent_volume, prior_volume = volume[i+1]-volume[left10], volume[left10]-volume[left20]
        hour = datetime.fromtimestamp(row['t'], ZoneInfo('Asia/Seoul')).hour
        f = dict(index=i, t=row['t'], quote_index=qi, ep=row['ep'], price=q['ask'],
            bid=q['bid'], ask=q['ask'], spread=q['ask']-q['bid'], hour=hour,
            hold=row['t']-hold_t, hold_quotes=hold_quotes, sell_count=sells[i+1]-sells[left5],
            sell_dominant=sv>bv, buy_share=bv/(bv+sv) if bv+sv else None,
            prior_buy_share=pb/(pb+ps) if pb+ps else None,
            sell_decay=sv/ps if ps else None,
            volume_acceleration=recent_volume/prior_volume if prior_volume else None,
            book_ratio=q['bq']/q['aq'], windows={})
        current_book = books.get((q['ep'],q['seq'])) if books else None
        before_book = [p for p in book_history if depth[p[0]]['t'] <= row['t']-5]
        prior_book = before_book[-1] if before_book else None
        old_q = depth[prior_book[0]] if prior_book else None
        old_book = prior_book[1] if prior_book else None
        valid_books = (current_book and old_book and all(p[1] is not None for p in book_history
            if depth[p[0]]['t'] >= old_q['t']))
        f.update(depth_ratio=current_book['bid_sum']/current_book['ask_sum'] if current_book else None,
            prior_depth_ratio=old_book['bid_sum']/old_book['ask_sum'] if valid_books else None,
            bid_replenishment=q['bq']/old_q['bq'] if valid_books and q['bid']==old_q['bid'] and old_q['bq']>0 else None,
            ask_depletion=q['aq']/old_q['aq'] if valid_books and old_q['aq']>0
                and all(depth[p[0]]['ask']==q['ask'] for p in book_history if depth[p[0]]['t']>=old_q['t']) else None)
        for w in WINDOWS:
            while lows[w] and depth[lows[w][0]]['t'] <= row['t']-w: lows[w].popleft()
            while highs[w] and depth[highs[w][0]]['t'] <= row['t']-w: highs[w].popleft()
            half = w//2
            while lows[half] and depth[lows[half][0]]['t'] <= row['t']-half: lows[half].popleft()
            if row['t']-quote_start < w or row['t']-times[segment_i] < w or not lows[w] or not lows[half]:
                continue
            left = bisect_right(times, row['t']-w, 0, i+1)
            vol = volume[i+1]-volume[left]
            vwap = (notional[i+1]-notional[left])/vol if vol else None
            low, high, half_low = depth[lows[w][0]]['bid'], depth[highs[w][0]]['bid'], depth[lows[half][0]]['bid']
            if retests[w]['low'] != low:
                retests[w] = dict(low=low,first=row['t'],away=False,confirmed=False)
            old = previous['windows'].get(str(w)) if previous else None
            f['windows'][str(w)] = dict(low=low, high=high, half_low=half_low,
                drawdown=high-q['bid'], distance=q['bid']-low, vwap=vwap,
                retest=retests[w]['confirmed'],
                vwap_cross=bool(old and old['vwap'] is not None and vwap is not None
                    and previous['bid'] < old['vwap'] <= previous['ask']+500
                    and q['bid'] >= vwap),
                previous_high=old['high'] if old else None)
        if f['windows']:
            output.append(f)
        previous = f
    return output


def rules(fee_pct=None):
    micro = [dict(id=f'{family}:{w}:{level}:{region}', family=family, window=w,
        level=level, region=region,stage='micro',horizons=[600,1200,1800],room_net=None)
        for family,w,level,region in itertools.product(FAMILIES[:8], (60,180,300), (1,2), REGIONS)]
    cycle = [dict(id=f'{family}:{w}:{level}:{region}:room{room}', family=family, window=w,
        level=level, region=region,stage='cycle',horizons=[1200,1800,3600],room_net=room)
        for family,w,level,region,room in itertools.product(FAMILIES[:7],(300,900,1800),(1,2),REGIONS,(.1,.4))]
    book = [dict(id=f'{family}:{w}:{level}:{region}',family=family,window=w,
        level=level,region=region,stage='book',horizons=[600,1200,1800],room_net=None)
        for family,w,level,region in itertools.product(FAMILIES[8:],(60,180,300),(1,2),REGIONS)]
    initial = [{**r,'cost_pct':E.COST,'cost_model':'stress'} for r in micro+cycle+book]
    return initial+([{**r,'id':r['id']+':quote_fees','stage':'fees_'+r['stage'],
        'cost_pct':fee_pct,'cost_model':'quote_fees'} for r in initial] if fee_pct is not None else [])


def region_pass(f, region):
    # "all" refers to the exact input partition, not an implicit regular session.
    return region=='all' or (region=='open' and f['hour']==9) or (region=='day' and 10 <= f['hour'] < 16)


def qualifies(f, rule):
    x = f['windows'].get(str(rule['window']))
    if not x or f['spread'] > 500 or not region_pass(f, rule['region']): return False
    # Past resistance must leave room above the entry ask for the declared net
    # move. This is a causal hypothesis, never a promise of a future high.
    room = rule.get('room_net')
    if room is not None and (x['high']/f['ask']-1)*100-rule.get('cost_pct',E.COST) < room: return False
    family, level = rule['family'], rule['level']
    near = x['distance'] <= 500
    down = x['drawdown'] >= 500*level
    buying = f['buy_share'] is not None and f['buy_share'] >= .5
    if family=='absorption':
        return near and down and f['hold'] >= (3 if level==1 else 5) and f['hold_quotes']>=3 and f['sell_count']>=3 and f['sell_dominant']
    if family=='sell_decay':
        return near and down and buying and f['sell_decay'] is not None and f['sell_decay'] <= .5
    if family=='flow_flip':
        return near and down and f['buy_share'] is not None and f['buy_share']>=.6 and f['prior_buy_share'] is not None and f['prior_buy_share']<=.4
    if family=='range_retest':
        return x['retest'] and 500 <= x['distance'] <= 1000 and down and buying
    if family=='range_reclaim':
        return 500 <= x['distance'] <= 1000 and down and buying
    if family=='vwap_reclaim':
        return x['vwap_cross'] and down and buying
    if family=='trend_pullback':
        return x['half_low'] > x['low'] and f['bid']-x['half_low']<=500 and down and buying
    if family=='breakout':
        return (x['previous_high'] is not None and f['bid']>=x['previous_high']
            and x['high']-x['low']>=500*level and f['buy_share'] is not None
            and f['buy_share']>=.6 and f['volume_acceleration'] is not None and f['volume_acceleration']>=1.5)
    if family=='book_support':
        return near and down and buying and f['depth_ratio'] is not None and f['depth_ratio']>=(1.5 if level==1 else 2.)
    if family=='bid_replenish':
        return near and down and f['sell_dominant'] and f['hold']>=5 and f['sell_count']>=3 and f['bid_replenishment'] is not None and f['bid_replenishment']>=1.2
    if family=='ask_depletion':
        return near and down and buying and f['ask_depletion'] is not None and f['ask_depletion']<=.7
    if family=='book_flip':
        return near and down and buying and f['depth_ratio'] is not None and f['depth_ratio']>=1.5 and f['prior_depth_ratio'] is not None and f['prior_depth_ratio']<=1.
    raise ValueError('unknown_family')


def select(frames, horizon, rule=None, region='all'):
    until = -math.inf; selected = []; last_bucket = None
    for f in frames:
        if f['t'] < until: continue
        if rule is not None:
            if not qualifies(f, rule): continue
        else:
            bucket = math.floor(f['t']/horizon)
            if bucket==last_bucket or not region_pass(f, region): continue
            last_bucket = bucket
        selected.append(f); until = f['t']+horizon+1.5
    return selected


def metric(outcomes):
    full = [r for r in outcomes if r['complete']]
    binary = [r for r in full if r['binary'] is not None]
    wins = sum(r['binary']==1 for r in binary); losses = len(binary)-wins
    nets = [r['net'] for r in full]
    return dict(attempts=len(outcomes), complete=len(full), binary=len(binary), wins=wins, losses=losses,
        neither=sum(r['status']=='neither' for r in full), censored=len(outcomes)-len(full),
        win_rate=wins/len(binary) if binary else None, wilson=E.wilson(wins,len(binary)),
        target_per_attempt=wins/len(outcomes) if outcomes else None,
        mean_net_cf=mean(nets) if nets else None, worst_net_cf=min(nets) if nets else None,
        positive_cf=sum(n>0 for n in nets), states=dict(Counter(r['status'] for r in outcomes)),
        terminal_prefix_saved=sum(r.get('after_terminal_gap_ignored',False) for r in full),
        metric_role='price_counterfactual_not_fill_pnl_or_native_support')


def common_clock_comparison(ctx, frames, selected_frames, rule):
    """Same fixed clock window; distinct from native or same-shock comparison."""
    h,cost = rule['horizon'],rule['cost_pct']
    clock = select(frames,h,region=rule['region']); times = [f['t'] for f in clock]
    output = []
    for f in selected_frames:
        i = bisect_right(times,f['t'])-1
        if i<0 or f['t']>=clock[i]['t']+h:
            output.append(dict(candidate_t=f['t'],status='clock_reference_missing')); continue
        old = clock[i]; deadline = old['t']+h
        a,b = Q.entry_for(ctx,old),Q.entry_for(ctx,f)
        point = Q.endpoint_comparison(ctx,a,b,deadline)
        end_q = Q.quote_at(ctx['depth'],ctx['dt'],deadline,a['epoch']) if a else None
        if point['comparable'] and (end_q is None or not actionable(ctx['depth'][end_q])):
            point = dict(status='nonactionable_common_exit',comparable=False)
        if point['comparable']:
            old_net,new_net = point['baseline_net_cf']+E.COST-cost,point['candidate_net_cf']+E.COST-cost
            point = {**point,'baseline_net_cf':old_net,'candidate_net_cf':new_net,
                'baseline_positive_cf':old_net>0,'candidate_positive_cf':new_net>0,'cost_pct':cost}
        output.append(dict(candidate_t=f['t'],baseline_t=old['t'],deadline=deadline,status='matched',
            baseline=label(ctx,old,h,cost_pct=cost),
            candidate=label(ctx,f,deadline-f['t'],cost_pct=cost),endpoint=point))
    paired = [r for r in output if r['status']=='matched' and r['baseline']['complete'] and r['candidate']['complete']]
    points = [r['endpoint'] for r in output if r.get('endpoint',{}).get('comparable')]
    return dict(rows=output,paired=len(paired),baseline=metric([r['baseline'] for r in paired]),
        candidate=metric([r['candidate'] for r in paired]),endpoint_comparable=len(points),
        mean_endpoint_delta=mean(p['delta'] for p in points) if points else None,
        gained_targets=sum(r['candidate']['binary']==1 and r['baseline']['binary']!=1 for r in paired),
        lost_targets=sum(r['baseline']['binary']==1 and r['candidate']['binary']!=1 for r in paired),
        benchmark_role='same_clock_bucket_not_identical_shock_or_incumbent_main',used_for_selection=False)


def choose(candidates, baselines):
    eligible = []
    for c in candidates:
        m = c['metric']; b = baselines[baseline_key(c)]
        if m['binary']>=3 and b['binary']>=3 and m['win_rate'] > b['win_rate']:
            eligible.append(c)
    return max(eligible, key=lambda c:(c['metric']['win_rate'], c['metric']['wilson'],
        c['metric']['binary'], -FAMILIES.index(c['family']), -c['window'], -c['level'],
        -REGIONS.index(c['region']), -c['horizon'])) if eligible else None


def baseline_key(c):
    return f"{c['region']}:{c['horizon']}"+(f":{c['cost_model']}" if 'cost_model' in c else '')


def normalized_book(r):
    """Use the first three levels of a validated local depth-v1 snapshot.

    The local producer retains up to five levels. Extra retained levels do not
    invalidate a three-level hypothesis; validate them before taking the prefix.
    """
    result = {}
    for side in ('bid','ask'):
        levels = r.get(side+'_levels')
        if not isinstance(levels,list) or len(levels)<3: return None
        for i,level in enumerate(levels):
            if (not isinstance(level,list) or len(level)!=3 or type(level[0]) is not int or level[0]!=i+1
                or not R.finite(level[1]) or level[1]<=0 or not R.finite(level[2]) or level[2]<0): return None
            if i and (level[1]>=levels[i-1][1] if side=='bid' else level[1]<=levels[i-1][1]): return None
        if levels[0][1]!=r.get('best_'+side) or levels[0][2]!=r.get('best_'+side+'_qty'): return None
        result[side+'_sum'] = sum(p[2] for p in levels[:3])
    return result if result['ask_sum']>0 and result['bid_sum']>0 else None


def retained_books(day, parent_manifest, cache):
    expected = {(q['ep'],q['seq']):q for q in cache['depth']}
    records = {}; seen = set()
    for name in parent_manifest['source_manifest']:
        path = Path(name)
        if ('trade_date='+day not in name or 'market_depth_stream' not in name
            or path.name.endswith('manifest.json')): continue
        opener = E.gzip.open(path,'rt') if path.suffix=='.gz' else path.open()
        with opener as handle:
            for line in handle:
                if '005930' not in line: continue
                r = json.loads(line)
                if (r.get('symbol')!='005930' or r.get('schema')!='scalp_micro_reversion_market_depth_point_v1'
                    or r.get('item',r.get('source_item'))!='005930_AL'
                    or r.get('venue')!='SOR' or r.get('session_bucket')!='SOR_REGULAR'): continue
                identity = (r.get('sequence_epoch'),r.get('series_sequence'))
                if not all(type(v) is int for v in identity): continue
                if r.get('source_item') not in (None,'005930_AL'):
                    raise ValueError('normalized_book_source_item_conflict')
                q = expected.get(identity)
                if q is None: continue
                if identity in seen: raise ValueError('duplicate_normalized_book_identity')
                seen.add(identity)
                if (R.epoch(r['local_receive_timestamp'])!=q['t']
                    or r.get('best_bid')!=q['bid'] or r.get('best_ask')!=q['ask']
                    or r.get('best_bid_qty')!=q['bq'] or r.get('best_ask_qty')!=q['aq']):
                    raise ValueError('normalized_book_cache_binding_conflict')
                records[identity] = normalized_book(r) if q['valid'] else None
    if set(expected)!=seen: raise ValueError('normalized_book_partition_incomplete')
    return records


def fee_profiles(root, records):
    found = {}; fees = []
    for day in R.DAYS:
        reference = root/f'data/report/micro_reversion_economic_reference/micro_reversion_economic_reference_{day}.json'
        reference = R.P.calibration.existing_or_gzip_path(reference)
        if reference is None: raise ValueError('economic_reference_missing')
        body = R.P.calibration._load_json(reference)
        records[str(reference)] = R.P.file_sha(reference)
        for s in body.get('source_artifacts',[]):
            records[str(Path(s['resolved_path']).resolve())] = s['expected_sha256']
        profiles = {v:R.P.calibration._hierarchy_cost_profiles(root/'data',day,v).get('005930') for v in ('KRX','NXT')}
        if not all(profiles.values()): raise ValueError('exact_date_fee_reference_missing')
        values = {v:sum(p[k] for k in ('buy_fee_bps','sell_fee_bps','statutory_sell_tax_bps','uncertainty_buffer_bps'))/100 for v,p in profiles.items()}
        if len(set(values.values()))!=1: raise ValueError('venue_costs_differ_without_execution_route')
        fees.append(values['KRX'])
        found[day] = dict(cost_pct=values['KRX'],economic_source_sha256=profiles['KRX']['economic_source_sha256'],
            venues_equal=True,spread_in_price=True,extra_impact_assumed_zero=True,
            cost_model='quote_fees_comparison_not_broker_reconciled_economics')
    if len(set(fees))!=1: raise ValueError('fees_change_across_dates_requires_per_day_model')
    return found,fees[0]


def native_bridge(projection, frames_by_day, rule):
    """Captured hard guards and native identities remain mandatory and unchanged."""
    observed = []; groups = {}; frames_times = {d:[f['t'] for f in fs] for d,fs in frames_by_day.items()}
    for row in sorted(projection['main'],key=lambda r:r['t']):
        if row['native'] is None: continue
        day = row['day']; fs = frames_by_day[day]
        i = bisect_left(frames_times[day],row['t'])-1
        source_epoch = row['features'].get('stream_epoch')
        frame = fs[i] if (i>=0 and row['t']-fs[i]['t']<=1.5
            and fs[i]['ep']==source_epoch and row['features'].get('stream_valid') is True) else None
        hit = bool(frame and qualifies(frame,rule))
        compatible = row['guard']['cohort'] in ('parent_enter','soft_confirmation_only') and not row['guard']['blockers']
        # The original recoverable contract also retains parent micro-price and
        # aggressive-flow confirmation; this study cannot turn it off.
        new = hit and compatible and (row['parent']=='ENTER_NOW' or row['recoverable'])
        native = tuple(row['native']); record = dict(trace=row['trace'],day=day,t=row['t'],
            native_identity=list(native),parent=row['parent'],rule_hit=hit,guard_compatible=compatible,
            admitted=bool(new),label=row['label'],cost_pct=row['cost'],blockers=row['guard']['blockers'],
            feature_status='observed' if frame else 'missing_or_stale')
        observed.append(record)
        g = groups.setdefault(native,dict(native_identity=list(native),baseline=None,candidate=None))
        if g['baseline'] is None and row['parent']=='ENTER_NOW': g['baseline'] = record
        if g['candidate'] is None and new: g['candidate'] = record
    def summarize(records):
        labels = [r['label'] for r in records]
        eligible = [l for l in labels if l['binary'] is not None]
        wins = sum(l['binary']==1 for l in eligible)
        return dict(admitted=len(records),binary=len(eligible),wins=wins,
            losses=len(eligible)-wins,win_rate=wins/len(eligible) if eligible else None,
            unknown=len(records)-len(eligible))
    return dict(native_groups=len(groups),attempts=len(observed),
        baseline=summarize([g['baseline'] for g in groups.values() if g['baseline']]),
        candidate=summarize([g['candidate'] for g in groups.values() if g['candidate']]),
        pattern_hits=sum(r['rule_hit'] for r in observed),
        hits_outside_preserved_guard=sum(r['rule_hit'] and not r['guard_compatible'] for r in observed),
        groups=list(groups.values()),observations=observed,
        policy_publication=False,synthetic_native_identity=False)


def prepare(root, source, projection, output):
    manifest = R.read(source)
    Q.verify_hashes({**manifest['source_manifest'], **manifest['kernel_manifest'],
        manifest['plan_path']:manifest['plan_sha256']})
    records = {str(source):R.P.file_sha(source), str(projection):R.P.file_sha(projection)}
    records.update({r['path']:r['sha256'] for r in manifest['files'].values()})
    plan = root/'docs/proposals/samsung-pattern-campaign-plan-2026-10-04.md'
    records[str(plan)] = R.P.file_sha(plan)
    continuity_plan=root/'docs/proposals/samsung-quote-continuity-sensitivity-research-plan-2026-10-04.md'
    records[str(continuity_plan)] = R.P.file_sha(continuity_plan)
    records[str(Path(__file__).resolve())] = R.P.file_sha(Path(__file__))
    records.update({**manifest['source_manifest'],**manifest['kernel_manifest'],
        manifest['plan_path']:manifest['plan_sha256']})
    profiles,fee_pct = fee_profiles(root,records)
    preserved = R.read(root/'tmp/samsung-continuous-recovery-research-20261003/preserved-artifacts.json')
    # Legacy preservation registry is a simple path -> SHA map, not a report.
    preserved = {str(root/k):v for k,v in preserved.items()}
    Q.verify_hashes(preserved)
    R.read(projection)
    files = {}; census = {}
    for day,r in manifest['files'].items():
        Q.verify_hashes({r['path']:r['sha256']})
        cache = E.read_cache(Path(r['path']))
        books = retained_books(day,manifest,cache)
        frames = feature_rows(cache,books)
        path = output/(day+'.json')
        write(path, dict(day=day,frames=frames,cache=r))
        files[day] = dict(path=str(path),sha256=R.P.file_sha(path))
        census[day] = dict(trades=len(cache['rows']), depth=len(cache['depth']),
            actionable_depth=sum(actionable(q) for q in cache['depth']), features=len(frames),
            book_valid=sum(b is not None for b in books.values()),
            window_support={str(w):sum(str(w) in f['windows'] for f in frames) for w in WINDOWS})
        print(day,'causal_frames',len(frames),flush=True)
    Q.verify_hashes(records)
    write(output/'manifest.json',dict(records=records,files=files,census=census,
        parent_manifest=str(source),projection=str(projection),preserved=preserved,
        rules=rules(fee_pct),horizons=list(HORIZONS),fee_profiles=profiles,success_preservation_veto=False))


def run(source, output, max_quote_gap=1.5):
    started = time.monotonic(); manifest,seals,source_sha = load_manifest(source)
    results = {}; baselines = {}; signals = {}; contexts = {}; frames_by_day = {}; outcomes_by_day = {}
    projection = R.read(Path(manifest['projection']))
    for day,r in manifest['files'].items():
        prepared = R.read(Path(r['path'])); frames = prepared['frames']
        frames_by_day[day] = frames
        cache = E.read_cache(Path(prepared['cache']['path'])); ctx = campaign_context(cache,max_quote_gap)
        contexts[day] = ctx; day_results = {}; day_base = {}; day_signals = {}
        labels = {}
        def get(f, horizon, cost):
            key = (f['index'],horizon,cost)
            if key not in labels: labels[key] = label(ctx,f,horizon,cost_pct=cost)
            return labels[key]
        for region,horizon,cost_model in itertools.product(REGIONS,HORIZONS,('stress','quote_fees')):
            cost = E.COST if cost_model=='stress' else manifest['fee_profiles'][day]['cost_pct']
            fs = select(frames,horizon,region=region)
            day_base[f'{region}:{horizon}:{cost_model}'] = metric([get(f,horizon,cost) for f in fs])
        for rule in manifest['rules']:
          for horizon in rule['horizons']:
            key = rule['id']+f':{horizon}'
            fs = select(frames,horizon,rule)
            day_results[key] = dict(**rule,horizon=horizon,metric=metric([get(f,horizon,rule['cost_pct']) for f in fs]))
            day_signals[key] = fs
        results[day] = day_results; baselines[day] = day_base; signals[day] = day_signals
        outcomes_by_day[day] = labels
        print(day,'rules',len(day_results),'cached_outcomes',len(labels),flush=True)
    folds = []
    for stage in ('micro','cycle','book','fees_micro','fees_cycle','fees_book'):
      for train_days, held in [(R.DAYS[:1],R.DAYS[1]),(R.DAYS[:2],R.DAYS[2])]:
        candidates = []
        for key,c in results[train_days[0]].items():
            if c['stage'] != stage: continue
            outcomes = [outcomes_by_day[d][(f['index'],c['horizon'],c['cost_pct'])] for d in train_days for f in signals[d][key]]
            candidates.append({**c,'key':key,'metric':metric(outcomes)})
        bases = {}
        for region,horizon,cost_model in itertools.product(REGIONS,HORIZONS,('stress','quote_fees')):
            cost = E.COST if cost_model=='stress' else manifest['fee_profiles'][train_days[0]]['cost_pct']
            outcomes = [outcomes_by_day[d][(f['index'],horizon,cost)] for d in train_days
                for f in select(frames_by_day[d],horizon,region=region)]
            bases[f'{region}:{horizon}:{cost_model}'] = metric(outcomes)
        selected = choose(candidates,bases)
        detail = None
        if selected:
            key = selected['key']; fs = signals[held][key]
            detail = dict(candidate=results[held][key],
                baseline=baselines[held][baseline_key(selected)],
                outcomes=[outcomes_by_day[held][(f['index'],selected['horizon'],selected['cost_pct'])] for f in fs],
                latency={str(latency):metric([label(contexts[held],f,selected['horizon'],latency=latency,cost_pct=selected['cost_pct']) for f in fs]) for latency in (.25,1.)},
                main_trailing_arm_price=metric([label(contexts[held],f,selected['horizon'],target_net=.4,cost_pct=selected['cost_pct']) for f in fs]),
                common_clock=common_clock_comparison(contexts[held],frames_by_day[held],fs,selected),
                neighbors=[c for c in results[held].values() if c['family']==selected['family']
                    and c['region']==selected['region'] and c['horizon']==selected['horizon']],
                native_bridge=native_bridge(projection,frames_by_day,selected))
        folds.append(dict(stage=stage,train_days=list(train_days),held_day=held,selected=selected,
            training_baselines=bases,training_candidates=candidates,held=detail))
    Q.verify_hashes(seals)
    preserved = manifest['preserved']
    Q.verify_hashes(preserved)
    write(output/'result.json',dict(source_manifest_sha256=source_sha,
        folds=folds,daily=results,baselines=baselines,census=manifest['census'],
        hypothesis_count=sum(len(r['horizons']) for r in manifest['rules']),elapsed_sec=time.monotonic()-started,
        fee_profiles=manifest['fee_profiles'],
        max_observed_quote_gap_sec=max_quote_gap,quote_gap_sensitivity=max_quote_gap!=1.5,
        selection='training_win_rate_then_wilson_support_simplicity',
        success_preservation_veto=False,main_native_promotion=False,execution_route_verified=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','run'))
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--projection',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-observed-quote-gap',type=float,choices=(1.5,3.,10.),default=1.5,
        help='Offline outcome sensitivity; entry/endpoint freshness and native guards stay fixed')
    args = parser.parse_args()
    if args.mode=='prepare':
        if args.projection is None: parser.error('--projection is required for prepare')
        prepare(args.root.resolve(),args.source.resolve(),args.projection.resolve(),args.output.resolve())
    else: run(args.source.resolve(),args.output.resolve(),args.max_observed_quote_gap)


if __name__=='__main__': main()
