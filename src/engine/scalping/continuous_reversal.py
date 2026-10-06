"""Shared normalized-price reversal kernel. No provider, broker or order authority.

The batch kernel is the reviewed zero-base research algorithm. Runtime consumes
normalized envelopes only; raw broker fields are owned by the WS parser.
"""
from __future__ import annotations
import bisect
import math
from collections import deque
import threading
from itertools import islice
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
KST=ZoneInfo("Asia/Seoul")
VERSION="continuous_reversal_v1"
COST=.0023
TARGET=.004
STOP=-.03
RULES=['ALL','DROP_GE_0_2','DROP_GE_0_4','DROP_GE_0_6','DROP_GE_1_0',
       'DD5_GE_0_4','DD5_GE_0_8','DD5_GE_1_2','DROP_0_4_REBOUND_LE_0_3',
       'DD5_0_8_REBOUND_LE_0_3','VOLUME_RATIO_GE_1_5','DROP_0_4_VOL_UP','DD5_0_8_VOL_UP']
FEATURES = ["buy_pressure_10t", "buy_pressure_30s", "return_10t_pct", "vs_vwap_60s_pct"]
def iso(t):return datetime.fromtimestamp(t,KST).isoformat(timespec='milliseconds')

def good_quote(r):
    return (r[8] and r[4] is not None and r[5] is not None and 0<r[4]<=r[5]
            and (r[10] is None or 0<=r[10]<=5000))

def connected(a,b):
    # Quiet intervals are not automatically missing data. Native sequence,
    # epoch and accepted packet quality define observed-price continuity.
    return bool(a[8] and b[8] and a[1]==b[1] and b[2]==a[2]+1 and b[0]>=a[0])

def segments(rows,quote=False):
    n=len(rows);ends=[0]*n;starts=[0]*n;start=0
    valid=[bool(good_quote(r) if quote else r[8]) for r in rows]
    for i in range(n):
        if not valid[i] or (i and (not valid[i-1] or not connected(rows[i-1],rows[i]))):start=i
        starts[i]=start
    for i in range(n-1,-1,-1):
        ends[i]=ends[i+1] if (i+1<n and valid[i] and valid[i+1] and connected(rows[i],rows[i+1])) else i
    return starts,ends,valid

class Tree:
    def __init__(self,values):
        self.n=1
        while self.n<len(values):self.n*=2
        self.hi=np.full(self.n*2,-math.inf);self.lo=np.full(self.n*2,math.inf)
        for i,v in enumerate(values):
            if v is not None and math.isfinite(v):self.hi[self.n+i]=self.lo[self.n+i]=v
        step=self.n//2
        while step:
            self.hi[step:2*step]=np.maximum(self.hi[2*step:4*step:2],self.hi[2*step+1:4*step:2])
            self.lo[step:2*step]=np.minimum(self.lo[2*step:4*step:2],self.lo[2*step+1:4*step:2])
            step//=2

    def cover(self,left,right):
        left+=self.n;right+=self.n+1;a=[];b=[]
        while left<right:
            if left&1:a.append(left);left+=1
            if right&1:right-=1;b.append(right)
            left//=2;right//=2
        return a+b[::-1]

    def first(self,left,right,value,above=True):
        if left>right:return None
        data=self.hi if above else self.lo
        def hit(node):return data[node]>=value if above else data[node]<=value
        for node in self.cover(left,right):
            if not hit(node):continue
            while node<self.n:
                node*=2
                if not hit(node):node+=1
            return node-self.n
        return None

    def maximum(self,left,right):
        return max(self.hi[n] for n in self.cover(left,right))

def turns(rows):
    """All micro turns; no minimum amplitude, time, volume, flow, or outcomes."""
    direction=0;peak=low=None;steps=0;out=[]
    for i,r in enumerate(rows):
        if i==0 or not connected(rows[i-1],r):
            direction=0;peak=low=None;steps=0;continue
        change=r[3]-rows[i-1][3]
        if change<0:
            if direction!=-1:peak=i-1;steps=0
            direction=-1;low=i;steps+=1
        elif change>0:
            if direction==-1:
                out.append(dict(peak_index=peak,low_index=low,entry_index=i,down_steps=steps))
            direction=1
    return out

def label(rows,times,tree,ends,valid,index,price,horizon=1800):
    if price is None or price<=0 or not valid[index]:return dict(status='UNRESOLVED',reason='entry_source_missing')
    start=times[index];deadline=start+horizon
    last=min(ends[index],bisect.bisect_right(times,deadline)-1)
    up=tree.first(index+1,last,price*(1+TARGET)/(1-COST),True)
    down=tree.first(index,last,price*(1+STOP)/(1-COST),False)
    if up is not None and (down is None or up<down):
        return dict(status='WIN',hit_index=up,hit_at=times[up],delay_sec=times[up]-start)
    if down is not None:
        return dict(status='FAIL_STOP',hit_index=down,hit_at=times[down],delay_sec=times[down]-start)
    if times[ends[index]]>=deadline:return dict(status='FAIL_TIMEOUT')
    return dict(status='UNRESOLVED',reason='path_end_before_horizon',observed_seconds=max(0,times[ends[index]]-start))

def conditions(e):
    d,dd,reb,vol=(e[k] for k in ('drop_pct','drawdown_5m_pct','confirmation_pct','volume_ratio_60s'))
    return dict(ALL=True,DROP_GE_0_2=d>=.2,DROP_GE_0_4=d>=.4,DROP_GE_0_6=d>=.6,DROP_GE_1_0=d>=1,
        DD5_GE_0_4=dd is not None and dd>=.4,DD5_GE_0_8=dd is not None and dd>=.8,DD5_GE_1_2=dd is not None and dd>=1.2,
        DROP_0_4_REBOUND_LE_0_3=d>=.4 and reb<=.3,
        DD5_0_8_REBOUND_LE_0_3=dd is not None and dd>=.8 and reb<=.3,
        VOLUME_RATIO_GE_1_5=vol is not None and vol>=1.5,
        DROP_0_4_VOL_UP=d>=.4 and vol is not None and vol>=1,
        DD5_0_8_VOL_UP=dd is not None and dd>=.8 and vol is not None and vol>=1)

def past_drawdown(rows,times,tree,index,low_price):
    left=bisect.bisect_left(times,times[index]-300)
    if left>=index:return None
    high=tree.maximum(left,index-1)
    return float(max(0.,(1-low_price/high)*100)) if math.isfinite(high) and high>0 else None

def analyze_symbol(rows,day,venue,session,code):
    times=[r[0] for r in rows]
    starts,ends,valid=segments(rows)
    _,qends,qvalid=segments(rows,True)
    tree=Tree([r[3] if r[8] else None for r in rows]);qtree=Tree([r[4] for r in rows])
    qty=[0.];qty_bad=[0]
    for r in rows:
        ok=r[6] is not None and r[6]>0
        qty.append(qty[-1]+(r[6] if ok else 0));qty_bad.append(qty_bad[-1]+(not ok))
    events=[]
    for turn in turns(rows):
        i,low,peak=(turn[k] for k in ('entry_index','low_index','peak_index'))
        r=rows[i];t=r[0]
        # Price-only observed high BEFORE the confirming uptick. Five minutes
        # is a maximum lookback, not a mandatory waiting/continuity gate.
        dd=past_drawdown(rows,times,tree,i,rows[low][3])
        a=bisect.bisect_left(times,t-120);b=bisect.bisect_left(times,t-60)
        vol=None
        if a>=starts[i] and t-times[starts[i]]>=120 and qty_bad[i+1]==qty_bad[a] and qty[b]>qty[a]:
            vol=(qty[i+1]-qty[b])/(qty[b]-qty[a])
        entry=r[5] if good_quote(r) else None
        e=dict(day=day,venue=venue,session=session,market=('PRE' if 'PREMARKET' in session else 'AFTER' if 'AFTERMARKET' in session else 'REGULAR'),
            symbol=code,group='samsung' if code=='005930' else 'other',
            event_id=f'{day}:{venue}:{session}:{code}:{r[1]}:{r[2]}',
            at=iso(t),epoch=t,entry_index=i,low_at=iso(rows[low][0]),low_epoch=rows[low][0],low_price=rows[low][3],
            peak_at=iso(rows[peak][0]),peak_price=rows[peak][3],confirmation_price=r[3],entry_ask=entry,
            drop_pct=(1-rows[low][3]/rows[peak][3])*100,
            decline_seconds=rows[low][0]-rows[peak][0],down_steps=turn['down_steps'],
            confirmation_pct=(r[3]/rows[low][3]-1)*100,
            low_to_confirmation_sec=t-rows[low][0],drawdown_5m_pct=dd,volume_ratio_60s=vol,
            spread_pct=(r[5]/r[4]-1)*100 if good_quote(r) else None,
            price_band='LT_20000' if r[3]<20000 else '20000_TO_100000' if r[3]<100000 else 'GE_100000',
            source_item=r[9],source_item_recorded=r[9] is not None,
            low_outcome=label(rows,times,tree,ends,valid,low,rows[low][3]),
            confirm_trade_outcome=label(rows,times,tree,ends,valid,i,r[3]),
            outcome=label(rows,times,tree,ends,valid,i,entry),
            bid_outcome=label(rows,times,qtree,qends,qvalid,i,entry))
        if e['outcome']['status']=='FAIL_TIMEOUT':
            e['late_outcome']=label(rows,times,tree,ends,valid,i,entry,3600)
        e['matches']=[k for k,v in conditions(e).items() if v]
        events.append(e)
    return events,dict(rows=len(rows),valid_price_rows=sum(valid),valid_quote_rows=sum(qvalid),
        first=iso(times[0]),last=iso(times[-1]),price_segments=sum(i==s for i,s in enumerate(starts)),
        source_item_missing=sum(r[9] is None for r in rows),
        receive_gaps_over_60s=sum(b-a>60 for a,b in zip(times,times[1:])))

def build_features(rows, *, earliest_segment_epoch=None):
    times = np.array([r[0] for r in rows])
    starts, _, valid = segments(rows)
    starts = np.array(starts)
    prices = np.array([r[3] if r[3] is not None else np.nan for r in rows])
    qty = np.array([r[6] if r[6] is not None and r[6]>0 and r[8] else 0 for r in rows])
    sides = np.array([r[7] for r in rows])
    def cumulative(a):
        return np.concatenate(([0.], np.cumsum(a)))
    q = cumulative(qty)
    buy = cumulative(np.where(sides==1, qty, 0))
    bad_qty = cumulative(qty<=0)
    bad_side = cumulative((qty<=0) | (sides==0))
    pv = cumulative(np.where(qty>0, qty*np.nan_to_num(prices), 0))
    outputs = {k: np.full(len(rows), np.nan) for k in FEATURES[:4]}
    for i in range(len(rows)):
        if not valid[i]:
            continue
        a = i-9
        if a>=starts[i]:
            if bad_side[i+1]==bad_side[a] and q[i+1]>q[a]:
                outputs['buy_pressure_10t'][i] = 100*(buy[i+1]-buy[a])/(q[i+1]-q[a])
            outputs['return_10t_pct'][i] = 100*(prices[i]/prices[a]-1)
        a = int(np.searchsorted(times, times[i]-30))
        segment_epoch=(earliest_segment_epoch if starts[i]==0 and earliest_segment_epoch is not None else times[starts[i]])
        if times[i]-segment_epoch>=30 and a>=starts[i] and bad_side[i+1]==bad_side[a] and q[i+1]>q[a]:
            outputs['buy_pressure_30s'][i] = 100*(buy[i+1]-buy[a])/(q[i+1]-q[a])
        a = int(np.searchsorted(times, times[i]-60))
        if times[i]-segment_epoch>=60 and a>=starts[i] and bad_qty[i+1]==bad_qty[a] and q[i+1]>q[a]:
            average = (pv[i+1]-pv[a])/(q[i+1]-q[a])
            outputs['vs_vwap_60s_pct'][i] = 100*(prices[i]/average-1)
    return outputs

from collections import defaultdict
INPUT_FEATURES = FEATURES + ["spread_pct", "confirmation_pct", "volume_ratio_60s"]
def make_input(e, rows, features):
    i=e['entry_index'];current=rows[i]
    # Strict allowlist. No labels, outcomes, future contacts, historical win rates,
    # or symbol-specific success hints are visible to the model.
    values={k:features[k] for k in INPUT_FEATURES}
    values.update({k:e[k] for k in ['drop_pct','drawdown_5m_pct','decline_seconds',
                                  'confirmation_price','low_price','entry_ask','down_steps']})
    positive=[dict(id='observed_price_decline',value=e['drop_pct'],unit='percent'),
              dict(id='first_price_uptick',value=e['confirmation_pct'],unit='percent'),
              dict(id='observed_drawdown_state',value=e['drawdown_5m_pct'],unit='percent')]
    adverse=[];bindings=defaultdict(list)
    for key, fact, code, predicate in [
        ('buy_pressure_10t','recent_sell_pressure','ADVERSE_TAPE',lambda x:x<40),
        ('return_10t_pct','negative_short_momentum','ADVERSE_TAPE',lambda x:x<0),
        ('vs_vwap_60s_pct','below_recent_vwap','ADVERSE_TAPE',lambda x:x<0),
        ('volume_ratio_60s','volume_not_expanding','CONFIRMATION_MISSING',lambda x:x<1),
        ('spread_pct','observable_wide_spread','LIQUIDITY_FRAGILE',lambda x:x>.3),
        ('confirmation_pct','rebound_already_consumed','OVEREXTENSION_CHASE',lambda x:x>.4),
    ]:
        value=values[key]
        if value is not None and predicate(value):
            adverse.append(dict(id=fact,value=value,source_feature=key,
                                disposition='research_context_not_proven_invalidation'))
            bindings[code].append(fact)
    if values['buy_pressure_10t'] is not None and values['buy_pressure_10t']>=60:
        positive.append(dict(id='recent_buy_pressure',value=values['buy_pressure_10t'],unit='percent'))
    # A research candidate is an observed price turn, not a forged historical
    # ENTER_NOW receipt. The wrapper makes the evaluation semantics explicit.
    return dict(schema='auxiliary_reversal_research_input_v1',
        context='offline reconstructed price reversal; not a historical machine ENTER_NOW or order',
        market=e['market'],venue=e['venue'],source_item=e['source_item'],
        symbol_group=e['group'],price_band=e['price_band'],as_of=e['at'],
        objective=dict(net_target_pct=.4,net_soft_stop_pct=-3.,horizon_seconds=1800,cost_rate=.0023,
                       target_price=e['entry_ask']*1.004/.9977,soft_stop_price=e['entry_ask']*.97/.9977,
                       metric='binary target-before-stop within horizon; no expected PnL or reward-risk floor'),
        mechanistic_entry_assessment=dict(action='ENTER_NOW',basis='counterfactual_price_reversal_research_only',
            price_reversal_confirmed=True,existing_live_machine_action='not_used'),
        entry_setup_evidence_v1=dict(schema='offline_reconstructed_fact_ledger_not_runtime_schema',
            setup_state='READY',readiness_basis='observed_price_turn_only_not_legacy_live_setup',source_quality='price_and_entry_quote_valid',
            positive_facts=positive,contradicting_facts=adverse,invalidation_facts=[],
            risk_fact_bindings=dict(bindings),facts=values,
            optional_missing=[k for k,v in values.items() if v is None],
            unobserved=['depth_queue','program_flow','investor_flow','market_news','live_account_order_guards']),
        recent_observed_prices=[dict(age_sec=round(current[0]-r[0],3),price=r[3],qty=r[6],
                                     side='BUY' if r[7]==1 else 'SELL' if r[7]==-1 else 'UNKNOWN')
                                for r in rows[max(i-9,0):i+1] if r[8] and r[1]==current[1]],
        runtime_effect=False,allowed_runtime_apply=False,actual_order_submitted=False)


def market_bucket(session):
    value = str(session).upper()
    if value in {'PRE', 'PREMARKET_KRX_LIKE', 'KRX_LIKE_PREMARKET', 'PREMARKET', 'KRX_PREMARKET', 'NXT_PREMARKET', 'SOR_PREMARKET'}:
        return 'PRE'
    if value in {'AFTER', 'KRX_AFTERMARKET', 'NXT_AFTERMARKET', 'SOR_AFTERMARKET', 'INTEGRATED_AFTERMARKET', 'KRX_NXT_AFTERMARKET'}:
        return 'AFTER'
    if value in {'REGULAR', 'KRX_REGULAR', 'NXT_REGULAR_OVERLAP', 'NXT_REGULAR', 'SOR_REGULAR', 'INTEGRATED_REGULAR'}:
        return 'REGULAR'
    raise ValueError('unsupported_reversal_session')


def cell_key(symbol, session, price):
    if not isinstance(price, (int, float)) or isinstance(price, bool) or not math.isfinite(price) or price <= 0:
        raise ValueError('invalid_cell_price')
    group = 'samsung' if symbol == '005930' else 'other'
    band = 'ALL' if group == 'samsung' else ('LT_20000' if price < 20000 else '20000_TO_100000' if price < 100000 else 'GE_100000')
    return '|'.join((group, market_bucket(session), band))


class ReversalState:
    """Constant-time ingestion; feature projection happens in the evaluator.

    Every normalized trade updates direction, independent of machine/provider
    cooldowns. One route/epoch/session never supplies another route's history.
    """
    def __init__(self):
        self.rows = deque()
        self.highs = deque()
        self.direction = 0
        self.peak = self.low = self.last = self.turn = None
        self.steps = 0
        self.segment_start = None

    def observe(self, row, *, symbol, venue, session):
        while len(self.rows) > 10 and self.rows[0][0] < row[0] - 305:
            self.rows.popleft()
        while self.highs and self.highs[0][0] < row[0] - 300:
            self.highs.popleft()
        if self.last and row[1:3] == self.last[1:3]:
            if row == self.last:
                return
            row = list(row)
            row[8] = 0
        if self.last is None or not connected(self.last, row):
            self.direction = 0
            self.peak = self.low = self.turn = None
            self.steps = 0
            self.segment_start = row[0]
        if not row[8]:
            self.rows.append(row)
            self.last = row
            self.turn = None
            return
        if self.last and connected(self.last, row):
            change = row[3] - self.last[3]
            if change < 0:
                if self.direction != -1:
                    self.peak, self.steps = self.last, 0
                self.direction = -1
                self.low = row
                self.steps += 1
                self.turn = None
            elif change > 0:
                if self.direction == -1:
                    high = self.highs[0][3] if self.highs else None
                    self.turn = dict(
                        event_id=f'{datetime.fromtimestamp(row[0], KST).date()}:{venue}:{session}:{symbol}:{row[1]}:{row[2]}',
                        symbol=symbol, venue=venue, session=session,
                        market=market_bucket(session), group='samsung' if symbol == '005930' else 'other',
                        price_band=('LT_20000' if row[3]<20000 else '20000_TO_100000' if row[3]<100000 else 'GE_100000'),
                        at=iso(row[0]), epoch=row[0], source_item=row[9],
                        low_price=self.low[3], confirmation_price=row[3],
                        entry_ask=row[5] if good_quote(row) else None,
                        drop_pct=(1-self.low[3]/self.peak[3])*100,
                        drawdown_5m_pct=max(0., (1-self.low[3]/high)*100) if high else None,
                        confirmation_pct=(row[3]/self.low[3]-1)*100,
                        decline_seconds=self.low[0]-self.peak[0], down_steps=self.steps,
                        spread_pct=(row[5]/row[4]-1)*100 if good_quote(row) else None,
                        volume_ratio_60s=None,
                        _recent_rows=list(reversed(list(islice(reversed(self.rows),9))))+[row[:]],
                    )
                self.direction = 1
        self.rows.append(row)
        while self.highs and self.highs[-1][3] <= row[3]:
            self.highs.pop()
        self.highs.append(row)
        self.last = row

    def snapshot(self):
        if self.turn is None:
            return None
        event = dict(self.turn)
        recent = event.pop('_recent_rows', [])
        if event['entry_ask'] is None:
            return event, None
        rows = [r[:] for r in self.rows if r[0] <= event['epoch'] and r[2] <= int(event['event_id'].rsplit(':', 1)[1])]
        identities={(r[1],r[2]) for r in rows}
        rows=sorted([r[:] for r in recent if (r[1],r[2]) not in identities]+rows,
                    key=lambda r:(r[0],r[1],r[2]))
        if not rows or rows[-1][0] != event['epoch']:
            return None
        t = event['epoch']
        if t-self.segment_start >= 120:
            window = [r for r in rows if r[0] >= t-120]
            if all(r[6] is not None and r[6] > 0 for r in window):
                previous = sum(r[6] for r in window if r[0] < t-60)
                if previous > 0:
                    event['volume_ratio_60s'] = sum(r[6] for r in window if r[0] >= t-60)/previous
        feature_arrays = build_features(rows, earliest_segment_epoch=self.segment_start)
        features = {k: float(v[-1]) if math.isfinite(v[-1]) else None for k, v in feature_arrays.items()}
        # Lookback coverage belongs to the uninterrupted original segment,
        # not the retained 300-second buffer's first row.
        features.update({k:event[k] for k in INPUT_FEATURES[4:]})
        event['entry_index'] = len(rows)-1
        return event, make_input(event, rows, features)


_STATES = {}
_ACTIVE_KEYS = {}
_LOCK = threading.RLock()


def observe_normalized(symbol, session, envelope):
    """Consume existing parser-owned envelope; no raw FID or protocol parsing."""
    venue = envelope.get('effective_venue')
    # SOR is an observation route, never an inferred actual execution venue.
    if envelope.get('market_route') == 'krx_nxt_integrated':
        venue = 'SOR'
    if venue not in {'KRX', 'NXT', 'SOR'}:
        return
    try:
        market = market_bucket(session)
        t = float(envelope['observed_epoch'])
        price = float(envelope['trade_price'])
        row = [t, envelope['transport_epoch'], envelope['route_sequence'], price,
               envelope.get('inline_best_bid'), envelope.get('inline_best_ask'),
               envelope.get('trade_qty'), {'BUY':1, 'SELL':-1}.get(envelope.get('aggressor_side'), 0),
               int(math.isfinite(t) and math.isfinite(price) and price > 0), envelope.get('item'), 0]
        exchange = envelope.get('provider_trade_epoch')
        row[8] = int(row[8] and isinstance(exchange, (int, float)) and 0 <= t-exchange <= 5)
        key = (symbol, venue, str(envelope.get('item')), market, datetime.fromtimestamp(t,KST).date())
        with _LOCK:
            scope=key[:3]
            old_key=_ACTIVE_KEYS.get(scope)
            if old_key is not None and old_key!=key:
                _STATES.pop(old_key,None)
            _ACTIVE_KEYS[scope]=key
            state = _STATES.setdefault(key, ReversalState())
            state.observe(row, symbol=symbol, venue=venue, session=session)
    except (KeyError, ValueError, TypeError, OverflowError):
        return


def current_snapshot(symbol, venue, session, *, now, item=None):
    market = market_bucket(session)
    with _LOCK:
        candidates = [state for key, state in _STATES.items()
                      if key[:2] == (symbol, venue) and key[3] == market
                      and key[4] == datetime.fromtimestamp(now,KST).date()
                      and (item is None or key[2] == item)]
        if len(candidates) != 1:
            return None
        state = candidates[0]
        if not state.turn or not 0 <= now-state.turn['epoch'] <= 5:
            return None
        # Copy under the ingestion lock, calculate rolling features outside it.
        frozen = ReversalState()
        frozen.rows = deque(r[:] for r in state.rows)
        frozen.turn = dict(state.turn)
        frozen.segment_start = state.segment_start
    return frozen.snapshot()


class Bars:
    def __init__(self,records):
        self.rows=sorted(records,key=lambda b:b['t']);self.times=[b['t'] for b in self.rows]
        self.high=Tree([b['h'] for b in self.rows]);self.low=Tree([b['l'] for b in self.rows])
        self.breaks=[i for i,b in enumerate(self.rows) if b.get('invalid') or (i and b['t']-self.rows[i-1]['t']!=60)]

    def label_one(self,at,price,horizon,shift):
        end=at+horizon
        i=bisect.bisect_right(self.times,at-shift)-1
        j=bisect.bisect_left(self.times,end-shift)-1
        if i<0 or j<i or self.times[i]+shift>at or self.times[i]+shift+60<=at:
            return dict(status='UNRESOLVED',reason='completed_bar_start_missing')
        gap=next((n for n in self.breaks[bisect.bisect_left(self.breaks,i):] if n<=j),None)
        last=min(j,gap-1) if gap is not None else j
        up=self.high.first(i,last,price*(1+TARGET)/(1-COST))
        down=self.low.first(i,last,price*(1+STOP)/(1-COST),False)
        first=min([n for n in [up,down] if n is not None],default=None)
        if first is not None:
            start=self.times[first]+shift;finish=start+60
            if start<at or finish>end:return dict(status='UNRESOLVED',reason='completed_bar_boundary_touch')
            if up==down:return dict(status='UNRESOLVED',reason='completed_bar_both_barriers')
            return dict(status='WIN' if first==up else 'FAIL_STOP',hit_at=finish,delay_sec=finish-at,
                        contact_time_is_bar_end_upper_bound=True)
        if gap is not None:return dict(status='UNRESOLVED',reason='completed_bar_gap')
        if j>=len(self.rows) or self.times[j]+shift+60<end:return dict(status='UNRESOLVED',reason='completed_bar_end_missing')
        return dict(status='FAIL_TIMEOUT')

    def label(self,at,price,horizon):
        if price is None or price<=0:return dict(status='UNRESOLVED',reason='entry_source_missing')
        result=self.label_one(at,price,horizon,0)
        # Even when shared bars give an exact minute start, use the stricter
        # common clock comparison for a mixed legacy REST/shared path.
        other=self.label_one(at,price,horizon,-60)
        if result['status']!=other['status']:return dict(status='UNRESOLVED',reason='completed_bar_clock_disagreement')
        return result
