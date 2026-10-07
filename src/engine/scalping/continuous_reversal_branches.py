"""Registered Main price branches, shared by replay and normalized ingestion.

This owner has no provider, broker, filesystem or order side effects in observe.
The v1 kernel remains byte-identical for historical native policies.
"""
from __future__ import annotations

import copy
import math
import threading
from collections import Counter, deque
from datetime import datetime
from itertools import islice

from src.engine.scalping import continuous_reversal as K
from src.engine.scalping.continuous_reversal_postclose import digest

VERSION = "continuous_reversal_branch_registry_v1"
BRANCH = "samsung_up_shallow_next_up_5_v1"
FIRST = "FIRST_UPTICK"
CONFIRMED = "CONFIRMED_UPTICK"
DEFINITION = dict(branch_id=BRANCH, kind="registered_pattern", symbol="005930",
                  market="REGULAR", venue="SOR", item="005930_AL",
                  drop_max_pct=.4, session_return_min_pct=.4,
                  return_60s_min_pct=.2, higher_low=True,
                  drawdown_5m_min_pct=.4, drawdown_5m_max_pct=.8,
                  confirmation_seconds=5, decision_phase=CONFIRMED)
DEFINITION_SHA256 = digest(DEFINITION)
MAX_PENDING = 1024
MAX_READY = 256


def legacy_branch(rule):
    if rule not in K.RULES:
        raise ValueError("unknown_legacy_reversal_rule")
    return dict(branch_id="legacy_" + rule.lower() + "_v1", kind="legacy_rule",
                rule=rule, decision_phase=FIRST)


def pattern_branch():
    return dict(branch_id=BRANCH, kind="registered_pattern", pattern=BRANCH,
                definition_sha256=DEFINITION_SHA256, decision_phase=CONFIRMED)


def payload(branches):
    return dict(composition="ANY_MATCH_ONE_INTENT", branches=copy.deepcopy(branches))


def validate_payload(value, key):
    if (not isinstance(value, dict) or set(value) != {"composition", "branches"}
            or value["composition"] != "ANY_MATCH_ONE_INTENT"
            or not isinstance(value["branches"], list) or not value["branches"]):
        raise ValueError("reversal_branch_composition_invalid")
    seen = set()
    for branch in value["branches"]:
        if not isinstance(branch, dict) or branch.get("branch_id") in seen:
            raise ValueError("reversal_branch_duplicate_or_invalid")
        seen.add(branch.get("branch_id"))
        if branch.get("kind") == "legacy_rule":
            if branch != legacy_branch(branch.get("rule")):
                raise ValueError("reversal_legacy_branch_invalid")
        elif branch != pattern_branch() or key != "samsung|REGULAR|ALL":
            raise ValueError("reversal_pattern_scope_or_definition_invalid")


class WindowMinimum:
    def __init__(self):
        self.queue = deque()

    def add(self, row):
        while self.queue and self.queue[-1][3] >= row[3]:
            self.queue.pop()
        self.queue.append(row)

    def expire(self, boundary):
        while self.queue and self.queue[0][0] < boundary:
            self.queue.popleft()

    def value(self):
        return self.queue[0][3] if self.queue else None


class PriceTurnState(K.ReversalState):
    """v1 price-turn semantics with only nine recent rows copied per trigger."""
    def observe(self,row,*,symbol,venue,session):
        while len(self.rows)>10 and self.rows[0][0]<row[0]-305:self.rows.popleft()
        while self.highs and self.highs[0][0]<row[0]-300:self.highs.popleft()
        if self.last and row[1:3]==self.last[1:3]:
            if row==self.last:return
            row=list(row);row[8]=0
        if self.last is None or not K.connected(self.last,row):
            self.direction=0;self.peak=self.low=self.turn=None;self.steps=0;self.segment_start=row[0]
        if not row[8]:
            self.rows.append(row);self.last=row;self.turn=None;return
        if self.last and K.connected(self.last,row):
            change=row[3]-self.last[3]
            if change<0:
                if self.direction!=-1:self.peak,self.steps=self.last,0
                self.direction=-1;self.low=row;self.steps+=1;self.turn=None
            elif change>0:
                if self.direction==-1:
                    high=self.highs[0][3] if self.highs else None
                    self.turn=dict(event_id=f'{datetime.fromtimestamp(row[0],K.KST).date()}:{venue}:{session}:{symbol}:{row[1]}:{row[2]}',
                        symbol=symbol,venue=venue,session=session,market=K.market_bucket(session),group='samsung' if symbol=='005930' else 'other',
                        price_band='LT_20000' if row[3]<20000 else '20000_TO_100000' if row[3]<100000 else 'GE_100000',
                        at=K.iso(row[0]),epoch=row[0],source_item=row[9],low_price=self.low[3],confirmation_price=row[3],
                        entry_ask=row[5] if K.good_quote(row) else None,drop_pct=100*(1-self.low[3]/self.peak[3]),
                        drawdown_5m_pct=max(0.,100*(1-self.low[3]/high)) if high else None,
                        confirmation_pct=100*(row[3]/self.low[3]-1),decline_seconds=self.low[0]-self.peak[0],down_steps=self.steps,
                        spread_pct=100*(row[5]/row[4]-1) if K.good_quote(row) else None,volume_ratio_60s=None,
                        _recent_rows=list(reversed(list(islice(reversed(self.rows),9))))+[row[:]])
                self.direction=1
        self.rows.append(row)
        while self.highs and self.highs[-1][3]<=row[3]:self.highs.pop()
        self.highs.append(row);self.last=row


class BranchState:
    """Amortized bounded rolling features; immutable first confirmation facts."""
    def __init__(self, *, session_anchor=None, generation="research"):
        self.legacy = PriceTurnState()
        self.session_anchor = session_anchor
        self.generation = generation
        self.history = deque()
        self.delay = deque()
        self.new_low, self.old_low = WindowMinimum(), WindowMinimum()
        self.pending = {}
        self.ready = deque()
        self.counts = Counter()
        self.last_anchor = None
        self.anchor_state='not_observed'

    def _reset_windows(self):
        self.history.clear()
        self.delay.clear()
        self.new_low = WindowMinimum()
        self.old_low = WindowMinimum()
        self.counts["confirmation_path_censored"] += len(self.pending)
        self.pending.clear()
        self.counts["ready_path_censored"] += len(self.ready)
        self.ready.clear()

    def features(self, row):
        t = row[0]
        # Keep the last observation at/before t-60 (research searchsorted right).
        while len(self.history) > 1 and self.history[1][0] <= t - 60:
            self.history.popleft()
        self.new_low.expire(t - 30)
        while self.delay and self.delay[0][0] < t - 30:
            self.old_low.add(self.delay.popleft())
        self.old_low.expire(t - 60)
        covered = t - self.legacy.segment_start >= 60
        past = self.history[0] if self.history and self.history[0][0] <= t - 60 else None
        low, old = self.new_low.value(), self.old_low.value()
        anchor = self.session_anchor
        return dict(ret60=100 * (row[3] / past[3] - 1) if covered and past else None,
                    session=100 * (row[3] / anchor[3] - 1) if anchor else None,
                    low_rising=bool(low > old) if covered and low is not None and old is not None else None,
                    session_anchor_epoch=anchor[0] if anchor else None,
                    session_anchor_price=anchor[3] if anchor else None)

    def observe(self, row, *, symbol, venue, session):
        last = self.legacy.last
        if last and row == last:
            return
        if last and (last[9]!=row[9] or datetime.fromtimestamp(last[0],K.KST).date()!=datetime.fromtimestamp(row[0],K.KST).date()):
            self._reset_windows()
            self.legacy=PriceTurnState()
            if datetime.fromtimestamp(last[0],K.KST).date()!=datetime.fromtimestamp(row[0],K.KST).date():self.session_anchor=None
        elif last and not K.connected(last, row):
            self._reset_windows()
        self.legacy.observe(row, symbol=symbol, venue=venue, session=session)
        if not row[8] or self.legacy.last[8] != 1:
            self._reset_windows()
            return
        t = row[0]
        self.history.append(row)
        self.delay.append(row)
        self.new_low.add(row)
        while self.ready and t - self.ready[0]["event"]["epoch"] > 5:
            self.ready.popleft()
            self.counts["ready_expired"] += 1
        matched = []
        for anchor_id, anchor in list(self.pending.items()):
            event = anchor["event"]
            reason = ("confirmation_timeout" if t > event["epoch"] + 5 else
                      "original_low_retested" if row[3] <= event["low_price"] else None)
            if reason:
                self.pending.pop(anchor_id)
                self.counts[reason] += 1
            elif row[3] > event["confirmation_price"]:
                matched.append(anchor)
                self.pending.pop(anchor_id)
        if matched:
            matched.sort(key=lambda a: (a["event"]["epoch"], a["event"]["event_id"]))
            original = matched[0]["event"]
            event = {k: v for k, v in original.items() if not k.startswith("_")}
            confirm_id = f'{datetime.fromtimestamp(t,K.KST).date()}:{venue}:{session}:{symbol}:{row[1]}:{row[2]}'
            event.update(event_id=confirm_id, signal_id=confirm_id, epoch=t, at=K.iso(t),
                         decision_phase=CONFIRMED, confirmation_price=row[3],
                         entry_ask=row[5] if K.good_quote(row) else None,
                         spread_pct=100*(row[5]/row[4]-1) if K.good_quote(row) else None,
                         anchor_event_id=original["event_id"], anchor_epoch=original["epoch"],
                         anchor_price=original["confirmation_price"],
                         anchor_ids=[a["event"]["event_id"] for a in matched],
                         branch_features=matched[0]["features"],
                         branch_definition_sha256=DEFINITION_SHA256,
                         native_epoch=row[1], native_sequence=row[2],
                         registry_generation=self.generation)
            if self.legacy.turn and self.legacy.turn['event_id']==confirm_id:
                event['coincident_first']={k:v for k,v in self.legacy.turn.items() if not k.startswith('_')}
            if len(self.ready) >= MAX_READY:
                self.counts["ready_overload"] += 1
            else:
                self.ready.append(dict(event=event, row=row, claimed=False))
                self.counts["confirmed"] += 1
        turn = self.legacy.turn
        if turn and turn["event_id"] != self.last_anchor:
            self.last_anchor = turn["event_id"]
            self.anchor_state='condition_not_met'
            self.counts["anchors"] += 1
            f = self.features(row)
            if (symbol, K.market_bucket(session), venue, row[9]) != ("005930", "REGULAR", "SOR", "005930_AL"):
                return
            if any(f[k] is None for k in ("ret60", "session", "low_rising")) or turn["drawdown_5m_pct"] is None:
                self.counts["required_feature_missing"] += 1
                self.anchor_state='required_feature_missing'
            elif (turn["drop_pct"] <= .4 and .4 <= turn["drawdown_5m_pct"] <= .8
                  and f["ret60"] >= .2 and f["session"] >= .4 and f["low_rising"]):
                if len(self.pending) >= MAX_PENDING:
                    self.counts["pending_overload"] += 1
                else:
                    self.pending[turn["event_id"]] = dict(event=copy.deepcopy(turn), features=f)
                    self.anchor_state='pending_confirmation'
                    self.counts["pending"] += 1
        # Quiet ticks also advance the delayed window; no feature uses future rows.
        self.features(row)

    def snapshot(self, ready):
        event = copy.deepcopy(ready["event"])
        rows = [r[:] for r in self.legacy.rows if r[1] == event["native_epoch"]
                and r[2] <= event["native_sequence"]]
        frozen = K.ReversalState()
        frozen.rows = deque(rows)
        frozen.turn = dict(event, _recent_rows=rows[-10:])
        frozen.segment_start = self.legacy.segment_start
        return frozen_snapshot(frozen)


def frozen_snapshot(frozen):
    """Keep both fact ledgers when one native tick matches two phases."""
    snap=frozen.snapshot()
    if snap and snap[0].get('coincident_first'):
        first=K.ReversalState();first.rows=frozen.rows
        first.turn=dict(snap[0]['coincident_first'],_recent_rows=list(islice(reversed(frozen.rows),10))[::-1])
        first.segment_start=frozen.segment_start
        original=first.snapshot()
        if original is None:raise ValueError('reversal_coincident_first_snapshot_missing')
        snap[0]['coincident_first'],snap[0]['coincident_first_input']=original
    return snap


_STATES = {}
_ANCHORS = {}
_RESTORED_DAYS = set()
_EMPTY_PREFIX_DAYS = set()
_LOCK = threading.RLock()
_GENERATION = None
_V2 = False
_CLAIMS = {}


def configure(family_sha256, *, v2=None):
    global _GENERATION, _V2
    with _LOCK:
        if v2 is not None:_V2=v2
        if family_sha256 != _GENERATION:
            for state in _STATES.values():
                state._reset_windows()
                state.legacy.turn=None
                state.last_anchor=None
                state.anchor_state = 'not_observed'
                state.generation = family_sha256
            _CLAIMS.clear()
            _GENERATION = family_sha256


def restore_session_anchors(data_root, day):
    """Restore the first native accepted observation outside the WS callback.

    This prefix is context only. It never republishes an old trigger or ready.
    """
    import json
    from pathlib import Path
    import gzip
    from src.engine.scalping.continuous_reversal_source import discover
    with _LOCK:
        if day in _RESTORED_DAYS:return
    specs = [s for s in discover(data_root,day) if (s['venue'],s['session'])==('SOR','SOR_REGULAR')]
    if not specs:
        with _LOCK:
            _EMPTY_PREFIX_DAYS.add(day)
            _RESTORED_DAYS.add(day)
        return
    first = None
    for spec in specs:
      for source in spec['files']:
        path=Path(source['path'])
        opener=gzip.open if path.suffix=='.gz' else open
        with opener(path,'rt') as handle:
            for line in handle:
              try:
                r = json.loads(line)
                if (r.get('schema')=='scalp_micro_reversion_market_stream_point_v3'
                        and r.get('venue')=='SOR' and r.get('session_bucket')=='SOR_REGULAR'
                        and r.get("symbol") == "005930" and r.get("source_item") == "005930_AL"
                        and r.get("path_consumer_eligible") is True and r.get("path_order_status") == "accept"):
                    received = datetime.fromisoformat(r["local_receive_timestamp"])
                    exchanged = datetime.fromisoformat(r["exchange_timestamp"])
                    if received.tzinfo is None or exchanged.tzinfo is None:continue
                    t,ex=received.timestamp(),exchanged.timestamp()
                    price = r.get("trade_price")
                    if (datetime.fromtimestamp(t,K.KST).date().isoformat()==day
                            and type(r.get('sequence_epoch')) is int and type(r.get('series_sequence')) is int
                            and r['series_sequence']>0 and type(price) in {int, float}
                            and math.isfinite(price) and price > 0 and 0 <= t-ex <= 5):
                        row=[t,r['sequence_epoch'],r['series_sequence'],price]
                        if first is None or tuple(row[:3])<tuple(first[:3]):first=row
                        break
              except (ValueError,TypeError,KeyError,OverflowError):continue
    with _LOCK:
        if first is not None:
            key = ("005930", "SOR", "005930_AL", "REGULAR", day)
            _ANCHORS[key] = first
            if key in _STATES:_STATES[key].session_anchor=first
        # Existing but invalid/unreadable source never licenses restart-price substitution.
        _RESTORED_DAYS.add(day)


def observe_normalized(symbol, session, envelope):
    if not _V2:K.observe_normalized(symbol, session, envelope)
    venue='SOR' if envelope.get('market_route')=='krx_nxt_integrated' else envelope.get('effective_venue')
    if venue not in {'SOR','KRX','NXT'}:return
    try:
        t, price = float(envelope["observed_epoch"]), float(envelope["trade_price"])
        exchange = envelope.get("provider_trade_epoch")
        row = [t, envelope["transport_epoch"], envelope["route_sequence"], price,
               envelope.get("inline_best_bid"), envelope.get("inline_best_ask"), envelope.get("trade_qty"),
               {"BUY": 1, "SELL": -1}.get(envelope.get("aggressor_side"), 0),
               int(math.isfinite(t) and math.isfinite(price) and price > 0
                   and type(exchange) in {int,float} and 0 <= t-exchange <= 5), envelope["item"], 0]
        key = (symbol,venue,row[9],K.market_bucket(session),datetime.fromtimestamp(t,K.KST).date().isoformat())
        with _LOCK:
            if (key[:4]==('005930','SOR','005930_AL','REGULAR') and key[4] in _EMPTY_PREFIX_DAYS
                    and row[8] and key not in _ANCHORS):
                _ANCHORS[key]=row[:4]
            for old in list(_STATES):
                if old[:3]==key[:3] and old!=key:_STATES.pop(old)
            state = _STATES.setdefault(key, BranchState(session_anchor=_ANCHORS.get(key), generation=_GENERATION))
            state.observe(row, symbol=symbol, venue=venue, session=session)
    except (ValueError, TypeError, KeyError, OverflowError):
        return


def claim_snapshot(symbol, venue, session, *, now, item, family_sha256):
    """Claim an immutable snapshot; a claim is not an evaluation/provider ACK."""
    configure(family_sha256,v2=True)
    key = (symbol, venue, item, K.market_bucket(session), datetime.fromtimestamp(now,K.KST).date().isoformat())
    with _LOCK:
        for token,claim in list(_CLAIMS.items()):
            if now-claim['snapshot'][0]['epoch']>5:_CLAIMS.pop(token)
        state = _STATES.get(key)
        selected=None
        if state:
            for ready in state.ready:
                if not ready["claimed"] and 0 <= now-ready["event"]["epoch"] <= 5:
                    ready['claimed']=True
                    event=copy.deepcopy(ready['event'])
                    frozen=PriceTurnState()
                    frozen.rows=deque(r[:] for r in state.legacy.rows if r[1]==event['native_epoch'] and r[2]<=event['native_sequence'])
                    frozen.turn=dict(event,_recent_rows=list(islice(reversed(frozen.rows),10))[::-1])
                    frozen.segment_start=state.legacy.segment_start
                    selected=frozen
                    break
    if selected:
        snap=frozen_snapshot(selected)
        token=digest([family_sha256,snap[0]['signal_id'],snap])
        with _LOCK:
            if _GENERATION!=family_sha256:return None
            _CLAIMS[token]=dict(snapshot=copy.deepcopy(snap),generation=family_sha256,scope=key)
        return dict(token=token,snapshot=snap,generation=family_sha256)
    with _LOCK:
        state=_STATES.get(key)
        if _V2 and state and state.legacy.turn and 0<=now-state.legacy.turn['epoch']<=5:
            frozen=PriceTurnState();frozen.rows=deque(r[:] for r in state.legacy.rows)
            frozen.turn=copy.deepcopy(state.legacy.turn);frozen.segment_start=state.legacy.segment_start
            frozen.turn['registered_branch_state']=state.anchor_state
        else:frozen=None
    snap=frozen.snapshot() if frozen else None if _V2 else K.current_snapshot(symbol, venue, session, now=now, item=item)
    if snap:
        snap[0].update(decision_phase=FIRST, signal_id=snap[0]["event_id"])
        token = digest([family_sha256, snap[0]["signal_id"], snap])
        with _LOCK:
            existing = _CLAIMS.get(token)
            if existing:
                return None
            _CLAIMS[token] = dict(snapshot=copy.deepcopy(snap), generation=family_sha256, scope=key)
        return dict(token=token, snapshot=snap, generation=family_sha256)
    return None


def validate_claim(claim, family_sha256, *, now):
    if not isinstance(claim, dict):
        raise ValueError("reversal_signal_claim_missing")
    with _LOCK:
        original = _CLAIMS.get(claim.get("token"))
        if not original or original["generation"] != family_sha256 or claim.get("generation") != family_sha256:
            raise ValueError("reversal_signal_generation_changed")
        snapshot = original["snapshot"]
        if digest(snapshot) != digest(claim.get("snapshot")) or not 0 <= now-snapshot[0]["epoch"] <= 5:
            raise ValueError("reversal_signal_expired_or_changed")
        key = original["scope"]
        if snapshot[0].get("decision_phase") == CONFIRMED:
            state = _STATES.get(key)
            event = snapshot[0]
            if (not state or not state.legacy.last or not state.legacy.last[8]
                    or state.legacy.last[1] != event["native_epoch"]
                    or not any(r["event"]["signal_id"] == event["signal_id"] for r in state.ready)):
                raise ValueError("reversal_signal_path_changed")
        elif _V2:
            state=_STATES.get(key)
            if not state or not state.legacy.turn or state.legacy.turn['event_id']!=snapshot[0]['event_id']:
                raise ValueError('reversal_first_signal_invalidated')
        return copy.deepcopy(snapshot)


def acknowledge(claim, *, status):
    with _LOCK:
        original = _CLAIMS.get((claim or {}).get("token"))
        if original:
            original["status"] = status
        # Bound memory by native freshness, preserving status while eligible.
        now = datetime.now(K.KST).timestamp()
        for token, item in list(_CLAIMS.items()):
            if now-item["snapshot"][0]["epoch"] > 5:
                _CLAIMS.pop(token)


def replay(rows, *, symbol, venue, session, bars=None):
    """Replay every normalized observation, with labels kept outside AI input."""
    rows=[r[:] for r in rows]
    if (symbol,venue,K.market_bucket(session))==('005930','SOR','REGULAR'):
        for r in rows:
            if r[9]!='005930_AL':r[8]=0
    anchor = next((r for r in rows if r[8]), None)
    state = BranchState(session_anchor=anchor)
    events = []
    for index, row in enumerate(rows):
        before = state.counts["confirmed"]
        state.observe(row, symbol=symbol, venue=venue, session=session)
        if state.counts["confirmed"] > before:
            snap = state.snapshot(state.ready[-1])
            event, source = snap
            event["entry_index"] = index
            events.append(dict(event=event, input=source))
    times = [r[0] for r in rows]
    _, ends, valid = K.segments(rows)
    tree = K.Tree([r[3] if r[8] else None for r in rows])
    for point in events:
        event = point["event"]
        outcome = K.label(rows,times,tree,ends,valid,event["entry_index"],event["entry_ask"])
        if outcome["status"] == "UNRESOLVED" and event["entry_ask"] is not None and bars:
            supplement = bars.label(event["epoch"], event["entry_ask"], 1800)
            if supplement["status"] != "UNRESOLVED":
                outcome = {**supplement, "source":"same_item_completed_bar_backfill"}
        point["outcome"] = outcome
    return events, dict(state.counts)
