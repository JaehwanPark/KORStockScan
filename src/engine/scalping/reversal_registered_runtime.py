"""Shared rolling state and multi-branch claims for the registered Main family.

Consumes normalized observations only. No filesystem work on the WS callback,
provider calls, subscriptions, account reads, or order authority.
"""
from __future__ import annotations
import copy
import gzip
import json
import math
import threading
from collections import Counter, deque
from datetime import datetime
from pathlib import Path
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_registered_catalog as C
from src.engine.scalping.continuous_reversal_postclose import digest


class Extreme(B.WindowMinimum):
    def __init__(self, maximum=False):
        super().__init__(); self.maximum = maximum

    def add(self, row):
        while self.queue and (self.queue[-1][3] <= row[3] if self.maximum else self.queue[-1][3] >= row[3]):
            self.queue.pop()
        self.queue.append(row)


class QuantityWindow:
    def __init__(self, seconds=None, ticks=None, sides=False):
        self.rows = deque(); self.seconds = seconds; self.ticks = ticks; self.sides = sides
        self.qty = self.pv = self.buy = 0.; self.bad = 0

    def _delta(self, row, sign):
        q = row[6]
        valid = type(q) in (int, float) and math.isfinite(q) and q > 0
        self.bad += sign * int(not valid or (self.sides and row[7] not in (-1, 1)))
        if valid:
            self.qty += sign*q; self.pv += sign*q*row[3]
            self.buy += sign*q*int(row[7] == 1)

    def add(self, row):
        self.rows.append(row); self._delta(row, 1)
        while ((self.seconds and self.rows and self.rows[0][0] < row[0]-self.seconds)
               or (self.ticks and len(self.rows) > self.ticks)):
            self._delta(self.rows.popleft(), -1)


class State(B.BranchState):
    def __init__(self, *, branch_ids, session_anchor=None, generation='research'):
        super().__init__(session_anchor=session_anchor, generation=generation)
        self.branch_ids = tuple(branch_ids); self._extra_reset()

    def _extra_reset(self):
        self.new_high = Extreme(True); self.old_high = Extreme(True)
        self.high_delay = deque()
        self.q60 = QuantityWindow(seconds=60); self.q120 = QuantityWindow(seconds=120)
        self.q10 = QuantityWindow(ticks=10, sides=True)

    def _reset_windows(self):
        super()._reset_windows(); self._extra_reset()

    def features(self, row):
        f = super().features(row)
        self.new_high.expire(row[0]-30)
        while self.high_delay and self.high_delay[0][0] < row[0]-30:
            self.old_high.add(self.high_delay.popleft())
        self.old_high.expire(row[0]-60)
        covered = row[0]-self.legacy.segment_start >= 60
        low, old = self.new_low.value(), self.old_low.value()
        hi, prev = self.new_high.value(), self.old_high.value()
        valid = covered and all(v is not None for v in (low, old, hi, prev))
        structure = ('RISING' if hi > prev and low > old else 'FALLING' if hi < prev and low < old else 'MIXED') if valid else None
        s = f['session']
        q = self.q60
        f.update(ret=f['ret60'], structure=structure,
                 session_trend=None if s is None else 'UP' if s >= .4 else 'DOWN' if s <= -.4 else 'NEUTRAL',
                 high_rising=hi > prev if valid else None,
                 vwap=100*(row[3]/(q.pv/q.qty)-1) if covered and q.qty > 0 and not q.bad else None,
                 buy10=100*self.q10.buy/self.q10.qty if len(self.q10.rows) == 10 and self.q10.qty > 0 and not self.q10.bad else None)
        return f

    def observe(self, row, *, symbol, venue, session):
        last = self.legacy.last
        if last and row == last:
            return []
        if last and (last[9] != row[9] or not K.connected(last, row)):
            self._reset_windows()
        self.legacy.observe(row, symbol=symbol, venue=venue, session=session)
        if not row[8] or not self.legacy.last[8]:
            self._reset_windows(); return []
        self.history.append(row); self.delay.append(row); self.high_delay.append(row)
        self.new_low.add(row); self.new_high.add(row)
        for q in (self.q60, self.q120, self.q10):
            q.add(row)
        f = self.features(row); t = row[0]; signals = {}
        while self.ready and t-self.ready[0]['event']['epoch'] > 5:
            self.ready.popleft(); self.counts['ready_expired'] += 1
        # Ready observations are invalidated by native path breaks, not by a
        # different branch's new anchor. Pending ownership includes definition.
        for identity, anchor in list(self.pending.items()):
            e = anchor['event']
            reason = 'confirmation_timeout' if t > e['epoch']+5 else 'original_low_retested' if row[3] <= e['low_price'] else None
            if reason:
                self.pending.pop(identity); self.counts[reason] += 1
            elif row[3] > e['confirmation_price']:
                self.pending.pop(identity)
                bid = anchor['branch_id']
                event = {k: v for k, v in e.items() if not k.startswith('_')}
                eid = f'{datetime.fromtimestamp(t,K.KST).date()}:{venue}:{session}:{symbol}:{row[1]}:{row[2]}'
                event.update(event_id=eid, signal_id=eid, epoch=t, at=K.iso(t),
                             decision_phase=B.CONFIRMED, confirmation_price=row[3],
                             entry_ask=row[5] if K.good_quote(row) else None,
                             spread_pct=100*(row[5]/row[4]-1) if K.good_quote(row) else None,
                             anchor_event_id=e['event_id'], anchor_epoch=e['epoch'],
                             anchor_price=e['confirmation_price'], branch_features=anchor['features'],
                             native_epoch=row[1], native_sequence=row[2],
                             registry_generation=self.generation,
                             branch_definition_sha256=C.branch(bid).get('definition_sha256'))
                signals.setdefault(bid, []).append(event)
        turn = self.legacy.turn
        if turn and turn['event_id'] != self.last_anchor:
            self.last_anchor = turn['event_id']; self.counts['anchors'] += 1
            # The first-tick volume fact is frozen with the type filters.
            old_qty = self.q120.qty-self.q60.qty
            turn['volume_ratio_60s'] = (self.q60.qty/old_qty if t-self.legacy.segment_start >= 120 and not self.q120.bad and old_qty > 0 else None)
            turn.update(decision_phase=B.FIRST, signal_id=turn['event_id'],
                        branch_features=copy.deepcopy(f),
                        native_epoch=row[1], native_sequence=row[2], registry_generation=self.generation)
            self.anchor_state = 'condition_not_met'
            for bid in self.branch_ids:
                match = C.matches(bid, turn, f)
                self.counts[bid+(':missing' if match is None else ':matched' if match else ':miss')] += 1
                if match is None:
                    self.anchor_state = 'required_feature_missing'
                if not match:
                    continue
                if C.branch(bid)['decision_phase'] == B.FIRST:
                    signals.setdefault(bid, []).append(copy.deepcopy(turn))
                elif len(self.pending) >= B.MAX_PENDING:
                    self.counts['pending_overload'] += 1
                else:
                    self.pending[bid+':'+turn['event_id']] = dict(branch_id=bid, event=copy.deepcopy(turn), features=copy.deepcopy(f))
                    self.anchor_state = 'pending_confirmation'
        if not signals:
            if self.ready and all(e['decision_phase'] == B.FIRST for e in self.ready[-1]['event']['branch_signals'].values()) and (not turn or turn['event_id'] != self.ready[-1]['event']['event_id']):
                self.ready.pop(); self.counts['first_invalidated'] += 1
            return []
        represented = {}; lineage = {}
        for bid, anchors in signals.items():
            anchors.sort(key=lambda e: (e.get('anchor_epoch', e['epoch']), e.get('anchor_event_id', e['event_id'])))
            represented[bid] = anchors[0]
            lineage[bid] = [e.get('anchor_event_id', e['event_id']) for e in anchors]
        # One bundle per native confirmation tick, including simultaneous phases.
        first = next(iter(represented.values()))
        event = {k: v for k, v in first.items() if not k.startswith('_')}
        event.update(branch_signals={b: {k: v for k, v in e.items() if not k.startswith('_')} for b,e in represented.items()},
                     anchor_lineage=lineage, registry_sha256=C.SHA256)
        event['canonical_opportunity_id'] = digest([str(datetime.fromtimestamp(t,K.KST).date()), symbol,
            K.market_bucket(session), venue, row[9], row[1], row[2]])
        ready = dict(event=event, row=row, claimed=False)
        if self.ready and all(e['decision_phase'] == B.FIRST for e in self.ready[-1]['event']['branch_signals'].values()) and (not turn or turn['event_id'] != self.ready[-1]['event']['event_id']):
            self.ready.pop()
        if len(self.ready) >= B.MAX_READY:
            self.counts['ready_overload'] += 1
            return []
        self.ready.append(ready); self.counts['confirmed'] += 1
        return [ready]

    def snapshot(self, ready):
        event = copy.deepcopy(ready['event'])
        rows = [r for r in self.legacy.rows if r[1] == event['native_epoch'] and r[2] <= event['native_sequence']]
        phase_inputs = {}
        for bid, signal in event['branch_signals'].items():
            frozen = K.ReversalState(); frozen.rows = deque(rows)
            frozen.turn = dict(signal, _recent_rows=rows[-10:]); frozen.segment_start = self.legacy.segment_start
            snap = frozen.snapshot()
            event['branch_signals'][bid] = snap[0]
            phase_inputs[bid] = snap[1]
        return event, dict(branch_inputs=phase_inputs)


_LOCK = threading.RLock()
_STATES = {}; _ANCHORS = {}; _RESTORED_DAYS = set(); _EMPTY_PREFIX_DAYS = set()
_CLAIMS = {}; _GENERATION = None; _FAMILY = None


def configure(family):
    global _GENERATION, _FAMILY
    with _LOCK:
        if _GENERATION != family['family_sha256']:
            for state in _STATES.values():
                state.pending.clear(); state.ready.clear(); state.legacy.turn = None; state.last_anchor = None
                state.generation=family['family_sha256']
            _CLAIMS.clear()
        _GENERATION = family['family_sha256']; _FAMILY = family


def restore_session_anchors(data_root, day):
    from src.engine.scalping.continuous_reversal_source import discover
    with _LOCK:
        if day in _RESTORED_DAYS:
            return
    specs = discover(data_root, day); anchors = {}
    for spec in specs:
        for source in spec['files']:
            path = Path(source['path']); opener = gzip.open if path.suffix == '.gz' else open
            with opener(path, 'rt') as handle:
                for line in handle:
                    try:
                        r = json.loads(line)
                        received = datetime.fromisoformat(r['local_receive_timestamp']); exchanged = datetime.fromisoformat(r['exchange_timestamp'])
                        p = r['trade_price']; item = r['source_item']; code = r['symbol']; venue = r['venue']
                        if (r.get('schema') != 'scalp_micro_reversion_market_stream_point_v3' or not received.tzinfo or not exchanged.tzinfo
                                or received.astimezone(K.KST).date().isoformat() != day
                                or r.get('path_consumer_eligible') is not True or r.get('path_order_status') != 'accept'
                                or type(p) not in (int,float) or not math.isfinite(p) or p <= 0
                                or not 0 <= received.timestamp()-exchanged.timestamp() <= 5
                                or type(r['sequence_epoch']) is not int or type(r['series_sequence']) is not int or r['series_sequence'] <= 0):
                            continue
                        from src.trading.market.session_contract import market_source_partition_venue as _explicit_item_venue
                        if item.split('_',1)[0] != code or _explicit_item_venue(item) != venue:
                            continue
                        key = code, venue, item, K.market_bucket(r['session_bucket']), day
                        row = [received.timestamp(), r['sequence_epoch'], r['series_sequence'], p]
                        if key not in anchors or tuple(row[:3]) < tuple(anchors[key][:3]):
                            anchors[key] = row
                    except (ValueError, KeyError, TypeError, OverflowError):
                        continue
    with _LOCK:
        _ANCHORS.update(anchors)
        if not specs:
            _EMPTY_PREFIX_DAYS.add(day)
        for key, state in _STATES.items():
            state.session_anchor = _ANCHORS.get(key)
        _RESTORED_DAYS.add(day)


def observe_normalized(symbol, session, envelope):
    if _FAMILY is None:
        return B.observe_normalized(symbol, session, envelope)
    venue = 'SOR' if envelope.get('market_route') == 'krx_nxt_integrated' else envelope.get('effective_venue')
    if venue not in C.ROUTES.get(K.market_bucket(session), ()):
        return
    from src.trading.market.session_contract import market_source_partition_venue as _explicit_item_venue
    item = envelope.get('item')
    if not isinstance(item,str) or item.split('_',1)[0] != symbol or _explicit_item_venue(item) != venue:
        return
    try:
        t, price = float(envelope['observed_epoch']), float(envelope['trade_price'])
        ex = envelope.get('provider_trade_epoch')
        row = [t, envelope['transport_epoch'], envelope['route_sequence'], price,
               envelope.get('inline_best_bid'), envelope.get('inline_best_ask'), envelope.get('trade_qty'),
               {'BUY':1, 'SELL':-1}.get(envelope.get('aggressor_side'), 0),
               int(math.isfinite(t) and math.isfinite(price) and price > 0 and type(ex) in (int,float) and 0 <= t-ex <= 5), envelope['item'], 0]
        key = symbol, venue, row[9], K.market_bucket(session), datetime.fromtimestamp(t,K.KST).date().isoformat()
        with _LOCK:
            if key[4] in _EMPTY_PREFIX_DAYS and row[8] and key not in _ANCHORS:
                _ANCHORS[key] = row[:4]
            cell = _FAMILY['machine_cells'][C.cell_key(symbol, session, price)]['routes'][venue]
            ids = tuple(b['branch_id'] for b in cell['payload']['branches'])
            state = _STATES.get(key)
            if state is None:
                state = _STATES[key] = State(branch_ids=ids, session_anchor=_ANCHORS.get(key), generation=_GENERATION)
            else:
                state.branch_ids = ids
            for old in list(_STATES):
                if old[:3] == key[:3] and old != key:
                    _STATES.pop(old)
            state.observe(row, symbol=symbol, venue=venue, session=session)
    except (ValueError, KeyError, TypeError, OverflowError):
        return


def claim_snapshot(symbol, venue, session, *, now, item, family_sha256):
    key = symbol, venue, item, K.market_bucket(session), datetime.fromtimestamp(now,K.KST).date().isoformat()
    with _LOCK:
        if family_sha256 != _GENERATION:
            return None
        for token, old in list(_CLAIMS.items()):
            if now-old['snapshot'][0]['epoch'] > 5:
                _CLAIMS.pop(token)
        state = _STATES.get(key)
        if not state:
            return None
        for ready in state.ready:
            if ready['claimed'] or not 0 <= now-ready['event']['epoch'] <= 5:
                continue
            e = ready['event']
            # An all-FIRST bundle must still be the latest uninvalidated turn.
            if all(s['decision_phase'] == B.FIRST for s in e['branch_signals'].values()) and (not state.legacy.turn or state.legacy.turn['event_id'] != e['event_id']):
                ready['claimed'] = True; continue
            ready['claimed'] = True; snap = state.snapshot(ready)
            if not state.legacy.turn or state.legacy.turn['event_id'] != e['event_id']:
                for bid in list(snap[0]['branch_signals']):
                    if snap[0]['branch_signals'][bid]['decision_phase'] == B.FIRST:
                        snap[0]['branch_signals'].pop(bid)
                        snap[1]['branch_inputs'].pop(bid)
                if not snap[0]['branch_signals']:
                    continue
            token = digest([family_sha256, e['signal_id'], snap])
            _CLAIMS[token] = dict(snapshot=copy.deepcopy(snap), generation=family_sha256, scope=key)
            return dict(token=token, snapshot=snap, generation=family_sha256, backend='registered_v3')
    return None


def validate_claim(claim, family_sha256, *, now):
    if not isinstance(claim, dict):
        raise ValueError('reversal_signal_claim_missing')
    with _LOCK:
        original = _CLAIMS.get(claim.get('token'))
        if not original or original['generation'] != family_sha256 or claim.get('generation') != family_sha256 or _GENERATION != family_sha256:
            raise ValueError('reversal_signal_generation_changed')
        snap = original['snapshot']; event = snap[0]
        if digest(snap) != digest(claim.get('snapshot')) or not 0 <= now-event['epoch'] <= 5:
            raise ValueError('reversal_signal_expired_or_changed')
        state = _STATES.get(original['scope'])
        if not state or not state.legacy.last or not state.legacy.last[8] or state.legacy.last[1] != event['native_epoch']:
            raise ValueError('reversal_signal_path_changed')
        from src.engine.scalping.continuous_reversal_policy_v3 import primary
        cell = _FAMILY['machine_cells'][C.cell_key(event['symbol'],event['market'],event['confirmation_price'])]['routes'][event['venue']]
        matched = [b for b in event['branch_signals'] if b in {x['branch_id'] for x in cell['payload']['branches']}]
        if not matched:
            raise ValueError('reversal_signal_path_changed')
        bid = primary(cell,matched)
        if event['branch_signals'][bid]['decision_phase'] == B.FIRST and (not state.legacy.turn or state.legacy.turn['event_id'] != event['event_id']):
            raise ValueError('reversal_first_signal_invalidated')
        if not any(r['event']['signal_id'] == event['signal_id'] for r in state.ready):
            raise ValueError('reversal_signal_path_changed')
        return copy.deepcopy(snap)


def acknowledge(claim, *, status):
    with _LOCK:
        old = _CLAIMS.get((claim or {}).get('token'))
        if old:
            old['status'] = status


def backend(claim=None):
    return __import__(__name__, fromlist=['*']) if (claim or {}).get('backend') == 'registered_v3' or (claim is None and _FAMILY is not None) else B


def configure_bundle(bundle, data_root, day):
    global _FAMILY
    family = (bundle or {}).get('continuous_reversal')
    if family and family.get('schema') == 'continuous_reversal_policy_v3':
        configure(family); restore_session_anchors(data_root, day)
    else:
        _FAMILY = None
        B.restore_session_anchors(data_root, day)
        if family:
            B.configure(family['family_sha256'], v2=family.get('schema') == 'continuous_reversal_policy_v2')


def validate_any_claim(claim, family_sha256, *, now):
    return backend(claim).validate_claim(claim, family_sha256, now=now)


def acknowledge_any(claim, *, status):
    return backend(claim).acknowledge(claim, status=status)
