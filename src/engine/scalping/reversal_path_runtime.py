"""Causal all-tick paths, independent of the immutable v3 turn registry."""
from __future__ import annotations
import copy
import math
import threading
import gzip
import json
from pathlib import Path
from collections import deque
from datetime import datetime
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_registered_runtime as OLD
from src.engine.scalping import reversal_path_catalog as C
from src.engine.scalping.continuous_reversal_postclose import digest


class State(OLD.State):
    def __init__(self, *, branch_ids, session_anchor=None, generation='research', offline=False):
        self.selected_ids = tuple(branch_ids)
        self.offline = offline
        self.path_pending = {}
        self.root_previous = {}
        self.prior_high = OLD.Extreme(True)
        self.prior_60_high = OLD.Extreme(True)
        self.q30 = OLD.QuantityWindow(seconds=30, sides=True)
        self.last_path_turn = None
        self._feature_key = None
        self._feature_values = None
        super().__init__(branch_ids=[b for b in branch_ids if b not in C.NEW_DEFINITIONS],
                         session_anchor=session_anchor, generation=generation)

    def _reset_windows(self):
        super()._reset_windows()
        self.counts['path_source_censored'] += len(self.path_pending)
        self.path_pending.clear()
        self.root_previous.clear()
        self.prior_high = OLD.Extreme(True)
        self.prior_60_high = OLD.Extreme(True)
        self.q30 = OLD.QuantityWindow(seconds=30, sides=True)
        self.last_path_turn = None
        self._feature_key = None
        self._feature_values = None

    def features(self,row):
        identity=tuple(row[:3])
        if identity!=self._feature_key:
            self._feature_values=super().features(row)
            self._feature_key=identity
        return self._feature_values.copy()

    def _observe_legacy(self, row, *, symbol, venue, session):
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
                             branch_definition_sha256=C.OLD.branch(bid).get('definition_sha256'))
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
                match = C.OLD.matches(bid, turn, f)
                self.counts[bid+(':missing' if match is None else ':matched' if match else ':miss')] += 1
                if match is None:
                    self.anchor_state = 'required_feature_missing'
                if not match:
                    continue
                if C.OLD.branch(bid)['decision_phase'] == B.FIRST:
                    signals.setdefault(bid, []).append(copy.deepcopy(turn))
                elif not self.offline and len(self.pending)+len(self.path_pending) >= B.MAX_PENDING:
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
                     anchor_lineage=lineage, registry_sha256=C.OLD.SHA256)
        event['canonical_opportunity_id'] = digest([str(datetime.fromtimestamp(t,K.KST).date()), symbol,
            K.market_bucket(session), venue, row[9], row[1], row[2]])
        ready = dict(event=event, row=row, claimed=False)
        if self.ready and all(e['decision_phase'] == B.FIRST for e in self.ready[-1]['event']['branch_signals'].values()) and (not turn or turn['event_id'] != self.ready[-1]['event']['event_id']):
            self.ready.pop()
        if not self.offline and len(self.ready) >= B.MAX_READY:
            self.counts['ready_overload'] += 1
            return []
        self.ready.append(ready); self.counts['confirmed'] += 1
        return [ready]

    def _event(self, bid, row, symbol, venue, session, f, proof):
        eid = f'{datetime.fromtimestamp(row[0],K.KST).date()}:{venue}:{session}:{symbol}:{row[1]}:{row[2]}'
        return dict(event_id=eid, signal_id=eid, symbol=symbol, venue=venue, session=session,
                    market=K.market_bucket(session), source_item=row[9], epoch=row[0], at=K.iso(row[0]),
                    confirmation_price=row[3], entry_ask=row[5] if K.good_quote(row) else None,
                    spread_pct=100*(row[5]-row[4])/row[3] if K.good_quote(row) else None,
                    drawdown_5m_pct=f['dd'], volume_ratio_60s=f['volume'],
                    branch_features=copy.deepcopy(f), decision_phase=C.PHASES[bid],
                    signal_kind=C.PHASES[bid], signal_proof=copy.deepcopy(proof),
                    native_epoch=row[1], native_sequence=row[2], registry_generation=self.generation,
                    branch_definition_sha256=C.branch(bid)['definition_sha256'])

    def _source(self, event, row):
        f = event['branch_features']
        recent = list(self.legacy.rows)[-10:]
        prices = [dict(age_sec=event['epoch']-r[0], price=r[3], qty=r[6],
                       side={1:'BUY',-1:'SELL'}.get(r[7],'UNKNOWN')) for r in recent]
        q = self.q30
        facts = dict(confirmation_price=row[3], entry_ask=event['entry_ask'],
                     spread_pct=event['spread_pct'], drawdown_5m_pct=f['dd'],
                     volume_ratio_60s=f['volume'], return_60s_pct=f['ret'],
                     session_return_pct=f['session'], vs_vwap_60s_pct=f['vwap'],
                     buy_pressure_10t=f['buy10'],
                     buy_pressure_30s=100*q.buy/q.qty if row[0]-self.legacy.segment_start>=30 and q.qty>0 and not q.bad else None,
                     return_10t_pct=100*(row[3]/recent[-10][3]-1) if len(recent)>=10 else None)
        return dict(market=event['market'], venue=event['venue'], source_item=event['source_item'],
                    symbol_group=C.group(event['symbol']), price_band=C.band(row[3]), as_of=K.iso(row[0]),
                    schema='continuous_path_prefix_v1', facts=facts, signal_kind=event['signal_kind'],
                    signal_proof=copy.deepcopy(event['signal_proof']), recent_observed_prices=prices)

    def observe(self, row, *, symbol, venue, session):
        last = self.legacy.last
        if last and row == last:
            return []
        self.branch_ids = tuple(b for b in self.selected_ids if b not in C.NEW_DEFINITIONS)
        old_ready = self._observe_legacy(row, symbol=symbol, venue=venue, session=session)
        if not row[8] or not self.legacy.last[8]:
            return []
        t = row[0]
        self.prior_high.expire(t-300)
        self.prior_60_high.expire(t-60)
        previous_high, previous_60_high = self.prior_high.value(), self.prior_60_high.value()
        f = self.features(row)
        old_qty = self.q120.qty-self.q60.qty
        f.update(dd=100*(previous_high/row[3]-1) if previous_high else None,
                 volume=self.q60.qty/old_qty if t-self.legacy.segment_start>=120 and not self.q120.bad and old_qty>0 else None)
        self.q30.add(row)
        candidates = []
        ids = [bid for bid in self.selected_ids if bid in C.NEW_DEFINITIONS]
        # Pending roots own their first confirmation, even if its quote/filter fails.
        for identity, pending in list(self.path_pending.items()):
            bid = pending['bid']; phase = C.PHASES[bid]
            if bid not in ids:
                self.path_pending.pop(identity); continue
            if phase == 'MOMENTUM_HOLD':
                if row[3] < pending['price']:
                    self.path_pending.pop(identity); self.counts['hold_breached'] += 1; continue
                pending['minimum_price'] = min(pending['minimum_price'], row[3])
                confirmed = t-pending['epoch'] >= 1
            else:
                if t > pending['epoch']+120 or row[3] < pending['low']*.998:
                    self.path_pending.pop(identity); self.counts['retest_expired_or_breached'] += 1; continue
                pending['minimum_price'] = min(pending['minimum_price'],row[3])
                if pending.get('touch_sequence') is None and row[3] <= pending['low']:
                    pending.update(touch_sequence=row[2], touch_epoch=t, touch_price=row[3])
                confirmed = pending.get('touch_sequence') is not None and row[2] > pending['touch_sequence'] and row[3] >= pending['reclaim']
            if confirmed:
                self.path_pending.pop(identity)
                candidates.append((bid,dict(pending)))
        turn = self.legacy.turn
        if turn and turn['event_id'] != self.last_path_turn:
            self.last_path_turn = turn['event_id']
            # Freeze every native FIRST, independently of other policies' verdicts.
            for bid in ids:
                phase = C.PHASES[bid]
                if phase == B.FIRST:
                    signal = copy.deepcopy(turn)
                    signal.update(branch_features=copy.deepcopy(f), decision_phase=B.FIRST,
                                  native_epoch=row[1], native_sequence=row[2], registry_generation=self.generation,
                                  branch_definition_sha256=C.branch(bid)['definition_sha256'])
                    # HA retains the native low-based DD and FIRST input semantics.
                    signal['volume_ratio_60s'] = f['volume']
                    candidates.append((bid,signal))
                elif phase.startswith('RETEST_'):
                    if not self.offline and len(self.path_pending)+len(self.pending) >= B.MAX_PENDING:
                        self.counts['path_pending_overload'] += 1; continue
                    self.path_pending[bid+':'+turn['event_id']] = dict(bid=bid,epoch=t,price=row[3],
                        native_sequence=row[2],native_epoch=row[1],anchor_event_id=turn['event_id'],
                        low=turn['low_price'],peak=self.legacy.peak[3],
                        reclaim=self.legacy.peak[3] if phase=='RETEST_RECLAIM_PEAK' else row[3],
                        minimum_price=row[3],touch_sequence=None)
        for bid in ids:
            root = C.NEW_DEFINITIONS[bid].get('root_contract',{})
            phase = C.PHASES[bid]
            if phase not in {'MOMENTUM_CROSS','MOMENTUM_HOLD','HIGH_BREAKOUT'}:
                continue
            if phase == 'HIGH_BREAKOUT':
                known = t-self.legacy.segment_start>=60 and previous_60_high is not None
                value = row[3] > previous_60_high if known else None
                proof = dict(prior_high=previous_60_high, previous_condition=self.root_previous.get(bid),
                             price=row[3], epoch=t, native_epoch=row[1], native_sequence=row[2])
            else:
                known = f['ret'] is not None
                value = f['ret'] >= root['return_60s_min_pct'] if known else None
                proof = dict(threshold=root['return_60s_min_pct'], return_60s_pct=f['ret'],
                             previous_condition=self.root_previous.get(bid), price=row[3],epoch=t,
                             native_epoch=row[1],native_sequence=row[2])
            crossed = known and self.root_previous.get(bid) is False and value is True
            self.root_previous[bid] = value
            if crossed:
                if phase == 'MOMENTUM_HOLD':
                    if self.offline or len(self.path_pending)+len(self.pending) < B.MAX_PENDING:
                        self.path_pending[bid+':'+str(row[2])] = dict(bid=bid,minimum_price=row[3],**proof)
                    else:
                        self.counts['path_pending_overload'] += 1
                else:
                    candidates.append((bid,proof))
        self.prior_high.add(row); self.prior_60_high.add(row)
        signals = copy.deepcopy(old_ready[0]['event']['branch_signals']) if old_ready else {}
        inputs = {}
        lineage = copy.deepcopy(old_ready[0]['event']['anchor_lineage']) if old_ready else {}
        for bid,proof in candidates:
            event = proof if C.PHASES[bid]==B.FIRST else self._event(bid,row,symbol,venue,session,f,proof)
            matched = C.matches(bid,event,event['branch_features'])
            self.counts[bid+(':missing' if matched is None else ':matched' if matched else ':miss')] += 1
            if not matched:continue
            if event.get('entry_ask') is None:
                self.counts['path_first_confirmation_quote_missing'] += 1
                continue
            lineage.setdefault(bid,[]).append(proof.get('anchor_event_id',event['event_id']))
            if bid in signals:continue
            signals[bid] = event
            if C.PHASES[bid] != B.FIRST:
                inputs[bid] = self._source(event,row)
        if not signals:
            return []
        first = next(iter(signals.values()))
        event = copy.deepcopy(first)
        event.update(branch_signals=signals,anchor_lineage=lineage,registry_sha256=C.SHA256,
                     canonical_opportunity_id=digest([str(datetime.fromtimestamp(t,K.KST).date()),symbol,
                         K.market_bucket(session),venue,row[9],row[1],row[2]]))
        if old_ready:
            self.ready.remove(old_ready[0])
        if not self.offline and len(self.ready)>=B.MAX_READY:
            self.counts['path_ready_overload'] += 1; return []
        ready = dict(event=event,row=row,claimed=False,path_inputs=inputs)
        self.ready.append(ready)
        return [ready]

    def snapshot(self, ready):
        event = copy.deepcopy(ready['event'])
        branch_inputs = copy.deepcopy(ready.get('path_inputs',{}))
        old_signals = {bid:signal for bid,signal in event['branch_signals'].items() if bid not in branch_inputs}
        if old_signals:
            source_ready = dict(ready,event=dict(event,branch_signals=old_signals))
            old_event,old_source = super().snapshot(source_ready)
            event['branch_signals'].update(old_event['branch_signals'])
            branch_inputs.update(old_source['branch_inputs'])
        return event,dict(branch_inputs=branch_inputs)


_LOCK = threading.RLock()
_STATES = {}; _ANCHORS = {}; _RESTORED_DAYS = set(); _EMPTY_PREFIX_DAYS = set()
_CLAIMS = {}; _GENERATION = None; _FAMILY = None


def configure(family):
    global _GENERATION, _FAMILY
    with _LOCK:
        if _GENERATION != family['family_sha256']:
            for state in _STATES.values():
                state._reset_windows(); state.ready.clear(); state.legacy.turn = None; state.last_anchor = None
                state.legacy.segment_start = state.legacy.last[0] if state.legacy.last else None
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
                        from src.engine.scalping.micro_reversion.forward_collector import _explicit_item_venue
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
    from src.engine.scalping.micro_reversion.forward_collector import _explicit_item_venue
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
            # Track selected definitions across bands; filter at the actual confirmation.
            ids = tuple(dict.fromkeys(b['branch_id'] for band in C.BANDS
                for b in _FAMILY['machine_cells'][f'{C.group(symbol)}|{K.market_bucket(session)}|{band}']['routes'][venue]['payload']['branches']))
            state = _STATES.get(key)
            if state is None:
                state = _STATES[key] = State(branch_ids=ids, session_anchor=_ANCHORS.get(key), generation=_GENERATION)
            else:
                state.selected_ids = ids
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
            cell = _FAMILY['machine_cells'][C.cell_key(symbol,session,e['confirmation_price'])]['routes'][venue]
            selected = {b['branch_id'] for b in cell['payload']['branches']}
            for bid in list(snap[0]['branch_signals']):
                if bid not in selected:
                    snap[0]['branch_signals'].pop(bid)
                    snap[1]['branch_inputs'].pop(bid)
            if not snap[0]['branch_signals']:
                continue
            if not state.legacy.turn or state.legacy.turn['event_id'] != e['event_id']:
                for bid in list(snap[0]['branch_signals']):
                    if snap[0]['branch_signals'][bid]['decision_phase'] == B.FIRST:
                        snap[0]['branch_signals'].pop(bid)
                        snap[1]['branch_inputs'].pop(bid)
                if not snap[0]['branch_signals']:
                    continue
            token = digest([family_sha256, e['signal_id'], snap])
            _CLAIMS[token] = dict(snapshot=copy.deepcopy(snap), generation=family_sha256, scope=key)
            return dict(token=token, snapshot=snap, generation=family_sha256, backend='registered_v4')
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
        from src.engine.scalping.continuous_reversal_policy_v4 import primary
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
