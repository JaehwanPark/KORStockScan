"""Independent fixed extended-session roots on the existing shared rolling state.

The frozen v4 implementation continues to own all original branch observations.
New roots neither reset those branches nor change their feature dictionaries.
"""
from __future__ import annotations
import copy
from datetime import datetime
from types import MappingProxyType
from src.engine.scalping import continuous_reversal as K
from src.engine.scalping import continuous_reversal_branches as B
from src.engine.scalping import reversal_path_runtime as OLD
from src.engine.scalping import reversal_extended_catalog as C
from src.engine.scalping.continuous_reversal_postclose import digest


class State(OLD.State):
    def __init__(self, *, branch_ids, registry_sha256=None, **kwargs):
        self.registry_sha256=registry_sha256 or (C.SHA256 if any(b in C.NEW_DEFINITIONS for b in branch_ids) else C.OLD.SHA256)
        self.extended_ids=tuple(b for b in branch_ids if b in C.NEW_DEFINITIONS)
        self.extended_pending={};self.extended_previous={};self.extended_turn=None
        self.coverage_snapshot=MappingProxyType({});self.coverage_identity=None
        super().__init__(branch_ids=[b for b in branch_ids if b not in C.NEW_DEFINITIONS],**kwargs)

    def _reset_windows(self):
        super()._reset_windows()
        self.counts['extended_source_censored']+=len(self.extended_pending)
        self.extended_pending.clear();self.extended_previous.clear();self.extended_turn=None
        self.coverage_snapshot=MappingProxyType({});self.coverage_identity=None

    def _extended_event(self,bid,row,symbol,venue,session,f,proof):
        eid=f'{datetime.fromtimestamp(row[0],K.KST).date()}:{venue}:{session}:{symbol}:{row[1]}:{row[2]}'
        result=dict(event_id=eid,signal_id=eid,symbol=symbol,venue=venue,session=session,
            market=K.market_bucket(session),source_item=row[9],epoch=row[0],at=K.iso(row[0]),
            confirmation_price=row[3],entry_ask=row[5] if K.good_quote(row) else None,
            spread_pct=100*(row[5]-row[4])/row[3] if K.good_quote(row) else None,
            drawdown_5m_pct=f['dd'],volume_ratio_60s=f['volume'],branch_features=copy.deepcopy(f),
            decision_phase=C.PHASES[bid],signal_kind=C.PHASES[bid],signal_proof=copy.deepcopy(proof),
            native_epoch=row[1],native_sequence=row[2],registry_generation=self.generation,
            branch_definition_sha256=C.branch(bid)['definition_sha256'],extended_definition_id=bid)
        if C.PHASES[bid]==B.FIRST:
            # Preserve native FIRST identity/low for subsequent validity checks;
            # this definition explicitly uses confirmation-based DD instead.
            result.update(low_price=proof['low'],anchor_event_id=proof['anchor_event_id'])
        return result

    def observe(self,row,*,symbol,venue,session):
        previous=self.legacy.last
        if previous and row==previous:return []
        self.prior_high.expire(row[0]-300)
        prior=self.prior_high.value() if previous and K.connected(previous,row) else None
        missing_before={b:self.counts[b+':missing'] for b in self.selected_ids}
        overload_before=sum(self.counts[k] for k in ('pending_overload','path_pending_overload','ready_overload','path_ready_overload'))
        old_ready=super().observe(row,symbol=symbol,venue=venue,session=session)
        all_ids=(*self.selected_ids,*self.extended_ids)
        valid=bool(row[8] and self.legacy.last and self.legacy.last[8])
        known=bool(valid and previous and K.connected(previous,row))
        truth={b:'FALSE' if known and K.good_quote(row) else 'UNKNOWN' for b in all_ids}
        self.coverage_identity=tuple(row[:3])
        if not valid:
            self.coverage_snapshot=MappingProxyType(truth);return old_ready
        t=row[0];f=self.features(row);prior_qty=self.q120.qty-self.q60.qty
        f.update(dd=100*(prior/row[3]-1) if prior else None,
                 volume=self.q60.qty/prior_qty if t-self.legacy.segment_start>=120 and not self.q120.bad and prior_qty>0 else None)
        candidates=[]
        for identity,p in list(self.extended_pending.items()):
            bid=p['bid'];root=C.definition(bid)['root_contract']
            if t>p['epoch']+root['maximum_wait_seconds'] or row[3]<p['low']*(1-root['allowed_below_original_low_pct']/100):
                self.extended_pending.pop(identity);self.counts['extended_expired_or_breached']+=1;continue
            p['minimum_price']=min(p['minimum_price'],row[3])
            if root['confirmation'].startswith('RETEST'):
                if p.get('touch_sequence') is None and row[3]<=p['low']:
                    p.update(touch_sequence=row[2],touch_epoch=t,touch_price=row[3])
                reached=p.get('touch_sequence') is not None and row[2]>p['touch_sequence'] and row[3]>=p['reclaim']
            else:reached=row[3]>=p['reclaim']
            if reached:
                self.extended_pending.pop(identity);candidates.append((bid,copy.deepcopy(p)))
        turn=self.legacy.turn
        fresh_turn=turn and turn['event_id']!=self.extended_turn
        if fresh_turn:
            self.extended_turn=turn['event_id']
            for bid in self.extended_ids:
                root=C.definition(bid)['root_contract']
                if root['signal']!='native_first_turn':continue
                proof=dict(bid=bid,epoch=t,price=row[3],native_sequence=row[2],native_epoch=row[1],
                    anchor_event_id=turn['event_id'],low=turn['low_price'],peak=self.legacy.peak[3],minimum_price=row[3],
                    root_contract=copy.deepcopy(root))
                if root['confirmation']=='immediate':candidates.append((bid,proof));continue
                proof['reclaim']=proof['peak'] if root['confirmation'] in {'PEAK','RETEST_PEAK'} else row[3]
                if root['confirmation']=='PEAK' and row[3]>=proof['reclaim']:
                    candidates.append((bid,proof));continue
                if not self.offline and len(self.extended_pending)+len(self.path_pending)+len(self.pending)>=B.MAX_PENDING:
                    self.counts['extended_pending_overload']+=1;truth[bid]='UNKNOWN';continue
                self.extended_pending[bid+':'+turn['event_id']]=proof
        for bid in self.extended_ids:
            root=C.definition(bid)['root_contract']
            if root['signal']!='MOMENTUM':continue
            value=f['ret']>=root['return_60s_min_pct'] if f['ret'] is not None else None
            previous_value=self.extended_previous.get(bid)
            self.extended_previous[bid]=value
            if value is None or previous_value is None:truth[bid]='UNKNOWN'
            if value is True and previous_value is False:
                candidates.append((bid,dict(epoch=t,price=row[3],native_epoch=row[1],native_sequence=row[2],
                    threshold=root['return_60s_min_pct'],return_60s_pct=f['ret'],previous_condition=False,root_contract=copy.deepcopy(root))))
        signals=copy.deepcopy(old_ready[0]['event']['branch_signals']) if old_ready else {}
        inputs=copy.deepcopy(old_ready[0].get('path_inputs',{})) if old_ready else {}
        lineage=copy.deepcopy(old_ready[0]['event']['anchor_lineage']) if old_ready else {}
        for bid,proof in candidates:
            event=self._extended_event(bid,row,symbol,venue,session,f,proof)
            matched=C.matches(bid,event,f)
            truth[bid]='UNKNOWN' if matched is None else 'FALSE'
            self.counts[bid+(':missing' if matched is None else ':matched' if matched else ':miss')]+=1
            if matched and event['entry_ask'] is not None:
                signals.setdefault(bid,event);inputs.setdefault(bid,self._source(event,row))
                lineage.setdefault(bid,[]).append(proof.get('anchor_event_id',event['event_id']))
        # Coverage is a detector-time snapshot. Known lack of a FIRST root is
        # FALSE; optional rolling windows cannot turn that absence into UNKNOWN.
        for bid in self.selected_ids:
            phase=C.branch(bid)['decision_phase']
            if phase in {'MOMENTUM_CROSS','MOMENTUM_HOLD','HIGH_BREAKOUT'} and self.root_previous.get(bid) is None:
                truth[bid]='UNKNOWN'
            # Consume the detector's own exact-phase outcome. Reconstructing
            # features here loses low-based DD and legacy volume completion.
            if self.counts[bid+':missing']>missing_before[bid]:truth[bid]='UNKNOWN'
            if sum(self.counts[k] for k in ('pending_overload','path_pending_overload','ready_overload','path_ready_overload'))>overload_before:
                truth[bid]='UNKNOWN'
        for bid in signals:truth[bid]='TRUE'
        if not K.good_quote(row):truth={b:'UNKNOWN' for b in all_ids}
        self.coverage_snapshot=MappingProxyType(truth)
        if not signals:return []
        if old_ready:self.ready.remove(old_ready[0])
        if not self.offline and len(self.ready)>=B.MAX_READY:
            self.counts['extended_ready_overload']+=1;return []
        event=copy.deepcopy(next(iter(signals.values())))
        event.update(branch_signals=signals,anchor_lineage=lineage,registry_sha256=self.registry_sha256,
            canonical_opportunity_id=digest([str(datetime.fromtimestamp(t,K.KST).date()),symbol,K.market_bucket(session),venue,row[9],row[1],row[2]]))
        ready=dict(event=event,row=row,claimed=False,path_inputs=inputs)
        self.ready.append(ready);return [ready]
